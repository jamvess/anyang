"""Tests for the line scorer of PoC P1 (specs/poc/README.md P1: a line is read correctly when
it is mathematically equal to the label line, checked with SymPy).

    cd apps/api && uv run --with "antlr4-python3-runtime==4.11.*" pytest ../../poc/P1 -q

PoC-only code: the real SymPy service is apps/api/app/math (Junior, S3).
"""

import pytest
from lines import align, same_line, to_sympy

# --- parsing ----------------------------------------------------------------------------------


def test_AM01_poc_leading_equals_sign_is_dropped():
    assert to_sympy("=x(x^{2}-1)") is not None
    assert to_sympy("=x(x^{2}-1)") == to_sympy("x(x^{2}-1)")


def test_AM01_poc_top_level_commas_split_a_line():
    parts = to_sympy(r"x=0, x=\ln(2)")
    assert parts is not None and len(parts) == 2


def test_AM01_poc_commas_inside_brackets_do_not_split():
    parts = to_sympy(r"\left(1, 2\right)")
    assert parts is None or len(parts) == 1


def test_AM01_poc_unparseable_line_gives_none():
    assert to_sympy(r"\? + 1") is None


# --- same_line --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("predicted", "label"),
    [
        (r"x^{2} - 1", r"x^{2}-1"),  # spacing
        (r"\left(x+1\right)", r"(x+1)"),  # \left \right
        (r"x^{2}\cos(x)+2x\sin(x)", r"2x\sin(x)+x^{2}\cos(x)"),  # order of terms
        (r"(x-2)(x+2)", r"(x+2)(x-2)"),  # order of factors
        (r"3=x", r"x=3"),  # sides of an equation
        (r"x^{2}-2x-3=0", r"x^{2} - 2x - 3 = 0"),
        (r"=x(x^{2}-1)", r"x(x^{2}-1)"),  # leading "="
        (r"x=0, x=\ln(2)", r"x=0,x=\ln(2)"),
    ],
)
def test_AM01_poc_equal_lines(predicted: str, label: str):
    assert same_line(predicted, label)


@pytest.mark.parametrize(
    ("predicted", "label"),
    [
        (r"(x+3)(x-1)", r"(x-3)(x+1)"),  # a sign misread is a different line
        (r"2x\sin(x)-x^{2}\cos(x)", r"2x\sin(x)+x^{2}\cos(x)"),
        (r"\frac{d}{dx}\left(x^{2}\right)", r"2x"),  # no evaluating: the derivative was not written
        (r"\lim_{x \to 1} \frac{x^{2}+1}{x+1}", r"1"),
        (r"x=0, x=\ln(3)", r"x=0, x=\ln(2)"),
        (r"x=0", r"x=0, x=\ln(2)"),  # a missing part
        (r"\? + 1", r"x + 1"),  # unparseable prediction
    ],
)
def test_AM01_poc_different_lines(predicted: str, label: str):
    assert not same_line(predicted, label)


def test_AM01_poc_unparseable_lines_compare_as_text():
    assert same_line(r"\text{ไม่รู้}", r"\text{ไม่รู้}")


# --- alignment --------------------------------------------------------------------------------


def eq(a: str, b: str) -> bool:
    return a == b


def test_AM01_poc_alignment_counts_matching_lines_in_order():
    result = align(["a", "x", "b", "c"], ["a", "b", "c"], eq)
    assert result.correct == 3
    assert result.predicted_wrong == [1]  # the extra line "x"
    assert result.label_missed == []


def test_AM01_poc_alignment_missing_line():
    result = align(["a", "c"], ["a", "b", "c"], eq)
    assert result.correct == 2
    assert result.label_missed == [1]


def test_AM01_poc_alignment_misread_line_is_wrong_and_missed():
    result = align(["a", "B", "c"], ["a", "b", "c"], eq)
    assert result.correct == 2
    assert result.predicted_wrong == [1]
    assert result.label_missed == [1]


def test_AM01_poc_alignment_keeps_order():
    # "c" then "a" can only match one of the two label lines in order.
    result = align(["c", "a"], ["a", "c"], eq)
    assert result.correct == 1


# --- score.py: numbers of the P1 report -----------------------------------------------------

from score import ConfidencePoint, choose_threshold, pr_at, score_image  # noqa: E402


def line(latex: str, confidence: float) -> dict:
    return {"latex": latex, "confidence": confidence}


def test_AM01_poc_score_image_counts_correct_lines_and_flags_wrong_predictions():
    result = score_image([line("x+1", 0.9), line("x-9", 0.4)], ["x+1", "x-2"], unclear=[])
    assert (result.correct, result.label_lines) == (1, 2)
    assert result.points == [ConfidencePoint(0.9, wrong=False), ConfidencePoint(0.4, wrong=True)]


def test_AM01_poc_score_image_drops_unclear_label_lines():
    # unclear_lines are 1-based (evals/README.md); they are not scored
    result = score_image([line("x+1", 0.9)], ["x+1", r"\?"], unclear=[2])
    assert (result.correct, result.label_lines) == (1, 1)


def test_AM02_poc_pr_at_threshold():
    points = [
        ConfidencePoint(0.3, wrong=True),
        ConfidencePoint(0.6, wrong=True),
        ConfidencePoint(0.7, wrong=False),
        ConfidencePoint(0.95, wrong=False),
    ]
    at = pr_at(points, 0.65)  # flags confidence < 0.65
    assert at["recall_wrong"] == 1.0
    assert at["precision_wrong"] == 1.0
    assert at["flag_rate"] == 0.5
    at = pr_at(points, 0.5)
    assert at["recall_wrong"] == 0.5


def test_AM02_poc_choose_lowest_threshold_reaching_target_recall():
    points = [ConfidencePoint(0.3, True), ConfidencePoint(0.6, True), ConfidencePoint(0.8, False)]
    # 0.65 already flags both wrong lines; higher thresholds only add confirmations
    assert choose_threshold(points, thresholds=[0.5, 0.65, 0.8, 0.9], target=0.95) == 0.65


def test_AM02_poc_choose_threshold_none_when_target_unreachable():
    points = [ConfidencePoint(0.99, True), ConfidencePoint(0.5, False)]
    assert choose_threshold(points, thresholds=[0.5, 0.9], target=0.95) is None


def test_AM02_poc_no_wrong_lines_means_recall_is_undefined():
    assert pr_at([ConfidencePoint(0.9, False)], 0.5)["recall_wrong"] is None
