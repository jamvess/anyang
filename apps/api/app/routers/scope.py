"""Scope review endpoints (specs/system/api.md v1.6 "หน้าตรวจขอบเขต"), and ingestion progress,
scope chat and the change log (v1.11).

Stubs until ingestion and stars exist: they serve fixture data from app/stubs/ and send
`X-Stub: true`, so May can wire the scope page (specs/features/scope/scope-review.md) and
S11, S13, S14. Shapes are checked by tests/unit/test_scope_api_contract.py and
test_scope_edit_api_contract.py, which the real endpoints must also pass.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sse_starlette import EventSourceResponse

from app import stubs
from app.auth import AuthContext, get_auth
from app.clock import get_now
from app.db.errors import DB_DOWN_MESSAGE, DbUnavailableError
from app.db.ingestion import IngestionReader, get_ingestion_reader
from app.db.scope import ScopeRepository, get_scope_repository
from app.domain.exam_prep import bangkok_today
from app.models.error import error_docs, error_response, too_long_message, unavailable_docs
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
from app.services import scope_db
from app.services.ingestion import ingestion_view

router = APIRouter(tags=["scope"])

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
TopicId = Annotated[UUID, Path(alias="id")]
Now = Annotated[datetime, Depends(get_now)]


_STUB_VERSION_ID = UUID("6f1d2c3a-0000-4000-8000-0000000000c1")


Repo = Annotated[ScopeRepository | None, Depends(get_scope_repository)]
_DB_DOWN = unavailable_docs("db_unavailable")


async def _with_db[T](work: Callable[[], T]) -> T | JSONResponse:
    """Run a scope service call in the thread pool; a refusal or a database failure becomes the
    error envelope of api.md (specs/features/scope/scope-db.md §2)."""
    try:
        return await run_in_threadpool(work)
    except scope_db.ScopeRefused as refused:
        return error_response(refused.status, refused.code, refused.message)
    except DbUnavailableError:
        return error_response(503, "db_unavailable", DB_DOWN_MESSAGE)


@router.get(
    "/exam-preps/{id}/scope",
    response_model=Scope,
    responses={**error_docs(conflict="scope_not_ready"), **_DB_DOWN},
)
async def get_scope(prep_id: PrepId, response: Response, repo: Repo, now: Now) -> Any:
    """Draft topics with stars and reasons, in API order (SM-02, SM-03), excluded topics included.

    With a token: the rows of the user's JWT (specs/features/scope/scope-db.md §2.1). Without
    one: the stub.
    """
    if repo is None:
        response.headers.update(stubs.HEADERS)
        return Scope.model_validate(stubs.scope())
    return await _with_db(lambda: scope_db.scope_of(repo, prep_id, bangkok_today(now)))


@router.get(
    "/topics/{id}/sources",
    response_model=TopicSources,
    responses={**error_docs(), **_DB_DOWN},
)
async def get_topic_sources(topic_id: TopicId, response: Response, repo: Repo) -> Any:
    """Source pages and past exam questions of one topic (SM-04).

    With a token: the pages of the topic's ranges and its questions (scope-db.md §2.2). Without
    one: the stub, the sources of the difference-of-squares topic for every id (May's
    sources-t3.json).
    """
    if repo is None:
        response.headers.update(stubs.HEADERS)
        return TopicSources.model_validate(stubs.topic_sources())
    return await _with_db(lambda: scope_db.sources_of(repo, topic_id))


@router.post(
    "/exam-preps/{id}/scope/confirm",
    response_model=ScopeConfirmed,
    responses={
        **error_docs(conflict="scope_not_ready, scope_already_confirmed or scope_empty"),
        **_DB_DOWN,
    },
)
async def confirm_scope(
    prep_id: PrepId,
    response: Response,
    repo: Repo,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    now: Now,
) -> Any:
    """Lock the draft scope as a scope version (SM-09).

    With a token: a `scope_versions` row, `active_scope_version_id`, draft topics confirmed
    (scope-db.md §2.3). Without one: the stub.
    """
    if repo is None or auth is None:
        response.headers.update(stubs.HEADERS)
        return ScopeConfirmed(scope_version_id=_STUB_VERSION_ID, version=1)
    return await _with_db(lambda: scope_db.confirm(repo, prep_id, auth.tenant_id, now))


# --- ingestion progress, scope chat, change log (api.md v1.11 · proposal pending Junior) ---


@router.get(
    "/exam-preps/{id}/ingestion",
    response_model=Ingestion,
    responses={**error_docs(), **unavailable_docs("db_unavailable")},
)
async def get_ingestion(
    prep_id: PrepId,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    reader: Annotated[IngestionReader | None, Depends(get_ingestion_reader)],
) -> Any:
    """Progress by file and by step; S11 polls until scope_ready, then opens S12 (CM-07).

    With a token: the rows the user's JWT can see (specs/features/scope/ingestion.md §2.6) ·
    another tenant's prep → 404. Without one (AUTH_REQUIRED=false): the stub, always the same
    moment (one file running, one failed, topics not started).
    """
    if auth is None or reader is None:
        response.headers.update(stubs.HEADERS)
        return Ingestion.model_validate(stubs.ingestion())
    try:
        snapshot = await run_in_threadpool(reader.snapshot, prep_id)
    except DbUnavailableError:
        return error_response(503, "db_unavailable", DB_DOWN_MESSAGE)
    if snapshot is None:
        return error_response(404, "not_found", "Not found")
    return ingestion_view(snapshot)


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
    if too_long := too_long_message(body.text):
        return stubs.error(422, "message_too_long", too_long)
    return stubs.stream("scope_chat")


@router.get("/exam-preps/{id}/scope/changes", responses=error_docs(conflict="scope_not_ready"))
async def list_scope_changes(prep_id: PrepId, response: Response) -> list[ScopeChange]:
    """What changed since the last confirmed version, oldest first, with reasons (SM-08).

    stub — the same two changes, whatever was sent to scope/chat
    """
    response.headers.update(stubs.HEADERS)
    return [ScopeChange.model_validate(c) for c in stubs.scope_changes()]
