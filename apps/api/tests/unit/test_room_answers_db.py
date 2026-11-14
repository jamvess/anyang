"""Answers checked in the room with a token, through a database RoomState
(specs/features/tutor/room-answers-db.md · AC-1 to AC-13).

No network. The room repository is the fake of #123 (sessions, messages); the problem repository
is the fake of #131 extended here with attempts, `ended_at` and `working_steps` (a subclass, so
the reviewed test files stay as they are). SymPy is real.

Interfaces these tests expect (to be built by /implement-feature):
- `ProblemRepository` (app/db/room_problems.py) gains `add_attempt(**fields)`,
  `count_wrong_attempts(problem_id) -> int`, `end_problem(problem_id)`,
  `working_steps(problem_id) -> int`, `add_working_steps(problem_id, steps)`; "open" means
  `ended_at is null` (spec §2.2 item 1)
- `RoomState.record_answer(key, pending, lines, result, independent)` (no-op in the demo states)
- `app.services.room_db_state.DbRoomState` used by the token paths of messages and ocr/confirm
"""

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.db.exam_preps import DbUnavailableError
from app.db.room_problems import ProblemRecord, get_problem_repository
from app.main import app
from app.services.dev_uploads import get_local_mode, get_local_upload_dir
from tests.unit import test_room_sessions_api as room_api
from tests.unit.test_room_problems_api import (
    LIMIT,
    FakeProblemRepo,
    generated,
)
from tests.unit.test_room_sessions_api import USER, FakeRoomRepo, send
from tests.unit.test_tutor_reply_stream_api import parse_sse

# Fixtures of test_room_sessions_api.py (#123).
client = room_api.client
fake = room_api.fake
no_retry_sleep = room_api.no_retry_sleep
repo = room_api.repo
signed_in = room_api.signed_in

NEXT = "ข้อต่อไปนะ"
RIGHT = ["x^2-49", "= (x-7)(x+7)"]
WRONG = ["x^2-49", "= (x-7)(x-7)"]
JPEG = b"\xff\xd8 handwriting"


@dataclass
class AnswerProblemRepo(FakeProblemRepo):
    """#131's fake plus what step 7 writes: attempts, ended problems, working steps."""

    attempts: list[dict[str, Any]] = field(default_factory=list)
    ended: set[uuid.UUID] = field(default_factory=set)
    steps: dict[uuid.UUID, int] = field(default_factory=dict)
    fail_attempts: bool = False

    def open_problem(self, prep_id, topic_id):
        mine = [p for p in self.problems if p.topic_id == topic_id and p.id not in self.ended]
        return mine[-1] if mine else None

    def session_problem(self, session_id):
        mine = [p for p in self.problems if p.id not in self.ended]
        return mine[-1] if mine else None

    def add_attempt(self, **fields: Any) -> None:
        if self.fail_attempts:
            raise DbUnavailableError("insert attempts")
        self.attempts.append(fields)

    def count_wrong_attempts(self, problem_id) -> int:
        return sum(
            1
            for a in self.attempts
            if a["problem_id"] == problem_id and a["verdict"] == "incorrect"
        )

    def end_problem(self, problem_id) -> None:
        self.ended.add(problem_id)

    def working_steps(self, problem_id) -> int:
        return self.steps.get(problem_id, 0)

    def add_working_steps(self, problem_id, steps: int) -> None:
        self.steps[problem_id] = self.steps.get(problem_id, 0) + steps


def factor_problem(session_id: uuid.UUID) -> ProblemRecord:
    return ProblemRecord(
        id=uuid.uuid4(),
        session_id=session_id,
        topic_id=LIMIT.id,
        skill_id=None,
        text="แยกตัวประกอบ $x^2-49$",
        reference_answer="(x-7)(x+7)",
        solution_steps=["x^2-7^2", "= (x-7)(x+7)"],
        answer_format="factored",
        difficulty=3,
        purpose="probe",
    )


@dataclass
class Room:
    client: TestClient
    repo: FakeRoomRepo
    problems: AnswerProblemRepo
    fake: Any
    session_id: uuid.UUID
    open: ProblemRecord

    def say(self, text: str) -> list[tuple[str, Any]]:
        return parse_sse(send(self.client, self.session_id, text).text)

    def requests(self, purpose: str) -> list[Any]:
        return [r for r in self.fake.requests if r.purpose == purpose]

    def script(self, **purposes: list[Any]) -> None:
        for purpose, replies in purposes.items():
            self.fake._script.setdefault(purpose, []).extend(replies)


@pytest.fixture
def room(signed_in, repo: FakeRoomRepo, fake, request) -> Room:
    local = getattr(request, "param", False)
    app.dependency_overrides[get_local_mode] = lambda: local
    problems = AnswerProblemRepo()
    app.dependency_overrides[get_problem_repository] = lambda: problems
    session = repo.add_session()
    problem = factor_problem(session.id)
    problems.problems.append(problem)
    return Room(signed_in, repo, problems, fake, session.id, problem)


local_room = pytest.mark.parametrize("room", [True], indirect=True)


def typed(lines: list[str]) -> str:
    return json.dumps({"is_answer": True, "lines": lines})


def classify(verdict: str, error_type: str | None = None, line: int | None = None) -> str:
    return json.dumps(
        {
            "error_type": error_type,
            "evidence": "",
            "method": "doc",
            "verdict": verdict,
            "first_wrong_line": line,
            "confidence": 0.9,
        }
    )


RIGHT_ROUND = {
    "typed_answer": [typed(RIGHT)],
    "check_answer": [classify("correct")],
    "explain_check": ["เก่งมาก"],
}
WRONG_ROUND = {
    "typed_answer": [typed(WRONG)],
    "check_answer": [classify("incorrect", "sign", 2)],
    "explain_check": ["ดูบรรทัดสอง"],
}


def names(events) -> list[str]:
    return [n for n, _ in events]


def event(events, name: str) -> Any:
    return next(d for n, d in events if n == name)


def directive_of(request: Any) -> str:
    import re

    match = re.search(r'<document name="directive">\n(.*?)\n</document>', request.prompt, re.DOTALL)
    assert match
    return match.group(1)


# --- typed answers ---------------------------------------------------------------------------


def test_AM04_PM01_a_right_answer_is_checked_saved_and_the_next_problem_follows(room: Room):
    # AC-1 · not local: typed_answer runs anyway on the token path
    room.script(**RIGHT_ROUND, generate_problem=[generated()])

    events = room.say("x^2-49 = (x-7)(x+7)")

    assert len(room.requests("typed_answer")) == 1
    assert event(events, "verdict")["verdict"] == "correct"
    assert ("token", {"speaker": "tutor", "text": NEXT}) in events
    new_id = event(events, "problem")["problem_id"]
    assert new_id != str(room.open.id)
    assert names(events)[-1] == "done"
    [attempt] = room.problems.attempts
    assert (
        attempt["problem_id"],
        attempt["topic_id"],
        attempt["verdict"],
        attempt["is_correct"],
    ) == (
        room.open.id,
        LIMIT.id,
        "correct",
        True,
    )
    assert (attempt["tenant_id"], attempt["user_id"]) == (USER.tenant_id, USER.user_id)
    assert attempt["answer_text"] == "\n".join(RIGHT)
    assert room.open.id in room.problems.ended


@local_room
def test_AM07_wrong_answers_climb_the_ladder_counted_from_attempts(room: Room):
    # AC-2
    room.script(
        typed_answer=[typed(WRONG)] * 3,
        check_answer=[classify("incorrect", "sign", 2)] * 3,
        explain_check=["ใบ้หนึ่ง", "ใบ้สอง", "เฉลย"],
        generate_problem=[generated()],
    )

    first = room.say("(x-7)(x-7)")
    assert event(first, "problem")["problem_id"] == str(room.open.id)
    assert room.open.id not in room.problems.ended
    second = room.say("(x-7)(x-7)")
    third = room.say("(x-7)(x-7)")

    assert [directive_of(r) for r in room.requests("explain_check")] == [
        "hint_1",
        "hint_2",
        "reveal",
    ]
    assert event(second, "verdict")["verdict"] == "incorrect"
    assert ("token", {"speaker": "tutor", "text": NEXT}) in third
    assert len(room.problems.attempts) == 3
    assert room.open.id in room.problems.ended


def test_AM07_outside_local_the_first_wrong_answer_gets_the_solution(room: Room):
    # AC-3
    room.script(**WRONG_ROUND, generate_problem=[generated()])

    events = room.say("(x-7)(x-7)")

    assert directive_of(room.requests("explain_check")[0]) == "reveal"
    assert ("token", {"speaker": "tutor", "text": NEXT}) in events
    assert room.open.id in room.problems.ended


@local_room
def test_AM05_an_unfinished_step_saves_steps_and_no_attempt(room: Room):
    # AC-4: x^3-x not factored yet is `incomplete` → continue; then one more step passes.
    room.script(
        typed_answer=[typed(["x^2-49", "= (x^2-49)"]), typed(["= (x-7)(x+7)"])],
        check_answer=[classify("incomplete", "concept"), classify("correct")],
        explain_check=["แยกต่อได้", "เก่งมาก"],
        generate_problem=[generated()],
    )

    first = room.say("x^2-49 = (x^2-49)")
    assert "verdict" not in names(first)
    assert room.problems.attempts == []
    assert room.problems.steps[room.open.id] == 2

    second = room.say("= (x-7)(x+7)")

    assert event(second, "verdict")["verdict"] == "correct"
    assert len(room.problems.attempts) == 1


def test_AM07_a_right_answer_without_working_saves_no_attempt(room: Room):
    # AC-5
    room.script(
        typed_answer=[typed(["(x-7)(x+7)"])],
        check_answer=[classify("correct")],
        explain_check=["ส่งวิธีทำมาด้วยนะ"],
    )

    events = room.say("(x-7)(x+7)")

    assert "verdict" not in names(events)
    assert event(events, "problem")["problem_id"] == str(room.open.id)
    assert room.problems.attempts == []
    assert room.open.id not in room.problems.ended


def test_AM07_giving_up_ends_the_problem_without_an_attempt(room: Room):
    # AC-6
    room.script(
        typed_answer=[json.dumps({"is_answer": False, "lines": [], "give_up": True})],
        explain_check=["ไม่เป็นไร"],
        generate_problem=[generated()],
    )

    events = room.say("ไม่ได้จริงๆ")

    assert room.requests("check_answer") == []
    assert ("token", {"speaker": "tutor", "text": NEXT}) in events
    assert room.problems.attempts == []
    assert room.open.id in room.problems.ended


def test_TM10_a_message_that_is_not_an_answer_goes_to_the_tutor(room: Room):
    # AC-7
    room.script(
        typed_answer=[json.dumps({"is_answer": False, "lines": []})], tutor_reply=["ลองดูนะ"]
    )

    events = room.say("เริ่มยังไง")

    assert "verdict" not in names(events)
    [reply] = room.requests("tutor_reply")
    assert "x^2-49" in reply.prompt
    assert "(x-7)(x+7)" not in reply.prompt  # no answer (AM-13)
    assert room.problems.attempts == []


def test_TM10_no_open_problem_keeps_the_path_of_131(room: Room):
    # AC-8
    room.problems.ended.add(room.open.id)

    room.say("สวัสดี")

    assert room.requests("typed_answer") == []
    assert len(room.requests("tutor_reply")) == 1


@local_room
def test_TM13_the_lines_are_saved_as_user_tutor_and_hidden_system(room: Room):
    # AC-9
    room.script(**WRONG_ROUND, tutor_reply=["ok"])
    room.script(typed_answer=[json.dumps({"is_answer": False, "lines": []})])

    room.say("(x-7)(x-7)")
    saved = [(m.role, m.content) for m in room.repo.messages[room.session_id]]
    room.say("ทำไม")

    assert saved[0] == ("user", "(x-7)(x-7)")
    assert saved[1][0] == "system" and saved[1][1].startswith("(ผลตรวจ) verdict incorrect")
    assert ("tutor", "ดูบรรทัดสอง") in saved
    assert saved[-1][0] == "system" and saved[-1][1].startswith("(โจทย์)")
    [reply] = room.requests("tutor_reply")
    assert "ติวเตอร์: (ผลตรวจ) verdict incorrect" in reply.prompt
    assert "นักเรียน: (x-7)(x-7)" in reply.prompt


# --- photo and canvas (local) ----------------------------------------------------------------


@local_room
def test_TM06_a_photo_of_the_open_problem_is_checked_and_saved(room: Room, tmp_path: Path):
    # AC-10
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

    preview = parse_sse(
        room.client.post(
            f"/sessions/{room.session_id}/messages", json={"image_path": ticket["path"]}
        ).text
    )
    confirmed = parse_sse(
        room.client.post(f"/sessions/{room.session_id}/ocr/confirm", json={"lines": RIGHT}).text
    )

    assert "ocr_preview" in names(preview)
    assert room.open.text in room.requests("extract_answer")[0].prompt
    assert event(confirmed, "verdict")["verdict"] == "correct"
    assert len(room.problems.attempts) == 1
    saved = [(m.role, m.content) for m in room.repo.messages[room.session_id]]
    assert any(r == "system" and c.startswith("(ส่งรูปวิธีทำ)") for r, c in saved)
    assert any(r == "system" and c.startswith("(ยืนยันคำตอบ)") for r, c in saved)


# --- edges --------------------------------------------------------------------------------------


def test_TM13_reopening_after_a_wrong_answer_gives_the_same_problem(room: Room):
    # AC-11 (with a ladder off, a wrong answer ends the problem; use ask_working: not ended)
    room.script(
        typed_answer=[typed(["(x-7)(x+7)"])],
        check_answer=[classify("correct")],
        explain_check=["ส่งวิธีทำมาด้วยนะ"],
        open_session=["สวัสดี"],
    )
    room.say("(x-7)(x+7)")

    opened = parse_sse(room.client.post(f"/exam-preps/{room_api.PREP_ID}/sessions").text)

    assert event(opened, "problem")["problem_id"] == str(room.open.id)


def test_AM11_no_next_problem_still_ends_the_answered_one(room: Room):
    # AC-12
    room.script(**RIGHT_ROUND, generate_problem=[RuntimeError("down")] * 3)

    events = room.say("x^2-49 = (x-7)(x+7)")

    assert event(events, "verdict")["verdict"] == "correct"
    assert "problem" not in names(events)
    assert ("token", {"speaker": "tutor", "text": NEXT}) not in events
    assert room.open.id in room.problems.ended


def test_PM01_an_attempt_that_cannot_be_saved_does_not_stop_the_stream(room: Room):
    # AC-13
    room.problems.fail_attempts = True
    room.script(**RIGHT_ROUND, generate_problem=[generated()])

    events = room.say("x^2-49 = (x-7)(x+7)")

    assert event(events, "verdict")["verdict"] == "correct"
    assert names(events)[-1] == "done"
