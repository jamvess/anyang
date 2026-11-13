"""Structured outputs of the AI calls of the tutor room (ai-orchestration §2.2).

`generate_problem` (specs/features/tutor/room-problems-db.md §2.3): code checks `expression`
against `reference_answer` with SymPy before the problem reaches the student (AM-11).
"""

from typing import Literal

from pydantic import BaseModel, Field

# The formats the answer checker grades (app/domain/checker.py · spec §2.3 item 2).
GradedFormat = Literal["expression", "factored", "equation"]


class GenerateProblemResult(BaseModel):
    text: str = Field(min_length=1)  # Thai with $…$ math, shown to the student
    text_latex: str = Field(min_length=1)  # one line for the problem card
    expression: str = Field(min_length=1)  # what SymPy evaluates to the answer
    answer_format: GradedFormat
    reference_answer: str = Field(min_length=1)
    solution_steps: list[str] = Field(min_length=1)
    skill: str | None = None  # "s<n>" of the skills given, or null
