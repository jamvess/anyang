"""An answer checked in the room with a token, on real Supabase
(specs/features/tutor/room-answers-db.md · AC-tenant, AC-1 on real rows · needs migration 0006).

Same setup as test_room_problems_db.py: the prep and its topic are seeded with the service role,
the API reads and writes with the user's JWT, so RLS decides. The AI is the fake provider;
SymPy is real.
"""

import json

from fastapi.testclient import TestClient
from supabase import Client

from app.ai.gateway import Gateway, get_gateway
from app.ai.providers.fake import FakeProvider
from app.main import app
from app.settings import get_settings
from tests.integration import test_room_sessions_db as room_db
from tests.integration.test_room_problems_db import PROBLEM, seed_prep_with_topic, user_client
from tests.unit.test_tutor_reply_stream_api import parse_sse

admin = room_db.admin
make_user = room_db.make_user
client = room_db.client

LINES = [r"\lim_{x \to 2}\frac{x^{2}-4}{x-2}", r"= \lim_{x \to 2}(x+2)", "= 4"]
CLASSIFY = json.dumps(
    {
        "error_type": None,
        "evidence": "",
        "method": "doc",
        "verdict": "correct",
        "first_wrong_line": None,
        "confidence": 0.9,
    }
)


def scripted_gateway() -> Gateway:
    fake = FakeProvider(
        {
            "generate_problem": [PROBLEM, PROBLEM],
            "open_session": ["สวัสดี เริ่มลิมิตกัน"],
            "typed_answer": [json.dumps({"is_answer": True, "lines": LINES})],
            "check_answer": [CLASSIFY],
            "explain_check": ["เก่งมาก"],
        },
        defaults={"tutor_reply": "ตอบจากติวเตอร์"},
    )
    return Gateway(
        config=get_settings().ai, prompts_dir=get_settings().env.prompts_dir, provider=fake
    )


def test_SA06_PM01_the_answer_is_saved_for_its_user_only(
    admin: Client, make_user, client: TestClient
) -> None:
    # AC-tenant · AC-1 on real rows
    owner, other = make_user(), make_user()
    prep, topic = seed_prep_with_topic(admin, owner)
    gateway = scripted_gateway()
    app.dependency_overrides[get_gateway] = lambda: gateway
    opened = parse_sse(client.post(f"/exam-preps/{prep}/sessions", headers=owner.headers).text)
    session_id = next(d for n, d in opened if n == "session")["session_id"]
    problem_id = next(d for n, d in opened if n == "problem")["problem_id"]

    answered = parse_sse(
        client.post(
            f"/sessions/{session_id}/messages",
            json={"text": " ".join(LINES)},
            headers=owner.headers,
        ).text
    )

    assert next(d for n, d in answered if n == "verdict")["verdict"] == "correct"
    assert next(d for n, d in answered if n == "problem")["problem_id"] != problem_id
    mine = user_client(owner)
    [attempt] = mine.table("attempts").select("*").eq("problem_id", problem_id).execute().data
    assert (attempt["tenant_id"], attempt["user_id"], attempt["topic_id"]) == (
        owner.tenant_id,
        owner.user_id,
        topic,
    )
    assert (attempt["verdict"], attempt["is_correct"]) == ("correct", True)
    [ended] = mine.table("problems").select("ended_at").eq("id", problem_id).execute().data
    assert ended["ended_at"] is not None
    roles = [
        m["role"]
        for m in mine.table("messages").select("role").eq("session_id", session_id).execute().data
    ]
    assert "system" in roles and "user" in roles
    assert user_client(other).table("attempts").select("id").execute().data == []
    intruder = client.post(
        f"/sessions/{session_id}/messages", json={"text": "= 4"}, headers=other.headers
    )
    assert intruder.status_code == 404
