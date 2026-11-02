"""Cases found by the self-review of PR #104 (api.md v1.9)."""

import pytest

from app.models.room import SessionEndEvent


@pytest.mark.parametrize("lines", [[""], ["   "], ["บรรทัด 1", ""]])
def test_PM05_summary_lines_are_not_blank(lines: list[str]) -> None:
    with pytest.raises(ValueError):
        SessionEndEvent.model_validate({"summary_lines": lines})
