"""The next problem differs from the latest problems of its topic
(specs/features/tutor/room-problems-db.md §2.3 v2 · AC-15 to AC-18).

No network. The fakes of #131 and #132, plus `recent_problems`; SymPy is real, so every problem
below is right for real and only its sameness decides.

Interfaces these tests expect (to be built by /implement-feature):
- `ProblemRepository.recent_problems(prep_id, topic_id, limit) -> list[ProblemRecord]`: the
  topic's problems in the prep, newest first, ended or not
- `app.domain.room.same_problem(text, other) -> bool`
- `session.avoid_recent_problems` in config/learning.yaml
- prompt `generate_problem/v2` with the data block `previous_problems`
"""

import json
import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from app.db.room_problems import ProblemRecord, get_problem_repository
from app.domain import room as domain_room
from app.main import app
from app.services.dev_uploads import get_local_mode
from tests.unit import test_room_sessions_api as room_api
from tests.unit.test_room_answers_db import AnswerProblemRepo, classify, typed
from tests.unit.test_room_problems_api import (
    FACTOR,
    LIMIT,
    NO_PROBLEM,
    OPEN,
    SETTINGS,
    block,
    event,
    names,
    requests,
    script,
)
from tests.unit.test_room_sessions_api import FakeRoomRepo, send
from tests.unit.test_tutor_reply_stream_api import parse_sse, tokens

client = room_api.client
fake = room_api.fake
no_retry_sleep = room_api.no_retry_sleep
repo = room_api.repo
signed_in = room_api.signed_in

NEXT = "ข้อต่อไปนะ"
# Three limits SymPy verifies: (text, expression, reference answer).
TO_2 = (r"หาค่า $\lim_{x \to 2} \frac{x^2-4}{x-2}$", r"\lim_{x \to 2}\frac{x^{2}-4}{x-2}", "4")
TO_3 = (r"หาค่า $\lim_{x \to 3} \frac{x^2-9}{x-3}$", r"\lim_{x \to 3}\frac{x^{2}-9}{x-3}", "6")
TO_1 = (r"หาค่า $\lim_{x \to 1} \frac{x^2-1}{x-1}$", r"\lim_{x \to 1}\frac{x^{2}-1}{x-1}", "2")


def generated(problem: tuple[str, str, str], text: str | None = None) -> str:
    """A `generate_problem` reply for one of the limits above; ``text`` replaces its text."""
    shown, expression, reference = problem
    return json.dumps(
        {
            "text": text or shown,
            "text_latex": r"\text{หาค่า } " + expression,
            "expression": expression,
            "answer_format": "expression",
            "reference_answer": reference,
            "solution_steps": [f"= {reference}"],
            "skill": None,
        },
        ensure_ascii=False,
    )


@dataclass
class RecentProblemRepo(AnswerProblemRepo):
    """#132's fake plus `recent_problems`."""

    def recent_problems(self, prep_id, topic_id, limit: int) -> list[ProblemRecord]:
        mine = [p for p in self.problems if p.topic_id == topic_id]
        return list(reversed(mine))[:limit]


def record(problem: tuple[str, str, str], topic=LIMIT, session_id=None) -> ProblemRecord:
    return ProblemRecord(
        id=uuid.uuid4(),
        session_id=session_id or uuid.uuid4(),
        topic_id=topic.id,
        skill_id=None,
        text=problem[0],
        reference_answer=problem[2],
        solution_steps=[f"= {problem[2]}"],
        answer_format="expression",
        difficulty=3,
        purpose="practice",
    )


@pytest.fixture
def problems(signed_in) -> RecentProblemRepo:
    store = RecentProblemRepo()
    app.dependency_overrides[get_problem_repository] = lambda: store
    return store


def ended(store: RecentProblemRepo, *rows: ProblemRecord) -> None:
    for row in rows:
        store.problems.append(row)
        store.ended.add(row.id)


def avoid(monkeypatch, n: int) -> None:
    # The config is frozen: the service gets a copy (as AC-boundary of #131 · Jam ok 13 Nov).
    session = SETTINGS.learning.session.model_copy(update={"avoid_recent_problems": n})
    learning = SETTINGS.learning.model_copy(update={"session": session})
    settings = SETTINGS.model_copy(update={"learning": learning})
    monkeypatch.setattr("app.services.room_problems.get_settings", lambda: settings)


# --- the input ---------------------------------------------------------------------------------


def test_AM11_generate_problem_gets_the_latest_problems_of_its_topic(
    signed_in, problems, fake, monkeypatch
):
    # AC-15: 3 of the topic in 2 sessions (all ended here, so a new one is made), 1 of another
    avoid(monkeypatch, 2)
    earlier = uuid.uuid4()
    ended(problems, record(TO_2, session_id=earlier), record(TO_3, session_id=earlier))
    ended(problems, record(TO_1), record(TO_2, topic=FACTOR))
    script(fake, generate_problem=[generated(TO_2)], open_session=["สวัสดี"])

    parse_sse(signed_in.post(OPEN).text)

    [request] = requests(fake, "generate_problem")
    assert block(request, "previous_problems") == f"- {TO_1[0]}\n- {TO_3[0]}"


def test_AM11_a_topic_with_no_problems_has_none_before(signed_in, problems, fake):
    # AC-15
    script(fake, generate_problem=[generated(TO_2)], open_session=["สวัสดี"])

    parse_sse(signed_in.post(OPEN).text)

    [request] = requests(fake, "generate_problem")
    assert block(request, "previous_problems") == "none"


# --- sameness ----------------------------------------------------------------------------------


def test_AM11_a_problem_like_one_before_counts_as_a_try(signed_in, problems, fake):
    # AC-16: only the spaces differ
    ended(problems, record(TO_2))
    spaced = r"หาค่า  $\lim_{x\to 2}\frac{x^2-4}{x-2}$ "
    script(
        fake,
        generate_problem=[generated(TO_2, text=spaced), generated(TO_3)],
        open_session=["สวัสดี"],
    )

    events = parse_sse(signed_in.post(OPEN).text)

    assert len(requests(fake, "generate_problem")) == 2
    saved = problems.problems[-1]
    assert saved.text == TO_3[0]
    assert event(events, "problem")["problem_id"] == str(saved.id)


@pytest.mark.parametrize(
    ("text", "other", "same"),
    [
        (r"หาค่า $\lim_{x \to 2} x^2$", r"หาค่า  $\lim_{x\to 2} x^2$", True),
        (r"หาค่า $\lim_{x \to 2} x^2$", r"จงหาค่าของ $\lim_{x \to 2} x^2$", True),
        (r"หาค่า $\lim_{x \to 1} x^2$", r"หาค่า $\lim_{x \to 2} x^2$", False),
        ("แยกตัวประกอบพหุนามของข้อที่แล้ว", "แยกตัวประกอบพหุนามของ ข้อที่แล้ว", True),
        ("แยกตัวประกอบพหุนามของข้อที่แล้ว", "หาอนุพันธ์ของข้อที่แล้ว", False),
    ],
    ids=["spaces", "other_words", "other_numbers", "no_math_same", "no_math_other"],
)
def test_AM11_same_problem(text, other, same):
    # AC-17
    assert domain_room.same_problem(text, other) is same
    assert domain_room.same_problem(other, text) is same


def test_AM11_only_problems_like_before_gives_no_problem(signed_in, problems, fake, monkeypatch):
    # AC-18: every try is the problem before
    ended(problems, record(TO_2))
    tries = 1 + SETTINGS.learning.checker.max_generate_retries
    script(fake, generate_problem=[generated(TO_2)] * tries, open_session=["สวัสดี"])

    events = parse_sse(signed_in.post(OPEN).text)

    assert len(requests(fake, "generate_problem")) == tries
    assert "problem" not in names(events)
    assert tokens(events)[-1] == NO_PROBLEM


# --- the bug of the live run (room-answers-db.md §8) -------------------------------------------


def test_AM11_the_next_problem_after_an_answer_is_not_the_same_again(
    signed_in, repo: FakeRoomRepo, problems, fake
):
    # AC-16 after a right answer: the model first gives the problem just ended
    app.dependency_overrides[get_local_mode] = lambda: False
    session = repo.add_session()
    problems.problems.append(record(TO_2, session_id=session.id))
    script(
        fake,
        typed_answer=[
            typed([r"\lim_{x \to 2}\frac{x^{2}-4}{x-2}", "= \\lim_{x \\to 2}(x+2)", "= 4"])
        ],
        check_answer=[classify("correct")],
        explain_check=["เก่งมาก"],
        generate_problem=[generated(TO_2), generated(TO_1)],
    )

    events: list[tuple[str, Any]] = parse_sse(send(signed_in, session.id, "= 4").text)

    assert ("token", {"speaker": "tutor", "text": NEXT}) in events
    assert problems.problems[-1].text == TO_1[0]
    assert event(events, "problem")["problem_id"] == str(problems.problems[-1].id)


# --- added by the self-review of PR #133 -----------------------------------------------------


@pytest.mark.parametrize(
    ("text", "other"),
    [
        (r"หาค่า $\lim_{x \to 2} \frac{x^2-4}{x-2}$", r"หาค่า $\lim_{x\to 2}\dfrac{x^{2}-4}{x-2}$"),
        (r"หาค่า $\lim_{x \to 2} (x+1)$", r"หาค่า $\lim\limits_{x \to 2} \left(x+1\right)$"),
        ("แยกตัวประกอบพหุนามของข้อที่แล้ว", "แยกตัวประกอบ​พหุนามของข้อที่แล้ว"),
    ],
    ids=["dfrac_and_braces", "left_right_limits", "zero_width_space"],
)
def test_AM11_the_same_latex_written_another_way_is_the_same_problem(text, other):
    assert domain_room.same_problem(text, other)
    assert not domain_room.same_problem(text, r"หาค่า $\lim_{x \to 3} (x+1)$")
