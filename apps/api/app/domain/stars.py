"""Topic importance: stars 0-3 and signal_r (specs/features/scope/compute-importance.md).

Code gives the stars, not the AI (CLAUDE.md rule 1): the inputs are the topics, the past
exams and which topic each exam question was mapped to (A6, A7). Every number comes from
``cfg`` (config/learning.yaml -> stars). Pure function: no database, no network, no file;
the caller turns DB rows into inputs and writes the result to ``topics`` (spec §2, §9).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from app.settings import StarsConfig

REASON_EXCLUDED = "ตัดออกตามที่แจ้ง"
REASON_NOT_SEEN = "ไม่พบในข้อสอบเก่า"
REASON_ONLY_ZERO_WEIGHT = "พบเฉพาะในข้อสอบที่ไม่ได้ใช้คิดดาว"
REASON_NO_PAST_EXAM = "ไม่มีข้อสอบเก่า จึงประเมินจากจำนวนหน้าในชีท"

THREE_STARS = 3
TWO_STARS = 2
ONE_STAR = 1
ZERO_STARS = 0


@dataclass(frozen=True)
class TopicIn:
    """One topic, in ``order_index`` order. ``page_count`` is the number of distinct pages in
    the A6 ``sources`` of the topic (spec §2 "ผู้เรียก")."""

    id: str
    name: str
    prereq_ids: Sequence[str]
    excluded: bool
    importance_source: Literal["computed", "user"]
    current_importance: int | None
    current_reason: str | None
    page_count: int


@dataclass(frozen=True)
class ExamIn:
    """A past exam (a material) and its ``relevance_weight``."""

    material_id: str
    weight: float


@dataclass(frozen=True)
class TopicImportance:
    topic_id: str
    importance: int
    signal_r: float
    reason: str | None  # None only when a user-set topic had no reason (kept as it was)


def compute_importance(
    topics: Sequence[TopicIn],
    exams: Sequence[ExamIn],
    appearances: set[tuple[str, str]],
    cfg: StarsConfig,
) -> list[TopicImportance]:
    """Stars and signal_r of every topic, in input order.

    ``appearances`` holds (topic_id, material_id) when the exam has at least one question
    mapped to the topic. Exams of weight 0 do not count as past exams (spec §2 step 1).
    """
    counted = {e.material_id: e.weight for e in exams if e.weight > 0}
    if not counted:
        # cfg.no_past_exam_method has one allowed value, page_terciles (checked at config load).
        return _from_page_terciles(topics)
    not_counted = {e.material_id for e in exams} - counted.keys()
    return _from_past_exams(topics, counted, not_counted, appearances, cfg)


def _fixed(topic: TopicIn) -> tuple[int, str | None] | None:
    """Rules 1-2 of both modes: excluded → 0; stars the user set → kept as they are."""
    if topic.excluded:
        return ZERO_STARS, REASON_EXCLUDED
    if topic.importance_source == "user" and topic.current_importance is not None:
        return topic.current_importance, topic.current_reason
    return None


def _from_page_terciles(topics: Sequence[TopicIn]) -> list[TopicImportance]:
    """Spec §2 step 3: no past exam, so stars come from the page-count rank (no prerequisite
    rule) and signal_r is the page share of every topic, excluded ones included."""
    total_pages = sum(t.page_count for t in topics)
    ranked = [t for t in topics if not t.excluded]  # user-set topics take a rank too
    n = len(ranked)
    pages_equal = len({t.page_count for t in ranked}) <= 1

    results = []
    for topic in topics:
        signal_r = topic.page_count / total_pages if total_pages else 0.0
        if fixed := _fixed(topic):
            stars, reason = fixed
        else:
            reason = REASON_NO_PAST_EXAM
            if pages_equal:
                # Page counts say nothing when they are all the same (spec §10 item 6).
                stars = TWO_STARS
            else:
                # Ties share the rank of the first topic of their group, starting at 0.
                k = sum(1 for t in ranked if t.page_count > topic.page_count)
                # k < n/3 and k < 2n/3, in integers.
                stars = THREE_STARS if 3 * k < n else TWO_STARS if 3 * k < 2 * n else ONE_STAR
        results.append(TopicImportance(topic.id, stars, signal_r, reason))
    return results


def _from_past_exams(
    topics: Sequence[TopicIn],
    weights: dict[str, float],
    zero_weight: set[str],
    appearances: set[tuple[str, str]],
    cfg: StarsConfig,
) -> list[TopicImportance]:
    """Spec §2 step 2: the first rule that matches gives the stars. ``weights`` holds only the
    exams that count (weight > 0); ``zero_weight`` the ones that do not."""
    seen_in: dict[str, set[str]] = {}
    for topic_id, material_id in appearances:
        seen_in.setdefault(topic_id, set()).add(material_id)
    total_weight = sum(weights.values())

    signal: dict[str, float] = {}
    n_in: dict[str, int] = {}
    for topic in topics:
        counted = seen_in.get(topic.id, set()) & weights.keys()
        signal[topic.id] = sum(weights[m] for m in counted) / total_weight
        n_in[topic.id] = len(counted)

    # Rules 1-4, which do not depend on other topics.
    decided: dict[str, tuple[int, str | None]] = {}
    for topic in topics:
        r = signal[topic.id]
        if fixed := _fixed(topic):
            decided[topic.id] = fixed
        elif r >= cfg.three_star_min_r:
            decided[topic.id] = (THREE_STARS, _seen_reason(n_in[topic.id], len(weights)))
        elif r > 0:
            decided[topic.id] = (TWO_STARS, _seen_reason(n_in[topic.id], len(weights)))

    # Rule 5: final ★★★ (computed or user-set) of a topic that is not excluded lifts its
    # direct prerequisites; the first such topic in input order names the reason.
    # An excluded topic already has 0 stars (rule 1), so it is never in this list.
    three_star = [t for t in topics if t.id in decided and decided[t.id][0] == THREE_STARS]
    results = []
    for topic in topics:
        if topic.id in decided:
            stars, reason = decided[topic.id]
        elif parent := next((t for t in three_star if topic.id in t.prereq_ids), None):
            stars, reason = cfg.prerequisite_of_three_star_gets, f'เป็นพื้นฐานของ "{parent.name}"'
        elif seen_in.get(topic.id, set()) & zero_weight:
            # Rule 6: only in exams of weight 0; the user saw those exams, so not "not found".
            stars, reason = ONE_STAR, REASON_ONLY_ZERO_WEIGHT
        else:
            stars, reason = ONE_STAR, REASON_NOT_SEEN
        results.append(TopicImportance(topic.id, stars, signal[topic.id], reason))
    return results


def _seen_reason(n_in: int, n_total: int) -> str:
    return f"ออกในข้อสอบเก่า {n_in} จาก {n_total} ชุด"
