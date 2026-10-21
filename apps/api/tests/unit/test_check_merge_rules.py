"""Merge rules of the answer checker: SymPy result + LLM classifier -> verdict.

Spec: specs/features/check/merge-rules.md (ai-orchestration.md §2.4.5). Pure domain code: the
SymPy and LLM results below are hand-made, no model and no database is used.
"""

import pytest

from app.domain.checker import CheckResult, LlmResult, SympyResult, merge_check

ERROR_TYPES = {"calculation", "sign", "wrong_method", "concept", "prerequisite", "no_answer"}


def sympy(
    *,
    final_equal: bool | None = True,
    line_ok: list[bool] | None = None,
    final_in_form: bool | None = None,
    parsed: bool = True,
    timed_out: bool = False,
) -> SympyResult:
    return SympyResult(
        parsed=parsed,
        timed_out=timed_out,
        final_equal=final_equal,
        final_in_form=final_in_form,
        line_ok=line_ok if line_ok is not None else [True],
    )


def llm(
    *,
    error_type: str | None = None,
    method: str = "doc",
    verdict: str | None = None,
    first_wrong_line: int | None = None,
    confidence: float = 0.9,
    evidence: str = "",
) -> LlmResult:
    return LlmResult(
        error_type=error_type,
        evidence=evidence,
        method=method,
        verdict=verdict,
        first_wrong_line=first_wrong_line,
        confidence=confidence,
    )


def merge(
    lines: list[str],
    sympy_result: SympyResult,
    llm_result: LlmResult,
    answer_format: str = "expression",
) -> CheckResult:
    return merge_check(answer_format=answer_format, lines=lines, sympy=sympy_result, llm=llm_result)


# --- correct --------------------------------------------------------------------------------


def test_AM04_correct_when_final_answer_and_every_line_are_right():  # AC-1
    result = merge(["2x\\sin(x)+x^{2}\\cos(x)"], sympy(final_equal=True, line_ok=[True]), llm())

    assert result.verdict == "correct"
    assert result.is_correct is True
    assert result.error_type is None
    assert result.first_wrong_line is None
    assert result.decided_by == "sympy"


def test_AM04_correct_with_another_method_still_counts_as_correct():  # AC-2
    result = merge(["3"], sympy(final_equal=True, line_ok=[True]), llm(method="other"))

    assert result.verdict == "correct"
    assert result.method == "other"
    assert result.is_correct is True


# --- correct_with_flaw ----------------------------------------------------------------------


def test_AM05_right_final_answer_with_a_wrong_line_is_correct_with_flaw():  # AC-3
    result = merge(
        ["a", "b", "c", "d"],
        sympy(final_equal=True, line_ok=[True, False, False, True]),
        llm(error_type="sign"),
    )

    assert result.verdict == "correct_with_flaw"
    assert result.first_wrong_line == 2
    assert result.error_type == "sign"
    assert result.is_correct is False


# --- incomplete -----------------------------------------------------------------------------


def test_AM04_equal_but_not_factored_is_incomplete_with_concept():  # AC-4
    result = merge(
        ["x^{3}-x", "x(x^{2}-1)"],
        sympy(final_equal=True, final_in_form=False, line_ok=[True, True]),
        llm(error_type="calculation"),
        answer_format="factored",
    )

    assert result.verdict == "incomplete"
    assert result.error_type == "concept"  # set by code, not by the LLM
    assert result.first_wrong_line is None
    assert result.is_correct is False


def test_AM04_form_is_only_checked_for_factored_answers():  # AC-13
    result = merge(
        ["x=-1, x=3"],
        sympy(final_equal=True, final_in_form=None, line_ok=[True]),
        llm(),
        answer_format="equation",
    )

    assert result.verdict == "correct"


# --- incorrect ------------------------------------------------------------------------------


def test_AM05_wrong_final_answer_is_incorrect_at_the_first_wrong_line():  # AC-5
    result = merge(
        ["2x\\cos(x)+x^{2}\\sin(x)"],
        sympy(final_equal=False, line_ok=[False]),
        llm(error_type="sign"),
    )

    assert result.verdict == "incorrect"
    assert result.first_wrong_line == 1
    assert result.error_type == "sign"
    assert result.is_correct is False


def test_AM05_first_wrong_line_is_the_first_one_not_the_last():  # AC-6
    result = merge(
        ["a", "b", "c", "d"],
        sympy(final_equal=False, line_ok=[True, True, False, False]),
        llm(error_type="calculation"),
    )

    assert result.first_wrong_line == 3


@pytest.mark.parametrize(("llm_line", "expected"), [(2, 2), (None, 3)])
def test_AM05_wrong_final_answer_with_no_wrong_line_uses_the_llm_then_the_last_line(  # AC-6b
    llm_line: int | None, expected: int
):
    result = merge(
        ["a", "b", "c"],
        sympy(final_equal=False, line_ok=[True, True, True]),
        llm(error_type="concept", first_wrong_line=llm_line),
    )

    assert result.verdict == "incorrect"
    assert result.first_wrong_line == expected


# --- no answer ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sympy_result",
    [
        sympy(final_equal=True, line_ok=[]),
        sympy(final_equal=None, line_ok=[], parsed=False),
    ],
)
def test_AM06_no_lines_is_no_answer_whatever_sympy_and_llm_say(sympy_result):  # AC-7
    result = merge([], sympy_result, llm(error_type="sign", verdict="correct"))

    assert result.verdict == "incorrect"
    assert result.error_type == "no_answer"
    assert result.first_wrong_line is None
    assert result.is_correct is False


def test_AM06_no_answer_is_decided_by_code_with_full_confidence():  # AC-7b
    result = merge([], sympy(line_ok=[]), llm(confidence=0.3))

    assert result.decided_by == "sympy"
    assert result.confidence == 1.0


# --- SymPy cannot decide --------------------------------------------------------------------


@pytest.mark.parametrize(
    "sympy_result",
    [
        sympy(parsed=False, final_equal=None, line_ok=[False, False]),  # AC-8
        sympy(timed_out=True, final_equal=None, line_ok=[False, False]),  # AC-9
    ],
    ids=["not_parsed", "timed_out"],
)
def test_AM04_llm_decides_when_sympy_cannot(sympy_result):  # AC-8, AC-9
    result = merge(
        ["a", "b"],
        sympy_result,
        llm(verdict="incorrect", error_type="concept", first_wrong_line=2, confidence=0.6),
    )

    assert result.verdict == "incorrect"
    assert result.error_type == "concept"
    assert result.first_wrong_line == 2
    assert result.confidence == 0.6
    assert result.decided_by == "llm"
    assert result.is_correct is False


# --- SymPy and LLM disagree -----------------------------------------------------------------


def test_AM04_sympy_wins_when_llm_says_wrong_but_sympy_says_right():  # AC-10
    result = merge(["3"], sympy(final_equal=True, line_ok=[True]), llm(verdict="incorrect"))

    assert result.verdict == "correct"
    assert result.decided_by == "sympy"
    assert result.disagreement is True


def test_AM04_sympy_wins_when_llm_says_right_but_sympy_says_wrong():  # AC-11
    result = merge(
        ["4"],
        sympy(final_equal=False, line_ok=[False]),
        llm(verdict="correct", error_type="calculation"),
    )

    assert result.verdict == "incorrect"
    assert result.disagreement is True


def test_AM04_no_disagreement_when_llm_gives_no_verdict():  # AC-12
    result = merge(["3"], sympy(final_equal=True, line_ok=[True]), llm(verdict=None))

    assert result.disagreement is False


# --- confidence -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sympy_result",
    [sympy(final_equal=True, line_ok=[True]), sympy(final_equal=False, line_ok=[False])],
    ids=["correct", "incorrect"],
)
def test_AM04_confidence_is_full_when_sympy_decides(sympy_result):  # AC-15
    result = merge(["x"], sympy_result, llm(error_type="sign", confidence=0.6))

    assert result.confidence == 1.0


# --- error_type is always one of the six or empty for correct -------------------------------

CASES = {
    "correct": (["a"], sympy(final_equal=True, line_ok=[True]), llm(), "expression"),
    "correct_with_flaw": (
        ["a", "b"],
        sympy(final_equal=True, line_ok=[False, True]),
        llm(error_type="calculation"),
        "expression",
    ),
    "incomplete": (
        ["a"],
        sympy(final_equal=True, final_in_form=False, line_ok=[True]),
        llm(error_type="sign"),
        "factored",
    ),
    "incorrect": (
        ["a"],
        sympy(final_equal=False, line_ok=[False]),
        llm(error_type="prerequisite"),
        "expression",
    ),
    "no_answer": ([], sympy(line_ok=[]), llm(), "expression"),
    "llm_decides": (
        ["a"],
        sympy(parsed=False, final_equal=None, line_ok=[False]),
        llm(verdict="incorrect", error_type="wrong_method", first_wrong_line=1),
        "expression",
    ),
}


@pytest.mark.parametrize("case", CASES, ids=list(CASES))
def test_AM06_error_type_is_one_of_six_unless_correct(case):  # AC-14
    lines, sympy_result, llm_result, answer_format = CASES[case]

    result = merge(lines, sympy_result, llm_result, answer_format=answer_format)

    if result.verdict == "correct":
        assert result.error_type is None
    else:
        assert result.error_type in ERROR_TYPES
