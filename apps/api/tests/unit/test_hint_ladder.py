"""The hint ladder as pure rules (specs/features/tutor/demo-room.md §2 K · AC-39, AC-40, AC-48).

Code picks the directive, the LLM only says it (CLAUDE.md rule 1). ``wrong_before`` is how
many wrong answers this problem already had; None means the room has no ladder (not local).
The number of hints comes from ``tutoring.max_hints_before_solution``, read from the config.
"""

import pytest

from app.domain.hint_ladder import attempt_outcome, decide_directive, unfinished
from app.settings import get_settings


def tutoring(max_hints: int | None = None):
    cfg = get_settings().learning.tutoring
    if max_hints is None:
        return cfg
    return cfg.model_copy(update={"max_hints_before_solution": max_hints})


def directive(
    verdict,
    wrong_before,
    *,
    give_up=False,
    is_unfinished=False,
    no_working=False,
    max_hints=None,
):
    return decide_directive(
        verdict,
        give_up=give_up,
        unfinished=is_unfinished,
        no_working=no_working,
        wrong_before=wrong_before,
        cfg=tutoring(max_hints),
    )


# --- AC-39 · the table of §2 K item 1 (config: max_hints_before_solution = 2) -----------------


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        pytest.param({"verdict": None, "wrong_before": 0, "give_up": True}, "reveal", id="give up"),
        pytest.param(
            {"verdict": None, "wrong_before": 1, "give_up": True},
            "reveal",
            id="give up after a hint",
        ),
        pytest.param(
            {"verdict": "correct", "wrong_before": 0, "is_unfinished": True},
            "continue",
            id="right step, not finished",
        ),
        pytest.param(
            {"verdict": "incomplete", "wrong_before": 1, "is_unfinished": True},
            "continue",
            id="not in the asked form",
        ),
        pytest.param(
            {"verdict": "correct", "wrong_before": 0, "is_unfinished": True, "no_working": True},
            "continue",
            id="unfinished comes before missing working",
        ),
        pytest.param(
            {"verdict": "correct", "wrong_before": 0, "no_working": True},
            "ask_working",
            id="right but no working",
        ),
        pytest.param({"verdict": "correct", "wrong_before": 0}, "praise_and_show", id="correct"),
        pytest.param(
            {"verdict": "correct", "wrong_before": 2},
            "praise_and_show",
            id="correct after two hints",
        ),
        pytest.param({"verdict": "incorrect", "wrong_before": 0}, "hint_1", id="1st wrong"),
        pytest.param({"verdict": "incorrect", "wrong_before": 1}, "hint_2", id="2nd wrong"),
        pytest.param({"verdict": "incorrect", "wrong_before": 2}, "reveal", id="3rd wrong"),
        pytest.param(
            {"verdict": "correct_with_flaw", "wrong_before": 0},
            "reveal",
            id="correct with a flaw",
        ),
    ],
)
def test_AM07_directive_follows_the_ladder(kwargs, expected):
    assert tutoring().max_hints_before_solution == 2, "the table is written for the config value"

    assert directive(**kwargs) == expected


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        pytest.param({"verdict": "correct"}, "praise_and_show", id="correct"),
        pytest.param({"verdict": "correct", "no_working": True}, "ask_working", id="no working"),
        pytest.param({"verdict": "incorrect"}, "reveal", id="1st wrong"),
        pytest.param({"verdict": "incomplete"}, "reveal", id="incomplete"),
        pytest.param(
            {"verdict": "correct", "is_unfinished": True},
            "praise_and_show",
            id="no continue either",
        ),
    ],
)
def test_AM07_no_ladder_outside_local(kwargs, expected):
    # wrong_before None: the room has no ladder, so AM-07 as written today.
    assert directive(wrong_before=None, **kwargs) == expected


# --- AC-40 · unfinished ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("verdict", "last_line", "expected"),
    [
        pytest.param("correct", r"2x\sin(x) + x^{2}\frac{d}{dx}\sin(x)", True, id="d/dx left"),
        pytest.param("correct", r"\frac{d^{2}}{dx^{2}}(x^{4})", True, id="second derivative"),
        pytest.param("correct", r"\frac{d}{d x}(x^{2})", True, id="d/dx with a space"),
        pytest.param("correct", r"\lim_{x \to 2}(x+2)", True, id="lim left"),
        pytest.param("correct", r"\int x\,dx", True, id="integral left"),
        pytest.param("correct", r"\sum_{k=1}^{n} k", True, id="sum left"),
        pytest.param("correct", "d/dx(x^2)", True, id="plain d/dx"),
        pytest.param("correct", r"2x\sin(x)+x^{2}\cos(x)", False, id="finished"),
        pytest.param("incomplete", "(x^2-1)x", True, id="not factored yet"),
        pytest.param("incorrect", r"\frac{d}{dx}x", False, id="wrong is not unfinished"),
        pytest.param("correct_with_flaw", r"\lim_{x \to 2}(x+2)", False, id="flaw is not"),
    ],
)
def test_AM05_unfinished_step(verdict, last_line, expected):
    assert unfinished(verdict, last_line) is expected


# --- AC-48 · boundaries of max_hints_before_solution, and the BKT outcome ---------------------


@pytest.mark.parametrize(
    ("max_hints", "ladder"),
    [
        pytest.param(0, ["reveal"], id="0: the solution at once (AM-07 today)"),
        pytest.param(1, ["hint_1", "reveal"], id="1"),
        pytest.param(3, ["hint_1", "hint_2", "hint_2", "reveal"], id="3: hint_2 again"),
    ],
)
def test_AM07_max_hints_boundary(max_hints, ladder):
    got = [directive("incorrect", n, max_hints=max_hints) for n in range(len(ladder))]

    assert got == ladder


@pytest.mark.parametrize(
    ("chosen", "wrong_before", "max_hints", "expected"),
    [
        pytest.param("praise_and_show", 0, None, (True, True), id="right, no hint"),
        pytest.param("praise_and_show", 1, None, (True, True), id="right after hint_1"),
        pytest.param("praise_and_show", 2, None, (True, False), id="right after hint_2"),
        pytest.param("praise_and_show", 0, 1, (True, True), id="max 1: right, no hint"),
        pytest.param("praise_and_show", 1, 1, (True, False), id="max 1: right after the last hint"),
        pytest.param("reveal", 2, None, (False, True), id="wrong to the end"),
        pytest.param("reveal", 0, None, (False, True), id="gave up"),
        pytest.param("continue", 0, None, None, id="continue: not counted"),
        pytest.param("hint_1", 0, None, None, id="hint: not counted"),
        pytest.param("hint_2", 1, None, None, id="hint 2: not counted"),
        pytest.param("ask_working", 0, None, None, id="no working: not counted"),
    ],
)
def test_PM02_attempt_counted_once_per_problem(chosen, wrong_before, max_hints, expected):
    # §2 K item 8: (is_correct, independent), or None when nothing is recorded yet.
    assert attempt_outcome(chosen, wrong_before, tutoring(max_hints)) == expected


# --- added after the live smoke on Vertex (12 Nov) · not in the reviewed AC-40 table -------------


@pytest.mark.parametrize(
    ("last_line", "expected"),
    [
        pytest.param(r"\lim_{x \to 2}\frac{x+2}{x-1} = 4", False, id="lim worked out to 4"),
        pytest.param(r"\frac{d}{dx}(x^{2}) = 2x", False, id="d/dx worked out"),
        pytest.param(r"x^{2}\sin(x) = \frac{d}{dx}(x^{2})\sin(x)", True, id="d/dx after the ="),
    ],
)
def test_AM05_only_the_part_after_the_last_equals_counts(last_line, expected):
    # The whole line had \lim in it, so a finished limit was taken for an unfinished step.
    assert unfinished("correct", last_line) is expected
