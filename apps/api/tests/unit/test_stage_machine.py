"""The stage machine of a topic (specs/features/tutor/stage-machine.md · AC-1 to AC-16 · TM-03,
TM-04, AM-08, AM-09, TM-16, SM-12).

Every threshold comes from config/learning.yaml through get_settings() (stages.*, park.*,
done.*); boundaries are built from those values. The cap is bkt.target_difficulty.

Interfaces these tests expect (built by /implement-feature), in app/domain/stage_machine.py:
- `SkillState(id, exam_freq, independent_correct, problems_today)`
- `TopicState(stage, stars, level, skills, current_skill_id, difficulty, fail_streak)`
- `Start(user_new)`, `Answer(correct, error_type, independent)`
- `next_step(state, event, mode, cfg) -> Step` with `stage`, `teach` (`kind`, `angle`,
  `error_type`) or None, `problem` (`skill_id`, `difficulty`, `purpose`) or None,
  `fail_streak`, `park_reason`
"""

import uuid

import pytest

from app.domain.bkt import target_difficulty
from app.domain.stage_machine import Answer, SkillState, Start, TopicState, next_step
from app.settings import LearningConfig, get_settings


@pytest.fixture
def cfg() -> LearningConfig:
    return get_settings().learning


def sid(n: int) -> uuid.UUID:
    return uuid.UUID(int=n)


def skill(n: int, freq: int = 1, correct: int = 0, today: int = 0) -> SkillState:
    return SkillState(id=sid(n), exam_freq=freq, independent_correct=correct, problems_today=today)


TWO_SKILLS = (skill(1, freq=2), skill(2, freq=1))


def state(
    stage=None,
    skills=TWO_SKILLS,
    stars=3,
    level="developing",
    current=None,
    difficulty=None,
    fail_streak=0,
) -> TopicState:
    return TopicState(
        stage=stage,
        stars=stars,
        level=level,
        skills=tuple(skills),
        current_skill_id=None if current is None else sid(current),
        difficulty=difficulty,
        fail_streak=fail_streak,
    )


RIGHT = Answer(correct=True, error_type=None, independent=True)


def wrong(error="sign", independent=True) -> Answer:
    return Answer(correct=False, error_type=error, independent=independent)


def cap(cfg: LearningConfig, stars: int = 3, mode: str = "normal") -> int:
    return target_difficulty(stars, mode, cfg)


def verify_level(cfg: LearningConfig, d: int) -> int:
    return max(d - cfg.stages.verify_difficulty_drop, 1)


# --- AC-1 to AC-3 · Probe (TM-03) ----------------------------------------------------------------


def test_TM03_a_new_topic_starts_with_a_probe_problem(cfg: LearningConfig):
    skills = (skill(1, freq=1), skill(2, freq=2))

    step = next_step(state(skills=skills), Start(user_new=False), "normal", cfg)

    assert step.stage == "probe"
    assert step.teach is None
    assert step.fail_streak == 0
    assert (step.problem.skill_id, step.problem.purpose) == (sid(2), "probe")
    assert step.problem.difficulty == min(cfg.stages.probe_difficulty, cap(cfg))


def test_TM03_a_user_new_to_the_topic_is_taught_first_not_probed(cfg: LearningConfig):
    step = next_step(state(), Start(user_new=True), "normal", cfg)

    assert step.stage == "practice"
    assert step.teach.kind == "introduce"
    assert step.problem.purpose == "practice"
    assert step.problem.difficulty == min(cfg.stages.practice_start_difficulty, cap(cfg))


def test_TM03_a_right_probe_skips_the_explanation(cfg: LearningConfig):
    m = cfg.done.min_independent_correct_per_skill
    d = cfg.stages.probe_difficulty
    skills = (skill(1, freq=2, correct=m), skill(2, freq=1))  # skill 1 covered by this probe

    step = next_step(state("probe", skills, current=1, difficulty=d), RIGHT, "normal", cfg)

    assert step.teach is None
    assert step.stage == "practice"
    assert (step.problem.skill_id, step.problem.purpose) == (sid(2), "practice")
    assert step.problem.difficulty == min(d + 1, cap(cfg))


# --- AC-4 to AC-8 · Teach → Verify (AM-08, AM-09, TM-04) -----------------------------------------


@pytest.mark.parametrize("stage", ["probe", "practice"])
def test_AM08_a_wrong_answer_is_taught_then_verified_on_the_same_skill(cfg, stage):
    d = cap(cfg)

    step = next_step(state(stage, current=1, difficulty=d), wrong("sign"), "normal", cfg)

    assert step.stage == "verify"
    assert (step.teach.kind, step.teach.angle, step.teach.error_type) == ("point_fix", 1, "sign")
    assert (step.problem.skill_id, step.problem.purpose) == (sid(1), "verify")
    assert step.problem.difficulty == verify_level(cfg, d)
    assert step.problem.difficulty <= d  # never harder
    assert step.fail_streak == 1


@pytest.mark.parametrize(
    ("error_type", "kind"),
    [
        ("calculation", "point_fix"),
        ("sign", "point_fix"),
        ("wrong_method", "explain_method"),
        ("concept", "explain_concept"),
        (None, "explain_concept"),
        ("prerequisite", "explain_prerequisite"),
        ("no_answer", "show_first_step"),
    ],
)
def test_AM08_the_teaching_follows_the_error_type(cfg, error_type, kind):
    d = cfg.stages.probe_difficulty

    step = next_step(state("probe", current=1, difficulty=d), wrong(error_type), "normal", cfg)

    assert step.teach.kind == kind
    assert step.teach.error_type == error_type


def test_AM09_a_second_explanation_takes_a_new_angle(cfg: LearningConfig):
    assert cfg.park.max_fail_streak_per_skill > 2  # room for two explanations before Park
    d = cfg.stages.probe_difficulty
    verify = state("verify", current=1, difficulty=d, fail_streak=1)

    step = next_step(verify, wrong("concept"), "normal", cfg)

    assert (step.teach.angle, step.fail_streak) == (2, 2)


def test_TM04_a_right_verify_goes_back_to_practice(cfg: LearningConfig):
    m = cfg.done.min_independent_correct_per_skill
    d = cfg.stages.probe_difficulty
    skills = (skill(1, freq=2, correct=m), skill(2, freq=1))
    verify = state("verify", skills, current=1, difficulty=d, fail_streak=2)

    step = next_step(verify, RIGHT, "normal", cfg)

    assert step.stage == "practice"
    assert step.fail_streak == 0
    assert (step.problem.skill_id, step.problem.purpose) == (sid(2), "practice")


def test_AM08_right_after_seeing_the_working_is_verified_again(cfg: LearningConfig):
    d = cfg.stages.probe_difficulty
    verify = state("verify", current=1, difficulty=d, fail_streak=1)

    shown = Answer(correct=True, error_type=None, independent=False)

    step = next_step(verify, shown, "normal", cfg)

    assert step.stage == "verify"
    assert (step.problem.skill_id, step.problem.purpose) == (sid(1), "verify")
    assert step.fail_streak == 1


# --- AC-9 to AC-13 · Practice and skills (SM-12, TM-16) ------------------------------------------


@pytest.mark.parametrize(
    ("skills", "chosen"),
    [
        ((skill(1, freq=1), skill(2, freq=3), skill(3, freq=2)), 2),  # most exam_freq first
        ((skill(1, freq=2), skill(2, freq=2)), 1),  # tie → order
        ((skill(1, freq=3, correct=99), skill(2, freq=1)), 2),  # covered is skipped
        ((skill(1, freq=0), skill(2, freq=1)), 2),  # never on an exam: not needed
        ((skill(1, freq=0, correct=99), skill(2, freq=0)), 2),  # no past exam: every skill
        ((), None),  # a topic with no skill
    ],
    ids=["exam-freq", "tie-order", "covered", "not-on-exam", "no-past-exam", "no-skill"],
)
def test_SM12_the_next_skill_is_an_open_exam_skill(cfg, skills, chosen):
    step = next_step(state(skills=skills), Start(user_new=False), "normal", cfg)

    assert step.problem.skill_id == (None if chosen is None else sid(chosen))


def test_SM12_all_covered_but_not_passed_practises_the_least_done_skill(cfg: LearningConfig):
    m = cfg.done.min_independent_correct_per_skill
    skills = (
        skill(1, freq=1, correct=m + 2),
        skill(2, freq=3, correct=m + 1),
        skill(3, freq=1, correct=m + 1),  # same count as skill 2, fewer on exams
    )
    d = cfg.stages.probe_difficulty

    step = next_step(state("practice", skills, current=1, difficulty=d), RIGHT, "normal", cfg)

    assert step.problem.skill_id == sid(2)


@pytest.mark.parametrize(("offset", "chosen"), [(-1, 1), (0, 2)], ids=["min-1", "min"])
def test_TM16_a_skill_is_covered_at_the_configured_count(cfg, offset, chosen):
    m = cfg.done.min_independent_correct_per_skill
    skills = (skill(1, freq=3, correct=m + offset), skill(2, freq=1))

    step = next_step(state(skills=skills), Start(user_new=False), "normal", cfg)

    assert step.problem.skill_id == sid(chosen)


@pytest.mark.parametrize("stars", [3, 1], ids=["three-stars", "one-star"])
def test_TM16_practice_never_goes_above_the_target_difficulty(cfg, stars):
    top = cap(cfg, stars)
    if stars == 1:
        assert top == cfg.done.one_star_final_difficulty
    practice = state("practice", stars=stars, current=1, difficulty=top)

    step = next_step(practice, RIGHT, "normal", cfg)

    assert step.problem.difficulty == top


def test_TM16_a_passed_topic_is_done(cfg: LearningConfig):
    practice = state("practice", level="passed", current=1, difficulty=cap(cfg), fail_streak=1)

    step = next_step(practice, RIGHT, "normal", cfg)

    assert (step.stage, step.problem, step.fail_streak) == ("done", None, 0)


# --- AC-14, AC-15 · Park -------------------------------------------------------------------------


@pytest.mark.parametrize(("before", "parked"), [(-2, False), (-1, True)], ids=["max-1", "max"])
def test_TM19_park_after_the_configured_wrong_streak(cfg, before, parked):
    streak = cfg.park.max_fail_streak_per_skill + before
    d = cfg.stages.probe_difficulty
    verify = state("verify", current=1, difficulty=d, fail_streak=streak)

    step = next_step(verify, wrong("concept"), "normal", cfg)

    assert step.fail_streak == streak + 1
    if parked:
        assert (step.stage, step.park_reason, step.problem) == ("park", "fail_streak", None)
    else:
        assert (step.stage, step.park_reason) == ("verify", None)
        assert step.problem.purpose == "verify"


@pytest.mark.parametrize("answer", ["wrong", "right"])
@pytest.mark.parametrize(("offset", "parked"), [(-1, False), (0, True)], ids=["max-1", "max"])
def test_TM19_park_when_the_next_skill_had_enough_problems_today(cfg, answer, offset, parked):
    today = cfg.park.max_problems_per_skill_per_day + offset
    m = cfg.done.min_independent_correct_per_skill
    d = cfg.stages.probe_difficulty
    if answer == "wrong":  # the next problem is a Verify of skill 1
        skills = (skill(1, freq=2, today=today), skill(2, freq=1))
        event = wrong("sign")
    else:  # skill 1 is now covered, so the next problem is skill 2
        skills = (skill(1, freq=2, correct=m), skill(2, freq=1, today=today))
        event = RIGHT

    step = next_step(state("practice", skills, current=1, difficulty=d), event, "normal", cfg)

    if parked:
        assert (step.stage, step.park_reason, step.problem) == ("park", "too_many_today", None)
    else:
        assert step.park_reason is None
        assert step.problem is not None


# --- AC-16 · Start of a topic done before (TM-04) ------------------------------------------------


def test_TM04_a_topic_resumed_in_a_new_session_keeps_its_stage(cfg: LearningConfig):
    d = cap(cfg)
    start = Start(user_new=False)

    open_verify = state("verify", current=1, difficulty=d, fail_streak=1)

    verify = next_step(open_verify, start, "normal", cfg)
    assert verify.stage == "verify"
    assert (verify.problem.skill_id, verify.problem.difficulty) == (sid(1), d)
    assert verify.problem.purpose == "verify"

    practice = next_step(state("practice", current=1, difficulty=d), start, "normal", cfg)
    assert (practice.stage, practice.problem.purpose) == ("practice", "practice")

    done = next_step(state("done", level="passed"), start, "normal", cfg)
    assert (done.stage, done.problem) == ("done", None)

    parked = next_step(state("park", current=1, difficulty=d, fail_streak=3), start, "normal", cfg)
    assert (parked.stage, parked.problem.purpose, parked.fail_streak) == ("probe", "probe", 0)
