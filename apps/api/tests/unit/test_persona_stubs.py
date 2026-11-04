"""Stub-only checks for personas, profiles and deleting. Delete with the stub fixtures when the
real endpoints exist.

Contract checks that the real endpoints must also pass are in test_persona_api_contract.py.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import get_settings
from tests.unit.test_persona_api_contract import (
    EXTRACT,
    PREP_ID,
    buddy_params,
    profile_body,
    tutor_params,
)

ENDPOINTS: list[tuple[str, str, Any, int]] = [
    ("get", "/personas/presets", None, 200),
    ("post", EXTRACT, {"kind": "tutor", "description": "ใจดี"}, 200),
    ("get", "/me/tutor-profile", None, 200),
    ("put", "/me/tutor-profile", {"params": tutor_params(), "description": None}, 200),
    ("get", "/me/buddy-profile", None, 200),
    (
        "put",
        "/me/buddy-profile",
        {"enabled": True, "params": buddy_params(), "description": None},
        200,
    ),
    ("get", "/me/profile", None, 200),
    ("put", "/me/profile", profile_body(), 200),
    ("delete", "/me", None, 204),
    ("delete", f"/exam-preps/{PREP_ID}", None, 204),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(("method", "url", "body", "status"), ENDPOINTS)
def test_apimd_persona_stubs_send_x_stub_header(
    client: TestClient, method: str, url: str, body: Any, status: int
) -> None:
    response = client.request(method.upper(), url, json=body)

    assert response.status_code == status
    assert response.headers.get("x-stub") == "true"


def test_UM05_extract_too_long_sends_x_stub_header(client: TestClient) -> None:
    max_chars = get_settings().ai.guards.max_message_chars

    response = client.post(EXTRACT, json={"kind": "buddy", "description": "ก" * (max_chars + 1)})

    assert response.status_code == 422
    assert response.headers.get("x-stub") == "true"


def test_UM03_UM04_presets_are_the_people_of_wireframe_s04(client: TestClient) -> None:
    presets = client.get("/personas/presets").json()

    assert [p["params"]["name"] for p in presets["tutors"]] == ["พี่กร", "พี่ตาล", "พี่โจ๊ก"]
    assert [p["params"]["name"] for p in presets["buddies"]] == ["มีน", "ต้าร์"]


def test_UM09_stub_profiles_match_the_people_of_the_room_fixture(client: TestClient) -> None:
    room = client.get("/sessions/00000000-0000-4000-8000-000000000002").json()

    assert client.get("/me/tutor-profile").json()["params"]["name"] == room["tutor_name"]
    assert client.get("/me/buddy-profile").json()["params"]["name"] == room["buddy_name"]
    assert client.get("/me/profile").json()["nickname"] == room["user_name"]


def test_UM05_extract_stub_shows_a_refused_part(client: TestClient) -> None:
    """Wireframe S05: the box "ทำให้ไม่ได้: …" (UC-01 E4)."""
    response = client.post(EXTRACT, json={"kind": "tutor", "description": "ใจดี"})

    assert response.json()["refused"]


@pytest.mark.parametrize(
    ("url", "body"),
    [
        ("/me/tutor-profile", {"params": tutor_params(name="พี่แก้ว"), "description": "ใหม่"}),
        ("/me/profile", profile_body(nickname="ชื่อใหม่", auto_read=True)),
    ],
)
def test_UM09_stub_saves_nothing(client: TestClient, url: str, body: dict[str, Any]) -> None:
    before = client.get(url).json()

    client.put(url, json=body)

    assert client.get(url).json() == before


def test_UM10_stub_delete_me_deletes_nothing(client: TestClient) -> None:
    client.delete("/me")

    assert client.get("/me/profile").status_code == 200


def test_CM10_stub_delete_exam_prep_deletes_nothing(client: TestClient) -> None:
    before = client.get("/exam-preps").json()

    client.delete(f"/exam-preps/{PREP_ID}")

    assert [p["id"] for p in client.get("/exam-preps").json()] == [p["id"] for p in before]
