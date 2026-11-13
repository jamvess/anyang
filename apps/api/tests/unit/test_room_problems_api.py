"""Opening the room with a token when the prep has topics: card, chosen topic, verified problem
(specs/features/tutor/room-problems-db.md §2.2-2.4 · AC-1, AC-3 to AC-13).

No network. The room repository is the fake of test_room_sessions_api.py (#123); the new reads go
through a second fake, `FakeProblemRepo`, installed with `get_problem_repository`. SymPy is the
real one, so the generated problems below are right or wrong for real.

Interfaces these tests expect (to be built by /implement-feature):
- `app.db.room_problems`: `ProgressFacts(topic_id, mastery, attempts_n, level, d_max)`,
  `SkillFacts(id, name)`, `ProblemRecord(id, session_id, topic_id, skill_id, text,
  reference_answer, solution_steps, answer_format, difficulty, purpose)`, the protocol
  `ProblemRepository` (methods as in `FakeProblemRepo`) and the dependency
  `get_problem_repository` (None unless the room repository is the Supabase one, so the #123
  tests keep their behavior)
- `app.domain.room.TopicFacts` (see test_room_problems.py)
- `app.models.tutor_ai.GenerateProblemResult`
- `get_settings().messages.room.no_problem` (config/messages.yaml → room.no_problem)
- prompts `generate_problem/v1`, `open_session/v2` (input `focus`)
"""

import json
import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.db.exam_preps import DbUnavailableError
from app.db.room_problems import ProblemRecord, ProgressFacts, SkillFacts, get_problem_repository
from app.domain.bkt import target_difficulty
from app.domain.room import TopicFacts
from app.main import app
from app.settings import get_settings
from tests.unit import test_room_sessions_api as room_api
from tests.unit.test_room_sessions_api import (
    PREP_ID,
    USER,
    FakeRoomRepo,
    expected_greeting,
    send,
)
from tests.unit.test_tutor_reply_stream_api import parse_sse, tokens

# Fixtures of test_room_sessions_api.py (#123): fake room repository, provider, client, a user.
client = room_api.client
fake = room_api.fake
no_retry_sleep = room_api.no_retry_sleep
repo = room_api.repo
signed_in = room_api.signed_in

SETTINGS = get_settings()
P_INIT = SETTINGS.learning.bkt.p_init
NO_PROBLEM = SETTINGS.messages.room.no_problem
OPEN = f"/exam-preps/{PREP_ID}/sessions"

LIMIT = TopicFacts(uuid.uuid4(), "ลิมิต", 1, 3, "draft", "doc")
FACTOR = TopicFacts(uuid.uuid4(), "แยกตัวประกอบ", 2, 2, "draft", "doc")
GRAPH = TopicFacts(uuid.uuid4(), "กราฟ", 3, 1, "draft", "doc")
SKILL = SkillFacts(uuid.uuid4(), "ลิมิตรูปแบบ 0/0")


@dataclass
class FakeProblemRepo:
    """The rows the user's JWT can see (RLS)."""

    topics: list[TopicFacts] = field(default_factory=lambda: [LIMIT, FACTOR, GRAPH])
    progress: list[ProgressFacts] = field(default_factory=list)
    skills: dict[uuid.UUID, list[SkillFacts]] = field(default_factory=lambda: {LIMIT.id: [SKILL]})
    chunks: dict[uuid.UUID, list[str]] = field(default_factory=dict)
    problems: list[ProblemRecord] = field(default_factory=list)
    answered: set[uuid.UUID] = field(default_factory=set)  # problem ids with an attempt
    prep_of_session: dict[uuid.UUID, uuid.UUID] = field(default_factory=dict)
    fail_insert: bool = False
    chunk_limits: list[int] = field(default_factory=list)
    inserted: list[dict[str, Any]] = field(default_factory=list)  # what add_problem got

    def list_topics(self, prep_id: uuid.UUID) -> list[TopicFacts]:
        return list(self.topics) if prep_id == PREP_ID else []

    def list_progress(self, prep_id: uuid.UUID) -> list[ProgressFacts]:
        return list(self.progress)

    def list_skills(self, topic_id: uuid.UUID) -> list[SkillFacts]:
        return list(self.skills.get(topic_id, []))

    def source_chunks(self, topic_id: uuid.UUID, limit: int) -> list[str]:
        self.chunk_limits.append(limit)
        return self.chunks.get(topic_id, [])[:limit]

    def open_problem(self, prep_id: uuid.UUID, topic_id: uuid.UUID) -> ProblemRecord | None:
        mine = [p for p in self.problems if p.topic_id == topic_id and p.id not in self.answered]
        return mine[-1] if mine else None

    def session_problem(self, session_id: uuid.UUID) -> ProblemRecord | None:
        mine = [
            p for p in self.problems if p.session_id == session_id and p.id not in self.answered
        ]
        return mine[-1] if mine else None

    def topic_has_problems(self, prep_id: uuid.UUID, topic_id: uuid.UUID) -> bool:
        return any(p.topic_id == topic_id for p in self.problems)

    def add_problem(self, **fields: Any) -> ProblemRecord:
        """Keyword fields: the `problems` columns (tenant_id, session_id, topic_id, skill_id,
        source, text, reference_answer, solution_steps, answer_format, verified, difficulty,
        purpose)."""
        if self.fail_insert:
            raise DbUnavailableError("insert problems")
        self.inserted.append(dict(fields))
        record = ProblemRecord(
            id=uuid.uuid4(),
            **{k: fields[k] for k in ProblemRecord.__dataclass_fields__ if k != "id"},
        )
        self.problems.append(record)
        return record


def generated(
    expression: str = r"\lim_{x \to 2}\frac{x^{2}-4}{x-2}",
    reference: str = "4",
    answer_format: str = "expression",
    skill: str | None = "s1",
) -> str:
    return json.dumps(
        {
            "text": r"หาค่า $\lim_{x \to 2} \frac{x^2-4}{x-2}$",
            "text_latex": r"\text{หาค่า } \lim_{x \to 2} \frac{x^{2}-4}{x-2}",
            "expression": expression,
            "answer_format": answer_format,
            "reference_answer": reference,
            "solution_steps": [r"\frac{(x-2)(x+2)}{x-2}", "= x+2", "= 4"],
            "skill": skill,
        },
        ensure_ascii=False,
    )


WRONG = generated(reference="5")


@pytest.fixture
def problems(signed_in: TestClient) -> Iterator[FakeProblemRepo]:
    store = FakeProblemRepo()
    app.dependency_overrides[get_problem_repository] = lambda: store
    yield store


def script(fake, **purposes: list[Any]) -> None:
    for purpose, replies in purposes.items():
        fake._script[purpose] = list(replies)


def requests(fake, purpose: str) -> list[Any]:
    return [r for r in fake.requests if r.purpose == purpose]


def block(request: Any, name: str) -> str:
    match = re.search(rf'<document name="{name}">\n(.*?)\n</document>', request.prompt, re.DOTALL)
    assert match, f"no {name} block"
    return match.group(1)


def names(events: list[tuple[str, Any]]) -> list[str]:
    return [n for n, _ in events]


def event(events: list[tuple[str, Any]], name: str) -> Any:
    return next(d for n, d in events if n == name)


# --- opening ------------------------------------------------------------------------------------


def test_TM15_AM11_the_room_opens_with_a_card_a_greeting_and_a_verified_problem(
    signed_in, problems, fake
):
    # AC-1
    script(fake, generate_problem=[generated()], open_session=["สวัสดี เริ่มลิมิตกัน"])

    events = parse_sse(signed_in.post(OPEN).text)

    order = [n for i, n in enumerate(names(events)) if i == 0 or n != names(events)[i - 1]]
    assert order == ["session", "progress_card", "token", "problem", "done"]
    card = event(events, "progress_card")
    assert [t["id"] for t in card["topics"]] == [str(LIMIT.id), str(FACTOR.id), str(GRAPH.id)]
    assert {t["level"] for t in card["topics"]} == {"not_started"}
    assert (card["readiness"], card["passed"], card["total"]) == (0, 0, 3)
    assert card["days_left"] == 27
    [row] = problems.problems
    [fields] = problems.inserted
    assert (fields["tenant_id"], fields["session_id"]) == (
        USER.tenant_id,
        uuid.UUID(events[0][1]["session_id"]),
    )
    assert (fields["source"], fields["verified"]) == ("generated", True)
    assert row.topic_id == LIMIT.id
    assert (row.purpose, row.difficulty) == (
        "probe",
        target_difficulty(3, "normal", SETTINGS.learning),
    )
    assert row.skill_id == SKILL.id
    assert row.reference_answer == "4"
    card_event = event(events, "problem")
    assert card_event == {
        "problem_id": str(row.id),
        "text_latex": r"\text{หาค่า } \lim_{x \to 2} \frac{x^{2}-4}{x-2}",
        "difficulty": row.difficulty,
        "purpose": "probe",
    }


def test_TM02_AM13_open_session_gets_the_focus_and_the_problem_without_its_answer(
    signed_in, problems, fake
):
    # AC-3
    script(fake, generate_problem=[generated()], open_session=["สวัสดี"])

    parse_sse(signed_in.post(OPEN).text)

    [greeting] = requests(fake, "open_session")
    assert block(greeting, "focus") == "ลิมิต · 3 ดาว · ยังไม่เริ่ม"
    assert r"\lim" in block(greeting, "problem")
    assert "= x+2" not in greeting.prompt  # no solution step
    assert "= 4" not in greeting.prompt  # no answer


def test_SM11_generate_problem_gets_the_topic_skills_difficulty_and_its_own_pages(
    signed_in, problems, fake
):
    # AC-4
    limit = SETTINGS.learning.session.grounding_chunks
    problems.chunks = {LIMIT.id: [f"หน้า {n} ของลิมิต" for n in range(limit + 2)], FACTOR.id: ["ไม่ใช่"]}
    problems.skills[LIMIT.id] = [SKILL, SkillFacts(uuid.uuid4(), "ลิมิตที่อนันต์")]
    script(fake, generate_problem=[generated()], open_session=["สวัสดี"])

    parse_sse(signed_in.post(OPEN).text)

    [request] = requests(fake, "generate_problem")
    assert block(request, "topic") == "ลิมิต"
    assert block(request, "skills") == "s1: ลิมิตรูปแบบ 0/0\ns2: ลิมิตที่อนันต์"
    assert block(request, "difficulty") == str(target_difficulty(3, "normal", SETTINGS.learning))
    source = block(request, "source_text")
    assert f"หน้า {limit - 1} ของลิมิต" in source
    assert f"หน้า {limit} ของลิมิต" not in source
    assert "ไม่ใช่" not in source
    assert problems.chunk_limits == [limit]


def test_AM11_a_wrong_answer_is_generated_again(signed_in, problems, fake):
    # AC-5
    script(fake, generate_problem=[WRONG, generated()], open_session=["สวัสดี"])

    events = parse_sse(signed_in.post(OPEN).text)

    assert len(requests(fake, "generate_problem")) == 2
    [row] = problems.problems
    assert row.reference_answer == "4"
    assert event(events, "problem")["problem_id"] == str(row.id)


@pytest.mark.parametrize("retries", [0, 2])
def test_AM11_no_problem_after_the_last_try(signed_in, problems, fake, monkeypatch, retries):
    # AC-boundary
    # The config is frozen: the service gets a copy with this retry count (Jam ok 13 Nov).
    checker = SETTINGS.learning.checker.model_copy(update={"max_generate_retries": retries})
    learning = SETTINGS.learning.model_copy(update={"checker": checker})
    settings = SETTINGS.model_copy(update={"learning": learning})
    monkeypatch.setattr("app.services.room_problems.get_settings", lambda: settings)
    script(fake, generate_problem=[WRONG] * (retries + 1), open_session=["สวัสดี"])

    events = parse_sse(signed_in.post(OPEN).text)

    assert len(requests(fake, "generate_problem")) == retries + 1
    assert "problem" not in names(events)
    assert problems.problems == []
    assert tokens(events)[-1] == NO_PROBLEM
    assert block(requests(fake, "open_session")[0], "problem") == "none"
    assert names(events)[-1] == "done"


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(generated(r"x^{3}-x", r"x(x^{2}-1)", "factored"), id="not fully factored"),
        pytest.param(generated("หาค่าลิมิตนี้", "4"), id="expression does not parse"),
        pytest.param(RuntimeError("down"), id="the model fails"),
    ],
)
def test_AM11_these_do_not_pass_and_count_as_a_try(signed_in, problems, fake, bad):
    # AC-6
    script(
        fake,
        generate_problem=[bad, generated(r"x^{3}-x", r"x(x-1)(x+1)", "factored")],
        open_session=["สวัสดี"],
    )

    parse_sse(signed_in.post(OPEN).text)

    assert len(requests(fake, "generate_problem")) == 2
    [row] = problems.problems
    assert (row.answer_format, row.reference_answer) == ("factored", "x(x-1)(x+1)")


@pytest.mark.parametrize("skill", ["s9", None])
def test_AM11_an_unknown_skill_keeps_the_problem_without_one(signed_in, problems, fake, skill):
    # AC-7
    script(fake, generate_problem=[generated(skill=skill)], open_session=["สวัสดี"])

    parse_sse(signed_in.post(OPEN).text)

    [row] = problems.problems
    assert row.skill_id is None


def test_TM13_an_open_problem_of_the_topic_is_used_again(signed_in, problems, fake):
    # AC-8
    old = ProblemRecord(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        topic_id=LIMIT.id,
        skill_id=None,
        text=r"หาค่า $\lim_{x \to 1} (x+1)$",
        reference_answer="2",
        solution_steps=["= 2"],
        answer_format="expression",
        difficulty=3,
        purpose="probe",
    )
    problems.problems.append(old)
    script(fake, open_session=["สวัสดี"])

    events = parse_sse(signed_in.post(OPEN).text)

    assert requests(fake, "generate_problem") == []
    assert problems.problems == [old]
    shown = event(events, "problem")
    assert shown["problem_id"] == str(old.id)
    assert shown["text_latex"] == r"\text{หาค่า } \lim_{x \to 1} (x+1)"


def test_TM03_a_topic_already_practised_gets_a_practice_problem(signed_in, problems, fake):
    # AC-9
    done = ProblemRecord(
        uuid.uuid4(), uuid.uuid4(), LIMIT.id, None, "เก่า", "1", [], "expression", 3, "probe"
    )
    problems.problems.append(done)
    problems.answered.add(done.id)
    script(fake, generate_problem=[generated()], open_session=["สวัสดี"])

    parse_sse(signed_in.post(OPEN).text)

    assert problems.problems[-1].purpose == "practice"


def test_TM13_a_prep_without_topics_opens_as_before(signed_in, problems, fake):
    # AC-10
    problems.topics = []

    events = parse_sse(signed_in.post(OPEN).text)

    assert set(names(events)) == {"session", "token", "done"}
    assert "".join(tokens(events)) == expected_greeting(None)
    assert fake.requests == []


def test_TM15_a_failed_greeting_still_gives_the_card_and_the_problem(signed_in, problems, fake):
    # AC-11
    script(fake, generate_problem=[generated()], open_session=[RuntimeError("down")])

    events = parse_sse(signed_in.post(OPEN).text)

    assert "".join(tokens(events)) == expected_greeting(None)
    assert {"progress_card", "problem", "done"} <= set(names(events))


def test_AM11_a_problem_that_cannot_be_saved_is_not_shown(signed_in, problems, fake):
    # AC-12
    problems.fail_insert = True
    script(fake, generate_problem=[generated()], open_session=["สวัสดี"])

    events = parse_sse(signed_in.post(OPEN).text)

    assert "problem" not in names(events)
    assert tokens(events)[-1] == NO_PROBLEM


# --- typed messages -----------------------------------------------------------------------------


def test_TM10_AM13_the_tutor_knows_the_open_problem_without_its_answer(
    signed_in, problems, fake, repo: FakeRoomRepo
):
    # AC-13
    session = repo.add_session()
    problems.problems.append(
        ProblemRecord(
            uuid.uuid4(),
            session.id,
            LIMIT.id,
            None,
            r"หาค่า $\lim_{x \to 3} x^2$",
            "9",
            ["= 9"],
            "expression",
            3,
            "probe",
        )
    )

    send(signed_in, session.id, "เริ่มยังไง")

    [reply] = requests(fake, "tutor_reply")
    assert block(reply, "problem") == r"หาค่า $\lim_{x \to 3} x^2$"
    assert "= 9" not in reply.prompt


def test_TM10_no_open_problem_is_none(signed_in, problems, fake, repo: FakeRoomRepo):
    # AC-13
    session = repo.add_session()

    send(signed_in, session.id, "สวัสดี")

    [reply] = requests(fake, "tutor_reply")
    assert block(reply, "problem") == "none"
