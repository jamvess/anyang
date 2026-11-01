"""Self-review of PR #98 (specs/features/platform/api-auth.md AC-16, AC-17).

AC-16: Supabase Auth being unreachable is a 503 ``auth_unavailable``, not a 401 that would send
every user back to sign in. AC-17: a client that leaves mid-reply still gets its ``ai_calls`` row
under the user's tenant (the context must outlive ``aclosing`` of the gateway stream).
"""

import json
import threading
import time
import uuid
from contextlib import aclosing
from typing import Annotated, Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import app.ai.gateway as gateway_module
from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.ai.providers.fake import FakeProvider
from app.auth import (
    AuthContext,
    TokenVerifier,
    get_auth,
    get_auth_required,
    get_verifier,
    install_auth_errors,
)
from app.db.ai_calls import AICallLog
from app.services.tutor_turn import reply_events
from app.settings import get_settings

KEY = ec.generate_private_key(ec.SECP256R1())
TENANT = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
USER = uuid.UUID("00000000-0000-4000-8000-0000000000b2")


def make_token() -> str:
    now = int(time.time())
    claims = {
        "sub": str(USER),
        "tenant_id": str(TENANT),
        "role": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(claims, KEY, algorithm="ES256", headers={"kid": "k1"})


def probe(verifier: TokenVerifier) -> TestClient:
    app = FastAPI()
    install_auth_errors(app)

    @app.get("/probe")
    async def handler(auth: Annotated[AuthContext | None, Depends(get_auth)]) -> dict[str, str]:
        return {"ok": "yes"}

    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_auth_required] = lambda: True
    return TestClient(app)


@pytest.mark.parametrize(
    "outage",
    [
        pytest.param(lambda r: httpx.Response(503, json={"msg": "down"}), id="auth-503"),
        pytest.param(lambda r: httpx.Response(429, json={"msg": "slow down"}), id="auth-429"),
        pytest.param(
            lambda r: (_ for _ in ()).throw(httpx.ConnectError("no route", request=r)),
            id="unreachable",
        ),
    ],
)
def test_SA06_auth_outage_is_503_not_401(outage: Any):
    http = httpx.AsyncClient(transport=httpx.MockTransport(outage))
    client = probe(TokenVerifier("https://test.supabase.co", "anon", http_client=http))

    response = client.get("/probe", headers={"Authorization": f"Bearer {make_token()}"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "auth_unavailable"
    assert "www-authenticate" not in response.headers


class FakeWriter:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.inserted = threading.Event()

    def insert(self, row: dict) -> None:
        self.rows.append(row)
        self.inserted.set()


async def test_AI04_client_leaving_mid_reply_still_logs_the_tenant(
    monkeypatch: pytest.MonkeyPatch,
):
    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", no_sleep)
    settings = get_settings()
    fake = FakeProvider({"tutor_reply": ["หนึ่ง สอง สาม สี่ ห้า"]})
    gateway = Gateway(config=settings.ai, prompts_dir=settings.env.prompts_dir, provider=fake)
    call_log = AICallLog(writer=FakeWriter())
    gateway.add_listener(call_log)

    async with aclosing(
        reply_events(gateway, "สวัสดี", AICallContext(tenant_id=TENANT, user_id=USER))
    ) as events:
        async for event, _ in events:
            assert event == "token"
            break  # the client leaves after the first chunk
    await call_log.flush()

    rows = call_log.writer.rows
    assert len(rows) == 1
    assert rows[0]["tenant_id"] == str(TENANT)
    assert rows[0]["user_id"] == str(USER)
    assert rows[0]["status"] == "error"  # the gateway reports a stream stopped early as an error


def test_SA06_outage_log_names_the_error_not_the_token(caplog: pytest.LogCaptureFixture):
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    client = probe(TokenVerifier("https://test.supabase.co", "anon", http_client=http))
    token = make_token()

    client.get("/probe", headers={"Authorization": f"Bearer {token}"})

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "unreachable" in logged.lower()
    assert token.split(".")[2] not in logged
    assert json.dumps(token) not in logged
