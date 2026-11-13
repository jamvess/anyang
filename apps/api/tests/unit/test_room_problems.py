"""Choosing the topic, its reason, and the card text of a problem
(specs/features/tutor/room-problems-db.md §2.2 items 3-4, §10 item 4 · AC-2, AC-3).

Interfaces these tests expect (to be built by /implement-feature):
- `app.domain.room`: `TopicFacts(id, name, order_index, importance, status, origin)`,
  `choose_topic(topics, mastery, levels, p_init) -> TopicFacts | None` (mastery and levels by
  topic id; a topic missing from them is not started, at `p_init`), `focus_text(topic, level)`,
  `text_latex_of(text)`
"""

import uuid

import pytest

from app.domain.room import TopicFacts, choose_topic, focus_text, text_latex_of
from app.settings import get_settings

P_INIT = get_settings().learning.bkt.p_init


def topic(name: str, stars: int | None, order: int, status: str = "draft") -> TopicFacts:
    return TopicFacts(
        id=uuid.uuid4(), name=name, order_index=order, importance=stars, status=status, origin="doc"
    )


def test_TM01_more_stars_first():
    two, three = topic("แยกตัวประกอบ", 2, 1), topic("ลิมิต", 3, 2)

    assert choose_topic([two, three], {}, {}, P_INIT) == three


def test_TM01_same_stars_lower_mastery_first():
    a, b = topic("ลิมิต", 3, 1), topic("อนุพันธ์", 3, 2)

    assert choose_topic([a, b], {a.id: 0.6, b.id: 0.4}, {}, P_INIT) == b


@pytest.mark.parametrize(
    ("mastery_a", "chosen"),
    [
        pytest.param(P_INIT - 0.01, "a", id="started below p_init beats not started"),
        pytest.param(P_INIT, "a", id="tie on mastery: order_index"),
        pytest.param(P_INIT + 0.01, "b", id="not started (p_init) beats a higher mastery"),
    ],
)
def test_TM01_a_topic_not_started_counts_at_p_init(mastery_a, chosen):
    a, b = topic("ลิมิต", 3, 1), topic("อนุพันธ์", 3, 2)

    got = choose_topic([a, b], {a.id: mastery_a}, {}, P_INIT)

    assert got == {"a": a, "b": b}[chosen]


def test_TM01_zero_stars_and_excluded_are_never_chosen():
    zero = topic("ฟังก์ชัน", 0, 1)
    excluded = topic("ลำดับ", 3, 2, status="excluded")
    one = topic("ปริพันธ์", 1, 3)

    assert choose_topic([zero, excluded, one], {}, {}, P_INIT) == one


def test_TM01_passed_topics_are_skipped_until_all_are_passed():
    a, b = topic("ลิมิต", 3, 1), topic("อนุพันธ์", 2, 2)

    assert choose_topic([a, b], {a.id: 0.97}, {a.id: "passed"}, P_INIT) == b
    every = {a.id: "passed", b.id: "passed"}
    assert choose_topic([a, b], {a.id: 0.97, b.id: 0.96}, every, P_INIT) == b  # lowest mastery


def test_TM01_no_topic_with_a_star_chooses_none():
    assert choose_topic([topic("ฟังก์ชัน", 0, 1), topic("x", None, 2)], {}, {}, P_INIT) is None
    assert choose_topic([], {}, {}, P_INIT) is None


def test_TM02_the_reason_is_name_stars_and_level():
    # AC-3
    assert focus_text(topic("ลิมิต", 3, 1), "not_started") == "ลิมิต · 3 ดาว · ยังไม่เริ่ม"
    assert focus_text(topic("อนุพันธ์", 2, 2), "weak") == "อนุพันธ์ · 2 ดาว · อ่อน"


@pytest.mark.parametrize(
    ("text", "latex"),
    [
        (r"หาค่า $\lim_{x \to 2} x^2$", r"\text{หาค่า } \lim_{x \to 2} x^2"),
        (r"แยกตัวประกอบ $x^3-x$ ให้สุด", r"\text{แยกตัวประกอบ } x^3-x \text{ ให้สุด}"),
        ("ข้อนี้ไม่มีสมการ", r"\text{ข้อนี้ไม่มีสมการ}"),
    ],
)
def test_TM13_card_latex_from_the_stored_text(text, latex):
    # §10 item 4: problems has no text_latex column; a reused problem rebuilds it from text.
    assert text_latex_of(text) == latex
