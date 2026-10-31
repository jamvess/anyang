"""SA-06: a user cannot read or write another tenant's rows through RLS.

Two users are created with the admin API (the signup trigger gives each a personal
tenant), signed in with a password, and then queried through anon-key clients that
carry only their own JWT. Rows are seeded with the service role, which bypasses RLS.
"""

import base64
import json
import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date

import pytest
from postgrest.exceptions import APIError
from supabase import Client, ClientOptions, create_client

from app.settings import EnvSettings

_env = EnvSettings()
_URL = _env.supabase_url
_ANON_KEY = _env.supabase_anon_key.get_secret_value()
_SERVICE_KEY = _env.supabase_service_role_key.get_secret_value()

if not (_URL and _ANON_KEY and _SERVICE_KEY):
    # CI must never silently skip the isolation proof.
    if os.environ.get("CI"):
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY not set")
    pytest.skip("Supabase is not configured", allow_module_level=True)

_NO_SESSION = {"auto_refresh_token": False, "persist_session": False}


@dataclass
class TenantUser:
    user_id: str
    tenant_id: str
    jwt: str
    client: Client  # anon key + this user's JWT, so RLS applies
    rows: dict[str, str] = field(default_factory=dict)  # table -> seeded row id


def _jwt_claims(token: str) -> dict:
    payload = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


def _seed(admin: Client, user_id: str, tenant_id: str) -> dict[str, str]:
    """Insert one exam_prep, message and attempt (plus their parents) for this user."""

    def insert(table: str, row: dict) -> str:
        return admin.table(table).insert({"tenant_id": tenant_id, **row}).execute().data[0]["id"]

    exam_prep = insert(
        "exam_preps", {"user_id": user_id, "title": "SA06", "exam_date": date.today().isoformat()}
    )
    scope = insert("scope_versions", {"exam_prep_id": exam_prep, "version": 1, "snapshot": {}})
    topic = insert("topics", {"exam_prep_id": exam_prep, "name": "SA06", "order_index": 0})
    session = insert(
        "tutor_sessions",
        {"user_id": user_id, "exam_prep_id": exam_prep, "scope_version_id": scope},
    )
    message = insert("messages", {"session_id": session, "role": "user", "content": "SA06"})
    problem = insert(
        "problems",
        {
            "session_id": session,
            "topic_id": topic,
            "source": "generated",
            "text": "1+1",
            "reference_answer": "2",
            "answer_format": "numeric",
            "difficulty": 1,
            "purpose": "probe",
        },
    )
    attempt = insert(
        "attempts",
        {
            "user_id": user_id,
            "problem_id": problem,
            "topic_id": topic,
            "answer_text": "2",
            "verdict": "correct",
            "is_correct": True,
            "decided_by": "sympy",
        },
    )
    return {
        "exam_preps": exam_prep,
        "messages": message,
        "attempts": attempt,
        "tutor_sessions": session,
        "problems": problem,
        "topics": topic,
    }


@pytest.fixture(scope="module")
def admin() -> Client:
    return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))


@pytest.fixture(scope="module")
def users(admin: Client) -> Iterator[tuple[TenantUser, TenantUser]]:
    created: list[TenantUser] = []
    try:
        for _ in range(2):
            email = f"sa06-{uuid.uuid4().hex}@example.test"
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
            jwt = signer.auth.sign_in_with_password(
                {"email": email, "password": password}
            ).session.access_token
            client = create_client(
                _URL,
                _ANON_KEY,
                ClientOptions(headers={"Authorization": f"Bearer {jwt}"}, **_NO_SESSION),
            )
            user = TenantUser(user_id, tenant_id, jwt, client)
            created.append(user)
            user.rows = _seed(admin, user_id, tenant_id)
        yield created[0], created[1]
    finally:
        for user in created:
            admin.auth.admin.delete_user(user.user_id)
            # Tenants are not owned by auth.users; deleting them cascades to tenant rows.
            admin.table("tenants").delete().eq("id", user.tenant_id).execute()


def _foreign_insert_row(table: str, victim: TenantUser) -> dict:
    """A row that claims to belong to the victim's tenant."""
    rows = victim.rows
    base = {"tenant_id": victim.tenant_id}
    if table == "exam_preps":
        return {
            **base,
            "user_id": victim.user_id,
            "title": "intruder",
            "exam_date": date.today().isoformat(),
        }
    if table == "messages":
        return {**base, "session_id": rows["tutor_sessions"], "role": "user", "content": "intruder"}
    return {
        **base,
        "user_id": victim.user_id,
        "problem_id": rows["problems"],
        "topic_id": rows["topics"],
        "verdict": "incorrect",
        "is_correct": False,
        "decided_by": "llm",
    }


_UPDATE = {
    "exam_preps": {"title": "hacked"},
    "messages": {"content": "hacked"},
    "attempts": {"answer_text": "hacked"},
}


@pytest.mark.parametrize("table", ["exam_preps", "attempts", "messages"])
def test_SA06_tenant_isolation(
    table: str, admin: Client, users: tuple[TenantUser, TenantUser]
) -> None:
    a, b = users

    # The custom access token hook puts the caller's tenant into the JWT.
    assert _jwt_claims(a.jwt)["tenant_id"] == a.tenant_id
    assert _jwt_claims(b.jwt)["tenant_id"] == b.tenant_id
    assert a.tenant_id != b.tenant_id

    own_id, other_id = a.rows[table], b.rows[table]

    # Read: A sees exactly its own row, never B's.
    visible = {r["id"] for r in a.client.table(table).select("id").execute().data}
    assert visible == {own_id}
    assert a.client.table(table).select("id").eq("id", other_id).execute().data == []

    # Insert into B's tenant is rejected by the WITH CHECK clause.
    with pytest.raises(APIError) as exc:
        a.client.table(table).insert(_foreign_insert_row(table, b)).execute()
    assert exc.value.code == "42501"

    # Update and delete of B's row match nothing.
    assert a.client.table(table).update(_UPDATE[table]).eq("id", other_id).execute().data == []
    assert a.client.table(table).delete().eq("id", other_id).execute().data == []

    # B's row is untouched (checked with the service role).
    row = admin.table(table).select("*").eq("id", other_id).single().execute().data
    for column, value in _UPDATE[table].items():
        assert row[column] != value


def _ai_call_row(tenant_id: str, user_id: str) -> dict:
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "purpose": "tutor_reply",
        "provider": "fake",
        "model": "fake",
        "status": "ok",
    }


def test_SA06_ai_calls_isolated_and_not_insertable_by_users(
    admin: Client, users: tuple[TenantUser, TenantUser]
) -> None:
    """ai-calls-log.md AC-tenant: rows come only from the backend (service role)."""
    a, b = users
    own_id = admin.table("ai_calls").insert(_ai_call_row(a.tenant_id, a.user_id)).execute()
    other_id = admin.table("ai_calls").insert(_ai_call_row(b.tenant_id, b.user_id)).execute()
    own_id, other_id = own_id.data[0]["id"], other_id.data[0]["id"]

    # Read: A sees its own row, never B's.
    visible = {r["id"] for r in a.client.table("ai_calls").select("id").execute().data}
    assert own_id in visible
    assert other_id not in visible

    # Insert is rejected even into A's own tenant: the policy is select only.
    for victim in (a, b):
        with pytest.raises(APIError) as exc:
            a.client.table("ai_calls").insert(
                _ai_call_row(victim.tenant_id, victim.user_id)
            ).execute()
        assert exc.value.code == "42501"
