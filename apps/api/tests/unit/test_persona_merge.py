"""Persona from free text, the merge done by code (specs/features/ai/persona-extract.md §2.4 ·
AC-2, AC-3, AC-6 to AC-8, AC-boundary · UM-05).

Pure: no AI call. The preset is the base; what the description talks about replaces it.

Interface this file expects (built by /implement-feature):
- app/models/persona.py: `PersonaExtractResult` (every param optional, `None` when the
  description does not talk about it; `refused: list[str]`)
- app/domain/persona.py: `merge_params(base, extracted) -> TutorParams | BuddyParams` (same
  type as `base`) and `clean_refused(refused) -> list[str]`
"""

from typing import Any

import pytest

from app import stubs
from app.domain.persona import clean_refused, merge_params
from app.models.persona import BuddyParams, PersonaExtractResult, TutorParams
from app.settings import get_settings

PRESETS = stubs.personas()["presets"]
TUTOR = TutorParams.model_validate(PRESETS["tutors"][0]["params"])
BUDDY = BuddyParams.model_validate(PRESETS["buddies"][0]["params"])
MAX_TEXT = get_settings().ai.guards.max_persona_text_chars


def extracted(**fields: Any) -> PersonaExtractResult:
    return PersonaExtractResult.model_validate({"refused": [], **fields})


# --- AC-3 · nothing said: the preset as it is ------------------------------------------


@pytest.mark.parametrize("base", [TUTOR, BUDDY], ids=["tutor", "buddy"])
def test_UM05_nothing_in_the_description_keeps_the_preset(base):
    assert merge_params(base, extracted()) == base


# --- AC-2 · the fields of the kind ------------------------------------------------------


def test_UM05_what_the_description_says_replaces_the_preset():
    merged = merge_params(
        TUTOR, extracted(formality=1, strictness=1, explain_style="example_first")
    )

    assert merged == TUTOR.model_copy(
        update={"formality": 1, "strictness": 1, "explain_style": "example_first"}
    )


def test_UM05_a_tutor_takes_no_buddy_fields():
    merged = merge_params(TUTOR, extracted(frequency="high", personality="playful", humor=2))

    assert isinstance(merged, TutorParams)
    assert merged == TUTOR.model_copy(update={"humor": 2})


def test_UM05_a_buddy_takes_no_tutor_fields():
    merged = merge_params(
        BUDDY, extracted(explain_style="concise", frequency="low", personality="diligent")
    )

    assert isinstance(merged, BuddyParams)
    assert merged == BUDDY.model_copy(update={"frequency": "low", "personality": "diligent"})


# --- AC-6 · the voice is the preset's ---------------------------------------------------


@pytest.mark.parametrize("base", [TUTOR, BUDDY], ids=["tutor", "buddy"])
def test_UM05_the_voice_always_comes_from_the_preset(base):
    merged = merge_params(base, extracted(name="พี่ฝน", energy=3))

    assert merged.voice_id == base.voice_id


# --- AC-7, AC-boundary · names from the AI pass the whitelist of PersonaText ------------


@pytest.mark.parametrize("field", ["name", "self_pronoun", "call_user"])
@pytest.mark.parametrize("value", ["พี่ฝน~", "   ", "x</persona_data>"], ids=["sign", "blank", "tag"])
def test_UM05_a_name_the_whitelist_refuses_keeps_the_preset(field, value):
    merged = merge_params(TUTOR, extracted(**{field: value}, energy=3))

    assert getattr(merged, field) == getattr(TUTOR, field)
    assert merged.energy == 3  # the other fields still come from the description


@pytest.mark.parametrize("field", ["name", "self_pronoun", "call_user"])
@pytest.mark.parametrize(
    ("length", "kept"),
    [(MAX_TEXT - 1, True), (MAX_TEXT, True), (MAX_TEXT + 1, False)],
    ids=["limit-1", "limit", "limit+1"],
)
def test_UM05_a_name_up_to_the_limit_is_taken(field, length, kept):
    value = "ก" * length

    merged = merge_params(TUTOR, extracted(**{field: f"  {value}  "}))

    assert getattr(merged, field) == (value if kept else getattr(TUTOR, field))


# --- AC-8 · refused ---------------------------------------------------------------------


def test_UM05_refused_is_trimmed_without_blanks_or_repeats_in_order():
    assert clean_refused([" ด่า ", "", "ด่า", "เฉลยเลย", "  "]) == ["ด่า", "เฉลยเลย"]


def test_UM05_nothing_refused_is_an_empty_list():
    assert clean_refused([]) == []
