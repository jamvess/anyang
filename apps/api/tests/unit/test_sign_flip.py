"""Hint ``sign_flip_detected`` for the check_answer classifier (ai-orchestration.md §2.4.4).

Spec: specs/features/check/check-answer-classifier.md §2.4 (AC-16 to AC-18). Flipping the sign of
one term of any sum on the first wrong line makes that line follow from the line before it.
Pure SymPy in-process; the async wrapper is tested with a fake pool.
"""

import json
from functools import cache

import pytest

from app.math.sympy_service import SympyTimeoutError, detect_sign_flip, sign_flip_line
from app.settings import _REPO_ROOT

GOLDEN = _REPO_ROOT / "evals" / "answers" / "labels.jsonl"


@cache
def golden() -> dict[str, dict]:
    rows = (json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line)
    return {row["id"]: row for row in rows}


def flip(answer_id: str) -> int | None:
    row = golden()[answer_id]
    return sign_flip_line(row["answer_format"], row["reference"], row["lines"])


def test_AM06_sign_inside_a_factor_is_detected() -> None:
    # AC-16: the §2.4.4 example, x^2 - 5x + 6 = (x-2)(x+3); flipping +3 gives (x-2)(x-3).
    result = sign_flip_line("factored", "(x-2)(x-3)", ["x^{2}-5x+6", "=(x-2)(x+3)"])

    assert result == 2


def test_AM06_sign_of_a_term_in_a_derivative_is_detected() -> None:
    # AC-17: ans_007, 2x sin(x) - x^2 cos(x).
    assert flip("ans_007") == 3


def test_AM06_calculation_error_gives_no_sign_hint() -> None:
    # AC-18: ans_019, f''(x) = 16x^2 - 6 is wrong by calculation, not by sign.
    assert flip("ans_019") is None


@pytest.mark.parametrize("answer_id", ["ans_003", "ans_004"])
def test_AM06_no_hint_without_a_wrong_line(answer_id: str) -> None:
    # §2.4: only when SymPy decided and some line_ok is false (ans_003 all true · ans_004 not
    # parsed).
    assert flip(answer_id) is None


class FakePool:
    def __init__(self, *, raise_timeout: bool = False) -> None:
        self.raise_timeout = raise_timeout

    async def run(self, fn, *args, timeout_s: float):
        if self.raise_timeout:
            raise SympyTimeoutError
        return fn(*args)


async def test_AM06_detect_runs_in_the_pool() -> None:
    row = golden()["ans_007"]

    result = await detect_sign_flip(
        answer_format=row["answer_format"],
        reference_answer=row["reference"],
        lines=row["lines"],
        pool=FakePool(),
    )

    assert result == 3


async def test_AM06_timeout_gives_no_hint() -> None:
    # §2.4: same timeout as the SymPy check; a timeout means no hint, not an error.
    row = golden()["ans_007"]

    result = await detect_sign_flip(
        answer_format=row["answer_format"],
        reference_answer=row["reference"],
        lines=row["lines"],
        pool=FakePool(raise_timeout=True),
    )

    assert result is None
