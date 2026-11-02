"""Stub-only checks for exam preps and materials. Delete with the stub fixtures when the real
endpoints exist.

Contract checks that the real endpoints must also pass are in test_exam_prep_api_contract.py.
"""

from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.unit.test_exam_prep_api_contract import MATERIAL_ID, PREP_ID, today, upload

ENDPOINTS: list[tuple[str, str, Any, int]] = [
    ("post", "/exam-preps", {"title": "x", "exam_date": None}, 201),
    ("get", "/exam-preps", None, 200),
    ("post", f"/exam-preps/{PREP_ID}/materials", upload(), 200),
    ("post", f"/materials/{MATERIAL_ID}/uploaded", {}, 202),
    ("get", f"/exam-preps/{PREP_ID}/materials", None, 200),
    (
        "post",
        f"/exam-preps/{PREP_ID}/materials/confirm",
        {"materials": [{"id": MATERIAL_ID, "kind": "sheet"}]},
        202,
    ),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(("method", "url", "body", "status"), ENDPOINTS)
def test_apimd_exam_prep_stubs_send_x_stub_header(
    client: TestClient, method: str, url: str, body: Any, status: int
) -> None:
    if body and "exam_date" in body:
        body = {**body, "exam_date": str(today() + timedelta(days=3))}

    response = client.request(method.upper(), url, json=body)

    assert response.status_code == status
    assert response.headers.get("x-stub") == "true"


def test_CM07_materials_stub_shows_every_status_the_s10_and_s11_screens_handle(
    client: TestClient,
) -> None:
    """The fixture has a file still being classified, one classified and one that failed."""
    statuses = {m["status"] for m in client.get(f"/exam-preps/{PREP_ID}/materials").json()}

    assert {"uploaded", "classified", "failed"} <= statuses


def test_PM04_list_stub_has_a_prep_in_each_stage(client: TestClient) -> None:
    stages = {p["stage"] for p in client.get("/exam-preps").json()}

    assert stages == {"materials", "processing", "scope", "tutoring"}


def test_CM03_refused_upload_sends_x_stub_header(client: TestClient) -> None:
    response = client.post(
        f"/exam-preps/{PREP_ID}/materials", json=upload(content_type="text/plain")
    )

    assert response.status_code == 422
    assert response.headers.get("x-stub") == "true"
