"""BKT into topic_progress when a problem ends; the card of a new room follows it
(specs/features/planner/topic-progress-db.md · AC-1 to AC-8).

No network. The fakes of #123, #131 and #132, plus the user's `topic_progress` rows; SymPy is
real. Every expected number comes from app/domain/bkt.py and config/learning.yaml.

Interfaces these tests expect (to be built by /implement-feature):
- `ProgressFacts` gains `correct_n` (default 0)
- `ProblemRepository.get_topic_progress(topic_id) -> ProgressFacts | None` (the user's row)
- `ProblemRepository.save_topic_progress(**fields)`: upsert by (user_id, topic_id) with
  tenant_id, user_id, exam_prep_id, topic_id, mastery, level, attempts_n, correct_n, d_max,
  last_seen_at
- `DbRoomState.record_check` does the BKT step (spec §2)
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.db.exam_preps import DbUnavailableError
from app.db.room_problems import ProgressFacts, get_problem_repository
from app.domain.bkt import TopicProgress, level, target_difficulty, update_mastery
from app.main import app
from app.services.dev_uploads import get_local_mode
from tests.unit import test_room_sessions_api as room_api
from tests.unit.test_room_answers_db import (
    RIGHT,
    RIGHT_ROUND,
    WRONG,
    WRONG_ROUND,
    AnswerProblemRepo,
    classify,
    factor_problem,
    typed,
)
from tests.unit.test_room_problems_api import LIMIT, OPEN, SETTINGS, event, generated, script
from tests.unit.test_room_sessions_api import PREP_ID, USER, FakeRoomRepo, send
from tests.unit.test_tutor_reply_stream_api import parse_sse

client = room_api.client
fake = room_api.fake
no_retry_sleep = room_api.no_retry_sleep
repo = room_api.repo
signed_in = room_api.signed_in

CFG = SETTINGS.learning
P_INIT = CFG.bkt.p_init
TARGET = target_difficulty(LIMIT.importance or 0, "normal", CFG)  # the topic of the problem


@dataclass
class ProgressProblemRepo(AnswerProblemRepo):
    """#132's fake plus the user's topic_progress rows, keyed by topic."""

    rows: dict[uuid.UUID, dict[str, Any]] = field(default_factory=dict)
    fail_progress: bool = False

    def list_progress(self, prep_id) -> list[ProgressFacts]:
        return [self._facts(row) for row in self.rows.values()]

    def get_topic_progress(self, topic_id) -> ProgressFacts | None:
        if self.fail_progress:
            raise DbUnavailableError("select topic_progress")
        row = self.rows.get(topic_id)
        return self._facts(row) if row else None

    def save_topic_progress(self, **fields: Any) -> None:
        if self.fail_progress:
            raise DbUnavailableError("upsert topic_progress")
        self.rows[fields["topic_id"]] = dict(fields)

    @staticmethod
    def _facts(row: dict[str, Any]) -> ProgressFacts:
        return ProgressFacts(
            topic_id=row["topic_id"],
            mastery=row["mastery"],
            attempts_n=row["attempts_n"],
            level=row["level"],
            d_max=row["d_max"],
            correct_n=row["correct_n"],
        )


@dataclass
class Room:
    client: TestClient
    repo: FakeRoomRepo
    problems: ProgressProblemRepo
    fake: Any
    session_id: uuid.UUID

    def say(self, text: str) -> list[tuple[str, Any]]:
        return parse_sse(send(self.client, self.session_id, text).text)

    def script(self, **purposes: list[Any]) -> None:
        for purpose, replies in purposes.items():
            self.fake._script.setdefault(purpose, []).extend(replies)


@pytest.fixture
def room(signed_in, repo: FakeRoomRepo, fake, request) -> Room:
    app.dependency_overrides[get_local_mode] = lambda: getattr(request, "param", False)
    problems = ProgressProblemRepo()
    app.dependency_overrides[get_problem_repository] = lambda: problems
    session = repo.add_session()
    problems.problems.append(factor_problem(session.id))  # LIMIT · difficulty 3
    return Room(signed_in, repo, problems, fake, session.id)


local_room = pytest.mark.parametrize("room", [True], indirect=True)


def expected_level(mastery: float, attempts: int, d_max: int) -> str:
    return level(TopicProgress(mastery, attempts, d_max), TARGET, True, CFG)


def limit_row(room: Room) -> dict[str, Any] | None:
    return room.problems.rows.get(LIMIT.id)


# --- when mastery changes ----------------------------------------------------------------------


def test_PM02_a_right_answer_starts_the_row_from_p_init(room: Room):
    # AC-1
    room.script(**RIGHT_ROUND, generate_problem=[generated()])

    room.say("x^2-49 = (x-7)(x+7)")

    row = limit_row(room)
    assert row is not None
    mastery = update_mastery(P_INIT, True, CFG.bkt)
    assert row["mastery"] == pytest.approx(mastery)
    assert (row["attempts_n"], row["correct_n"], row["d_max"]) == (1, 1, 3)
    assert row["level"] == expected_level(mastery, 1, 3)
    assert (row["tenant_id"], row["user_id"]) == (USER.tenant_id, USER.user_id)
    assert (row["exam_prep_id"], row["topic_id"]) == (PREP_ID, LIMIT.id)
    assert row["last_seen_at"] is not None


def test_PM02_a_wrong_answer_lowers_mastery(room: Room):
    # AC-2: not local, so the first wrong answer gets the solution and the problem ends
    room.script(**WRONG_ROUND, generate_problem=[generated()])

    room.say("(x-7)(x-7)")

    row = limit_row(room)
    assert row is not None
    assert row["mastery"] == pytest.approx(update_mastery(P_INIT, False, CFG.bkt))
    assert (row["attempts_n"], row["correct_n"], row["d_max"]) == (1, 0, 0)


def test_PM02_giving_up_counts_as_wrong(room: Room):
    # AC-3
    room.script(
        typed_answer=[json.dumps({"is_answer": False, "lines": [], "give_up": True})],
        explain_check=["ไม่เป็นไร"],
        generate_problem=[generated()],
    )

    room.say("ไม่ได้จริงๆ")

    row = limit_row(room)
    assert row is not None
    assert row["mastery"] == pytest.approx(update_mastery(P_INIT, False, CFG.bkt))
    assert (row["attempts_n"], row["correct_n"]) == (1, 0)


def test_PM02_a_row_before_is_updated_from_its_values(room: Room):
    # AC-4
    before = 0.5
    room.problems.rows[LIMIT.id] = {
        "topic_id": LIMIT.id,
        "mastery": before,
        "attempts_n": 3,
        "correct_n": 2,
        "d_max": 2,
        "level": "developing",
    }
    room.script(**RIGHT_ROUND, generate_problem=[generated()])

    room.say("x^2-49 = (x-7)(x+7)")

    row = limit_row(room)
    assert row is not None
    assert row["mastery"] == pytest.approx(update_mastery(before, True, CFG.bkt))
    assert (row["attempts_n"], row["correct_n"], row["d_max"]) == (4, 3, 3)


@local_room
def test_PM02_right_after_the_last_hint_does_not_count(room: Room):
    # AC-5
    room.script(
        typed_answer=[typed(WRONG), typed(WRONG), typed(RIGHT)],
        check_answer=[classify("incorrect", "sign", 2)] * 2 + [classify("correct")],
        explain_check=["ใบ้หนึ่ง", "ใบ้สอง", "เก่งมาก"],
        generate_problem=[generated()],
    )

    room.say("(x-7)(x-7)")
    room.say("(x-7)(x-7)")
    assert limit_row(room) is None  # hints: the problem goes on
    room.say("x^2-49 = (x-7)(x+7)")

    assert limit_row(room) is None


@local_room
def test_PM02_continue_does_not_count(room: Room):
    # AC-6: an unfinished step
    room.script(
        typed_answer=[typed(["x^2-49", "= (x^2-49)"])],
        check_answer=[classify("incomplete", "concept")],
        explain_check=["แยกต่อได้"],
    )

    room.say("x^2-49 = (x^2-49)")

    assert limit_row(room) is None


def test_PM02_ask_working_does_not_count(room: Room):
    # AC-6: right but no working
    room.script(
        typed_answer=[typed(["(x-7)(x+7)"])],
        check_answer=[classify("correct")],
        explain_check=["ส่งวิธีทำมาด้วยนะ"],
    )

    room.say("(x-7)(x+7)")

    assert limit_row(room) is None


# --- the card of a new room --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("d_max", "passed"), [(TARGET, True), ((TARGET or 1) - 1, False)], ids=["at_target", "below"]
)
def test_TM15_PM03_the_card_of_a_new_room_follows_topic_progress(room: Room, d_max, passed):
    # AC-7
    mastery = min(0.99, CFG.bkt.mastery_threshold + 0.04)
    room.problems.rows[LIMIT.id] = {
        "topic_id": LIMIT.id,
        "mastery": mastery,
        "attempts_n": 5,
        "correct_n": 5,
        "d_max": d_max,
        "level": "developing",
    }
    script(room.fake, open_session=["สวัสดี"])

    events = parse_sse(room.client.post(OPEN).text)

    card = event(events, "progress_card")
    limit = next(t for t in card["topics"] if t["id"] == str(LIMIT.id))
    assert (limit["level"] == "passed") is passed
    assert (card["passed"] == 1) is passed
    assert card["readiness"] > 0


# --- failures ----------------------------------------------------------------------------------


def test_PM02_progress_that_cannot_be_saved_does_not_stop_the_stream(room: Room):
    # AC-8
    room.problems.fail_progress = True
    room.script(**RIGHT_ROUND, generate_problem=[generated()])

    events = room.say("x^2-49 = (x-7)(x+7)")

    assert event(events, "verdict")["verdict"] == "correct"
    assert any(n == "problem" for n, _ in events)
    assert events[-1][0] == "done"
