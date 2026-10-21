"""Merge rules of the answer checker (ai-orchestration.md §2.4.5).

SymPy decides right or wrong and which line went wrong; the LLM classifier (`check_answer`)
names the error type; this module joins the two with fixed rules (CLAUDE.md rule 1). Pure
function: no AI call, no database. Spec: specs/features/check/merge-rules.md.
"""

from dataclasses import dataclass
from typing import Literal

AnswerFormat = Literal["expression", "factored", "equation"]
Verdict = Literal["correct", "correct_with_flaw", "incomplete", "incorrect"]
ErrorType = Literal["calculation", "sign", "wrong_method", "concept", "prerequisite", "no_answer"]
Method = Literal["doc", "other"]
DecidedBy = Literal["sympy", "llm"]

# Code and SymPy do not guess (spec §10 decision 4).
CERTAIN = 1.0


@dataclass(frozen=True)
class SympyResult:
    """What the SymPy service (app/math) returns for one answer (spec §3, agreed with Junior).

    ``line_ok[i]`` says line i + 1 equals the line before it (line 1 is compared with the
    problem). ``final_in_form`` is only set for ``factored``."""

    parsed: bool
    timed_out: bool
    final_equal: bool | None
    final_in_form: bool | None
    line_ok: list[bool]


@dataclass(frozen=True)
class LlmResult:
    """Output of the ``check_answer`` classifier (§2.4.4). ``verdict`` and ``first_wrong_line``
    are only used when SymPy cannot decide."""

    error_type: ErrorType | None
    evidence: str
    method: Method
    verdict: Verdict | None
    first_wrong_line: int | None
    confidence: float


@dataclass(frozen=True)
class CheckResult:
    """What goes into ``attempts`` and the SSE ``verdict`` event (§2.4.5)."""

    verdict: Verdict
    final_answer_correct: bool
    first_wrong_line: int | None
    error_type: ErrorType | None
    evidence: str
    method: Method
    decided_by: DecidedBy
    confidence: float
    is_correct: bool
    disagreement: bool


def _first_false(flags: list[bool]) -> int | None:
    """1-based number of the first line that is not equal to the line before it."""
    return next((i for i, ok in enumerate(flags, start=1) if not ok), None)


def merge_check(
    *, answer_format: AnswerFormat, lines: list[str], sympy: SympyResult, llm: LlmResult
) -> CheckResult:
    def result(
        verdict: Verdict,
        *,
        first_wrong_line: int | None,
        error_type: ErrorType | None,
        final_answer_correct: bool,
        decided_by: DecidedBy = "sympy",
        confidence: float = CERTAIN,
    ) -> CheckResult:
        right = verdict == "correct"
        disagreement = (
            decided_by == "sympy"
            and llm.verdict is not None
            and (llm.verdict == "correct") != right
        )
        return CheckResult(
            verdict=verdict,
            final_answer_correct=final_answer_correct,
            first_wrong_line=first_wrong_line,
            error_type=None if right else error_type,
            evidence=llm.evidence,
            method=llm.method,
            decided_by=decided_by,
            confidence=confidence,
            is_correct=right,  # correct_with_flaw counts as wrong (§2.4.9)
            disagreement=disagreement,
        )

    # 1. No answer: decided by code (§2.4.4).
    if not lines:
        return result(
            "incorrect", first_wrong_line=None, error_type="no_answer", final_answer_correct=False
        )

    # 2. SymPy cannot decide: the LLM's verdict stands (§2.4.3 Safety).
    if not sympy.parsed or sympy.timed_out or sympy.final_equal is None:
        verdict = llm.verdict or "incorrect"
        return result(
            verdict,
            first_wrong_line=llm.first_wrong_line,
            error_type=llm.error_type,
            final_answer_correct=verdict in ("correct", "correct_with_flaw", "incomplete"),
            decided_by="llm",
            confidence=llm.confidence,
        )

    wrong_line = _first_false(sympy.line_ok)

    if sympy.final_equal:
        # 5. Equal but not in the form the problem asks for (only factored has a form).
        if answer_format == "factored" and sympy.final_in_form is False:
            return result(
                "incomplete", first_wrong_line=None, error_type="concept", final_answer_correct=True
            )
        # 3. Right everywhere.
        if wrong_line is None:
            return result(
                "correct", first_wrong_line=None, error_type=None, final_answer_correct=True
            )
        # 4. Two mistakes that cancel out.
        return result(
            "correct_with_flaw",
            first_wrong_line=wrong_line,
            error_type=llm.error_type,
            final_answer_correct=True,
        )

    # 6. Wrong final answer: SymPy's first wrong line, else the LLM's, else the last line.
    return result(
        "incorrect",
        first_wrong_line=wrong_line or llm.first_wrong_line or len(lines),
        error_type=llm.error_type,
        final_answer_correct=False,
    )
