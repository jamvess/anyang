"""OpenAPI documents the error envelope of api.md Conventions, so `pnpm gen:api`
generates the right error types: {"error": {"code", "message"}}, not FastAPI's
default HTTPValidationError.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

ROOM_ENDPOINTS = [
    ("get", "/exam-preps/{id}/sessions/active"),
    ("post", "/exam-preps/{id}/sessions"),
    ("get", "/sessions/{id}"),
    ("post", "/sessions/{id}/messages"),
]

ERROR_REF = "#/components/schemas/ErrorResponse"


@pytest.fixture
def openapi() -> dict:
    with TestClient(app) as client:
        return client.get("/openapi.json").json()


def test_apimd_conventions_openapi_has_no_fastapi_validation_schema(openapi: dict) -> None:
    schemas = openapi["components"]["schemas"]

    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas
    assert set(schemas["ErrorResponse"]["properties"]) == {"error"}


@pytest.mark.parametrize(("method", "path"), ROOM_ENDPOINTS)
@pytest.mark.parametrize("status", ["404", "422"])
def test_apimd_conventions_room_errors_ref_error_response(
    openapi: dict, method: str, path: str, status: str
) -> None:
    response = openapi["paths"][path][method]["responses"][status]

    assert response["content"]["application/json"]["schema"]["$ref"] == ERROR_REF
