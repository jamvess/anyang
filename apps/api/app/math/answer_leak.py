"""Placeholder for the red run of /spec-to-tests (specs/features/ai/answer-leak-check.md); built
by /implement-feature."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LeakProblem:
    reference_answer: str
    answer_format: str
    expression: str


def leaks_by_sympy(answer_format, reference_answer, problem_expression, parts):  # type: ignore[no-untyped-def]
    raise NotImplementedError


async def check_leak(reply, problem, *, enabled=None, timeout_s=None, pool=None):  # type: ignore[no-untyped-def]
    raise NotImplementedError
