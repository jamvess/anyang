"""Stub-only checks for the tutor room endpoints. Delete this file in P4-lite.

Contract checks that the real endpoints must also pass are in test_room_api_contract.py.
A text message is no longer a stub (specs/features/tutor/tutor-reply-stream.md, §10 item 5,
Jam 2026-10-31); an image message still is.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app

PREP_ID = "00000000-0000-4000-8000-000000000001"
SESSION_ID = "00000000-0000-4000-8000-000000000002"

ROOM_ENDPOINTS = [
    ("get", f"/exam-preps/{PREP_ID}/sessions/active", None),
    ("post", f"/exam-preps/{PREP_ID}/sessions", None),
    ("get", f"/sessions/{SESSION_ID}", None),
    ("post", f"/sessions/{SESSION_ID}/messages", {"image_path": "sessions/s1/วิธีทำ.jpg"}),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(("method", "url", "body"), ROOM_ENDPOINTS)
def test_apimd_room_stubs_send_x_stub_header(
    client: TestClient, method: str, url: str, body: dict[str, Any] | None
) -> None:
    response = client.request(method.upper(), url, json=body)

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"
