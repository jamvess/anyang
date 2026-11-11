"""Exam prep and material endpoints (specs/system/api.md "สร้างการเตรียมสอบและใส่ไฟล์").

POST and GET /exam-preps use the database (api.md v1.14 · specs/features/exam-prep/
create-exam-prep.md); without a token they keep the stub. Material endpoints are still stubs:
they serve fixture data from app/stubs/ and send `X-Stub: true`, so May can wire S09-S10.
Shapes and request rules are checked by tests/unit/test_exam_prep_api_contract.py.
"""

from datetime import date, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Path, Response
from fastapi.responses import JSONResponse

from app import stubs
from app.auth import AuthContext, get_auth
from app.clock import get_now
from app.db.exam_preps import (
    DbUnavailableError,
    ExamPrepRecord,
    ExamPrepRepository,
    get_exam_prep_repository,
)
from app.domain.exam_prep import bangkok_today, days_left, prep_stage
from app.models.error import ErrorResponse, error_docs, error_response
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
from app.models.room import BYTES_PER_MB, bare_content_type
from app.settings import get_settings

router = APIRouter(tags=["exam_prep"])

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
MaterialId = Annotated[UUID, Path(alias="id")]

# --- exam preps ------------------------------------------------------------------


_DB_DOWN_MESSAGE = "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง"
_DB_DOWN_DOC = {"model": ErrorResponse, "description": "db_unavailable, or auth_unavailable"}

Repository = Annotated[ExamPrepRepository | None, Depends(get_exam_prep_repository)]
Now = Annotated[datetime, Depends(get_now)]


def _exam_prep(record: ExamPrepRecord, today: date) -> ExamPrep:
    """readiness and topics_not_passed stay null until PM-03, PM-04 are computed (api.md v1.14)."""
    return ExamPrep(
        id=record.id,
        title=record.title,
        exam_date=record.exam_date,
        days_left=days_left(record.exam_date, today=today),
        daily_minutes=record.daily_minutes,
        stage=prep_stage(
            has_active_scope=record.active_scope_version_id is not None,
            topic_importances=record.topic_importances,
            materials=record.materials,
        ),
        readiness=None,
        topics_not_passed=None,
    )


def _db_unavailable() -> JSONResponse:
    return error_response(503, "db_unavailable", _DB_DOWN_MESSAGE)


# Sync endpoints: the Supabase client blocks, so FastAPI runs them in its thread pool.
# With a token they use the database. Without one (only possible with AUTH_REQUIRED=false,
# local dev) they serve the stub with X-Stub (create-exam-prep.md §2.1).


@router.post(
    "/exam-preps",
    status_code=201,
    response_model=ExamPrep,  # errors return a JSONResponse, so the return type is Any
    responses={
        422: {"model": ErrorResponse, "description": "Invalid body or exam_date_past"},
        503: _DB_DOWN_DOC,
    },
)
def create_exam_prep(
    body: CreateExamPrepRequest,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    repo: Repository,
    now: Now,
) -> Any:
    """New exam prep from S07-S08 (CM-01). Today in Bangkok is a valid exam date; earlier is
    not. Saved for the user of the token; tenant and user never come from the body."""
    today = bangkok_today(now)
    if body.exam_date < today:
        error = error_response(422, "exam_date_past", "exam_date is before today")
        if auth is None:
            error.headers.update(stubs.HEADERS)
        return error
    if auth is None or repo is None:
        response.headers.update(stubs.HEADERS)
        return ExamPrep(
            id=uuid4(),
            title=body.title,
            exam_date=body.exam_date,
            days_left=days_left(body.exam_date, today=today),
            daily_minutes=body.daily_minutes,
            stage="materials",
            readiness=None,
            topics_not_passed=None,
        )
    try:
        record = repo.create(
            tenant_id=auth.tenant_id,
            user_id=auth.user_id,
            title=body.title,
            exam_date=body.exam_date,
            daily_minutes=body.daily_minutes,
        )
    except DbUnavailableError:
        return _db_unavailable()
    return _exam_prep(record, today)


@router.get(
    "/exam-preps",
    response_model=list[ExamPrep],
    responses={503: _DB_DOWN_DOC},
)
def list_exam_preps(
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    repo: Repository,
    now: Now,
) -> Any:
    """The user's exam preps, soonest exam first then oldest created, archived ones left out
    (CM-01, CM-02, PM-04)."""
    today = bangkok_today(now)
    if auth is None or repo is None:
        response.headers.update(stubs.HEADERS)
        rows = sorted(stubs.exam_preps(), key=lambda row: row["days_left"])
        return [
            ExamPrep.model_validate({**row, "exam_date": today + timedelta(days=row["days_left"])})
            for row in rows
        ]
    try:
        records = repo.list_active()
    except DbUnavailableError:
        return _db_unavailable()
    records.sort(key=lambda r: (r.exam_date, r.created_at))
    return [_exam_prep(record, today) for record in records]


# --- materials --------------------------------------------------------------------


@router.post(
    "/exam-preps/{id}/materials",
    response_model=MaterialUploadTicket,  # errors return a JSONResponse, so the return type is Any
    responses=error_docs("Invalid path or body, unsupported_type or file_too_large"),
)
async def create_material(
    prep_id: PrepId,
    body: UploadMaterialRequest,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> Any:
    """Signed upload URL for one file (CM-03). Type and size are checked before the upload.

    stub — the URL is not a real Storage URL and no materials row is made
    """
    content_type = bare_content_type(body.content_type)
    if content_type not in MATERIAL_CONTENT_TYPES:
        return stubs.error(422, "unsupported_type", f"{body.content_type} is not accepted")
    # An image reaches vision_extract whole, like a photo in the room (api.md v1.13).
    guards = get_settings().ai.guards
    max_mb = guards.max_image_mb if content_type.startswith("image/") else guards.max_material_mb
    if body.size_bytes > max_mb * BYTES_PER_MB:
        return stubs.error(422, "file_too_large", f"file is over {max_mb} MB")
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


@router.delete("/exam-preps/{id}", status_code=204, responses=error_docs())
async def delete_exam_prep(prep_id: PrepId, response: Response) -> None:
    """Delete an exam prep and all its files (CM-10).

    stub — nothing is deleted, so the prep stays in GET /exam-preps
    """
    response.headers.update(stubs.HEADERS)
