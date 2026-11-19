"""Placeholder for the red run of /spec-to-tests (specs/features/tutor/stage-machine.md); built
by /implement-feature."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SkillState:
    id: UUID
    exam_freq: int
    independent_correct: int
    problems_today: int


@dataclass(frozen=True)
class TopicState:
    stage: str | None
    stars: int
    level: str
    skills: tuple[SkillState, ...]
    current_skill_id: UUID | None
    difficulty: int | None
    fail_streak: int


@dataclass(frozen=True)
class Start:
    user_new: bool


@dataclass(frozen=True)
class Answer:
    correct: bool
    error_type: str | None
    independent: bool


def next_step(state, event, mode, cfg):  # type: ignore[no-untyped-def]
    raise NotImplementedError
