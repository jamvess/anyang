"""Persona from free text (specs/features/ai/persona-extract.md §2.1-§2.6 · UM-05, UM-07).

persona_extract reads the description, code merges it onto the preset, then persona_preview
writes a sample from the params alone: the description never reaches the preview (§2.5).
Nothing is saved. Gateway errors are left to the caller (§2.6: 503, no fallback).
"""

from typing import Literal

from app import stubs
from app.ai.gateway import Gateway
from app.domain.persona import clean_refused, describe_style, merge_params
from app.models.persona import (
    BuddyParams,
    PersonaDraft,
    PersonaExtractResult,
    PersonaPreviewResult,
    TutorParams,
)

Kind = Literal["tutor", "buddy"]


class UnknownPresetError(ValueError):
    """`base_preset_id` is not a preset of this kind (§2.2 · AC-5)."""


def base_params(kind: Kind, preset_id: str | None) -> TutorParams | BuddyParams:
    """§2.2: the params of the chosen preset, or of the first one of the kind. The list is the
    one GET /personas/presets serves (api.md รอตัดสิน v1.12 ข้อ 5: where presets live)."""
    group = stubs.personas()["presets"]["tutors" if kind == "tutor" else "buddies"]
    model = TutorParams if kind == "tutor" else BuddyParams
    if preset_id is None:
        return model.model_validate(group[0]["params"])
    for preset in group:
        if preset["id"] == preset_id:
            return model.model_validate(preset["params"])
    raise UnknownPresetError(f"no {kind} preset {preset_id!r}")


async def draft_persona(
    gateway: Gateway, kind: Kind, description: str, base: TutorParams | BuddyParams
) -> PersonaDraft:
    extracted = await gateway.call(
        "persona_extract", {"kind": kind, "description": description}, PersonaExtractResult
    )
    params = merge_params(base, extracted)
    preview = await gateway.call(
        "persona_preview",
        {
            "kind": kind,
            "style": describe_style(params),
            "name": params.name,
            "self_pronoun": params.self_pronoun,
            "call_user": params.call_user,
        },
        PersonaPreviewResult,
    )
    return PersonaDraft(
        params=params, refused=clean_refused(extracted.refused), sample=preview.sample
    )
