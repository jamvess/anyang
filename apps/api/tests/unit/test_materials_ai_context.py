"""Background AI calls of the material endpoints carry the tenant and user of the token, so their
`ai_calls` rows are not null (specs/features/exam-prep/materials-db.md §2.4 item 6, §2.6 item 6
· AC-28 · AI-04 · ai-calls-log.md §2.1).

Found on the first live run on Vertex (2026-11-17): the rows of classify_material had tenant_id
and user_id null. Kept apart from test_materials_db_api.py, whose tests were already reviewed;
the fakes come from there unchanged.
"""

import asyncio
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.services.ingestion as ingestion
from app.ai.call_context import AICallContext, ai_call_context, current_call_context
from app.auth import get_auth
from app.db.materials import get_material_repository
from app.main import app
from app.services.ingestion import IngestionRunner, get_ingestion_runner
from app.services.material_storage import get_material_storage
from tests.unit.test_materials_db_api import (
    PREP,
    USER,
    FakeRepo,
    FakeStorage,
    classified,
    waiting,
)

EXPECTED = AICallContext(tenant_id=USER.tenant_id, user_id=USER.user_id)


@dataclass
class ContextRunner:
    """Records the AI call context at the moment the router hands work to the runner."""

    seen: list[tuple[str, AICallContext | None]] = field(default_factory=list)

    def classify(self, material_id: uuid.UUID) -> None:
        self.seen.append(("classify", current_call_context()))

    def start(self, prep_id: uuid.UUID) -> None:
        self.seen.append(("start", current_call_context()))


@pytest.fixture
def setup() -> Iterator[tuple[TestClient, FakeRepo, FakeStorage, ContextRunner]]:
    repo, storage, runner = FakeRepo(), FakeStorage(), ContextRunner()
    app.dependency_overrides[get_material_repository] = lambda: repo
    app.dependency_overrides[get_material_storage] = lambda: storage
    app.dependency_overrides[get_ingestion_runner] = lambda: runner
    app.dependency_overrides[get_auth] = lambda: USER
    try:
        with TestClient(app) as client:
            yield client, repo, storage, runner
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("endpoint", ["uploaded", "confirm"])
def test_AI04_background_ai_calls_carry_tenant_and_user(
    setup: tuple[TestClient, FakeRepo, FakeStorage, ContextRunner], endpoint: str
) -> None:
    client, repo, storage, runner = setup
    if endpoint == "uploaded":
        row = waiting(repo, storage)
        response = client.post(f"/materials/{row.id}/uploaded", json={})
    else:
        row = classified(repo)
        body = {"materials": [{"id": str(row.id), "kind": "sheet"}]}
        response = client.post(f"/exam-preps/{PREP}/materials/confirm", json=body)

    assert response.status_code == 202, response.text
    expected_call = "classify" if endpoint == "uploaded" else "start"
    assert runner.seen == [(expected_call, EXPECTED)]
    assert current_call_context() is None  # nothing leaks into the test's own context


async def test_AI04_classify_task_keeps_the_context_after_the_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real runner: the task made inside the request's context still has it once the
    request (the `with`) is over, because a task copies the context when it is created."""
    seen: list[AICallContext | None] = []
    released = asyncio.Event()

    async def fake_classify(material_id: uuid.UUID, deps: Any) -> None:
        await released.wait()  # runs only after the `with` below has ended
        seen.append(current_call_context())

    monkeypatch.setattr(ingestion, "classify_material", fake_classify)
    runner = IngestionRunner(deps=None)  # type: ignore[arg-type]  # fake_classify ignores deps

    with ai_call_context(USER.tenant_id, USER.user_id):
        task = runner.classify(uuid.uuid4())
    released.set()
    await task

    assert seen == [EXPECTED]
