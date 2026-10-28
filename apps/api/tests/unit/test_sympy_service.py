"""SymPy service of the answer checker: LaTeX lines + reference answer -> SympyResult.

Spec: specs/features/check/sympy-service.md (ai-orchestration.md §2.4.3). The comparison rules
are tested in-process through ``evaluate_lines`` (the function the worker runs); ``check_lines``
is tested with a fake pool, so no subprocess is started here. Worker processes and timeouts are
in test_sympy_service_timeout.py. Examples (ans_xxx) come from evals/answers/labels.jsonl.
"""

import json
from functools import cache

import pytest

from app.domain.checker import LlmResult, SympyResult, merge_check
from app.math import sympy_service
from app.math.sympy_service import SympyTimeoutError, check_lines, evaluate_lines
from app.settings import _REPO_ROOT, get_settings

GOLDEN = _REPO_ROOT / "evals" / "answers" / "labels.jsonl"


@cache
def golden() -> dict[str, dict]:
    rows = (json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line)
    return {row["id"]: row for row in rows}


def run(answer_id: str) -> SympyResult:
    row = golden()[answer_id]
    return evaluate_lines(row["answer_format"], row["reference"], row["lines"])


def undecided(result: SympyResult) -> bool:
    return result.final_equal is None and result.final_in_form is None and result.line_ok == []


class FakePool:
    """Runs the job in-process and records the timeout it was given."""

    def __init__(self, *, raise_timeout: bool = False) -> None:
        self.raise_timeout = raise_timeout
        self.calls: list[float] = []

    async def run(self, fn, *args, timeout_s: float):
        self.calls.append(timeout_s)
        if self.raise_timeout:
            raise SympyTimeoutError
        return fn(*args)


# --- expression -----------------------------------------------------------------------------


def test_AM04_expression_limit_chain_all_equal() -> None:
    # AC-1: ans_003, limit at infinity, reference 3/2.
    result = run("ans_003")

    assert result.parsed is True
    assert result.timed_out is False
    assert result.final_equal is True
    assert result.line_ok == [True, True, True, True]
    assert result.final_in_form is None


def test_AM04_first_line_derivative_is_computed_before_comparing() -> None:
    # AC-2: line 1 restates the problem; its value is the derivative, which equals the reference.
    result = evaluate_lines(
        "expression",
        r"2x\sin(x)+x^{2}\cos(x)",
        [r"\frac{d}{dx}\left(x^{2}\sin(x)\right)"],
    )

    assert result.line_ok == [True]
    assert result.final_equal is True


def test_AM05_limit_wrong_cancellation_marks_line_two() -> None:
    # AC-3: ans_002, line 2 drops x^2 terms; lines 3-4 follow from line 2, answer 1 not 4.
    result = run("ans_002")

    assert result.line_ok == [True, False, True, True]
    assert result.final_equal is False


def test_AM05_derivative_sign_error_marks_line_three() -> None:
    # AC-4: ans_007, line 3 writes -x^2 cos(x).
    result = run("ans_007")

    assert result.line_ok == [True, True, False]
    assert result.final_equal is False


def test_AM04_equivalence_is_mathematical_not_string() -> None:
    # AC-5: ans_010, written differently from the reference but equal.
    assert run("ans_010").final_equal is True


@pytest.mark.parametrize(
    "line",
    [
        r"=2\left(x+1\right)",
        r"2\,(x+1)",
        r"=\left(x+1\right)\cdot 2",
    ],
)
def test_AM04_spacing_left_right_and_leading_equals_are_ignored(line: str) -> None:
    # AC-6
    result = evaluate_lines("expression", "2x+2", [line])

    assert result.parsed is True
    assert result.line_ok == [True]
    assert result.final_equal is True


def test_AM04_limit_with_rewritten_fraction() -> None:
    # AC-7: ans_016, 3 sin(3x)/(3x) under lim x->0.
    result = run("ans_016")

    assert result.final_equal is True
    assert all(result.line_ok)


def test_AM05_chained_equals_in_one_line_all_steps_true() -> None:
    # AC-27
    result = evaluate_lines(
        "expression",
        "1",
        [r"\lim_{x \to 1} \frac{x^{2}+1}{x+1}", r"=\frac{1^{2}+1}{1+1}=\frac{2}{2}=1"],
    )

    assert result.line_ok == [True, True]
    assert result.final_equal is True


def test_AM05_chained_equals_in_one_line_with_a_wrong_step() -> None:
    # AC-27: the last step 2/2 = 3 is wrong, so the whole line is wrong.
    result = evaluate_lines(
        "expression",
        "1",
        [r"\lim_{x \to 1} \frac{x^{2}+1}{x+1}", r"=\frac{1^{2}+1}{1+1}=\frac{2}{2}=3"],
    )

    assert result.line_ok == [True, False]
    assert result.final_equal is False


# --- definition lines (f, f', f'') ----------------------------------------------------------


def test_AM04_definition_chain_second_derivative_correct() -> None:
    # AC-8: ans_017, f(x) -> f'(x) -> f''(x), reference 12x^2 - 6.
    result = run("ans_017")

    assert result.line_ok == [True, True, True]
    assert result.final_equal is True


def test_AM05_definition_chain_wrong_second_derivative() -> None:
    # AC-9: ans_019, f''(x) = 16x^2 - 6.
    result = run("ans_019")

    assert result.line_ok == [True, True, False]
    assert result.final_equal is False


# --- factored -------------------------------------------------------------------------------


def test_AM04_factored_not_fully_factored_is_not_in_form() -> None:
    # AC-10: ans_001, x(x^2 - 1) equals x(x-1)(x+1) but x^2 - 1 still factors.
    result = run("ans_001")

    assert result.final_equal is True
    assert result.final_in_form is False
    assert result.line_ok == [True, True]


@pytest.mark.parametrize("answer_id", ["ans_006", "ans_015"])
def test_AM04_factored_fully_factored_is_in_form(answer_id: str) -> None:
    # AC-11: (x-2)(x+2)(x^2+4) and (x-2)^2(x+2).
    result = run(answer_id)

    assert result.final_equal is True
    assert result.final_in_form is True


def test_AM04_factored_constant_factor_is_not_a_factor() -> None:
    # AC-12: 3(x+2) is factored; the parser must not distribute it into 3x + 6.
    result = evaluate_lines("factored", "3(x+2)", ["3x+6", "=3(x+2)"])

    assert result.final_equal is True
    assert result.final_in_form is True


def test_AM04_factored_expanded_answer_equal_but_not_in_form() -> None:
    # AC-12
    result = evaluate_lines("factored", "3(x+2)", ["3x+6"])

    assert result.final_equal is True
    assert result.final_in_form is False


@pytest.mark.parametrize("answer_id", ["ans_003", "ans_005"])
def test_AM04_form_is_only_checked_for_factored(answer_id: str) -> None:
    # AC-13: expression (ans_003) and equation (ans_005).
    assert run(answer_id).final_in_form is None


# --- equation -------------------------------------------------------------------------------


def test_AM04_equation_exponential_solved_over_reals() -> None:
    # AC-14: ans_005; e is Euler's number, and e^x = 1 has the single real solution 0.
    result = run("ans_005")

    assert result.parsed is True
    assert result.line_ok == [True] * len(golden()["ans_005"]["lines"])
    assert result.final_equal is True


def test_AM04_equation_solution_order_does_not_matter() -> None:
    # AC-15: ans_012, x=1, x=-1 against x=-1, x=1.
    assert run("ans_012").final_equal is True


def test_AM05_critical_points_wrong_last_line() -> None:
    # AC-16: ans_018, f -> f' -> f' = 0 -> ... -> (x-3)(x+1)=0 -> x=3, x=1.
    result = run("ans_018")

    assert result.line_ok == [True, True, True, True, True, False]
    assert result.final_equal is False


def test_AM05_line_equal_to_a_wrong_line_stays_true() -> None:
    # AC-17: ans_008, line 5 (x+3)(x-1)=0 is wrong; line 6 follows from it.
    result = run("ans_008")

    assert result.line_ok == [True, True, True, True, False, True]
    assert result.final_equal is False


# --- cannot decide --------------------------------------------------------------------------


@pytest.mark.parametrize("bad_line", [r"\text{ดังนั้น } x=1", r"x^{\?}"])
def test_AM04_unparseable_line_is_not_parsed(bad_line: str) -> None:
    # AC-18
    result = evaluate_lines("expression", "1", ["1", bad_line])

    assert result.parsed is False
    assert undecided(result)


def test_AM04_unparseable_reference_is_not_parsed() -> None:
    # AC-19
    result = evaluate_lines("expression", r"\text{ไม่มีเฉลย}", ["1"])

    assert result.parsed is False
    assert undecided(result)


def test_AM04_implicit_differentiation_is_not_supported() -> None:
    # AC-20: ans_004, equations in x and y inside an expression-format answer.
    result = run("ans_004")

    assert result.parsed is False
    assert undecided(result)


def test_AM04_equation_part_with_two_equals_is_not_supported() -> None:
    # AC-28
    result = evaluate_lines(
        "equation",
        "x=-1, x=3",
        ["f(x)=x^{3}-3x^{2}-9x+1", "f'(x)=3x^{2}-6x-9=0", "x=-1, x=3"],
    )

    assert result.parsed is False
    assert undecided(result)


def test_AM04_undecidable_solution_set_gives_no_verdict() -> None:
    # AC-21: x + sin(x) = 1 + sin(1) has no closed-form solveset (ConditionSet).
    result = evaluate_lines("equation", "x=1", [r"x+\sin(x)=1+\sin(1)"])

    assert result.parsed is True
    assert result.timed_out is False
    assert undecided(result)


async def test_AM06_no_lines_returns_without_running_sympy() -> None:
    # AC-22
    pool = FakePool()

    result = await check_lines(
        answer_format="expression", reference_answer="1", lines=[], pool=pool
    )

    assert result.parsed is False
    assert result.timed_out is False
    assert undecided(result)
    assert pool.calls == []


# --- check_lines: timeout and config --------------------------------------------------------


async def test_AM04_timeout_gives_timed_out_result() -> None:
    # AC-23 (result side; the real worker is killed in test_sympy_service_timeout.py)
    result = await check_lines(
        answer_format="expression",
        reference_answer="1",
        lines=["1"],
        pool=FakePool(raise_timeout=True),
    )

    assert result.timed_out is True
    assert result.parsed is True
    assert undecided(result)


async def test_AM04_default_timeout_comes_from_config() -> None:
    # AC-25
    pool = FakePool()

    result = await check_lines(
        answer_format="expression", reference_answer="1", lines=["1"], pool=pool
    )

    assert pool.calls == [get_settings().learning.checker.sympy_timeout_seconds]
    assert result.final_equal is True


async def test_AM04_explicit_timeout_overrides_config() -> None:
    # AC-25 (§3: timeout_s is optional)
    pool = FakePool()
    timeout_s = get_settings().learning.checker.sympy_timeout_seconds / 2

    await check_lines(
        answer_format="expression",
        reference_answer="1",
        lines=["1"],
        timeout_s=timeout_s,
        pool=pool,
    )

    assert pool.calls == [timeout_s]


async def test_AM04_without_pool_uses_default_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    # AC-25 / AC-29: the request path uses the shared pool built from config.
    pool = FakePool()
    monkeypatch.setattr(sympy_service, "default_pool", lambda: pool)

    await check_lines(answer_format="expression", reference_answer="1", lines=["1"])

    assert len(pool.calls) == 1


# --- feeds merge rules ----------------------------------------------------------------------


def test_AM04_result_feeds_merge_rules() -> None:
    # AC-26: ans_001 -> merge_check -> incomplete, as labelled.
    row = golden()["ans_001"]
    llm = LlmResult(
        error_type="calculation",
        evidence="",
        method="doc",
        verdict=None,
        first_wrong_line=None,
        confidence=0.9,
    )

    merged = merge_check(
        answer_format=row["answer_format"], lines=row["lines"], sympy=run("ans_001"), llm=llm
    )

    assert merged.verdict == row["verdict"] == "incomplete"


# --- numeric counterexample (spec §2.5, added after the golden-set run) -------------------


def test_AM05_numeric_counterexample_decides_when_sympy_equals_is_unsure() -> None:
    # AC-30: ans_042, line 2 multiplies the derivatives; SymPy's equals() returns None for
    # 2e^{x^2} vs the reference, but the values differ at a sample point.
    result = run("ans_042")

    assert result.parsed is True
    assert result.final_equal is False
    assert result.line_ok == [True, False, True, True]


def test_AM04_numeric_check_never_turns_an_identity_into_unequal() -> None:
    # AC-30: equal values stay equal (or undecided), never False.
    result = evaluate_lines("expression", r"\ln(6)", [r"\ln(2)+\ln(3)"])

    assert result.final_equal is not False
