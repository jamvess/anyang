"""Check one answer: SymPy -> ``check_answer`` classifier -> merge rules (ai-orchestration §2.4).

SymPy decides right or wrong and the wrong line whenever it can (CLAUDE.md rule 4); the LLM
names the error type, the evidence and the method, and decides only when SymPy cannot; the
merge rules (app/domain/checker.py) join the two. The caller writes ``attempts`` and sends the
SSE ``verdict``. Spec: specs/features/check/check-answer-classifier.md.
"""

from dataclasses import dataclass

from app import ai
from app.ai.gateway import Gateway
from app.domain.checker import AnswerFormat, CheckResult, LlmResult, SympyResult, merge_check
from app.math.sympy_service import SympyWorkerPool, check_lines, detect_sign_flip
from app.models.check import CheckAnswerResult

# No answer is decided by code (merge rules rule 1), which reads none of these fields
# (spec §10 decision 1).
_NO_ANSWER_LLM = LlmResult(
    error_type="no_answer",
    evidence="",
    method="doc",
    verdict=None,
    first_wrong_line=None,
    confidence=1.0,
)
_NO_SOLUTION_STEPS = "(none: the course sheet gives no method for this problem)"


@dataclass(frozen=True)
class CheckProblem:
    """The fields of ``problems`` the checker needs (§2.4.2)."""

    text: str
    reference_answer: str
    answer_format: AnswerFormat
    solution_steps: list[str]


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def describe_sympy(answer_format: AnswerFormat, sympy: SympyResult) -> str:
    """The SymPy result as short sentences for the prompt, so the LLM does not have to read
    the fields itself (spec §2.3)."""
    if not sympy.parsed or sympy.timed_out or sympy.final_equal is None:
        return (
            "decided: no (SymPy could not check this answer)\n"
            "Decide the verdict, first_wrong_line and confidence yourself."
        )
    facts = ["decided: yes", f"final answer equals reference: {_yes_no(sympy.final_equal)}"]
    if answer_format == "factored" and sympy.final_in_form is not None:
        facts.append(f"final answer fully factored: {_yes_no(sympy.final_in_form)}")
    for number, ok in enumerate(sympy.line_ok, start=1):
        before = "the reference" if number == 1 else f"line {number - 1}"
        verb = "follows" if ok else "does NOT follow"
        facts.append(f"line {number}: {verb} from {before}")
    return "\n".join(facts)


def _prompt_input(
    problem: CheckProblem, lines: list[str], sympy: SympyResult, sign_flip: int | None
) -> dict[str, str]:
    return {
        "problem": problem.text,
        "reference_answer": problem.reference_answer,
        "answer_format": problem.answer_format,
        "solution_steps": "\n".join(problem.solution_steps) or _NO_SOLUTION_STEPS,
        "answer_lines": "\n".join(f"{n}. {line}" for n, line in enumerate(lines, start=1)),
        "sympy_result": describe_sympy(problem.answer_format, sympy),
        "hints": f"sign_flip_detected: line {sign_flip}" if sign_flip else "none",
    }


async def check_answer(
    problem: CheckProblem,
    lines: list[str],
    *,
    gateway: Gateway | None = None,
    pool: SympyWorkerPool | None = None,
) -> CheckResult:
    """Verdict for one confirmed answer (spec §2.1). ``gateway`` and ``pool`` default to the
    shared ones. ``AISchemaError`` / ``AIProviderError`` reach the caller: no error type is
    guessed when the classifier fails (§10 decision 2)."""
    if not lines:
        return merge_check(
            answer_format=problem.answer_format,
            lines=lines,
            sympy=SympyResult(
                parsed=False, timed_out=False, final_equal=None, final_in_form=None, line_ok=[]
            ),
            llm=_NO_ANSWER_LLM,
        )

    sympy = await check_lines(
        answer_format=problem.answer_format,
        reference_answer=problem.reference_answer,
        lines=lines,
        pool=pool,
    )
    sign_flip = None
    if sympy.final_equal is not None and not all(sympy.line_ok):
        sign_flip = await detect_sign_flip(
            answer_format=problem.answer_format,
            reference_answer=problem.reference_answer,
            lines=lines,
            pool=pool,
        )

    call = gateway.call if gateway is not None else ai.call
    output = await call(
        "check_answer", _prompt_input(problem, lines, sympy, sign_flip), CheckAnswerResult
    )
    return merge_check(
        answer_format=problem.answer_format,
        lines=lines,
        sympy=sympy,
        llm=output.to_llm_result(line_count=len(lines)),
    )
