"""SymPy service of the answer checker (ai-orchestration.md §2.4.3).

SymPy decides whether each answer line follows from the line before it and whether the final
answer equals the reference; the merge rules (app/domain/checker.py) turn that into a verdict.
The comparison runs in a warm worker process with a timeout from config, because ``simplify``
can hang and starting Python + SymPy takes almost the whole budget. No AI call, no database.
Spec: specs/features/check/sympy-service.md.
"""

import asyncio
import multiprocessing
import queue
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import Any

import sympy
from sympy.parsing.latex import parse_latex

from app.domain.checker import AnswerFormat, SympyResult
from app.settings import get_settings

# --- results --------------------------------------------------------------------------------

_NOT_PARSED = SympyResult(
    parsed=False, timed_out=False, final_equal=None, final_in_form=None, line_ok=[]
)
_UNDECIDED = SympyResult(
    parsed=True, timed_out=False, final_equal=None, final_in_form=None, line_ok=[]
)
_TIMED_OUT = SympyResult(
    parsed=True, timed_out=True, final_equal=None, final_in_form=None, line_ok=[]
)


class _Unsupported(Exception):
    """A line or the reference cannot be parsed, or is a kind of step we do not check."""


class _Undecided(Exception):
    """SymPy cannot say for sure whether two values are equal."""


# --- parsing (spec §2.1, §2.2) --------------------------------------------------------------

_SPACING = re.compile(r"\\left|\\right|\\[,;:! ]|\$|\s+")
_DEFINITION = re.compile(r"[a-zA-Z](?P<primes>'*)\([a-zA-Z]\)")
_OPEN, _CLOSE = "({[", ")}]"
_EULER = sympy.Symbol("e")
# antlr reads x(x^{2}-1) as a function x applied to x^2 - 1; a single letter that is not part
# of a command (\sin, \ln) and is followed by "(" is a product.
_LETTER_TIMES = re.compile(r"(?<![\\a-zA-Z])([a-zA-Z])\(")


@dataclass(frozen=True)
class _Expression:
    """A value, or a chain ``a = b = c`` of values (§10 decision 3)."""

    written: list[sympy.Expr]  # as parsed, for the factored-form check

    @property
    def steps(self) -> list[sympy.Expr]:
        return [step.doit() for step in self.written]

    @property
    def value(self) -> sympy.Expr:
        return self.steps[-1]


@dataclass(frozen=True)
class _Definition:
    """``f(x) = E``, ``f'(x) = E``, ...; ``order`` is the number of primes."""

    order: int
    body: sympy.Expr


@dataclass(frozen=True)
class _Equation:
    """One or more equations separated by commas, e.g. ``x=0, x=\\ln(2)``."""

    sides: list[tuple[sympy.Expr, sympy.Expr]]


_Line = _Expression | _Definition | _Equation


def _split_top_level(text: str, separator: str) -> list[str]:
    """Split on ``separator`` where it is not inside (), {} or []."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        elif ch == separator and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def _parse(latex: str) -> sympy.Expr:
    # The lark backend silently misreads lines such as 2x\sin(x)+x^{2}\cos(x) (PoC P1).
    try:
        expr = parse_latex(_LETTER_TIMES.sub(r"\1\\cdot(", latex), backend="antlr")
    except Exception as error:  # LaTeXParsingError, or a SymPy error while building the tree
        raise _Unsupported from error
    return expr.xreplace({_EULER: sympy.E})


def _classify(latex: str, answer_format: AnswerFormat) -> _Line:
    text = _SPACING.sub("", latex).removeprefix("=")
    if not text:
        raise _Unsupported
    parts = [_split_top_level(part, "=") for part in _split_top_level(text, ",")]
    if len(parts) == 1:
        sides = parts[0]
        if len(sides) == 1:
            return _Expression([_parse(sides[0])])
        definition = _DEFINITION.fullmatch(sides[0])
        if definition:
            if len(sides) != 2:
                raise _Unsupported
            return _Definition(len(definition["primes"]), _parse(sides[1]).doit())
        if answer_format != "equation":
            return _Expression([_parse(side) for side in sides])
    if answer_format == "equation" and all(len(sides) == 2 for sides in parts):
        return _Equation([(_parse(lhs), _parse(rhs)) for lhs, rhs in parts])
    raise _Unsupported


def _symbols(line: _Line) -> set[sympy.Symbol]:
    match line:
        case _Expression():
            exprs = line.written
        case _Definition():
            exprs = [line.body]
        case _Equation():
            exprs = [side for pair in line.sides for side in pair]
    return set().union(*(expr.free_symbols for expr in exprs))


def _variable(lines: list[_Line]) -> sympy.Symbol | None:
    """The one free symbol of the problem (§2.2). Several symbols, as in implicit dy/dx, are
    not supported (§10 decision 2)."""
    symbols = set().union(*(_symbols(line) for line in lines))
    if len(symbols) > 1:
        raise _Unsupported
    return next(iter(symbols), None)


# --- comparing (spec §2.3, §2.4) ------------------------------------------------------------


def _equal(a: sympy.Basic, b: sympy.Basic) -> bool:
    """simplify(a - b) == 0 (§2.4.3), with SymPy's numeric check when simplify is not enough."""
    if a == b:
        return True
    if not (isinstance(a, sympy.Expr) and isinstance(b, sympy.Expr)):
        raise _Undecided
    difference = sympy.simplify(a - b)
    if difference == 0:
        return True
    same = difference.equals(0)
    if same is None:
        raise _Undecided
    return bool(same)


def _decidable(solutions: sympy.Set) -> sympy.Set:
    """A ConditionSet or ImageSet means SymPy could not solve in closed form."""
    if isinstance(solutions, sympy.Union):
        for part in solutions.args:
            _decidable(part)
    elif not isinstance(solutions, (sympy.FiniteSet, sympy.Interval)) and (
        solutions is not sympy.S.EmptySet
    ):
        raise _Undecided
    return solutions


def _solve(expr: sympy.Expr, variable: sympy.Symbol | None) -> sympy.Set:
    if variable is None:
        raise _Unsupported
    return _decidable(sympy.solveset(expr, variable, sympy.S.Reals))


def _solutions(line: _Equation, variable: sympy.Symbol | None) -> sympy.Set:
    return sympy.Union(*(_solve(lhs - rhs, variable) for lhs, rhs in line.sides))


def _same_set(a: sympy.Set, b: sympy.Set) -> bool:
    if a == b:
        return True
    if isinstance(a, sympy.FiniteSet) and isinstance(b, sympy.FiniteSet):

        def covers(x: sympy.FiniteSet, y: sympy.FiniteSet) -> bool:
            return all(any(_equal(p, q) for q in y) for p in x)

        return covers(a, b) and covers(b, a)
    return False


def _chain_ok(start: sympy.Expr, steps: list[sympy.Expr]) -> bool:
    previous = [start, *steps[:-1]]
    return all([_equal(step, before) for step, before in zip(steps, previous, strict=True)])


def _line_ok(before: _Line, line: _Line, *, first: bool, variable: sympy.Symbol | None) -> bool:
    """Does ``line`` follow from ``before``? For line 1, ``before`` is the reference (§2.4)."""
    match line:
        case _Expression():
            if isinstance(before, _Expression):
                return _chain_ok(before.value, line.steps)
            if isinstance(before, _Definition):
                return _chain_ok(before.body, line.steps)
        case _Definition():
            if first:
                return True  # restates the problem (§10 decision 1)
            if isinstance(before, _Definition) and line.order > before.order:
                if variable is None:
                    raise _Unsupported
                derivative = sympy.diff(before.body, variable, line.order - before.order)
                return _equal(line.body, derivative)
        case _Equation():
            if isinstance(before, _Equation):
                return _same_set(_solutions(line, variable), _solutions(before, variable))
            if isinstance(before, _Definition):  # "set the derivative to 0"
                return _same_set(_solutions(line, variable), _solve(before.body, variable))
    raise _Unsupported


def _in_factored_form(written: sympy.Expr, variable: sympy.Symbol | None) -> bool:
    """Every non-constant factor as written cannot be factored further, and carries no
    constant that factor_list would pull out (3x + 6 = 3(x + 2) is not in form)."""

    def factors(expr: sympy.Expr) -> list[sympy.Expr]:
        if isinstance(expr, sympy.Mul):
            return [f for arg in expr.args for f in factors(arg)]
        if isinstance(expr, sympy.Pow) and isinstance(expr.base, sympy.Mul):
            return factors(expr.base)
        return [expr]

    for factor in factors(written):
        if variable is None or not factor.has(variable):
            continue
        base, _ = factor.as_base_exp()
        coefficient, irreducible = sympy.factor_list(base)
        if abs(coefficient) != 1 or len(irreducible) != 1 or irreducible[0][1] != 1:
            return False
    return True


def evaluate_lines(
    answer_format: AnswerFormat, reference_answer: str, lines: list[str]
) -> SympyResult:
    """Run the checks of spec §2 in this process. The worker pool calls this function."""
    if not lines:
        return _NOT_PARSED
    try:
        reference = _classify(reference_answer, answer_format)
        written = [_classify(line, answer_format) for line in lines]
        if isinstance(reference, _Equation) != (answer_format == "equation") or isinstance(
            reference, _Definition
        ):
            raise _Unsupported
        variable = _variable([reference, *written])

        line_ok = [
            _line_ok(before, line, first=i == 0, variable=variable)
            for i, (before, line) in enumerate(
                zip([reference, *written[:-1]], written, strict=True)
            )
        ]

        last = written[-1]
        final_in_form = None
        if answer_format == "equation":
            if not isinstance(last, _Equation):
                raise _Unsupported
            final_equal = _same_set(_solutions(last, variable), _solutions(reference, variable))
        else:
            if isinstance(last, _Equation):
                raise _Unsupported
            value = last.value if isinstance(last, _Expression) else last.body
            final_equal = _equal(value, reference.value)
            if answer_format == "factored":
                if not isinstance(last, _Expression):
                    raise _Unsupported
                final_in_form = _in_factored_form(last.written[-1], variable)
    except _Unsupported:
        return _NOT_PARSED
    except _Undecided:
        return _UNDECIDED
    except Exception:  # SymPy raises many error types (NotImplementedError, PolynomialError, ...)
        return _UNDECIDED
    return SympyResult(
        parsed=True,
        timed_out=False,
        final_equal=final_equal,
        final_in_form=final_in_form,
        line_ok=line_ok,
    )


# --- worker processes (spec §2.5) -----------------------------------------------------------


class SympyTimeoutError(Exception):
    """The worker did not answer within the timeout; it was stopped and replaced."""


_READY = "ready"


def _worker_main(conn: Any) -> None:
    """Loop of one worker process: run ``(fn, args)`` jobs until the pipe closes."""
    parse_latex("x", backend="antlr")  # load the grammar before saying ready
    conn.send(_READY)
    while True:
        try:
            job = conn.recv()
        except EOFError:
            return
        fn, args = job
        try:
            conn.send((True, fn(*args)))
        except Exception as error:
            conn.send((False, repr(error)))


class _Worker:
    def __init__(self, context: Any) -> None:
        self.conn, child = context.Pipe()
        self.process = context.Process(target=_worker_main, args=(child,), daemon=True)
        self.process.start()
        child.close()
        self.ready = False

    def wait_ready(self) -> None:
        """Starting Python + SymPy takes about 2 s; it does not count towards the timeout."""
        if not self.ready:
            if self.conn.recv() != _READY:
                raise RuntimeError("SymPy worker did not start")
            self.ready = True

    def stop(self) -> None:
        self.process.kill()
        self.process.join()
        self.conn.close()


class SympyWorkerPool:
    """Warm worker processes (``checker.sympy_workers``). A job that runs past its timeout gets
    its worker killed and replaced, so a hanging ``simplify`` never blocks a request."""

    def __init__(self, workers: int) -> None:
        self.workers = workers
        # spawn, not fork: the API process runs threads (asyncio, uvicorn).
        self._context = multiprocessing.get_context("spawn")
        self._idle: queue.Queue[_Worker] = queue.Queue()
        for _ in range(workers):
            self._idle.put(_Worker(self._context))

    async def run(self, fn: Callable[..., Any], *args: Any, timeout_s: float) -> Any:
        return await asyncio.to_thread(self._run, fn, args, timeout_s)

    def _run(self, fn: Callable[..., Any], args: tuple[Any, ...], timeout_s: float) -> Any:
        worker = self._idle.get()
        try:
            worker.wait_ready()
            worker.conn.send((fn, args))
            if not worker.conn.poll(timeout_s):
                worker.stop()
                worker = _Worker(self._context)
                raise SympyTimeoutError
            ok, value = worker.conn.recv()
        except (EOFError, OSError) as error:  # the worker died
            worker.stop()
            worker = _Worker(self._context)
            raise RuntimeError("SymPy worker stopped unexpectedly") from error
        finally:
            self._idle.put(worker)
        if not ok:
            raise RuntimeError(f"SymPy worker failed: {value}")
        return value

    def close(self) -> None:
        while True:
            try:
                self._idle.get_nowait().stop()
            except queue.Empty:
                return


@cache
def default_pool() -> SympyWorkerPool:
    """The pool shared by all requests, sized from config."""
    return SympyWorkerPool(workers=get_settings().learning.checker.sympy_workers)


async def check_lines(
    *,
    answer_format: AnswerFormat,
    reference_answer: str,
    lines: list[str],
    timeout_s: float | None = None,
    pool: SympyWorkerPool | None = None,
) -> SympyResult:
    """SymPy verdict for one answer (spec §3). ``timeout_s`` defaults to
    ``checker.sympy_timeout_seconds``; ``pool`` defaults to the shared pool."""
    if not lines:
        return _NOT_PARSED  # no answer: merge rules decide from the empty lines (§2.6)
    if timeout_s is None:
        timeout_s = get_settings().learning.checker.sympy_timeout_seconds
    pool = pool or default_pool()
    try:
        return await pool.run(
            evaluate_lines, answer_format, reference_answer, lines, timeout_s=timeout_s
        )
    except SympyTimeoutError:
        return _TIMED_OUT
