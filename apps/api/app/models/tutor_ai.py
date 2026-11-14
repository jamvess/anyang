"""Structured outputs of the AI calls of the tutor room (ai-orchestration §2.2).

`generate_problem` (specs/features/tutor/room-problems-db.md §2.3): code checks `expression`
against `reference_answer` with SymPy before the problem reaches the student (AM-11).
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

# The formats the answer checker grades (app/domain/checker.py · spec §2.3 item 2).
GradedFormat = Literal["expression", "factored", "equation"]


class SessionSummaryResult(BaseModel):
    """1-2 lines that end the session (session-end-db.md §2.3 · api.md v1.9 รอตัดสิน 6)."""

    lines: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]] = Field(
        min_length=1, max_length=2
    )


class GenerateProblemResult(BaseModel):
    text: str = Field(min_length=1)  # Thai with $…$ math, shown to the student
    text_latex: str = Field(min_length=1)  # one line for the problem card
    expression: str = Field(min_length=1)  # what SymPy evaluates to the answer
    answer_format: GradedFormat
    reference_answer: str = Field(min_length=1)
    solution_steps: list[str] = Field(min_length=1)
    skill: str | None = None  # "s<n>" of the skills given, or null
