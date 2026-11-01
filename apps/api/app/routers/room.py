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
from fastapi.responses import JSONResponse
from sse_starlette import EventSourceResponse

from app import stubs
from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway, get_gateway
from app.auth import AuthContext, get_auth
from app.models.error import ErrorResponse, error_response
from app.models.room import (
    EVENT_MODELS,
    UPLOAD_CONTENT_TYPES,
    ActiveSession,
    Limits,
    OcrConfirmRequest,
    Room,
    SendMessageRequest,
    TranscribeRequest,
    Transcript,
    UploadRequest,
    UploadTicket,
)
from app.services.tutor_turn import reply_events
from app.settings import get_settings

router = APIRouter(tags=["room"])

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
SessionId = Annotated[UUID, Path(alias="id")]

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
                        for model in EVENT_MODELS.values()
                    ]
                }
            }
        },
    },
    **_ERRORS,
}


def _stream(name: str) -> EventSourceResponse:
    async def events() -> AsyncIterator[dict[str, str]]:
        for event, data in stubs.events(name):
            payload = EVENT_MODELS[event].model_validate(data)
            yield {"event": event, "data": payload.model_dump_json()}

    return EventSourceResponse(events(), headers=stubs.HEADERS)


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
    return _stream("session_start")


@router.get("/sessions/{id}", responses=_ERRORS)
async def get_session(session_id: SessionId, response: Response) -> Room:
    """Room data: header, input limits and messages (oldest first).

    stub — replaced in P4-lite
    """
    response.headers.update(stubs.HEADERS)
    guards = get_settings().ai.guards
    limits = Limits(max_message_chars=guards.max_message_chars, max_image_mb=guards.max_image_mb)
    return Room.model_validate({**stubs.room(), "session_id": session_id, "limits": limits})


@router.post(
    "/sessions/{id}/messages",
    response_class=EventSourceResponse,
    responses=_SSE_RESPONSE,
)
async def send_message(
    session_id: SessionId,
    body: SendMessageRequest,
    gateway: Annotated[Gateway, Depends(get_gateway)],
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> Response:
    """Send `{text}` or `{image_path}`; the reply streams as SSE and ends with done.

    `{text}` streams `tutor_reply` from the gateway (P4-lite). `{image_path}` is a stub that
    streams an `ocr_preview` to confirm with POST /sessions/{id}/ocr/confirm (api.md v1.7).
    """
    if body.text is None:
        return _stream("image_reply")
    max_chars = get_settings().ai.guards.max_message_chars
    if len(body.text) > max_chars:
        # Code proposed in tutor-reply-stream.md §10 item 3, pending Junior.
        return error_response(422, "message_too_long", f"text is over {max_chars} characters")

    # No session_id yet: the session is a stub with no tutor_sessions row (api-auth.md §2.5).
    call_context = AICallContext(auth.tenant_id, auth.user_id) if auth else None

    async def events() -> AsyncIterator[dict[str, str]]:
        # aclosing: a client that leaves closes the provider stream now (spec §2 Endpoint 8).
        async with aclosing(reply_events(gateway, body.text, call_context)) as replies:
            async for event, payload in replies:
                yield {"event": event, "data": payload.model_dump_json()}

    return EventSourceResponse(events())


# --- uploads, transcribe, ocr/confirm (api.md v1.7 · proposal pending Junior) -----

_BYTES_PER_MB = 1_048_576  # api.md: 1 MB = 1,048,576 bytes, same as Limits.max_image_mb
_STUB_TENANT = "00000000-0000-4000-8000-0000000000aa"
_STUB_TRANSCRIPT = "สองเอ็กซ์ลบห้า คูณ สองเอ็กซ์บวกห้า"  # voice-input.md §3 example


def _stub_error(status: int, code: str, message: str) -> JSONResponse:
    response = error_response(status, code, message)
    response.headers.update(stubs.HEADERS)
    return response


def _bare_type(content_type: str) -> str:
    """`audio/webm;codecs=opus` → `audio/webm`: browsers add codec parameters to MediaRecorder
    types and may use upper case (voice-input.md OQ 8)."""
    return content_type.split(";", 1)[0].strip().lower()


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
    content_type = _bare_type(body.content_type)
    if content_type not in UPLOAD_CONTENT_TYPES[body.kind]:
        return _stub_error(
            422, "unsupported_type", f"{body.content_type} is not an accepted {body.kind}"
        )
    max_mb = get_settings().ai.guards.max_image_mb
    if body.kind == "image" and body.size_bytes > max_mb * _BYTES_PER_MB:
        return _stub_error(422, "file_too_large", f"image is over {max_mb} MB")
    response.headers.update(stubs.HEADERS)
    # Storage paths start with the tenant (data-model.md); anonymous requests (AUTH_REQUIRED=false)
    # have none, so the stub uses a fixed one.
    tenant = auth.tenant_id if auth else _STUB_TENANT
    ext = content_type.split("/", 1)[1]
    path = f"{tenant}/sessions/{session_id}/{uuid4()}.{ext}"
    return UploadTicket(upload_url=f"https://stub.invalid/storage/{path}", path=path)


@router.post(
    "/sessions/{id}/transcribe",
    responses={
        **_ERRORS,
        422: {"model": ErrorResponse, "description": "Invalid body or audio_too_long"},
        # Replaces the 503 of AUTH_ERRORS on this route, so it names both causes.
        503: {
            "model": ErrorResponse,
            "description": "stt_unavailable, or auth_unavailable (Supabase Auth unreachable)",
        },
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
    },
)
async def confirm_ocr(session_id: SessionId, body: OcrConfirmRequest) -> Response:
    """Confirmed or edited lines of the last ocr_preview. SSE: verdict → token → done (AM-02).

    stub — checks the line count against the preview of the image message stub
    """
    preview = dict(stubs.events("image_reply"))["ocr_preview"]
    if len(body.lines) != len(preview["lines"]):
        return _stub_error(422, "ocr_lines_mismatch", f"send {len(preview['lines'])} lines")
    return _stream("ocr_confirm")
