"""Placeholder for the red run of /spec-to-tests (specs/features/planner/planner.md); built by
/implement-feature."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PlanTopic:
    id: UUID
    name: str
    order_index: int
    stars: int
    prereq_ids: tuple[UUID, ...]
    skills_total: int
    skills_covered: int
    level: str
    mastery_eff: float


@dataclass(frozen=True)
class PlanFacts:
    days_left: int
    daily_minutes: float | None
    minutes_per_problem: float | None
    current_topic_id: UUID | None


def problems_per_skill(cfg):  # type: ignore[no-untyped-def]
    raise NotImplementedError


def choose_mode(ratio, days_left, cfg):  # type: ignore[no-untyped-def]
    raise NotImplementedError


def next_topic(topics, mode, current_topic_id):  # type: ignore[no-untyped-def]
    raise NotImplementedError


def plan(topics, facts, previous_mode, cfg):  # type: ignore[no-untyped-def]
    raise NotImplementedError
