"""Contract tests for the tutor room (specs/system/api.md v1.2 "ห้องติว", "SSE events").

The stubs serve fixture data until P4-lite. These tests check shapes against the
api.md models, not the fixture values, so the real endpoints must pass them
unchanged. Stub-only checks live in test_room_stubs.py.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import app
from app.models.room import (
    ActiveSession,
    BuddyEvent,
    DoneEvent,
    ErrorEvent,
    Message,
    ProblemEvent,
    ProgressCardEvent,
    Room,
    SessionEvent,
    TokenEvent,
)
from app.settings import get_settings

PREP_ID = "00000000-0000-4000-8000-000000000001"
SESSION_ID = "00000000-0000-4000-8000-000000000002"

ROOM_ENDPOINTS = [
    ("get", "/exam-preps/{id}/sessions/active"),
    ("post", "/exam-preps/{id}/sessions"),
    ("get", "/sessions/{id}"),
    ("post", "/sessions/{id}/messages"),
]

# api.md "SSE events"
KNOWN_EVENTS = {
    "session",
    "token",
    "scope_patch",
    "progress_card",
    "problem",
    "ocr_preview",
    "verdict",
    "buddy",
    "session_end",
    "done",
    "error",
}

PAYLOAD_MODELS: dict[str, Any] = {
    "session": SessionEvent,
    "token": TokenEvent,
    "progress_card": ProgressCardEvent,
    "problem": ProblemEvent,
    "buddy": BuddyEvent,
    "done": DoneEvent,
    "error": ErrorEvent,
}

STREAM_ENDPOINTS = ["/exam-preps/{id}/sessions", "/sessions/{id}/messages"]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def parse_sse(body: str) -> list[tuple[str, Any]]:
    """Minimal text/event-stream parser: (event, data) pairs, comments skipped."""
    events = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        name, data = "message", []
        for line in block.split("\n"):
            if not line or line.startswith(":"):
                continue
            field, _, value = line.partition(":")
            value = value.removeprefix(" ")
            if field == "event":
                name = value
            elif field == "data":
                data.append(value)
        if data:
            events.append((name, json.loads("\n".join(data))))
    return events


def assert_stream(response: Any) -> list[tuple[str, Any]]:
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert set(names) <= KNOWN_EVENTS, names
    assert names[-1] == "done"
    assert names.count("done") == 1
    for name, data in events:
        if name in PAYLOAD_MODELS:
            PAYLOAD_MODELS[name].model_validate(data)
    return events


# --- endpoints and OpenAPI ---------------------------------------------------


def test_apimd_room_four_endpoints_in_openapi(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    for method, path in ROOM_ENDPOINTS:
        assert method in paths.get(path, {}), f"{method.upper()} {path} missing"


def test_apimd_sse_event_models_in_openapi(client: TestClient) -> None:
    # pnpm gen:api only generates types for schemas listed here (apps/web CLAUDE.md).
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    for model in PAYLOAD_MODELS.values():
        assert model.__name__ in schemas, f"{model.__name__} missing from components.schemas"


@pytest.mark.parametrize("path", STREAM_ENDPOINTS)
def test_apimd_sse_streams_declare_event_stream_in_openapi(client: TestClient, path: str) -> None:
    operation = client.get("/openapi.json").json()["paths"][path]["post"]
    assert "text/event-stream" in operation["responses"]["200"]["content"]


def test_apimd_room_schemas_have_exact_fields(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    assert set(schemas["Room"]["properties"]) == {
        "session_id",
        "prep_name",
        "days_left",
        "user_name",
        "tutor_name",
        "buddy_name",
        "limits",
        "messages",
    }
    assert set(schemas["Message"]["properties"]) == {
        "id",
        "role",
        "content",
        "card",
        "input_mode",
        "attachment_path",
        "attachment_name",
        "created_at",
    }
    assert set(schemas["Limits"]["properties"]) == {"max_message_chars", "max_image_mb"}


def test_apimd_room_limits_are_integers(client: TestClient) -> None:
    limits = client.get("/openapi.json").json()["components"]["schemas"]["Limits"]["properties"]

    assert limits["max_message_chars"]["type"] == "integer"
    assert limits["max_image_mb"]["type"] == "integer"


@pytest.mark.parametrize(
    ("data", "ok"),
    [
        ({"role": "tutor"}, True),
        ({"role": "card"}, True),
        ({"role": "system"}, True),
        ({"role": "assistant"}, False),
        ({"role": "user", "input_mode": "image"}, True),
        ({"role": "user", "input_mode": "photo"}, False),
    ],
)
def test_apimd_room_message_enums(data: dict[str, str], ok: bool) -> None:
    message = {
        "id": "m1",
        "content": None,
        "card": None,
        "input_mode": None,
        "attachment_path": None,
        "attachment_name": None,
        "created_at": "2026-08-28T13:30:00Z",
        **data,
    }
    if ok:
        Message.model_validate(message)
    else:
        with pytest.raises(ValueError):
            Message.model_validate(message)


# --- responses ---------------------------------------------------------------


def test_apimd_room_active_session_validates(client: TestClient) -> None:
    response = client.get(f"/exam-preps/{PREP_ID}/sessions/active")

    assert response.status_code == 200
    ActiveSession.model_validate(response.json())


def test_apimd_room_get_session_returns_room(client: TestClient) -> None:
    response = client.get(f"/sessions/{SESSION_ID}")

    assert response.status_code == 200
    room = Room.model_validate(response.json())
    assert str(room.session_id) == SESSION_ID
    assert room.messages, "fixture room should have messages"
    assert "extracted_text" not in response.text
    assert "intent" not in response.text


def test_apimd_room_limits_come_from_config_guards(client: TestClient) -> None:
    guards = get_settings().ai.guards

    room = client.get(f"/sessions/{SESSION_ID}").json()

    assert room["limits"] == {
        "max_message_chars": guards.max_message_chars,
        "max_image_mb": guards.max_image_mb,
    }


def test_apimd_room_messages_are_oldest_first(client: TestClient) -> None:
    messages = TypeAdapter(list[Message]).validate_python(
        client.get(f"/sessions/{SESSION_ID}").json()["messages"]
    )

    times = [m.created_at for m in messages]
    assert times == sorted(times)


# --- SSE streams ---------------------------------------------------------------


def test_apimd_sse_create_session_starts_with_session_event(client: TestClient) -> None:
    events = assert_stream(client.post(f"/exam-preps/{PREP_ID}/sessions"))

    name, data = events[0]
    assert name == "session"
    SessionEvent.model_validate(data)


def test_apimd_sse_create_session_order(client: TestClient) -> None:
    events = assert_stream(client.post(f"/exam-preps/{PREP_ID}/sessions"))

    # api.md: session → progress_card → token (opening) → problem → done
    names = [name for name, _ in events]
    expected = ["session", "progress_card", "token", "problem", "done"]
    first_seen = [names.index(n) for n in expected]
    assert first_seen == sorted(first_seen), names


@pytest.mark.parametrize("body", [{"text": "(x-7)(x+7)"}, {"image_path": "sessions/s1/วิธีทำ.jpg"}])
def test_apimd_sse_send_message_streams_reply(client: TestClient, body: dict[str, str]) -> None:
    events = assert_stream(client.post(f"/sessions/{SESSION_ID}/messages", json=body))

    assert any(name == "token" for name, _ in events)


# --- request validation and error envelope (api.md Conventions) ----------------


def assert_error_envelope(response: Any, status: int) -> None:
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"error"}
    assert isinstance(body["error"]["code"], str) and body["error"]["code"]
    assert isinstance(body["error"]["message"], str)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"text": None, "image_path": None},
        # api.md รอตัดสิน ข้อ 1 (Jam) — change with the spec if Jam allows both.
        # Text with an image waits for Jam (api.md "รอตัดสิน" item 1), so the old body applies.
        {"text": "ไม่แน่ใจบรรทัด 3", "image_path": "sessions/s1/วิธีทำ.jpg"},
    ],
)
def test_apimd_room_send_message_needs_exactly_one_of_text_or_image(
    client: TestClient, body: dict
) -> None:
    response = client.post(f"/sessions/{SESSION_ID}/messages", json=body)

    assert_error_envelope(response, 422)


def test_apimd_conventions_invalid_id_uses_error_envelope(client: TestClient) -> None:
    assert_error_envelope(client.get("/sessions/not-a-uuid"), 422)


def test_apimd_conventions_unknown_route_uses_error_envelope(client: TestClient) -> None:
    assert_error_envelope(client.get("/no-such-route"), 404)
