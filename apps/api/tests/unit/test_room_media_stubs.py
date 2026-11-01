"""Stub-only checks for uploads, transcribe, ocr/confirm and the image message.
Delete with the stub fixtures when the real endpoints exist.

Contract checks that the real endpoints must also pass are in test_room_media_api_contract.py.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.room import OcrPreviewEvent

SESSION_ID = "00000000-0000-4000-8000-000000000002"

UPLOAD = {"kind": "image", "content_type": "image/jpeg", "file_name": "a.jpg", "size_bytes": 10}
LINES = ["x^2 - 5x + 6", "= (x - 2)(x + 3)", "= x^2 + x - 6"]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def _events(body: str) -> list[tuple[str, Any]]:
    events = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        name, data = "message", None
        for line in block.split("\n"):
            field, _, value = line.partition(": ")
            if field == "event":
                name = value
            elif field == "data":
                data = json.loads(value)
        if data is not None:
            events.append((name, data))
    return events


@pytest.mark.parametrize(
    ("url", "body"),
    [
        (f"/sessions/{SESSION_ID}/uploads", UPLOAD),
        (f"/sessions/{SESSION_ID}/transcribe", {"audio_path": "t/sessions/s/a.webm"}),
        (f"/sessions/{SESSION_ID}/ocr/confirm", {"lines": LINES}),
    ],
)
def test_apimd_room_media_stubs_send_x_stub_header(
    client: TestClient, url: str, body: dict[str, Any]
) -> None:
    response = client.post(url, json=body)

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"


def test_AM02_image_message_stub_streams_ocr_preview(client: TestClient) -> None:
    # Lets May try the OCR confirm card over HTTP (ocr-confirm-card.md AC-1, AC-7).
    body = {"image_path": f"t/sessions/{SESSION_ID}/x.jpg"}

    response = client.post(f"/sessions/{SESSION_ID}/messages", json=body)

    events = _events(response.text)
    names = [name for name, _ in events]
    assert names[0] == "token" and "ocr_preview" in names and names[-1] == "done"
    preview = dict(events)["ocr_preview"]
    assert len(OcrPreviewEvent.model_validate(preview).lines) == len(LINES)


def test_AM02_ocr_confirm_stub_checks_line_count_against_its_preview(client: TestClient) -> None:
    response = client.post(f"/sessions/{SESSION_ID}/ocr/confirm", json={"lines": LINES[:2]})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ocr_lines_mismatch"
