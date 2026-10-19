"""Output model of vision_extract_pages: every page of a scanned file in one call (PoC P3).

Added after the free tier allowed only 20 requests per day per model: one call per exam
instead of one per page. prompts/README.md rule 4: prompt schema and model must match.
"""

import pytest
from pydantic import ValidationError

from app.models.scope_ai import VisionExtractPagesResult
from tests.unit.test_scope_ai_models import keys_of, keys_of_model, list_shape, prompt_schema


def test_AI05_vision_extract_pages_prompt_schema_matches_model():
    assert list_shape(keys_of(prompt_schema("vision_extract_pages"))) == list_shape(
        keys_of_model(VisionExtractPagesResult)
    )


def test_SM01_vision_extract_pages_accepts_pages_in_order():
    result = VisionExtractPagesResult.model_validate(
        {"pages": [{"page": 1, "text": "หมวด ก"}, {"page": 2, "text": ""}], "notes": ""}
    )
    assert [p.page for p in result.pages] == [1, 2]


@pytest.mark.parametrize("pages", [[2, 3], [1, 3], [2, 1], [1, 1]])
def test_SM01_vision_extract_pages_must_be_numbered_1_to_n(pages: list[int]):
    with pytest.raises(ValidationError, match=r"1..n"):
        VisionExtractPagesResult.model_validate(
            {"pages": [{"page": n, "text": "x"} for n in pages], "notes": ""}
        )
