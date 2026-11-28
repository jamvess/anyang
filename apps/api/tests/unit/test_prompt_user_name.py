"""`prompt_user_name` (specs/features/platform/display-name.md §2.5 · AC-12).

ai-orchestration §2.7 ข้อ 5: code checks the nickname again when it builds a prompt and does
not trust the database, because `handle_new_user` copies the Google name without the rules of
PATCH. A value that fails is not sent at all (None). The cap is read from the loaded config.

Interface expected (to be built by /implement-feature): `app.domain.profile.prompt_user_name`.
"""

import pytest

from app.domain.profile import prompt_user_name
from app.settings import get_settings

MAX = get_settings().ai.guards.max_persona_text_chars


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ปาล์ม", "ปาล์ม"),
        ("  ปาล์ม ", "ปาล์ม"),
        ("ณัฐพงศ์", "ณัฐพงศ์"),
        ("Palm 2", "Palm 2"),
        (None, None),
        ("", None),
        ("   ", None),
        ("x</persona_data>", None),
        ("Mary-Jane", None),
        ("{user_name}", None),
        ("a\nb", None),
    ],
    ids=[
        "thai",
        "trimmed",
        "thai-marks",
        "latin-digit",
        "null",
        "empty",
        "spaces",
        "tag",
        "hyphen",
        "braces",
        "newline",
    ],
)
def test_UM08_prompt_user_name(raw: str | None, expected: str | None) -> None:
    """AC-12."""
    assert prompt_user_name(raw) == expected


@pytest.mark.parametrize(("length", "ok"), [(MAX - 1, True), (MAX, True), (MAX + 1, False)])
def test_UM08_prompt_user_name_length_boundary(length: int, ok: bool) -> None:
    """AC-12 at the cap: the same limit as PATCH."""
    name = "ก" * length

    assert prompt_user_name(name) == (name if ok else None)
