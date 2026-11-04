"""Scope review endpoints (specs/system/api.md v1.6 "หน้าตรวจขอบเขต"), and ingestion progress,
scope chat and the change log (v1.11).

Stubs until ingestion and stars exist: they serve fixture data from app/stubs/ and send
`X-Stub: true`, so May can wire the scope page (specs/features/scope/scope-review.md) and
S11, S13, S14. Shapes are checked by tests/unit/test_scope_api_contract.py and
test_scope_edit_api_contract.py, which the real endpoints must also pass.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Response
from sse_starlette import EventSourceResponse

from app import stubs
from app.models.error import error_docs
from app.models.room import DoneEvent, ErrorEvent, TokenEvent
from app.models.scope import (
    Ingestion,
    Scope,
    ScopeChange,
    ScopeChatRequest,
    ScopeConfirmed,
    ScopePatchEvent,
    TopicSources,
)
from app.rate_limit import RATE_LIMITED_DOCS, chat_rate_limit
from app.settings import get_settings

router = APIRouter(tags=["scope"])

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
TopicId = Annotated[UUID, Path(alias="id")]


_STUB_VERSION_ID = UUID("6f1d2c3a-0000-4000-8000-0000000000c1")


@router.get("/exam-preps/{id}/scope", responses=error_docs(conflict="scope_not_ready"))
async def get_scope(prep_id: PrepId, response: Response) -> Scope:
    """Draft topics with stars and reasons, in API order (SM-02, SM-03), excluded topics included.

    stub — replaced when ingestion and compute_importance exist
    """
    response.headers.update(stubs.HEADERS)
    return Scope.model_validate(stubs.scope())


@router.get("/topics/{id}/sources", responses=error_docs())
async def get_topic_sources(topic_id: TopicId, response: Response) -> TopicSources:
    """Source pages and past exam questions of one topic (SM-04).

    stub — replaced when ingestion exists; every topic id gets the sources of the
    difference-of-squares topic (May's sources-t3.json)
    """
    response.headers.update(stubs.HEADERS)
    return TopicSources.model_validate(stubs.topic_sources())


@router.post(
    "/exam-preps/{id}/scope/confirm",
    responses=error_docs(conflict="scope_not_ready, scope_already_confirmed or scope_empty"),
)
async def confirm_scope(prep_id: PrepId, response: Response) -> ScopeConfirmed:
    """Lock the draft scope as a scope version (SM-09).

    stub — replaced when scope_versions are written
    """
    response.headers.update(stubs.HEADERS)
    return ScopeConfirmed(scope_version_id=_STUB_VERSION_ID, version=1)


# --- ingestion progress, scope chat, change log (api.md v1.11 · proposal pending Junior) ---


@router.get("/exam-preps/{id}/ingestion", responses=error_docs())
async def get_ingestion(prep_id: PrepId, response: Response) -> Ingestion:
    """Progress by file and by step; S11 polls until scope_ready, then opens S12 (CM-07).

    stub — always the same moment: one file running, one failed, topics not started. So
    scope_ready never turns true here; test the move to S12 with the web's own fixture.
    """
    response.headers.update(stubs.HEADERS)
    return Ingestion.model_validate(stubs.ingestion())


_CHAT_EVENTS = (ScopePatchEvent, TokenEvent, DoneEvent, ErrorEvent)
_CHAT_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "SSE stream: scope_patch (0 or more), then token, then done",
        "content": {
            "text/event-stream": {
                "schema": {
                    "oneOf": [
                        {"$ref": f"#/components/schemas/{model.__name__}"} for model in _CHAT_EVENTS
                    ]
                }
            }
        },
    },
    **error_docs("Invalid path or body, or message_too_long", "scope_not_ready"),
    **RATE_LIMITED_DOCS,
}


@router.post(
    "/exam-preps/{id}/scope/chat",
    response_class=EventSourceResponse,
    responses=_CHAT_RESPONSES,
    dependencies=[Depends(chat_rate_limit)],
)
async def scope_chat(prep_id: PrepId, body: ScopeChatRequest) -> Response:
    """Edit the draft scope by chat (SM-06, SM-07). Actions are checked before the reply.

    stub — always the same reply and patch; nothing is saved, so GET /scope does not change
    """
    max_chars = get_settings().ai.guards.max_message_chars
    if len(body.text) > max_chars:
        return stubs.error(422, "message_too_long", f"text is over {max_chars} characters")
    return stubs.stream("scope_chat")


@router.get("/exam-preps/{id}/scope/changes", responses=error_docs(conflict="scope_not_ready"))
async def list_scope_changes(prep_id: PrepId, response: Response) -> list[ScopeChange]:
    """What changed since the last confirmed version, oldest first, with reasons (SM-08).

    stub — the same two changes, whatever was sent to scope/chat
    """
    response.headers.update(stubs.HEADERS)
    return [ScopeChange.model_validate(c) for c in stubs.scope_changes()]
