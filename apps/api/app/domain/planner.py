"""The planner: the study mode for the time left and the one topic to study next
(specs/features/planner/planner.md · ai-orchestration.md §2.5 · learning-model.md §6).

Code decides, the LLM speaks (CLAUDE.md rule 1): the planner returns a mode, a topic and a
``reason_code``; the tutor room turns the code into a sentence. Pure functions: every
threshold comes from ``cfg`` (config/learning.yaml); the caller reads the topics and stores the
decision.
"""

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal
from uuid import UUID

from app.domain.bkt import Level, Mode, update_mastery
from app.settings import BktConfig, LearningConfig

ReasonCode = Literal[
    "continue_topic",
    "next_in_order",
    "prerequisite_first",
    "triage_focus",
    "final_review",
    "all_passed",
    "no_topic",
]

# Constants of the simulation (spec §10 item 1 (a)), not thresholds of the learning model:
# learning-model.md §6 reports its numbers from 100,000 runs; a fixed seed makes the mean the
# same on every call. A simulated student who never reaches the threshold stops at the cap.
_SIM_METHOD = "bkt_simulation"  # the only value of planner.problems_per_skill built so far
_SIM_RUNS = 100_000
_SIM_SEED = 0
_SIM_MAX_PROBLEMS = 1_000


@dataclass(frozen=True)
class PlanTopic:
    id: UUID
    name: str
    order_index: int
    stars: int
    prereq_ids: tuple[UUID, ...]
    skills_total: int
    skills_covered: int
    level: Level
    mastery_eff: float


@dataclass(frozen=True)
class PlanFacts:
    days_left: int
    daily_minutes: float | None
    minutes_per_problem: float | None
    current_topic_id: UUID | None


@dataclass(frozen=True)
class Choice:
    topic_id: UUID | None
    reason_code: ReasonCode
    reason_topic_id: UUID | None = None


@dataclass(frozen=True)
class PlannerDecision:
    """One topic and why; never the whole queue (TM-02 · spec §2.4)."""

    mode: Mode
    mode_changed: bool
    need_minutes: float
    available_minutes: float
    ratio: float | None
    topic_id: UUID | None
    reason_code: ReasonCode
    reason_topic_id: UUID | None


# --- §2.2 · mode --------------------------------------------------------------------------------


def problems_per_skill(cfg: LearningConfig) -> float:
    """Mean problems a simulated student needs before BKT mastery reaches the threshold."""
    method = cfg.planner.problems_per_skill
    if method != _SIM_METHOD:
        raise ValueError(f"planner.problems_per_skill: unknown method {method!r}")
    return _simulate(cfg.bkt)


@lru_cache(maxsize=8)
def _simulate(bkt: BktConfig) -> float:
    """``BktConfig`` is frozen, so the cache key is its values."""
    rng = random.Random(_SIM_SEED)
    total = 0
    for _ in range(_SIM_RUNS):
        knows = rng.random() < bkt.p_init
        estimate = bkt.p_init
        problems = 0
        while estimate < bkt.mastery_threshold and problems < _SIM_MAX_PROBLEMS:
            correct = rng.random() < ((1 - bkt.p_slip) if knows else bkt.p_guess)
            estimate = update_mastery(estimate, correct, bkt)
            knows = knows or rng.random() < bkt.p_transit
            problems += 1
        total += problems
    return total / _SIM_RUNS


def choose_mode(ratio: float | None, days_left: int, cfg: LearningConfig) -> Mode:
    """Spec §2.2 item 5: the first rule that matches wins; ``ratio`` None = no time left."""
    p = cfg.planner
    if days_left <= p.final_mode_days_left:
        return "final"
    if days_left <= p.triage_days_left or (ratio is not None and ratio > p.triage_ratio):
        return "triage"
    if ratio is not None and ratio > p.tight_ratio:
        return "tight"
    return "normal"


def _need_minutes(topics: Sequence[PlanTopic], minutes_per_problem: float, pps: float) -> float:
    open_skills = sum(
        max(t.skills_total - t.skills_covered, 1)
        for t in topics
        if t.stars >= 1 and t.level != "passed"
    )
    return open_skills * pps * minutes_per_problem


# --- §2.3 · next topic --------------------------------------------------------------------------


def _candidates(topics: Sequence[PlanTopic], mode: Mode) -> list[PlanTopic]:
    """Spec §2.3 item 1, in study order."""
    ordered = sorted((t for t in topics if t.stars >= 1), key=lambda t: t.order_index)
    if mode == "tight":
        return [t for t in ordered if t.stars >= 2] + [t for t in ordered if t.stars == 1]
    if mode == "triage":
        return [
            t
            for t in ordered
            if t.stars >= 3 or (t.stars == 2 and t.level in ("not_started", "weak"))
        ]
    if mode == "final":
        return [t for t in ordered if t.stars >= 3]
    return ordered


def _prerequisite(chosen: PlanTopic, topics: Sequence[PlanTopic]) -> PlanTopic:
    """Spec §2.3 item 5: follow open prerequisites down to one whose own are all passed."""
    by_id = {t.id: t for t in topics}
    seen = {chosen.id}
    current = chosen
    while True:
        open_prereqs = [
            by_id[i]
            for i in current.prereq_ids
            if i in by_id and i not in seen and by_id[i].stars >= 1 and by_id[i].level != "passed"
        ]
        if not open_prereqs:
            return current
        current = min(open_prereqs, key=lambda t: t.order_index)
        seen.add(current.id)


def next_topic(topics: Sequence[PlanTopic], mode: Mode, current_topic_id: UUID | None) -> Choice:
    starred = [t for t in topics if t.stars >= 1]
    if not starred:
        return Choice(None, "no_topic")

    candidates = _candidates(topics, mode)
    if not candidates:  # the mode cuts every topic: normal's queue (spec §2.3 item 1)
        return next_topic(topics, "normal", current_topic_id)

    for t in candidates:
        if t.id == current_topic_id and t.level != "passed":
            return Choice(t.id, "continue_topic")

    if mode == "final":
        weakest = min(candidates, key=lambda t: (t.mastery_eff, t.order_index))
        return Choice(weakest.id, "final_review")

    first_open = next((t for t in candidates if t.level != "passed"), None)
    if first_open is not None:
        start = _prerequisite(first_open, topics)
        if start.id != first_open.id:
            return Choice(start.id, "prerequisite_first", first_open.id)
        return Choice(first_open.id, "triage_focus" if mode == "triage" else "next_in_order")

    weakest = min(candidates, key=lambda t: (t.mastery_eff, t.order_index))
    return Choice(weakest.id, "all_passed")


# --- §2.4 · the decision ------------------------------------------------------------------------


def plan(
    topics: Sequence[PlanTopic],
    facts: PlanFacts,
    previous_mode: Mode | None,
    cfg: LearningConfig,
) -> PlannerDecision:
    p = cfg.planner
    minutes_per_problem = (
        p.default_minutes_per_problem
        if facts.minutes_per_problem is None
        else facts.minutes_per_problem
    )
    daily = p.default_daily_minutes if facts.daily_minutes is None else facts.daily_minutes

    need = _need_minutes(topics, minutes_per_problem, problems_per_skill(cfg))
    available = facts.days_left * daily
    ratio = need / available if available > 0 else None
    # No time at all: work left is over every ratio, no work is under all (spec §2.2 item 4).
    mode_ratio = ratio if ratio is not None else (math.inf if need > 0 else 0.0)
    mode = choose_mode(mode_ratio, facts.days_left, cfg)
    choice = next_topic(topics, mode, facts.current_topic_id)

    return PlannerDecision(
        mode=mode,
        mode_changed=previous_mode is not None and previous_mode != mode,
        need_minutes=need,
        available_minutes=available,
        ratio=ratio,
        topic_id=choice.topic_id,
        reason_code=choice.reason_code,
        reason_topic_id=choice.reason_topic_id,
    )
