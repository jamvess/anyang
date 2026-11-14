"""BKT into topic_progress on real Supabase, for its user only
(specs/features/planner/topic-progress-db.md · AC-tenant · needs migration 0007).

Same setup as test_room_answers_db.py (#132): the prep and its topic are seeded with the service
role, the API reads and writes with the user's JWT, so RLS decides.
"""

from fastapi.testclient import TestClient
from supabase import Client

from app.ai.gateway import get_gateway
from app.main import app
from tests.integration import test_room_sessions_db as room_db
from tests.integration.test_room_answers_db import LINES, scripted_gateway
from tests.integration.test_room_problems_db import seed_prep_with_topic, user_client
from tests.unit.test_tutor_reply_stream_api import parse_sse

admin = room_db.admin
make_user = room_db.make_user
client = room_db.client


def test_SA06_PM02_topic_progress_is_written_for_its_user_only(
    admin: Client, make_user, client: TestClient
) -> None:
    owner, other = make_user(), make_user()
    prep, topic = seed_prep_with_topic(admin, owner)
    gateway = scripted_gateway()
    app.dependency_overrides[get_gateway] = lambda: gateway
    opened = parse_sse(client.post(f"/exam-preps/{prep}/sessions", headers=owner.headers).text)
    session_id = next(d for n, d in opened if n == "session")["session_id"]

    client.post(
        f"/sessions/{session_id}/messages", json={"text": " ".join(LINES)}, headers=owner.headers
    )

    [row] = user_client(owner).table("topic_progress").select("*").execute().data
    assert (row["tenant_id"], row["user_id"], row["topic_id"]) == (
        owner.tenant_id,
        owner.user_id,
        topic,
    )
    assert (row["attempts_n"], row["correct_n"], row["exam_prep_id"]) == (1, 1, prep)
    assert row["d_max"] >= 1
    assert user_client(other).table("topic_progress").select("user_id").execute().data == []
    reopened = parse_sse(client.post(f"/exam-preps/{prep}/sessions", headers=owner.headers).text)
    card = next(d for n, d in reopened if n == "progress_card")
    assert card["topics"][0]["level"] != "not_started"
