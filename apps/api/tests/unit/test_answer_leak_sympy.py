"""Answer-leak check, step 2 (SymPy) and the two steps together
(specs/features/ai/answer-leak-check.md §2.3, §2.4 · AC-5 to AC-11 · AM-13).

`leaks_by_sympy` is called in-process, as test_sympy_service.py calls `evaluate_lines`; the
combined `check_leak` gets a fake pool, so no worker process starts. The flag comes from
config/ai.yaml → guards.answer_leak_check through get_settings().

Interfaces these tests expect (built by /implement-feature):
- app/domain/answer_leak.py: `math_parts(reply) -> list[str]` (§2.1 items 1-3)
- app/math/answer_leak.py: `LeakProblem(reference_answer, answer_format, expression)`,
  `leaks_by_sympy(answer_format, reference_answer, problem_expression, parts) -> bool`,
  `async check_leak(reply, problem, *, enabled=None, timeout_s=None, pool=None) -> LeakResult`
  with `leaked`, `method`, `part` (keywords and defaults as `check_lines`)
"""

import pytest

from app.domain.answer_leak import math_parts
from app.math.answer_leak import LeakProblem, check_leak, leaks_by_sympy
from app.math.sympy_service import SympyTimeoutError

FACTOR = LeakProblem(reference_answer="(x-7)(x+7)", answer_format="factored", expression="x^2-49")
DERIVATIVE = LeakProblem(
    reference_answer="3x^2", answer_format="expression", expression=r"\frac{d}{dx}x^3"
)
ROOTS = LeakProblem(reference_answer="x=7, x=-7", answer_format="equation", expression="x^2=49")


def sympy_leaks(reply: str, problem: LeakProblem) -> bool:
    return leaks_by_sympy(
        problem.answer_format, problem.reference_answer, problem.expression, math_parts(reply)
    )


class CountingPool:
    """Runs the job in-process and counts the calls (AC-11)."""

    def __init__(self) -> None:
        self.calls = 0

    async def run(self, fn, *args, timeout_s):
        self.calls += 1
        return fn(*args)


class TimeoutPool:
    async def run(self, fn, *args, timeout_s):
        raise SympyTimeoutError


# --- AC-5 to AC-8 · SymPy, the value and the final form -------------------------------------------


@pytest.mark.parametrize(
    ("reply", "leaked"),
    [("คำตอบคือ $(x+7)(x-7)$", True), ("ลองแยก $x^2-49$", False)],
    ids=["reordered-factors", "the-problem-not-factored"],
)
def test_AM13_factored_counts_only_in_factored_form(reply, leaked):
    assert sympy_leaks(reply, FACTOR) is leaked


@pytest.mark.parametrize(
    ("reply", "leaked"),
    [
        (r"ได้ $6x \cdot \frac{x}{2}$", True),
        (r"ลองหา $\frac{d}{dx}x^3$", False),
        (r"โจทย์คือ $\frac{d}{dx} x^{3}$", False),
    ],
    ids=["same-value", "operator-not-worked-out", "the-problem-written-again"],
)
def test_AM13_expression_counts_only_when_worked_out(reply, leaked):
    assert sympy_leaks(reply, DERIVATIVE) is leaked


@pytest.mark.parametrize(
    ("reply", "leaked"),
    [("ได้ $7 = x$", True), ("ลองแก้ $x^2 = 49$", False), ("ถ้า $x = 5$ ล่ะ", False)],
    ids=["sides-swapped", "not-solved", "not-a-root"],
)
def test_AM13_equation_counts_a_solved_root(reply, leaked):
    assert sympy_leaks(reply, ROOTS) is leaked


def test_AM13_a_part_sympy_cannot_read_is_skipped():
    reply = r"$\text{ลองดู}$ แล้ว $(x+7)(x-7)$"

    assert sympy_leaks(reply, FACTOR) is True
    assert sympy_leaks(r"$\text{ลองดู}$", FACTOR) is False


# --- AC-9 to AC-11 · the two steps together ------------------------------------------------------


async def test_AM13_the_check_is_off_when_the_guard_is_off():
    pool = CountingPool()

    result = await check_leak("คำตอบคือ $(x-7)(x+7)$", FACTOR, enabled=False, pool=pool)

    assert result.leaked is False
    assert pool.calls == 0


async def test_AM13_a_sympy_timeout_is_not_a_leak():
    result = await check_leak("คำตอบคือ $(x+7)(x-7)$", FACTOR, enabled=True, pool=TimeoutPool())

    assert (result.leaked, result.method) == (False, "sympy_timeout")


async def test_AM13_a_text_match_needs_no_sympy():
    pool = CountingPool()

    result = await check_leak("คำตอบคือ $(x-7)(x+7)$", FACTOR, enabled=True, pool=pool)

    assert (result.leaked, result.method, result.part) == (True, "text", "(x-7)(x+7)")
    assert pool.calls == 0


async def test_AM13_the_sympy_step_runs_when_the_text_does_not_match():
    pool = CountingPool()

    result = await check_leak("คำตอบคือ $(x+7)(x-7)$", FACTOR, enabled=True, pool=pool)

    assert (result.leaked, result.method) == (True, "sympy")
    assert pool.calls == 1


# --- AC-13 to AC-15 · gaps from the self-review (spec §10 item 6) ---------------------------------


@pytest.mark.parametrize(
    ("reply", "problem"),
    [
        (r"ได้ $\cos x \cdot 3$", LeakProblem(r"3\cos(x)", "expression", r"\frac{d}{dx}3\sin(x)")),
        ("ได้ $C + x^3$", LeakProblem("x^3+C", "expression", r"\int 3x^2 \, dx")),
    ],
    ids=["space-after-a-command", "two-symbols"],
)
async def test_AM13_sympy_reads_the_part_as_written(reply, problem):
    # AC-13 (B): spaces kept for SymPy; an answer with two symbols is still checked.
    result = await check_leak(reply, problem, enabled=True, pool=CountingPool())

    assert (result.leaked, result.method) == (True, "sympy")


@pytest.mark.parametrize(
    "reply",
    [r"ได้ $x = \pm 7$", "รากแรก $x_1 = 7$", "รากที่สอง $x_{2} = -7$"],
    ids=["plus-minus", "index", "index-in-braces"],
)
async def test_AM13_roots_written_with_pm_or_an_index_are_a_leak(reply):
    # AC-14 (C)
    result = await check_leak(reply, ROOTS, enabled=True, pool=CountingPool())

    assert result.leaked is True


async def test_AM13_a_substitution_or_an_identity_in_a_hint_is_not_the_answer():
    # AC-15 (D)
    limit = LeakProblem("0", "expression", r"\lim_{x \to 0} x^2")
    sine = LeakProblem("1", "expression", r"\lim_{x \to 0} \frac{\sin x}{x}")

    substitution = await check_leak("แทน $x = 0$", limit, enabled=True, pool=CountingPool())
    identity = await check_leak(
        r"ใช้ $\sin^2 x + \cos^2 x$ ไม่ได้นะ", sine, enabled=True, pool=CountingPool()
    )

    assert substitution.leaked is False
    assert identity.leaked is False
