"""Topic mastery with BKT, levels and readiness (specs/features/planner/bkt-mastery.md).

Every threshold comes from config/learning.yaml through get_settings(); a test that needs
another value changes it with model_copy. The only literal numbers are the worked examples of
learning-model.md §1 (0.71, 0.93, 0.986, 0.19), compared at the precision the table prints,
and the readiness example of the spec §3.
"""

import pytest

from app.domain.bkt import (
    ReadinessTopic,
    TopicProgress,
    level,
    mastery_eff,
    readiness,
    record_attempt,
    target_difficulty,
    update_mastery,
)
from app.settings import LearningConfig, get_settings

EPS = 1e-9  # spec AC-8


@pytest.fixture
def cfg() -> LearningConfig:
    return get_settings().learning


def fresh(cfg: LearningConfig) -> TopicProgress:
    return TopicProgress(mastery=cfg.bkt.p_init, attempts=0, d_max=0)


def with_bkt(cfg: LearningConfig, **changes: object) -> LearningConfig:
    return cfg.model_copy(update={"bkt": cfg.bkt.model_copy(update=changes)})


def expected_update(p: float, correct: bool, cfg: LearningConfig) -> float:
    """learning-model.md §1, written out again so a wrong formula in the code shows."""
    b = cfg.bkt
    if correct:
        posterior = p * (1 - b.p_slip) / (p * (1 - b.p_slip) + (1 - p) * b.p_guess)
    else:
        posterior = p * b.p_slip / (p * b.p_slip + (1 - p) * (1 - b.p_guess))
    return posterior + (1 - posterior) * b.p_transit


# --- BKT ------------------------------------------------------------------------------


def test_PM02_three_correct_in_a_row_from_p_init(cfg):
    # AC-1: the worked example of learning-model.md §1.
    p1 = update_mastery(cfg.bkt.p_init, True, cfg.bkt)
    p2 = update_mastery(p1, True, cfg.bkt)
    p3 = update_mastery(p2, True, cfg.bkt)

    assert (round(p1, 2), round(p2, 2), round(p3, 3)) == (0.71, 0.93, 0.986)
    assert p1 == pytest.approx(expected_update(cfg.bkt.p_init, True, cfg))
    assert p2 < cfg.bkt.mastery_threshold <= p3


def test_PM02_one_wrong_from_p_init(cfg):
    # AC-2
    p = update_mastery(cfg.bkt.p_init, False, cfg.bkt)

    assert round(p, 2) == 0.19
    assert p == pytest.approx(expected_update(cfg.bkt.p_init, False, cfg))


@pytest.mark.parametrize("p", [0.01, 0.5, 0.99])
def test_PM02_mastery_stays_inside_zero_one_and_correct_beats_wrong(cfg, p):
    # AC-3
    right = update_mastery(p, True, cfg.bkt)
    wrong = update_mastery(p, False, cfg.bkt)

    assert 0 < wrong < right < 1


def test_PM02_only_independent_attempts_count(cfg):
    # AC-4: an attempt right after a worked example does not move anything, unless the
    # config says every attempt counts.
    start = TopicProgress(mastery=cfg.bkt.p_init, attempts=2, d_max=1)

    skipped = record_attempt(start, True, 3, False, cfg)
    counted = record_attempt(start, True, 3, False, with_bkt(cfg, count_only_independent=False))

    assert skipped == start
    assert counted.attempts == 3
    assert counted.d_max == 3
    assert counted.mastery == pytest.approx(expected_update(start.mastery, True, cfg))


def test_TM16_d_max_is_the_hardest_correct_and_never_drops(cfg):
    # AC-5
    start = fresh(cfg)

    wrong_only = record_attempt(start, False, 3, True, cfg)
    hard_right = record_attempt(start, True, 3, True, cfg)
    then_easy_wrong = record_attempt(hard_right, False, 1, True, cfg)

    assert wrong_only.d_max == 0
    assert wrong_only.attempts == 1
    assert wrong_only.mastery == pytest.approx(expected_update(start.mastery, False, cfg))
    assert hard_right.d_max == 3
    assert then_easy_wrong.d_max == 3
    assert then_easy_wrong.attempts == 2


# --- target difficulty, cap and level ------------------------------------------------


# learning-model.md §4 table: the done.* field each (stars, mode) reads, or None (skipped).
TARGET_FIELD = {
    (3, "normal"): "three_star_final_difficulty",
    (3, "final"): "three_star_final_difficulty",
    (3, "tight"): "three_star_final_difficulty",
    (3, "triage"): "three_star_final_difficulty",
    (2, "normal"): "two_star_final_difficulty",
    (2, "final"): "two_star_final_difficulty",
    (2, "tight"): "tight_mode_two_star_difficulty",
    (2, "triage"): "tight_mode_two_star_difficulty",
    (1, "normal"): "one_star_final_difficulty",
    (1, "final"): "one_star_final_difficulty",
    (1, "tight"): "one_star_final_difficulty",
    (1, "triage"): None,
    (0, "normal"): None,
    (0, "final"): None,
    (0, "tight"): None,
    (0, "triage"): None,
}


@pytest.mark.parametrize(("stars", "mode"), list(TARGET_FIELD), ids=lambda v: str(v))
def test_TM16_target_difficulty_by_stars_and_mode(cfg, stars, mode):
    # AC-6
    field = TARGET_FIELD[(stars, mode)]
    expected = None if field is None else getattr(cfg.done, field)

    assert target_difficulty(stars, mode, cfg) == expected


def test_TM16_mastery_is_capped_by_the_hardest_correct(cfg):
    # AC-7: the ★★★ normal example of learning-model.md §4 (all answers right).
    d_target = target_difficulty(3, "normal", cfg)
    assert d_target is not None
    cap_one_below = (cfg.bkt.weak_below + cfg.bkt.mastery_threshold) / 2
    progress = fresh(cfg)
    for _ in range(3):
        progress = record_attempt(progress, True, d_target - 2, True, cfg)
    two_below = mastery_eff(progress.mastery, progress.d_max, d_target, cfg)
    progress = record_attempt(progress, True, d_target - 1, True, cfg)
    one_below = mastery_eff(progress.mastery, progress.d_max, d_target, cfg)
    progress = record_attempt(progress, True, d_target, True, cfg)
    at_target = mastery_eff(progress.mastery, progress.d_max, d_target, cfg)

    assert two_below == pytest.approx(cfg.bkt.weak_below)  # 0.986 capped to weak_below
    assert one_below == pytest.approx(cap_one_below)
    assert at_target == progress.mastery
    assert mastery_eff(0.4, 0, None, cfg) == 0.4  # no target (skipped): no cap


@pytest.mark.parametrize(
    ("offset_from", "delta", "expected"),
    [
        pytest.param("weak_below", -EPS, "weak", id="weak_below - eps"),
        pytest.param("weak_below", 0.0, "developing", id="weak_below"),
        pytest.param("mastery_threshold", -EPS, "developing", id="mastery_threshold - eps"),
        pytest.param("mastery_threshold", 0.0, "passed", id="mastery_threshold"),
    ],
)
def test_TM15_level_boundaries(cfg, offset_from, delta, expected):
    # AC-8: at the target difficulty, so no cap; every skill covered.
    d_target = target_difficulty(3, "normal", cfg)
    mastery = getattr(cfg.bkt, offset_from) + delta
    progress = TopicProgress(mastery=mastery, attempts=1, d_max=d_target)

    assert level(progress, d_target, True, cfg) == expected


def test_TM15_no_attempt_is_not_started(cfg):
    # AC-8
    d_target = target_difficulty(3, "normal", cfg)

    assert level(fresh(cfg), d_target, True, cfg) == "not_started"


def test_TM16_passed_needs_skills_and_a_target(cfg):
    # AC-9: high mastery alone is not enough.
    d_target = target_difficulty(3, "normal", cfg)
    high = TopicProgress(mastery=cfg.bkt.mastery_threshold, attempts=3, d_max=d_target)
    one_star_triage = target_difficulty(1, "triage", cfg)

    assert level(high, d_target, False, cfg) == "developing"
    assert one_star_triage is None
    assert level(high, one_star_triage, True, cfg) != "passed"


# --- readiness -----------------------------------------------------------------------


def test_PM03_readiness_is_signal_weighted_mastery(cfg):
    # AC-10: spec §3 example, plus a 0-star topic that must not count.
    topics = [
        ReadinessTopic(stars=3, signal_r=1.0, mastery_eff=0.71, attempts=1),
        ReadinessTopic(stars=2, signal_r=0.5, mastery_eff=0.30, attempts=1),
        ReadinessTopic(stars=0, signal_r=1.0, mastery_eff=1.0, attempts=1),
    ]

    assert cfg.readiness.exclude_zero_star is True
    assert readiness(topics, cfg) == pytest.approx((1.0 * 0.71 + 0.5 * 0.30) / 1.5, abs=EPS)
    assert readiness([], cfg) == 0.0
    assert (
        readiness([ReadinessTopic(stars=3, signal_r=0.0, mastery_eff=0.9, attempts=1)], cfg) == 0.0
    )


def test_PM03_topic_not_started_counts_as_zero(cfg):
    # AC-10b (learning-model v1.4 §5): not p_init.
    started = ReadinessTopic(stars=3, signal_r=1.0, mastery_eff=0.8, attempts=2)
    not_started = ReadinessTopic(stars=3, signal_r=1.0, mastery_eff=cfg.bkt.p_init, attempts=0)

    assert readiness([started, not_started], cfg) == pytest.approx(0.8 / 2, abs=EPS)
    assert readiness([not_started], cfg) == 0.0
