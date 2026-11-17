"""Exam prep and material endpoints (specs/system/api.md "สร้างการเตรียมสอบและใส่ไฟล์").

POST and GET /exam-preps use the database (api.md v1.14 · specs/features/exam-prep/
create-exam-prep.md), and so do the upload, uploaded, list and confirm endpoints of materials
(api.md v1.21 · specs/features/exam-prep/materials-db.md). Without a token they keep the stub
(fixture data from app/stubs/ and `X-Stub: true`); retry and DELETE are still stubs.
Shapes and request rules are checked by tests/unit/test_exam_prep_api_contract.py.
"""

from datetime import date, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Path, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app import stubs
from app.ai.call_context import ai_call_context
from app.auth import AuthContext, get_auth
from app.clock import get_now
from app.db.errors import DB_DOWN_MESSAGE
from app.db.exam_preps import (
    DbUnavailableError,
    ExamPrepRecord,
    ExamPrepRepository,
    get_exam_prep_repository,
)
from app.db.materials import MaterialRecord, MaterialRepository, get_material_repository
from app.domain.exam_prep import bangkok_today, days_left, prep_stage
from app.domain.ingestion import clean_file_name
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
from app.services.ingestion import IngestionRunner, get_ingestion_runner
from app.services.material_storage import (
    MaterialStorage,
    StorageUnavailableError,
    get_material_storage,
)
from app.settings import get_settings

router = APIRouter(tags=["exam_prep"])

# api.md writes every path parameter as {id}.
PrepId = Annotated[UUID, Path(alias="id")]
MaterialId = Annotated[UUID, Path(alias="id")]

# --- exam preps ------------------------------------------------------------------


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
    return error_response(503, "db_unavailable", DB_DOWN_MESSAGE)


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


# With a token the four endpoints below use the materials table and Storage with the user's JWT
# (materials-db.md · api.md v1.21); without one they keep the stub. retry and DELETE are stubs.

MaterialRepo = Annotated[MaterialRepository | None, Depends(get_material_repository)]
Storage = Annotated[MaterialStorage | None, Depends(get_material_storage)]
Runner = Annotated[IngestionRunner, Depends(get_ingestion_runner)]
_UNAVAILABLE = (DbUnavailableError, StorageUnavailableError)


def _max_bytes(content_type: str) -> tuple[int, int]:
    """(limit in bytes, limit in MB) for this type. An image reaches vision_extract whole, like a
    photo in the room (api.md v1.13)."""
    guards = get_settings().ai.guards
    max_mb = guards.max_image_mb if content_type.startswith("image/") else guards.max_material_mb
    return max_mb * BYTES_PER_MB, max_mb


def _material(record: MaterialRecord) -> Material:
    return Material.model_validate(
        {
            "id": record.id,
            "file_name": record.file_name,
            "kind": record.kind,
            "kind_confidence": record.kind_confidence,
            "kind_confirmed": record.kind_confirmed,
            "user_note": record.user_note,
            "status": record.status,
            "error": record.error,
        }
    )


def _not_found() -> JSONResponse:
    return error_response(404, "not_found", "not found")


@router.post(
    "/exam-preps/{id}/materials",
    response_model=MaterialUploadTicket,  # errors return a JSONResponse, so the return type is Any
    responses={
        **error_docs("Invalid path or body, unsupported_type or file_too_large"),
        503: _DB_DOWN_DOC,
    },
)
def create_material(
    prep_id: PrepId,
    body: UploadMaterialRequest,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    repo: MaterialRepo,
    storage: Storage,
) -> Any:
    """Signed upload URL for one file (CM-03). Type and size are checked before the upload and
    before the database; the real size is checked again at /uploaded."""
    stub = auth is None or repo is None or storage is None
    fail = stubs.error if stub else error_response
    content_type = bare_content_type(body.content_type)
    if content_type not in MATERIAL_CONTENT_TYPES:
        return fail(422, "unsupported_type", f"{body.content_type} is not accepted")
    max_bytes, max_mb = _max_bytes(content_type)
    if body.size_bytes > max_bytes:
        return fail(422, "file_too_large", f"file is over {max_mb} MB")
    if auth is None or repo is None or storage is None:
        response.headers.update(stubs.HEADERS)
        material_id = uuid4()
        path = f"{stubs.tenant_of(auth)}/{prep_id}/{material_id}"
        return MaterialUploadTicket(
            material_id=material_id, upload_url=f"{stubs.STORAGE_URL}/{path}", path=path
        )
    try:
        if repo.prep_status(prep_id) != "active":
            return _not_found()
        material_id = uuid4()
        # uuids only: the user's file name never reaches the path (spec §2.2 items 2-3).
        path = f"{auth.tenant_id}/{prep_id}/{material_id}"
        # The URL first, so a Storage outage leaves no row behind (spec §2.3 item 5).
        upload_url = storage.signed_upload_url(path)
        repo.create(
            id=material_id,
            tenant_id=auth.tenant_id,
            exam_prep_id=prep_id,
            storage_path=path,
            file_name=clean_file_name(
                body.file_name, get_settings().ai.guards.max_attachment_name_chars
            ),
            content_type=content_type,
        )
    except _UNAVAILABLE:
        return _db_unavailable()
    return MaterialUploadTicket(material_id=material_id, upload_url=upload_url, path=path)


def _check_upload(
    material_id: UUID, user_note: str | None, repo: MaterialRepository, storage: MaterialStorage
) -> MaterialRecord | JSONResponse:
    """Spec §2.4 items 2-5, in the thread pool: the Supabase clients block."""
    row = repo.get(material_id)
    if row is None:
        return _not_found()
    if row.uploaded_at is not None:
        return error_response(409, "already_uploaded", "this file was already announced")
    stored = storage.object_info(row.storage_path)
    if stored is None:
        return error_response(409, "not_uploaded", "the file has not reached storage yet")
    stored_type = bare_content_type(stored.content_type)
    if row.content_type is not None and stored_type != row.content_type:
        storage.remove(row.storage_path)
        return error_response(422, "unsupported_type", "the file is not the type announced")
    max_bytes, max_mb = _max_bytes(row.content_type or stored_type)
    if stored.size_bytes > max_bytes:
        storage.remove(row.storage_path)
        return error_response(422, "file_too_large", f"file is over {max_mb} MB")
    updated = repo.mark_uploaded(material_id, user_note=user_note)
    if updated is None:  # another request set uploaded_at first
        return error_response(409, "already_uploaded", "this file was already announced")
    return updated


@router.post(
    "/materials/{id}/uploaded",
    status_code=202,
    response_model=Material,
    responses={
        **error_docs(
            "Invalid path or body, unsupported_type or file_too_large",
            "already_uploaded, not_uploaded",
        ),
        503: _DB_DOWN_DOC,
    },
)
async def material_uploaded(
    material_id: MaterialId,
    body: MaterialUploadedRequest,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    repo: MaterialRepo,
    storage: Storage,
    runner: Runner,
) -> Any:
    """The browser finished the upload: the real object is checked, then classification starts
    in the background (CM-04, CM-06, CM-07 · §2.3.2 step 2)."""
    if auth is None or repo is None or storage is None:
        response.headers.update(stubs.HEADERS)
        row = next(m for m in stubs.materials() if m["status"] == "uploaded")
        return Material.model_validate({**row, "id": material_id, "user_note": body.user_note})
    try:
        result = await run_in_threadpool(_check_upload, material_id, body.user_note, repo, storage)
    except _UNAVAILABLE:
        return _db_unavailable()
    if isinstance(result, JSONResponse):
        return result
    # The task copies this context when it is made, so ai_calls of A1 carry tenant and user
    # (AI-04). Not awaited: a cancelled request cannot cancel it.
    with ai_call_context(auth.tenant_id, auth.user_id):
        runner.classify(material_id)
    return _material(result)


@router.get(
    "/exam-preps/{id}/materials",
    response_model=list[Material],
    responses={**error_docs(), 503: _DB_DOWN_DOC},
)
def list_materials(
    prep_id: PrepId,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    repo: MaterialRepo,
) -> Any:
    """Files of this exam prep, oldest first; S10 polls until every file has a kind (CM-07).
    A file whose upload was never announced is left out."""
    if auth is None or repo is None:
        response.headers.update(stubs.HEADERS)
        return [Material.model_validate(m) for m in stubs.materials()]
    try:
        if repo.prep_status(prep_id) is None:  # archived preps stay readable
            return _not_found()
        rows = repo.list_for_prep(prep_id)
    except _UNAVAILABLE:
        return _db_unavailable()
    shown = [r for r in rows if r.uploaded_at is not None]
    shown.sort(key=lambda r: (r.created_at, r.id))
    return [_material(r) for r in shown]


def _confirm(
    prep_id: UUID, body: ConfirmMaterialsRequest, repo: MaterialRepository
) -> JSONResponse | None:
    """Spec §2.6 items 2-5, in the thread pool. None when every file was confirmed."""
    if repo.prep_status(prep_id) != "active":
        return _not_found()
    announced = {r.id: r for r in repo.list_for_prep(prep_id) if r.uploaded_at is not None}
    # Every file is checked before any write; an unknown file is named before an unclassified one.
    if any(item.id not in announced for item in body.materials):
        return error_response(422, "unknown_material", "a file is not part of this exam prep")
    if any(announced[item.id].status != "classified" for item in body.materials):
        return error_response(409, "not_classified", "a file is not ready to confirm")
    confirmed = [repo.confirm(item.id, kind=item.kind) for item in body.materials]
    if not all(confirmed):  # a status changed between the check and the update (§10 item 6)
        return error_response(409, "not_classified", "a file is not ready to confirm")
    return None


@router.post(
    "/exam-preps/{id}/materials/confirm",
    status_code=202,
    response_model=MaterialsQueued,
    responses={
        **error_docs("Invalid path or body, or unknown_material", "not_classified"),
        503: _DB_DOWN_DOC,
    },
)
async def confirm_materials(
    prep_id: PrepId,
    body: ConfirmMaterialsRequest,
    response: Response,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    repo: MaterialRepo,
    runner: Runner,
) -> Any:
    """The user's kind for each file sent; ingestion starts (CM-06, §2.3.2 step 3)."""
    if auth is None or repo is None:
        response.headers.update(stubs.HEADERS)
        return MaterialsQueued(queued=len(body.materials))
    try:
        refused = await run_in_threadpool(_confirm, prep_id, body, repo)
    except _UNAVAILABLE:
        return _db_unavailable()
    if refused is not None:
        return refused
    # Not awaited; the runner reads the confirmed files itself. Tenant and user for ai_calls.
    with ai_call_context(auth.tenant_id, auth.user_id):
        runner.start(prep_id)
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
