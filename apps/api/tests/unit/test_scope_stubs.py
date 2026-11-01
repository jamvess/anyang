"""Stub-only checks for the scope review endpoints. Delete this file with app/stubs/scope*.json
when the real endpoints exist.

Contract checks that the real endpoints must also pass are in test_scope_api_contract.py.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app

PREP_ID = "00000000-0000-4000-8000-000000000001"
TOPIC_ID = "00000000-0000-4000-8000-000000000003"

SCOPE_ENDPOINTS = [
    ("get", f"/exam-preps/{PREP_ID}/scope"),
    ("get", f"/topics/{TOPIC_ID}/sources"),
    ("post", f"/exam-preps/{PREP_ID}/scope/confirm"),
]

# May's fixtures, which the scope page tests use (specs/features/scope/scope-review.md §4).
WEB_FIXTURES = Path(__file__).resolve().parents[3] / "apps" / "web" / "tests" / "fixtures" / "scope"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def _without_ids(value: Any) -> Any:
    """The web fixtures use ids like "t3"; the API sends uuids. Compare everything else."""
    if isinstance(value, dict):
        return {k: _without_ids(v) for k, v in value.items() if k != "id"}
    if isinstance(value, list):
        return [_without_ids(v) for v in value]
    return value


def _web_fixture(name: str) -> Any:
    return json.loads((WEB_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(("method", "url"), SCOPE_ENDPOINTS)
def test_apimd_scope_stubs_send_x_stub_header(client: TestClient, method: str, url: str) -> None:
    response = client.request(method.upper(), url)

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"


def test_apimd_scope_stub_matches_web_fixture(client: TestClient) -> None:
    scope = client.get(f"/exam-preps/{PREP_ID}/scope").json()

    assert _without_ids(scope) == _without_ids(_web_fixture("scope-s12.json"))


def test_apimd_scope_sources_stub_matches_web_fixture(client: TestClient) -> None:
    sources = client.get(f"/topics/{TOPIC_ID}/sources").json()

    assert _without_ids(sources) == _without_ids(_web_fixture("sources-t3.json"))
