"""Stub-only checks for session end, chat history, progress card and tts. Delete with the stub
fixtures when the real endpoints exist.

Contract checks that the real endpoints must also pass are in test_room_rest_api_contract.py.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import stubs
from app.main import app
from app.rate_limit import RateLimiter, get_rate_limiter
from app.settings import get_settings

PREP_ID = "00000000-0000-4000-8000-000000000001"
SESSION_ID = "00000000-0000-4000-8000-000000000002"
MESSAGE_ID = "00000000-0000-4000-8000-000000000004"

ENDPOINTS = [
    ("post", f"/sessions/{SESSION_ID}/end"),
    ("get", f"/sessions/{SESSION_ID}/messages"),
    ("get", f"/exam-preps/{PREP_ID}/progress"),
    ("get", f"/messages/{MESSAGE_ID}/tts"),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(("method", "url"), ENDPOINTS)
def test_apimd_room_rest_stubs_send_x_stub_header(
    client: TestClient, method: str, url: str
) -> None:
    response = client.request(method.upper(), url)

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"


def test_TM13_history_stub_is_the_room_fixture(client: TestClient) -> None:
    """The history and GET /sessions/{id} show the same messages."""
    history = client.get(f"/sessions/{SESSION_ID}/messages").json()

    assert history == client.get(f"/sessions/{SESSION_ID}").json()["messages"]


def test_TM15_progress_stub_is_the_session_start_card(client: TestClient) -> None:
    """The card on the home page and the one that opens the session agree."""
    card = dict(stubs.events("session_start"))["progress_card"]

    assert client.get(f"/exam-preps/{PREP_ID}/progress").json() == card


def test_TM21_session_end_is_not_rate_limited(client: TestClient) -> None:
    """api.md v1.9 รอตัดสิน item 2: /end does not count with the room's user messages."""
    limit = get_settings().ai.guards.rate_limit_messages_per_minute
    limiter = RateLimiter(limit=limit)
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    try:
        image = {"image_path": f"t/sessions/{SESSION_ID}/x.jpg"}
        for _ in range(limit):
            client.post(f"/sessions/{SESSION_ID}/messages", json=image)
        assert client.post(f"/sessions/{SESSION_ID}/messages", json=image).status_code == 429

        assert client.post(f"/sessions/{SESSION_ID}/end").status_code == 200
    finally:
        app.dependency_overrides.pop(get_rate_limiter, None)
