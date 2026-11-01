"""API models of the tutor room (specs/system/api.md "ห้องติว" v1.2, uploads / transcribe /
ocr/confirm v1.7, and "SSE events").

Field names follow api.md, not the database columns: the router maps
`exam_preps.title` to `prep_name`, `profiles.nickname` to `user_name` and so on.
`extracted_text` and `intent` of `messages` stay inside the backend.

Difficulty 1-3 and the problem purposes repeat the check constraints of
`problems` in 0001_init.sql; they are schema rules, not learning-model thresholds.
The same holds for the progress card topics: stars 0-3 (`topics.importance`), level
(`topic_progress.level`, also `levels.show` in config/learning.yaml) and origin
(`topics.origin`). Verdict and error types come from app.domain.checker. Tests keep them in sync.
"""

from datetime import datetime
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from app.domain.checker import ErrorType, Verdict
from app.models.base import ApiModel

# --- REST ----------------------------------------------------------------------


class Limits(ApiModel):
    """Input limits from config/ai.yaml → guards. 1 MB = 1,048,576 bytes."""

    max_message_chars: int
    max_image_mb: int


class Message(ApiModel):
    id: str
    role: Literal["user", "tutor", "buddy", "card", "system"]
    content: str | None
    card: dict[str, Any] | None
    input_mode: Literal["text", "voice", "image"] | None
    attachment_path: str | None
    attachment_name: str | None  # display only, never part of the Storage path
    created_at: datetime


class Room(ApiModel):
    """Response of GET /sessions/{id}."""

    session_id: UUID
    prep_name: str
    days_left: int
    user_name: str
    tutor_name: str
    buddy_name: str | None
    limits: Limits
    messages: list[Message]


class ActiveSession(ApiModel):
    """Response of GET /exam-preps/{id}/sessions/active."""

    session_id: UUID


class SendMessageRequest(ApiModel):
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


class UploadRequest(ApiModel):
    """Body of POST /sessions/{id}/uploads (api.md v1.7). The router checks `content_type`
    against UPLOAD_CONTENT_TYPES and the image size against config/ai.yaml → guards."""

    kind: Literal["image", "audio"]
    content_type: str
    file_name: str = Field(min_length=1)  # display only (messages.attachment_name), never a path
    size_bytes: int = Field(ge=1)


# File types each kind accepts (api.md v1.7). audio/mp4 is what Safari on iOS records.
UPLOAD_CONTENT_TYPES: dict[str, frozenset[str]] = {
    "image": frozenset({"image/jpeg", "image/png", "image/webp", "image/heic"}),
    "audio": frozenset({"audio/webm", "audio/ogg", "audio/mp4"}),
}


class UploadTicket(ApiModel):
    """Response of POST /sessions/{id}/uploads: PUT the file to `upload_url`, then send `path`."""

    upload_url: str
    path: str


class TranscribeRequest(ApiModel):
    audio_path: str


class Transcript(ApiModel):
    """Response of POST /sessions/{id}/transcribe. Goes into the input box, never sent (TM-07)."""

    text: str


class OcrConfirmRequest(ApiModel):
    """Body of POST /sessions/{id}/ocr/confirm: every line in order, as many as the preview."""

    # A blank line cancels an edit on the card (ocr-confirm-card OQ 2), so none arrive here.
    lines: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]] = Field(
        min_length=1
    )


# --- SSE event payloads ----------------------------------------------------------


class SessionEvent(ApiModel):
    session_id: UUID


class TokenEvent(ApiModel):
    speaker: Literal["tutor", "buddy"]
    text: str


class ProgressTopic(ApiModel):
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


class ProgressCardEvent(ApiModel):
    days_left: int
    passed: int
    total: int
    readiness: float
    topics: list[ProgressTopic]


class ProblemEvent(ApiModel):
    """No reference answer: extra fields are rejected."""

    problem_id: str
    text_latex: str
    difficulty: int = Field(ge=1, le=3)
    purpose: Literal["probe", "verify", "practice", "review"]


class BuddyEvent(ApiModel):
    text: str


class DoneEvent(ApiModel):
    pass


class ErrorEvent(ApiModel):
    code: str
    message: str


class OcrLine(ApiModel):
    latex: str  # plain LaTeX without $ delimiters, like problem.text_latex
    confidence: float = Field(ge=0, le=1)


class OcrPreviewEvent(ApiModel):
    """An unreadable photo is a tutor token instead, so lines is never empty (AM-02)."""

    lines: list[OcrLine] = Field(min_length=1)


class VerdictEvent(ApiModel):
    """Merged checker result (specs/features/check/merge-rules.md)."""

    verdict: Verdict
    first_wrong_line: int | None = Field(ge=1)
    error_type: ErrorType | None

    @model_validator(mode="after")
    def _merge_rules(self) -> Self:
        # merge-rules.md §2: the combinations the checker can produce.
        line, error = self.first_wrong_line, self.error_type
        if self.verdict == "correct":
            ok = line is None and error is None  # rule 3
        elif self.verdict == "incomplete":
            ok = line is None and error == "concept"  # rule 5
        elif error == "no_answer":
            ok = self.verdict == "incorrect" and line is None  # rule 1
        else:
            ok = line is not None and error is not None  # rules 4 and 6
        if not ok:
            raise ValueError(f"{self.verdict} with line {line} and {error} breaks merge-rules.md")
        return self


EVENT_MODELS: dict[str, type[ApiModel]] = {
    "session": SessionEvent,
    "token": TokenEvent,
    "progress_card": ProgressCardEvent,
    "problem": ProblemEvent,
    "ocr_preview": OcrPreviewEvent,
    "verdict": VerdictEvent,
    "buddy": BuddyEvent,
    "done": DoneEvent,
    "error": ErrorEvent,
}
