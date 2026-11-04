"""Contract tests for ingestion progress, scope chat and the change log (specs/system/api.md v1.11
"ความคืบหน้า แชทแก้ขอบเขต และ change log"), and for scope/chat in the rate limit
(specs/features/ai/gateway-guards.md AC-11, AC-26).

The stubs serve fixture data until the real endpoints exist. These tests check shapes and
request rules, not fixture values, so the real endpoints must pass them unchanged.
Stub-only checks live in test_scope_edit_stubs.py.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import app
from app.models.exam_prep import Material
from app.models.room import EVENT_MODELS
from app.models.scope import (
    Ingestion,
    IngestionFile,
    IngestionStep,
    ScopeChange,
    ScopeChatRequest,
    ScopePatchEvent,
)
from app.rate_limit import RateLimiter, get_rate_limiter
from app.settings import get_settings
from tests.unit.test_room_api_contract import assert_stream

PREP_ID = "00000000-0000-4000-8000-000000000001"
SESSION_ID = "00000000-0000-4000-8000-000000000002"
TOPIC_ID = "00000000-0000-4000-8000-000000000003"
MATERIAL_ID = "00000000-0000-4000-8000-000000000008"

CHAT = f"/exam-preps/{PREP_ID}/scope/chat"
MESSAGES = f"/sessions/{SESSION_ID}/messages"
IMAGE = {"image_path": f"t/sessions/{SESSION_ID}/x.jpg"}  # stub reply, no AI call

ERROR_REF = "#/components/schemas/ErrorResponse"

# api.md v1.11: documented errors of each endpoint (401/503 auth errors come from get_auth).
DOCUMENTED_ERRORS = [
    ("get", "/exam-preps/{id}/ingestion", ["404", "422"]),
    ("post", "/materials/{id}/retry", ["404", "409", "422"]),
    ("delete", "/materials/{id}", ["404", "409", "422"]),
    ("post", "/exam-preps/{id}/scope/chat", ["404", "409", "422", "429"]),
    ("get", "/exam-preps/{id}/scope/changes", ["404", "409", "422"]),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def openapi(client: TestClient) -> dict[str, Any]:
    return client.get("/openapi.json").json()


def chat(client: TestClient, text: str = "การจัดกลุ่มออกเยอะกว่านั้นนะ") -> Any:
    return client.post(CHAT, json={"text": text})


# --- endpoints and OpenAPI ---------------------------------------------------


@pytest.mark.parametrize(("method", "path", "statuses"), DOCUMENTED_ERRORS)
def test_apimd_scope_edit_endpoints_and_errors_in_openapi(
    openapi: dict[str, Any], method: str, path: str, statuses: list[str]
) -> None:
    responses = openapi["paths"][path][method]["responses"]

    errors = sorted(code for code in responses if code.startswith(("4", "5")))
    assert errors == sorted({*statuses, "401", "503"})
    for status in statuses:
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"] == ERROR_REF


def test_apimd_scope_edit_schemas_have_exact_required_fields(openapi: dict[str, Any]) -> None:
    schemas = openapi["components"]["schemas"]
    expected = {
        "Ingestion": {"scope_ready", "files", "steps"},
        "IngestionFile": {"material_id", "file_name", "status", "detail", "error"},
        "IngestionStep": {"label", "status"},
        "ScopePatchEvent": {"topic_id", "changes"},
        "ScopeChange": {
            "id",
            "topic_id",
            "topic_name",
            "op",
            "before",
            "after",
            "reason",
            "actor",
            "created_at",
        },
    }
    for name, fields in expected.items():
        assert set(schemas[name]["properties"]) == fields, name
        assert set(schemas[name]["required"]) == fields, name


def test_SM07_scope_patch_changes_are_the_fields_of_a_scope_topic(openapi: dict[str, Any]) -> None:
    """api.md v1.11: every ScopeTopic field but id, and none of them required."""
    schemas = openapi["components"]["schemas"]
    changes = schemas["ScopePatchChanges"]

    assert set(changes["properties"]) == set(schemas["ScopeTopic"]["properties"]) - {"id"}
    assert "required" not in changes


def test_SM06_scope_chat_declares_its_events(openapi: dict[str, Any]) -> None:
    operation = openapi["paths"]["/exam-preps/{id}/scope/chat"]["post"]

    schema = operation["responses"]["200"]["content"]["text/event-stream"]["schema"]
    refs = {item["$ref"].rsplit("/", 1)[1] for item in schema["oneOf"]}
    assert refs == {"TokenEvent", "ScopePatchEvent", "DoneEvent", "ErrorEvent"}


def test_SM07_scope_patch_is_an_sse_event_model() -> None:
    assert EVENT_MODELS["scope_patch"] is ScopePatchEvent


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [("post", "/materials/{id}/retry", "202"), ("delete", "/materials/{id}", "204")],
)
def test_CM07_failed_file_endpoints_declare_their_status(
    openapi: dict[str, Any], method: str, path: str, status: str
) -> None:
    """api.md Conventions: long-running jobs answer 202 Accepted; a delete has no body."""
    assert status in openapi["paths"][path][method]["responses"]


# --- model rules -------------------------------------------------------------


@pytest.mark.parametrize(
    ("body", "ok"),
    [
        ({"text": "กำลังสามไม่ต้องเรียนนะ"}, True),
        ({"text": ""}, False),
        ({"text": "   "}, False),
        ({}, False),
        ({"text": "x", "history": []}, False),
    ],
)
def test_SM06_chat_request_rules(body: dict[str, Any], ok: bool) -> None:
    if ok:
        ScopeChatRequest.model_validate(body)
    else:
        with pytest.raises(ValueError):
            ScopeChatRequest.model_validate(body)


@pytest.mark.parametrize(
    ("changes", "ok"),
    [
        ({"stars": 3, "reason": "คุณบอกว่าอาจารย์เน้นมาก"}, True),
        ({"stars": 0, "reason": "คุณบอกว่าไม่ต้องเรียน"}, True),  # 0 stars = excluded
        ({"name": "แยกตัวประกอบ"}, True),
        ({"order": 2}, True),
        (
            {
                "order": 9,
                "name": "กำลังสาม",
                "stars": 1,
                "reason": "เพิ่มเอง",
                "source_label": "นอกเอกสาร",
                "origin": "user",
            },
            True,
        ),
        ({}, False),  # at least one field changes
        ({"id": TOPIC_ID}, False),  # the card's id is topic_id
        ({"stars": 4}, False),
        ({"stars": -1}, False),
        ({"order": 0}, False),
        ({"origin": "ai"}, False),
    ],
)
def test_SM07_scope_patch_changes_rules(changes: dict[str, Any], ok: bool) -> None:
    data = {"topic_id": TOPIC_ID, "changes": changes}
    if ok:
        ScopePatchEvent.model_validate(data)
    else:
        with pytest.raises(ValueError):
            ScopePatchEvent.model_validate(data)


def test_SM07_scope_patch_topic_id_is_a_uuid() -> None:
    with pytest.raises(ValueError):
        ScopePatchEvent.model_validate({"topic_id": "t3", "changes": {"order": 1}})


@pytest.mark.parametrize("status", ["queued", "running", "done", "failed"])
def test_CM07_file_status_values(status: str) -> None:
    data = {
        "material_id": MATERIAL_ID,
        "file_name": "whiteboard.heic",
        "status": status,
        "detail": None,
        "error": None,
    }
    assert IngestionFile.model_validate(data).status == status


@pytest.mark.parametrize(
    ("model", "data"),
    [
        (
            IngestionFile,
            {
                "material_id": MATERIAL_ID,
                "file_name": "a.pdf",
                "status": "ingesting",  # a value of materials.status, not of ingestion_jobs.status
                "detail": None,
                "error": None,
            },
        ),
        (IngestionStep, {"label": "หาหัวข้อและลำดับการเรียน", "status": "skipped"}),
        (IngestionStep, {"label": "หาหัวข้อและลำดับการเรียน", "status": "queued"}),
    ],
)
def test_CM07_ingestion_rejects_other_status_values(model: Any, data: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        model.model_validate(data)


@pytest.mark.parametrize(
    ("change", "ok"),
    [
        ({}, True),
        ({"op": "add_topic", "before": None, "after": {"name": "กำลังสาม", "stars": 1}}, True),
        ({"reason": None, "actor": "ai"}, True),
        ({"op": "delete"}, False),  # not in the scope_changes.op check
        ({"actor": "bot"}, False),  # not in the scope_changes.actor check
        ({"topic_id": None}, False),  # rows without a topic are not sent
    ],
)
def test_SM08_change_row_rules(change: dict[str, Any], ok: bool) -> None:
    data = {
        "id": "00000000-0000-4000-8000-000000000021",
        "topic_id": TOPIC_ID,
        "topic_name": "การจัดกลุ่ม",
        "op": "set_importance",
        "before": {"stars": 2},
        "after": {"stars": 3},
        "reason": "คุณบอกว่าอาจารย์เน้นมาก",
        "actor": "user",
        "created_at": "2026-11-04T13:27:00+00:00",
        **change,
    }
    if ok:
        ScopeChange.model_validate(data)
    else:
        with pytest.raises(ValueError):
            ScopeChange.model_validate(data)


# --- ingestion ---------------------------------------------------------------------


def test_CM07_ingestion_validates(client: TestClient) -> None:
    response = client.get(f"/exam-preps/{PREP_ID}/ingestion")

    assert response.status_code == 200
    ingestion = Ingestion.model_validate(response.json())
    assert ingestion.files, "fixture should have files"
    assert ingestion.steps, "fixture should have steps"


def test_CM07_retry_answers_202_with_a_file_no_longer_failed(client: TestClient) -> None:
    response = client.post(f"/materials/{MATERIAL_ID}/retry")

    assert response.status_code == 202
    material = Material.model_validate(response.json())
    assert str(material.id) == MATERIAL_ID
    assert material.status != "failed"
    assert material.error is None


def test_CM10_delete_material_answers_204_without_a_body(client: TestClient) -> None:
    response = client.delete(f"/materials/{MATERIAL_ID}")

    assert response.status_code == 204
    assert response.content == b""


# --- scope chat -------------------------------------------------------------------


def test_SM06_chat_streams_patches_then_a_tutor_reply_then_done(client: TestClient) -> None:
    events = assert_stream(chat(client))

    names = [name for name, _ in events]
    assert "token" in names
    assert names[-1] == "done"
    assert "scope_patch" not in names[names.index("token") :]  # actions are checked before words
    assert {data["speaker"] for name, data in events if name == "token"} == {"tutor"}


def test_SM07_patch_sends_only_the_fields_that_changed(client: TestClient) -> None:
    """A null would overwrite the card, because the web merges `changes` into it."""
    events = assert_stream(chat(client))

    patches = [data for name, data in events if name == "scope_patch"]
    assert patches, "fixture should change a topic"
    for patch in patches:
        ScopePatchEvent.model_validate(patch)
        assert patch["changes"]
        assert None not in patch["changes"].values()


def test_SM06_chat_blank_text_is_refused(client: TestClient) -> None:
    response = chat(client, "   ")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_SM06_chat_text_at_the_limit_is_accepted(client: TestClient) -> None:
    max_chars = get_settings().ai.guards.max_message_chars

    assert_stream(chat(client, "ก" * max_chars))


def test_SM06_chat_text_over_the_limit_is_refused(client: TestClient) -> None:
    max_chars = get_settings().ai.guards.max_message_chars

    response = chat(client, "ก" * (max_chars + 1))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "message_too_long"


# --- rate limit (gateway-guards.md §2.1) -------------------------------------------


@pytest.fixture
def limit() -> Iterator[int]:
    """A limiter with a stopped clock, so no request leaves the window during a test."""
    value = get_settings().ai.guards.rate_limit_messages_per_minute
    limiter = RateLimiter(limit=value, clock=lambda: 1000.0)
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    yield value
    app.dependency_overrides.pop(get_rate_limiter, None)


def test_TM21_scope_chat_shares_one_counter_with_room_messages(
    client: TestClient, limit: int
) -> None:
    """gateway-guards.md AC-26"""
    for _ in range(limit - 1):
        assert client.post(MESSAGES, json=IMAGE).status_code == 200

    assert chat(client).status_code == 200

    response = client.post(MESSAGES, json=IMAGE)
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"


def test_TM21_scope_chat_over_the_limit_is_429_with_retry_after(
    client: TestClient, limit: int
) -> None:
    for _ in range(limit):
        assert chat(client).status_code == 200

    response = chat(client)

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert int(response.headers["retry-after"]) > 0


# --- changes and bad ids -----------------------------------------------------------


def test_SM08_changes_are_oldest_first(client: TestClient) -> None:
    response = client.get(f"/exam-preps/{PREP_ID}/scope/changes")

    assert response.status_code == 200
    changes = TypeAdapter(list[ScopeChange]).validate_python(response.json())
    assert changes, "fixture should have changes"
    times = [c.created_at for c in changes]
    assert times == sorted(times)


@pytest.mark.parametrize(
    ("method", "url", "body"),
    [
        ("get", "/exam-preps/x/ingestion", None),
        ("post", "/materials/x/retry", None),
        ("delete", "/materials/x", None),
        ("post", "/exam-preps/x/scope/chat", {"text": "x"}),
        ("get", "/exam-preps/x/scope/changes", None),
    ],
)
def test_apimd_scope_edit_bad_id_is_422_envelope(
    client: TestClient, method: str, url: str, body: Any
) -> None:
    response = client.request(method.upper(), url, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


# --- added at step 7 (after Jam's test review) ---------------------------------------


def test_SM07_scope_patch_changes_schema_says_left_out_not_null(openapi: dict[str, Any]) -> None:
    """A default or a null here makes generated types say `stars: number | null` is always
    there, but a field that did not change is absent, and `undefined` would overwrite the card."""
    properties = openapi["components"]["schemas"]["ScopePatchChanges"]["properties"]

    for name, field in properties.items():
        assert "default" not in field, name
        assert "anyOf" not in field, name


# --- added in self-review (after Jam's test review) ----------------------------------


def test_CM07_step_can_report_a_failure() -> None:
    """api.md v1.11: otherwise a failed topic merge leaves S11 polling with every file green.

    Jam chose this in self-review, and the case in the reject test above became `skipped`."""
    step = IngestionStep.model_validate({"label": "หาหัวข้อและลำดับการเรียน", "status": "failed"})

    assert step.status == "failed"


@pytest.mark.parametrize(
    "changes",
    [
        {"stars": None},
        {"stars": 0, "reason": None},  # the excluded card would keep its old reason
        {"name": ""},
        {"name": "   "},
    ],
)
def test_SM07_scope_patch_refuses_null_and_blank_values(changes: dict[str, Any]) -> None:
    """api.md v1.11: no nulls and no blank name, so a bad action fails validation (UC-02 E2)."""
    with pytest.raises(ValueError):
        ScopePatchEvent.model_validate({"topic_id": TOPIC_ID, "changes": changes})


def test_SM07_room_streams_do_not_declare_scope_patch(openapi: dict[str, Any]) -> None:
    """api.md "SSE events": scope_patch belongs to flow 2.3."""
    operation = openapi["paths"]["/sessions/{id}/messages"]["post"]

    schema = operation["responses"]["200"]["content"]["text/event-stream"]["schema"]
    assert "ScopePatchEvent" not in {item["$ref"].rsplit("/", 1)[1] for item in schema["oneOf"]}


def test_CM07_retry_of_a_file_that_failed_classifying_goes_back_to_uploaded(
    client: TestClient,
) -> None:
    """api.md v1.11: a state the materials flow can reach, not confirmed without a kind."""
    material = client.post(f"/materials/{MATERIAL_ID}/retry").json()

    assert material["kind"] is None
    assert material["kind_confirmed"] is False
    assert material["status"] == "uploaded"
