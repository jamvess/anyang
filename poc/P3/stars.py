"""Importance stars for PoC P3 (ai-orchestration.md §2.3.5, compute-importance.md §2).

Throwaway PoC code: the real compute_importance is built with the team in P8-lite (S4) at
apps/api/app/domain/stars.py. Every number comes from config/learning.yaml -> stars.
The no-past-exam rule (page terciles) is not needed for MTH10101, which has two past exams.
"""

from dataclasses import dataclass

import common  # noqa: F401  (puts apps/api on sys.path)

from app.settings import StarsConfig


@dataclass(frozen=True)
class Topic:
    id: str
    prereqs: list[str]
    excluded: bool
    name: str = ""


@dataclass(frozen=True)
class Importance:
    importance: int
    signal_r: float
    reason: str


def stars(
    topics: list[Topic],
    exam_weights: dict[str, float],
    appearances: set[tuple[str, str]],
    cfg: StarsConfig,
) -> dict[str, Importance]:
    """``appearances`` holds (topic_id, exam_id) when the exam has a question on the topic."""
    if not exam_weights:
        raise NotImplementedError("no past exam: page terciles are out of P3's scope")
    total = sum(exam_weights.values())
    signal = {
        t.id: sum(w for exam, w in exam_weights.items() if (t.id, exam) in appearances) / total
        for t in topics
    }
    seen_in = {t.id: sum(1 for exam in exam_weights if (t.id, exam) in appearances) for t in topics}
    three_star = {t.id for t in topics if not t.excluded and signal[t.id] >= cfg.three_star_min_r}

    result: dict[str, Importance] = {}
    for topic in topics:
        r = signal[topic.id]
        if topic.excluded:
            result[topic.id] = Importance(0, r, "ตัดออกตามที่แจ้ง")
        elif r > 0:
            reason = f"ออกในข้อสอบเก่า {seen_in[topic.id]} จาก {len(exam_weights)} ชุด"
            result[topic.id] = Importance(3 if topic.id in three_star else 2, r, reason)
        elif parents := [t for t in topics if topic.id in t.prereqs and t.id in three_star]:
            reason = f'เป็นพื้นฐานของ "{parents[0].name or parents[0].id}"'
            result[topic.id] = Importance(cfg.prerequisite_of_three_star_gets, r, reason)
        else:
            result[topic.id] = Importance(1, r, "ไม่พบในข้อสอบเก่า")
    return result
