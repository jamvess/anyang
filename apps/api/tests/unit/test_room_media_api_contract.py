"""Contract tests for uploads, transcribe and ocr/confirm (specs/system/api.md v1.7
"รูป เสียง และยืนยันลายมือ") and the `ocr_preview` / `verdict` event payloads.

The stubs serve fixture data until the real endpoints exist. These tests check shapes and
request rules, not fixture values, so the real endpoints must pass them unchanged.
Stub-only checks live in test_room_media_stubs.py.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.room import (
    OcrConfirmRequest,
    OcrPreviewEvent,
    Transcript,
    UploadRequest,
    UploadTicket,
    VerdictEvent,
)
from app.settings import get_settings

SESSION_ID = "00000000-0000-4000-8000-000000000002"
MB = 1_048_576  # api.md: 1 MB = 1,048,576 bytes

ERROR_REF = "#/components/schemas/ErrorResponse"

# api.md v1.7: documented errors of each endpoint (401/503 auth errors come from get_auth).
DOCUMENTED_ERRORS = [
    ("/sessions/{id}/uploads", ["404", "422"]),
    ("/sessions/{id}/transcribe", ["404", "422", "503"]),
    ("/sessions/{id}/ocr/confirm", ["404", "409", "422"]),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def openapi(client: TestClient) -> dict[str, Any]:
    return client.get("/openapi.json").json()


def parse_sse(body: str) -> list[tuple[str, Any]]:
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


def upload(**change: Any) -> dict[str, Any]:
    return {
        "kind": "image",
        "content_type": "image/jpeg",
        "file_name": "วิธีทำ.jpg",
        "size_bytes": 2 * MB,
        **change,
    }


# --- endpoints and OpenAPI ---------------------------------------------------


@pytest.mark.parametrize(("path", "statuses"), DOCUMENTED_ERRORS)
def test_apimd_room_media_endpoints_and_errors_in_openapi(
    openapi: dict[str, Any], path: str, statuses: list[str]
) -> None:
    responses = openapi["paths"][path]["post"]["responses"]

    errors = sorted(code for code in responses if code.startswith(("4", "5")))
    assert errors == sorted({*statuses, "401", "503"})
    for status in statuses:
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"] == ERROR_REF


def test_apimd_room_ocr_confirm_declares_event_stream(openapi: dict[str, Any]) -> None:
    operation = openapi["paths"]["/sessions/{id}/ocr/confirm"]["post"]

    assert "text/event-stream" in operation["responses"]["200"]["content"]


def test_apimd_room_media_schemas_have_exact_required_fields(openapi: dict[str, Any]) -> None:
    schemas = openapi["components"]["schemas"]
    expected = {
        "UploadRequest": {"kind", "content_type", "file_name", "size_bytes"},
        "UploadTicket": {"upload_url", "path"},
        "TranscribeRequest": {"audio_path"},
        "Transcript": {"text"},
        "OcrConfirmRequest": {"lines"},
        "OcrLine": {"latex", "confidence"},
        "OcrPreviewEvent": {"lines"},
        "VerdictEvent": {"verdict", "first_wrong_line", "error_type"},
    }
    for name, fields in expected.items():
        assert set(schemas[name]["properties"]) == fields, name
        assert set(schemas[name]["required"]) == fields, name


# --- event payloads ------------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "ok"),
    [
        ({"verdict": "incorrect", "first_wrong_line": 2, "error_type": "sign"}, True),
        ({"verdict": "correct", "first_wrong_line": None, "error_type": None}, True),
        ({"verdict": "incorrect", "first_wrong_line": None, "error_type": "no_answer"}, True),
        ({"verdict": "maybe", "first_wrong_line": None, "error_type": None}, False),
        ({"verdict": "incorrect", "first_wrong_line": 0, "error_type": "sign"}, False),
        ({"verdict": "incorrect", "first_wrong_line": 1, "error_type": "typo"}, False),
    ],
)
def test_AM05_verdict_payload_rules(data: dict[str, Any], ok: bool) -> None:
    if ok:
        VerdictEvent.model_validate(data)
    else:
        with pytest.raises(ValueError):
            VerdictEvent.model_validate(data)


@pytest.mark.parametrize(
    ("lines", "ok"),
    [
        ([{"latex": "x^2 - 5x + 6", "confidence": 0.97}], True),
        ([{"latex": "x", "confidence": 0}, {"latex": "y", "confidence": 1}], True),
        ([], False),  # an unreadable photo is a tutor token, not an empty preview
        ([{"latex": "x", "confidence": 1.2}], False),
        ([{"latex": "x", "confidence": -0.1}], False),
    ],
)
def test_AM02_ocr_preview_payload_rules(lines: list[dict[str, Any]], ok: bool) -> None:
    if ok:
        OcrPreviewEvent.model_validate({"lines": lines})
    else:
        with pytest.raises(ValueError):
            OcrPreviewEvent.model_validate({"lines": lines})


# --- uploads -------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        upload(),
        upload(content_type="image/png"),
        upload(content_type="image/heic"),
        upload(kind="audio", content_type="audio/webm", file_name="เสียง.webm", size_bytes=900_000),
    ],
)
def test_TM06_upload_gives_url_and_path(client: TestClient, body: dict[str, Any]) -> None:
    response = client.post(f"/sessions/{SESSION_ID}/uploads", json=body)

    assert response.status_code == 200
    ticket = UploadTicket.model_validate(response.json())
    assert ticket.upload_url
    assert f"/sessions/{SESSION_ID}/" in ticket.path
    assert body["file_name"] not in ticket.path  # names never build Storage paths


@pytest.mark.parametrize(
    "body",
    [
        upload(content_type="application/pdf"),
        upload(kind="audio", content_type="image/jpeg"),  # type must match kind
        upload(kind="image", content_type="audio/webm"),
    ],
)
def test_TM21_upload_rejects_unsupported_type(client: TestClient, body: dict[str, Any]) -> None:
    response = client.post(f"/sessions/{SESSION_ID}/uploads", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_type"


def test_TM21_image_size_limit_comes_from_config(client: TestClient) -> None:
    limit = get_settings().ai.guards.max_image_mb * MB
    url = f"/sessions/{SESSION_ID}/uploads"

    at_limit = client.post(url, json=upload(size_bytes=limit))
    over = client.post(url, json=upload(size_bytes=limit + 1))

    assert at_limit.status_code == 200
    assert over.status_code == 422
    assert over.json()["error"]["code"] == "file_too_large"


@pytest.mark.parametrize("change", [{"size_bytes": 0}, {"kind": "video"}, {"file_name": ""}])
def test_apimd_room_upload_body_validation(client: TestClient, change: dict[str, Any]) -> None:
    response = client.post(f"/sessions/{SESSION_ID}/uploads", json=upload(**change))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_apimd_room_upload_request_rejects_extra_fields() -> None:
    with pytest.raises(ValueError):
        UploadRequest.model_validate(upload(path="x"))


# --- transcribe ----------------------------------------------------------------


def test_TM07_transcribe_returns_text_only(client: TestClient) -> None:
    body = {"audio_path": f"t1/sessions/{SESSION_ID}/a.webm"}

    response = client.post(f"/sessions/{SESSION_ID}/transcribe", json=body)

    assert response.status_code == 200
    Transcript.model_validate(response.json())


def test_TM07_transcribe_needs_audio_path(client: TestClient) -> None:
    response = client.post(f"/sessions/{SESSION_ID}/transcribe", json={})

    assert response.status_code == 422


# --- ocr/confirm ---------------------------------------------------------------


def test_AM02_ocr_confirm_streams_verdict_before_tutor(client: TestClient) -> None:
    body = {"lines": ["x^2 - 5x + 6", "= (x - 2)(x + 3)", "= x^2 + x - 6"]}

    response = client.post(f"/sessions/{SESSION_ID}/ocr/confirm", json=body)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[-1] == "done"
    assert "verdict" in names
    first_token = names.index("token") if "token" in names else len(names)
    assert names.index("verdict") < first_token  # ai-orchestration §2.4.5
    for name, data in events:
        if name == "verdict":
            VerdictEvent.model_validate(data)


@pytest.mark.parametrize("body", [{}, {"lines": []}, {"lines": "x^2"}])
def test_AM02_ocr_confirm_body_validation(client: TestClient, body: dict[str, Any]) -> None:
    response = client.post(f"/sessions/{SESSION_ID}/ocr/confirm", json=body)

    assert response.status_code == 422


def test_apimd_room_ocr_confirm_request_rejects_extra_fields() -> None:
    with pytest.raises(ValueError):
        OcrConfirmRequest.model_validate({"lines": ["x"], "action": "retake"})
