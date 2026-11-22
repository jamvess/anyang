"""The stage machine of a topic: Probe → Teach → Verify → Practice → Done, or Park
(specs/features/tutor/stage-machine.md · ai-orchestration.md §2.2.4, §2.5.4 · learning-model.md
§4, §7).

Code decides the stage and the next problem; the LLM only says it (CLAUDE.md rule 1). Pure
functions: every threshold comes from ``cfg`` (config/learning.yaml); the caller records the
attempt and BKT first, then stores the returned stage and fail streak.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.domain.bkt import Level, Mode, target_difficulty
from app.domain.checker import ErrorType
from app.settings import LearningConfig

Stage = Literal["probe", "verify", "practice", "done", "park"]
Purpose = Literal["probe", "verify", "practice"]
TeachKind = Literal[
    "introduce",
    "point_fix",
    "explain_method",
    "explain_concept",
    "explain_prerequisite",
    "show_first_step",
]
ParkReason = Literal["fail_streak", "too_many_today"]

# The bottom of the 1-3 difficulty scale (`problems.difficulty` check in 0001_init.sql), not a
# threshold of the learning model.
MIN_DIFFICULTY = 1

# ai-orchestration §2.2.4 "การสอนตาม error type"; null is taught as a concept (spec §2.3).
_TEACH_KIND: dict[ErrorType | None, TeachKind] = {
    "calculation": "point_fix",
    "sign": "point_fix",
    "wrong_method": "explain_method",
    "concept": "explain_concept",
    None: "explain_concept",
    "prerequisite": "explain_prerequisite",
    "no_answer": "show_first_step",
}


@dataclass(frozen=True)
class SkillState:
    id: UUID
    exam_freq: int
    independent_correct: int  # all sessions, this attempt included
    problems_today: int  # this attempt included


@dataclass(frozen=True)
class TopicState:
    """The topic after the caller recorded this event's attempt (spec §2.1)."""

    stage: Stage | None
    stars: int
    level: Level
    skills: tuple[SkillState, ...]  # in topic_skills order
    current_skill_id: UUID | None
    difficulty: int | None  # of the latest problem
    fail_streak: int  # before this event


@dataclass(frozen=True)
class Start:
    user_new: bool


@dataclass(frozen=True)
class Answer:
    correct: bool  # verdict == "correct", as in BKT
    error_type: ErrorType | None
    independent: bool


@dataclass(frozen=True)
class Teach:
    kind: TeachKind
    angle: int  # 1 = first explanation; 2 and up = a new angle (AM-09)
    error_type: ErrorType | None


@dataclass(frozen=True)
class ProblemSpec:
    skill_id: UUID | None
    difficulty: int
    purpose: Purpose


@dataclass(frozen=True)
class Step:
    stage: Stage
    teach: Teach | None
    problem: ProblemSpec | None
    fail_streak: int
    park_reason: ParkReason | None


# --- §2.2 · shared values ------------------------------------------------------------------------


def _required(skills: Sequence[SkillState], cfg: LearningConfig) -> list[SkillState]:
    """Skills that must be covered (TM-16): those on past exams, or all when none was."""
    on_exam = [s for s in skills if s.exam_freq > 0]
    if on_exam and cfg.done.require_exam_skills_covered:
        return on_exam
    return list(skills)


def next_skill(skills: Sequence[SkillState], cfg: LearningConfig) -> UUID | None:
    """Spec §2.2 item 3: the open exam skill with most exam_freq, else the least practised."""
    required = _required(skills, cfg)
    if not required:
        return None
    order = {s.id: i for i, s in enumerate(skills)}
    need = cfg.done.min_independent_correct_per_skill
    open_skills = [s for s in required if s.independent_correct < need]
    if open_skills:
        return min(open_skills, key=lambda s: (-s.exam_freq, order[s.id])).id
    return min(required, key=lambda s: (s.independent_correct, -s.exam_freq, order[s.id])).id


def _cap(state: TopicState, mode: Mode, cfg: LearningConfig) -> int:
    target = target_difficulty(state.stars, mode, cfg)
    return cfg.done.three_star_final_difficulty if target is None else target


def _practice_start(cap: int, cfg: LearningConfig) -> int:
    return min(cfg.stages.practice_start_difficulty, cap)


def _last_or_start(state: TopicState, cap: int, cfg: LearningConfig) -> int:
    """The latest problem's difficulty within the cap; the first practice level when none."""
    return _practice_start(cap, cfg) if state.difficulty is None else min(state.difficulty, cap)


def _skill(state: TopicState, skill_id: UUID | None) -> SkillState | None:
    return next((s for s in state.skills if s.id == skill_id), None)


def _verify(state: TopicState, cap: int, cfg: LearningConfig) -> ProblemSpec:
    """Spec §2.2 items 3, 5: the same skill (null → the next one), never harder, within the cap."""
    skill_id = state.current_skill_id
    if skill_id is None:
        skill_id = next_skill(state.skills, cfg)
    if state.difficulty is None:
        level = _practice_start(cap, cfg)
    else:
        lower = max(state.difficulty - cfg.stages.verify_difficulty_drop, MIN_DIFFICULTY)
        level = min(lower, cap)
    return ProblemSpec(skill_id, level, "verify")


def _practice_after_right(state: TopicState, cap: int, cfg: LearningConfig) -> ProblemSpec:
    """Spec §2.2 item 5: one level up on a skill already worked on; a new skill starts again."""
    skill_id = next_skill(state.skills, cfg)
    skill = _skill(state, skill_id)
    worked_on = skill_id == state.current_skill_id or (
        skill is not None and skill.independent_correct > 0
    )
    if state.difficulty is None or not worked_on:
        return ProblemSpec(skill_id, _practice_start(cap, cfg), "practice")
    return ProblemSpec(skill_id, min(state.difficulty + 1, cap), "practice")


# --- §2.3 · rules --------------------------------------------------------------------------------


def _probe(state: TopicState, cap: int, cfg: LearningConfig, fail_streak: int) -> Step:
    problem = ProblemSpec(
        next_skill(state.skills, cfg), min(cfg.stages.probe_difficulty, cap), "probe"
    )
    return Step("probe", None, problem, fail_streak, None)


def _start(state: TopicState, event: Start, cap: int, cfg: LearningConfig) -> Step:
    if state.level == "passed":  # before item 1: a mode change can pass a topic (§10 item 7 B)
        return Step("done", None, None, 0, None)
    if state.stage is None or state.stage == "park":  # items 1-2 · park: spec §10 item 6
        if not event.user_new:
            return _probe(state, cap, cfg, 0)
        problem = ProblemSpec(next_skill(state.skills, cfg), _practice_start(cap, cfg), "practice")
        return Step("practice", Teach("introduce", 1, None), problem, 0, None)
    if state.stage == "probe":  # item 4
        return _probe(state, cap, cfg, state.fail_streak)
    if state.stage == "verify":
        verify = _verify(state, cap, cfg)
        same = ProblemSpec(verify.skill_id, _last_or_start(state, cap, cfg), "verify")
        return Step("verify", None, same, state.fail_streak, None)
    # practice, or done but no longer passed (item 3)
    problem = ProblemSpec(
        next_skill(state.skills, cfg), _last_or_start(state, cap, cfg), "practice"
    )
    return Step("practice", None, problem, state.fail_streak, None)


def _answer(state: TopicState, event: Answer, cap: int, cfg: LearningConfig) -> Step:
    if state.level == "passed":  # item 5
        return Step("done", None, None, 0, None)

    if event.correct and event.independent:  # item 6
        return Step("practice", None, _practice_after_right(state, cap, cfg), 0, None)

    verify = _verify(state, cap, cfg)
    if event.correct:  # item 7: right after seeing the working
        return Step("verify", None, verify, state.fail_streak, None)

    streak = state.fail_streak + 1  # item 8
    if streak >= cfg.park.max_fail_streak_per_skill:
        return Step("park", None, None, streak, "fail_streak")
    teach = Teach(_TEACH_KIND[event.error_type], streak, event.error_type)
    return Step("verify", teach, verify, streak, None)


def _too_many_today(step: Step, state: TopicState, cfg: LearningConfig) -> Step:
    """Spec §2.3 item 9: park when the next problem's skill already had its day's problems."""
    if step.problem is None:
        return step
    skill = _skill(state, step.problem.skill_id)
    if skill is None or skill.problems_today < cfg.park.max_problems_per_skill_per_day:
        return step
    return Step("park", None, None, step.fail_streak, "too_many_today")


def next_step(state: TopicState, event: Start | Answer, mode: Mode, cfg: LearningConfig) -> Step:
    cap = _cap(state, mode, cfg)
    if isinstance(event, Start):
        step = _start(state, event, cap, cfg)
    else:
        step = _answer(state, event, cap, cfg)
    return _too_many_today(step, state, cfg)
