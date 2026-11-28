"""GET and PATCH /me/profile against real Supabase (specs/features/platform/display-name.md).

Like test_exam_prep_db.py: users come from the admin API (handle_new_user gives each a personal
tenant and a profiles row with nickname null, since these accounts have no Google name), the app
checks real tokens (AUTH_REQUIRED=true), and the API writes through the user's JWT, so RLS
decides. The service role only sets up facts the API cannot (tutor and buddy rows, a raw
nickname, a missing row) and reads rows back. The greeting texts come from config/messages.yaml.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from supabase import Client, ClientOptions, create_client

from app.auth import TokenVerifier, get_auth_required, get_verifier
from app.main import app
from app.settings import EnvSettings, get_settings
from tests.unit.test_tutor_reply_stream_api import parse_sse

_env = EnvSettings()
_URL = _env.supabase_url
_ANON_KEY = _env.supabase_anon_key.get_secret_value()
_SERVICE_KEY = _env.supabase_service_role_key.get_secret_value()

if not (_URL and _ANON_KEY and _SERVICE_KEY):
    if os.environ.get("CI"):
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY not set")
    pytest.skip("Supabase is not configured", allow_module_level=True)

_NO_SESSION = {"auto_refresh_token": False, "persist_session": False}
PATH = "/me/profile"
GREETING = get_settings().messages.room_greeting


@dataclass
class User:
    user_id: str
    tenant_id: str
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


@pytest.fixture(scope="module")
def admin() -> Client:
    return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))


@pytest.fixture(scope="module")
def make_user(admin: Client) -> Iterator[Callable[[], User]]:
    created: list[User] = []

    def make() -> User:
        email = f"profile-{uuid.uuid4().hex}@example.test"
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
        signer = create_client(_URL, _ANON_KEY, ClientOptions(**_NO_SESSION))
        token = signer.auth.sign_in_with_password(
            {"email": email, "password": password}
        ).session.access_token
        user = User(user_id, tenant_id, token)
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


def profile_row(admin: Client, user: User) -> dict[str, Any] | None:
    rows = admin.table("profiles").select("*").eq("user_id", user.user_id).execute().data
    return rows[0] if rows else None


def add_crew(admin: Client, user: User) -> None:
    owner = {"tenant_id": user.tenant_id, "user_id": user.user_id}
    admin.table("tutor_profiles").insert({**owner, "params": {"name": "พี่ฟ้า"}}).execute()
    admin.table("buddy_profiles").insert(
        {**owner, "enabled": True, "params": {"name": "ต้นกล้า"}}
    ).execute()


def greeting_of(client: TestClient, user: User) -> tuple[str, str]:
    """A new prep and a new session: (Room.user_name, the first tutor message)."""
    body = {"title": "แคลคูลัส 1", "exam_date": str(date.today() + timedelta(days=20))}
    prep = client.post("/exam-preps", json=body, headers=user.headers)
    assert prep.status_code == 201, prep.text
    opened = client.post(f"/exam-preps/{prep.json()['id']}/sessions", headers=user.headers)
    assert opened.status_code == 200, opened.text
    session_id = parse_sse(opened.text)[0][1]["session_id"]
    room = client.get(f"/sessions/{session_id}", headers=user.headers).json()
    return room["user_name"], room["messages"][0]["content"]


# --- save and read (AC-1, AC-2, AC-4) -----------------------------------------------------


def test_UM08_patch_saves_and_get_reads_it_back(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-1, AC-2: a new account starts with nickname null, PATCH writes the row through the
    user's JWT, and GET reads it back with no X-Stub."""
    a = make_user()
    assert profile_row(admin, a)["nickname"] is None

    saved = client.patch(PATH, json={"nickname": "  ปาล์ม "}, headers=a.headers)
    read = client.get(PATH, headers=a.headers)

    assert saved.status_code == 200, saved.text
    assert read.status_code == 200, read.text
    assert saved.json()["nickname"] == read.json()["nickname"] == "ปาล์ม"
    assert "x-stub" not in saved.headers and "x-stub" not in read.headers
    assert profile_row(admin, a)["nickname"] == "ปาล์ม"


def test_UM09_clearing_the_nickname_stores_null(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-4."""
    a = make_user()
    admin.table("profiles").update({"nickname": "ปาล์ม"}).eq("user_id", a.user_id).execute()

    response = client.patch(PATH, json={"nickname": ""}, headers=a.headers)

    assert response.status_code == 200, response.text
    assert response.json()["nickname"] is None
    assert profile_row(admin, a)["nickname"] is None


# --- only the sent field (AC-8) and setup_step (AC-9) -------------------------------------


def test_UM09_patch_leaves_the_other_columns_alone(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-8."""
    a = make_user()
    admin.table("profiles").update({"education_level": "university", "explain_language": "en"}).eq(
        "user_id", a.user_id
    ).execute()

    body = client.patch(PATH, json={"nickname": "ปาล์ม"}, headers=a.headers).json()

    row = profile_row(admin, a)
    assert (row["education_level"], row["explain_language"]) == ("university", "en")
    assert (body["education_level"], body["explain_language"]) == ("university", "en")


def test_UM08_setup_step_from_real_rows(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-9: crew → profile → done as the rows appear. auto_read stays false."""
    a = make_user()
    steps = [client.get(PATH, headers=a.headers).json()]
    add_crew(admin, a)
    steps.append(client.get(PATH, headers=a.headers).json())
    admin.table("profiles").update({"education_level": "university"}).eq(
        "user_id", a.user_id
    ).execute()
    steps.append(client.get(PATH, headers=a.headers).json())

    assert [s["setup_step"] for s in steps] == ["crew", "profile", "done"]
    assert {s["auto_read"] for s in steps} == {False}


# --- the room uses the new name (AC-11) ---------------------------------------------------


def test_TM13_a_new_session_greets_with_the_saved_name(
    client: TestClient, make_user: Callable[[], User]
) -> None:
    """AC-11: after PATCH the next session is named, after clearing it is anonymous, and the
    greeting saved in the first session does not change."""
    a = make_user()

    client.patch(PATH, json={"nickname": "ปาล์ม"}, headers=a.headers)
    named_user, named_greeting = greeting_of(client, a)
    client.patch(PATH, json={"nickname": None}, headers=a.headers)
    anonymous_user, anonymous_greeting = greeting_of(client, a)

    assert named_user == "ปาล์ม"
    assert named_greeting.startswith(GREETING.hello_named.format(user_name="ปาล์ม"))
    assert anonymous_user == "คุณ"
    assert anonymous_greeting.startswith(GREETING.hello_anonymous)
    assert not anonymous_greeting.startswith(GREETING.hello_named.format(user_name="ปาล์ม"))


def test_TM13_an_earlier_greeting_is_not_rewritten(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-11: the saved greeting message keeps the old name."""
    a = make_user()
    client.patch(PATH, json={"nickname": "ปาล์ม"}, headers=a.headers)
    _, first = greeting_of(client, a)

    client.patch(PATH, json={"nickname": "นนท์"}, headers=a.headers)

    rows = (
        admin.table("messages")
        .select("content")
        .eq("tenant_id", a.tenant_id)
        .eq("role", "tutor")
        .execute()
        .data
    )
    assert [r["content"] for r in rows] == [first]
    assert "ปาล์ม" in first


# --- no profiles row (AC-no-row) ----------------------------------------------------------


def test_UM09_no_profile_row_is_404_and_none_is_created(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-no-row."""
    a = make_user()
    admin.table("profiles").delete().eq("user_id", a.user_id).execute()

    read = client.get(PATH, headers=a.headers)
    saved = client.patch(PATH, json={"nickname": "ปาล์ม"}, headers=a.headers)

    assert read.status_code == 404, read.text
    assert saved.status_code == 404, saved.text
    assert read.json()["error"]["code"] == saved.json()["error"]["code"] == "not_found"
    assert profile_row(admin, a) is None


# --- tenants (AC-tenant through the API) --------------------------------------------------


def test_SA06_patch_changes_only_the_callers_row(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-tenant: A's PATCH and GET never touch or show B's row."""
    a, b = make_user(), make_user()
    client.patch(PATH, json={"nickname": "บี"}, headers=b.headers)

    client.patch(PATH, json={"nickname": "เอ"}, headers=a.headers)

    assert client.get(PATH, headers=a.headers).json()["nickname"] == "เอ"
    assert client.get(PATH, headers=b.headers).json()["nickname"] == "บี"
    assert profile_row(admin, b)["nickname"] == "บี"
