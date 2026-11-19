"""Guard: unit tests cannot reach the network, Supabase included (apps/api/CLAUDE.md "unit/ ...
no network" · test-strategy.md §2). The autouse fixture `network_attempts` in
tests/unit/conftest.py blocks and records; these tests prove it does."""

import re
import socket
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from supabase import create_client

from app.auth import AuthContext, get_auth
from app.main import app
from tests.unit.network_guard import NetworkBlockedError, fail_if_attempted

FAKE_SUPABASE = "https://guard-test.supabase.co"


def test_test_strategy_unit_tests_cannot_open_a_socket_to_supabase(network_attempts):
    with pytest.raises(NetworkBlockedError):
        socket.create_connection(("guard-test.supabase.co", 443), timeout=1)

    assert network_attempts == ["guard-test.supabase.co"]
    network_attempts.clear()


def test_test_strategy_unit_tests_cannot_query_supabase(network_attempts):
    client = create_client(FAKE_SUPABASE, "anon-key")

    with pytest.raises(httpx.ConnectError):  # httpx wraps the refused connect
        client.table("tutor_sessions").select("id").execute()

    assert "guard-test.supabase.co" in network_attempts
    network_attempts.clear()


def test_test_strategy_a_room_request_with_a_token_and_no_fake_repository_is_caught(
    network_attempts, monkeypatch: pytest.MonkeyPatch
):
    """The case that slipped through on 2026-11-11: a token sends the room to the DB; the
    repository turns the refused connect into 503, so only the recorded attempt shows it."""
    import app.auth as auth_module

    env = auth_module.get_settings().env
    monkeypatch.setattr(env, "supabase_url", FAKE_SUPABASE)
    monkeypatch.setattr(env, "supabase_anon_key", type(env.supabase_anon_key)("anon-key"))
    user = AuthContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), token="t")
    app.dependency_overrides[get_auth] = lambda: user
    try:
        with TestClient(app) as client:
            response = client.get(f"/sessions/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.pop(get_auth, None)

    assert response.status_code == 503
    assert "guard-test.supabase.co" in network_attempts
    network_attempts.clear()


def test_test_strategy_a_swallowed_attempt_still_fails_the_test():
    with pytest.raises(pytest.fail.Exception, match=re.escape("guard-test.supabase.co")):
        fail_if_attempted(["guard-test.supabase.co"])


def test_test_strategy_loopback_stays_open():
    """asyncio and the Windows socketpair fallback connect to 127.0.0.1 in process."""
    left, right = socket.socketpair()
    left.close()
    right.close()
