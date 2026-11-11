"""Pure rules of an exam prep (specs/features/exam-prep/create-exam-prep.md §2.3, §2.4 ·
api.md v1.14 `ExamPrep`). No I/O: the repository collects the facts, these functions decide.

The statuses below repeat the check constraint of `materials.status` (0001_init.sql); they are
schema values, not learning-model thresholds.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

Stage = Literal["materials", "processing", "scope", "tutoring"]

# api.md: days are counted in Asia/Bangkok, which has no DST.
BANGKOK = timezone(timedelta(hours=7))

# A confirmed file in one of these statuses is still being read or needs a retry, so the scope
# is not ready yet (api.md `Ingestion.scope_ready`).
_NOT_READ_YET = frozenset({"confirmed", "ingesting", "failed"})


@dataclass(frozen=True)
class MaterialFacts:
    kind_confirmed: bool
    status: str


def bangkok_today(now: datetime) -> date:
    """The calendar date in Bangkok at the aware instant ``now``."""
    return now.astimezone(BANGKOK).date()


def days_left(exam_date: date, *, today: date) -> int:
    """CM-02. Negative once the exam is over."""
    return (exam_date - today).days


def prep_stage(
    *,
    has_active_scope: bool,
    topic_importances: Sequence[int | None],
    materials: Sequence[MaterialFacts],
) -> Stage:
    """Where the prep card leads: the first rule that matches, in this order (§2.4)."""
    if has_active_scope:
        return "tutoring"
    confirmed = [m for m in materials if m.kind_confirmed]
    # No topics at all is not ready (Junior 2026-11-11). Jam revisits this at ingestion.
    scope_ready = (
        bool(topic_importances)
        and all(importance is not None for importance in topic_importances)
        and not any(m.status in _NOT_READ_YET for m in confirmed)
    )
    if scope_ready:
        return "scope"
    if confirmed:
        return "processing"
    return "materials"
