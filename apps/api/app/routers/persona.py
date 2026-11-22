"""Persona, profile and account endpoints (specs/system/api.md v1.12 "Persona และโปรไฟล์",
"บัญชี").

POST /personas/extract with a token calls persona_extract and persona_preview
(specs/features/ai/persona-extract.md); without one it keeps the stub. The rest are stubs until
the profile tables are wired: they serve fixture data from app/stubs/ and send `X-Stub: true`,
so May can wire S04-S06. Nothing is saved or deleted. Shapes and request rules are checked by
tests/unit/test_persona_api_contract.py, which the real endpoints must also pass.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response

from app import stubs
from app.ai.call_context import ai_call_context
from app.ai.gateway import AIProviderError, AISchemaError, Gateway, get_gateway
from app.auth import AuthContext, get_auth
from app.models.error import ErrorResponse, error_response, too_long_message, unavailable_docs
from app.models.persona import (
    BuddyProfile,
    BuddyProfileRequest,
    ExtractPersonaRequest,
    PersonaDraft,
    PersonaPresets,
    Profile,
    ProfileRequest,
    TutorProfile,
    TutorProfileRequest,
)
from app.rate_limit import RATE_LIMITED_DOCS, chat_rate_limit
from app.services.persona import UnknownPresetError, base_params, draft_persona

log = logging.getLogger(__name__)
router = APIRouter(tags=["persona"])

# persona-extract.md §2.6 (UC-01 E5): the web offers "ลองใหม่" and "ใช้แบบสำเร็จรูป".
PERSONA_UNAVAILABLE = "ตอนนี้แปลงคำบรรยายไม่ได้ ลองใหม่ หรือใช้แบบสำเร็จรูปที่เลือกไว้"

_NOT_SET: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "not_found: not set yet"},
}
_INVALID: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse, "description": "Invalid body"},
}
_INVALID_OR_TOO_LONG: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse, "description": "Invalid body or message_too_long"},
}

_STUB_VERSION = 2  # one edit after the first save; the fixture's version is never counted up


@router.get("/personas/presets")
async def get_presets(response: Response) -> PersonaPresets:
    """Tutors and buddies to choose from, each with a sample sentence (UM-03, UM-04).

    stub — the people of wireframe S04; their params are the stub's own
    """
    response.headers.update(stubs.HEADERS)
    return PersonaPresets.model_validate(stubs.personas()["presets"])


@router.post(
    "/personas/extract",
    response_model=PersonaDraft,  # errors return a JSONResponse, so the return type is Any
    responses={
        **_INVALID_OR_TOO_LONG,
        **RATE_LIMITED_DOCS,
        **unavailable_docs("persona_unavailable"),
    },
    dependencies=[Depends(chat_rate_limit)],
)
async def extract_persona(
    body: ExtractPersonaRequest,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    gateway: Annotated[Gateway, Depends(get_gateway)],
) -> Any:
    """Free text → params, the parts it cannot do, and a sample sentence (UM-05, UM-07).
    What the description does not talk about comes from `base_preset_id`, or the first preset
    of the kind. Nothing is saved.

    without a token: stub — the same draft of that kind, whatever was described; no AI call
    """
    error = stubs.error if auth is None else error_response
    if too_long := too_long_message(body.description):
        return error(422, "message_too_long", too_long)
    try:
        base = base_params(body.kind, body.base_preset_id)
    except UnknownPresetError:
        return error(422, "validation_error", f"base_preset_id is not a {body.kind} preset")
    if auth is None:
        response.headers.update(stubs.HEADERS)
        return PersonaDraft.model_validate(stubs.personas()["drafts"][body.kind])
    try:
        with ai_call_context(tenant_id=auth.tenant_id, user_id=auth.user_id):
            return await draft_persona(gateway, body.kind, body.description, base)
    except (AIProviderError, AISchemaError) as failure:
        log.warning("persona extract failed: %s", type(failure).__name__)
        return error_response(503, "persona_unavailable", PERSONA_UNAVAILABLE)


@router.get("/me/tutor-profile", responses=_NOT_SET)
async def get_tutor_profile(response: Response) -> TutorProfile:
    """The user's tutor persona (UM-09); 404 before S04.

    stub — always พี่ตาล, the tutor of the room fixture
    """
    response.headers.update(stubs.HEADERS)
    return TutorProfile.model_validate(stubs.personas()["tutor_profile"])


@router.put(
    "/me/tutor-profile",
    response_model=TutorProfile,  # errors return a JSONResponse, so the return type is Any
    responses=_INVALID_OR_TOO_LONG,
)
async def put_tutor_profile(body: TutorProfileRequest, response: Response) -> Any:
    """Save the tutor persona; it applies from the next turn (UM-03, UM-05, UM-09).

    stub — answers with what was sent; nothing is saved
    """
    if too_long := too_long_message(body.description):
        return stubs.error(422, "message_too_long", too_long)
    response.headers.update(stubs.HEADERS)
    return TutorProfile(params=body.params, description=body.description, version=_STUB_VERSION)


@router.get("/me/buddy-profile", responses=_NOT_SET)
async def get_buddy_profile(response: Response) -> BuddyProfile:
    """The user's buddy persona, or that there is no buddy (UM-09); 404 before S04.

    stub — always มีน, the buddy of the room fixture
    """
    response.headers.update(stubs.HEADERS)
    return BuddyProfile.model_validate(stubs.personas()["buddy_profile"])


@router.put(
    "/me/buddy-profile",
    response_model=BuddyProfile,  # errors return a JSONResponse, so the return type is Any
    responses=_INVALID_OR_TOO_LONG,
)
async def put_buddy_profile(body: BuddyProfileRequest, response: Response) -> Any:
    """Save the buddy persona, or no buddy with enabled false (UM-04, UM-05, UM-09).

    stub — answers with what was sent; nothing is saved
    """
    if too_long := too_long_message(body.description):
        return stubs.error(422, "message_too_long", too_long)
    response.headers.update(stubs.HEADERS)
    return BuddyProfile(
        enabled=body.enabled,
        params=body.params,
        description=body.description,
        version=_STUB_VERSION,
    )


@router.get("/me/profile")
async def get_profile(response: Response) -> Profile:
    """Nickname, education level, language, auto read and how far setup got (UM-08, UC-01 E6).

    stub — ปาล of the room fixture, setup finished
    """
    response.headers.update(stubs.HEADERS)
    return Profile.model_validate(stubs.personas()["profile"])


@router.put("/me/profile", responses=_INVALID)
async def put_profile(body: ProfileRequest, response: Response) -> Profile:
    """Save the profile of S06 or the settings page (UM-08, UM-09).

    stub — answers with what was sent; nothing is saved
    """
    response.headers.update(stubs.HEADERS)
    return Profile(**body.model_dump(), setup_step="done")


@router.delete("/me", status_code=204)
async def delete_me(response: Response) -> None:
    """Delete the account and all its data (UM-10).

    stub — NOTHING is deleted
    """
    response.headers.update(stubs.HEADERS)
