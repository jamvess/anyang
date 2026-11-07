"""API models of exam preps and materials (specs/system/api.md v1.10
"สร้างการเตรียมสอบและใส่ไฟล์").

The shape is a proposal pending Junior (api.md "รอตัดสิน (v1.10 · Junior)").
Material kinds and statuses repeat the check constraints of `materials` in 0001_init.sql;
they are schema rules, not learning-model thresholds. `stage` is computed by the backend
from the materials and the active scope version (api.md v1.10 `ExamPrep`).
"""

from datetime import date
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from app.models.base import ApiModel

MaterialKind = Literal["sheet", "slides", "past_exam", "notes", "other"]
MaterialStatus = Literal["uploaded", "classified", "confirmed", "ingesting", "ready", "failed"]

# File types a material may be (api.md v1.10 รอตัดสิน 1 · ai-orchestration §2.3.3).
MATERIAL_CONTENT_TYPES = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)


# --- exam preps ------------------------------------------------------------------


class CreateExamPrepRequest(ApiModel):
    """Body of POST /exam-preps (CM-01). A date before today is checked by the endpoint."""

    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    exam_date: date
    # None: the planner uses config/learning.yaml → planner.default_daily_minutes (UC-02 A1).
    daily_minutes: int | None = Field(default=None, ge=1)


class ExamPrep(ApiModel):
    """Response of POST /exam-preps and each row of GET /exam-preps."""

    id: UUID
    title: str
    exam_date: date
    days_left: int
    daily_minutes: int | None
    stage: Literal["materials", "processing", "scope", "tutoring"]
    readiness: float | None = Field(ge=0, le=1)  # null until stage is tutoring
    topics_not_passed: int | None = Field(ge=0)  # null until stage is tutoring


# --- materials --------------------------------------------------------------------


class UploadMaterialRequest(ApiModel):
    """Body of POST /exam-preps/{id}/materials (CM-03). The endpoint checks `content_type`
    against MATERIAL_CONTENT_TYPES and `size_bytes` against config/ai.yaml →
    guards.max_material_mb, or max_image_mb for an image. `size_bytes` is what the client
    declares, not the real size."""

    # Display only (materials.file_name), never a path.
    file_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    content_type: str
    size_bytes: int = Field(ge=1)


class MaterialUploadTicket(ApiModel):
    """PUT the file to `upload_url`, then call POST /materials/{material_id}/uploaded."""

    material_id: UUID
    upload_url: str
    path: str  # {tenant_id}/{exam_prep_id}/{material_id} (data-model.md)


class MaterialUploadedRequest(ApiModel):
    """Body of POST /materials/{id}/uploaded (CM-04)."""

    user_note: str | None = None


class Material(ApiModel):
    """Each row of GET /exam-preps/{id}/materials and the response of /uploaded."""

    id: UUID
    file_name: str
    kind: MaterialKind | None  # null until classified
    kind_confidence: float | None = Field(ge=0, le=1)
    kind_confirmed: bool
    user_note: str | None
    status: MaterialStatus
    error: str | None  # short text the user may see, when status is failed (UC-02 E5)


class ConfirmedKind(ApiModel):
    id: UUID
    kind: MaterialKind


class ConfirmMaterialsRequest(ApiModel):
    """Body of POST /exam-preps/{id}/materials/confirm (CM-06): the files to confirm, each once.
    Failed files are left out; files not sent are not checked, so files can be added later
    (CM-05)."""

    materials: list[ConfirmedKind] = Field(min_length=1)

    @model_validator(mode="after")
    def _each_file_once(self) -> Self:
        ids = [m.id for m in self.materials]
        if len(ids) != len(set(ids)):
            raise ValueError("each material id may appear once")
        return self


class MaterialsQueued(ApiModel):
    """Response of /materials/confirm: how many files started ingestion."""

    queued: int = Field(ge=0)
