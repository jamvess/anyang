"""The tutor room against real Supabase (specs/features/tutor/room-sessions-db.md).

Same setup as test_exam_prep_db.py: users from the admin API (deleted afterwards), real tokens
with AUTH_REQUIRED=true, the user's JWT for every query so RLS decides. The AI is the fake
provider (no network). Needs migration 0004 (scope_version_id may be null) on the project.
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

from app.ai.gateway import Gateway, get_gateway
from app.ai.providers.fake import FakeProvider
from app.auth import TokenVerifier, get_auth_required, get_verifier
from app.main import app
from app.settings import EnvSettings, get_settings
from tests.unit.test_tutor_reply_stream_api import parse_sse, tokens

_env = EnvSettings()
_URL = _env.supabase_url
_ANON_KEY = _env.supabase_anon_key.get_secret_value()
_SERVICE_KEY = _env.supabase_service_role_key.get_secret_value()

if not (_URL and _ANON_KEY and _SERVICE_KEY):
    if os.environ.get("CI"):
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY not set")
    pytest.skip("Supabase is not configured", allow_module_level=True)

_NO_SESSION = {"auto_refresh_token": False, "persist_session": False}


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


def sign_in(email: str, password: str) -> str:
    signer = create_client(_URL, _ANON_KEY, ClientOptions(**_NO_SESSION))
    return signer.auth.sign_in_with_password(
        {"email": email, "password": password}
    ).session.access_token


@pytest.fixture(scope="module")
def admin() -> Client:
    return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))


@pytest.fixture(scope="module")
def make_user(admin: Client) -> Iterator[Callable[[], User]]:
    created: list[User] = []

    def make() -> User:
        email = f"room-{uuid.uuid4().hex}@example.test"
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
    fake = FakeProvider({}, defaults={"tutor_reply": "ตอบจากติวเตอร์"})
    gateway = Gateway(
        config=get_settings().ai, prompts_dir=get_settings().env.prompts_dir, provider=fake
    )
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_auth_required] = lambda: True
    app.dependency_overrides[get_gateway] = lambda: gateway
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def new_prep(client: TestClient, user: User, title: str = "แคลคูลัส 1 กลางภาค") -> str:
    body = {"title": title, "exam_date": str(date.today() + timedelta(days=20))}
    response = client.post("/exam-preps", json=body, headers=user.headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def open_session(client: TestClient, user: User, prep_id: str) -> list[tuple[str, Any]]:
    response = client.post(f"/exam-preps/{prep_id}/sessions", headers=user.headers)
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


def test_TM13_open_session_saves_the_row_and_the_greeting(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-1 on real tables (scope_version_id null needs 0004)."""
    a = make_user()
    prep_id = new_prep(client, a)

    events = open_session(client, a, prep_id)

    session_id = events[0][1]["session_id"]
    [row] = admin.table("tutor_sessions").select("*").eq("id", session_id).execute().data
    assert (row["tenant_id"], row["user_id"], row["exam_prep_id"]) == (
        a.tenant_id,
        a.user_id,
        prep_id,
    )
    assert row["scope_version_id"] is None and row["ended_at"] is None
    [greeting] = admin.table("messages").select("*").eq("session_id", session_id).execute().data
    assert greeting["role"] == "tutor"
    assert greeting["content"] == "".join(tokens(events))
    assert greeting["tenant_id"] == a.tenant_id
    assert events[-1] == ("done", {"message_ids": [greeting["id"]]})


def test_TM13_open_session_attaches_the_active_scope_version(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-2."""
    a = make_user()
    prep_id = new_prep(client, a)
    version_id = (
        admin.table("scope_versions")
        .insert(
            {
                "tenant_id": a.tenant_id,
                "exam_prep_id": prep_id,
                "version": 1,
                "status": "confirmed",
                "snapshot": {},
            }
        )
        .execute()
        .data[0]["id"]
    )
    admin.table("exam_preps").update({"active_scope_version_id": version_id}).eq(
        "id", prep_id
    ).execute()

    session_id = open_session(client, a, prep_id)[0][1]["session_id"]

    [row] = admin.table("tutor_sessions").select("*").eq("id", session_id).execute().data
    assert row["scope_version_id"] == version_id


def test_TM13_leave_and_come_back(client: TestClient, make_user: Callable[[], User]) -> None:
    """AC-6, AC-10: chat, sign in again, find the open session and its whole history."""
    a = make_user()
    prep_id = new_prep(client, a)
    open_session(client, a, prep_id)  # an older open session
    session_id = open_session(client, a, prep_id)[0][1]["session_id"]
    for text in ["q1", "q2"]:
        response = client.post(
            f"/sessions/{session_id}/messages", json={"text": text}, headers=a.headers
        )
        assert parse_sse(response.text)[-1][0] == "done"

    fresh = {"Authorization": f"Bearer {sign_in(a.email, a.password)}"}
    active = client.get(f"/exam-preps/{prep_id}/sessions/active", headers=fresh)
    room = client.get(f"/sessions/{session_id}", headers=fresh).json()

    assert active.json() == {"session_id": session_id}
    assert [(m["role"], m["content"]) for m in room["messages"]][1:] == [
        ("user", "q1"),
        ("tutor", "ตอบจากติวเตอร์"),
        ("user", "q2"),
        ("tutor", "ตอบจากติวเตอร์"),
    ]
    assert room["messages"][0]["role"] == "tutor"  # the greeting
    assert room["prep_name"] == "แคลคูลัส 1 กลางภาค"
    assert client.get(f"/sessions/{session_id}/messages", headers=fresh).json() == room["messages"]


def test_TM13_room_names_from_real_profiles(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-11 on real tables: nickname, the highest tutor profile version, buddy enabled.
    Names differ from app/stubs/room.json, so the stub cannot pass this."""
    a = make_user()
    admin.table("profiles").update({"nickname": "นนท์"}).eq("user_id", a.user_id).execute()
    for version, name in [(1, "พี่เก่า"), (2, "พี่ฟ้า")]:
        admin.table("tutor_profiles").insert(
            {
                "tenant_id": a.tenant_id,
                "user_id": a.user_id,
                "params": {"name": name},
                "version": version,
            }
        ).execute()
    admin.table("buddy_profiles").insert(
        {
            "tenant_id": a.tenant_id,
            "user_id": a.user_id,
            "enabled": True,
            "params": {"name": "ต้นกล้า"},
        }
    ).execute()
    prep_id = new_prep(client, a)
    session_id = open_session(client, a, prep_id)[0][1]["session_id"]

    room = client.get(f"/sessions/{session_id}", headers=a.headers).json()

    assert (room["user_name"], room["tutor_name"], room["buddy_name"]) == ("นนท์", "พี่ฟ้า", "ต้นกล้า")


def test_SA06_other_tenant_cannot_see_or_write_the_room(
    client: TestClient, admin: Client, make_user: Callable[[], User]
) -> None:
    """AC-13, AC-21, AC-8, AC-3."""
    a, b = make_user(), make_user()
    prep_id = new_prep(client, a)
    session_id = open_session(client, a, prep_id)[0][1]["session_id"]

    room = client.get(f"/sessions/{session_id}", headers=b.headers)
    history = client.get(f"/sessions/{session_id}/messages", headers=b.headers)
    send = client.post(f"/sessions/{session_id}/messages", json={"text": "x"}, headers=b.headers)
    active = client.get(f"/exam-preps/{prep_id}/sessions/active", headers=b.headers)
    opened = client.post(f"/exam-preps/{prep_id}/sessions", headers=b.headers)

    for response in [room, history, send, active, opened]:
        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "not_found"
    rows = admin.table("messages").select("tenant_id").eq("session_id", session_id).execute().data
    assert [r["tenant_id"] for r in rows] == [a.tenant_id]  # only the greeting
    assert admin.table("tutor_sessions").select("id").eq("user_id", b.user_id).execute().data == []


def test_SA06_tampered_token_is_401(client: TestClient, make_user: Callable[[], User]) -> None:
    """AC-auth-bad."""
    a = make_user()
    prep_id = new_prep(client, a)
    head, payload, signature = a.token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]

    response = client.get(
        f"/exam-preps/{prep_id}/sessions/active",
        headers={"Authorization": f"Bearer {head}.{payload}.{flipped}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
