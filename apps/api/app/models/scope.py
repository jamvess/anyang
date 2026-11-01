"""API models of the scope review page (specs/system/api.md v1.6 "หน้าตรวจขอบเขต").

Field names follow api.md, not the database columns: the router maps `exam_preps.title`
to `prep_name`, `topics.order_index` to `order`, `topics.importance` to `stars` and so on.
The shape is a proposal pending Junior (api.md "รอตัดสิน (v1.6 · Junior)").

Stars 0-3 and origin repeat the check constraints of `topics` in 0001_init.sql; they are
schema rules, not learning-model thresholds. Excluded topics are sent with 0 stars.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _Api(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScopeTopic(_Api):
    id: UUID
    order: int = Field(ge=1)  # topics.order_index, counted from 1
    name: str
    # Never null: topics whose importance is not computed yet are not sent.
    stars: int = Field(ge=0, le=3)
    reason: str
    source_label: str  # ready to show; built by the backend from topic_sources
    origin: Literal["doc", "user"]


class PastQuestion(_Api):
    id: UUID
    label: str
    text: str  # math as $…$ (api.md Conventions)
    map_note: str | None


class Scope(_Api):
    """Response of GET /exam-preps/{id}/scope."""

    prep_name: str
    days_left: int
    status: Literal["draft", "confirmed"]
    topics: list[ScopeTopic]
    unmapped_questions: list[PastQuestion]


class SourceExcerpt(_Api):
    material_name: str
    page: int
    text: str


class TopicSources(_Api):
    """Response of GET /topics/{id}/sources."""

    excerpts: list[SourceExcerpt]
    questions: list[PastQuestion]


class ScopeConfirmed(_Api):
    """Response of POST /exam-preps/{id}/scope/confirm."""

    scope_version_id: UUID
    version: int
