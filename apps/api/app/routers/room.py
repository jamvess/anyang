"""Tutor room endpoints (specs/system/api.md v1.2 "ห้องติว").

Stubs until P4-lite: they serve fixture data from app/stubs/ and send `X-Stub: true`,
so May can wire the HTTP transport before the tutor turn exists. Shapes are checked
by tests/unit/test_room_api_contract.py, which the real endpoints must also pass.

A text message is real since P4-lite: the reply streams from the gateway
(specs/features/tutor/tutor-reply-stream.md). An image message is still a stub, and so are
uploads, transcribe and ocr/confirm (api.md v1.7 · test_room_media_api_contract.py).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing
from datetime import datetime
from pathlib import Path as PathLib
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Path, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette import EventSourceResponse
from starlette.concurrency import run_in_threadpool

from app import stubs
from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway, get_gateway
from app.auth import AuthContext, get_auth
from app.clock import get_now
from app.db.errors import DB_DOWN_MESSAGE, DbUnavailableError
from app.db.room import RoomRepository, SessionRecord, get_room_repository
from app.domain.exam_prep import bangkok_today
from app.models.error import ErrorResponse, error_response, too_long_message, unavailable_docs
from app.models.room import (
    BYTES_PER_MB,
    EVENT_MODELS,
    UPLOAD_CONTENT_TYPES,
    ActiveSession,
    DoneEvent,
    Limits,
    Message,
    OcrConfirmRequest,
    ProgressCardEvent,
    Room,
    SendMessageRequest,
    TokenEvent,
    TranscribeRequest,
    Transcript,
    TtsAudio,
    UploadRequest,
    UploadTicket,
    bare_content_type,
)
from app.rate_limit import RATE_LIMITED_DOCS, chat_rate_limit
from app.services import room_db
from app.services.dev_uploads import (
    LocalImageStore,
    get_local_mode,
    get_local_upload_dir,
    image_mime,
    upload_path_ok,
)
from app.services.photo_check import (
    NO_PENDING_PROBLEM,
    ImageStore,
    confirm_events,
    get_image_store,
    photo_events,
)
from app.services.room_chat import text_message_events
from app.services.room_opening import opening_events
from app.services.room_state import (
    STUDENT,
    RoomState,
    get_room_state,
    room_key,
)
from app.settings import get_settings

log = logging.getLogger(__name__)

router = APIRouter(tags=["room"])

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
SessionId = Annotated[UUID, Path(alias="id")]
MessageId = Annotated[UUID, Path(alias="id")]

# Documented error shape for every room endpoint, so generated types match the envelope.
_ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Not found"},
    422: {"model": ErrorResponse, "description": "Invalid path or body"},
}

# OpenAPI for the SSE endpoints: each event payload is a schema in components
# (added in app.main) so `pnpm gen:api` generates types for them.
_SSE_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {
        "description": 'SSE stream; event names and payloads per api.md "SSE events"',
        "content": {
            "text/event-stream": {
                "schema": {
                    "oneOf": [
                        {"$ref": f"#/components/schemas/{model.__name__}"}
                        for name, model in EVENT_MODELS.items()
                        if name != "scope_patch"  # flow 2.3 only (api.md "SSE events")
                    ]
                }
            }
        },
    },
    **_ERRORS,
}


# --- the room on the database (room-sessions-db.md · api.md v1.15) ---------------------------
# With a token every endpoint below reads and writes through the user's JWT (RLS); without one
# (AUTH_REQUIRED=false) it keeps its stub or local demo. The Supabase client blocks, so DB work
# runs in the thread pool. Checks that answer 404, 409 or 503 run before any stream starts.

Auth = Annotated[AuthContext | None, Depends(get_auth)]
Repo = Annotated[RoomRepository | None, Depends(get_room_repository)]
Now = Annotated[datetime, Depends(get_now)]

_DB_ERRORS: dict[int | str, dict[str, Any]] = {**_ERRORS, **unavailable_docs("db_unavailable")}
_DB_SSE_RESPONSE: dict[int | str, dict[str, Any]] = {**_SSE_RESPONSE, **_DB_ERRORS}


def _not_found() -> JSONResponse:
    return error_response(404, "not_found", "Not found")


def _db_unavailable() -> JSONResponse:
    return error_response(503, "db_unavailable", DB_DOWN_MESSAGE)


def _open_and_save(
    prep_id: UUID, auth: AuthContext, repo: RoomRepository, now: datetime
) -> Response:
    """POST /exam-preps/{id}/sessions with a token (spec §2.4)."""
    try:
        prep = repo.get_prep(prep_id)
        if prep is None:
            return _not_found()
        profile = repo.profile_facts()
        session = repo.create_session(
            tenant_id=auth.tenant_id,
            user_id=auth.user_id,
            exam_prep_id=prep.id,
            scope_version_id=prep.active_scope_version_id,
        )
    except DbUnavailableError:
        return _db_unavailable()
    greeting = room_db.greeting_of(prep, profile, bangkok_today(now))
    return _sse(room_db.opening_events(repo, auth, session, greeting))


async def _send_and_save(
    session_id: UUID, text: str, auth: AuthContext, repo: RoomRepository, gateway: Gateway
) -> Response:
    """POST /sessions/{id}/messages `{text}` with a token (spec §2.7): 404 / 409 / 503 before
    the stream; the user message is saved before the model is called."""

    def check_and_save_user() -> tuple[SessionRecord, str] | JSONResponse:
        try:
            session = repo.get_session(session_id)
            if session is None:
                return _not_found()
            if session.ended_at is not None:
                return error_response(
                    409, "session_already_ended", "This session has already ended"
                )
            conversation = room_db.conversation_of(repo.list_messages(session.id))
            repo.add_message(
                tenant_id=auth.tenant_id,
                session_id=session.id,
                role="user",
                content=text,
                input_mode="text",
            )
        except DbUnavailableError:
            return _db_unavailable()
        return session, conversation

    checked = await run_in_threadpool(check_and_save_user)
    if isinstance(checked, JSONResponse):
        return checked
    session, conversation = checked
    return _sse(room_db.reply_and_save(gateway, repo, auth, session, text, conversation))


@router.get(
    "/exam-preps/{id}/sessions/active",
    response_model=ActiveSession,  # errors return a JSONResponse, so the return type is Any
    responses=_DB_ERRORS,
)
def get_active_session(
    prep_id: PrepId,
    response: Response,
    local: Annotated[bool, Depends(get_local_mode)],
    auth: Auth,
    repo: Repo,
) -> Any:
    """Open session of this exam prep, the latest started (TM-13); 404 `no_active_session` if
    none, `not_found` if the prep is not the user's.

    Without a token (AUTH_REQUIRED=false): stub. On a local machine there is none, so the web
    opens a new session and the tutor greets first (demo-room.md §2 F item 1).
    """
    if auth is not None and repo is not None:
        try:
            if repo.get_prep(prep_id) is None:
                return _not_found()
            session = repo.latest_open_session(prep_id)
        except DbUnavailableError:
            return _db_unavailable()
        if session is None:
            return error_response(404, "no_active_session", "No open session for this exam prep")
        return ActiveSession(session_id=session.id)
    if local:
        return error_response(404, "no_active_session", "No open session for this exam prep")
    response.headers.update(stubs.HEADERS)
    return ActiveSession(session_id=stubs.room()["session_id"])


@router.post(
    "/exam-preps/{id}/sessions",
    response_class=EventSourceResponse,
    responses=_DB_SSE_RESPONSE,
)
async def create_session(
    prep_id: PrepId,
    gateway: Annotated[Gateway, Depends(get_gateway)],
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    local: Annotated[bool, Depends(get_local_mode)],
    room_state: Annotated[RoomState, Depends(get_room_state)],
    repo: Repo,
    now: Now,
) -> Response:
    """Start a session. With a token: a new tutor_sessions row, then SSE session → token (the
    greeting from config/messages.yaml) → done, with no progress_card or problem yet
    (room-sessions-db.md §2.4). 404 if the prep is not the user's.

    Without a token (AUTH_REQUIRED=false): stub SSE session → progress_card → token → problem →
    done. On a local machine it is a new session of the demo: the card comes from real mastery
    and the problem is the one reached (demo-room.md §2 D, F, J).
    """
    if auth is not None and repo is not None:
        return await run_in_threadpool(_open_and_save, prep_id, auth, repo, now)
    if not local:
        return stubs.stream("session_start")
    recorded = stubs.events("session_start")
    key = room_key(stubs.tenant_of(auth), dict(recorded)["session"]["session_id"])
    await room_state.start_session(key)
    card = await room_state.progress_card(key)
    if card is None:
        return stubs.stream("session_start")
    call_context = AICallContext(auth.tenant_id, auth.user_id) if auth else None
    return _sse(opening_events(gateway, room_state, key, recorded, card, call_context))


@router.get("/sessions/{id}", response_model=Room, responses=_DB_ERRORS)
def get_session(
    session_id: SessionId,
    response: Response,
    local: Annotated[bool, Depends(get_local_mode)],
    auth: Auth,
    repo: Repo,
    now: Now,
) -> Any:
    """Room data: header, input limits and messages (oldest first). An ended session still
    opens (room-sessions-db.md §2.5).

    Without a token (AUTH_REQUIRED=false): stub. On a local machine there is no sample history:
    the tutor never had that conversation (demo-room.md §2 E item 1).
    """
    if auth is not None and repo is not None:
        try:
            session = repo.get_session(session_id)
            prep = repo.get_prep(session.exam_prep_id) if session else None
            if session is None or prep is None:
                return _not_found()
            profile = repo.profile_facts()
            messages = repo.list_messages(session.id)
        except DbUnavailableError:
            return _db_unavailable()
        return room_db.room_of(session, prep, profile, messages, bangkok_today(now))
    response.headers.update(stubs.HEADERS)
    guards = get_settings().ai.guards
    limits = Limits(max_message_chars=guards.max_message_chars, max_image_mb=guards.max_image_mb)
    room = {**stubs.room(), "session_id": session_id, "limits": limits}
    if local:
        room["messages"] = []
    return Room.model_validate(room)


# --- end, history, progress, tts (api.md v1.9 · proposal pending Junior) ----------


@router.post(
    "/sessions/{id}/end",
    response_class=EventSourceResponse,
    responses={
        **_SSE_RESPONSE,
        409: {"model": ErrorResponse, "description": "session_already_ended"},
    },
)
async def end_session(session_id: SessionId) -> EventSourceResponse:
    """The user ends the session. SSE: session_end (1-2 summary lines) → done (PM-05).

    stub — always the same summary; nothing is saved
    """
    return stubs.stream("session_end")


@router.get("/sessions/{id}/messages", response_model=list[Message], responses=_DB_ERRORS)
def list_messages(session_id: SessionId, response: Response, auth: Auth, repo: Repo) -> Any:
    """Chat history, oldest first (TM-13). Not paged yet.

    Without a token (AUTH_REQUIRED=false): the messages of the room fixture.
    """
    if auth is not None and repo is not None:
        try:
            if repo.get_session(session_id) is None:
                return _not_found()
            messages = repo.list_messages(session_id)
        except DbUnavailableError:
            return _db_unavailable()
        return [room_db.message_of(m) for m in messages]
    response.headers.update(stubs.HEADERS)
    return [Message.model_validate(m) for m in stubs.room()["messages"]]


@router.get(
    "/exam-preps/{id}/progress",
    responses={
        **_ERRORS,
        409: {"model": ErrorResponse, "description": "scope_not_confirmed"},
    },
)
async def get_progress(prep_id: PrepId, response: Response) -> ProgressCardEvent:
    """Progress card, the same shape as the progress_card event (TM-11, TM-15).

    stub — the card that opens the session fixture
    """
    response.headers.update(stubs.HEADERS)
    return ProgressCardEvent.model_validate(dict(stubs.events("session_start"))["progress_card"])


_STUB_AUDIO_URL = f"{stubs.STORAGE_URL}/tts/stub.mp3"


@router.get(
    "/messages/{id}/tts",
    responses={
        **_ERRORS,
        409: {"model": ErrorResponse, "description": "tts_unavailable for this message"},
        **unavailable_docs("tts_unavailable"),
    },
)
async def get_tts(message_id: MessageId, response: Response) -> TtsAudio:
    """Signed URL of the message read aloud, cached by text + voice (TM-09 · term 2).

    stub — the URL is not a real Storage URL
    """
    response.headers.update(stubs.HEADERS)
    return TtsAudio(audio_url=_STUB_AUDIO_URL)


@router.post(
    "/sessions/{id}/messages",
    response_class=EventSourceResponse,
    responses={
        **_DB_SSE_RESPONSE,
        409: {"model": ErrorResponse, "description": "session_already_ended"},
        **RATE_LIMITED_DOCS,
    },
    dependencies=[Depends(chat_rate_limit)],
)
async def send_message(
    session_id: SessionId,
    body: SendMessageRequest,
    gateway: Annotated[Gateway, Depends(get_gateway)],
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    image_store: Annotated[ImageStore | None, Depends(get_image_store)],
    room_state: Annotated[RoomState, Depends(get_room_state)],
    local: Annotated[bool, Depends(get_local_mode)],
    repo: Repo,
) -> Response:
    """Send `{text}`, `{image_path}` or both; the reply streams as SSE and ends with done.

    `{text}` streams `tutor_reply` from the gateway (P4-lite). With `image_path` the photo is read
    with `extract_answer` and streams an `ocr_preview` to confirm with
    POST /sessions/{id}/ocr/confirm (api.md v1.7 · photo-check-in-room.md); `text` is then the
    photo's caption and does not reach the model. Until Storage exists it is a stub.
    """
    if too_long := too_long_message(body.text):
        # Code proposed in tutor-reply-stream.md §10 item 3, pending Junior.
        return error_response(422, "message_too_long", too_long)
    if auth is not None and repo is not None and body.image_path is None and body.text:
        return await _send_and_save(session_id, body.text, auth, repo, gateway)
    # No session_id yet: the session is a stub with no tutor_sessions row (api-auth.md §2.5).
    call_context = AICallContext(auth.tenant_id, auth.user_id) if auth else None
    if body.image_path is not None:
        if image_store is None:  # no Storage yet (photo-check-in-room.md §2.4)
            return stubs.stream("image_reply")
        return await _photo_message(
            str(session_id),
            body.image_path,
            body.text,
            auth,
            gateway,
            image_store,
            room_state,
            call_context,
        )

    key = room_key(stubs.tenant_of(auth), str(session_id))
    return _sse(text_message_events(gateway, room_state, key, body.text, local, call_context))


def _sse(events: AsyncIterator[tuple[str, BaseModel]]) -> EventSourceResponse:
    """(event, payload) pairs as SSE. aclosing: a client that leaves closes the provider
    stream now (tutor-reply-stream.md §2 Endpoint 8)."""

    async def encoded() -> AsyncIterator[dict[str, str]]:
        async with aclosing(events) as pairs:
            async for event, payload in pairs:
                yield {"event": event, "data": payload.model_dump_json()}

    return EventSourceResponse(encoded())


def _own_upload(path: str, tenant_id: str, session_id: str) -> bool:
    """`{tenant_id}/sessions/{session_id}/{file}` (api.md v1.7) with a plain file name, so
    another tenant's or session's file, or a `..` path, is never read (SA-06)."""
    prefix = f"{tenant_id}/sessions/{session_id}/"
    name = path.removeprefix(prefix)
    return (
        path.startswith(prefix)
        and bool(name)
        and "/" not in name
        and "\\" not in name
        and not name.startswith(".")
    )


async def _photo_message(
    session_id: str,
    image_path: str,
    text: str | None,
    auth: AuthContext | None,
    gateway: Gateway,
    image_store: ImageStore,
    room_state: RoomState,
    call_context: AICallContext | None,
) -> Response:
    """Checks before the SSE starts (photo-check-in-room.md §2.1 items 1-3)."""
    tenant_id = stubs.tenant_of(auth)
    if not _own_upload(image_path, tenant_id, session_id):
        return error_response(404, "not_found", "No such upload in this session")
    key = room_key(tenant_id, session_id)
    pending = await room_state.pending_problem(key)
    if pending is None:
        # UC-04 E9 before an intent router exists (spec §10 item 4 · proposal pending Junior).
        return _sse(_no_pending_problem())
    image = await image_store.read(image_path)
    if image is None:
        return error_response(404, "not_found", "No such upload in this session")
    max_mb = get_settings().ai.guards.max_image_mb
    if len(image.data) > max_mb * BYTES_PER_MB:  # the browser's size_bytes is checked again
        return error_response(422, "file_too_large", f"image is over {max_mb} MB")
    caption = f" {text}" if text else ""
    await room_state.remember(key, STUDENT, f"(ส่งรูปวิธีทำ){caption}")
    return _sse(photo_events(gateway, room_state, key, pending, image, call_context))


async def _no_pending_problem() -> AsyncIterator[tuple[str, BaseModel]]:
    yield "token", TokenEvent(speaker="tutor", text=NO_PENDING_PROBLEM)
    yield "done", DoneEvent()


# --- uploads, transcribe, ocr/confirm (api.md v1.7 · proposal pending Junior) -----

_STUB_TRANSCRIPT = "สองเอ็กซ์ลบห้า คูณ สองเอ็กซ์บวกห้า"  # voice-input.md §3 example


@router.post(
    "/sessions/{id}/uploads",
    response_model=UploadTicket,  # errors return a JSONResponse, so the return type is Any
    responses={
        **_ERRORS,
        422: {
            "model": ErrorResponse,
            "description": "Invalid body, unsupported_type or file_too_large",
        },
    },
)
async def create_upload(
    session_id: SessionId,
    body: UploadRequest,
    request: Request,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    local: Annotated[bool, Depends(get_local_mode)],
) -> Any:
    """Signed upload URL for one image or audio file (TM-06, TM-07, TM-21).

    stub — the URL is not a real Storage URL until the endpoint talks to Supabase Storage.
    On a local machine an image gets a URL of this API, so the photo really arrives
    (demo-room.md §2 A).
    """
    content_type = bare_content_type(body.content_type)
    if content_type not in UPLOAD_CONTENT_TYPES[body.kind]:
        return stubs.error(
            422, "unsupported_type", f"{body.content_type} is not an accepted {body.kind}"
        )
    max_mb = get_settings().ai.guards.max_image_mb
    if body.kind == "image" and body.size_bytes > max_mb * BYTES_PER_MB:
        return stubs.error(422, "file_too_large", f"image is over {max_mb} MB")
    ext = content_type.split("/", 1)[1]
    path = f"{stubs.tenant_of(auth)}/sessions/{session_id}/{uuid4()}.{ext}"
    if local and body.kind == "image":
        return UploadTicket(upload_url=f"{request.base_url}dev/uploads/{path}", path=path)
    response.headers.update(stubs.HEADERS)
    return UploadTicket(upload_url=f"{stubs.STORAGE_URL}/{path}", path=path)


@router.put("/dev/uploads/{path:path}", include_in_schema=False)
async def put_local_upload(
    path: str,
    request: Request,
    local: Annotated[bool, Depends(get_local_mode)],
    upload_dir: Annotated[PathLib, Depends(get_local_upload_dir)],
) -> Response:
    """Local stand-in for the signed Storage URL (demo-room.md §2 A). Not in api.md: it exists
    only with APP_ENV=local, and answers 404 everywhere else."""
    if not local or not upload_path_ok(path):
        return error_response(404, "not_found", "Not found")
    content_type = bare_content_type(request.headers.get("content-type", ""))
    if content_type not in UPLOAD_CONTENT_TYPES["image"] or image_mime(path) is None:
        return error_response(422, "unsupported_type", f"{content_type} is not an accepted image")
    max_mb = get_settings().ai.guards.max_image_mb
    limit = max_mb * BYTES_PER_MB
    declared = request.headers.get("content-length", "")
    # Refuse a declared size before reading the body (self-review); check the real size too.
    if declared.isdigit() and int(declared) > limit:
        return error_response(422, "file_too_large", f"image is over {max_mb} MB")
    data = await request.body()
    if len(data) > limit:
        return error_response(422, "file_too_large", f"image is over {max_mb} MB")
    if not LocalImageStore(upload_dir).write(path, data):
        return error_response(404, "not_found", "Not found")
    return Response(status_code=200)


@router.post(
    "/sessions/{id}/transcribe",
    responses={
        **_ERRORS,
        422: {"model": ErrorResponse, "description": "Invalid body or audio_too_long"},
        **unavailable_docs("stt_unavailable"),
    },
)
async def transcribe(
    session_id: SessionId, body: TranscribeRequest, response: Response
) -> Transcript:
    """Speech to text for the input box; the client sends it itself (TM-07).

    stub — always the same Thai sentence
    """
    response.headers.update(stubs.HEADERS)
    return Transcript(text=_STUB_TRANSCRIPT)


@router.post(
    "/sessions/{id}/ocr/confirm",
    response_class=EventSourceResponse,
    responses={
        **_SSE_RESPONSE,
        409: {"model": ErrorResponse, "description": "no_pending_ocr"},
        422: {"model": ErrorResponse, "description": "Invalid body or ocr_lines_mismatch"},
        **RATE_LIMITED_DOCS,
    },
    dependencies=[Depends(chat_rate_limit)],
)
async def confirm_ocr(
    session_id: SessionId,
    body: OcrConfirmRequest,
    gateway: Annotated[Gateway, Depends(get_gateway)],
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    image_store: Annotated[ImageStore | None, Depends(get_image_store)],
    room_state: Annotated[RoomState, Depends(get_room_state)],
) -> Response:
    """Confirmed or edited lines of the last ocr_preview. SSE: verdict → token → done (AM-02).

    The checker of P2 checks the confirmed lines, then `explain_check` explains the result
    (photo-check-in-room.md §2.2). Until Storage exists it is a stub that checks the line count
    against the preview of the image message stub.
    """
    if image_store is None:
        stub_preview = dict(stubs.events("image_reply"))["ocr_preview"]
        if len(body.lines) != len(stub_preview["lines"]):
            return stubs.error(
                422, "ocr_lines_mismatch", f"send {len(stub_preview['lines'])} lines"
            )
        return stubs.stream("ocr_confirm")

    key = room_key(stubs.tenant_of(auth), str(session_id))
    # Taken out now, so a second confirm sent at the same time gets 409 (one confirm per
    # preview); confirm_events puts it back if no verdict comes (spec §2.2 items 5, 7).
    preview = await room_state.take_preview(key)
    if preview is None:
        return error_response(409, "no_pending_ocr", "No handwriting preview waits to be confirmed")
    if len(body.lines) != len(preview.lines):
        await room_state.restore_preview(key, preview)
        return error_response(422, "ocr_lines_mismatch", f"send {len(preview.lines)} lines")
    call_context = AICallContext(auth.tenant_id, auth.user_id) if auth else None
    return _sse(
        confirm_events(gateway, room_state, key, str(session_id), preview, body.lines, call_context)
    )
