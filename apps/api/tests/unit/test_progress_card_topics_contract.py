"""Contract tests for progress_card.topics[] (specs/system/api.md v1.4, part of #40).

`ProgressTopic` gives the web a generated type through `pnpm gen:api`, so the OpenAPI
schema is checked as well as validation. The enums repeat config/learning.yaml and the
check constraints of 0001_init.sql; the drift tests fail if either side changes alone.

The stars range is still open (api.md "รอตัดสิน" item 4): tests that depend on it are
skipped until May decides.
"""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, get_args

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import stubs
from app.main import app
from app.models.room import ProgressCardEvent, ProgressTopic
from app.settings import get_settings

MIGRATION = Path(__file__).resolve().parents[4] / "supabase" / "migrations" / "0001_init.sql"

FIELDS = {"id", "name", "stars", "level", "review_due", "origin"}

STARS_RANGE_OPEN = "stars range waits for api.md รอตัดสิน item 4 (May, PR #63)"


def topic(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "t1",
        "name": "ตัวประกอบร่วม",
        "stars": 2,
        "level": "weak",
        "review_due": False,
        "origin": "doc",
    } | overrides


def check_values(table: str, column: str) -> set[str]:
    """Values of `check (<column> in (...))` inside `create table public.<table>`."""
    sql = MIGRATION.read_text(encoding="utf-8")
    body = re.search(rf"create table public\.{table} \((.*?)\n\);", sql, re.S)
    assert body, f"table {table} not found in {MIGRATION.name}"
    check = re.search(rf"check \({column} in \(([^)]*)\)\)", body.group(1))
    assert check, f"check on {table}.{column} not found"
    return set(re.findall(r"'([^']*)'", check.group(1)))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def schemas(client: TestClient) -> dict[str, Any]:
    return client.get("/openapi.json").json()["components"]["schemas"]


# --- validation ----------------------------------------------------------------


def test_apimd_progress_card_topics_are_typed() -> None:
    card = ProgressCardEvent.model_validate(
        {
            "days_left": 5,
            "passed": 0,
            "total": 1,
            "readiness": 0.0,
            "topics": [topic()],
        }
    )
    assert isinstance(card.topics[0], ProgressTopic)


def test_apimd_progress_card_stub_fixtures_pass() -> None:
    cards = [m["card"] for m in stubs.room()["messages"] if m["role"] == "card"]
    cards += [data for name, data in stubs.events("session_start") if name == "progress_card"]
    assert cards
    for card in cards:
        ProgressCardEvent.model_validate(card)


@pytest.mark.parametrize("level", ["not_started", "weak", "developing", "passed"])
def test_apimd_progress_card_accepts_each_level(level: str) -> None:
    assert ProgressTopic.model_validate(topic(level=level)).level == level


@pytest.mark.parametrize("origin", ["doc", "user"])
def test_apimd_progress_card_accepts_each_origin(origin: str) -> None:
    assert ProgressTopic.model_validate(topic(origin=origin)).origin == origin


@pytest.mark.parametrize(
    "overrides",
    [
        {"level": "mystery"},
        {"level": None},
        {"origin": "ai"},
        {"origin": None},
        {"stars": None},  # never null: topics without importance are left out
        {"stars": 4},
        {"stars": -1},
        {"stars": 2.5},
        {"review_due": None},
        {"extra": 1},
    ],
    ids=lambda o: ",".join(f"{k}={v}" for k, v in o.items()),
)
def test_apimd_progress_card_rejects_bad_topic(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ProgressTopic.model_validate(topic(**overrides))


@pytest.mark.parametrize("field", sorted(FIELDS))
def test_apimd_progress_card_topic_field_required(field: str) -> None:
    data = topic()
    del data[field]
    with pytest.raises(ValidationError):
        ProgressTopic.model_validate(data)


def test_apimd_progress_card_three_stars_accepted() -> None:
    assert ProgressTopic.model_validate(topic(stars=3)).stars == 3


@pytest.mark.skip(reason=STARS_RANGE_OPEN)
def test_apimd_progress_card_zero_stars() -> None:
    # 0-3: accepted · 1-3: rejected. Write the assertion once May answers.
    raise NotImplementedError


# --- drift against config and the database --------------------------------------


def test_apimd_progress_card_level_matches_learning_yaml() -> None:
    level = ProgressTopic.model_fields["level"].annotation
    assert list(get_args(level)) == get_settings().learning.levels.show


def test_apimd_progress_card_level_matches_db_check() -> None:
    level = ProgressTopic.model_fields["level"].annotation
    assert set(get_args(level)) == check_values("topic_progress", "level")


def test_apimd_progress_card_origin_matches_db_check() -> None:
    origin = ProgressTopic.model_fields["origin"].annotation
    assert set(get_args(origin)) == check_values("topics", "origin")


# --- OpenAPI (what pnpm gen:api sees) --------------------------------------------


def test_apimd_progress_card_topics_ref_progress_topic(schemas: dict[str, Any]) -> None:
    items = schemas["ProgressCardEvent"]["properties"]["topics"]["items"]
    assert items == {"$ref": "#/components/schemas/ProgressTopic"}


def test_apimd_progress_topic_schema_fields(schemas: dict[str, Any]) -> None:
    schema = schemas["ProgressTopic"]
    assert set(schema["properties"]) == FIELDS
    assert set(schema["required"]) == FIELDS
    assert schema["additionalProperties"] is False


def test_apimd_progress_topic_stars_is_plain_integer(schemas: dict[str, Any]) -> None:
    # number, not number | null, in the generated type
    stars = schemas["ProgressTopic"]["properties"]["stars"]
    assert stars["type"] == "integer"
    assert "anyOf" not in stars
    assert stars["maximum"] == 3


def test_apimd_progress_topic_enums(schemas: dict[str, Any]) -> None:
    props = schemas["ProgressTopic"]["properties"]
    assert props["level"]["enum"] == get_settings().learning.levels.show
    assert set(props["origin"]["enum"]) == {"doc", "user"}
