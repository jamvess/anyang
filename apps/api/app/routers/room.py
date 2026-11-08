"""Tutor room endpoints (specs/system/api.md v1.2 "ห้องติว").

Stubs until P4-lite: they serve fixture data from app/stubs/ and send `X-Stub: true`,
so May can wire the HTTP transport before the tutor turn exists. Shapes are checked
by tests/unit/test_room_api_contract.py, which the real endpoints must also pass.

A text message is real since P4-lite: the reply streams from the gateway
(specs/features/tutor/tutor-reply-stream.md). An image message is still a stub, and so are
uploads, transcribe and ocr/confirm (api.md v1.7 · test_room_media_api_contract.py).
"""

from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Path, Response
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from app import stubs
from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway, get_gateway
from app.auth import AuthContext, get_auth
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
from app.services.photo_check import (
    NO_PENDING_PROBLEM,
    ImageStore,
    confirm_events,
    get_image_store,
    photo_events,
)
from app.services.room_state import RoomState, get_room_state
from app.services.tutor_turn import reply_events
from app.settings import get_settings

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


@router.get("/exam-preps/{id}/sessions/active", responses=_ERRORS)
async def get_active_session(prep_id: PrepId, response: Response) -> ActiveSession:
    """Open session of this exam prep (TM-13); 404 `no_active_session` if none.

    stub — replaced in P4-lite
    """
    response.headers.update(stubs.HEADERS)
    return ActiveSession(session_id=stubs.room()["session_id"])


@router.post(
    "/exam-preps/{id}/sessions",
    response_class=EventSourceResponse,
    responses=_SSE_RESPONSE,
)
async def create_session(prep_id: PrepId) -> EventSourceResponse:
    """Start a session. SSE: session → progress_card → token (opening) → problem → done.

    stub — replaced in P4-lite
    """
    return stubs.stream("session_start")


@router.get("/sessions/{id}", responses=_ERRORS)
async def get_session(session_id: SessionId, response: Response) -> Room:
    """Room data: header, input limits and messages (oldest first).

    stub — replaced in P4-lite
    """
    response.headers.update(stubs.HEADERS)
    guards = get_settings().ai.guards
    limits = Limits(max_message_chars=guards.max_message_chars, max_image_mb=guards.max_image_mb)
    return Room.model_validate({**stubs.room(), "session_id": session_id, "limits": limits})


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


@router.get("/sessions/{id}/messages", responses=_ERRORS)
async def list_messages(session_id: SessionId, response: Response) -> list[Message]:
    """Chat history, oldest first (TM-13). Not paged yet.

    stub — the messages of the room fixture
    """
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
    responses={**_SSE_RESPONSE, **RATE_LIMITED_DOCS},
    dependencies=[Depends(chat_rate_limit)],
)
async def send_message(
    session_id: SessionId,
    body: SendMessageRequest,
    gateway: Annotated[Gateway, Depends(get_gateway)],
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    image_store: Annotated[ImageStore | None, Depends(get_image_store)],
    room_state: Annotated[RoomState, Depends(get_room_state)],
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
    # No session_id yet: the session is a stub with no tutor_sessions row (api-auth.md §2.5).
    call_context = AICallContext(auth.tenant_id, auth.user_id) if auth else None
    if body.image_path is not None:
        if image_store is None:  # no Storage yet (photo-check-in-room.md §2.4)
            return stubs.stream("image_reply")
        return await _photo_message(
            str(session_id), body.image_path, auth, gateway, image_store, room_state, call_context
        )

    async def events() -> AsyncIterator[dict[str, str]]:
        # aclosing: a client that leaves closes the provider stream now (spec §2 Endpoint 8).
        async with aclosing(reply_events(gateway, body.text, call_context)) as replies:
            async for event, payload in replies:
                yield {"event": event, "data": payload.model_dump_json()}

    return EventSourceResponse(events())


def _sse(events: AsyncIterator[tuple[str, BaseModel]]) -> EventSourceResponse:
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
    auth: AuthContext | None,
    gateway: Gateway,
    image_store: ImageStore,
    room_state: RoomState,
    call_context: AICallContext | None,
) -> Response:
    """Checks before the SSE starts (photo-check-in-room.md §2.1 items 1-3)."""
    if not _own_upload(image_path, stubs.tenant_of(auth), session_id):
        return error_response(404, "not_found", "No such upload in this session")
    pending = await room_state.pending_problem(session_id)
    if pending is None:
        # UC-04 E9 before an intent router exists (spec §10 item 4 · proposal pending Junior).
        return _sse(_no_pending_problem())
    image = await image_store.read(image_path)
    if image is None:
        return error_response(404, "not_found", "No such upload in this session")
    max_mb = get_settings().ai.guards.max_image_mb
    if len(image.data) > max_mb * BYTES_PER_MB:  # the browser's size_bytes is checked again
        return error_response(422, "file_too_large", f"image is over {max_mb} MB")
    return _sse(photo_events(gateway, room_state, session_id, pending, image, call_context))


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
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> Any:
    """Signed upload URL for one image or audio file (TM-06, TM-07, TM-21).

    stub — the URL is not a real Storage URL until the endpoint talks to Supabase Storage
    """
    content_type = bare_content_type(body.content_type)
    if content_type not in UPLOAD_CONTENT_TYPES[body.kind]:
        return stubs.error(
            422, "unsupported_type", f"{body.content_type} is not an accepted {body.kind}"
        )
    max_mb = get_settings().ai.guards.max_image_mb
    if body.kind == "image" and body.size_bytes > max_mb * BYTES_PER_MB:
        return stubs.error(422, "file_too_large", f"image is over {max_mb} MB")
    response.headers.update(stubs.HEADERS)
    ext = content_type.split("/", 1)[1]
    path = f"{stubs.tenant_of(auth)}/sessions/{session_id}/{uuid4()}.{ext}"
    return UploadTicket(upload_url=f"{stubs.STORAGE_URL}/{path}", path=path)


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

    preview = await room_state.preview(str(session_id))
    if preview is None:
        return error_response(409, "no_pending_ocr", "No handwriting preview waits to be confirmed")
    if len(body.lines) != len(preview.lines):
        return error_response(422, "ocr_lines_mismatch", f"send {len(preview.lines)} lines")
    call_context = AICallContext(auth.tenant_id, auth.user_id) if auth else None
    return _sse(
        confirm_events(gateway, room_state, str(session_id), preview, body.lines, call_context)
    )
