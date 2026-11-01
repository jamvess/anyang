"""Contract tests for the scope review endpoints (specs/system/api.md v1.6 "หน้าตรวจขอบเขต").

The stubs serve fixture data until the real endpoints exist. These tests check shapes
against the api.md models, not the fixture values, so the real endpoints must pass them
unchanged. Stub-only checks live in test_scope_stubs.py.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.scope import (
    PastQuestion,
    Scope,
    ScopeConfirmed,
    ScopeTopic,
    SourceExcerpt,
    TopicSources,
)

PREP_ID = "00000000-0000-4000-8000-000000000001"
TOPIC_ID = "00000000-0000-4000-8000-000000000003"

SCOPE_ENDPOINTS = [
    ("get", "/exam-preps/{id}/scope"),
    ("get", "/topics/{id}/sources"),
    ("post", "/exam-preps/{id}/scope/confirm"),
]

ERROR_REF = "#/components/schemas/ErrorResponse"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def openapi(client: TestClient) -> dict[str, Any]:
    return client.get("/openapi.json").json()


# --- endpoints and OpenAPI ---------------------------------------------------


def test_apimd_scope_three_endpoints_in_openapi(openapi: dict[str, Any]) -> None:
    paths = openapi["paths"]
    for method, path in SCOPE_ENDPOINTS:
        assert method in paths.get(path, {}), f"{method.upper()} {path} missing"


# api.md v1.6: 409 scope_not_ready on GET /scope; confirm adds scope_already_confirmed and
# scope_empty; sources has no 409.
DOCUMENTED_ERRORS = [
    ("get", "/exam-preps/{id}/scope", ["404", "409", "422"]),
    ("get", "/topics/{id}/sources", ["404", "422"]),
    ("post", "/exam-preps/{id}/scope/confirm", ["404", "409", "422"]),
]


@pytest.mark.parametrize(("method", "path", "statuses"), DOCUMENTED_ERRORS)
def test_apimd_scope_errors_ref_error_response(
    openapi: dict[str, Any], method: str, path: str, statuses: list[str]
) -> None:
    responses = openapi["paths"][path][method]["responses"]

    errors = sorted(code for code in responses if code.startswith(("4", "5")))
    assert errors == sorted([*statuses, "401", "503"])  # 401/503 come from get_auth
    for status in statuses:
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"] == ERROR_REF


def test_apimd_scope_schemas_have_exact_fields(openapi: dict[str, Any]) -> None:
    schemas = openapi["components"]["schemas"]

    assert set(schemas["Scope"]["properties"]) == {
        "prep_name",
        "days_left",
        "status",
        "topics",
        "unmapped_questions",
    }
    assert set(schemas["ScopeTopic"]["properties"]) == {
        "id",
        "order",
        "name",
        "stars",
        "reason",
        "source_label",
        "origin",
    }
    assert set(schemas["PastQuestion"]["properties"]) == {"id", "label", "text", "map_note"}
    assert set(schemas["TopicSources"]["properties"]) == {"excerpts", "questions"}
    assert set(schemas["SourceExcerpt"]["properties"]) == {"material_name", "page", "text"}
    assert set(schemas["ScopeConfirmed"]["properties"]) == {"scope_version_id", "version"}


def test_apimd_scope_every_field_is_required(openapi: dict[str, Any]) -> None:
    # "ทุก field ต้องมี": generated types must not mark any field optional.
    schemas = openapi["components"]["schemas"]
    names = (
        "Scope",
        "ScopeTopic",
        "PastQuestion",
        "TopicSources",
        "SourceExcerpt",
        "ScopeConfirmed",
    )
    for name in names:
        assert set(schemas[name]["required"]) == set(schemas[name]["properties"]), name


def test_apimd_scope_stars_and_order_are_integers(openapi: dict[str, Any]) -> None:
    topic = openapi["components"]["schemas"]["ScopeTopic"]["properties"]

    assert topic["stars"]["type"] == "integer"
    assert topic["order"]["type"] == "integer"


# --- model rules -------------------------------------------------------------

TOPIC = {
    "id": TOPIC_ID,
    "order": 3,
    "name": "ผลต่างกำลังสอง",
    "stars": 3,
    "reason": "ออกทุกชุด",
    "source_label": "ch3 น.5",
    "origin": "doc",
}


@pytest.mark.parametrize(
    ("change", "ok"),
    [
        ({"stars": 0}, True),  # excluded topics are sent with 0 stars
        ({"stars": 3}, True),
        ({"stars": 4}, False),
        ({"stars": -1}, False),
        ({"stars": None}, False),  # never null: not-yet-computed topics are not sent
        ({"order": 1}, True),
        ({"order": 0}, False),  # order_index counts from 1
        ({"origin": "user"}, True),
        ({"origin": "ai"}, False),
        ({"id": "t3"}, False),
        ({"extra": 1}, False),
    ],
)
def test_SM03_scope_topic_rules(change: dict[str, Any], ok: bool) -> None:
    data = {**TOPIC, **change}
    if ok:
        ScopeTopic.model_validate(data)
    else:
        with pytest.raises(ValueError):
            ScopeTopic.model_validate(data)


@pytest.mark.parametrize(
    ("status", "ok"), [("draft", True), ("confirmed", True), ("locked", False)]
)
def test_apimd_scope_status_enum(status: str, ok: bool) -> None:
    data = {
        "prep_name": "Factorization",
        "days_left": 5,
        "status": status,
        "topics": [],
        "unmapped_questions": [],
    }
    if ok:
        Scope.model_validate(data)
    else:
        with pytest.raises(ValueError):
            Scope.model_validate(data)


@pytest.mark.parametrize(("page", "ok"), [(1, True), (0, False)])
def test_SM04_source_page_counts_from_one(page: int, ok: bool) -> None:
    data = {"material_name": "ch3-factorization.pdf", "page": page, "text": "a^2 - b^2"}
    if ok:
        SourceExcerpt.model_validate(data)
    else:
        with pytest.raises(ValueError):
            SourceExcerpt.model_validate(data)


@pytest.mark.parametrize(("version", "ok"), [(1, True), (0, False)])
def test_SM09_confirmed_version_counts_from_one(version: int, ok: bool) -> None:
    data = {"scope_version_id": TOPIC_ID, "version": version}
    if ok:
        ScopeConfirmed.model_validate(data)
    else:
        with pytest.raises(ValueError):
            ScopeConfirmed.model_validate(data)


def test_SM04_map_note_may_be_null() -> None:
    PastQuestion.model_validate(
        {"id": TOPIC_ID, "label": "midterm-2566 ข้อ 3", "text": "$x^2 - 49$", "map_note": None}
    )


# --- responses ---------------------------------------------------------------


def test_apimd_scope_get_scope_validates(client: TestClient) -> None:
    response = client.get(f"/exam-preps/{PREP_ID}/scope")

    assert response.status_code == 200
    scope = Scope.model_validate(response.json())
    assert scope.topics, "fixture scope should have topics"


def test_SM02_scope_topics_keep_api_order(client: TestClient) -> None:
    # SM-02: the web shows topics in the order the API sends, so the API sorts by order.
    topics = client.get(f"/exam-preps/{PREP_ID}/scope").json()["topics"]

    orders = [t["order"] for t in topics]
    assert orders == sorted(orders)


def test_SM04_scope_topic_ids_open_their_sources(client: TestClient) -> None:
    # The page fetches /topics/{id}/sources with the id from /scope (scope-review AC-7).
    topic_id = client.get(f"/exam-preps/{PREP_ID}/scope").json()["topics"][0]["id"]

    response = client.get(f"/topics/{topic_id}/sources")

    assert response.status_code == 200


def test_apimd_scope_get_sources_validates(client: TestClient) -> None:
    response = client.get(f"/topics/{TOPIC_ID}/sources")

    assert response.status_code == 200
    TopicSources.model_validate(response.json())


def test_SM09_scope_confirm_validates(client: TestClient) -> None:
    response = client.post(f"/exam-preps/{PREP_ID}/scope/confirm")

    assert response.status_code == 200
    ScopeConfirmed.model_validate(response.json())


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", "/exam-preps/not-a-uuid/scope"),
        ("get", "/topics/t3/sources"),
        ("post", "/exam-preps/not-a-uuid/scope/confirm"),
    ],
)
def test_apimd_scope_bad_id_is_422_envelope(client: TestClient, method: str, url: str) -> None:
    response = client.request(method.upper(), url)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
