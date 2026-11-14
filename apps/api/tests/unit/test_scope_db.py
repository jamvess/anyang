"""The scope page with a token: topics with stars, sources, confirm
(specs/features/scope/scope-db.md · AC-1 to AC-11).

No network. A fake scope repository holds the rows the user's JWT can see.

Interfaces these tests expect (to be built by /implement-feature), in `app/db/scope.py`:
- `get_scope_repository` (FastAPI dependency; None without a user, so the stubs stay)
- `ScopeRepository` with the methods of `FakeScopeRepo` below; the records it returns have the
  attributes of the dataclasses below (`ScopePrep`, `TopicRow`, `SourceRange`, `QuestionRow`,
  `VersionRow`)
- `VersionTakenError`: `add_version` raises it when (exam_prep_id, version) exists
"""

import importlib
import uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.db.exam_preps import DbUnavailableError
from app.domain.exam_prep import bangkok_today, days_left
from app.main import app
from tests.unit import test_room_sessions_api as room_api
from tests.unit.test_room_sessions_api import NOW, USER

client = room_api.client
fake = room_api.fake
repo = room_api.repo
signed_in = room_api.signed_in

PREP_ID = uuid.uuid4()
SHEET_1 = uuid.uuid4()
SHEET_3 = uuid.uuid4()
EXAM = uuid.uuid4()


@dataclass(frozen=True)
class ScopePrep:
    id: uuid.UUID
    title: str
    exam_date: date
    active_scope_version_id: uuid.UUID | None


@dataclass(frozen=True)
class TopicRow:
    id: uuid.UUID
    exam_prep_id: uuid.UUID
    name: str
    order_index: int
    importance: int | None
    importance_reason: str | None
    status: str
    origin: str


@dataclass(frozen=True)
class SourceRange:
    topic_id: uuid.UUID
    material_id: uuid.UUID
    file_name: str
    material_created_at: datetime
    page_from: int
    page_to: int


@dataclass(frozen=True)
class QuestionRow:
    id: uuid.UUID
    material_id: uuid.UUID
    file_name: str
    material_created_at: datetime
    q_no: str
    page_no: int | None
    text: str
    map_note: str | None
    topic_id: uuid.UUID | None


@dataclass(frozen=True)
class VersionRow:
    id: uuid.UUID
    version: int
    confirmed_at: datetime | None


class VersionTaken(Exception):
    pass


LIMIT = TopicRow(uuid.uuid4(), PREP_ID, "ลิมิต", 1, 3, "ออกข้อสอบทุกปี", "draft", "doc")
FACTOR = TopicRow(uuid.uuid4(), PREP_ID, "แยกตัวประกอบ", 2, 2, "ออกบางปี", "draft", "doc")
GRAPH = TopicRow(uuid.uuid4(), PREP_ID, "กราฟ", 3, 0, "ไม่อยู่ในขอบเขต", "excluded", "doc")
MINE = TopicRow(uuid.uuid4(), PREP_ID, "หัวข้อที่เพิ่มเอง", 4, 1, None, "draft", "user")


def at(minutes: int) -> datetime:
    return NOW + timedelta(minutes=minutes)


@dataclass
class FakeScopeRepo:
    preps: dict[uuid.UUID, ScopePrep] = field(
        default_factory=lambda: {
            PREP_ID: ScopePrep(PREP_ID, "MTH10101 Calculus I", date(2026, 12, 8), None)
        }
    )
    topics: list[TopicRow] = field(default_factory=lambda: [LIMIT, FACTOR, GRAPH, MINE])
    sources: list[SourceRange] = field(
        default_factory=lambda: [
            SourceRange(LIMIT.id, SHEET_3, "sheet-03.pdf", at(2), 1, 2),
            SourceRange(LIMIT.id, SHEET_1, "sheet-01.pdf", at(1), 30, 30),
            SourceRange(LIMIT.id, SHEET_1, "sheet-01.pdf", at(1), 2, 26),
            SourceRange(FACTOR.id, SHEET_1, "sheet-01.pdf", at(1), 2, 3),
            SourceRange(FACTOR.id, SHEET_1, "sheet-01.pdf", at(1), 3, 4),
        ]
    )
    questions: list[QuestionRow] = field(
        default_factory=lambda: [
            QuestionRow(uuid.uuid4(), EXAM, "final-2566.pdf", at(3), "10", 2, "ข้อสิบ", None, None),
            QuestionRow(
                uuid.uuid4(), EXAM, "final-2566.pdf", at(3), "2", 1, "ข้อสอง", "ไม่ตรง", None
            ),
            QuestionRow(
                uuid.uuid4(), EXAM, "final-2566.pdf", at(3), "1", 1, "ลิมิต", "ตรง", LIMIT.id
            ),
        ]
    )
    pages_text: dict[tuple[uuid.UUID, int], str] = field(
        default_factory=lambda: {(SHEET_1, n): f"หน้า {n}" for n in range(1, 40)}
    )
    versions: dict[uuid.UUID, list[VersionRow]] = field(default_factory=dict)
    changes_at: list[datetime] = field(default_factory=list)
    added: list[dict[str, Any]] = field(default_factory=list)
    down: bool = False
    lose_the_race: bool = False

    def _touch(self) -> None:
        if self.down:
            raise DbUnavailableError("down")

    def get_prep(self, prep_id):
        self._touch()
        return self.preps.get(prep_id)

    def list_topics(self, prep_id):
        self._touch()
        return sorted(
            (t for t in self.topics if t.exam_prep_id == prep_id), key=lambda t: t.order_index
        )

    def list_sources(self, prep_id):
        ids = {t.id for t in self.topics if t.exam_prep_id == prep_id}
        return [s for s in self.sources if s.topic_id in ids]

    def list_questions(self, prep_id):
        return list(self.questions)

    def scope_version(self, version_id):
        rows = [v for vs in self.versions.values() for v in vs if v.id == version_id]
        return rows[0] if rows else None

    def has_changes_after(self, prep_id, after):
        return any(c > after for c in self.changes_at)

    def latest_version(self, prep_id):
        return max((v.version for v in self.versions.get(prep_id, [])), default=0)

    def add_version(self, **fields):
        if self.lose_the_race:
            raise importlib.import_module("app.db.scope").VersionTakenError("taken")
        self.added.append(dict(fields))
        row = VersionRow(uuid.uuid4(), fields["version"], fields["confirmed_at"])
        self.versions.setdefault(fields["exam_prep_id"], []).append(row)
        return row.id

    def set_active_version(self, prep_id, version_id):
        self.preps[prep_id] = replace(self.preps[prep_id], active_scope_version_id=version_id)

    def confirm_topics(self, prep_id):
        self.topics = [
            replace(t, status="confirmed")
            if t.exam_prep_id == prep_id and t.status == "draft"
            else t
            for t in self.topics
        ]

    def get_topic(self, topic_id):
        self._touch()
        return next((t for t in self.topics if t.id == topic_id), None)

    def pages(self, material_id, page_nos):
        return {
            n: self.pages_text[(material_id, n)]
            for n in page_nos
            if (material_id, n) in self.pages_text
        }


@dataclass
class Scope:
    client: TestClient
    repo: FakeScopeRepo

    def get(self, prep_id=PREP_ID) -> Any:
        return self.client.get(f"/exam-preps/{prep_id}/scope")

    def confirm(self, prep_id=PREP_ID) -> Any:
        return self.client.post(f"/exam-preps/{prep_id}/scope/confirm")

    def sources(self, topic_id) -> Any:
        return self.client.get(f"/topics/{topic_id}/sources")


@pytest.fixture
def scope(signed_in) -> Scope:
    store = FakeScopeRepo()
    dependency = importlib.import_module("app.db.scope").get_scope_repository
    app.dependency_overrides[dependency] = lambda: store
    return Scope(signed_in, store)


def topic(body: dict[str, Any], row: TopicRow) -> dict[str, Any]:
    return next(t for t in body["topics"] if t["id"] == str(row.id))


# --- GET /scope ---------------------------------------------------------------------------------


def test_SM02_SM03_the_scope_comes_from_the_database(scope: Scope):
    # AC-1
    response = scope.get()

    assert response.status_code == 200
    assert "X-Stub" not in response.headers
    body = response.json()
    assert [t["id"] for t in body["topics"]] == [str(t.id) for t in (LIMIT, FACTOR, GRAPH, MINE)]
    assert topic(body, LIMIT) | {"source_label": None} == {
        "id": str(LIMIT.id),
        "order": 1,
        "name": "ลิมิต",
        "stars": 3,
        "reason": "ออกข้อสอบทุกปี",
        "source_label": None,
        "origin": "doc",
    }
    assert topic(body, GRAPH)["stars"] == 0
    assert topic(body, MINE)["reason"] == ""
    assert body["status"] == "draft"
    assert body["prep_name"] == "MTH10101 Calculus I"
    assert body["days_left"] == days_left(date(2026, 12, 8), today=bangkok_today(NOW))


def test_SM04_source_label_in_file_then_page_order(scope: Scope):
    # AC-2
    body = scope.get().json()

    assert topic(body, LIMIT)["source_label"] == "sheet-01 น.2–26, sheet-01 น.30, sheet-03 น.1–2"  # noqa: RUF001
    assert topic(body, MINE)["source_label"] == ""


def test_SM04_unmapped_questions_only_in_number_order(scope: Scope):
    # AC-3
    body = scope.get().json()

    assert [(q["label"], q["text"], q["map_note"]) for q in body["unmapped_questions"]] == [
        ("final-2566 ข้อ 2", "ข้อสอง", "ไม่ตรง"),
        ("final-2566 ข้อ 10", "ข้อสิบ", None),
    ]


@pytest.mark.parametrize("missing", ["no_topics", "stars_not_ready"])
def test_SM03_a_scope_not_ready_is_409(scope: Scope, missing):
    # AC-4
    if missing == "no_topics":
        scope.repo.topics = []
    else:
        scope.repo.topics = [LIMIT, replace(FACTOR, importance=None)]

    for response in (scope.get(), scope.confirm()):
        room_api.assert_error(response, 409, "scope_not_ready")
    assert scope.repo.added == []


# --- GET /topics/{id}/sources -------------------------------------------------------------------


def test_SM04_sources_are_the_pages_of_the_topic_once_each(scope: Scope):
    # AC-5
    response = scope.sources(FACTOR.id)

    assert response.status_code == 200
    body = response.json()
    assert [(e["material_name"], e["page"], e["text"]) for e in body["excerpts"]] == [
        ("sheet-01.pdf", 2, "หน้า 2"),
        ("sheet-01.pdf", 3, "หน้า 3"),
        ("sheet-01.pdf", 4, "หน้า 4"),
    ]
    assert body["questions"] == []
    limit = scope.sources(LIMIT.id).json()
    assert [q["label"] for q in limit["questions"]] == ["final-2566 ข้อ 1"]
    assert scope.sources(MINE.id).json()["excerpts"] == []
    room_api.assert_error(scope.sources(uuid.uuid4()), 404, "not_found")


# --- POST /scope/confirm ------------------------------------------------------------------------


def test_SM09_confirming_writes_a_version_and_confirms_the_topics(scope: Scope):
    # AC-6
    response = scope.confirm()

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    [fields] = scope.repo.added
    assert (fields["tenant_id"], fields["exam_prep_id"], fields["version"]) == (
        USER.tenant_id,
        PREP_ID,
        1,
    )
    assert fields["status"] == "confirmed" and fields["confirmed_at"] is not None
    assert [(t["topic_id"], t["status"]) for t in fields["snapshot"]] == [
        (str(LIMIT.id), "confirmed"),
        (str(FACTOR.id), "confirmed"),
        (str(GRAPH.id), "excluded"),
        (str(MINE.id), "confirmed"),
    ]
    prep = scope.repo.preps[PREP_ID]
    assert str(prep.active_scope_version_id) == body["scope_version_id"]
    assert {t.name: t.status for t in scope.repo.topics} == {
        "ลิมิต": "confirmed",
        "แยกตัวประกอบ": "confirmed",
        "กราฟ": "excluded",
        "หัวข้อที่เพิ่มเอง": "confirmed",
    }
    assert scope.get().json()["status"] == "confirmed"


def test_SM09_a_confirmed_scope_cannot_be_confirmed_again(scope: Scope):
    # AC-7
    scope.confirm()

    response = scope.confirm()

    room_api.assert_error(response, 409, "scope_already_confirmed")
    assert len(scope.repo.added) == 1


def test_SM09_a_change_after_confirming_makes_it_a_draft_again(scope: Scope):
    # AC-8
    scope.confirm()
    scope.repo.changes_at.append(NOW + timedelta(days=1))

    assert scope.get().json()["status"] == "draft"
    assert scope.confirm().json()["version"] == 2


def test_SM09_no_topic_left_is_scope_empty(scope: Scope):
    # AC-9
    scope.repo.topics = [GRAPH, replace(LIMIT, importance=0)]

    room_api.assert_error(scope.confirm(), 409, "scope_empty")


def test_SM09_a_version_taken_by_another_request_is_409(scope: Scope):
    # AC-10
    scope.repo.lose_the_race = True

    response = scope.confirm()

    room_api.assert_error(response, 409, "scope_already_confirmed")
    assert scope.repo.preps[PREP_ID].active_scope_version_id is None


# --- errors -------------------------------------------------------------------------------------


def test_SA06_a_prep_that_is_not_there_is_404(scope: Scope):
    # AC-11
    other = uuid.uuid4()

    room_api.assert_error(scope.get(other), 404, "not_found")
    room_api.assert_error(scope.confirm(other), 404, "not_found")


def test_SA06_a_database_that_is_down_is_503(scope: Scope):
    # AC-11
    scope.repo.down = True

    room_api.assert_error(scope.get(), 503, "db_unavailable")
    room_api.assert_error(scope.confirm(), 503, "db_unavailable")
    room_api.assert_error(scope.sources(LIMIT.id), 503, "db_unavailable")
