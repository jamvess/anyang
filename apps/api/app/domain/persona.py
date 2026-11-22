"""Persona from free text, the merge done by code (specs/features/ai/persona-extract.md §2.4 ·
UM-05). Pure: no AI call, no I/O."""

from app.models.persona import BuddyParams, PersonaExtractResult, TutorParams


def merge_params[P: (TutorParams, BuddyParams)](base: P, extracted: PersonaExtractResult) -> P:
    raise NotImplementedError


def clean_refused(refused: list[str]) -> list[str]:
    raise NotImplementedError
