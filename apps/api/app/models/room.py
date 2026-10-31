"""API models of the tutor room (specs/system/api.md v1.2 "ห้องติว" and "SSE events").

Field names follow api.md, not the database columns: the router maps
`exam_preps.title` to `prep_name`, `profiles.nickname` to `user_name` and so on.
`extracted_text` and `intent` of `messages` stay inside the backend.

Difficulty 1-3 and the problem purposes repeat the check constraints of
`problems` in 0001_init.sql; they are schema rules, not learning-model thresholds.
The same holds for the progress card topics: stars 0-3 (`topics.importance`), level
(`topic_progress.level`, also `levels.show` in config/learning.yaml) and origin
(`topics.origin`). Tests keep them in sync.
"""

from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Api(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- REST ----------------------------------------------------------------------


class Limits(_Api):
    """Input limits from config/ai.yaml → guards. 1 MB = 1,048,576 bytes."""

    max_message_chars: int
    max_image_mb: int


class Message(_Api):
    id: str
    role: Literal["user", "tutor", "buddy", "card", "system"]
    content: str | None
    card: dict[str, Any] | None
    input_mode: Literal["text", "voice", "image"] | None
    attachment_path: str | None
    attachment_name: str | None  # display only, never part of the Storage path
    created_at: datetime


class Room(_Api):
    """Response of GET /sessions/{id}."""

    session_id: UUID
    prep_name: str
    days_left: int
    user_name: str
    tutor_name: str
    buddy_name: str | None
    limits: Limits
    messages: list[Message]


class ActiveSession(_Api):
    """Response of GET /exam-preps/{id}/sessions/active."""

    session_id: UUID


class SendMessageRequest(_Api):
    """Body of POST /sessions/{id}/messages: exactly one of `text` or `image_path`.

    api.md "รอตัดสิน" item 1 (Jam) may allow both; change this with the spec.
    """

    text: str | None = None
    image_path: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if (self.text is None) == (self.image_path is None):
            raise ValueError("send exactly one of text or image_path")
        if self.text is not None and not self.text.strip():
            # Blank text is no message: never a billed tutor_reply call (tutor-reply-stream AC-21).
            raise ValueError("text is empty")
        return self


# --- SSE event payloads ----------------------------------------------------------


class SessionEvent(_Api):
    session_id: UUID


class TokenEvent(_Api):
    speaker: Literal["tutor", "buddy"]
    text: str


class ProgressTopic(_Api):
    """One row of progress_card.topics (api.md v1.4).

    `stars` is never null: topics whose importance is not computed yet are left out.
    """

    id: str
    name: str
    # 0-3 as in the DB until api.md "รอตัดสิน" item 4 decides whether 0-star topics show.
    stars: int = Field(ge=0, le=3)
    level: Literal["not_started", "weak", "developing", "passed"]
    review_due: bool
    origin: Literal["doc", "user"]


class ProgressCardEvent(_Api):
    days_left: int
    passed: int
    total: int
    readiness: float
    topics: list[ProgressTopic]


class ProblemEvent(_Api):
    """No reference answer: extra fields are rejected."""

    problem_id: str
    text_latex: str
    difficulty: int = Field(ge=1, le=3)
    purpose: Literal["probe", "verify", "practice", "review"]


class BuddyEvent(_Api):
    text: str


class DoneEvent(_Api):
    pass


class ErrorEvent(_Api):
    code: str
    message: str


EVENT_MODELS: dict[str, type[_Api]] = {
    "session": SessionEvent,
    "token": TokenEvent,
    "progress_card": ProgressCardEvent,
    "problem": ProblemEvent,
    "buddy": BuddyEvent,
    "done": DoneEvent,
    "error": ErrorEvent,
}
