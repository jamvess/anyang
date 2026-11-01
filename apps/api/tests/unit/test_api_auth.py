"""SA-06: the API checks the Supabase JWT of every request outside the public allowlist.

Behavior from specs/features/platform/api-auth.md §2 and §4 (AC-1 to AC-14). No network: tokens
are signed here with an ES256 key made by the test, and the verifier's HTTP client is an httpx
MockTransport that serves the JWKS of that key (the way Supabase cloud signs, `anyang-dev`).
The HS256 path of the local Supabase stack is covered by tests/integration/test_api_auth_db.py.
"""

import json
import logging
import threading
import time
import uuid
from collections.abc import Iterator
from typing import Annotated, Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.routing import Route

import app.ai.gateway as gateway_module
from app.ai.gateway import Gateway, get_gateway
from app.ai.providers.fake import FakeProvider
from app.auth import (
    PUBLIC_PATHS,
    AuthContext,
    TokenVerifier,
    build_verifier,
    get_auth,
    get_auth_required,
    get_verifier,
    install_auth_errors,
)
from app.db.ai_calls import AICallLog
from app.main import app
from app.models.error import ErrorResponse
from app.settings import EnvSettings, get_settings

SUPABASE_URL = "https://test-project.supabase.co"
ANON_KEY = "test-anon-key"
KID = "test-key-1"
TENANT = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
USER = uuid.UUID("00000000-0000-4000-8000-0000000000b2")
SESSION_ID = "00000000-0000-4000-8000-000000000002"

SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_KEY = ec.generate_private_key(ec.SECP256R1())  # not in the JWKS


def jwks_of(key: ec.EllipticCurvePrivateKey, kid: str = KID) -> dict[str, Any]:
    public = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(key.public_key()))
    return {"keys": [public | {"kid": kid, "alg": "ES256", "use": "sig"}]}


def make_token(
    key: ec.EllipticCurvePrivateKey = SIGNING_KEY, kid: str = KID, **claim_changes: Any
) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "sub": str(USER),
        "tenant_id": str(TENANT),
        "role": "authenticated",
        "aud": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(claim_changes)
    claims = {k: v for k, v in claims.items() if v is not None}  # None removes a claim
    return jwt.encode(claims, key, algorithm="ES256", headers={"kid": kid})


class FakeSupabaseAuth:
    """Serves GET /auth/v1/.well-known/jwks.json and counts every request by path."""

    def __init__(self) -> None:
        self.requests: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request.url.path)
        if request.url.path.endswith("/.well-known/jwks.json"):
            return httpx.Response(200, json=jwks_of(SIGNING_KEY))
        return httpx.Response(401, json={"msg": "unexpected call in a unit test"})


@pytest.fixture
def supabase_auth() -> FakeSupabaseAuth:
    return FakeSupabaseAuth()


@pytest.fixture
def verifier(supabase_auth: FakeSupabaseAuth) -> TokenVerifier:
    http = httpx.AsyncClient(transport=httpx.MockTransport(supabase_auth.handler))
    return TokenVerifier(SUPABASE_URL, ANON_KEY, http_client=http)


def probe_app(verifier: TokenVerifier | None, required: bool) -> tuple[FastAPI, list[Any]]:
    """A one-route app whose handler records the AuthContext it was given."""
    seen: list[Any] = []
    probe = FastAPI()
    install_auth_errors(probe)  # the 401 envelope, as app.main does (Jam ok 2026-11-01)

    @probe.get("/probe")
    async def handler(auth: Annotated[AuthContext | None, Depends(get_auth)]) -> dict[str, str]:
        seen.append(auth)
        return {"ok": "yes"}

    probe.dependency_overrides[get_verifier] = lambda: verifier
    probe.dependency_overrides[get_auth_required] = lambda: required
    return probe, seen


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_401(response: httpx.Response, code: str) -> None:
    assert response.status_code == 401
    assert response.headers["www-authenticate"].lower().startswith("bearer")
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == code


@pytest.fixture
def real_app(verifier: TokenVerifier) -> Iterator[TestClient]:
    """The real app with auth required and the test verifier."""
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_auth_required] = lambda: True
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_verifier, None)
        app.dependency_overrides.pop(get_auth_required, None)


# --- AC-1 to AC-6 · checking the token ---------------------------------------------------------


def test_SA06_valid_token_gives_tenant_and_user(verifier: TokenVerifier):
    probe, seen = probe_app(verifier, required=True)

    token = make_token()

    response = TestClient(probe).get("/probe", headers=bearer(token))

    assert response.status_code == 200
    assert len(seen) == 1
    assert (seen[0].tenant_id, seen[0].user_id) == (TENANT, USER)
    assert seen[0].token == token  # kept for the per-request Supabase client


def test_SA06_missing_token_is_401(verifier: TokenVerifier):
    probe, seen = probe_app(verifier, required=True)

    response = TestClient(probe).get("/probe")

    assert_401(response, "missing_token")
    assert seen == []


@pytest.mark.parametrize("header", ["Basic abc", "Bearer", "Bearer ", "", "Token xyz"])
def test_SA06_non_bearer_header_is_missing_token(verifier: TokenVerifier, header: str):
    probe, _ = probe_app(verifier, required=True)

    response = TestClient(probe).get("/probe", headers={"Authorization": header})

    assert_401(response, "missing_token")


def test_SA06_lowercase_bearer_is_accepted(verifier: TokenVerifier):
    probe, seen = probe_app(verifier, required=True)

    response = TestClient(probe).get("/probe", headers={"Authorization": f"bearer {make_token()}"})

    assert response.status_code == 200
    assert seen[0].tenant_id == TENANT


def _tampered() -> str:
    head, payload, signature = make_token().split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
    return ".".join([head, payload, flipped])


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(_tampered(), id="bad-signature"),
        pytest.param(make_token(key=OTHER_KEY), id="key-not-in-jwks"),
        pytest.param(make_token(exp=int(time.time()) - 60), id="expired"),
        pytest.param("not-a-jwt", id="not-a-jwt"),
    ],
)
def test_SA06_bad_token_is_401(verifier: TokenVerifier, token: str):
    probe, seen = probe_app(verifier, required=True)

    response = TestClient(probe).get("/probe", headers=bearer(token))

    assert_401(response, "invalid_token")
    assert seen == []


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"tenant_id": None}, id="no-tenant"),
        pytest.param({"tenant_id": "tenant-1"}, id="tenant-not-uuid"),
        pytest.param({"sub": None}, id="no-sub"),
        pytest.param({"role": "anon"}, id="anon-role"),
    ],
)
def test_SA06_token_without_tenant_or_user_is_401(verifier: TokenVerifier, changes: dict):
    probe, seen = probe_app(verifier, required=True)

    response = TestClient(probe).get("/probe", headers=bearer(make_token(**changes)))

    assert_401(response, "invalid_token")
    assert seen == []


def test_SA06_401_hides_details_and_never_logs_the_token(
    verifier: TokenVerifier, caplog: pytest.LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)
    probe, _ = probe_app(verifier, required=True)
    client = TestClient(probe)
    bad_tokens = [_tampered(), make_token(key=OTHER_KEY), make_token(exp=int(time.time()) - 60)]

    messages = {
        client.get("/probe", headers=bearer(t)).json()["error"]["message"] for t in bad_tokens
    }

    assert len(messages) == 1  # one fixed text, whatever went wrong
    logged = "\n".join(r.getMessage() for r in caplog.records)
    for token in bad_tokens:
        assert token not in logged
        assert token.split(".")[2] not in logged  # not even the signature part


# --- AC-7, AC-8 · AUTH_REQUIRED -----------------------------------------------------------------


def test_SA06_auth_not_required_lets_anonymous_through(verifier: TokenVerifier):
    probe, seen = probe_app(verifier, required=False)
    client = TestClient(probe)

    anonymous = client.get("/probe")
    bad = client.get("/probe", headers=bearer(_tampered()))
    good = client.get("/probe", headers=bearer(make_token()))

    assert anonymous.status_code == 200
    assert_401(bad, "invalid_token")
    assert good.status_code == 200
    assert seen[0] is None
    assert seen[1].tenant_id == TENANT


def test_SA06_required_auth_needs_supabase_settings(caplog: pytest.LogCaptureFixture):
    with pytest.raises(ValidationError) as raised:
        EnvSettings(_env_file=None, auth_required=True, supabase_url="", supabase_anon_key="")
    assert "SUPABASE_URL" in str(raised.value)

    caplog.set_level(logging.WARNING)
    env = EnvSettings(_env_file=None, auth_required=False, supabase_url="", supabase_anon_key="")
    assert build_verifier(env) is None
    assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 1

    # Without a verifier nothing is checked: even a token gets no AuthContext.
    probe, seen = probe_app(None, required=False)
    response = TestClient(probe).get("/probe", headers=bearer(make_token()))
    assert response.status_code == 200
    assert seen == [None]


def test_SA06_supabase_settings_build_a_verifier():
    env = EnvSettings(
        _env_file=None, auth_required=True, supabase_url=SUPABASE_URL, supabase_anon_key=ANON_KEY
    )

    assert isinstance(build_verifier(env), TokenVerifier)


# --- AC-9 to AC-11 · which endpoints are checked ------------------------------------------------


def _example_path(path: str) -> str:
    """Fill every {param} with a UUID (every path parameter of api.md is an id)."""
    parts = []
    for part in path.split("/"):
        parts.append(str(uuid.uuid4()) if part.startswith("{") else part)
    return "/".join(parts)


def _all_endpoints() -> list[tuple[str, str]]:
    """(method, path) of every endpoint. FastAPI 0.143 keeps an included router as one
    ``_IncludedRouter`` entry in ``app.routes`` with no path, so API endpoints come from the
    OpenAPI schema; the docs routes are plain Starlette routes (Jam ok 2026-11-01)."""
    endpoints = [(m.upper(), p) for p, ops in app.openapi()["paths"].items() for m in ops]
    endpoints += [("GET", r.path) for r in app.routes if isinstance(r, Route)]
    return endpoints


def test_SA06_every_route_outside_allowlist_needs_a_token(real_app: TestClient):
    checked = []
    for method, path in _all_endpoints():
        url = _example_path(path)
        body = {"text": "สวัสดี"} if method == "POST" else None
        response = real_app.request(method, url, json=body)
        if path in PUBLIC_PATHS:
            assert response.status_code == 200, path
        else:
            assert_401(response, "missing_token")
            checked.append(path)

    room_paths = {p for p in app.openapi()["paths"] if p != "/health"}
    assert len(room_paths) >= 4  # the walk must not come back empty
    assert room_paths <= set(checked)  # the 4 room endpoints at least
    assert {"/health", "/openapi.json", "/docs"} <= set(PUBLIC_PATHS)


def test_SA06_cors_preflight_is_not_blocked(real_app: TestClient):
    origin = get_settings().env.cors_allow_origins[0]

    response = real_app.options(
        f"/sessions/{SESSION_ID}/messages",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_SA06_openapi_documents_bearer_and_401():
    schema = app.openapi()

    schemes = schema["components"]["securitySchemes"].values()
    assert any(s.get("type") == "http" and s.get("scheme", "").lower() == "bearer" for s in schemes)
    for path, operations in schema["paths"].items():
        if path in PUBLIC_PATHS:
            continue
        for method, operation in operations.items():
            response = operation["responses"].get("401")
            assert response is not None, f"{method.upper()} {path} has no 401"
            ref = response["content"]["application/json"]["schema"]["$ref"]
            assert ref.endswith("/ErrorResponse")
            assert operation.get("security"), f"{method.upper()} {path} has no security"


# --- AC-12, AC-13 · the auth result reaches ai_calls --------------------------------------------


class FakeWriter:
    """The insert runs on the listener's thread, so the test waits on ``inserted``."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.inserted = threading.Event()

    def insert(self, row: dict) -> None:
        self.rows.append(row)
        self.inserted.set()


@pytest.fixture
def logged_gateway(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Gateway, AICallLog]]:
    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", no_sleep)
    fake = FakeProvider({"tutor_reply": ["สวัสดีครับ วันนี้ทวนลิมิตกัน"]})
    settings = get_settings()
    gateway = Gateway(config=settings.ai, prompts_dir=settings.env.prompts_dir, provider=fake)
    call_log = AICallLog(writer=FakeWriter())
    gateway.add_listener(call_log)
    app.dependency_overrides[get_gateway] = lambda: gateway
    try:
        yield gateway, call_log
    finally:
        app.dependency_overrides.pop(get_gateway, None)


def test_AI04_chat_turn_writes_ai_calls_row_for_the_token_user(
    real_app: TestClient, logged_gateway: tuple[Gateway, AICallLog]
):
    _, call_log = logged_gateway

    response = real_app.post(
        f"/sessions/{SESSION_ID}/messages", json={"text": "สวัสดี"}, headers=bearer(make_token())
    )

    assert response.status_code == 200
    assert call_log.writer.inserted.wait(timeout=5)
    assert "event: done" in response.text
    rows = call_log.writer.rows
    assert len(rows) == 1
    assert rows[0]["tenant_id"] == str(TENANT)
    assert rows[0]["user_id"] == str(USER)
    assert rows[0]["purpose"] == "tutor_reply"
    assert rows[0]["session_id"] is None


def test_AI04_anonymous_chat_turn_still_streams_without_a_row(
    verifier: TokenVerifier, logged_gateway: tuple[Gateway, AICallLog]
):
    _, call_log = logged_gateway
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_auth_required] = lambda: False
    try:
        with TestClient(app) as client:
            response = client.post(f"/sessions/{SESSION_ID}/messages", json={"text": "สวัสดี"})
    finally:
        app.dependency_overrides.pop(get_verifier, None)
        app.dependency_overrides.pop(get_auth_required, None)

    # Without a tenant the listener decides on the spot not to insert, so no wait is needed.
    assert response.status_code == 200
    assert "event: token" in response.text
    assert "event: done" in response.text
    assert call_log.writer.rows == []


# --- AC-14 · no network per request -------------------------------------------------------------


def test_NFRP1_es256_check_fetches_jwks_once(
    verifier: TokenVerifier, supabase_auth: FakeSupabaseAuth
):
    probe, seen = probe_app(verifier, required=True)
    client = TestClient(probe)

    first = client.get("/probe", headers=bearer(make_token()))
    second = client.get("/probe", headers=bearer(make_token(sub=str(uuid.uuid4()))))

    assert (first.status_code, second.status_code) == (200, 200)
    assert len(seen) == 2
    jwks_calls = [p for p in supabase_auth.requests if p.endswith("/.well-known/jwks.json")]
    assert len(jwks_calls) == 1
    assert not [p for p in supabase_auth.requests if p.endswith("/user")]  # no get_user
