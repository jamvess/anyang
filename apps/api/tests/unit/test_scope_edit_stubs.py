"""Stub-only checks for ingestion progress, scope chat and the change log. Delete with the stub
fixtures when the real endpoints exist.

Contract checks that the real endpoints must also pass are in test_scope_edit_api_contract.py.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import get_settings
from tests.unit.test_room_api_contract import assert_stream
from tests.unit.test_scope_edit_api_contract import CHAT, MATERIAL_ID, PREP_ID

ENDPOINTS: list[tuple[str, str, Any, int]] = [
    ("get", f"/exam-preps/{PREP_ID}/ingestion", None, 200),
    ("post", f"/materials/{MATERIAL_ID}/retry", None, 202),
    ("delete", f"/materials/{MATERIAL_ID}", None, 204),
    ("post", CHAT, {"text": "การจัดกลุ่มออกเยอะกว่านั้นนะ"}, 200),
    ("get", f"/exam-preps/{PREP_ID}/scope/changes", None, 200),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def scope_topics(client: TestClient) -> dict[str, Any]:
    topics = client.get(f"/exam-preps/{PREP_ID}/scope").json()["topics"]
    return {t["id"]: t for t in topics}


@pytest.mark.parametrize(("method", "url", "body", "status"), ENDPOINTS)
def test_apimd_scope_edit_stubs_send_x_stub_header(
    client: TestClient, method: str, url: str, body: Any, status: int
) -> None:
    response = client.request(method.upper(), url, json=body)

    assert response.status_code == status
    assert response.headers.get("x-stub") == "true"


def test_SM06_chat_text_too_long_sends_x_stub_header(client: TestClient) -> None:
    max_chars = get_settings().ai.guards.max_message_chars

    response = client.post(CHAT, json={"text": "ก" * (max_chars + 1)})

    assert response.status_code == 422
    assert response.headers.get("x-stub") == "true"


def test_CM07_ingestion_stub_shows_every_state_of_the_s11_screen(client: TestClient) -> None:
    """Wireframe S11 and S31: a finished file, a file being read, a failed one, and steps
    still to come."""
    ingestion = client.get(f"/exam-preps/{PREP_ID}/ingestion").json()

    assert ingestion["scope_ready"] is False
    assert {"done", "running", "failed"} <= {f["status"] for f in ingestion["files"]}
    assert {"done", "pending"} <= {s["status"] for s in ingestion["steps"]}


def test_CM07_failed_file_of_the_stub_has_the_id_the_retry_test_uses(client: TestClient) -> None:
    files = client.get(f"/exam-preps/{PREP_ID}/ingestion").json()["files"]

    failed = [f for f in files if f["status"] == "failed"]
    assert [f["material_id"] for f in failed] == [MATERIAL_ID]
    assert failed[0]["error"]


def test_SM07_chat_stub_patches_a_topic_of_the_scope_fixture(client: TestClient) -> None:
    topics = scope_topics(client)

    events = assert_stream(client.post(CHAT, json={"text": "อาจารย์เน้นมาก"}))

    patches = [data for name, data in events if name == "scope_patch"]
    assert patches
    for patch in patches:
        topic = topics[patch["topic_id"]]
        assert any(topic[field] != value for field, value in patch["changes"].items())


def test_SM07_chat_stub_saves_nothing(client: TestClient) -> None:
    before = scope_topics(client)

    client.post(CHAT, json={"text": "อาจารย์เน้นมาก"})

    assert scope_topics(client) == before


def test_SM08_changes_stub_names_topics_of_the_scope_fixture(client: TestClient) -> None:
    topics = scope_topics(client)

    changes = client.get(f"/exam-preps/{PREP_ID}/scope/changes").json()

    assert {c["op"] for c in changes} >= {"set_importance", "exclude"}
    for change in changes:
        assert topics[change["topic_id"]]["name"] == change["topic_name"]
