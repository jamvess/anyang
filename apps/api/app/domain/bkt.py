"""Topic mastery with Bayesian Knowledge Tracing, the level shown on the progress card and the
readiness % (specs/features/planner/bkt-mastery.md · learning-model.md §1, §4, §5).

Code decides how well the student knows a topic, not the LLM (CLAUDE.md rule 1). Pure
functions: every number comes from ``cfg`` (config/learning.yaml); the caller reads and
writes ``topic_progress`` and ``attempts``.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Literal

from app.settings import BktConfig, LearningConfig

Mode = Literal["normal", "tight", "triage", "final"]
Level = Literal["not_started", "weak", "developing", "passed"]


@dataclass(frozen=True)
class TopicProgress:
    """``mastery`` is the raw BKT value (starts at ``bkt.p_init``); ``d_max`` the hardest
    difficulty answered right independently (0 when none)."""

    mastery: float
    attempts: int
    d_max: int


@dataclass(frozen=True)
class ReadinessTopic:
    stars: int
    signal_r: float
    mastery_eff: float
    attempts: int  # 0 = not started, counted as 0 (learning-model v1.4 §5)


def update_mastery(p: float, correct: bool, cfg: BktConfig) -> float:
    """One BKT step: the posterior after the answer, then the chance to learn (§1)."""
    if correct:
        hit = p * (1 - cfg.p_slip)
        posterior = hit / (hit + (1 - p) * cfg.p_guess)
    else:
        miss = p * cfg.p_slip
        posterior = miss / (miss + (1 - p) * (1 - cfg.p_guess))
    return posterior + (1 - posterior) * cfg.p_transit


def record_attempt(
    progress: TopicProgress, correct: bool, difficulty: int, independent: bool, cfg: LearningConfig
) -> TopicProgress:
    """``correct`` is ``CheckResult.is_correct`` (correct_with_flaw and incomplete are wrong).
    An attempt right after a worked example does not count (``bkt.count_only_independent``)."""
    if not independent and cfg.bkt.count_only_independent:
        return progress
    return replace(
        progress,
        mastery=update_mastery(progress.mastery, correct, cfg.bkt),
        attempts=progress.attempts + 1,
        d_max=max(progress.d_max, difficulty) if correct else progress.d_max,
    )


def target_difficulty(stars: int, mode: Mode, cfg: LearningConfig) -> int | None:
    """The difficulty a topic must be solved at to pass (§4 table); None = skipped."""
    done = cfg.done
    if stars >= 3:
        return done.three_star_final_difficulty
    if stars == 2:
        if mode in ("tight", "triage"):
            return done.tight_mode_two_star_difficulty
        return done.two_star_final_difficulty
    if stars == 1 and mode != "triage":
        return done.one_star_final_difficulty
    return None


def mastery_eff(mastery: float, d_max: int, d_target: int | None, cfg: LearningConfig) -> float:
    """BKT does not know difficulty, so mastery is capped until the target is solved (§4)."""
    if d_target is None or d_max >= d_target:
        return mastery
    if d_max == d_target - 1:
        return min(mastery, (cfg.bkt.weak_below + cfg.bkt.mastery_threshold) / 2)
    return min(mastery, cfg.bkt.weak_below)


def level(
    progress: TopicProgress, d_target: int | None, skills_covered: bool, cfg: LearningConfig
) -> Level:
    """``skills_covered``: every skill the Done rule asks for has its independent corrects
    (learning-model §4 item 1), counted by the caller."""
    if progress.attempts == 0:
        return "not_started"
    eff = mastery_eff(progress.mastery, progress.d_max, d_target, cfg)
    if (
        skills_covered
        and d_target is not None
        and progress.d_max >= d_target
        and eff >= cfg.bkt.mastery_threshold
    ):
        return "passed"
    if eff < cfg.bkt.weak_below:
        return "weak"
    return "developing"


def readiness(topics: Sequence[ReadinessTopic], cfg: LearningConfig) -> float:
    """sum(signal_r * mastery_eff) / sum(signal_r) (§5); a topic not started counts as 0."""
    counted = [t for t in topics if t.stars > 0 or not cfg.readiness.exclude_zero_star]
    total = sum(t.signal_r for t in counted)
    if total == 0:
        return 0.0
    return sum(t.signal_r * (t.mastery_eff if t.attempts else 0.0) for t in counted) / total
