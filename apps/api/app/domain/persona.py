"""Persona from free text, the merge done by code (specs/features/ai/persona-extract.md §2.4 ·
UM-05). Pure: no AI call, no I/O.

The preset is the base. A field the description talks about replaces it; a name that fails the
whitelist of PersonaText keeps the preset's, and the voice is always the preset's.
"""

import logging
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.models.persona import BuddyParams, PersonaExtractResult, PersonaText, TutorParams

log = logging.getLogger(__name__)

_NAMES = ("name", "self_pronoun", "call_user")
_PERSONA_TEXT = TypeAdapter(PersonaText)


def _name(field: str, value: str) -> str | None:
    try:
        return _PERSONA_TEXT.validate_python(value)
    except ValidationError:
        log.warning("persona_extract: %s fails the whitelist, the preset's is kept", field)
        return None


def merge_params[P: (TutorParams, BuddyParams)](base: P, extracted: PersonaExtractResult) -> P:
    said = extracted.model_dump(exclude_none=True, exclude={"refused"})
    change = {field: value for field, value in said.items() if field in type(base).model_fields}
    change.pop("voice_id", None)  # §2.4 item 4: never from the AI
    for field in _NAMES:
        if field in change and (name := _name(field, change[field])) is not None:
            change[field] = name
        else:
            change.pop(field, None)
    return type(base).model_validate({**base.model_dump(), **change})  # §2.4 item 6


_SCALES = {
    "formality": {1: "casual and friendly", 2: "polite but warm", 3: "formal"},
    "energy": {1: "calm", 2: "normal", 3: "lively"},
    "strictness": {1: "gentle", 2: "normal", 3: "strict"},
    "humor": {0: "serious", 1: "a little humor", 2: "jokes often"},
}
_CHOICES = {
    "explain_style": {
        "step_by_step": "explains every step",
        "example_first": "shows an example before the rule",
        "concise": "short, only what matters",
    },
    "frequency": {"low": "talks rarely", "med": "talks sometimes", "high": "talks often"},
    "personality": {
        "curious": "asks questions",
        "playful": "jokes and teases",
        "diligent": "hard-working, keeps the student on track",
    },
}


def describe_style(params: TutorParams | BuddyParams) -> str:
    """§2.5: the `style` input of persona_preview, written by code from the enum and number
    params only (no text the user typed), one setting per line."""
    values = params.model_dump()

    def line(field: str, words: dict[Any, str]) -> str:
        return f"{field}: {values[field]} ({words[values[field]]})"

    lines = [line(field, words) for field, words in _SCALES.items()]
    lines.append(f"emoji: {'on' if params.emoji else 'off'}")
    lines.extend(line(field, words) for field, words in _CHOICES.items() if field in values)
    return "\n".join(lines)


def clean_refused(refused: list[str]) -> list[str]:
    """§2.4 item 5: trimmed, no blanks, no repeats, in order."""
    return list(dict.fromkeys(part.strip() for part in refused if part.strip()))
