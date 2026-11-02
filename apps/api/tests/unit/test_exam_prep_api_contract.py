"""Contract tests for exam preps and materials (specs/system/api.md v1.10
"สร้างการเตรียมสอบและใส่ไฟล์").

The stubs serve fixture data until the real endpoints exist. These tests check shapes and
request rules, not fixture values, so the real endpoints must pass them unchanged.
Stub-only checks live in test_exam_prep_stubs.py.
"""

from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import app
from app.models.exam_prep import (
    ConfirmMaterialsRequest,
    CreateExamPrepRequest,
    ExamPrep,
    Material,
    MaterialsQueued,
    MaterialUploadTicket,
)

PREP_ID = "00000000-0000-4000-8000-000000000001"
MATERIAL_ID = "00000000-0000-4000-8000-000000000005"
BANGKOK = timezone(timedelta(hours=7))  # api.md: days are counted in Asia/Bangkok (no DST)

ERROR_REF = "#/components/schemas/ErrorResponse"
PDF = "application/pdf"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# api.md v1.10: documented errors of each endpoint (401/503 auth errors come from get_auth).
DOCUMENTED_ERRORS = [
    ("post", "/exam-preps", ["422"]),
    ("get", "/exam-preps", []),
    ("post", "/exam-preps/{id}/materials", ["404", "422"]),
    ("post", "/materials/{id}/uploaded", ["404", "409", "422"]),
    ("get", "/exam-preps/{id}/materials", ["404", "422"]),
    ("post", "/exam-preps/{id}/materials/confirm", ["404", "409", "422"]),
]


def today() -> date:
    return datetime.now(BANGKOK).date()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def openapi(client: TestClient) -> dict[str, Any]:
    return client.get("/openapi.json").json()


def new_prep(**change: Any) -> dict[str, Any]:
    return {"title": "Calculus 1 midterm", "exam_date": str(today() + timedelta(days=5)), **change}


def upload(**change: Any) -> dict[str, Any]:
    return {
        "file_name": "ch3-factorization.pdf",
        "content_type": PDF,
        "size_bytes": 900_000,
        **change,
    }


# --- endpoints and OpenAPI ---------------------------------------------------


@pytest.mark.parametrize(("method", "path", "statuses"), DOCUMENTED_ERRORS)
def test_apimd_exam_prep_endpoints_and_errors_in_openapi(
    openapi: dict[str, Any], method: str, path: str, statuses: list[str]
) -> None:
    responses = openapi["paths"][path][method]["responses"]

    errors = sorted(code for code in responses if code.startswith(("4", "5")))
    assert errors == sorted({*statuses, "401", "503"})
    for status in statuses:
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"] == ERROR_REF


def test_apimd_exam_prep_schemas_have_exact_required_fields(openapi: dict[str, Any]) -> None:
    schemas = openapi["components"]["schemas"]
    expected = {
        "ExamPrep": {
            "id",
            "title",
            "exam_date",
            "days_left",
            "daily_minutes",
            "stage",
            "readiness",
            "topics_not_passed",
        },
        "Material": {
            "id",
            "file_name",
            "kind",
            "kind_confidence",
            "kind_confirmed",
            "user_note",
            "status",
            "error",
        },
        "MaterialUploadTicket": {"material_id", "upload_url", "path"},
        "MaterialsQueued": {"queued"},
    }
    for name, fields in expected.items():
        assert set(schemas[name]["properties"]) == fields, name
        assert set(schemas[name]["required"]) == fields, name


@pytest.mark.parametrize(
    ("path", "status"),
    [("/materials/{id}/uploaded", "202"), ("/exam-preps/{id}/materials/confirm", "202")],
)
def test_CM06_jobs_answer_202(openapi: dict[str, Any], path: str, status: str) -> None:
    """api.md Conventions: long-running jobs answer 202 Accepted."""
    assert status in openapi["paths"][path]["post"]["responses"]


# --- model rules -------------------------------------------------------------


@pytest.mark.parametrize(
    ("body", "ok"),
    [
        ({"title": "Midterm", "exam_date": "2026-12-01"}, True),
        ({"title": "Midterm", "exam_date": "2026-12-01", "daily_minutes": 30}, True),
        ({"title": "", "exam_date": "2026-12-01"}, False),
        ({"title": "   ", "exam_date": "2026-12-01"}, False),
        ({"title": "Midterm", "exam_date": "2026-12-01", "daily_minutes": 0}, False),
        ({"title": "Midterm"}, False),
        ({"title": "Midterm", "exam_date": "next week"}, False),
    ],
)
def test_CM01_create_request_rules(body: dict[str, Any], ok: bool) -> None:
    if ok:
        CreateExamPrepRequest.model_validate(body)
    else:
        with pytest.raises(ValueError):
            CreateExamPrepRequest.model_validate(body)


@pytest.mark.parametrize(
    ("change", "ok"),
    [
        ({"kind": "past_exam", "status": "classified"}, True),
        ({"kind": None, "kind_confidence": None, "status": "uploaded"}, True),
        ({"kind": "exercise"}, False),  # not in the materials.kind check (api.md รอตัดสิน 5)
        ({"status": "processing"}, False),
        ({"kind_confidence": 1.5}, False),
    ],
)
def test_CM07_material_enums(change: dict[str, Any], ok: bool) -> None:
    data = {
        "id": MATERIAL_ID,
        "file_name": "midterm-2566.pdf",
        "kind": "past_exam",
        "kind_confidence": 0.9,
        "kind_confirmed": False,
        "user_note": None,
        "status": "classified",
        "error": None,
        **change,
    }
    if ok:
        Material.model_validate(data)
    else:
        with pytest.raises(ValueError):
            Material.model_validate(data)


@pytest.mark.parametrize(
    ("body", "ok"),
    [
        ({"materials": [{"id": MATERIAL_ID, "kind": "sheet"}]}, True),
        ({"materials": []}, False),
        ({"materials": [{"id": MATERIAL_ID, "kind": "exercise"}]}, False),
        ({"materials": [{"id": "m1", "kind": "sheet"}]}, False),
    ],
)
def test_CM06_confirm_request_rules(body: dict[str, Any], ok: bool) -> None:
    if ok:
        ConfirmMaterialsRequest.model_validate(body)
    else:
        with pytest.raises(ValueError):
            ConfirmMaterialsRequest.model_validate(body)


# --- exam preps ----------------------------------------------------------------


def test_CM01_create_returns_201_and_the_new_prep(client: TestClient) -> None:
    response = client.post("/exam-preps", json=new_prep(daily_minutes=40))

    assert response.status_code == 201
    prep = ExamPrep.model_validate(response.json())
    assert prep.title == "Calculus 1 midterm"
    assert prep.daily_minutes == 40
    assert prep.stage == "materials"
    assert prep.readiness is None and prep.topics_not_passed is None


def test_CM01_daily_minutes_may_be_left_out(client: TestClient) -> None:
    """UC-02 A1: no daily minutes means the planner's default from config."""
    response = client.post("/exam-preps", json=new_prep())

    assert response.status_code == 201
    assert response.json()["daily_minutes"] is None


@pytest.mark.parametrize("days", [0, 1, 30])
def test_CM02_days_left_counts_from_today_in_bangkok(client: TestClient, days: int) -> None:
    exam_date = today() + timedelta(days=days)

    response = client.post("/exam-preps", json=new_prep(exam_date=str(exam_date)))

    assert response.status_code == 201
    assert response.json()["days_left"] == days


def test_CM01_exam_date_in_the_past_is_refused(client: TestClient) -> None:
    """api.md รอตัดสิน 3: today is allowed (above), yesterday is not."""
    response = client.post("/exam-preps", json=new_prep(exam_date=str(today() - timedelta(days=1))))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "exam_date_past"


def test_PM04_list_is_soonest_exam_first(client: TestClient) -> None:
    response = client.get("/exam-preps")

    assert response.status_code == 200
    preps = TypeAdapter(list[ExamPrep]).validate_python(response.json())
    assert preps, "fixture should have exam preps"
    dates = [p.exam_date for p in preps]
    assert dates == sorted(dates)


# --- materials ------------------------------------------------------------------


@pytest.mark.parametrize(
    "content_type",
    [
        PDF,
        "image/jpeg",
        "image/PNG",
        "image/webp",
        "image/heic",
        PPTX,
        DOCX,
        "application/pdf; x=1",
    ],
)
def test_CM03_accepted_file_types_get_an_upload_url(client: TestClient, content_type: str) -> None:
    response = client.post(
        f"/exam-preps/{PREP_ID}/materials", json=upload(content_type=content_type)
    )

    assert response.status_code == 200
    ticket = MaterialUploadTicket.model_validate(response.json())
    assert ticket.upload_url
    assert ticket.path.endswith(f"/{PREP_ID}/{ticket.material_id}")  # data-model.md Storage path
    assert "ch3-factorization" not in ticket.path  # names never build Storage paths


@pytest.mark.parametrize("content_type", ["text/plain", "application/zip", "audio/webm"])
def test_CM03_other_file_types_are_refused(client: TestClient, content_type: str) -> None:
    response = client.post(
        f"/exam-preps/{PREP_ID}/materials", json=upload(content_type=content_type)
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_type"


@pytest.mark.parametrize("change", [{"size_bytes": 0}, {"file_name": ""}])
def test_CM03_upload_body_validation(client: TestClient, change: dict[str, Any]) -> None:
    response = client.post(f"/exam-preps/{PREP_ID}/materials", json=upload(**change))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize("body", [{}, {"user_note": "ของรุ่นพี่ คนละอาจารย์กัน"}])
def test_CM04_uploaded_takes_an_optional_note_and_answers_202(
    client: TestClient, body: dict[str, Any]
) -> None:
    response = client.post(f"/materials/{MATERIAL_ID}/uploaded", json=body)

    assert response.status_code == 202
    material = Material.model_validate(response.json())
    assert material.user_note == body.get("user_note")


def test_CM07_materials_list_validates(client: TestClient) -> None:
    response = client.get(f"/exam-preps/{PREP_ID}/materials")

    assert response.status_code == 200
    materials = TypeAdapter(list[Material]).validate_python(response.json())
    assert materials, "fixture should have materials"


def test_CM06_confirm_answers_202_with_the_queued_count(client: TestClient) -> None:
    body = {"materials": [{"id": MATERIAL_ID, "kind": "past_exam"}]}

    response = client.post(f"/exam-preps/{PREP_ID}/materials/confirm", json=body)

    assert response.status_code == 202
    assert MaterialsQueued.model_validate(response.json()).queued >= 0


@pytest.mark.parametrize(
    ("method", "url", "body"),
    [
        ("post", "/exam-preps/x/materials", upload()),
        ("post", "/materials/x/uploaded", {}),
        ("get", "/exam-preps/x/materials", None),
        (
            "post",
            "/exam-preps/x/materials/confirm",
            {"materials": [{"id": MATERIAL_ID, "kind": "sheet"}]},
        ),
    ],
)
def test_apimd_exam_prep_bad_id_is_422_envelope(
    client: TestClient, method: str, url: str, body: Any
) -> None:
    response = client.request(method.upper(), url, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
