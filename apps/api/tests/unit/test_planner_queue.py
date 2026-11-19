"""The planner's next topic (specs/features/planner/planner.md §2.3 · AC-6 to AC-13 · TM-01,
TM-02, SM-02). No literal thresholds: the mode is given, or built from config/learning.yaml.

Interface this file adds (built by /implement-feature), in app/domain/planner.py:
- `next_topic(topics, mode, current_topic_id) -> Choice` with `topic_id`, `reason_code`,
  `reason_topic_id`
"""

import dataclasses
import uuid

import pytest

from app.domain.planner import PlanFacts, PlanTopic, next_topic, plan
from app.settings import LearningConfig, get_settings


@pytest.fixture
def cfg() -> LearningConfig:
    return get_settings().learning


def tid(n: int) -> uuid.UUID:
    return uuid.UUID(int=n)


def topic(
    n: int,
    stars: int = 3,
    level: str = "not_started",
    mastery: float = 0.3,
    prereqs: tuple[int, ...] = (),
    order: int | None = None,
) -> PlanTopic:
    return PlanTopic(
        id=tid(n),
        name=f"หัวข้อ {n}",
        order_index=n if order is None else order,
        stars=stars,
        prereq_ids=tuple(tid(p) for p in prereqs),
        skills_total=1,
        skills_covered=0,
        level=level,
        mastery_eff=mastery,
    )


def picked(topics, mode="normal", current=None):
    choice = next_topic(topics, mode, None if current is None else tid(current))
    return choice.topic_id, choice.reason_code, choice.reason_topic_id


# --- AC-6 · the agreed order ---------------------------------------------------------------------


def test_TM01_normal_takes_the_next_topic_in_the_agreed_order():
    topics = [topic(1), topic(2), topic(3)]
    assert picked(topics) == (tid(1), "next_in_order", None)

    topics[0] = topic(1, level="passed")
    assert picked(topics)[:2] == (tid(2), "next_in_order")


def test_TM01_order_is_the_agreed_order_not_the_stars():
    # The demo rule took the most stars first; the planner follows order_index (spec §10 item 4).
    topics = [topic(1, stars=1), topic(2, stars=3)]
    assert picked(topics)[0] == tid(1)


# --- AC-7 · finish the open topic first ----------------------------------------------------------


def test_TM01_an_open_topic_from_the_last_session_comes_first():
    topics = [topic(1), topic(2), topic(3)]
    assert picked(topics, current=3) == (tid(3), "continue_topic", None)

    topics[2] = topic(3, level="passed")
    assert picked(topics, current=3)[:2] == (tid(1), "next_in_order")


def test_TM18_an_open_topic_the_mode_cuts_is_not_continued():
    topics = [topic(1, stars=3), topic(2, stars=1)]
    assert picked(topics, mode="triage", current=2)[0] == tid(1)


# --- AC-8 · tight ------------------------------------------------------------------------------


def test_TM18_tight_puts_one_star_topics_last():
    topics = [topic(1, stars=1), topic(2, stars=3)]
    assert picked(topics, mode="tight")[0] == tid(2)

    topics[1] = topic(2, stars=3, level="passed")
    assert picked(topics, mode="tight")[0] == tid(1)


# --- AC-9 · triage ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stars", "level", "chosen"),
    [
        (1, "not_started", False),
        (2, "developing", False),
        (2, "weak", True),
        (2, "not_started", True),
        (3, "developing", True),
    ],
)
def test_TM18_triage_keeps_three_stars_and_weak_two_stars(stars, level, chosen):
    # Topic 2 (★★★, later in order) keeps a candidate in the list, so a topic triage cuts
    # gives way to it instead of hitting the empty-candidates fallback (spec §2.3 item 6).
    topics = [topic(1, stars=stars, level=level), topic(2, stars=3)]
    topic_id, reason, _ = picked(topics, mode="triage")
    if chosen:
        assert (topic_id, reason) == (tid(1), "triage_focus")
    else:
        assert (topic_id, reason) == (tid(2), "triage_focus")


# --- AC-10 · final ----------------------------------------------------------------------------


def test_TM18_final_reviews_the_weakest_three_star_topic_even_if_passed():
    topics = [
        topic(1, stars=3, level="passed", mastery=0.6),
        topic(2, stars=3, level="passed", mastery=0.97),
        topic(3, stars=2, level="weak", mastery=0.2),
    ]
    assert picked(topics, mode="final") == (tid(1), "final_review", None)


# --- AC-11 · prerequisites first (SM-02) ---------------------------------------------------------


def test_SM02_a_prerequisite_not_passed_comes_first():
    # Topic 1 (order 1) needs topic 2 (order 2), which the order put later by mistake.
    topics = [topic(1, prereqs=(2,)), topic(2)]
    assert picked(topics) == (tid(2), "prerequisite_first", tid(1))


def test_SM02_prerequisites_are_followed_down_two_levels():
    topics = [topic(1, prereqs=(2,)), topic(2, prereqs=(3,)), topic(3)]
    assert picked(topics) == (tid(3), "prerequisite_first", tid(1))


def test_SM02_a_cut_prerequisite_does_not_block():
    topics = [topic(1, prereqs=(2,)), topic(2, stars=0)]
    assert picked(topics) == (tid(1), "next_in_order", None)


# --- AC-12 · nothing new to open ------------------------------------------------------------------


def test_TM01_all_passed_reviews_the_weakest_and_none_means_no_topic():
    topics = [topic(1, level="passed", mastery=0.97), topic(2, level="passed", mastery=0.8)]
    assert picked(topics)[:2] == (tid(2), "all_passed")

    assert picked([topic(1, stars=0)]) == (None, "no_topic", None)


# --- AC-13 · one topic, never the plan (TM-02) ----------------------------------------------------


def test_TM02_the_decision_names_one_topic_and_no_queue(cfg: LearningConfig):
    days = cfg.planner.triage_days_left + 30
    facts = PlanFacts(
        days_left=days, daily_minutes=None, minutes_per_problem=None, current_topic_id=None
    )

    decision = plan([topic(1), topic(2), topic(3)], facts, None, cfg)

    fields = {f.name for f in dataclasses.fields(decision)}
    assert fields == {
        "mode",
        "mode_changed",
        "need_minutes",
        "available_minutes",
        "ratio",
        "topic_id",
        "reason_code",
        "reason_topic_id",
    }
    assert decision.topic_id == tid(1)


def test_TM18_plan_uses_the_mode_it_chose(cfg: LearningConfig):
    # Few days left: triage, so a one-star topic first in order is skipped.
    facts = PlanFacts(
        days_left=cfg.planner.triage_days_left,
        daily_minutes=None,
        minutes_per_problem=None,
        current_topic_id=None,
    )

    decision = plan([topic(1, stars=1), topic(2, stars=3)], facts, None, cfg)

    assert (decision.mode, decision.topic_id, decision.reason_code) == (
        "triage",
        tid(2),
        "triage_focus",
    )
