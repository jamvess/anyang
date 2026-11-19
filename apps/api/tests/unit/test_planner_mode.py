"""The planner's mode (specs/features/planner/planner.md §2.2 · AC-1 to AC-5 · TM-18).

Every threshold comes from config/learning.yaml through get_settings(); boundaries are built
from those values. The only literal numbers are learning-model.md §6's reported range of
problems per skill (median 6, p90 15), used as a sanity band.

Interfaces these tests expect (built by /implement-feature), all in app/domain/planner.py:
- `PlanTopic(id, name, order_index, stars, prereq_ids, skills_total, skills_covered, level,
  mastery_eff)`, `PlanFacts(days_left, daily_minutes, minutes_per_problem, current_topic_id)`
- `problems_per_skill(cfg) -> float` (spec §10 item 1 (a): seeded simulation, the mean)
- `choose_mode(ratio: float | None, days_left: int, cfg) -> Mode`
- `plan(topics, facts, previous_mode, cfg) -> PlannerDecision`
"""

import uuid

import pytest

from app.domain.planner import PlanFacts, PlanTopic, choose_mode, plan, problems_per_skill
from app.settings import LearningConfig, get_settings

EPS = 1e-6


@pytest.fixture
def cfg() -> LearningConfig:
    return get_settings().learning


def topic(n: int, stars: int = 3, level: str = "not_started", total: int = 1, covered: int = 0):
    return PlanTopic(
        id=uuid.UUID(int=n),
        name=f"หัวข้อ {n}",
        order_index=n,
        stars=stars,
        prereq_ids=(),
        skills_total=total,
        skills_covered=covered,
        level=level,
        mastery_eff=0.3,
    )


def facts(days_left: int, daily: float | None = None, per_problem: float | None = None):
    return PlanFacts(
        days_left=days_left,
        daily_minutes=daily,
        minutes_per_problem=per_problem,
        current_topic_id=None,
    )


# --- AC-1 · need ------------------------------------------------------------------------------


def test_TM18_need_counts_open_skills_of_topics_not_passed(cfg: LearningConfig):
    p = cfg.planner
    pps = problems_per_skill(cfg)
    topics = [
        topic(1, stars=3, total=4, covered=1),  # 3 open skills
        topic(2, stars=2, total=0),  # no skill yet: counts as 1
        topic(3, stars=3, level="passed", total=5),  # passed: not counted
        topic(4, stars=0, total=5),  # cut: not counted
    ]
    days = p.triage_days_left + 30

    decision = plan(topics, facts(days), None, cfg)

    assert decision.need_minutes == pytest.approx((3 + 1) * pps * p.default_minutes_per_problem)
    assert decision.available_minutes == pytest.approx(days * p.default_daily_minutes)
    assert decision.ratio == pytest.approx(decision.need_minutes / decision.available_minutes)


def test_TM18_the_users_own_minutes_replace_the_defaults(cfg: LearningConfig):
    pps = problems_per_skill(cfg)
    days = cfg.planner.triage_days_left + 30

    decision = plan([topic(1, total=2)], facts(days, daily=30, per_problem=6), None, cfg)

    assert decision.need_minutes == pytest.approx(2 * pps * 6)
    assert decision.available_minutes == pytest.approx(days * 30)


# --- AC-2 · ratio boundaries ---------------------------------------------------------------------


def test_TM18_ratio_boundaries_pick_the_mode(cfg: LearningConfig):
    p = cfg.planner
    days = p.triage_days_left + 1  # far enough that the days alone do not mean triage
    cases = [
        (p.tight_ratio - EPS, "normal"),
        (p.tight_ratio, "normal"),
        (p.tight_ratio + EPS, "tight"),
        (p.triage_ratio, "tight"),
        (p.triage_ratio + EPS, "triage"),
    ]
    assert [choose_mode(r, days, cfg) for r, _ in cases] == [mode for _, mode in cases]


# --- AC-3 · day boundaries -----------------------------------------------------------------------


def test_TM18_day_boundaries_pick_the_mode(cfg: LearningConfig):
    p = cfg.planner
    low = p.tight_ratio / 2
    cases = [
        (p.triage_days_left + 1, "normal"),
        (p.triage_days_left, "triage"),
        (p.final_mode_days_left, "final"),
        (0, "final"),
    ]
    assert [choose_mode(low, d, cfg) for d, _ in cases] == [mode for _, mode in cases]


def test_TM18_no_time_left_is_final_whatever_the_ratio(cfg: LearningConfig):
    assert choose_mode(None, 0, cfg) == "final"


# --- AC-4 · telling the user once ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("previous", "changed"),
    [(None, False), ("normal", False), ("tight", True)],
    ids=["never-told", "same-mode", "new-mode"],
)
def test_TM18_mode_changed_only_when_a_told_mode_differs(cfg, previous, changed):
    days = cfg.planner.triage_days_left + 30  # one small topic: normal

    decision = plan([topic(1)], facts(days), previous, cfg)

    assert decision.mode == "normal"
    assert decision.mode_changed is changed


# --- AC-5 · problems per skill -------------------------------------------------------------------


def test_TM18_problems_per_skill_is_fixed_and_in_the_reported_range(cfg: LearningConfig):
    first = problems_per_skill(cfg)

    assert problems_per_skill(cfg) == first  # deterministic (seeded)
    assert 6 <= first <= 15  # learning-model.md §6: median 6, p90 15, mean 7.8


def test_TM18_faster_learning_needs_fewer_problems(cfg: LearningConfig):
    faster = cfg.model_copy(
        update={"bkt": cfg.bkt.model_copy(update={"p_transit": cfg.bkt.p_transit * 2})}
    )

    assert problems_per_skill(faster) < problems_per_skill(cfg)
