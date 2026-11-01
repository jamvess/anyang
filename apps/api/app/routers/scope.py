"""Scope review endpoints (specs/system/api.md v1.6 "หน้าตรวจขอบเขต").

Stubs until ingestion and stars exist: they serve fixture data from app/stubs/ and send
`X-Stub: true`, so May can wire the scope page (specs/features/scope/scope-review.md).
Shapes are checked by tests/unit/test_scope_api_contract.py, which the real endpoints
must also pass.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Path, Response

from app import stubs
from app.models.error import ErrorResponse
from app.models.scope import Scope, ScopeConfirmed, TopicSources

router = APIRouter(tags=["scope"])

STUB_HEADERS = {"X-Stub": "true"}

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
TopicId = Annotated[UUID, Path(alias="id")]

# Documented error shape, so generated types match the envelope. 409 codes per api.md v1.6:
# scope_not_ready, scope_already_confirmed, scope_empty.
_ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Not found"},
    409: {"model": ErrorResponse, "description": "Scope not ready, already confirmed or empty"},
    422: {"model": ErrorResponse, "description": "Invalid path"},
}

_STUB_VERSION_ID = UUID("6f1d2c3a-0000-4000-8000-0000000000c1")


@router.get("/exam-preps/{id}/scope", responses=_ERRORS)
async def get_scope(prep_id: PrepId, response: Response) -> Scope:
    """Draft topics with stars and reasons, in API order (SM-02, SM-03), excluded topics included.

    stub — replaced when ingestion and compute_importance exist
    """
    response.headers.update(STUB_HEADERS)
    return Scope.model_validate(stubs.scope())


@router.get("/topics/{id}/sources", responses=_ERRORS)
async def get_topic_sources(topic_id: TopicId, response: Response) -> TopicSources:
    """Source pages and past exam questions of one topic (SM-04).

    stub — replaced when ingestion exists
    """
    response.headers.update(STUB_HEADERS)
    return TopicSources.model_validate(stubs.topic_sources())


@router.post("/exam-preps/{id}/scope/confirm", responses=_ERRORS)
async def confirm_scope(prep_id: PrepId, response: Response) -> ScopeConfirmed:
    """Lock the draft scope as a scope version (SM-09).

    stub — replaced when scope_versions are written
    """
    response.headers.update(STUB_HEADERS)
    return ScopeConfirmed(scope_version_id=_STUB_VERSION_ID, version=1)
