"""`POST /materials/{id}/retry` on the database, with fakes
(specs/features/exam-prep/material-retry.md · AC-1 to AC-11 · api.md).

The fakes, fixtures and helpers come from test_materials_db_api.py unchanged (already
reviewed). `RetryRepo` only adds the new repository method.

Interface these tests expect (to be built by /implement-feature):
- `MaterialRepository.retry(material_id, *, status) -> MaterialRecord | None` in `app.db.materials`:
  set `status` and `error = null` only while `status = 'failed'`; None when no row changed
  (another request changed it first). Errors: `DbUnavailableError`.
- The router starts `runner.classify(id)` (back to `uploaded`) or `runner.start(prep_id)` (back
  to `confirmed`) under `ai_call_context` of the token, without waiting (spec §2.2 items 4-6).
"""

import uuid
from dataclasses import dataclass, replace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.ai.call_context import AICallContext, current_call_context
from app.auth import InvalidTokenError, get_auth_required, get_verifier
from app.db.errors import DbUnavailableError
from app.db.materials import MaterialRecord
from app.main import app
from tests.unit import test_materials_db_api as materials_db_api
from tests.unit.test_materials_db_api import (
    PREP,
    USER,
    FakeRepo,
    FakeRunner,
    FakeStorage,
    add,
    assert_error,
)

# Fixtures of test_materials_db_api.py.
client = materials_db_api.client
signed_in = materials_db_api.signed_in
storage = materials_db_api.storage
runner = materials_db_api.runner

TRY_AGAIN = "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้"


@dataclass
class RetryRepo(FakeRepo):
    """FakeRepo plus `retry`. `lose_retry_race`: another request changed the status first."""

    lose_retry_race: bool = False
    down_on_retry: bool = False  # the read works, the update does not

    def retry(self, material_id: uuid.UUID, *, status: str) -> MaterialRecord | None:
        self._call("retry")
        if self.down_on_retry:
            raise DbUnavailableError("connection refused")
        row = self.rows.get(material_id)
        if row is None or row.status != "failed" or self.lose_retry_race:
            return None
        row = replace(row, status=status, error=None)
        self.rows[material_id] = row
        return row


@pytest.fixture
def repo() -> RetryRepo:
    return RetryRepo()


def failed_at_classify(repo: FakeRepo) -> MaterialRecord:
    return add(repo, status="failed", error=TRY_AGAIN)


def failed_at_ingest(repo: FakeRepo) -> MaterialRecord:
    return add(
        repo,
        status="failed",
        error=TRY_AGAIN,
        kind="past_exam",
        kind_confidence=0.99,
        kind_confirmed=True,
    )


def retry(c: TestClient, material_id: Any) -> Any:
    return c.post(f"/materials/{material_id}/retry")


def nothing_started(runner: FakeRunner) -> bool:
    return runner.classified == [] and runner.started == []


# --- AC-1, AC-2 · the happy paths -----------------------------------------------------------


def test_CM07_retry_after_classify_failed_classifies_again(
    signed_in: TestClient, repo: RetryRepo, runner: FakeRunner
) -> None:
    """AC-1."""
    row = failed_at_classify(repo)

    response = retry(signed_in, row.id)

    assert response.status_code == 202, response.text
    assert "x-stub" not in response.headers
    body = response.json()
    assert body["id"] == str(row.id)
    assert body["status"] == "uploaded"
    assert body["error"] is None
    assert repo.rows[row.id].status == "uploaded"
    assert repo.rows[row.id].error is None
    assert runner.classified == [row.id]
    assert runner.started == []


def test_CM07_retry_after_ingest_failed_queues_the_prep_again(
    signed_in: TestClient, repo: RetryRepo, runner: FakeRunner
) -> None:
    """AC-2."""
    row = failed_at_ingest(repo)

    response = retry(signed_in, row.id)

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["error"] is None
    assert body["kind"] == "past_exam"
    assert body["kind_confirmed"] is True
    after = repo.rows[row.id]
    assert (after.status, after.error, after.kind) == ("confirmed", None, "past_exam")
    assert runner.started == [PREP]
    assert runner.classified == []


# --- AC-3 to AC-5 · only a failed file, only once --------------------------------------------


@pytest.mark.parametrize("status", ["uploaded", "classified", "confirmed", "ingesting", "ready"])
def test_CM07_retry_of_a_file_not_failed_is_409(
    signed_in: TestClient, repo: RetryRepo, runner: FakeRunner, status: str
) -> None:
    """AC-3."""
    row = add(repo, status=status, kind_confirmed=status in ("confirmed", "ingesting", "ready"))

    response = retry(signed_in, row.id)

    assert_error(response, 409, "not_failed")
    assert repo.rows[row.id] == row
    assert nothing_started(runner)


def test_CM07_retry_lost_to_another_request_is_409(
    signed_in: TestClient, repo: RetryRepo, runner: FakeRunner
) -> None:
    """AC-4: the row read as failed, but the conditional update changed nothing."""
    row = failed_at_classify(repo)
    repo.lose_retry_race = True

    response = retry(signed_in, row.id)

    assert_error(response, 409, "not_failed")
    assert nothing_started(runner)


def test_CM07_retry_twice_starts_the_job_once(
    signed_in: TestClient, repo: RetryRepo, runner: FakeRunner
) -> None:
    """AC-5."""
    row = failed_at_classify(repo)

    first = retry(signed_in, row.id)
    second = retry(signed_in, row.id)

    assert first.status_code == 202, first.text
    assert_error(second, 409, "not_failed")
    assert runner.classified == [row.id]
    assert runner.started == []


# --- AC-6 · another tenant's file -------------------------------------------------------------


def test_SA06_retry_of_another_tenants_file_is_404(
    signed_in: TestClient, repo: RetryRepo, runner: FakeRunner
) -> None:
    """AC-6: RLS hides the row, so the user's repository does not have it."""
    response = retry(signed_in, uuid.uuid4())

    assert_error(response, 404, "not_found")
    assert "retry" not in repo.calls
    assert nothing_started(runner)


# --- AC-7 · ai_calls get the tenant and user --------------------------------------------------


@dataclass
class ContextRunner(FakeRunner):
    """Records the AI call context at the moment the router hands work to the runner."""

    seen: list[tuple[str, AICallContext | None]] | None = None

    def classify(self, material_id: uuid.UUID) -> None:
        super().classify(material_id)
        assert self.seen is not None
        self.seen.append(("classify", current_call_context()))

    def start(self, prep_id: uuid.UUID) -> None:
        super().start(prep_id)
        assert self.seen is not None
        self.seen.append(("start", current_call_context()))


@pytest.mark.parametrize("stage", ["classify", "ingest"])
def test_AI04_retry_starts_the_job_with_the_users_ai_context(
    signed_in: TestClient, repo: RetryRepo, stage: str
) -> None:
    """AC-7."""
    context_runner = ContextRunner(seen=[])
    app.dependency_overrides[materials_db_api.get_ingestion_runner] = lambda: context_runner
    row = failed_at_classify(repo) if stage == "classify" else failed_at_ingest(repo)

    response = retry(signed_in, row.id)

    assert response.status_code == 202, response.text
    expected = AICallContext(tenant_id=USER.tenant_id, user_id=USER.user_id)
    call = "classify" if stage == "classify" else "start"
    assert context_runner.seen == [(call, expected)]


# --- AC-8 · the database is down --------------------------------------------------------------


@pytest.mark.parametrize("where", ["read", "update"])
def test_CM07_retry_db_down_is_503(
    signed_in: TestClient, repo: RetryRepo, runner: FakeRunner, where: str
) -> None:
    """AC-8."""
    row = failed_at_classify(repo)
    if where == "read":
        repo.down = True
    else:
        repo.down_on_retry = True

    response = retry(signed_in, row.id)

    assert_error(response, 503, "db_unavailable")
    assert nothing_started(runner)


# --- AC-9 to AC-11 · token and path ---------------------------------------------------------


def test_CM07_retry_without_token_keeps_the_stub(
    client: TestClient, repo: RetryRepo, storage: FakeStorage, runner: FakeRunner
) -> None:
    """AC-9: AUTH_REQUIRED=false (conftest) and no token."""
    response = retry(client, uuid.uuid4())

    assert response.status_code == 202, response.text
    assert response.headers.get("x-stub") == "true"
    assert response.json()["status"] == "uploaded"
    assert repo.calls == []
    assert nothing_started(runner)


class RefusingVerifier:
    async def verify(self, token: str) -> Any:
        raise InvalidTokenError("bad signature")


@pytest.mark.parametrize(
    ("required", "token", "code"),
    [
        (True, None, "missing_token"),
        (True, "bad", "invalid_token"),
        (False, "bad", "invalid_token"),
    ],
    ids=["required-no-token", "required-bad-token", "optional-bad-token"],
)
def test_CM07_retry_auth_errors(
    client: TestClient,
    repo: RetryRepo,
    runner: FakeRunner,
    required: bool,
    token: str | None,
    code: str,
) -> None:
    """AC-10: the real get_auth with a verifier that refuses every token (no network)."""
    app.dependency_overrides[get_auth_required] = lambda: required
    app.dependency_overrides[get_verifier] = lambda: RefusingVerifier()
    row = failed_at_classify(repo)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    response = client.post(f"/materials/{row.id}/retry", headers=headers)

    assert_error(response, 401, code)
    assert repo.calls == []
    assert nothing_started(runner)


def test_CM07_retry_bad_id_is_422(signed_in: TestClient, repo: RetryRepo) -> None:
    """AC-11."""
    response = retry(signed_in, "not-a-uuid")

    assert_error(response, 422, "validation_error")
    assert repo.calls == []
