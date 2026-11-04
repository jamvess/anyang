"""API models of personas and profiles (specs/system/api.md v1.12 "Persona และโปรไฟล์").

The shape is a proposal pending Junior (api.md "รอตัดสิน (v1.12 · Junior)"). The params are
ai-orchestration §2.7. They reach the prompt through a template, and so does the nickname (§2.2
context layer 2), so the short texts pass a whitelist of characters and every other param is
strict: an enum or a small range, with no type coercion. `description` is the user's free text:
it is stored in `description_raw` and never reaches a prompt.
"""

from typing import Annotated, Literal, Self

from pydantic import Field, StrictBool, StrictInt, StringConstraints, model_validator

from app.models.base import ApiModel
from app.settings import get_settings

# ai-orchestration §2.7 "ผ่าน whitelist ตัวอักษร": Thai consonants, vowels, tone marks and digits
# (no ฿ ๏ ๚ ๛ and no unassigned code points of the block), Latin letters, digits and spaces.
_PERSONA_TEXT = "^[\u0e01-\u0e3a\u0e40-\u0e4e\u0e50-\u0e59A-Za-z0-9 ]+$"

NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# Stripped first, so spaces around a name neither reach the prompt nor use up the limit.
PersonaText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=_PERSONA_TEXT,
        max_length=get_settings().ai.guards.max_persona_text_chars,
    ),
]
OneToThree = Annotated[StrictInt, Field(ge=1, le=3)]
# Google TTS voice names; the allowed list is api.md รอตัดสิน v1.12 ข้อ 5.
VoiceId = Annotated[str, Field(pattern="^th-TH-[A-Za-z0-9-]{1,40}$")]


class _SharedParams(ApiModel):
    name: PersonaText
    self_pronoun: PersonaText
    call_user: PersonaText
    formality: OneToThree
    energy: OneToThree
    strictness: OneToThree
    humor: StrictInt = Field(ge=0, le=2)
    emoji: StrictBool
    voice_id: VoiceId


class TutorParams(_SharedParams):
    explain_style: Literal["step_by_step", "example_first", "concise"]


class BuddyParams(_SharedParams):
    frequency: Literal["low", "med", "high"]
    personality: Literal["curious", "playful", "diligent"]


# --- presets and extract ------------------------------------------------------------


class TutorPreset(ApiModel):
    id: str
    title: str  # e.g. "ใจเย็น"
    sample: str  # a sentence in this voice (UM-03)
    params: TutorParams


class BuddyPreset(ApiModel):
    id: str
    title: str
    sample: str
    params: BuddyParams


class PersonaPresets(ApiModel):
    """Response of GET /personas/presets. "No buddy" is the web's own choice, not a preset."""

    tutors: list[TutorPreset]
    buddies: list[BuddyPreset]


class ExtractPersonaRequest(ApiModel):
    """Body of POST /personas/extract. The endpoint checks the length against
    config/ai.yaml → guards.max_message_chars."""

    kind: Literal["tutor", "buddy"]
    description: NonBlank


class PersonaDraft(ApiModel):
    """Response of POST /personas/extract. Nothing is saved until PUT."""

    params: TutorParams | BuddyParams  # by the `kind` of the request
    refused: list[str]  # the parts it cannot do, for the box "ทำให้ไม่ได้: …" (UC-01 E4)
    sample: str  # persona_preview (UM-07)


# --- persona profiles ---------------------------------------------------------------


class TutorProfileRequest(ApiModel):
    """Body of PUT /me/tutor-profile. `description` is null for a preset."""

    params: TutorParams
    description: str | None


class TutorProfile(TutorProfileRequest):
    """Response of GET and PUT /me/tutor-profile."""

    version: int = Field(ge=1)


class BuddyProfileRequest(ApiModel):
    """Body of PUT /me/buddy-profile. No buddy (UC-01 A2) is `enabled: false`; params may stay,
    so turning the buddy back on does not lose them."""

    enabled: StrictBool
    params: BuddyParams | None
    description: str | None

    @model_validator(mode="after")
    def _on_needs_params(self) -> Self:
        if self.enabled and self.params is None:
            raise ValueError("enabled needs params")
        return self


class BuddyProfile(BuddyProfileRequest):
    """Response of GET and PUT /me/buddy-profile."""

    version: int = Field(ge=1)


# --- profile -----------------------------------------------------------------------

EducationLevel = Literal["lower_secondary", "upper_secondary", "university", "other"]
ExplainLanguage = Literal["th_en", "th", "en"]  # ไทย + ศัพท์อังกฤษ / ไทยล้วน / English


class ProfileRequest(ApiModel):
    """Body of PUT /me/profile."""

    nickname: PersonaText  # reaches the prompt like the persona params
    education_level: EducationLevel
    explain_language: ExplainLanguage
    auto_read: StrictBool  # TM-09; has no column yet (api.md รอตัดสิน v1.12 ข้อ 1)


class Profile(ApiModel):
    """Response of GET and PUT /me/profile."""

    nickname: str | None  # the signup trigger copies it from the Google name
    education_level: EducationLevel | None  # null until S06
    explain_language: ExplainLanguage
    auto_read: bool
    # Computed: crew without a tutor or buddy profile, then profile while education_level is
    # null, else done. The web returns to the page left unfinished (UC-01 E6).
    setup_step: Literal["crew", "profile", "done"]
