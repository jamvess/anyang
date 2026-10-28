"""Tests for the PoC-only parts of P3 that decide the numbers in the report.

    cd apps/api && uv run pytest ../../poc/P3 -q

stars(): the formula of ai-orchestration.md §2.3.5 / specs/features/scope/compute-importance.md
(AC-1..AC-8), written again here as throwaway PoC code. The real compute_importance is built
with the team in P8-lite (S4) and is not touched by P3.
match_topics(): pairs AI topics with label topics by overlapping PDF pages (Jam's choice).
"""

import pytest
from score import match_topics, page_set
from stars import Topic, stars

from app.settings import StarsConfig

CFG = StarsConfig(
    weight_same_instructor=1.0,
    weight_other_instructor=0.5,
    three_star_min_r=0.6,
    prerequisite_of_three_star_gets=2,
    no_past_exam_method="page_terciles",
)
SAME = {"m1": 1.0, "m2": 1.0}


def one(prereqs: list[str] | None = None, tid: str = "t1") -> Topic:
    return Topic(id=tid, prereqs=prereqs or [], excluded=False)


# --- stars (compute-importance.md AC-1..AC-8) ---------------------------------------------


@pytest.mark.parametrize(
    ("weights", "seen_in", "r", "expected"),
    [
        (SAME, {"m1", "m2"}, 1.0, 3),  # AC-1
        (SAME, {"m1"}, 0.5, 2),  # AC-2
        ({"m1": 1.0, "m2": 0.5}, {"m1"}, 2 / 3, 3),  # AC-3
        ({"m1": 1.0, "m2": 0.5}, {"m2"}, 1 / 3, 2),  # AC-4
    ],
)
def test_SM03_poc_stars_examples(weights, seen_in, r, expected):
    appearances = {("t1", exam) for exam in seen_in}
    result = stars([one()], weights, appearances, CFG)["t1"]
    assert result.signal_r == pytest.approx(r)
    assert result.importance == expected


def test_SM03_poc_direct_prerequisite_of_three_star_gets_two():  # AC-5, AC-6
    topics = [one(tid="A", prereqs=["B"]), one(tid="B", prereqs=["C"]), one(tid="C")]
    result = stars(topics, SAME, {("A", "m1"), ("A", "m2")}, CFG)
    assert (result["A"].importance, result["B"].importance, result["C"].importance) == (3, 2, 1)
    assert result["B"].reason == 'เป็นพื้นฐานของ "A"'


def test_SM03_poc_never_seen_gets_one():  # AC-7
    result = stars([one()], SAME, set(), CFG)["t1"]
    assert (result.importance, result.reason) == (1, "ไม่พบในข้อสอบเก่า")


def test_SM03_poc_excluded_gets_zero():  # AC-8
    topic = Topic(id="t1", prereqs=[], excluded=True)
    assert stars([topic], SAME, {("t1", "m1"), ("t1", "m2")}, CFG)["t1"].importance == 0


def test_SM03_poc_threshold_boundary_reads_config():  # AC-boundary, AC-config
    exactly = {("t1", "m1")}
    weights = {"m1": 0.6, "m2": 0.4}
    assert stars([one()], weights, exactly, CFG)["t1"].importance == 3
    stricter = CFG.model_copy(update={"three_star_min_r": 0.61})
    assert stars([one()], weights, exactly, stricter)["t1"].importance == 2


# --- page matching ---------------------------------------------------------------------------


def test_p3_page_set_expands_ranges_per_file():
    assert page_set(["sheet-01:2-4", "sheet-03:1-1"]) == {
        ("sheet-01", 2),
        ("sheet-01", 3),
        ("sheet-01", 4),
        ("sheet-03", 1),
    }


def test_p3_match_pairs_topics_with_most_overlap_one_to_one():
    ai = {"a1": ["sheet-01:1-10"], "a2": ["sheet-01:11-20"]}
    label = {"L1": ["sheet-01:2-10"], "L2": ["sheet-01:11-19"], "L3": ["sheet-01:30-40"]}

    pairs = match_topics(ai, label, min_iou=0.5)

    assert pairs == {"L1": "a1", "L2": "a2"}  # L3 has no AI topic


def test_p3_match_requires_min_iou():
    # One big AI topic covering two label topics: IoU with L1 = 4/10, with L2 = 6/10.
    ai = {"a1": ["sheet-01:1-10"]}
    label = {"L1": ["sheet-01:1-4"], "L2": ["sheet-01:5-10"]}

    assert match_topics(ai, label, min_iou=0.5) == {"L2": "a1"}
    assert match_topics(ai, label, min_iou=0.7) == {}


def test_p3_match_each_ai_topic_used_once():
    ai = {"a1": ["sheet-01:1-10"]}
    label = {"L1": ["sheet-01:1-9"], "L2": ["sheet-01:1-10"]}

    assert match_topics(ai, label, min_iou=0.5) == {"L2": "a1"}  # best pair wins
