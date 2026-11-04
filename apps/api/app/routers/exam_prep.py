"""Exam prep and material endpoints (specs/system/api.md v1.10 "สร้างการเตรียมสอบและใส่ไฟล์").

Stubs until materials are stored and classified: they serve fixture data from app/stubs/ and
send `X-Stub: true`, so May can wire S07-S10 (UC-02 steps 1-5). Nothing is saved. Shapes and
request rules are checked by tests/unit/test_exam_prep_api_contract.py, which the real
endpoints must also pass.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Path, Response

from app import stubs
from app.auth import AuthContext, get_auth
from app.models.error import ErrorResponse, error_docs
from app.models.exam_prep import (
    MATERIAL_CONTENT_TYPES,
    ConfirmMaterialsRequest,
    CreateExamPrepRequest,
    ExamPrep,
    Material,
    MaterialsQueued,
    MaterialUploadedRequest,
    MaterialUploadTicket,
    UploadMaterialRequest,
)
from app.models.room import bare_content_type

router = APIRouter(tags=["exam_prep"])

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
MaterialId = Annotated[UUID, Path(alias="id")]

# api.md v1.10: days are counted in Asia/Bangkok, which has no DST.
_BANGKOK = timezone(timedelta(hours=7))


def _today() -> date:
    return datetime.now(_BANGKOK).date()


# --- exam preps ------------------------------------------------------------------


@router.post(
    "/exam-preps",
    status_code=201,
    response_model=ExamPrep,  # errors return a JSONResponse, so the return type is Any
    responses={
        422: {"model": ErrorResponse, "description": "Invalid body or exam_date_past"},
    },
)
async def create_exam_prep(body: CreateExamPrepRequest, response: Response) -> Any:
    """New exam prep from S07-S08 (CM-01). Today is a valid exam date; earlier is not.

    stub — the prep is not saved, so it is not in GET /exam-preps
    """
    days_left = (body.exam_date - _today()).days
    if days_left < 0:
        return stubs.error(422, "exam_date_past", "exam_date is before today")
    response.headers.update(stubs.HEADERS)
    return ExamPrep(
        id=uuid4(),
        title=body.title,
        exam_date=body.exam_date,
        days_left=days_left,
        daily_minutes=body.daily_minutes,
        stage="materials",
        readiness=None,
        topics_not_passed=None,
    )


@router.get("/exam-preps")
async def list_exam_preps(response: Response) -> list[ExamPrep]:
    """The user's exam preps, soonest exam first, archived ones left out (PM-04).

    stub — one prep in each stage; exam dates count from today
    """
    response.headers.update(stubs.HEADERS)
    rows = sorted(stubs.exam_preps(), key=lambda row: row["days_left"])
    today = _today()
    return [
        ExamPrep.model_validate({**row, "exam_date": today + timedelta(days=row["days_left"])})
        for row in rows
    ]


# --- materials --------------------------------------------------------------------


@router.post(
    "/exam-preps/{id}/materials",
    response_model=MaterialUploadTicket,  # errors return a JSONResponse, so the return type is Any
    responses=error_docs("Invalid path or body, or unsupported_type"),
)
async def create_material(
    prep_id: PrepId,
    body: UploadMaterialRequest,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> Any:
    """Signed upload URL for one file (CM-03). The type is checked before the browser sends it.

    stub — the URL is not a real Storage URL and no materials row is made
    """
    if bare_content_type(body.content_type) not in MATERIAL_CONTENT_TYPES:
        return stubs.error(422, "unsupported_type", f"{body.content_type} is not accepted")
    response.headers.update(stubs.HEADERS)
    material_id = uuid4()
    path = f"{stubs.tenant_of(auth)}/{prep_id}/{material_id}"
    return MaterialUploadTicket(
        material_id=material_id, upload_url=f"{stubs.STORAGE_URL}/{path}", path=path
    )


@router.post(
    "/materials/{id}/uploaded",
    status_code=202,
    responses=error_docs("Invalid path or body", "already_uploaded"),
)
async def material_uploaded(
    material_id: MaterialId, body: MaterialUploadedRequest, response: Response
) -> Material:
    """The browser finished the upload; classification starts (CM-04, §2.3.2 step 2).

    stub — answers with the fixture file that is still being classified
    """
    response.headers.update(stubs.HEADERS)
    row = next(m for m in stubs.materials() if m["status"] == "uploaded")
    return Material.model_validate({**row, "id": material_id, "user_note": body.user_note})


@router.get("/exam-preps/{id}/materials", responses=error_docs())
async def list_materials(prep_id: PrepId, response: Response) -> list[Material]:
    """Files of this exam prep, oldest first; S10 polls until every file has a kind (CM-07).

    stub — a classified, a still uploaded and a failed file
    """
    response.headers.update(stubs.HEADERS)
    return [Material.model_validate(m) for m in stubs.materials()]


@router.post(
    "/exam-preps/{id}/materials/confirm",
    status_code=202,
    responses=error_docs("Invalid path or body, or unknown_material", "not_classified"),
)
async def confirm_materials(
    prep_id: PrepId, body: ConfirmMaterialsRequest, response: Response
) -> MaterialsQueued:
    """The user's kind for each file sent; ingestion starts (CM-06, §2.3.2 step 3).

    stub — queues every file sent; nothing is checked against the fixture
    """
    response.headers.update(stubs.HEADERS)
    return MaterialsQueued(queued=len(body.materials))


@router.post(
    "/materials/{id}/retry",
    status_code=202,
    responses=error_docs("Invalid path", "not_failed"),
)
async def retry_material(material_id: MaterialId, response: Response) -> Material:
    """ "Try again" on a failed file of S11: read it again from the step that failed (UC-02 E5).

    stub — the fixture's failed file failed while being classified, so it is back at uploaded
    """
    response.headers.update(stubs.HEADERS)
    row = next(m for m in stubs.materials() if m["status"] == "failed")
    return Material.model_validate({**row, "id": material_id, "status": "uploaded", "error": None})


@router.delete(
    "/materials/{id}",
    status_code=204,
    responses=error_docs("Invalid path", "material_busy"),
)
async def delete_material(material_id: MaterialId, response: Response) -> None:
    """Remove a file: "go on without this file" of S11 (UC-02 E5) and CM-10.

    stub — nothing is deleted, so the file stays in GET /exam-preps/{id}/materials
    """
    response.headers.update(stubs.HEADERS)
