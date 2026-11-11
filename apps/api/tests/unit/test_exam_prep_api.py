"""POST and GET /exam-preps on the database, with a fake repository
(specs/features/exam-prep/create-exam-prep.md · api.md v1.14).

No network: the repository dependency `get_exam_prep_repository` is replaced by `FakeRepo`,
`get_auth` by a fixed user when a test needs "a valid token", and `get_now` by a fixed instant
(2026-11-11 12:00 in Bangkok). The title cap is read from the loaded config, never written here.

Interfaces these tests expect (to be built by /implement-feature):
- `app.db.exam_preps`: `ExamPrepRecord`, `DbUnavailableError`, `SupabaseExamPrepRepository`,
  `get_exam_prep_repository` (dependency)
- `app.domain.exam_prep.MaterialFacts`
- `app.clock.get_now` (dependency returning an aware datetime)
"""

import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from supabase import ClientOptions, create_client

from app.auth import AuthContext, get_auth, get_auth_required
from app.clock import get_now
from app.db.exam_preps import (
    DbUnavailableError,
    ExamPrepRecord,
    SupabaseExamPrepRepository,
    get_exam_prep_repository,
)
from app.domain.exam_prep import MaterialFacts
from app.main import app
from app.settings import get_settings

NOW = datetime(2026, 11, 11, 5, 0, tzinfo=UTC)  # 12:00 in Bangkok
TODAY = date(2026, 11, 11)
USER = AuthContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), token="test-token")
MAX_TITLE = get_settings().ai.guards.max_exam_prep_title_chars
DB_DOWN_MESSAGE = "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง"


@dataclass
class FakeRepo:
    """Stands in for the Supabase repository. Records every call."""

    rows: list[ExamPrepRecord] = field(default_factory=list)
    created: list[dict[str, Any]] = field(default_factory=list)
    calls: int = 0
    down: bool = False

    def create(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        exam_date: date,
        daily_minutes: int | None,
    ) -> ExamPrepRecord:
        self.calls += 1
        if self.down:
            raise DbUnavailableError("connection refused")
        self.created.append(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "title": title,
                "exam_date": exam_date,
                "daily_minutes": daily_minutes,
            }
        )
        record = record_of(title=title, exam_date=exam_date, daily_minutes=daily_minutes)
        self.rows.append(record)
        return record

    def list_active(self) -> list[ExamPrepRecord]:
        self.calls += 1
        if self.down:
            raise DbUnavailableError("connection refused")
        return list(self.rows)


def record_of(**change: Any) -> ExamPrepRecord:
    data: dict[str, Any] = {
        "id": uuid.uuid4(),
        "title": "แคลคูลัส 1 กลางภาค",
        "exam_date": TODAY + timedelta(days=27),
        "daily_minutes": None,
        "created_at": NOW,
        "active_scope_version_id": None,
        "topic_importances": [],
        "materials": [],
        **change,
    }
    return ExamPrepRecord(**data)


@pytest.fixture
def repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def client(repo: FakeRepo) -> Iterator[TestClient]:
    """No token, AUTH_REQUIRED=false (conftest) unless a test overrides more."""
    app.dependency_overrides[get_exam_prep_repository] = lambda: repo
    app.dependency_overrides[get_now] = lambda: NOW
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def signed_in(client: TestClient) -> TestClient:
    """A request with a valid token (AC-auth-real)."""
    app.dependency_overrides[get_auth] = lambda: USER
    return client


def prep(**change: Any) -> dict[str, Any]:
    return {"title": "แคลคูลัส 1 กลางภาค", "exam_date": str(TODAY + timedelta(days=27)), **change}


def assert_error(response: Any, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


# --- three auth cases (§2.1 ข้อ 1) ---------------------------------------------------


@pytest.mark.parametrize(("method", "body"), [("POST", prep()), ("GET", None)])
def test_SA06_no_token_with_auth_required_is_401_never_stub(
    client: TestClient, repo: FakeRepo, method: str, body: Any
) -> None:
    """AC-auth-required."""
    app.dependency_overrides[get_auth_required] = lambda: True

    response = client.request(method, "/exam-preps", json=body)

    assert_error(response, 401, "missing_token")
    assert "x-stub" not in response.headers
    assert repo.calls == 0


def test_SA06_no_token_without_auth_required_gets_the_stub_list(
    client: TestClient, repo: FakeRepo
) -> None:
    """AC-auth-stub: the fixture with a prep in every stage, and the repository untouched."""
    response = client.get("/exam-preps")

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"
    assert {p["stage"] for p in response.json()} == {"materials", "processing", "scope", "tutoring"}
    assert repo.calls == 0


def test_SA06_no_token_without_auth_required_gets_the_stub_create(
    client: TestClient, repo: FakeRepo
) -> None:
    """AC-auth-stub: 201 with X-Stub, nothing saved."""
    response = client.post("/exam-preps", json=prep())

    assert response.status_code == 201
    assert response.headers.get("x-stub") == "true"
    assert repo.calls == 0


def test_SA06_stub_create_still_validates_the_body(client: TestClient, repo: FakeRepo) -> None:
    """AC-auth-stub: a bad body is 422 on the stub path too."""
    response = client.post("/exam-preps", json=prep(title="แคลคูลัส\n1"))

    assert_error(response, 422, "validation_error")
    assert repo.calls == 0


@pytest.mark.parametrize("required", [True, False])
@pytest.mark.parametrize(("method", "body", "status"), [("POST", prep(), 201), ("GET", None, 200)])
def test_CM01_with_a_token_uses_the_database_and_no_stub_header(
    signed_in: TestClient,
    repo: FakeRepo,
    required: bool,
    method: str,
    body: Any,
    status: int,
) -> None:
    """AC-auth-real."""
    app.dependency_overrides[get_auth_required] = lambda: required

    response = signed_in.request(method, "/exam-preps", json=body)

    assert response.status_code == status, response.text
    assert "x-stub" not in response.headers
    assert repo.calls == 1


# --- create (CM-01) ------------------------------------------------------------------


def test_CM01_create_saves_with_tenant_and_user_from_the_token(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """AC-1 (the row itself is checked against the real DB in the integration test)."""
    response = signed_in.post("/exam-preps", json=prep())

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "id",
        "title",
        "exam_date",
        "days_left",
        "daily_minutes",
        "stage",
        "readiness",
        "topics_not_passed",
    }
    assert body["title"] == "แคลคูลัส 1 กลางภาค"
    assert body["exam_date"] == "2026-12-08"
    assert body["days_left"] == 27
    assert body["daily_minutes"] is None
    assert body["stage"] == "materials"
    assert body["readiness"] is None and body["topics_not_passed"] is None
    assert repo.created == [
        {
            "tenant_id": USER.tenant_id,
            "user_id": USER.user_id,
            "title": "แคลคูลัส 1 กลางภาค",
            "exam_date": date(2026, 12, 8),
            "daily_minutes": None,
        }
    ]


@pytest.mark.parametrize(("sent", "saved"), [(45, 45), (None, None)])
def test_CM01_daily_minutes_saved(
    signed_in: TestClient, repo: FakeRepo, sent: int | None, saved: int | None
) -> None:
    """AC-2, AC-3."""
    response = signed_in.post("/exam-preps", json=prep(daily_minutes=sent))

    assert response.status_code == 201
    assert response.json()["daily_minutes"] == saved
    assert repo.created[0]["daily_minutes"] == saved


def test_CM01_title_is_trimmed(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-4."""
    response = signed_in.post("/exam-preps", json=prep(title="  แคลคูลัส 1  "))

    assert response.status_code == 201
    assert response.json()["title"] == "แคลคูลัส 1"
    assert repo.created[0]["title"] == "แคลคูลัส 1"


@pytest.mark.parametrize(
    "body",
    [
        prep(title=""),  # AC-5
        prep(title="   "),  # AC-5
        {"exam_date": str(TODAY)},  # AC-6: no title
        {"title": "แคลคูลัส 1"},  # AC-6: no exam_date
        prep(subject="math"),  # AC-6: extra field
        prep(user_id=str(uuid.uuid4())),  # AC-6 / AC-tenant-body
        prep(tenant_id=str(uuid.uuid4())),  # AC-6 / AC-tenant-body
        prep(exam_date="2026-1-5"),  # AC-7
        prep(exam_date="05/01/2026"),  # AC-7
        prep(exam_date="2026-11-11T00:00:00"),  # AC-7
        prep(exam_date="2026-02-30"),  # AC-7
        prep(daily_minutes="30"),  # AC-8
        prep(daily_minutes=True),  # AC-8
        prep(daily_minutes=30.5),  # AC-8
        prep(title=123),  # wrong type
    ],
)
def test_CM01_invalid_body_is_422_and_saves_nothing(
    signed_in: TestClient, repo: FakeRepo, body: dict[str, Any]
) -> None:
    response = signed_in.post("/exam-preps", json=body)

    assert_error(response, 422, "validation_error")
    assert repo.created == []


def test_CM01_same_title_twice_is_allowed(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-9."""
    first = signed_in.post("/exam-preps", json=prep(title="แคลคูลัส 1"))
    second = signed_in.post("/exam-preps", json=prep(title="แคลคูลัส 1"))

    assert first.status_code == second.status_code == 201
    assert len(repo.created) == 2


# --- boundaries -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("offset", "status", "days"),
    [(-1, 422, None), (0, 201, 0), (1, 201, 1)],
)
def test_CM01_exam_date_boundary(
    signed_in: TestClient, repo: FakeRepo, offset: int, status: int, days: int | None
) -> None:
    """AC-boundary-date."""
    response = signed_in.post("/exam-preps", json=prep(exam_date=str(TODAY + timedelta(offset))))

    assert response.status_code == status
    if status == 422:
        assert response.json()["error"]["code"] == "exam_date_past"
        assert repo.created == []
    else:
        assert response.json()["days_left"] == days


@pytest.mark.parametrize(
    ("exam_date", "status", "days"),
    [("2026-11-11", 422, None), ("2026-11-12", 201, 0)],
)
def test_CM02_exam_date_uses_the_bangkok_day_not_utc(
    signed_in: TestClient, exam_date: str, status: int, days: int | None
) -> None:
    """AC-boundary-date-tz: 17:30 UTC on the 11th is 00:30 on the 12th in Bangkok."""
    app.dependency_overrides[get_now] = lambda: datetime(2026, 11, 11, 17, 30, tzinfo=UTC)

    response = signed_in.post("/exam-preps", json=prep(exam_date=exam_date))

    assert response.status_code == status
    if status == 422:
        assert response.json()["error"]["code"] == "exam_date_past"
    else:
        assert response.json()["days_left"] == days


@pytest.mark.parametrize(("length", "status"), [(-1, 201), (0, 201), (1, 422)])
def test_CM01_title_length_boundary_in_graphemes(
    signed_in: TestClient, length: int, status: int
) -> None:
    """AC-boundary-title: N - 1, N, N + 1 with N = guards.max_exam_prep_title_chars."""
    title = "ก" * (MAX_TITLE + length)

    response = signed_in.post("/exam-preps", json=prep(title=title))

    assert response.status_code == status, response.text
    if status == 422:
        assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize(("length", "status"), [(0, 201), (1, 422)])
def test_CM01_thai_marks_do_not_count_toward_the_title_cap(
    signed_in: TestClient, length: int, status: int
) -> None:
    """AC-boundary-title-thai: "กี่" is 3 code points but 1 grapheme."""
    title = "กี่" * (MAX_TITLE + length)
    assert len(title) > MAX_TITLE

    response = signed_in.post("/exam-preps", json=prep(title=title))

    assert response.status_code == status, response.text


def test_CM01_surrounding_spaces_do_not_count_toward_the_title_cap(
    signed_in: TestClient,
) -> None:
    """AC-boundary-title-thai: N graphemes plus spaces around it."""
    response = signed_in.post("/exam-preps", json=prep(title=f"  {'ก' * MAX_TITLE}  "))

    assert response.status_code == 201


@pytest.mark.parametrize(
    "title",
    [
        "แคลคูลัส\n1",
        "แคลคูลัส\t1",
        "แคลคูลัส\x001",
        "แคลคูลัส\r\n1",
        "แคลคูลัส\x7f",
        "แคลคูลัส 1\n",  # at the end: refused, not trimmed away
        "\tแคลคูลัส 1",  # at the start
    ],
)
def test_CM01_title_with_control_characters_is_refused(
    signed_in: TestClient, repo: FakeRepo, title: str
) -> None:
    """AC-title-control."""
    response = signed_in.post("/exam-preps", json=prep(title=title))

    assert_error(response, 422, "validation_error")
    assert repo.created == []


@pytest.mark.parametrize(
    "title",
    ["แคล‍คูลัส", "แคล‌คูลัส", "แคลคูลัส 1 กลางภาค"],
)
def test_CM01_title_with_format_characters_is_kept(
    signed_in: TestClient, repo: FakeRepo, title: str
) -> None:
    """AC-title-format-ok: a zero-width joiner or non-joiner is not a control character."""
    response = signed_in.post("/exam-preps", json=prep(title=title))

    assert response.status_code == 201
    assert response.json()["title"] == title
    assert repo.created[0]["title"] == title


@pytest.mark.parametrize(("minutes", "status"), [(0, 422), (1, 201), (1440, 201), (1441, 422)])
def test_CM01_daily_minutes_boundary(signed_in: TestClient, minutes: int, status: int) -> None:
    """AC-boundary-minutes."""
    response = signed_in.post("/exam-preps", json=prep(daily_minutes=minutes))

    assert response.status_code == status


# --- list (CM-01, CM-02) ------------------------------------------------------------------


def test_CM01_empty_list(signed_in: TestClient) -> None:
    """AC-10."""
    response = signed_in.get("/exam-preps")

    assert response.status_code == 200
    assert response.json() == []
    assert "x-stub" not in response.headers


def test_CM02_list_is_soonest_exam_first_then_oldest_created(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """AC-11, AC-12: the router orders, whatever order the repository returns."""
    later = record_of(title="far", exam_date=TODAY + timedelta(10))
    second = record_of(title="b", exam_date=TODAY + timedelta(3), created_at=NOW)
    first = record_of(title="a", exam_date=TODAY + timedelta(3), created_at=NOW - timedelta(1))
    repo.rows = [later, second, first]

    body = signed_in.get("/exam-preps").json()

    assert [p["title"] for p in body] == ["a", "b", "far"]
    assert [p["days_left"] for p in body] == [3, 3, 10]


def test_CM02_past_exam_has_negative_days_left(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-14."""
    repo.rows = [record_of(exam_date=TODAY - timedelta(1))]

    assert signed_in.get("/exam-preps").json()[0]["days_left"] == -1


def test_CM01_list_stage_comes_from_the_facts(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-15 at the API: the router computes stage from the record; readiness stays null."""
    repo.rows = [
        record_of(title="m"),
        record_of(title="p", materials=[MaterialFacts(kind_confirmed=True, status="ingesting")]),
        record_of(
            title="s",
            topic_importances=[3, 1],
            materials=[MaterialFacts(kind_confirmed=True, status="ready")],
        ),
        record_of(title="t", active_scope_version_id=uuid.uuid4()),
    ]

    body = {p["title"]: p for p in signed_in.get("/exam-preps").json()}

    assert {t: p["stage"] for t, p in body.items()} == {
        "m": "materials",
        "p": "processing",
        "s": "scope",
        "t": "tutoring",
    }
    assert all(p["readiness"] is None and p["topics_not_passed"] is None for p in body.values())


# --- DB down -----------------------------------------------------------------------------


@pytest.mark.parametrize(("method", "body"), [("POST", prep()), ("GET", None)])
def test_CM01_database_down_is_503_db_unavailable(
    signed_in: TestClient, repo: FakeRepo, method: str, body: Any
) -> None:
    """AC-db."""
    repo.down = True

    response = signed_in.request(method, "/exam-preps", json=body)

    assert response.status_code == 503
    assert response.json() == {"error": {"code": "db_unavailable", "message": DB_DOWN_MESSAGE}}
    assert "connection refused" not in response.text
    assert response.headers.get("x-request-id")


def test_CM01_supabase_repository_turns_network_errors_into_db_unavailable() -> None:
    """AC-db: nothing listens on port 9, so the real repository must raise DbUnavailableError."""
    client = create_client(
        "http://127.0.0.1:9",
        "sb_publishable_test",
        ClientOptions(auto_refresh_token=False, persist_session=False, postgrest_client_timeout=2),
    )
    repo = SupabaseExamPrepRepository(client)

    with pytest.raises(DbUnavailableError):
        repo.list_active()
    with pytest.raises(DbUnavailableError):
        repo.create(
            tenant_id=USER.tenant_id,
            user_id=USER.user_id,
            title="x",
            exam_date=TODAY,
            daily_minutes=None,
        )
