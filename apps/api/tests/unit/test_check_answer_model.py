"""Output schema of the check_answer classifier.

Spec: specs/features/check/check-answer-classifier.md §2.5 (AC-8, AC-19, AC-20). The gateway
validates the model's JSON with this schema and retries when it fails (AI-05).
"""

import json

import pytest
from pydantic import ValidationError

from app.domain.checker import LlmResult
from app.models.check import CheckAnswerResult

VALID = {
    "error_type": "sign",
    "evidence": "บรรทัด 2: -3 กลายเป็น +3",
    "method": "doc",
    "verdict": "incorrect",
    "first_wrong_line": 2,
    "confidence": 0.9,
}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("error_type", "typo"),
        ("verdict", "maybe"),
        ("method", "sheet"),
        ("confidence", 1.5),
        ("confidence", -0.1),
        ("first_wrong_line", 0),
    ],
)
def test_AI05_out_of_schema_values_are_rejected(field: str, value: object) -> None:
    # AC-19
    with pytest.raises(ValidationError):
        CheckAnswerResult.model_validate_json(json.dumps({**VALID, field: value}))


@pytest.mark.parametrize("confidence", [0.0, 1.0])
def test_AI05_confidence_bounds_are_inclusive(confidence: float) -> None:
    # AC-19 boundary: 0 and 1 are valid
    result = CheckAnswerResult.model_validate({**VALID, "confidence": confidence})

    assert result.confidence == confidence


def test_AM06_valid_output_converts_to_llm_result() -> None:
    # AC-20
    result = CheckAnswerResult.model_validate_json(json.dumps(VALID, ensure_ascii=False))

    assert result.to_llm_result(line_count=3) == LlmResult(**VALID)


def test_AM06_null_error_type_and_verdict_are_allowed() -> None:
    # §2.5: null error_type when the LLM thinks the answer is right; null verdict allowed.
    result = CheckAnswerResult.model_validate(
        {**VALID, "error_type": None, "verdict": None, "first_wrong_line": None}
    )

    llm = result.to_llm_result(line_count=3)
    assert llm.error_type is None
    assert llm.verdict is None


@pytest.mark.parametrize(("line", "kept"), [(3, 3), (4, None)])
def test_AM05_first_wrong_line_must_exist_in_the_answer(line: int, kept: int | None) -> None:
    # AC-8 boundary: line_count = 3 -> line 3 kept, line 4 dropped.
    result = CheckAnswerResult.model_validate({**VALID, "first_wrong_line": line})

    assert result.to_llm_result(line_count=3).first_wrong_line == kept
