"""POST and GET /exam-preps against real Supabase (specs/features/exam-prep/create-exam-prep.md).

Runs against the Supabase stack of .env or CI, like test_api_auth_db.py: users are created with
the admin API (each gets a personal tenant from handle_new_user) and deleted afterwards. The app
checks real tokens (AUTH_REQUIRED=true through get_auth_required) and writes through the user's
JWT, so RLS decides what each user sees. The service role only sets up facts the API cannot
create yet (archived preps, files, topics, a confirmed scope) and reads rows back.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from supabase import Client, ClientOptions, create_client

from app.auth import TokenVerifier, get_auth_required, get_verifier
from app.main import app
from app.settings import EnvSettings

_env = EnvSettings()
_URL = _env.supabase_url
_ANON_KEY = _env.supabase_anon_key.get_secret_value()
_SERVICE_KEY = _env.supabase_service_role_key.get_secret_value()

if not (_URL and _ANON_KEY and _SERVICE_KEY):
    if os.environ.get("CI"):
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY not set")
    pytest.skip("Supabase is not configured", allow_module_level=True)

_NO_SESSION = {"auto_refresh_token": False, "persist_session": False}
_BANGKOK = timezone(timedelta(hours=7))


def today() -> date:
    return datetime.now(_BANGKOK).date()


@dataclass
class User:
    user_id: str
    tenant_id: str
    email: str
    password: str
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


@pytest.fixture(scope="module")
def admin() -> Client:
    return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))


def sign_in(email: str, password: str) -> str:
    signer = create_client(_URL, _ANON_KEY, ClientOptions(**_NO_SESSION))
    return signer.auth.sign_in_with_password(
        {"email": email, "password": password}
    ).session.access_token


@pytest.fixture(scope="module")
def make_user(admin: Client) -> Iterator[Callable[[], User]]:
    created: list[User] = []

    def make() -> User:
        email = f"exam-prep-{uuid.uuid4().hex}@example.test"
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
        user = User(user_id, tenant_id, email, password, sign_in(email, password))
        created.append(user)
        return user

    try:
        yield make
    finally:
        for user in created:
            admin.auth.admin.delete_user(user.user_id)
            admin.table("tenants").delete().eq("id", user.tenant_id).execute()


@pytest.fixture
def client() -> Iterator[TestClient]:
    verifier = TokenVerifier(_URL, _ANON_KEY)
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_auth_required] = lambda: True
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def prep(**change: Any) -> dict[str, Any]:
    return {"title": "แคลคูลัส 1 กลางภาค", "exam_date": str(today() + timedelta(27)), **change}


def rows_of(admin: Client, user: User) -> list[dict[str, Any]]:
    return admin.table("exam_preps").select("*").eq("user_id", user.user_id).execute().data


def insert_prep(admin: Client, user: User, **change: Any) -> str:
    row = {
        "tenant_id": user.tenant_id,
        "user_id": user.user_id,
        "title": "seeded",
        "exam_date": str(today() + timedelta(5)),
        **change,
    }
    return admin.table("exam_preps").insert(row).execute().data[0]["id"]


# --- create ------------------------------------------------------------------------------


def test_CM01_create_saves_a_row_for_the_signed_in_user(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-1, AC-auth-real."""
    a = make_user()

    response = client.post("/exam-preps", json=prep(), headers=a.headers)

    assert response.status_code == 201, response.text
    assert "x-stub" not in response.headers
    body = response.json()
    assert body["days_left"] == 27
    assert body["stage"] == "materials"
    [row] = rows_of(admin, a)
    assert row["id"] == body["id"]
    assert row["tenant_id"] == a.tenant_id
    assert row["user_id"] == a.user_id
    assert row["title"] == "แคลคูลัส 1 กลางภาค"
    assert row["exam_date"] == str(today() + timedelta(27))
    assert row["daily_minutes"] is None
    assert row["subject"] is None
    assert row["status"] == "active"


@pytest.mark.parametrize(("sent", "saved"), [(45, 45), (None, None)])
def test_CM01_daily_minutes_is_saved(
    client: TestClient,
    admin: Client,
    make_user: Callable[[], User],
    sent: int | None,
    saved: int | None,
) -> None:
    """AC-2, AC-3."""
    a = make_user()

    response = client.post("/exam-preps", json=prep(daily_minutes=sent), headers=a.headers)

    assert response.status_code == 201
    assert rows_of(admin, a)[0]["daily_minutes"] == saved


def test_CM01_same_title_twice_makes_two_rows(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-9."""
    a = make_user()

    for _ in range(2):
        assert client.post("/exam-preps", json=prep(), headers=a.headers).status_code == 201

    assert len(rows_of(admin, a)) == 2


# --- list --------------------------------------------------------------------------------


def test_CM01_new_user_has_an_empty_list(client: TestClient, make_user: Callable[[], User]) -> None:
    """AC-10."""
    a = make_user()

    response = client.get("/exam-preps", headers=a.headers)

    assert response.status_code == 200
    assert response.json() == []
    assert "x-stub" not in response.headers


def test_CM02_list_order_and_days_left(client: TestClient, make_user: Callable[[], User]) -> None:
    """AC-11, AC-12."""
    a = make_user()
    for title, days in [("far", 10), ("first", 3), ("second", 3)]:
        body = prep(title=title, exam_date=str(today() + timedelta(days)))
        assert client.post("/exam-preps", json=body, headers=a.headers).status_code == 201

    body = client.get("/exam-preps", headers=a.headers).json()

    assert [p["title"] for p in body] == ["first", "second", "far"]
    assert [p["days_left"] for p in body] == [3, 3, 10]


def test_CM01_archived_preps_are_left_out(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-13."""
    a = make_user()
    insert_prep(admin, a, title="archived", status="archived")
    insert_prep(admin, a, title="active")

    titles = [p["title"] for p in client.get("/exam-preps", headers=a.headers).json()]

    assert titles == ["active"]


def test_CM02_past_exam_is_listed_with_negative_days(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-14."""
    a = make_user()
    insert_prep(admin, a, exam_date=str(today() - timedelta(1)))

    assert client.get("/exam-preps", headers=a.headers).json()[0]["days_left"] == -1


def test_CM01_stage_reads_files_topics_and_scope_through_rls(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-15 on the real tables (every rule is covered in test_exam_prep_stage.py)."""
    a = make_user()
    ids = {name: insert_prep(admin, a, title=name) for name in ["m", "p", "s", "t"]}

    def material(prep_id: str, kind_confirmed: bool, status: str) -> None:
        material_id = str(uuid.uuid4())
        admin.table("materials").insert(
            {
                "id": material_id,
                "tenant_id": a.tenant_id,
                "exam_prep_id": prep_id,
                "storage_path": f"{a.tenant_id}/{prep_id}/{material_id}",
                "file_name": "sheet.pdf",
                "kind": "sheet",
                "kind_confirmed": kind_confirmed,
                "status": status,
            }
        ).execute()

    material(ids["m"], False, "classified")
    material(ids["p"], True, "ingesting")
    material(ids["s"], True, "ready")
    for index, importance in enumerate([3, 1]):
        admin.table("topics").insert(
            {
                "tenant_id": a.tenant_id,
                "exam_prep_id": ids["s"],
                "name": f"topic {index}",
                "order_index": index,
                "importance": importance,
            }
        ).execute()
    version_id = (
        admin.table("scope_versions")
        .insert(
            {
                "tenant_id": a.tenant_id,
                "exam_prep_id": ids["t"],
                "version": 1,
                "status": "confirmed",
                "snapshot": {},
            }
        )
        .execute()
        .data[0]["id"]
    )
    admin.table("exam_preps").update({"active_scope_version_id": version_id}).eq(
        "id", ids["t"]
    ).execute()

    body = {p["title"]: p for p in client.get("/exam-preps", headers=a.headers).json()}

    assert {t: p["stage"] for t, p in body.items()} == {
        "m": "materials",
        "p": "processing",
        "s": "scope",
        "t": "tutoring",
    }
    assert body["t"]["readiness"] is None and body["t"]["topics_not_passed"] is None


def test_CM01_saved_prep_is_there_after_signing_in_again(
    client: TestClient, make_user: Callable[[], User]
) -> None:
    """AC-16: saved in the database, not in the API's memory."""
    a = make_user()
    created = client.post("/exam-preps", json=prep(), headers=a.headers).json()

    fresh = sign_in(a.email, a.password)
    body = client.get("/exam-preps", headers={"Authorization": f"Bearer {fresh}"}).json()

    assert [p["id"] for p in body] == [created["id"]]


# --- auth and tenants --------------------------------------------------------------------


def test_SA06_tenants_do_not_see_each_others_preps(
    client: TestClient, make_user: Callable[[], User]
) -> None:
    """AC-tenant."""
    a, b = make_user(), make_user()
    for title in ["a1", "a2"]:
        client.post("/exam-preps", json=prep(title=title), headers=a.headers)

    assert client.get("/exam-preps", headers=b.headers).json() == []

    client.post("/exam-preps", json=prep(title="b1"), headers=b.headers)

    assert sorted(p["title"] for p in client.get("/exam-preps", headers=a.headers).json()) == [
        "a1",
        "a2",
    ]


@pytest.mark.parametrize("field", ["tenant_id", "user_id"])
def test_SA06_body_cannot_name_another_tenant_or_user(
    client: TestClient, admin: Client, make_user: Callable[[], User], field: str
) -> None:
    """AC-tenant-body."""
    a, b = make_user(), make_user()
    target = a.tenant_id if field == "tenant_id" else a.user_id

    response = client.post("/exam-preps", json=prep(**{field: target}), headers=b.headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert rows_of(admin, a) == [] and rows_of(admin, b) == []


@pytest.mark.parametrize(("method", "body"), [("POST", prep()), ("GET", None)])
def test_SA06_tampered_token_is_401(
    client: TestClient,
    admin: Client,
    make_user: Callable[[], User],
    method: str,
    body: Any,
) -> None:
    """AC-auth-bad (with AUTH_REQUIRED=true here; the unit tests cover the switch)."""
    a = make_user()
    head, payload, signature = a.token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]

    response = client.request(
        method,
        "/exam-preps",
        json=body,
        headers={"Authorization": f"Bearer {head}.{payload}.{flipped}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
    assert rows_of(admin, a) == []


def test_SA06_tampered_token_is_401_without_auth_required(
    client: TestClient, make_user: Callable[[], User]
) -> None:
    """AC-auth-bad: AUTH_REQUIRED=false never turns a bad token into the stub."""
    app.dependency_overrides[get_auth_required] = lambda: False
    a = make_user()
    head, payload, signature = a.token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]

    response = client.get(
        "/exam-preps", headers={"Authorization": f"Bearer {head}.{payload}.{flipped}"}
    )

    assert response.status_code == 401
    assert "x-stub" not in response.headers
