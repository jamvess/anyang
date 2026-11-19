"""`GET /exam-preps/{id}/ingestion` on the database (specs/features/scope/ingestion.md §2.6 ·
AC-23 to AC-26 · api.md `Ingestion`). No network: the in-memory store stands in for the rows the
user's JWT can see (RLS), and `get_auth` gives a fixed user for "a valid token".

Interfaces these tests expect (to be built by /implement-feature), besides those listed in
test_ingestion_pipeline.py:
- `app.db.ingestion.get_ingestion_reader` (FastAPI dependency) · `InMemoryIngestionStore` gives
  `reader_for(tenant_id)` (sees only that tenant's rows) and `down` (every read raises
  `DbUnavailableError`) · seeding helpers `add_job(prep_id, stage, status, *, material_id=None,
  error=None)`, `add_pages(material_id, count)`, `add_questions(material_id, count)`,
  `set_error(material_id, text)`
"""

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import stubs
from app.auth import AuthContext, get_auth, get_auth_required
from app.db.ingestion import InMemoryIngestionStore, get_ingestion_reader
from app.main import app

USER = AuthContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), token="test-token")
OTHER_TENANT = uuid.uuid4()
DB_DOWN = {"error": {"code": "db_unavailable", "message": "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง"}}
LABEL_NOTES = "อ่านสิ่งที่คุณเขียนกำกับไว้"
LABEL_TOPICS = "หาหัวข้อและลำดับการเรียน"


@pytest.fixture(autouse=True)
def clean_overrides() -> Iterator[None]:
    yield
    for dependency in (get_auth, get_auth_required, get_ingestion_reader):
        app.dependency_overrides.pop(dependency, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def store() -> InMemoryIngestionStore:
    store = InMemoryIngestionStore()
    app.dependency_overrides[get_auth] = lambda: USER
    app.dependency_overrides[get_ingestion_reader] = lambda: store.reader_for(USER.tenant_id)
    return store


def get(client: TestClient, prep: uuid.UUID):
    return client.get(f"/exam-preps/{prep}/ingestion")


def sheet_done(store, prep, name, pages):
    m = store.add_material(prep, file_name=name, kind="sheet", storage_path=name, status="ready")
    for stage in ("extract", "chunk", "embed"):
        store.add_job(prep, stage, "done", material_id=m)
    store.add_pages(m, pages)
    return m


def test_CM07_files_show_their_status_detail_and_error(client, store):
    # AC-23
    prep = store.add_prep(USER.tenant_id)
    done = sheet_done(store, prep, "sheet-01.pdf", 14)
    running = store.add_material(
        prep, file_name="midterm.pdf", kind="past_exam", storage_path="m", status="ingesting"
    )
    store.add_job(prep, "extract", "done", material_id=running)
    store.add_job(prep, "split_exam", "running", material_id=running)
    failed = store.add_material(
        prep, file_name="sheet-02.pdf", kind="sheet", storage_path="s2", status="failed"
    )
    store.set_error(failed, "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้")
    store.add_job(prep, "extract", "failed", material_id=failed, error="Traceback: provider down")
    store.add_material(
        prep,
        file_name="draft.pdf",
        kind="sheet",
        storage_path="d",
        status="classified",
        kind_confirmed=False,
    )

    response = get(client, prep)

    assert response.status_code == 200
    assert "X-Stub" not in response.headers
    body = response.json()
    assert body["files"] == [
        {
            "material_id": str(done),
            "file_name": "sheet-01.pdf",
            "status": "done",
            "detail": "14 หน้า",
            "error": None,
        },
        {
            "material_id": str(running),
            "file_name": "midterm.pdf",
            "status": "running",
            "detail": "กำลังแยกรายข้อ",
            "error": None,
        },
        {
            "material_id": str(failed),
            "file_name": "sheet-02.pdf",
            "status": "failed",
            "detail": None,
            "error": "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้",
        },
    ]
    assert body["scope_ready"] is False
    assert "Traceback" not in response.text


def test_CM07_scope_ready_when_every_file_and_step_is_done(client, store):
    # AC-24
    prep = store.add_prep(USER.tenant_id)
    sheet_done(store, prep, "sheet-01.pdf", 3)
    exam = store.add_material(
        prep, file_name="midterm.pdf", kind="past_exam", storage_path="m", status="ready"
    )
    store.add_job(prep, "extract", "done", material_id=exam)
    store.add_job(prep, "split_exam", "done", material_id=exam)
    store.add_pages(exam, 2)
    store.add_questions(exam, 12)
    store.add_job(prep, "topics", "done")
    store.add_job(prep, "stars", "done")

    body = get(client, prep).json()

    assert body["scope_ready"] is True
    assert body["steps"] == [
        {"label": LABEL_NOTES, "status": "done"},
        {"label": LABEL_TOPICS, "status": "done"},
        {"label": "เทียบกับข้อสอบเก่า 1 ชุด", "status": "done"},
    ]
    assert body["files"][1]["detail"] == "2 หน้า · 12 ข้อ"


def test_CM07_no_past_exam_has_no_exam_step(client, store):
    # AC-24 · AC-14
    prep = store.add_prep(USER.tenant_id)
    sheet_done(store, prep, "sheet-01.pdf", 3)
    store.add_job(prep, "topics", "running")

    body = get(client, prep).json()

    assert body["steps"] == [
        {"label": LABEL_NOTES, "status": "done"},
        {"label": LABEL_TOPICS, "status": "running"},
    ]
    assert body["scope_ready"] is False


def test_CM07_no_confirmed_file_is_an_empty_list(client, store):
    # AC-25
    prep = store.add_prep(USER.tenant_id)

    response = get(client, prep)

    assert response.status_code == 200
    assert response.json()["files"] == []
    assert response.json()["scope_ready"] is False


def test_SA06_another_tenants_prep_is_not_found(client, store):
    # AC-tenant (API part)
    prep = store.add_prep(OTHER_TENANT)
    sheet_done(store, prep, "sheet-01.pdf", 3)

    response = get(client, prep)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_CM07_database_down_is_503(client, store):
    # AC-26
    prep = store.add_prep(USER.tenant_id)
    store.down = True

    response = get(client, prep)

    assert response.status_code == 503
    assert response.json() == DB_DOWN


def test_CM07_no_token_keeps_the_stub(client):
    # AC-26
    app.dependency_overrides[get_auth] = lambda: None
    app.dependency_overrides[get_auth_required] = lambda: False

    response = client.get(f"/exam-preps/{uuid.uuid4()}/ingestion")

    assert response.status_code == 200
    assert response.headers.get("X-Stub") == stubs.HEADERS["X-Stub"]
