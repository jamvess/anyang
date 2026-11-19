"""Ending the session with a token: closed first, facts by code, a summary by session_summary
(specs/features/tutor/session-end-db.md · AC-1 to AC-10).

No network. Subclasses of the fakes of #123 and #135 (the reviewed files stay as they are).

Interfaces these tests expect (to be built by /implement-feature):
- `RoomRepository.end_session(session_id, reason) -> bool`: one conditional update
  (`ended_at is null`); False when no row changed
- `RoomRepository.save_summary(session_id, summary)`
- `ProblemRepository.attempts_since(since) -> list[AttemptFacts]`; `app.db.room_problems.
  AttemptFacts(topic_id, is_correct, created_at)` (the user's attempts, any prep)
- `app.models.tutor_ai.SessionSummaryResult(lines)` and prompt `session_summary/v1` with the
  data blocks `prep_name`, `days_left`, `topics`, `totals`
- `config/messages.yaml` → `room.session_summary_answered` (`{answers}`, `{right}`) and
  `room.session_summary_empty`
"""

import json
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.db import room_problems as db
from app.db.exam_preps import DbUnavailableError
from app.db.room_problems import get_problem_repository
from app.domain.room import LEVEL_NAMES
from app.main import app
from tests.unit import test_room_sessions_api as room_api
from tests.unit.test_room_answers_db import factor_problem
from tests.unit.test_room_problems_api import FACTOR, LIMIT, OPEN, SETTINGS, block, event, script
from tests.unit.test_room_sessions_api import NOW, PREP_ID, FakeRoomRepo
from tests.unit.test_topic_progress_db import ProgressProblemRepo
from tests.unit.test_tutor_reply_stream_api import parse_sse

client = room_api.client
fake = room_api.fake
no_retry_sleep = room_api.no_retry_sleep
signed_in = room_api.signed_in

LINES = ["วันนี้ทำลิมิตไป 2 ข้อ ถูกทั้งสองข้อ", "ครั้งหน้าลองแยกตัวประกอบต่อนะ"]
ROOM = SETTINGS.messages.room


@dataclass
class EndRoomRepo(FakeRoomRepo):
    """#123's fake plus closing a session and saving its summary."""

    summaries: dict[uuid.UUID, str] = field(default_factory=dict)
    reasons: dict[uuid.UUID, str] = field(default_factory=dict)
    lose_the_race: bool = False  # another request closed it between the read and the update
    fail_summary: bool = False

    def end_session(self, session_id: uuid.UUID, reason: str) -> bool:
        self._touch()
        session = self.sessions.get(session_id)
        if session is None or session.ended_at is not None or self.lose_the_race:
            return False
        self.sessions[session_id] = replace(session, ended_at=NOW + timedelta(hours=1))
        self.reasons[session_id] = reason
        return True

    def save_summary(self, session_id: uuid.UUID, summary: str) -> None:
        if self.fail_summary:
            raise DbUnavailableError("update tutor_sessions")
        self.summaries[session_id] = summary


@dataclass
class SessionProblemRepo(ProgressProblemRepo):
    """#135's fake plus the user's attempts with their time."""

    answers: list[Any] = field(default_factory=list)

    def attempts_since(self, since: datetime) -> list[Any]:
        return [a for a in self.answers if a.created_at >= since]


def answer(topic, is_correct: bool, minutes: int = 5) -> Any:
    return db.AttemptFacts(
        topic_id=topic.id, is_correct=is_correct, created_at=NOW + timedelta(minutes=minutes)
    )


@dataclass
class Ending:
    client: TestClient
    repo: EndRoomRepo
    problems: SessionProblemRepo
    fake: Any
    session_id: uuid.UUID

    def end(self) -> Any:
        return self.client.post(f"/sessions/{self.session_id}/end")

    def requests(self, purpose: str) -> list[Any]:
        return [r for r in self.fake.requests if r.purpose == purpose]


@pytest.fixture
def repo() -> EndRoomRepo:
    """Replaces the `repo` fixture of #123, so its `client` uses this one."""
    return EndRoomRepo(preps={PREP_ID: room_api.prep_record()})


@pytest.fixture
def ending(signed_in, repo: EndRoomRepo, fake) -> Ending:
    problems = SessionProblemRepo()
    app.dependency_overrides[get_problem_repository] = lambda: problems
    session = repo.add_session()
    problems.problems.append(factor_problem(session.id))  # an open problem of the prep
    return Ending(signed_in, repo, problems, fake, session.id)


def three_answers(ending: Ending) -> None:
    ending.problems.answers += [
        answer(LIMIT, True),
        answer(FACTOR, False, minutes=10),
        answer(LIMIT, True, minutes=15),
        answer(LIMIT, False, minutes=-5),  # before the session started
        db.AttemptFacts(uuid.uuid4(), True, NOW + timedelta(minutes=1)),  # a topic of another prep
    ]
    ending.problems.rows[LIMIT.id] = {
        "topic_id": LIMIT.id,
        "mastery": 0.7,
        "attempts_n": 2,
        "correct_n": 2,
        "d_max": 3,
        "level": "developing",
    }


def summary(lines: list[str]) -> str:
    return json.dumps({"lines": lines}, ensure_ascii=False)


# --- the summary -------------------------------------------------------------------------------


def test_PM05_the_session_ends_with_a_summary_saved_as_a_chat_message(ending: Ending):
    # AC-1
    three_answers(ending)
    script(ending.fake, session_summary=[summary(LINES)])

    response = ending.end()

    events = parse_sse(response.text)
    assert [n for n, _ in events] == ["session_end", "done"]
    assert event(events, "session_end") == {"summary_lines": LINES}
    session = ending.repo.sessions[ending.session_id]
    assert session.ended_at is not None
    assert ending.repo.reasons[ending.session_id] == "user"
    assert ending.repo.summaries[ending.session_id] == "\n".join(LINES)
    [saved] = ending.repo.messages[ending.session_id]
    assert (saved.role, saved.content) == ("tutor", "\n".join(LINES))
    assert event(events, "done")["message_ids"] == [str(saved.id)]


def test_PM05_session_summary_gets_the_facts_of_this_session_only(ending: Ending):
    # AC-2
    three_answers(ending)
    script(ending.fake, session_summary=[summary(LINES)])

    ending.end()

    [request] = ending.requests("session_summary")
    assert block(request, "topics") == (
        f"{LIMIT.name} · ตอบ 2 ครั้ง ถูก 2 · ระดับตอนนี้ {LEVEL_NAMES['developing']}\n"
        f"{FACTOR.name} · ตอบ 1 ครั้ง ถูก 0 · ระดับตอนนี้ {LEVEL_NAMES['not_started']}"
    )
    assert block(request, "totals") == "ตอบ 3 ครั้ง ถูก 2"
    assert block(request, "prep_name") == room_api.prep_record().title
    assert block(request, "days_left") == "27"


def test_PM05_a_session_with_no_answers_still_gets_a_summary(ending: Ending):
    # AC-3
    script(ending.fake, session_summary=[summary(["วันนี้ยังไม่ได้ทำโจทย์ ไว้มาต่อกันนะ"])])

    events = parse_sse(ending.end().text)

    [request] = ending.requests("session_summary")
    assert block(request, "topics") == "none"
    assert event(events, "session_end")["summary_lines"]


@pytest.mark.parametrize("answered", [True, False], ids=["answers", "no_answers"])
def test_PM05_a_failed_summary_falls_back_to_the_template(ending: Ending, answered):
    # AC-4
    if answered:
        three_answers(ending)
    script(ending.fake, session_summary=[RuntimeError("down")] * 5)

    events = parse_sse(ending.end().text)

    expected = (
        ROOM.session_summary_answered.format(answers=3, right=2)
        if answered
        else ROOM.session_summary_empty
    )
    assert event(events, "session_end") == {"summary_lines": [expected]}
    assert ending.repo.summaries[ending.session_id] == expected
    assert ending.repo.sessions[ending.session_id].ended_at is not None


# --- refusals ----------------------------------------------------------------------------------


def test_PM05_an_ended_session_cannot_end_again(ending: Ending):
    # AC-5
    ending.repo.sessions[ending.session_id] = replace(
        ending.repo.sessions[ending.session_id], ended_at=NOW
    )

    response = ending.end()

    room_api.assert_error(response, 409, "session_already_ended")
    assert ending.requests("session_summary") == []
    assert ending.repo.messages[ending.session_id] == []


def test_PM05_a_session_another_request_closed_first_gets_409(ending: Ending):
    # AC-6
    ending.repo.lose_the_race = True

    response = ending.end()

    room_api.assert_error(response, 409, "session_already_ended")
    assert ending.requests("session_summary") == []


def test_TM13_after_ending_a_new_room_has_a_new_session_and_the_open_problem(ending: Ending):
    # AC-7
    script(ending.fake, session_summary=[summary(LINES)], open_session=["กลับมาแล้ว"])
    ending.end()

    active = ending.client.get(f"/exam-preps/{PREP_ID}/sessions/active")
    opened = parse_sse(ending.client.post(OPEN).text)

    room_api.assert_error(active, 404, "no_active_session")
    assert event(opened, "session")["session_id"] != str(ending.session_id)
    assert event(opened, "problem")["problem_id"] == str(ending.problems.problems[0].id)


def test_PM05_an_unknown_session_is_not_found(ending: Ending):
    # AC-8
    response = ending.client.post(f"/sessions/{uuid.uuid4()}/end")

    room_api.assert_error(response, 404, "not_found")


def test_PM05_a_database_that_is_down_gives_503(ending: Ending):
    # AC-8
    ending.repo.down = True

    response = ending.end()

    room_api.assert_error(response, 503, "db_unavailable")


def test_PM05_a_summary_that_cannot_be_saved_still_ends_the_stream(ending: Ending):
    # AC-9 · answers, so the numbers of LINES are facts (self-review PR #136 · Jam ok)
    three_answers(ending)
    ending.repo.fail_summary = True
    ending.repo.fail_insert_role = "tutor"
    script(ending.fake, session_summary=[summary(LINES)])

    events = parse_sse(ending.end().text)

    assert event(events, "session_end") == {"summary_lines": LINES}
    assert event(events, "done")["message_ids"] == []
    assert ending.repo.sessions[ending.session_id].ended_at is not None


# --- added by the self-review of PR #136 -----------------------------------------------------


def test_PM05_a_summary_with_a_number_that_is_not_in_the_facts_is_not_shown(ending: Ending):
    # §2.3 item 2: code decides the counts (3 answers, 2 right · no 5)
    three_answers(ending)
    script(ending.fake, session_summary=[summary(["วันนี้ตอบไป 5 ข้อ ถูก 2 ข้อ"])])

    events = parse_sse(ending.end().text)

    expected = ROOM.session_summary_answered.format(answers=3, right=2)
    assert event(events, "session_end") == {"summary_lines": [expected]}


def test_PM05_answers_that_cannot_be_read_are_not_called_none(ending: Ending):
    # A failed read must not become "you answered nothing"
    three_answers(ending)

    def down(since):
        raise DbUnavailableError("select attempts")

    ending.problems.attempts_since = down  # type: ignore[method-assign]

    events = parse_sse(ending.end().text)

    assert event(events, "session_end") == {"summary_lines": [ROOM.session_summary_unknown]}
    assert ending.requests("session_summary") == []
