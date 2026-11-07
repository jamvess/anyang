"""The size limit of a material (specs/system/api.md v1.13 `POST /exam-preps/{id}/materials`,
"รอตัดสิน (v1.10)" item 2).

The limit is `guards.max_material_mb` from config/ai.yaml, never a literal, or `max_image_mb` for
an image. It is checked before the browser sends the file, against the size the client declares,
so the real limit on Storage needs the bucket too (api.md "รอตัดสิน (v1.10)" item 2).
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import get_settings
from tests.unit.test_exam_prep_api_contract import PREP_ID, upload

BYTES_PER_MB = 1_048_576  # api.md: 1 MB = 1,048,576 bytes
URL = f"/exam-preps/{PREP_ID}/materials"


def limit_bytes() -> int:
    return get_settings().ai.guards.max_material_mb * BYTES_PER_MB


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("delta", [-1, 0])
def test_CM03_material_up_to_the_limit_gets_an_upload_url(client: TestClient, delta: int) -> None:
    response = client.post(URL, json=upload(size_bytes=limit_bytes() + delta))

    assert response.status_code == 200
    assert response.json()["upload_url"]


def test_CM03_material_over_the_limit_is_refused(client: TestClient) -> None:
    response = client.post(URL, json=upload(size_bytes=limit_bytes() + 1))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "file_too_large"


def test_CM03_refused_material_sends_x_stub_header(client: TestClient) -> None:
    """Delete with the stub."""
    response = client.post(URL, json=upload(size_bytes=limit_bytes() + 1))

    assert response.headers.get("x-stub") == "true"


def test_CM03_wrong_type_is_named_before_the_size(client: TestClient) -> None:
    """A file with both problems gets the error the user can act on first: another file type."""
    body = upload(content_type="text/plain", size_bytes=limit_bytes() + 1)

    response = client.post(URL, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_type"


def test_CM03_limit_is_documented_in_openapi(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/exam-preps/{id}/materials"]["post"]

    assert "file_too_large" in operation["responses"]["422"]["description"]


# --- added in self-review (after Jam's test review) ----------------------------------


def test_apimd_config_version_is_not_read_as_a_float() -> None:
    """Unquoted, YAML reads `version: 1.10` as 1.1, the same as the real ai.yaml 1.1."""
    assert isinstance(get_settings().ai.version, str)


def image_limit_bytes() -> int:
    return get_settings().ai.guards.max_image_mb * BYTES_PER_MB


@pytest.mark.parametrize("delta", [-1, 0])
def test_CM03_image_up_to_the_image_limit_gets_an_upload_url(
    client: TestClient, delta: int
) -> None:
    """api.md v1.13: an image reaches vision_extract whole, like a photo in the room."""
    body = upload(content_type="image/jpeg", size_bytes=image_limit_bytes() + delta)

    assert client.post(URL, json=body).status_code == 200


def test_CM03_image_over_the_image_limit_is_refused(client: TestClient) -> None:
    body = upload(content_type="IMAGE/JPEG; x=1", size_bytes=image_limit_bytes() + 1)

    response = client.post(URL, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "file_too_large"


@pytest.mark.parametrize(
    "content_type",
    [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
)
def test_CM03_documents_keep_the_material_limit(client: TestClient, content_type: str) -> None:
    body = upload(content_type=content_type, size_bytes=image_limit_bytes() + 1)

    assert client.post(URL, json=body).status_code == 200
