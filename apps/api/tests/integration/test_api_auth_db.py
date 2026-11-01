"""SA-06: real Supabase tokens pass the API check, and the per-request client keeps RLS on.

specs/features/platform/api-auth.md AC-15 and AC-tenant. Runs against the Supabase stack of
.env or CI (local `supabase start` signs with HS256, so the verifier asks the Auth server; the
cloud project signs with ES256 and checks the JWKS). Users are created with the admin API and
deleted afterwards, as in test_rls_isolation.py.
"""

import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError
from supabase import Client, ClientOptions, create_client

from app.auth import (
    AuthContext,
    TokenVerifier,
    get_auth,
    get_auth_required,
    get_user_db,
    get_verifier,
    install_auth_errors,
)
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


@dataclass
class SignedInUser:
    user_id: str
    tenant_id: str
    token: str
    exam_prep_id: str


@pytest.fixture(scope="module")
def admin() -> Client:
    return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))


@pytest.fixture(scope="module")
def users(admin: Client) -> Iterator[tuple[SignedInUser, SignedInUser]]:
    created: list[SignedInUser] = []
    try:
        for _ in range(2):
            email = f"auth-{uuid.uuid4().hex}@example.test"
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
            exam_prep_id = (
                admin.table("exam_preps")
                .insert(
                    {
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "title": "api-auth",
                        "exam_date": date.today().isoformat(),
                    }
                )
                .execute()
                .data[0]["id"]
            )
            created.append(SignedInUser(user_id, tenant_id, token, exam_prep_id))
        yield created[0], created[1]
    finally:
        for user in created:
            admin.auth.admin.delete_user(user.user_id)
            admin.table("tenants").delete().eq("id", user.tenant_id).execute()


def _probe() -> tuple[TestClient, list[Any]]:
    seen: list[Any] = []
    probe = FastAPI()
    install_auth_errors(probe)  # the 401 envelope, as app.main does (Jam ok 2026-11-01)

    @probe.get("/probe")
    async def handler(auth: Annotated[AuthContext | None, Depends(get_auth)]) -> dict[str, str]:
        seen.append(auth)
        return {"ok": "yes"}

    verifier = TokenVerifier(_URL, _ANON_KEY)
    probe.dependency_overrides[get_verifier] = lambda: verifier
    probe.dependency_overrides[get_auth_required] = lambda: True
    return TestClient(probe), seen


def test_SA06_real_supabase_token_passes_and_tampered_fails(
    users: tuple[SignedInUser, SignedInUser],
) -> None:
    a, _ = users
    client, seen = _probe()

    ok = client.get("/probe", headers={"Authorization": f"Bearer {a.token}"})
    # Change the first signature character: the last one has spare base64 bits, so changing it
    # sometimes leaves the same signature bytes (CI flake on #98 · Jam ok 2026-11-01).
    head, payload, signature = a.token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered = ".".join([head, payload, flipped])
    bad = client.get("/probe", headers={"Authorization": f"Bearer {tampered}"})

    assert ok.status_code == 200
    assert seen[0].tenant_id == uuid.UUID(a.tenant_id)
    assert seen[0].user_id == uuid.UUID(a.user_id)
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "invalid_token"


def test_SA06_user_db_client_sees_only_own_tenant(
    users: tuple[SignedInUser, SignedInUser],
) -> None:
    a, b = users
    auth = AuthContext(
        tenant_id=uuid.UUID(a.tenant_id), user_id=uuid.UUID(a.user_id), token=a.token
    )

    db = get_user_db(auth)

    visible = {row["id"] for row in db.table("exam_preps").select("id").execute().data}
    assert visible == {a.exam_prep_id}
    with pytest.raises(APIError) as exc:
        db.table("exam_preps").insert(
            {
                "tenant_id": b.tenant_id,
                "user_id": b.user_id,
                "title": "intruder",
                "exam_date": date.today().isoformat(),
            }
        ).execute()
    assert exc.value.code == "42501"
