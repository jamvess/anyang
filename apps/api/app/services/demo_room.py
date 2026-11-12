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
from app.services.room_state import (
    STUB_PROBLEM,
    STUDENT,
    InMemoryRoomState,
    LadderProgress,
    PendingProblem,
)
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


def _student(key: str) -> str:
    """The tenant part of `room_key(tenant_id, session_id)`."""
    return key.split("/", 1)[0]


class DemoRoomState(InMemoryRoomState):
    def __init__(self, recent_turns: int | None = None) -> None:
        """``recent_turns`` defaults to ``session.context_recent_turns`` (tests set it)."""
        super().__init__()
        # Per student (tenant), like topic_progress: kept across sessions (spec §2 J item 2).
        self._index: dict[str, int] = {}
        self._progress: dict[str, dict[str, TopicProgress]] = {}
        # The hint ladder of each student's pending problem (spec §2 K item 9).
        self._ladder: dict[str, LadderProgress] = {}
        # Students whose pending problem has its one attempt already (spec §2 K item 8): when
        # the tutor fails after it, the problem stays and must not count again (self-review).
        self._counted: set[str] = set()
        # Turns of (role, text) lines; a student line starts a turn (spec §2 E item 3).
        self._turns: dict[str, list[list[tuple[str, str]]]] = {}
        self._recent_turns = recent_turns

    async def pending_problem(self, key: str) -> PendingProblem | None:
        return DEMO_PROBLEMS[self._index.get(_student(key), 0)]

    async def start_session(self, key: str) -> None:
        """A new session: a new conversation and no pending preview, but mastery and the
        problem reached stay (spec §2 J item 2). Restart the API to start the demo over."""
        await super().start_session(key)
        self._turns.pop(key, None)

    def _is_pending(self, key: str, problem: PendingProblem) -> bool:
        return DEMO_PROBLEMS[self._index.get(_student(key), 0)].problem_id == problem.problem_id

    async def record_check(
        self, key: str, pending: PendingProblem, is_correct: bool, independent: bool = True
    ) -> None:
        # A stale preview of a problem already answered is not counted twice (self-review).
        if pending.topic_id is None or not self._is_pending(key, pending):
            return
        if _student(key) in self._counted:
            return
        self._counted.add(_student(key))
        cfg = get_settings().learning
        topics = self._progress.setdefault(_student(key), {})
        before = topics.get(pending.topic_id, TopicProgress(cfg.bkt.p_init, 0, 0))
        # Not independent only right after the last hint (spec §2 K item 8).
        topics[pending.topic_id] = record_attempt(
            before, is_correct, pending.difficulty, independent, cfg
        )

    async def ladder(self, key: str, pending: PendingProblem) -> LadderProgress | None:
        if not self._is_pending(key, pending):
            # A stale preview: explained as before, with no hint and nothing moved (§2 K 9).
            return None
        return self._ladder.get(_student(key), LadderProgress())

    async def note_try(
        self, key: str, pending: PendingProblem, *, wrong: bool = False, steps: int = 0
    ) -> None:
        if not self._is_pending(key, pending):
            return
        student = _student(key)
        now = self._ladder.get(student, LadderProgress())
        self._ladder[student] = LadderProgress(
            wrong_before=now.wrong_before + wrong, steps_before=now.steps_before + steps
        )

    async def remember(self, key: str, role: str, text: str) -> None:
        turns = self._turns.setdefault(key, [])
        if role == STUDENT or not turns:
            turns.append([])
        turns[-1].append((role, text))
        keep = self._recent_turns or get_settings().learning.session.context_recent_turns
        del turns[:-keep]

    async def conversation(self, key: str) -> list[tuple[str, str]]:
        return [line for turn in self._turns.get(key, []) for line in turn]

    async def next_problem(self, key: str, answered: PendingProblem) -> PendingProblem | None:
        if not self._is_pending(key, answered):
            return None  # answered late (a stale preview): the pending problem stays
        student = _student(key)
        self._index[student] = (self._index.get(student, 0) + 1) % len(DEMO_PROBLEMS)
        self._ladder.pop(student, None)  # the ladder starts over (spec §2 K item 9)
        self._counted.discard(student)
        return DEMO_PROBLEMS[self._index[student]]

    async def progress_card(self, key: str) -> ProgressCardEvent | None:
        cfg = get_settings().learning
        progress = self._progress.get(_student(key), {})
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
