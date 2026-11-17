"""The four material endpoints on the database and Storage, with fakes
(specs/features/exam-prep/materials-db.md · api.md v1.21).

No network: the repository (`get_material_repository`), the Storage adapter
(`get_material_storage`) and the ingestion runner (`get_ingestion_runner`) are replaced by fakes,
and `get_auth` by a fixed user when a test needs "a valid token". Limits are read from the loaded
config (`guards.*`), never written here.

Interfaces these tests expect (to be built by /implement-feature):
- `app.db.materials`: `MaterialRecord` (a frozen dataclass with the fields of `record()`
  below), `SupabaseMaterialRepository`,
  `get_material_repository` (dependency · None without a user) with
  `prep_status(prep_id) -> str | None` (None when RLS hides it or it does not exist),
  `create(*, id, tenant_id, exam_prep_id, storage_path, file_name, content_type) -> MaterialRecord`,
  `get(material_id) -> MaterialRecord | None`,
  `mark_uploaded(material_id, *, user_note) -> MaterialRecord | None` (update only while
  `uploaded_at is null`; None when no row changed),
  `list_for_prep(prep_id) -> list[MaterialRecord]` (every row of the prep, any order),
  `confirm(material_id, *, kind) -> bool` (update only while `status = 'classified'`).
  Errors: `app.db.errors.DbUnavailableError`.
- `app.services.material_storage`: `StoredObject(size_bytes, content_type)`,
  `StorageUnavailableError`, `SupabaseMaterialStorage`, `get_material_storage` (dependency · None
  without a user) with `signed_upload_url(path) -> str`, `object_info(path) -> StoredObject | None`,
  `remove(path) -> None`.
- `app.services.ingestion.get_ingestion_runner` used as a dependency of the router, and a new
  `IngestionRunner.classify(material_id)` that starts `classify_material` without waiting.
"""

import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from supabase import ClientOptions, create_client

from app.auth import AuthContext, get_auth, get_auth_required
from app.db.errors import DB_DOWN_MESSAGE, DbUnavailableError
from app.db.materials import MaterialRecord, SupabaseMaterialRepository, get_material_repository
from app.domain.ingestion import clean_file_name
from app.main import app
from app.models.room import BYTES_PER_MB
from app.services.ingestion import get_ingestion_runner
from app.services.material_storage import (
    StorageUnavailableError,
    StoredObject,
    SupabaseMaterialStorage,
    get_material_storage,
)
from app.settings import get_settings

GUARDS = get_settings().ai.guards
MAX_MATERIAL = GUARDS.max_material_mb * BYTES_PER_MB
MAX_IMAGE = GUARDS.max_image_mb * BYTES_PER_MB
MAX_NAME = GUARDS.max_attachment_name_chars
MAX_NOTE = GUARDS.max_message_chars

USER = AuthContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), token="test-token")
PREP = uuid.uuid4()
OTHER_PREP = uuid.uuid4()  # the same user's other prep
FOREIGN_PREP = uuid.uuid4()  # another tenant's: RLS hides it, so the fake does not have it
T0 = datetime(2026, 11, 17, 3, 0, tzinfo=UTC)
UPLOADED_AT = T0 + timedelta(minutes=1)
PDF = "application/pdf"
UUID4 = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"


# --- fakes ---------------------------------------------------------------------------


@dataclass
class FakeRepo:
    """Stands in for the Supabase repository: rows the user can see through RLS."""

    preps: dict[uuid.UUID, str] = field(
        default_factory=lambda: {PREP: "active", OTHER_PREP: "active"}
    )
    rows: dict[uuid.UUID, MaterialRecord] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)
    down: bool = False
    lose_upload_race: bool = False  # another request set uploaded_at first
    lose_confirm_race: set[uuid.UUID] = field(default_factory=set)  # status changed first

    def _call(self, name: str) -> None:
        self.calls.append(name)
        if self.down:
            raise DbUnavailableError("connection refused")

    def prep_status(self, prep_id: uuid.UUID) -> str | None:
        self._call("prep_status")
        return self.preps.get(prep_id)

    def create(
        self,
        *,
        id: uuid.UUID,
        tenant_id: uuid.UUID,
        exam_prep_id: uuid.UUID,
        storage_path: str,
        file_name: str,
        content_type: str,
    ) -> MaterialRecord:
        self._call("create")
        row = record(
            id=id,
            tenant_id=tenant_id,
            exam_prep_id=exam_prep_id,
            storage_path=storage_path,
            file_name=file_name,
            content_type=content_type,
            uploaded_at=None,
        )
        self.rows[id] = row
        return row

    def get(self, material_id: uuid.UUID) -> MaterialRecord | None:
        self._call("get")
        return self.rows.get(material_id)

    def mark_uploaded(
        self, material_id: uuid.UUID, *, user_note: str | None
    ) -> MaterialRecord | None:
        self._call("mark_uploaded")
        row = self.rows.get(material_id)
        if row is None or row.uploaded_at is not None or self.lose_upload_race:
            return None
        row = replace(row, uploaded_at=UPLOADED_AT, user_note=user_note)
        self.rows[material_id] = row
        return row

    def list_for_prep(self, prep_id: uuid.UUID) -> list[MaterialRecord]:
        self._call("list_for_prep")
        return [r for r in reversed(list(self.rows.values())) if r.exam_prep_id == prep_id]

    def confirm(self, material_id: uuid.UUID, *, kind: str) -> bool:
        self._call("confirm")
        row = self.rows.get(material_id)
        if row is None or row.status != "classified" or material_id in self.lose_confirm_race:
            return False
        self.rows[material_id] = replace(row, kind=kind, kind_confirmed=True, status="confirmed")
        return True


@dataclass
class FakeStorage:
    """Stands in for Supabase Storage: objects by path."""

    objects: dict[str, StoredObject] = field(default_factory=dict)
    signed: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)
    down: bool = False

    def signed_upload_url(self, path: str) -> str:
        if self.down:
            raise StorageUnavailableError("storage refused")
        self.signed.append(path)
        return f"https://fake.supabase.co/storage/v1/object/upload/sign/materials/{path}?token=t"

    def object_info(self, path: str) -> StoredObject | None:
        if self.down:
            raise StorageUnavailableError("storage refused")
        self.reads.append(path)
        return self.objects.get(path)

    def remove(self, path: str) -> None:
        if self.down:
            raise StorageUnavailableError("storage refused")
        self.removed.append(path)
        self.objects.pop(path, None)


@dataclass
class FakeRunner:
    classified: list[uuid.UUID] = field(default_factory=list)
    started: list[uuid.UUID] = field(default_factory=list)

    def classify(self, material_id: uuid.UUID) -> None:
        self.classified.append(material_id)

    def start(self, prep_id: uuid.UUID) -> None:
        self.started.append(prep_id)


def record(**change: Any) -> MaterialRecord:
    material_id = change.get("id") or uuid.uuid4()
    prep_id = change.get("exam_prep_id", PREP)
    data: dict[str, Any] = {
        "id": material_id,
        "tenant_id": USER.tenant_id,
        "exam_prep_id": prep_id,
        "storage_path": f"{USER.tenant_id}/{prep_id}/{material_id}",
        "file_name": "ชีท บทที่ 3.pdf",
        "content_type": PDF,
        "kind": None,
        "kind_confidence": None,
        "kind_confirmed": False,
        "user_note": None,
        "status": "uploaded",
        "error": None,
        "uploaded_at": UPLOADED_AT,
        "created_at": T0,
        **change,
    }
    return MaterialRecord(**data)


def add(repo: FakeRepo, **change: Any) -> MaterialRecord:
    row = record(**change)
    repo.rows[row.id] = row
    return row


def classified(repo: FakeRepo, **change: Any) -> MaterialRecord:
    return add(repo, status="classified", kind="sheet", kind_confidence=0.9, **change)


def waiting(repo: FakeRepo, storage: FakeStorage, **change: Any) -> MaterialRecord:
    """A row whose URL was asked for and whose object is in Storage, not yet announced."""
    row = add(repo, uploaded_at=None, **change)
    storage.objects[row.storage_path] = StoredObject(
        size_bytes=2_400_000, content_type=row.content_type
    )
    return row


def assert_error(response: Any, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def ticket(**change: Any) -> dict[str, Any]:
    return {"file_name": "ชีท บทที่ 3.pdf", "content_type": PDF, "size_bytes": 2_400_000, **change}


# --- fixtures --------------------------------------------------------------------------


@pytest.fixture
def repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def runner() -> FakeRunner:
    return FakeRunner()


@pytest.fixture
def client(repo: FakeRepo, storage: FakeStorage, runner: FakeRunner) -> Iterator[TestClient]:
    """No token, AUTH_REQUIRED=false (conftest) unless a test overrides more. The fakes are
    returned only for a user, like the real dependencies."""

    app.dependency_overrides[get_material_repository] = lambda: repo
    app.dependency_overrides[get_material_storage] = lambda: storage
    app.dependency_overrides[get_ingestion_runner] = lambda: runner
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def signed_in(client: TestClient) -> TestClient:
    app.dependency_overrides[get_auth] = lambda: USER
    return client


# --- ขอที่อัปโหลด (§2.3) ----------------------------------------------------------------


def test_CM03_upload_ticket_creates_row_with_uuid_path(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage
) -> None:
    """AC-1."""
    response = signed_in.post(f"/exam-preps/{PREP}/materials", json=ticket())

    assert response.status_code == 200, response.text
    assert "x-stub" not in response.headers
    body = response.json()
    material_id = uuid.UUID(body["material_id"])
    assert body["path"] == f"{USER.tenant_id}/{PREP}/{material_id}"
    assert "." not in body["path"].rsplit("/", 1)[1]
    assert storage.signed == [body["path"]]
    assert body["upload_url"].endswith(f"/materials/{body['path']}?token=t")
    row = repo.rows[material_id]
    assert row.tenant_id == USER.tenant_id
    assert row.exam_prep_id == PREP
    assert row.storage_path == body["path"]
    assert row.status == "uploaded"
    assert row.uploaded_at is None
    assert row.content_type == PDF


@pytest.mark.parametrize(
    "file_name",
    [
        "../../00000000-0000-0000-0000-000000000000/x.pdf",
        "ชีทบทที่ " + "สามสิบเอ็ด" * 60 + ".pdf",
        "a/b\\c\n.pdf",
    ],
    ids=["dot-dot", "thai-over-cap", "slashes-newline"],
)
def test_CM03_file_name_never_reaches_the_path(
    signed_in: TestClient, repo: FakeRepo, file_name: str
) -> None:
    """AC-2."""
    response = signed_in.post(f"/exam-preps/{PREP}/materials", json=ticket(file_name=file_name))

    assert response.status_code == 200, response.text
    body = response.json()
    assert re.fullmatch(f"{USER.tenant_id}/{PREP}/{UUID4}", body["path"])
    row = repo.rows[uuid.UUID(body["material_id"])]
    assert row.file_name == clean_file_name(file_name, MAX_NAME)
    assert row.storage_path == body["path"]


def test_CM03_long_file_name_is_cut_and_keeps_its_extension(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """AC-2: too long is cut, not refused."""
    name = "ก" * (MAX_NAME + 50) + ".pdf"

    response = signed_in.post(f"/exam-preps/{PREP}/materials", json=ticket(file_name=name))

    assert response.status_code == 200, response.text
    stored = repo.rows[uuid.UUID(response.json()["material_id"])].file_name
    assert stored.endswith(".pdf")
    assert len(stored) <= MAX_NAME


def test_CM03_content_type_is_stored_bare_and_lowercase(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """AC-3."""
    response = signed_in.post(
        f"/exam-preps/{PREP}/materials", json=ticket(content_type="Application/PDF; charset=x")
    )

    assert response.status_code == 200, response.text
    assert repo.rows[uuid.UUID(response.json()["material_id"])].content_type == PDF


@pytest.mark.parametrize(
    ("prep_id", "status"),
    [(FOREIGN_PREP, None), (uuid.uuid4(), None), (OTHER_PREP, "archived")],
    ids=["other-tenant", "missing", "archived"],
)
def test_SA06_upload_ticket_for_unknown_or_foreign_prep_is_not_found(
    signed_in: TestClient,
    repo: FakeRepo,
    storage: FakeStorage,
    prep_id: uuid.UUID,
    status: str | None,
) -> None:
    """AC-4."""
    if status is not None:
        repo.preps[prep_id] = status

    response = signed_in.post(f"/exam-preps/{prep_id}/materials", json=ticket())

    assert_error(response, 404, "not_found")
    assert storage.signed == []
    assert repo.rows == {}


@pytest.mark.parametrize(
    ("body", "code"),
    [
        (ticket(content_type="text/plain"), "unsupported_type"),
        (ticket(size_bytes=MAX_MATERIAL + 1), "file_too_large"),
        (ticket(content_type="image/png", size_bytes=MAX_IMAGE + 1), "file_too_large"),
        (ticket(content_type="text/plain", size_bytes=MAX_MATERIAL + 1), "unsupported_type"),
    ],
    ids=["type", "pdf-size", "image-size", "type-before-size"],
)
def test_CM03_type_and_size_are_checked_before_db_with_token(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage, body: dict[str, Any], code: str
) -> None:
    """AC-5."""
    response = signed_in.post(f"/exam-preps/{PREP}/materials", json=body)

    assert_error(response, 422, code)
    assert repo.calls == []
    assert storage.signed == []


def test_CM03_storage_down_leaves_no_row(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage
) -> None:
    """AC-6: the URL is asked for before the insert."""
    storage.down = True

    response = signed_in.post(f"/exam-preps/{PREP}/materials", json=ticket())

    assert response.status_code == 503
    assert response.json() == {"error": {"code": "db_unavailable", "message": DB_DOWN_MESSAGE}}
    assert "storage refused" not in response.text
    assert repo.rows == {}
    assert "create" not in repo.calls


def test_CM03_db_down_on_insert_is_503(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-6."""

    def down(**_: Any) -> MaterialRecord:
        raise DbUnavailableError("connection refused")

    repo.create = down  # type: ignore[method-assign]

    response = signed_in.post(f"/exam-preps/{PREP}/materials", json=ticket())

    assert response.status_code == 503
    assert response.json() == {"error": {"code": "db_unavailable", "message": DB_DOWN_MESSAGE}}


# --- ส่งไฟล์เสร็จ (§2.4) -------------------------------------------------------------------


def test_CM06_uploaded_saves_note_and_starts_classify_once(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage, runner: FakeRunner
) -> None:
    """AC-7."""
    row = waiting(repo, storage)

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={"user_note": "  ข้อสอบปีที่แล้ว  "})

    assert response.status_code == 202, response.text
    assert "x-stub" not in response.headers
    body = response.json()
    assert body["id"] == str(row.id)
    assert body["status"] == "uploaded"
    assert body["kind"] is None
    assert body["user_note"] == "ข้อสอบปีที่แล้ว"
    assert repo.rows[row.id].uploaded_at is not None
    assert repo.rows[row.id].user_note == "ข้อสอบปีที่แล้ว"
    assert runner.classified == [row.id]
    assert storage.removed == []


def test_CM07_uploaded_without_object_is_not_uploaded_and_can_retry(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage, runner: FakeRunner
) -> None:
    """AC-8."""
    row = add(repo, uploaded_at=None)

    first = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    assert_error(first, 409, "not_uploaded")
    assert repo.rows[row.id].uploaded_at is None
    assert runner.classified == []

    storage.objects[row.storage_path] = StoredObject(size_bytes=10, content_type=PDF)
    again = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    assert again.status_code == 202, again.text
    assert runner.classified == [row.id]


@pytest.mark.parametrize(
    ("content_type", "limit"),
    [(PDF, MAX_MATERIAL), ("image/png", MAX_IMAGE)],
    ids=["pdf", "image"],
)
@pytest.mark.parametrize(("delta", "ok"), [(-1, True), (0, True), (1, False)])
def test_CM03_real_size_over_limit_is_rejected_and_removed(
    signed_in: TestClient,
    repo: FakeRepo,
    storage: FakeStorage,
    runner: FakeRunner,
    content_type: str,
    limit: int,
    delta: int,
    ok: bool,
) -> None:
    """AC-9: the client said size_bytes 1 when it asked for the URL."""
    row = add(repo, uploaded_at=None, content_type=content_type)
    storage.objects[row.storage_path] = StoredObject(
        size_bytes=limit + delta, content_type=content_type
    )

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    if ok:
        assert response.status_code == 202, response.text
        assert storage.removed == []
        assert runner.classified == [row.id]
    else:
        assert_error(response, 422, "file_too_large")
        assert storage.removed == [row.storage_path]
        assert runner.classified == []
        assert repo.rows[row.id].uploaded_at is None


@pytest.mark.parametrize("stored_type", ["image/png", "application/PDF; x=y"], ids=["png", "case"])
def test_CM03_object_type_not_matching_row_is_rejected_and_removed(
    signed_in: TestClient,
    repo: FakeRepo,
    storage: FakeStorage,
    runner: FakeRunner,
    stored_type: str,
) -> None:
    """AC-10: a different type is refused; the same type with other case or parameters is not."""
    row = add(repo, uploaded_at=None, content_type=PDF)
    storage.objects[row.storage_path] = StoredObject(size_bytes=10, content_type=stored_type)

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    if stored_type == "image/png":
        assert_error(response, 422, "unsupported_type")
        assert storage.removed == [row.storage_path]
        assert runner.classified == []
        assert repo.rows[row.id].uploaded_at is None
    else:
        assert response.status_code == 202, response.text


def test_CM07_uploaded_twice_is_already_uploaded(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage, runner: FakeRunner
) -> None:
    """AC-11."""
    row = waiting(repo, storage)
    assert signed_in.post(f"/materials/{row.id}/uploaded", json={}).status_code == 202

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    assert_error(response, 409, "already_uploaded")
    assert runner.classified == [row.id]


def test_CM07_concurrent_uploaded_classifies_once(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage, runner: FakeRunner
) -> None:
    """AC-11: the other request set uploaded_at between the read and the update."""
    row = waiting(repo, storage)
    repo.lose_upload_race = True

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    assert_error(response, 409, "already_uploaded")
    assert runner.classified == []


@pytest.mark.parametrize(
    "material_id", [uuid.uuid4(), uuid.uuid4()], ids=["other-tenant", "missing"]
)
def test_SA06_uploaded_for_foreign_material_is_not_found(
    signed_in: TestClient,
    storage: FakeStorage,
    runner: FakeRunner,
    material_id: uuid.UUID,
) -> None:
    """AC-12: RLS hides another tenant's row, so it looks the same as a missing one."""
    response = signed_in.post(f"/materials/{material_id}/uploaded", json={})

    assert_error(response, 404, "not_found")
    assert storage.reads == []
    assert runner.classified == []


@pytest.mark.parametrize(
    ("note", "status", "stored"),
    [
        ("ข้อสอบ\x00ปีที่แล้ว", 422, None),
        ("ข้อสอบ\tปีที่แล้ว", 422, None),
        ("ก" * MAX_NOTE, 202, "ก" * MAX_NOTE),
        ("ก" * (MAX_NOTE + 1), 422, None),
        ("กี่" * MAX_NOTE, 202, "กี่" * MAX_NOTE),  # Thai marks do not count on their own
        ("บทที่ 5\nไม่ออกสอบ", 202, "บทที่ 5\nไม่ออกสอบ"),
        ("", 202, None),
        ("   \n  ", 202, None),
        (None, 202, None),
    ],
    ids=["nul", "tab", "at-cap", "over-cap", "graphemes", "newline", "empty", "blank", "null"],
)
def test_CM04_user_note_rules(
    signed_in: TestClient,
    repo: FakeRepo,
    storage: FakeStorage,
    runner: FakeRunner,
    note: str | None,
    status: int,
    stored: str | None,
) -> None:
    """AC-13."""
    row = waiting(repo, storage)

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={"user_note": note})

    if status == 422:
        assert_error(response, 422, "validation_error")
        assert repo.rows[row.id].uploaded_at is None
        assert runner.classified == []
    else:
        assert response.status_code == 202, response.text
        assert response.json()["user_note"] == stored
        assert repo.rows[row.id].user_note == stored


def test_CM04_user_note_may_be_left_out(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage
) -> None:
    """AC-13: no body field at all."""
    row = waiting(repo, storage)

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    assert response.status_code == 202, response.text
    assert response.json()["user_note"] is None


# --- สถานะรายไฟล์ (§2.5) -------------------------------------------------------------------


def test_CM07_list_shows_only_uploaded_files_oldest_first(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """AC-14."""
    later = classified(repo, created_at=T0 + timedelta(minutes=5), file_name="b.pdf")
    first = add(repo, created_at=T0, file_name="a.pdf")
    add(repo, created_at=T0 + timedelta(minutes=1), uploaded_at=None, file_name="never.pdf")
    failed = add(
        repo,
        created_at=T0 + timedelta(minutes=9),
        status="failed",
        error="เปิดไฟล์นี้ไม่ได้",
        file_name="c.pdf",
    )
    add(repo, exam_prep_id=OTHER_PREP, file_name="other-prep.pdf")

    response = signed_in.get(f"/exam-preps/{PREP}/materials")

    assert response.status_code == 200, response.text
    assert "x-stub" not in response.headers
    body = response.json()
    assert [m["id"] for m in body] == [str(first.id), str(later.id), str(failed.id)]
    assert body[2]["error"] == "เปิดไฟล์นี้ไม่ได้"
    assert body[1]["kind"] == "sheet"


def test_CM07_list_ties_on_created_at_are_ordered_by_id(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """AC-14 / §2.5 item 3."""
    rows = [add(repo, created_at=T0) for _ in range(4)]

    response = signed_in.get(f"/exam-preps/{PREP}/materials")

    assert [m["id"] for m in response.json()] == sorted(str(r.id) for r in rows)


def test_CM07_list_of_prep_without_files_is_empty(signed_in: TestClient) -> None:
    """§2.5 item 3."""
    response = signed_in.get(f"/exam-preps/{PREP}/materials")

    assert response.status_code == 200
    assert response.json() == []


def test_CM07_list_of_archived_prep_is_still_readable(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """§2.5 item 1."""
    repo.preps[OTHER_PREP] = "archived"
    row = add(repo, exam_prep_id=OTHER_PREP)

    response = signed_in.get(f"/exam-preps/{OTHER_PREP}/materials")

    assert response.status_code == 200
    assert [m["id"] for m in response.json()] == [str(row.id)]


@pytest.mark.parametrize("prep_id", [FOREIGN_PREP, uuid.uuid4()], ids=["other-tenant", "missing"])
def test_SA06_list_for_foreign_prep_is_not_found(signed_in: TestClient, prep_id: uuid.UUID) -> None:
    """AC-15."""
    assert_error(signed_in.get(f"/exam-preps/{prep_id}/materials"), 404, "not_found")


# --- ยืนยัน (§2.6) -----------------------------------------------------------------------------


def confirm(
    client: TestClient, *items: tuple[MaterialRecord | uuid.UUID, str], prep: uuid.UUID = PREP
) -> Any:
    materials = [{"id": str(getattr(m, "id", m)), "kind": kind} for m, kind in items]
    return client.post(f"/exam-preps/{prep}/materials/confirm", json={"materials": materials})


def test_CM06_confirm_sets_user_kind_and_starts_ingestion(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-16."""
    a = classified(repo)
    b = classified(repo)

    response = confirm(signed_in, (a, "sheet"), (b, "past_exam"))

    assert response.status_code == 202, response.text
    assert "x-stub" not in response.headers
    assert response.json() == {"queued": 2}
    for row, kind in ((a, "sheet"), (b, "past_exam")):
        saved = repo.rows[row.id]
        assert (saved.kind, saved.kind_confirmed, saved.status) == (kind, True, "confirmed")
    assert runner.started == [PREP]


def test_CM06_confirm_with_unclassified_file_writes_nothing(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-17."""
    a = classified(repo)
    b = add(repo, status="uploaded")

    response = confirm(signed_in, (a, "sheet"), (b, "sheet"))

    assert_error(response, 409, "not_classified")
    assert repo.rows[a.id].status == "classified"
    assert repo.rows[a.id].kind_confirmed is False
    assert "confirm" not in repo.calls
    assert runner.started == []


@pytest.mark.parametrize("status", ["confirmed", "ingesting", "ready", "failed"])
def test_CM06_confirm_of_a_file_past_classified_is_not_classified(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner, status: str
) -> None:
    """§2.6 item 3: already confirmed, or further along, is not classified."""
    row = add(repo, status=status, kind="sheet")

    assert_error(confirm(signed_in, (row, "sheet")), 409, "not_classified")
    assert runner.started == []


@pytest.mark.parametrize("case", ["other-prep", "other-tenant", "not-announced"])
def test_SA06_confirm_with_foreign_or_unannounced_id_is_unknown_material(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner, case: str
) -> None:
    """AC-18; with an unclassified file too, unknown_material comes first (§2.6 item 3)."""
    good = classified(repo)
    pending = add(repo, status="uploaded")
    bad: MaterialRecord | uuid.UUID
    if case == "other-prep":
        bad = classified(repo, exam_prep_id=OTHER_PREP)
    elif case == "other-tenant":
        bad = uuid.uuid4()  # RLS hides it
    else:
        bad = classified(repo, uploaded_at=None)

    response = confirm(signed_in, (good, "sheet"), (pending, "sheet"), (bad, "sheet"))

    assert_error(response, 422, "unknown_material")
    assert "confirm" not in repo.calls
    assert repo.rows[good.id].status == "classified"
    assert runner.started == []


def test_CM05_confirm_leaves_files_not_sent(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-19."""
    a = classified(repo)
    c = classified(repo)

    response = confirm(signed_in, (a, "notes"))

    assert response.status_code == 202, response.text
    assert response.json() == {"queued": 1}
    assert repo.rows[c.id].status == "classified"
    assert repo.rows[c.id].kind_confirmed is False


def test_CM06_confirm_race_is_not_classified_without_ingestion(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-20: a passed the check, then its status changed before the update."""
    a = classified(repo)
    b = classified(repo)
    repo.lose_confirm_race = {b.id}

    response = confirm(signed_in, (a, "sheet"), (b, "sheet"))

    assert_error(response, 409, "not_classified")
    assert runner.started == []


@pytest.mark.parametrize("prep_id", [FOREIGN_PREP, uuid.uuid4()], ids=["other-tenant", "missing"])
def test_SA06_confirm_for_foreign_prep_is_not_found(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner, prep_id: uuid.UUID
) -> None:
    """§2.6 item 2."""
    a = classified(repo)

    assert_error(confirm(signed_in, (a, "sheet"), prep=prep_id), 404, "not_found")
    assert runner.started == []


# --- ไม่มี token และ DB ล่ม (§2.1) ----------------------------------------------------------------


def _endpoints(material_id: uuid.UUID) -> list[tuple[str, str, Any]]:
    return [
        ("POST", f"/exam-preps/{PREP}/materials", ticket()),
        ("POST", f"/materials/{material_id}/uploaded", {"user_note": None}),
        ("GET", f"/exam-preps/{PREP}/materials", None),
        (
            "POST",
            f"/exam-preps/{PREP}/materials/confirm",
            {"materials": [{"id": str(material_id), "kind": "sheet"}]},
        ),
    ]


@pytest.mark.parametrize("index", range(4), ids=["ticket", "uploaded", "list", "confirm"])
@pytest.mark.parametrize("required", [False, True], ids=["auth-optional", "auth-required"])
def test_SA06_materials_without_token_keep_stub_or_401(
    client: TestClient,
    repo: FakeRepo,
    storage: FakeStorage,
    runner: FakeRunner,
    index: int,
    required: bool,
) -> None:
    """AC-21."""
    app.dependency_overrides[get_auth_required] = lambda: required
    method, url, body = _endpoints(uuid.uuid4())[index]

    response = client.request(method, url, json=body)

    if required:
        assert_error(response, 401, "missing_token")
        assert "x-stub" not in response.headers
    else:
        assert response.status_code < 300, response.text
        assert response.headers.get("x-stub") == "true"
    assert repo.calls == []
    assert storage.signed == storage.reads == storage.removed == []
    assert runner.classified == runner.started == []


@pytest.mark.parametrize("index", range(4), ids=["ticket", "uploaded", "list", "confirm"])
def test_SA06_materials_db_down_is_503(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage, index: int
) -> None:
    """AC-22."""
    row = waiting(repo, storage, status="classified")
    repo.down = True
    method, url, body = _endpoints(row.id)[index]

    response = signed_in.request(method, url, json=body)

    assert response.status_code == 503, response.text
    assert response.json() == {"error": {"code": "db_unavailable", "message": DB_DOWN_MESSAGE}}
    assert "connection refused" not in response.text
    assert response.headers.get("x-request-id")


def test_SA06_storage_down_on_uploaded_is_503(
    signed_in: TestClient, repo: FakeRepo, storage: FakeStorage, runner: FakeRunner
) -> None:
    """§2.4 item 8."""
    row = waiting(repo, storage)
    storage.down = True

    response = signed_in.post(f"/materials/{row.id}/uploaded", json={})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "db_unavailable"
    assert repo.rows[row.id].uploaded_at is None
    assert runner.classified == []


def _unreachable_client() -> Any:
    """Nothing listens on port 9."""
    return create_client(
        "http://127.0.0.1:9",
        "sb_publishable_test",
        ClientOptions(auto_refresh_token=False, persist_session=False, postgrest_client_timeout=2),
    )


def test_SA06_supabase_adapters_turn_network_errors_into_unavailable() -> None:
    """AC-6, AC-22: the real adapters, not only the fakes, raise the errors the router maps."""
    repo = SupabaseMaterialRepository(_unreachable_client())
    storage = SupabaseMaterialStorage(_unreachable_client())

    with pytest.raises(DbUnavailableError):
        repo.prep_status(PREP)
    with pytest.raises(DbUnavailableError):
        repo.get(uuid.uuid4())
    with pytest.raises(StorageUnavailableError):
        storage.signed_upload_url(f"{USER.tenant_id}/{PREP}/{uuid.uuid4()}")
    with pytest.raises(StorageUnavailableError):
        storage.object_info(f"{USER.tenant_id}/{PREP}/{uuid.uuid4()}")
