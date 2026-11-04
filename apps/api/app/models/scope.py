"""API models of the scope review page (specs/system/api.md v1.6 "หน้าตรวจขอบเขต"), and of
ingestion progress, scope chat and the change log (v1.11).

Field names follow api.md, not the database columns: the router maps `exam_preps.title`
to `prep_name`, `topics.order_index` to `order`, `topics.importance` to `stars` and so on.
The shape is a proposal pending Junior (api.md "รอตัดสิน (v1.6 · Junior)", "(v1.11 · Junior)").

Stars 0-3 and origin repeat the check constraints of `topics` in 0001_init.sql; they are
schema rules, not learning-model thresholds. Excluded topics are sent with 0 stars.
The same holds for `ingestion_jobs.status` and for `scope_changes.op` and `.actor`.
"""

from datetime import datetime
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import (
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    StringConstraints,
    model_serializer,
    model_validator,
)

from app.models.base import ApiModel


class ScopeTopic(ApiModel):
    id: UUID
    order: int = Field(ge=1)  # topics.order_index, counted from 1
    name: str
    # Never null: until every topic has stars the endpoint answers 409 scope_not_ready.
    # 0 stars means excluded (ai-orchestration §2.3.5).
    stars: int = Field(ge=0, le=3)
    reason: str
    source_label: str  # ready to show; built by the backend from topic_sources
    origin: Literal["doc", "user"]


class PastQuestion(ApiModel):
    id: UUID
    label: str
    text: str  # math as $…$ (api.md Conventions)
    map_note: str | None


class Scope(ApiModel):
    """Response of GET /exam-preps/{id}/scope."""

    prep_name: str
    days_left: int
    status: Literal["draft", "confirmed"]
    topics: list[ScopeTopic]
    unmapped_questions: list[PastQuestion]


class SourceExcerpt(ApiModel):
    material_name: str
    page: int = Field(ge=1)  # material_pages.page_no, the PDF page number
    text: str


class TopicSources(ApiModel):
    """Response of GET /topics/{id}/sources."""

    excerpts: list[SourceExcerpt]
    questions: list[PastQuestion]


class ScopeConfirmed(ApiModel):
    """Response of POST /exam-preps/{id}/scope/confirm."""

    scope_version_id: UUID
    version: int = Field(ge=1)


# --- ingestion progress (api.md v1.11) -------------------------------------------


class IngestionFile(ApiModel):
    material_id: UUID
    file_name: str
    status: Literal["queued", "running", "done", "failed"]  # values of ingestion_jobs.status
    detail: str | None  # ready to show, e.g. "14 หน้า"; built by the backend
    error: str | None  # short text the user may see, when status is failed (UC-02 E5)


class IngestionStep(ApiModel):
    label: str  # ready to show, e.g. "หาหัวข้อและลำดับการเรียน"; built by the backend
    status: Literal["pending", "running", "done"]


class Ingestion(ApiModel):
    """Response of GET /exam-preps/{id}/ingestion."""

    scope_ready: bool  # GET /exam-preps/{id}/scope no longer answers 409 scope_not_ready
    files: list[IngestionFile]
    steps: list[IngestionStep]


# --- scope chat (api.md v1.11) ------------------------------------------------------


class ScopeChatRequest(ApiModel):
    """Body of POST /exam-preps/{id}/scope/chat. The endpoint checks the length against
    config/ai.yaml → guards.max_message_chars."""

    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _left_out_not_null(schema: dict[str, Any]) -> None:
    """OpenAPI as the wire is: a field that did not change is absent, never null, so generated
    types read `stars?: number` instead of a required `stars: number | null`."""
    for field in schema["properties"].values():
        del field["default"]
        field.update(field.pop("anyOf")[0])


class ScopePatchChanges(ApiModel):
    """The fields of a ScopeTopic that changed; the web merges them into the card, so the ones
    left out are not sent at all (a null would overwrite the card)."""

    model_config = ConfigDict(json_schema_extra=_left_out_not_null)

    order: int | None = Field(default=None, ge=1)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = None
    stars: int | None = Field(default=None, ge=0, le=3)
    reason: str | None = None
    source_label: str | None = None
    origin: Literal["doc", "user"] | None = None

    # No return annotation: with one, OpenAPI would show `changes` as a bare object, without fields.
    @model_serializer(mode="wrap")
    def _only_changed(self, handler: SerializerFunctionWrapHandler):
        return {field: value for field, value in handler(self).items() if value is not None}

    @model_validator(mode="after")
    def _real_changes_only(self) -> Self:
        sent = self.model_fields_set
        if not sent or any(getattr(self, field) is None for field in sent):
            raise ValueError("changes needs at least one field, and none of them null")
        return self


class ScopePatchEvent(ApiModel):
    """SSE event `scope_patch`. An unknown topic_id is a new card (op add_topic)."""

    topic_id: UUID
    changes: ScopePatchChanges


# --- change log (api.md v1.11) -------------------------------------------------------


class ScopeChange(ApiModel):
    """Each row of GET /exam-preps/{id}/scope/changes. Rows without a topic are not sent."""

    id: UUID
    topic_id: UUID
    topic_name: str
    op: Literal[
        "set_importance",
        "exclude",
        "include",
        "rename",
        "reorder",
        "add_topic",
        "exclude_skill",
        "include_skill",
    ]
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None
    actor: Literal["user", "ai", "system"]
    created_at: datetime
