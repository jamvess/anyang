""" "ลองใหม่" on S11: `POST /materials/{id}/retry` on the database and the new
`POST /exam-preps/{id}/ingestion/retry` (specs/features/exam-prep/ingestion-retry.md §2.2, §2.3 ·
AC-11 to AC-21, router side). No network: the repository and the ingestion reader are fakes of
the rows the user's JWT can see (RLS), and the runner is a fake that records what it was asked.
What the runner writes before it returns is tested in test_ingestion_retry_runner.py.

Interfaces these tests expect (to be built by /implement-feature):
- `IngestionRunner.retry_file(material_id) -> None` (async): sets the failed file back to
  `uploaded` or `confirmed` (and its failed jobs to `queued`), then classifies or starts the prep
  in the background · the existing `retry` is kept for the reviewed tests that await it.
- `IngestionRunner.retry_steps(prep_id) -> None` (async): `topics` and `stars` back to `queued`,
  then `start(prep_id)` in the background.
- the router `POST /materials/{id}/retry` uses `get_material_repository`, `get_ingestion_runner`
  and `get_auth` (as `/uploaded` does) · `POST /exam-preps/{id}/ingestion/retry` uses
  `get_ingestion_reader`, `get_ingestion_runner` and `get_auth` (as `GET /ingestion` does).
"""

import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient

from app.auth import get_auth
from app.db.ingestion import InMemoryIngestionStore, get_ingestion_reader
from app.db.materials import get_material_repository
from app.main import app
from app.services.ingestion import get_ingestion_runner
from tests.unit.test_materials_db_api import PREP, USER, FakeRepo, add, assert_error

DB_DOWN = "db_unavailable"


@dataclass
class FakeRunner:
    """Records the retries asked of it; nothing runs."""

    files: list[uuid.UUID] = field(default_factory=list)
    steps: list[uuid.UUID] = field(default_factory=list)
    classified: list[uuid.UUID] = field(default_factory=list)
    started: list[uuid.UUID] = field(default_factory=list)

    async def retry_file(self, material_id: uuid.UUID) -> None:
        self.files.append(material_id)

    async def retry_steps(self, prep_id: uuid.UUID) -> None:
        self.steps.append(prep_id)

    def classify(self, material_id: uuid.UUID) -> None:
        self.classified.append(material_id)

    def start(self, prep_id: uuid.UUID) -> None:
        self.started.append(prep_id)

    def untouched(self) -> bool:
        return not (self.files or self.steps or self.classified or self.started)


@pytest.fixture
def repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def store() -> InMemoryIngestionStore:
    return InMemoryIngestionStore()


@pytest.fixture
def runner() -> FakeRunner:
    return FakeRunner()


@pytest.fixture
def client(
    repo: FakeRepo, store: InMemoryIngestionStore, runner: FakeRunner
) -> Iterator[TestClient]:
    """No token (AUTH_REQUIRED=false · conftest) unless `signed_in` is used."""
    app.dependency_overrides[get_material_repository] = lambda: repo
    app.dependency_overrides[get_ingestion_reader] = lambda: store.reader_for(USER.tenant_id)
    app.dependency_overrides[get_ingestion_runner] = lambda: runner
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def signed_in(client: TestClient) -> TestClient:
    app.dependency_overrides[get_auth] = lambda: USER
    return client


def retry_file(client: TestClient, material_id: uuid.UUID):
    return client.post(f"/materials/{material_id}/retry")


def retry_steps(client: TestClient, prep_id: uuid.UUID):
    return client.post(f"/exam-preps/{prep_id}/ingestion/retry")


def prep_with_steps(
    store: InMemoryIngestionStore, *, topics: str | None, stars: str | None, file: str = "ready"
) -> uuid.UUID:
    """The user's prep with one sheet (`file` status, its jobs to match) and the prep's steps."""
    prep = store.add_prep(USER.tenant_id)
    sheet = store.add_material(
        prep, file_name="sheet-01.pdf", kind="sheet", storage_path="s1", status=file
    )
    job = {"ready": "done", "failed": "failed", "ingesting": "running"}[file]
    store.add_job(prep, "extract", job, material_id=sheet)
    if topics is not None:
        store.add_job(prep, "topics", topics)
    if stars is not None:
        store.add_job(prep, "stars", stars)
    return prep


def prep_jobs(store: InMemoryIngestionStore, prep: uuid.UUID) -> dict[str, str]:
    return {
        j["stage"]: j["status"]
        for j in store.rows("ingestion_jobs")
        if j["exam_prep_id"] == prep and j["material_id"] is None
    }


# --- POST /materials/{id}/retry (§2.2) ----------------------------------------------------------


def test_CM07_retry_a_file_failed_while_reading_comes_back_confirmed(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-11 (router side): 202, the row as it is after the reset, and the runner asked once."""
    row = add(
        repo,
        status="failed",
        error="อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้",
        kind="sheet",
        kind_confidence=0.9,
        kind_confirmed=True,
    )

    response = retry_file(signed_in, row.id)

    assert response.status_code == 202, response.text
    assert "x-stub" not in response.headers
    body = response.json()
    assert (body["id"], body["status"], body["error"]) == (str(row.id), "confirmed", None)
    assert runner.files == [row.id]


def test_CM07_retry_a_file_failed_while_classifying_comes_back_uploaded(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-12 (router side)."""
    row = add(repo, status="failed", error="อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้", kind_confirmed=False)

    response = retry_file(signed_in, row.id)

    assert response.status_code == 202, response.text
    body = response.json()
    assert (body["status"], body["error"]) == ("uploaded", None)
    assert runner.files == [row.id]


@pytest.mark.parametrize("status", ["uploaded", "classified", "confirmed", "ingesting", "ready"])
def test_CM07_retry_a_file_that_did_not_fail_is_409(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner, status: str
) -> None:
    """AC-13."""
    row = add(repo, status=status, kind="sheet", kind_confirmed=status != "uploaded")

    assert_error(retry_file(signed_in, row.id), 409, "not_failed")
    assert repo.rows[row.id] == row
    assert runner.untouched()


def test_SA06_retry_a_file_the_user_cannot_see_is_404(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-14: another tenant's file is hidden by RLS, so the fake does not have it; a file that
    does not exist answers the same."""
    assert_error(retry_file(signed_in, uuid.uuid4()), 404, "not_found")
    assert runner.untouched()


def test_CM07_retry_a_file_while_the_database_is_down_is_503(
    signed_in: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-15 (file)."""
    row = add(repo, status="failed", kind="sheet", kind_confirmed=True)
    repo.down = True

    assert_error(retry_file(signed_in, row.id), 503, DB_DOWN)
    assert runner.untouched()


def test_CM07_retry_a_file_without_a_token_keeps_the_stub(
    client: TestClient, repo: FakeRepo, runner: FakeRunner
) -> None:
    """AC-16 (file)."""
    response = retry_file(client, uuid.uuid4())

    assert response.status_code == 202, response.text
    assert response.headers["x-stub"] == "true"
    assert repo.calls == []
    assert runner.untouched()


# --- POST /exam-preps/{id}/ingestion/retry (§2.3) -------------------------------------------------


def test_CM07_retry_the_steps_after_topics_failed(
    signed_in: TestClient, store: InMemoryIngestionStore, runner: FakeRunner
) -> None:
    """AC-17 (router side): 202 with no body, the runner asked once."""
    prep = prep_with_steps(store, topics="failed", stars="queued")

    response = retry_steps(signed_in, prep)

    assert response.status_code == 202, response.text
    assert "x-stub" not in response.headers
    assert response.content == b""
    assert runner.steps == [prep]


def test_CM07_retry_the_steps_after_only_stars_failed(
    signed_in: TestClient, store: InMemoryIngestionStore, runner: FakeRunner
) -> None:
    """AC-18 (router side): a failed `stars` alone is a failed step too."""
    prep = prep_with_steps(store, topics="done", stars="failed")

    assert retry_steps(signed_in, prep).status_code == 202
    assert runner.steps == [prep]


@pytest.mark.parametrize(
    ("topics", "stars"),
    [("done", "done"), ("running", "queued"), (None, None)],
    ids=["all done", "topics running", "no step rows yet"],
)
def test_CM07_retry_the_steps_when_none_failed_is_409(
    signed_in: TestClient,
    store: InMemoryIngestionStore,
    runner: FakeRunner,
    topics: str | None,
    stars: str | None,
) -> None:
    """AC-19."""
    prep = prep_with_steps(store, topics=topics, stars=stars)
    before = prep_jobs(store, prep)

    assert_error(retry_steps(signed_in, prep), 409, "not_failed")
    assert prep_jobs(store, prep) == before
    assert runner.untouched()


def test_CM07_retry_the_steps_while_a_file_failed_is_409(
    signed_in: TestClient, store: InMemoryIngestionStore, runner: FakeRunner
) -> None:
    """AC-20: the failed file is retried on its own row first."""
    prep = prep_with_steps(store, topics="failed", stars="queued", file="failed")

    assert_error(retry_steps(signed_in, prep), 409, "not_failed")
    assert prep_jobs(store, prep) == {"topics": "failed", "stars": "queued"}
    assert runner.untouched()


def test_SA06_retry_the_steps_of_a_prep_the_user_cannot_see_is_404(
    signed_in: TestClient, store: InMemoryIngestionStore, runner: FakeRunner
) -> None:
    """AC-21: another tenant's prep with a failed step, and a prep that does not exist."""
    foreign = store.add_prep(uuid.uuid4())
    store.add_job(foreign, "topics", "failed")

    assert_error(retry_steps(signed_in, foreign), 404, "not_found")
    assert_error(retry_steps(signed_in, uuid.uuid4()), 404, "not_found")
    assert prep_jobs(store, foreign) == {"topics": "failed"}
    assert runner.untouched()


def test_CM07_retry_the_steps_while_the_database_is_down_is_503(
    signed_in: TestClient, store: InMemoryIngestionStore, runner: FakeRunner
) -> None:
    """AC-15 (steps)."""
    prep = prep_with_steps(store, topics="failed", stars="queued")
    store.down = True

    assert_error(retry_steps(signed_in, prep), 503, DB_DOWN)
    assert runner.untouched()


def test_CM07_retry_the_steps_without_a_token_is_a_stub(
    client: TestClient, runner: FakeRunner
) -> None:
    """AC-16 (steps)."""
    response = retry_steps(client, PREP)

    assert response.status_code == 202, response.text
    assert response.headers["x-stub"] == "true"
    assert runner.untouched()
