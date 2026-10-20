"""Tutor room endpoints (specs/system/api.md v1.2 "ห้องติว").

Stubs until P4-lite: they serve fixture data from app/stubs/ and send `X-Stub: true`,
so May can wire the HTTP transport before the tutor turn exists. Shapes are checked
by tests/unit/test_room_api_contract.py, which the real endpoints must also pass.
"""

from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Path, Response
from sse_starlette import EventSourceResponse

from app import stubs
from app.models.error import ErrorResponse
from app.models.room import EVENT_MODELS, ActiveSession, Limits, Room, SendMessageRequest
from app.settings import get_settings

router = APIRouter(tags=["room"])

STUB_HEADERS = {"X-Stub": "true"}

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

    return EventSourceResponse(events(), headers=STUB_HEADERS)


@router.get("/exam-preps/{id}/sessions/active", responses=_ERRORS)
async def get_active_session(prep_id: PrepId, response: Response) -> ActiveSession:
    """Open session of this exam prep (TM-13); 404 `no_active_session` if none.

    stub — replaced in P4-lite
    """
    response.headers.update(STUB_HEADERS)
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
    response.headers.update(STUB_HEADERS)
    guards = get_settings().ai.guards
    limits = Limits(max_message_chars=guards.max_message_chars, max_image_mb=guards.max_image_mb)
    return Room.model_validate({**stubs.room(), "session_id": session_id, "limits": limits})


@router.post(
    "/sessions/{id}/messages",
    response_class=EventSourceResponse,
    responses=_SSE_RESPONSE,
)
async def send_message(session_id: SessionId, body: SendMessageRequest) -> EventSourceResponse:
    """Send `{text}` or `{image_path}`; the reply streams as SSE and ends with done.

    stub — replaced in P4-lite
    """
    return _stream("tutor_reply")
