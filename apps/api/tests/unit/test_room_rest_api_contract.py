"""Contract tests for session end, chat history, progress card and tts (specs/system/api.md v1.9
"จบ session ประวัติแชท progress card และเสียงอ่าน").

The stubs serve fixture data until the real endpoints exist. These tests check shapes and
request rules, not fixture values, so the real endpoints must pass them unchanged.
Stub-only checks live in test_room_rest_stubs.py.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import app
from app.models.room import EVENT_MODELS, Message, ProgressCardEvent, SessionEndEvent, TtsAudio
from tests.unit.test_room_api_contract import assert_stream

PREP_ID = "00000000-0000-4000-8000-000000000001"
SESSION_ID = "00000000-0000-4000-8000-000000000002"
MESSAGE_ID = "00000000-0000-4000-8000-000000000004"

ERROR_REF = "#/components/schemas/ErrorResponse"

# api.md v1.9: documented errors of each endpoint (401/503 auth errors come from get_auth).
DOCUMENTED_ERRORS = [
    ("post", "/sessions/{id}/end", ["404", "409", "422"]),
    ("get", "/sessions/{id}/messages", ["404", "422"]),
    ("get", "/exam-preps/{id}/progress", ["404", "409", "422"]),
    ("get", "/messages/{id}/tts", ["404", "409", "422", "503"]),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def openapi(client: TestClient) -> dict[str, Any]:
    return client.get("/openapi.json").json()


# --- endpoints and OpenAPI ---------------------------------------------------


@pytest.mark.parametrize(("method", "path", "statuses"), DOCUMENTED_ERRORS)
def test_apimd_room_rest_endpoints_and_errors_in_openapi(
    openapi: dict[str, Any], method: str, path: str, statuses: list[str]
) -> None:
    responses = openapi["paths"][path][method]["responses"]

    errors = sorted(code for code in responses if code.startswith(("4", "5")))
    assert errors == sorted({*statuses, "401", "503"})
    for status in statuses:
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"] == ERROR_REF


def test_apimd_room_end_declares_event_stream(openapi: dict[str, Any]) -> None:
    operation = openapi["paths"]["/sessions/{id}/end"]["post"]

    assert "text/event-stream" in operation["responses"]["200"]["content"]


def test_apimd_room_rest_schemas_have_exact_required_fields(openapi: dict[str, Any]) -> None:
    schemas = openapi["components"]["schemas"]
    expected = {"SessionEndEvent": {"summary_lines"}, "TtsAudio": {"audio_url"}}
    for name, fields in expected.items():
        assert set(schemas[name]["properties"]) == fields, name
        assert set(schemas[name]["required"]) == fields, name


def test_TM15_progress_response_is_the_progress_card_event(openapi: dict[str, Any]) -> None:
    """api.md v1.9: the same shape as the progress_card event, so the web reuses one type."""
    response = openapi["paths"]["/exam-preps/{id}/progress"]["get"]["responses"]["200"]

    schema = response["content"]["application/json"]["schema"]
    assert schema["$ref"] == "#/components/schemas/ProgressCardEvent"


def test_TM13_messages_response_is_a_list_of_message(openapi: dict[str, Any]) -> None:
    response = openapi["paths"]["/sessions/{id}/messages"]["get"]["responses"]["200"]

    schema = response["content"]["application/json"]["schema"]
    assert schema["type"] == "array"
    assert schema["items"]["$ref"] == "#/components/schemas/Message"


# --- payload rules ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("lines", "ok"),
    [
        (["วันนี้ผ่านผลต่างกำลังสอง"], True),
        (["บรรทัด 1", "บรรทัด 2"], True),
        ([], False),
        (["1", "2", "3"], False),  # api.md: at most 2 lines
    ],
)
def test_PM05_session_end_summary_has_one_or_two_lines(lines: list[str], ok: bool) -> None:
    if ok:
        SessionEndEvent.model_validate({"summary_lines": lines})
    else:
        with pytest.raises(ValueError):
            SessionEndEvent.model_validate({"summary_lines": lines})


def test_PM05_session_end_event_is_an_sse_event_model() -> None:
    assert EVENT_MODELS["session_end"] is SessionEndEvent


# --- responses ---------------------------------------------------------------------


def test_PM05_end_streams_session_end_then_done(client: TestClient) -> None:
    events = assert_stream(client.post(f"/sessions/{SESSION_ID}/end"))

    names = [name for name, _ in events]
    assert names == ["session_end", "done"]
    SessionEndEvent.model_validate(events[0][1])


def test_TM13_messages_are_oldest_first(client: TestClient) -> None:
    response = client.get(f"/sessions/{SESSION_ID}/messages")

    assert response.status_code == 200
    messages = TypeAdapter(list[Message]).validate_python(response.json())
    assert messages, "fixture history should have messages"
    times = [m.created_at for m in messages]
    assert times == sorted(times)
    assert "extracted_text" not in response.text and "intent" not in response.text


@pytest.mark.parametrize("path", [f"/exam-preps/{PREP_ID}/progress"])
def test_TM11_progress_validates(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    ProgressCardEvent.model_validate(response.json())


def test_TM09_tts_gives_an_audio_url(client: TestClient) -> None:
    response = client.get(f"/messages/{MESSAGE_ID}/tts")

    assert response.status_code == 200
    assert TtsAudio.model_validate(response.json()).audio_url


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("post", "/sessions/not-a-uuid/end"),
        ("get", "/sessions/not-a-uuid/messages"),
        ("get", "/exam-preps/not-a-uuid/progress"),
        ("get", "/messages/m1/tts"),
    ],
)
def test_apimd_room_rest_bad_id_is_422_envelope(client: TestClient, method: str, url: str) -> None:
    response = client.request(method.upper(), url)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
