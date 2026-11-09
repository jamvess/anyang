"""The room state of the local demo (specs/features/tutor/demo-room.md §2 B, D).

Five problems in a fixed order (problems from evals/answers, each with a handwritten photo
right and wrong), the next one after every explained verdict, back to the first after the last.
Each answer updates the BKT mastery of its topic (app/domain/bkt.py), and the progress card is
built from it. Not a planner: no stage machine, no Verify of the same skill (spec §10 item 2).
"""

from dataclasses import dataclass

from app import stubs
from app.domain.bkt import (
    ReadinessTopic,
    TopicProgress,
    level,
    mastery_eff,
    readiness,
    record_attempt,
    target_difficulty,
)
from app.models.room import ProgressCardEvent, ProgressTopic
from app.services.checker import CheckProblem
from app.services.room_state import STUB_PROBLEM, InMemoryRoomState, PendingProblem
from app.settings import get_settings

# No planner yet, so the mode never changes (bkt-mastery.md §10 item 2).
MODE = "normal"
# Exam level, so a topic can reach `passed` in the demo (spec §3).
DIFFICULTY = 3


@dataclass(frozen=True)
class DemoTopic:
    """Stars and signal_r set for the demo (spec §3); real ones come from compute_importance."""

    topic_id: str
    name: str
    stars: int
    signal_r: float


DEMO_TOPICS = (
    DemoTopic("t-factor", "การแยกตัวประกอบ", 2, 0.5),
    DemoTopic("t-limit", "ลิมิต", 3, 1.0),
    DemoTopic("t-derivative", "อนุพันธ์", 3, 1.0),
)


def _problem(
    problem_id: str, topic_id: str, text: str, text_latex: str, answer_format: str, reference: str
) -> PendingProblem:
    return PendingProblem(
        problem_id=problem_id,
        problem=CheckProblem(
            text=text,
            reference_answer=reference,
            answer_format=answer_format,  # type: ignore[arg-type]
            solution_steps=[],
        ),
        text_latex=text_latex,
        difficulty=DIFFICULTY,
        topic_id=topic_id,
    )


DEMO_PROBLEMS = (
    # p1 is the problem the opening card of session_start.sse already shows.
    PendingProblem(
        problem_id=STUB_PROBLEM.problem_id,
        problem=STUB_PROBLEM.problem,
        text_latex=STUB_PROBLEM.text_latex,
        difficulty=DIFFICULTY,
        topic_id="t-factor",
    ),
    _problem(
        "demo-2",
        "t-limit",
        r"หาค่า $\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}$",
        r"\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}",
        "expression",
        "4",
    ),
    _problem(
        "demo-3",
        "t-derivative",
        r"หา $\frac{d}{dx}\left(x^{2}\sin(x)\right)$",
        r"\frac{d}{dx}\left(x^{2}\sin(x)\right)",
        "expression",
        r"2x\sin(x)+x^{2}\cos(x)",
    ),
    _problem(
        "demo-4",
        "t-derivative",
        r"ให้ $f(x)=x^{4}-3x^{2}+2x$ หา $f''(x)$",
        r"f(x)=x^{4}-3x^{2}+2x \text{ หา } f''(x)",
        "expression",
        r"12x^{2}-6",
    ),
    _problem(
        "demo-5",
        "t-factor",
        r"แยกตัวประกอบ $x^{3}-x$",
        r"\text{แยกตัวประกอบ } x^{3}-x",
        "factored",
        r"x(x-1)(x+1)",
    ),
)


class DemoRoomState(InMemoryRoomState):
    def __init__(self) -> None:
        super().__init__()
        self._index: dict[str, int] = {}
        self._progress: dict[str, dict[str, TopicProgress]] = {}

    async def pending_problem(self, key: str) -> PendingProblem | None:
        return DEMO_PROBLEMS[self._index.get(key, 0)]

    async def start_session(self, key: str) -> None:
        """Every opening starts the demo again (the stub session id never changes)."""
        await super().start_session(key)
        self._index.pop(key, None)
        self._progress.pop(key, None)

    async def record_check(self, key: str, pending: PendingProblem, is_correct: bool) -> None:
        if pending.topic_id is None:
            return
        cfg = get_settings().learning
        topics = self._progress.setdefault(key, {})
        before = topics.get(pending.topic_id, TopicProgress(cfg.bkt.p_init, 0, 0))
        # The next demo problem is never the one the tutor just worked: independent.
        topics[pending.topic_id] = record_attempt(before, is_correct, pending.difficulty, True, cfg)

    async def next_problem(self, key: str) -> PendingProblem | None:
        self._index[key] = (self._index.get(key, 0) + 1) % len(DEMO_PROBLEMS)
        return DEMO_PROBLEMS[self._index[key]]

    async def progress_card(self, key: str) -> ProgressCardEvent | None:
        cfg = get_settings().learning
        progress = self._progress.get(key, {})
        rows, weights, passed = [], [], 0
        for topic in DEMO_TOPICS:
            state = progress.get(topic.topic_id, TopicProgress(cfg.bkt.p_init, 0, 0))
            d_target = target_difficulty(topic.stars, MODE, cfg)
            # Every skill counts as covered: there is no topic_skills table yet (spec §2 D).
            topic_level = level(state, d_target, True, cfg)
            passed += topic_level == "passed"
            rows.append(
                ProgressTopic(
                    id=topic.topic_id,
                    name=topic.name,
                    stars=topic.stars,
                    level=topic_level,
                    review_due=False,
                    origin="doc",
                )
            )
            eff = mastery_eff(state.mastery, state.d_max, d_target, cfg)
            weights.append(ReadinessTopic(topic.stars, topic.signal_r, eff, state.attempts))
        return ProgressCardEvent(
            days_left=dict(stubs.events("session_start"))["progress_card"]["days_left"],
            passed=passed,
            total=len(DEMO_TOPICS),
            readiness=readiness(weights, cfg),
            topics=rows,
        )
