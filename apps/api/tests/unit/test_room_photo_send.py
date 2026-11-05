"""A message with text and a photo (specs/features/tutor/room-photo-send.md AC-1 to AC-4,
AC-boundary-caption · decided in PR #45, api.md "รอตัดสิน (PR #35)" item 1).
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.room import SendMessageRequest
from app.settings import get_settings
from tests.unit.test_room_api_contract import assert_stream

SESSION_ID = "00000000-0000-4000-8000-000000000002"
MESSAGES = f"/sessions/{SESSION_ID}/messages"
IMAGE_PATH = f"t/sessions/{SESSION_ID}/a.jpg"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def names(response) -> list[str]:
    return [name for name, _ in assert_stream(response)]


def test_TM06_text_with_a_photo_gets_the_ocr_preview(client: TestClient) -> None:
    """AC-1"""
    response = client.post(MESSAGES, json={"text": "ไม่แน่ใจบรรทัด 3", "image_path": IMAGE_PATH})

    assert "ocr_preview" in names(response)


def test_TM06_photo_alone_gets_the_ocr_preview(client: TestClient) -> None:
    """AC-2"""
    assert "ocr_preview" in names(client.post(MESSAGES, json={"image_path": IMAGE_PATH}))


def test_TM06_text_alone_gets_no_ocr_preview(client: TestClient) -> None:
    """AC-2"""
    assert "ocr_preview" not in names(client.post(MESSAGES, json={"text": "(x-7)(x+7)"}))


@pytest.mark.parametrize("body", [{}, {"text": None, "image_path": None}])
def test_TM06_message_needs_text_or_a_photo(client: TestClient, body: dict) -> None:
    """AC-3"""
    response = client.post(MESSAGES, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_TM06_blank_text_with_a_photo_is_refused(client: TestClient) -> None:
    """AC-4: the composer turns blank text into null, so a blank caption is a client bug."""
    response = client.post(MESSAGES, json={"text": "   ", "image_path": IMAGE_PATH})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_TM06_request_model_takes_both_fields() -> None:
    body = SendMessageRequest.model_validate({"text": "ข้อ 2 ครับ", "image_path": IMAGE_PATH})

    assert body.text == "ข้อ 2 ครับ"
    assert body.image_path == IMAGE_PATH


def test_TM21_caption_at_the_limit_is_accepted(client: TestClient) -> None:
    """AC-boundary-caption"""
    max_chars = get_settings().ai.guards.max_message_chars

    response = client.post(MESSAGES, json={"text": "ก" * max_chars, "image_path": IMAGE_PATH})

    assert "ocr_preview" in names(response)


def test_TM21_caption_over_the_limit_is_refused(client: TestClient) -> None:
    """AC-boundary-caption"""
    max_chars = get_settings().ai.guards.max_message_chars

    response = client.post(MESSAGES, json={"text": "ก" * (max_chars + 1), "image_path": IMAGE_PATH})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "message_too_long"
