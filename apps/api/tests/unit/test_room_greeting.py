"""The room greeting from config/messages.yaml, and the room header names
(specs/features/tutor/room-sessions-db.md §2.5, §2.8 · AC-4, AC-boundary-greeting, AC-config,
AC-11).

Pure functions in `app.domain.room`; the templates are `RoomGreetingConfig` in app.settings,
loaded from config/messages.yaml like the other config files.
"""

from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.room import (
    FALLBACK_USER_NAME,
    BuddyFacts,
    greeting_text,
    room_names,
)
from app.settings import RoomGreetingConfig, get_settings

# Wording that is not the real one, so a test proves the text comes from config.
TEST_TEMPLATES: dict[str, str] = {
    "hello_named": "HI {user_name}!",
    "hello_anonymous": "HI!",
    "days_left_many": "{days_left} DAYS TO {prep_name}",
    "exam_today": "{prep_name} IS TODAY",
    "exam_passed": "{prep_name} IS OVER",
    "invite": "ASK AWAY",
}


@pytest.fixture
def templates() -> RoomGreetingConfig:
    return RoomGreetingConfig.model_validate(TEST_TEMPLATES)


@pytest.mark.parametrize(
    ("days_left", "expected"),
    [
        (2, "HI ปาล! 2 DAYS TO แคลคูลัส 1 ASK AWAY"),
        (1, "HI ปาล! 1 DAYS TO แคลคูลัส 1 ASK AWAY"),
        (0, "HI ปาล! แคลคูลัส 1 IS TODAY ASK AWAY"),
        (-1, "HI ปาล! แคลคูลัส 1 IS OVER ASK AWAY"),
    ],
)
def test_TM13_greeting_by_days_left(
    templates: RoomGreetingConfig, days_left: int, expected: str
) -> None:
    """AC-boundary-greeting: ≥ 1 → days_left_many, 0 → exam_today, < 0 → exam_passed."""
    text = greeting_text(templates, user_name="ปาล", prep_name="แคลคูลัส 1", days_left=days_left)

    assert text == expected


def test_TM13_greeting_without_a_nickname(templates: RoomGreetingConfig) -> None:
    """AC-boundary-greeting: no nickname → hello_anonymous."""
    text = greeting_text(templates, user_name=None, prep_name="แคลคูลัส 1", days_left=3)

    assert text == "HI! 3 DAYS TO แคลคูลัส 1 ASK AWAY"


def test_TM13_braces_in_user_values_are_kept_as_text(templates: RoomGreetingConfig) -> None:
    """AC-boundary-greeting: a name or title is a value, never a format string."""
    text = greeting_text(templates, user_name="{days_left}", prep_name="{x} {0}", days_left=0)

    assert text == "HI {days_left}! {x} {0} IS TODAY ASK AWAY"


def test_TM13_real_config_has_the_greeting() -> None:
    """AC-config: config/messages.yaml loads with every key."""
    greeting = get_settings().messages.room_greeting

    text = greeting_text(greeting, user_name="ปาล", prep_name="แคลคูลัส 1", days_left=5)

    assert "ปาล" in text and "แคลคูลัส 1" in text and "5" in text


@pytest.mark.parametrize("missing", list(TEST_TEMPLATES))
def test_TM13_config_with_a_missing_key_is_refused(missing: str) -> None:
    """AC-config."""
    data = {k: v for k, v in TEST_TEMPLATES.items() if k != missing}

    with pytest.raises(ValidationError):
        RoomGreetingConfig.model_validate(data)


@pytest.mark.parametrize(
    ("key", "template"),
    [
        ("hello_named", "HI {nickname}!"),  # unknown placeholder
        ("hello_anonymous", "HI {user_name}!"),  # not allowed for this key
        ("exam_today", "{days_left} {prep_name}"),  # days_left only in days_left_many
        ("invite", "ASK {prep_name}"),
        ("days_left_many", "{days_left} DAYS {"),  # broken template
    ],
)
def test_TM13_config_with_an_unknown_placeholder_is_refused(key: str, template: str) -> None:
    """AC-config: the placeholders of each key are the ones in spec §2.8."""
    with pytest.raises(ValidationError):
        RoomGreetingConfig.model_validate({**TEST_TEMPLATES, key: template})


def test_TM13_config_with_an_extra_key_is_refused() -> None:
    with pytest.raises(ValidationError):
        RoomGreetingConfig.model_validate({**TEST_TEMPLATES, "farewell": "BYE"})


# --- header names (§2.5 · AC-11) --------------------------------------------------------

PRESET = "พี่กร"


@pytest.mark.parametrize(
    ("nickname", "tutor_params", "buddy", "expected"),
    [
        # no profile at all
        (None, None, None, (FALLBACK_USER_NAME, PRESET, None)),
        # blank nickname
        ("  ", None, None, (FALLBACK_USER_NAME, PRESET, None)),
        # nickname trimmed
        (" ปาล ", None, None, ("ปาล", PRESET, None)),
        # tutor profile name
        ("ปาล", {"name": "พี่ตาล"}, None, ("ปาล", "พี่ตาล", None)),
        # tutor name missing, blank or not a string → preset
        ("ปาล", {}, None, ("ปาล", PRESET, None)),
        ("ปาล", {"name": "  "}, None, ("ปาล", PRESET, None)),
        ("ปาล", {"name": 3}, None, ("ปาล", PRESET, None)),
        # buddy enabled with a name
        ("ปาล", None, BuddyFacts(enabled=True, params={"name": "มีน"}), ("ปาล", PRESET, "มีน")),
        # buddy disabled, or no name
        ("ปาล", None, BuddyFacts(enabled=False, params={"name": "มีน"}), ("ปาล", PRESET, None)),
        ("ปาล", None, BuddyFacts(enabled=True, params={}), ("ปาล", PRESET, None)),
        ("ปาล", None, BuddyFacts(enabled=True, params=None), ("ปาล", PRESET, None)),
    ],
)
def test_TM13_room_names(
    nickname: str | None,
    tutor_params: dict[str, Any] | None,
    buddy: BuddyFacts | None,
    expected: tuple[str, str, str | None],
) -> None:
    names = room_names(
        nickname=nickname, tutor_params=tutor_params, buddy=buddy, preset_tutor_name=PRESET
    )

    assert (names.user_name, names.tutor_name, names.buddy_name) == expected


def test_TM13_fallback_user_name_is_khun() -> None:
    assert FALLBACK_USER_NAME == "คุณ"
