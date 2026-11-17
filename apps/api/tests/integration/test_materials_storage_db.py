"""Material uploads against real Supabase DB and Storage
(specs/features/exam-prep/materials-db.md AC-23 to AC-26 · SA-06).

Runs against the Supabase stack of .env or CI, like test_exam_prep_db.py: users are created with
the admin API (each gets a personal tenant) and deleted afterwards, with their objects. The app
checks real tokens and uses the user's JWT for the DB and Storage. The ingestion runner is
replaced by a recorder, so no AI runs; AC-23 reads the file back with the ingestion reader
itself (`SupabaseMaterialFiles`, service role). Needs migration 0008 on the target project.
"""

import asyncio
import contextlib
import os
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from storage3.exceptions import StorageApiError
from supabase import Client, ClientOptions, create_client

from app.auth import TokenVerifier, get_auth_required, get_verifier
from app.main import app
from app.models.room import BYTES_PER_MB
from app.services.ingestion import MATERIALS_BUCKET, get_ingestion_runner
from app.services.material_files import SupabaseMaterialFiles
from app.settings import EnvSettings, get_settings

_env = EnvSettings()
_URL = _env.supabase_url
_ANON_KEY = _env.supabase_anon_key.get_secret_value()
_SERVICE_KEY = _env.supabase_service_role_key.get_secret_value()

if not (_URL and _ANON_KEY and _SERVICE_KEY):
    if os.environ.get("CI"):
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY not set")
    pytest.skip("Supabase is not configured", allow_module_level=True)

_NO_SESSION = {"auto_refresh_token": False, "persist_session": False}
PDF_BYTES = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
LIMIT = get_settings().ai.guards.max_material_mb * BYTES_PER_MB


@dataclass
class User:
    user_id: str
    tenant_id: str
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def client(self) -> Client:
        """Anon key + this user's JWT, so RLS and the storage policies apply."""
        options = ClientOptions(headers={"Authorization": f"Bearer {self.token}"}, **_NO_SESSION)
        return create_client(_URL, _ANON_KEY, options)


@dataclass
class Recorder:
    classified: list[uuid.UUID] = field(default_factory=list)
    started: list[uuid.UUID] = field(default_factory=list)

    def classify(self, material_id: uuid.UUID) -> None:
        self.classified.append(material_id)

    def start(self, prep_id: uuid.UUID) -> None:
        self.started.append(prep_id)


@pytest.fixture(scope="module")
def admin() -> Client:
    return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))


def anon() -> Client:
    return create_client(_URL, _ANON_KEY, ClientOptions(**_NO_SESSION))


@pytest.fixture(scope="module")
def make_user(admin: Client) -> Iterator[Callable[[], User]]:
    created: list[User] = []

    def make() -> User:
        email = f"materials-{uuid.uuid4().hex}@example.test"
        password = uuid.uuid4().hex
        user_id = admin.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        ).user.id
        tenant_id = (
            admin.table("memberships")
            .select("tenant_id")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data["tenant_id"]
        )
        token = (
            anon()
            .auth.sign_in_with_password({"email": email, "password": password})
            .session.access_token
        )
        user = User(user_id, tenant_id, token)
        created.append(user)
        return user

    try:
        yield make
    finally:
        bucket = admin.storage.from_(MATERIALS_BUCKET)
        for user in created:
            for prep in bucket.list(user.tenant_id):
                folder = f"{user.tenant_id}/{prep['name']}"
                names = [f"{folder}/{o['name']}" for o in bucket.list(folder)]
                if names:
                    bucket.remove(names)
            admin.auth.admin.delete_user(user.user_id)
            admin.table("tenants").delete().eq("id", user.tenant_id).execute()


@pytest.fixture
def runner() -> Recorder:
    return Recorder()


@pytest.fixture
def client(runner: Recorder) -> Iterator[TestClient]:
    verifier = TokenVerifier(_URL, _ANON_KEY)
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_auth_required] = lambda: True
    app.dependency_overrides[get_ingestion_runner] = lambda: runner
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def insert_prep(admin: Client, user: User) -> str:
    row = {
        "tenant_id": user.tenant_id,
        "user_id": user.user_id,
        "title": "materials-db",
        "exam_date": str(date.today() + timedelta(10)),
    }
    return admin.table("exam_preps").insert(row).execute().data[0]["id"]


def upload(
    client: TestClient, user: User, prep_id: str, data: bytes = PDF_BYTES
) -> tuple[dict[str, Any], httpx.Response]:
    """Ask the API for a URL, then PUT the file there with no token, like the browser."""
    ticket = client.post(
        f"/exam-preps/{prep_id}/materials",
        json={"file_name": "ชีท บทที่ 3.pdf", "content_type": "application/pdf", "size_bytes": 1},
        headers=user.headers,
    )
    assert ticket.status_code == 200, ticket.text
    body = ticket.json()
    put = httpx.put(
        body["upload_url"],
        content=data,
        headers={"Content-Type": "application/pdf"},
        timeout=120,
    )
    return body, put


def object_names(admin: Client, folder: str) -> list[str]:
    return [o["name"] for o in admin.storage.from_(MATERIALS_BUCKET).list(folder)]


# --- AC-23 ------------------------------------------------------------------------------------


def test_CM03_signed_upload_reaches_ingestion_reader(
    client: TestClient, admin: Client, make_user: Callable[[], User], runner: Recorder
) -> None:
    a = make_user()
    prep_id = insert_prep(admin, a)

    ticket, put = upload(client, a, prep_id)
    assert put.status_code < 300, put.text
    uploaded = client.post(
        f"/materials/{ticket['material_id']}/uploaded", json={}, headers=a.headers
    )

    assert uploaded.status_code == 202, uploaded.text
    assert runner.classified == [uuid.UUID(ticket["material_id"])]
    row = (
        admin.table("materials")
        .select("storage_path,uploaded_at,content_type,tenant_id")
        .eq("id", ticket["material_id"])
        .single()
        .execute()
        .data
    )
    assert row["storage_path"] == f"{a.tenant_id}/{prep_id}/{ticket['material_id']}"
    assert row["uploaded_at"] is not None
    assert row["content_type"] == "application/pdf"
    assert row["tenant_id"] == a.tenant_id

    def service() -> Client:
        return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))

    files = SupabaseMaterialFiles(service, MATERIALS_BUCKET)
    assert asyncio.run(files.read(row["storage_path"])) == PDF_BYTES


def test_CM07_uploaded_before_the_put_is_not_uploaded(
    client: TestClient, admin: Client, make_user: Callable[[], User], runner: Recorder
) -> None:
    """AC-8 on real Storage: no object yet."""
    a = make_user()
    prep_id = insert_prep(admin, a)
    ticket = client.post(
        f"/exam-preps/{prep_id}/materials",
        json={"file_name": "a.pdf", "content_type": "application/pdf", "size_bytes": 1},
        headers=a.headers,
    ).json()

    response = client.post(
        f"/materials/{ticket['material_id']}/uploaded", json={}, headers=a.headers
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "not_uploaded"
    assert runner.classified == []


# --- AC-24 ------------------------------------------------------------------------------------


@pytest.fixture
def a_object(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> tuple[User, str, str]:
    """User A with one uploaded object: (A, prep id, object path)."""
    a = make_user()
    prep_id = insert_prep(admin, a)
    ticket, put = upload(client, a, prep_id)
    assert put.status_code < 300, put.text
    return a, prep_id, ticket["path"]


@pytest.mark.parametrize("who", ["other-user", "anon"])
def test_SA06_storage_prefix_isolation(
    admin: Client,
    make_user: Callable[[], User],
    a_object: tuple[User, str, str],
    who: str,
) -> None:
    a, prep_id, path = a_object
    outsider = make_user().client() if who == "other-user" else anon()
    bucket = outsider.storage.from_(MATERIALS_BUCKET)
    folder = f"{a.tenant_id}/{prep_id}"

    with pytest.raises(StorageApiError):
        bucket.download(path)
    assert bucket.list(folder) == []
    with contextlib.suppress(StorageApiError):  # refused outright is fine too
        bucket.remove([path])
    assert path.rsplit("/", 1)[1] in object_names(admin, folder), "the object was deleted"
    with pytest.raises(StorageApiError):
        bucket.create_signed_upload_url(f"{folder}/{uuid.uuid4()}")


def test_SA06_storage_owner_can_use_own_prefix(a_object: tuple[User, str, str]) -> None:
    a, prep_id, path = a_object
    bucket = a.client().storage.from_(MATERIALS_BUCKET)
    folder = f"{a.tenant_id}/{prep_id}"

    assert bucket.download(path) == PDF_BYTES
    assert path.rsplit("/", 1)[1] in [o["name"] for o in bucket.list(folder)]
    assert bucket.create_signed_upload_url(f"{folder}/{uuid.uuid4()}")
    bucket.remove([path])
    assert bucket.list(folder) == []


# --- AC-25 ------------------------------------------------------------------------------------


def test_SA06_materials_rows_isolation(
    client: TestClient,
    admin: Client,
    make_user: Callable[[], User],
    a_object: tuple[User, str, str],
) -> None:
    _, _, path = a_object
    material_id = path.rsplit("/", 1)[1]
    b = make_user().client()

    assert b.table("materials").select("*").eq("id", material_id).execute().data == []
    changed = (
        b.table("materials")
        .update({"uploaded_at": "2026-01-01T00:00:00Z", "content_type": "image/png"})
        .eq("id", material_id)
        .execute()
        .data
    )
    assert changed == []
    row = admin.table("materials").select("uploaded_at,content_type").eq("id", material_id)
    saved = row.single().execute().data
    assert saved == {"uploaded_at": None, "content_type": "application/pdf"}


# --- AC-26 ------------------------------------------------------------------------------------


def test_CM03_bucket_is_private_with_size_limit(admin: Client) -> None:
    bucket = admin.storage.get_bucket(MATERIALS_BUCKET)

    assert bucket.public is False
    assert bucket.file_size_limit == LIMIT


def test_CM03_storage_refuses_object_over_bucket_limit(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """The client says size_bytes 1, then sends one byte over the hard limit (about 50 MB)."""
    a = make_user()
    prep_id = insert_prep(admin, a)

    _, put = upload(client, a, prep_id, data=b"\0" * (LIMIT + 1))

    assert put.status_code >= 400
    assert object_names(admin, f"{a.tenant_id}/{prep_id}") == []
