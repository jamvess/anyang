"""Answer-leak check, step 2 (SymPy) and the two steps together
(specs/features/ai/answer-leak-check.md §2.3, §2.4 · AM-13).

``leaking_part_by_sympy`` runs in the SymPy worker pool with ``checker.sympy_timeout_seconds``
(CLAUDE.md: never call SymPy in the request thread). A part counts only when it has the
answer's value **and** is written as a final answer, so the problem itself never counts.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import sympy

from app.domain.answer_leak import (
    _split_top_level,
    math_parts,
    math_parts_as_written,
    text_match,
)
from app.domain.checker import AnswerFormat
from app.domain.hint_ladder import _UNEVALUATED  # operators SymPy would work out by itself
from app.domain.room import _plain
from app.math.sympy_service import (
    SympyTimeoutError,
    SympyWorkerPool,
    _classify,
    _equal,
    _Equation,
    _Expression,
    _in_factored_form,
    _parse,
    _solutions,
    _variable,
    default_pool,
)
from app.settings import get_settings

LeakMethod = Literal["text", "sympy", "sympy_timeout"]
# §2.3 equation row (§10 item 6 C): `\pm c` is c and -c; `x_1`, `x_{2}` are the variable x.
_PLUS_MINUS = re.compile(r"\\[pm]m(?![A-Za-z])")
_INDEX = re.compile(r"_.*$")


@dataclass(frozen=True)
class LeakProblem:
    reference_answer: str
    answer_format: AnswerFormat
    expression: str  # the problem, so that writing it again never counts


@dataclass(frozen=True)
class LeakResult:
    leaked: bool
    method: LeakMethod | None
    part: str | None  # for the log only, never shown to the user


def _values(side: str) -> list[sympy.Expr]:
    if _PLUS_MINUS.search(side):
        return [_parse(_PLUS_MINUS.sub(sign, side)) for sign in ("+", "-")]
    return [_parse(side)]


def _is_variable(written: sympy.Expr, variable: sympy.Symbol) -> bool:
    return isinstance(written, sympy.Symbol) and _INDEX.sub("", written.name) == variable.name


def _solved_values(part: str, variable: sympy.Symbol) -> list[sympy.Expr]:
    """`x=c` or `c=x` with no variable in c (§2.3 equation row): the values of c, else []."""
    sides = _split_top_level(part, "=")
    if len(sides) != 2:
        return []
    for name, value in (sides, reversed(sides)):
        values = _values(value)
        if _is_variable(_parse(name), variable) and not any(v.free_symbols for v in values):
            return values
    return []


def _equation_leak(reference: _Equation, parts: Sequence[str]) -> str | None:
    variable = _variable([reference])
    if variable is None:
        return None
    roots = _solutions(reference, variable)
    if not isinstance(roots, sympy.FiniteSet):
        return None
    for part in parts:
        try:
            values = _solved_values(part, variable)
            if any(_equal(value, root) for value in values for root in roots):
                return part
        except Exception:  # cannot be read or compared: skip the part (AC-8)
            continue
    return None


def _value_leak(
    answer_format: AnswerFormat, reference: _Expression, problem: str, parts: Sequence[str]
) -> str | None:
    for part in parts:
        plain = _plain(part)
        if "=" in part or plain == problem or _UNEVALUATED.search(plain):
            continue  # a pair (its sides are parts too), the problem, or not worked out
        try:
            written = _parse(part)
            if not written.free_symbols <= reference.value.free_symbols:
                continue  # a variable the answer does not have (§10 item 6 D)
            if not _equal(written.doit(), reference.value):
                continue
            if answer_format == "factored" and not _in_factored_form(
                written, _variable([reference])
            ):
                continue
            return part
        except Exception:  # cannot be read or compared: skip the part (AC-8)
            continue
    return None


def leaking_part_by_sympy(
    answer_format: AnswerFormat,
    reference_answer: str,
    problem_expression: str,
    parts: Sequence[str],
) -> str | None:
    """§2.3: the part with the answer's value written as a final answer, or None."""
    try:
        reference = _classify(reference_answer, answer_format)
        if isinstance(reference, _Equation):
            return _equation_leak(reference, parts)
        if isinstance(reference, _Expression):
            return _value_leak(answer_format, reference, _plain(problem_expression), parts)
    except Exception:  # a reference SymPy cannot read: step 1 is all we can do
        return None
    return None


def leaks_by_sympy(
    answer_format: AnswerFormat,
    reference_answer: str,
    problem_expression: str,
    parts: Sequence[str],
) -> bool:
    return (
        leaking_part_by_sympy(answer_format, reference_answer, problem_expression, parts)
        is not None
    )


async def check_leak(
    reply: str,
    problem: LeakProblem,
    *,
    enabled: bool | None = None,
    timeout_s: float | None = None,
    pool: SympyWorkerPool | None = None,
) -> LeakResult:
    """§2.4: the guard, then the string match, then SymPy. A SymPy timeout or a failed worker
    is not a leak (§10 item 4); the caller logs ``method = "sympy_timeout"``."""
    if enabled is None:
        enabled = get_settings().ai.guards.answer_leak_check
    if not enabled:
        return LeakResult(False, None, None)

    part = text_match(math_parts(reply), problem.reference_answer, problem.answer_format)
    if part is not None:
        return LeakResult(True, "text", part)

    parts = math_parts_as_written(reply)  # spaces kept for SymPy (§2.1 item 3)
    if not parts:
        return LeakResult(False, None, None)
    if timeout_s is None:
        timeout_s = get_settings().learning.checker.sympy_timeout_seconds
    pool = pool or default_pool()
    try:
        part = await pool.run(
            leaking_part_by_sympy,
            problem.answer_format,
            problem.reference_answer,
            problem.expression,
            parts,
            timeout_s=timeout_s,
        )
    except (SympyTimeoutError, RuntimeError):
        return LeakResult(False, "sympy_timeout", None)
    if part is None:
        return LeakResult(False, None, None)
    return LeakResult(True, "sympy", part)
