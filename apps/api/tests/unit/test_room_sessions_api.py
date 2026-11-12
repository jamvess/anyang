"""The tutor room on the database, with a fake repository and the fake AI provider
(specs/features/tutor/room-sessions-db.md · api.md v1.15 "บันทึกลง DB").

No network. Dependencies replaced here: `get_room_repository` (FakeRoomRepo), `get_auth`
(a fixed user, for "a valid token"), `get_now` (2026-11-11 12:00 in Bangkok), `get_gateway`
(FakeProvider) and, per test, `get_auth_required` and `get_local_mode`.

Interfaces these tests expect (to be built by /implement-feature):
- `app.db.room`: `RoomRepository` protocol and `get_room_repository` (dependency), records
  `PrepRecord`, `SessionRecord`, `MessageRecord`, `ProfileFacts`
- `app.db.exam_preps.DbUnavailableError` (reused)
- `app.domain.room`: `BuddyFacts`, `greeting_text`, `FALLBACK_USER_NAME`
- `app.models.room.DoneEvent.message_ids: list[UUID]` (default [], as api.md "SSE events")
"""

import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.ai.gateway as gateway_module
from app.ai.call_context import current_call_context
from app.ai.gateway import Gateway, get_gateway
from app.ai.providers.fake import FakeProvider
from app.auth import AuthContext, get_auth, get_auth_required
from app.clock import get_now
from app.db.exam_preps import DbUnavailableError
from app.db.room import (
    MessageRecord,
    PrepRecord,
    ProfileFacts,
    SessionRecord,
    get_room_repository,
)
from app.domain.room import BuddyFacts, greeting_text
from app.main import app
from app.services.dev_uploads import get_local_mode
from app.settings import get_settings
from tests.unit.test_tutor_reply_stream_api import parse_sse, tokens

NOW = datetime(2026, 11, 11, 5, 0, tzinfo=UTC)  # 12:00 in Bangkok
TODAY = date(2026, 11, 11)
USER = AuthContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), token="test-token")
PREP_ID = uuid.uuid4()
OTHER_PREP_ID = uuid.uuid4()
DEGRADE_TEXT = "ระบบช้า ลองส่งอีกทีนะ"
DB_DOWN = {"error": {"code": "db_unavailable", "message": "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง"}}
N_TURNS = get_settings().learning.session.context_recent_turns


@dataclass
class FakeRoomRepo:
    """Rows the user can see through RLS. Anything not here is another tenant's or missing."""

    preps: dict[uuid.UUID, PrepRecord] = field(default_factory=dict)
    sessions: dict[uuid.UUID, SessionRecord] = field(default_factory=dict)
    messages: dict[uuid.UUID, list[MessageRecord]] = field(default_factory=dict)
    profile: ProfileFacts = field(
        default_factory=lambda: ProfileFacts(nickname=None, tutor_params=None, buddy=None)
    )
    calls: int = 0
    down: bool = False
    fail_insert_role: str | None = None
    created_sessions: list[dict[str, Any]] = field(default_factory=list)

    def _touch(self) -> None:
        self.calls += 1
        if self.down:
            raise DbUnavailableError("down")

    def get_prep(self, prep_id: uuid.UUID) -> PrepRecord | None:
        self._touch()
        return self.preps.get(prep_id)

    def create_session(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        exam_prep_id: uuid.UUID,
        scope_version_id: uuid.UUID | None,
    ) -> SessionRecord:
        self._touch()
        self.created_sessions.append(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "exam_prep_id": exam_prep_id,
                "scope_version_id": scope_version_id,
            }
        )
        record = SessionRecord(
            id=uuid.uuid4(), exam_prep_id=exam_prep_id, started_at=NOW, ended_at=None
        )
        self.sessions[record.id] = record
        self.messages[record.id] = []
        return record

    def latest_open_session(self, prep_id: uuid.UUID) -> SessionRecord | None:
        self._touch()
        open_ones = [
            s for s in self.sessions.values() if s.exam_prep_id == prep_id and s.ended_at is None
        ]
        return max(open_ones, key=lambda s: s.started_at, default=None)

    def get_session(self, session_id: uuid.UUID) -> SessionRecord | None:
        self._touch()
        return self.sessions.get(session_id)

    def list_messages(self, session_id: uuid.UUID) -> list[MessageRecord]:
        self._touch()
        return list(self.messages.get(session_id, []))

    def add_message(
        self,
        *,
        tenant_id: uuid.UUID,
        session_id: uuid.UUID,
        role: str,
        content: str,
        input_mode: str | None,
    ) -> MessageRecord:
        self._touch()
        if self.fail_insert_role == role:
            raise DbUnavailableError("insert failed")
        stamp = NOW + timedelta(seconds=len(self.messages[session_id]))
        record = MessageRecord(
            id=uuid.uuid4(),
            role=role,
            content=content,
            card=None,
            input_mode=input_mode,
            attachment_path=None,
            attachment_name=None,
            created_at=stamp,
        )
        self.messages[session_id].append(record)
        return record

    def profile_facts(self) -> ProfileFacts:
        self._touch()
        return self.profile

    # helpers for tests
    def add_session(self, prep_id: uuid.UUID = PREP_ID, **change: Any) -> SessionRecord:
        data: dict[str, Any] = {
            "id": uuid.uuid4(),
            "exam_prep_id": prep_id,
            "started_at": NOW,
            "ended_at": None,
            **change,
        }
        record = SessionRecord(**data)
        self.sessions[record.id] = record
        self.messages[record.id] = []
        return record

    def seed(self, session: SessionRecord, lines: list[tuple[str, str]]) -> None:
        for role, text in lines:
            self.add_message(
                tenant_id=USER.tenant_id,
                session_id=session.id,
                role=role,
                content=text,
                input_mode="text" if role == "user" else None,
            )
        self.calls = 0


def prep_record(**change: Any) -> PrepRecord:
    data: dict[str, Any] = {
        "id": PREP_ID,
        "title": "แคลคูลัส 1 กลางภาค",
        "exam_date": TODAY + timedelta(days=27),
        "active_scope_version_id": None,
        **change,
    }
    return PrepRecord(**data)


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)


@pytest.fixture
def repo() -> FakeRoomRepo:
    return FakeRoomRepo(preps={PREP_ID: prep_record()})


@pytest.fixture
def fake() -> FakeProvider:
    return FakeProvider({}, defaults={"tutor_reply": "ตอบจากติวเตอร์"})


def gateway_of(fake: FakeProvider) -> Gateway:
    config = get_settings().ai
    config = config.model_copy(update={"gateway": config.gateway.model_copy(update={"retries": 0})})
    return Gateway(config=config, prompts_dir=get_settings().env.prompts_dir, provider=fake)


@pytest.fixture
def client(repo: FakeRoomRepo, fake: FakeProvider) -> Iterator[TestClient]:
    """No token, AUTH_REQUIRED=false (conftest), not local, unless a test overrides more."""
    app.dependency_overrides[get_room_repository] = lambda: repo
    app.dependency_overrides[get_now] = lambda: NOW
    app.dependency_overrides[get_gateway] = lambda: gateway_of(fake)
    app.dependency_overrides[get_local_mode] = lambda: False
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def signed_in(client: TestClient) -> TestClient:
    app.dependency_overrides[get_auth] = lambda: USER
    return client


def send(client: TestClient, session_id: uuid.UUID, text: str = "อธิบายหน่อย") -> Any:
    return client.post(f"/sessions/{session_id}/messages", json={"text": text})


def assert_error(response: Any, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def expected_greeting(user_name: str | None, days_left: int = 27) -> str:
    return greeting_text(
        get_settings().messages.room_greeting,
        user_name=user_name,
        prep_name="แคลคูลัส 1 กลางภาค",
        days_left=days_left,
    )


# --- three auth cases (§2.1) ------------------------------------------------------------

READS = ["active", "room", "messages"]


def call(client: TestClient, which: str, session_id: uuid.UUID) -> Any:
    return {
        "active": lambda: client.get(f"/exam-preps/{PREP_ID}/sessions/active"),
        "open": lambda: client.post(f"/exam-preps/{PREP_ID}/sessions"),
        "room": lambda: client.get(f"/sessions/{session_id}"),
        "messages": lambda: client.get(f"/sessions/{session_id}/messages"),
        "send": lambda: send(client, session_id),
    }[which]()


ALL = ["active", "open", "room", "messages", "send"]


@pytest.mark.parametrize("which", ALL)
def test_SA06_no_token_with_auth_required_is_401_never_stub(
    client: TestClient, repo: FakeRoomRepo, fake: FakeProvider, which: str
) -> None:
    """AC-auth-required."""
    app.dependency_overrides[get_auth_required] = lambda: True
    session = repo.add_session()

    response = call(client, which, session.id)

    assert_error(response, 401, "missing_token")
    assert "x-stub" not in response.headers
    assert repo.calls == 0
    assert fake.requests == []


@pytest.mark.parametrize("which", READS)
def test_SA06_no_token_without_auth_required_keeps_the_stub(
    client: TestClient, repo: FakeRoomRepo, which: str
) -> None:
    """AC-auth-stub: the old stub answers, the repository is untouched."""
    response = call(client, which, uuid.uuid4())

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"
    assert repo.calls == 0


@pytest.mark.parametrize("which", ["open", "send"])
def test_SA06_no_token_without_auth_required_streams_without_the_database(
    client: TestClient, repo: FakeRoomRepo, which: str
) -> None:
    """AC-auth-stub for the two SSE endpoints."""
    response = call(client, which, uuid.uuid4())

    assert response.status_code == 200
    assert repo.calls == 0


@pytest.mark.parametrize("required", [True, False])
@pytest.mark.parametrize("local", [True, False])
@pytest.mark.parametrize("which", ALL)
def test_TM13_with_a_token_uses_the_database(
    signed_in: TestClient,
    repo: FakeRoomRepo,
    required: bool,
    local: bool,
    which: str,
) -> None:
    """AC-auth-real: AUTH_REQUIRED either way, on a dev machine too."""
    app.dependency_overrides[get_auth_required] = lambda: required
    app.dependency_overrides[get_local_mode] = lambda: local
    session = repo.add_session()

    response = call(signed_in, which, session.id)

    assert response.status_code == 200, response.text
    assert "x-stub" not in response.headers
    assert repo.calls > 0


# --- open a session (§2.4) ----------------------------------------------------------------


def test_TM13_open_saves_a_session_and_the_greeting(
    signed_in: TestClient, repo: FakeRoomRepo, fake: FakeProvider
) -> None:
    """AC-1, AC-4: session → token → done, no progress_card or problem, greeting from config,
    no AI call."""
    response = signed_in.post(f"/exam-preps/{PREP_ID}/sessions")

    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[0] == "session" and names[-1] == "done"
    assert set(names) == {"session", "token", "done"}
    session_id = uuid.UUID(events[0][1]["session_id"])
    assert repo.created_sessions == [
        {
            "tenant_id": USER.tenant_id,
            "user_id": USER.user_id,
            "exam_prep_id": PREP_ID,
            "scope_version_id": None,
        }
    ]
    assert session_id in repo.sessions
    greeting = "".join(tokens(events))
    assert greeting == expected_greeting(None)
    [saved] = repo.messages[session_id]
    assert (saved.role, saved.content, saved.input_mode) == ("tutor", greeting, None)
    assert events[-1][1] == {"message_ids": [str(saved.id)]}
    assert fake.requests == []


def test_TM13_open_greets_by_nickname(signed_in: TestClient, repo: FakeRoomRepo) -> None:
    """AC-4 with a nickname (hello_named)."""
    repo.profile = ProfileFacts(nickname="ปาล", tutor_params=None, buddy=None)

    events = parse_sse(signed_in.post(f"/exam-preps/{PREP_ID}/sessions").text)

    assert "".join(tokens(events)) == expected_greeting("ปาล")


def test_TM13_open_attaches_the_active_scope_version(
    signed_in: TestClient, repo: FakeRoomRepo
) -> None:
    """AC-2: still no progress_card in this feature."""
    version = uuid.uuid4()
    repo.preps[PREP_ID] = prep_record(active_scope_version_id=version)

    events = parse_sse(signed_in.post(f"/exam-preps/{PREP_ID}/sessions").text)

    assert repo.created_sessions[0]["scope_version_id"] == version
    assert "progress_card" not in [name for name, _ in events]


def test_SA06_open_on_a_missing_or_foreign_prep_is_404(
    signed_in: TestClient, repo: FakeRoomRepo
) -> None:
    """AC-3."""
    response = signed_in.post(f"/exam-preps/{OTHER_PREP_ID}/sessions")

    assert_error(response, 404, "not_found")
    assert repo.created_sessions == []


def test_TM13_greeting_not_saved_still_opens_the_room(
    signed_in: TestClient, repo: FakeRoomRepo
) -> None:
    """AC-5."""
    repo.fail_insert_role = "tutor"

    events = parse_sse(signed_in.post(f"/exam-preps/{PREP_ID}/sessions").text)

    assert events[-1] == ("done", {"message_ids": []})
    assert len(repo.created_sessions) == 1


# --- active session (§2.3) ---------------------------------------------------------------


def test_TM13_active_is_the_latest_open_session(signed_in: TestClient, repo: FakeRoomRepo) -> None:
    """AC-6, AC-9."""
    repo.add_session(started_at=NOW - timedelta(hours=2))
    latest = repo.add_session(started_at=NOW - timedelta(hours=1))
    repo.add_session(started_at=NOW, ended_at=NOW)  # ended
    repo.preps[OTHER_PREP_ID] = prep_record(id=OTHER_PREP_ID)
    repo.add_session(prep_id=OTHER_PREP_ID, started_at=NOW)  # another prep of A

    response = signed_in.get(f"/exam-preps/{PREP_ID}/sessions/active")

    assert response.status_code == 200
    assert response.json() == {"session_id": str(latest.id)}


@pytest.mark.parametrize("ended", [True, False])
def test_TM13_no_open_session_is_404_no_active_session(
    signed_in: TestClient, repo: FakeRoomRepo, ended: bool
) -> None:
    """AC-7: every session ended, or none at all."""
    if ended:
        repo.add_session(ended_at=NOW)

    assert_error(signed_in.get(f"/exam-preps/{PREP_ID}/sessions/active"), 404, "no_active_session")


def test_SA06_active_of_a_missing_or_foreign_prep_is_not_found(signed_in: TestClient) -> None:
    """AC-8: not_found, not no_active_session."""
    assert_error(signed_in.get(f"/exam-preps/{OTHER_PREP_ID}/sessions/active"), 404, "not_found")


# --- room and history (§2.5, §2.6) ------------------------------------------------------


def test_TM13_room_header_and_history(signed_in: TestClient, repo: FakeRoomRepo) -> None:
    """AC-10, AC-11 (names with no profile)."""
    session = repo.add_session()
    repo.seed(session, [("tutor", "สวัสดี"), ("user", "q1"), ("tutor", "a1")])
    presets = signed_in.get("/personas/presets").json()

    body = signed_in.get(f"/sessions/{session.id}").json()

    assert body["session_id"] == str(session.id)
    assert body["prep_name"] == "แคลคูลัส 1 กลางภาค"
    assert body["days_left"] == 27
    assert body["user_name"] == "คุณ"
    assert body["tutor_name"] == presets["tutors"][0]["params"]["name"]
    assert body["buddy_name"] is None
    guards = get_settings().ai.guards
    assert body["limits"] == {
        "max_message_chars": guards.max_message_chars,
        "max_image_mb": guards.max_image_mb,
    }
    assert [(m["role"], m["content"]) for m in body["messages"]] == [
        ("tutor", "สวัสดี"),
        ("user", "q1"),
        ("tutor", "a1"),
    ]
    assert [m["input_mode"] for m in body["messages"]] == [None, "text", None]
    assert all(uuid.UUID(m["id"]) for m in body["messages"])
    assert signed_in.get(f"/sessions/{session.id}/messages").json() == body["messages"]


def test_TM13_room_names_come_from_the_profiles(signed_in: TestClient, repo: FakeRoomRepo) -> None:
    """AC-11 with profiles (each rule is in test_room_greeting.py)."""
    repo.profile = ProfileFacts(
        nickname="นนท์",
        tutor_params={"name": "พี่ฟ้า"},
        buddy=BuddyFacts(enabled=True, params={"name": "ต้นกล้า"}),
    )
    session = repo.add_session()

    body = signed_in.get(f"/sessions/{session.id}").json()

    assert (body["user_name"], body["tutor_name"], body["buddy_name"]) == ("นนท์", "พี่ฟ้า", "ต้นกล้า")


def test_TM13_ended_session_still_opens(signed_in: TestClient, repo: FakeRoomRepo) -> None:
    """AC-12."""
    session = repo.add_session(ended_at=NOW)
    repo.seed(session, [("user", "q1")])

    response = signed_in.get(f"/sessions/{session.id}")

    assert response.status_code == 200
    assert len(response.json()["messages"]) == 1


@pytest.mark.parametrize("path", ["", "/messages"])
def test_SA06_room_of_a_missing_or_foreign_session_is_404(signed_in: TestClient, path: str) -> None:
    """AC-13."""
    assert_error(signed_in.get(f"/sessions/{uuid.uuid4()}{path}"), 404, "not_found")


def test_TM13_empty_session_has_no_messages(signed_in: TestClient, repo: FakeRoomRepo) -> None:
    """AC-14."""
    session = repo.add_session()

    assert signed_in.get(f"/sessions/{session.id}").json()["messages"] == []
    assert signed_in.get(f"/sessions/{session.id}/messages").json() == []


# --- send a message (§2.7) ----------------------------------------------------------------


def test_TM13_user_message_is_saved_before_the_tutor_is_called(
    signed_in: TestClient, repo: FakeRoomRepo
) -> None:
    """AC-15, AC-23: the user row exists when the model is called; the tutor reply is saved;
    the AI call carries the session id."""
    session = repo.add_session()
    seen: dict[str, Any] = {}

    async def at_first_chunk() -> None:
        seen["roles"] = [m.role for m in repo.messages[session.id]]
        seen["context"] = current_call_context()

    fake = FakeProvider({"tutor_reply": [[at_first_chunk, "ผลต่าง", "กำลังสอง"]]})
    app.dependency_overrides[get_gateway] = lambda: gateway_of(fake)

    events = parse_sse(send(signed_in, session.id, "อธิบายหน่อย").text)

    assert seen["roles"] == ["user"]
    assert seen["context"].session_id == session.id
    assert seen["context"].tenant_id == USER.tenant_id
    user, tutor = repo.messages[session.id]
    assert (user.role, user.content, user.input_mode) == ("user", "อธิบายหน่อย", "text")
    assert (tutor.role, tutor.content, tutor.input_mode) == ("tutor", "ผลต่างกำลังสอง", None)
    assert events[-1] == ("done", {"message_ids": [str(tutor.id)]})


def test_TM13_degrade_text_is_saved_as_the_tutor(signed_in: TestClient, repo: FakeRoomRepo) -> None:
    """AC-16."""
    session = repo.add_session()
    fake = FakeProvider({"tutor_reply": [RuntimeError("down")]})
    app.dependency_overrides[get_gateway] = lambda: gateway_of(fake)

    events = parse_sse(send(signed_in, session.id).text)

    assert tokens(events) == [DEGRADE_TEXT]
    tutor = repo.messages[session.id][-1]
    assert (tutor.role, tutor.content) == ("tutor", DEGRADE_TEXT)
    assert events[-1] == ("done", {"message_ids": [str(tutor.id)]})


def test_TM13_failure_after_a_token_saves_no_tutor_message(
    signed_in: TestClient, repo: FakeRoomRepo
) -> None:
    """AC-17."""
    session = repo.add_session()
    fake = FakeProvider({"tutor_reply": [["ผลต่าง", RuntimeError("cut")]]})
    app.dependency_overrides[get_gateway] = lambda: gateway_of(fake)

    events = parse_sse(send(signed_in, session.id).text)

    assert "error" in [name for name, _ in events]
    assert [m.role for m in repo.messages[session.id]] == ["user"]


def test_TM13_tutor_not_saved_gives_done_without_ids(
    signed_in: TestClient, repo: FakeRoomRepo, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-18."""
    session = repo.add_session()
    repo.fail_insert_role = "tutor"

    response = send(signed_in, session.id)

    assert parse_sse(response.text)[-1] == ("done", {"message_ids": []})
    assert response.headers["x-request-id"] in caplog.text


def test_TM13_user_not_saved_is_503_and_no_ai_call(
    signed_in: TestClient, repo: FakeRoomRepo, fake: FakeProvider
) -> None:
    """AC-19."""
    session = repo.add_session()
    repo.fail_insert_role = "user"

    response = send(signed_in, session.id)

    assert response.status_code == 503
    assert response.json() == DB_DOWN
    assert fake.requests == []


def test_TM13_ended_session_refuses_messages(
    signed_in: TestClient, repo: FakeRoomRepo, fake: FakeProvider
) -> None:
    """AC-20."""
    session = repo.add_session(ended_at=NOW)

    assert_error(send(signed_in, session.id), 409, "session_already_ended")
    assert repo.messages[session.id] == []
    assert fake.requests == []


def test_SA06_message_to_a_foreign_session_is_404(
    signed_in: TestClient, repo: FakeRoomRepo, fake: FakeProvider
) -> None:
    """AC-21."""
    assert_error(send(signed_in, uuid.uuid4()), 404, "not_found")
    assert all(not rows for rows in repo.messages.values())
    assert fake.requests == []


def test_TM13_tutor_gets_no_problem_and_the_saved_conversation(
    signed_in: TestClient, repo: FakeRoomRepo
) -> None:
    """AC-22, AC-boundary-turns at the API: N + 1 earlier turns, the oldest drops, the message
    being sent is not in the conversation, and `<` is escaped."""
    session = repo.add_session()
    lines = [("tutor", "turn0 greeting")]
    for i in range(1, N_TURNS + 1):
        lines += [("user", f"q{i} <b>"), ("tutor", f"a{i}")]
    repo.seed(session, lines)
    fake = FakeProvider({"tutor_reply": ["ok"]})
    app.dependency_overrides[get_gateway] = lambda: gateway_of(fake)

    send(signed_in, session.id, "ข้อความใหม่")

    prompt = fake.requests[0].prompt
    problem_block = prompt.split('<document name="problem">', 1)[1].split("</document>", 1)[0]
    assert problem_block.strip() == "none"
    conversation = prompt.split("<conversation>", 1)[1].split("</conversation>", 1)[0]
    assert "turn0 greeting" not in conversation
    assert "q1 &lt;b>" in conversation
    assert f"a{N_TURNS}" in conversation
    assert "<b>" not in conversation
    assert "ข้อความใหม่" not in conversation


# --- DB down ---------------------------------------------------------------------------------


@pytest.mark.parametrize("which", ALL)
def test_TM13_database_down_is_503_before_any_stream(
    signed_in: TestClient, repo: FakeRoomRepo, fake: FakeProvider, which: str
) -> None:
    """AC-db."""
    session = repo.add_session()
    repo.down = True

    response = call(signed_in, which, session.id)

    assert response.status_code == 503
    assert response.json() == DB_DOWN
    assert "down" not in response.text
    assert fake.requests == []
