"""The problem card saved in the chat history (specs/features/tutor/problem-card-history.md §6 ·
TM-13, TM-06, SA-06).

Every SSE `problem` sent on the token path is saved as one `messages` row: `role = "card"`,
`content = None`, `card = {"problem": <the event's payload>}`, before the next visible line, so
`GET /sessions/{id}` gives it back after a reload. No network; the fakes of #123, #131 and the
answers step.

Interfaces these tests expect (to be built by /implement-feature):
- `RoomRepository.add_message(..., content: str | None, ..., card: Mapping | None = None)`
- `done.message_ids` stays the tutor and buddy messages only (§6 item 4: the card's id is not in
  it, as `DoneEvent` says today)
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from app.db.exam_preps import DbUnavailableError
from app.db.room import MessageRecord
from app.main import app
from app.services.dev_uploads import get_local_upload_dir
from tests.unit import test_room_answers_db as answers
from tests.unit import test_room_problems_api as opening
from tests.unit import test_room_sessions_api as room_api
from tests.unit.test_room_answers_db import JPEG, RIGHT, RIGHT_ROUND, Room, classify, typed
from tests.unit.test_room_problems_api import OPEN, generated, script
from tests.unit.test_room_sessions_api import NOW, PREP_ID, USER, FakeRoomRepo, prep_record
from tests.unit.test_tutor_reply_stream_api import parse_sse

# Fixtures of the reviewed files; `repo` is replaced below by one that keeps `card`.
client = room_api.client
fake = room_api.fake
no_retry_sleep = room_api.no_retry_sleep
signed_in = room_api.signed_in
problems = opening.problems
room = answers.room
local_room = answers.local_room

NEXT = "ข้อต่อไปนะ"
GREETING = "สวัสดี เริ่มลิมิตกัน"


@dataclass
class CardRoomRepo(FakeRoomRepo):
    """The fake of #123 with the `card` column and the tenant of each card row."""

    card_tenants: list[uuid.UUID] = field(default_factory=list)

    def add_message(
        self,
        *,
        tenant_id: uuid.UUID,
        session_id: uuid.UUID,
        role: str,
        content: str | None,
        input_mode: str | None,
        card: Any = None,
    ) -> MessageRecord:
        self._touch()
        if self.fail_insert_role == role:
            raise DbUnavailableError("insert failed")
        if role == "card":
            self.card_tenants.append(tenant_id)
        record = MessageRecord(
            id=uuid.uuid4(),
            role=role,
            content=content,
            card=card,
            input_mode=input_mode,
            attachment_path=None,
            attachment_name=None,
            created_at=NOW + timedelta(seconds=len(self.messages[session_id])),
        )
        self.messages[session_id].append(record)
        return record


@pytest.fixture
def repo() -> CardRoomRepo:
    return CardRoomRepo(preps={PREP_ID: prep_record()})


def event(events: list[tuple[str, Any]], name: str) -> Any:
    return next(d for n, d in events if n == name)


def shown(rows: list[MessageRecord]) -> list[tuple[str, Any]]:
    """The rows the web shows (not the hidden `system` notes): a card by its `card`."""
    return [(m.role, m.card if m.role == "card" else m.content) for m in rows if m.role != "system"]


def open_room(signed_in, fake) -> tuple[uuid.UUID, list[tuple[str, Any]]]:
    script(fake, generate_problem=[generated()], open_session=[GREETING])
    events = parse_sse(signed_in.post(OPEN).text)
    return uuid.UUID(events[0][1]["session_id"]), events


# --- opening ------------------------------------------------------------------------------------


def test_TM13_SA06_the_opening_problem_card_is_saved_after_the_greeting(
    signed_in, problems, fake, repo: CardRoomRepo
):
    # §6 items 1-2: the opening (room_problems.opening_events)
    session_id, events = open_room(signed_in, fake)

    rows = repo.messages[session_id]
    assert [(m.role, m.content) for m in rows] == [("tutor", GREETING), ("card", None)]
    assert rows[1].card == {"problem": event(events, "problem")}
    assert rows[1].input_mode is None
    assert repo.card_tenants == [USER.tenant_id]


def test_TM13_done_keeps_only_the_tutor_message_ids(signed_in, problems, fake, repo: CardRoomRepo):
    # §6 item 4: the card's id is not in done.message_ids (DoneEvent: tutor and buddy messages)
    session_id, events = open_room(signed_in, fake)

    greeting = repo.messages[session_id][0]
    assert events[-1] == ("done", {"message_ids": [str(greeting.id)]})


def test_TM13_get_session_gives_the_problem_card_back(
    signed_in, problems, fake, repo: CardRoomRepo
):
    # §6 item 3: GET /sessions/{id} returns the row in `messages` as it is (no schema change)
    session_id, events = open_room(signed_in, fake)

    response = signed_in.get(f"/sessions/{session_id}")

    assert response.status_code == 200, response.text
    messages = response.json()["messages"]
    assert [m["role"] for m in messages] == ["tutor", "card"]
    assert messages[1]["content"] is None
    assert messages[1]["card"] == {"problem": event(events, "problem")}


def test_TM13_no_problem_saves_no_card(signed_in, problems, fake, repo: CardRoomRepo):
    # No `problem` event, no card row (the no_problem line is saved as before)
    script(fake, generate_problem=[generated(reference="5")] * 3, open_session=["สวัสดี"])

    events = parse_sse(signed_in.post(OPEN).text)

    session_id = uuid.UUID(events[0][1]["session_id"])
    assert "problem" not in [n for n, _ in events]
    assert all(m.role != "card" for m in repo.messages[session_id])


def test_TM13_a_card_that_cannot_be_saved_does_not_stop_the_stream(
    signed_in, problems, fake, repo: CardRoomRepo
):
    # Like every save inside the stream (room-sessions-db.md AC-5): the card is on screen
    repo.fail_insert_role = "card"

    session_id, events = open_room(signed_in, fake)

    assert event(events, "problem")["problem_id"]
    assert events[-1][0] == "done"
    assert [m.role for m in repo.messages[session_id]] == ["tutor"]


# --- the next problem after a check ---------------------------------------------------------------


def test_TM13_the_next_problem_after_a_typed_answer_is_saved_after_next(room: Room):
    # §6 item 2: the next problem after a typed answer (room-answers-db.md)
    room.script(**RIGHT_ROUND, generate_problem=[generated()])

    events = room.say("x^2-49 = (x-7)(x+7)")

    rows = shown(room.repo.messages[room.session_id])
    assert rows[-2:] == [("tutor", NEXT), ("card", {"problem": event(events, "problem")})]


def test_TM06_the_same_problem_sent_again_is_saved_again(room: Room):
    # §6 item 1 "every time": ask_working sends the open problem again at the bottom
    room.script(
        typed_answer=[typed(["(x-7)(x+7)"])],
        check_answer=[classify("correct")],
        explain_check=["ส่งวิธีทำมาด้วยนะ"],
    )

    events = room.say("(x-7)(x+7)")

    card = event(events, "problem")
    assert card["problem_id"] == str(room.open.id)
    rows = shown(room.repo.messages[room.session_id])
    assert rows[-2:] == [("tutor", "ส่งวิธีทำมาด้วยนะ"), ("card", {"problem": card})]


@local_room
def test_TM06_the_next_problem_after_a_photo_is_saved_as_a_card(room: Room, tmp_path: Path):
    # §6 item 2: after a photo / the handwriting confirm (photo_check)
    app.dependency_overrides[get_local_upload_dir] = lambda: tmp_path
    room.script(
        extract_answer=[
            json.dumps({"lines": [{"latex": x, "confidence": 0.9} for x in RIGHT], "notes": ""})
        ],
        check_answer=[classify("correct")],
        explain_check=["เก่งมาก"],
        generate_problem=[generated()],
    )
    ticket = room.client.post(
        f"/sessions/{room.session_id}/uploads",
        json={
            "kind": "image",
            "content_type": "image/jpeg",
            "file_name": "a.jpg",
            "size_bytes": len(JPEG),
        },
    ).json()
    room.client.put(ticket["upload_url"], content=JPEG, headers={"Content-Type": "image/jpeg"})
    room.client.post(f"/sessions/{room.session_id}/messages", json={"image_path": ticket["path"]})

    confirmed = parse_sse(
        room.client.post(f"/sessions/{room.session_id}/ocr/confirm", json={"lines": RIGHT}).text
    )

    rows = shown(room.repo.messages[room.session_id])
    assert rows[-2:] == [("tutor", NEXT), ("card", {"problem": event(confirmed, "problem")})]
