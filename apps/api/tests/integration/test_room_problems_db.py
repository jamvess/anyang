"""The room with a token on real Supabase: card, topic and a verified problem
(specs/features/tutor/room-problems-db.md · AC-tenant, AC-1 on real rows).

Same user setup as test_room_sessions_db.py. Topics and a skill are seeded with the service role
(as ingestion writes them); the API reads and writes with the user's JWT, so RLS decides. The AI
is the fake provider; SymPy is real.
"""

import json
import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient
from supabase import Client, ClientOptions, create_client

from app.ai.gateway import Gateway, get_gateway
from app.ai.providers.fake import FakeProvider
from app.main import app
from app.settings import get_settings
from tests.integration import test_room_sessions_db as room_db
from tests.integration.test_room_sessions_db import _ANON_KEY, _NO_SESSION, _URL, User
from tests.unit.test_tutor_reply_stream_api import parse_sse

# Fixtures of test_room_sessions_db.py: users from the admin API (deleted afterwards), the client.
admin = room_db.admin
make_user = room_db.make_user
client = room_db.client

PROBLEM = json.dumps(
    {
        "text": r"หาค่า $\lim_{x \to 2} \frac{x^2-4}{x-2}$",
        "text_latex": r"\text{หาค่า } \lim_{x \to 2} \frac{x^{2}-4}{x-2}",
        "expression": r"\lim_{x \to 2}\frac{x^{2}-4}{x-2}",
        "answer_format": "expression",
        "reference_answer": "4",
        "solution_steps": ["= x+2", "= 4"],
        "skill": "s1",
    },
    ensure_ascii=False,
)


def user_client(user: User) -> Client:
    c = create_client(_URL, _ANON_KEY, ClientOptions(**_NO_SESSION))
    c.postgrest.auth(user.token)
    return c


def seed_prep_with_topic(admin: Client, user: User) -> tuple[str, str]:
    prep = (
        admin.table("exam_preps")
        .insert(
            {
                "tenant_id": user.tenant_id,
                "user_id": user.user_id,
                "title": "MTH10101",
                "exam_date": (date.today() + timedelta(days=10)).isoformat(),
            }
        )
        .execute()
        .data[0]["id"]
    )
    topic = (
        admin.table("topics")
        .insert(
            {
                "tenant_id": user.tenant_id,
                "exam_prep_id": prep,
                "name": "ลิมิต",
                "order_index": 1,
                "importance": 3,
                "signal_r": 1.0,
            }
        )
        .execute()
        .data[0]["id"]
    )
    admin.table("topic_skills").insert(
        {"tenant_id": user.tenant_id, "topic_id": topic, "name": "ลิมิตรูปแบบ 0/0"}
    ).execute()
    return prep, topic


def scripted_gateway() -> Gateway:
    fake = FakeProvider(
        {"generate_problem": [PROBLEM], "open_session": ["สวัสดี เริ่มลิมิตกัน"]},
        defaults={"tutor_reply": "ตอบจากติวเตอร์"},
    )
    return Gateway(
        config=get_settings().ai, prompts_dir=get_settings().env.prompts_dir, provider=fake
    )


def test_SA06_the_problem_is_saved_for_its_tenant_only(
    admin: Client, make_user, client: TestClient
) -> None:
    # AC-tenant · AC-1 on real rows
    owner, other = make_user(), make_user()
    prep, topic = seed_prep_with_topic(admin, owner)
    gateway = scripted_gateway()
    app.dependency_overrides[get_gateway] = lambda: gateway

    events = parse_sse(client.post(f"/exam-preps/{prep}/sessions", headers=owner.headers).text)

    names = [n for n, _ in events]
    assert "progress_card" in names and "problem" in names
    problem_id = next(d for n, d in events if n == "problem")["problem_id"]
    [row] = user_client(owner).table("problems").select("*").eq("id", problem_id).execute().data
    assert (row["tenant_id"], row["topic_id"], row["verified"]) == (owner.tenant_id, topic, True)
    assert row["source"] == "generated" and row["purpose"] == "probe"
    assert user_client(other).table("problems").select("id").execute().data == []
    response = client.post(f"/exam-preps/{prep}/sessions", headers=other.headers)
    assert response.status_code == 404
    assert uuid.UUID(problem_id)
