"""Structured output of the ``check_answer`` classifier (ai-orchestration.md §2.4.4).

The gateway validates the model's JSON against ``CheckAnswerResult`` and retries when it does
not match (AI-05); the pipeline then turns it into the ``LlmResult`` the merge rules take.
Spec: specs/features/check/check-answer-classifier.md §2.5.
"""

from pydantic import BaseModel, Field

from app.domain.checker import ErrorType, LlmResult, Method, Verdict


class CheckAnswerResult(BaseModel):
    error_type: ErrorType | None
    evidence: str
    method: Method
    verdict: Verdict | None
    first_wrong_line: int | None = Field(ge=1)
    confidence: float = Field(ge=0, le=1)

    def to_llm_result(self, *, line_count: int) -> LlmResult:
        """The model may point at a line the answer does not have; that line is dropped."""
        line = self.first_wrong_line
        return LlmResult(
            error_type=self.error_type,
            evidence=self.evidence,
            method=self.method,
            verdict=self.verdict,
            first_wrong_line=line if line is not None and line <= line_count else None,
            confidence=self.confidence,
        )
