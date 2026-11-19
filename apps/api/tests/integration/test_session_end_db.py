"""Ending the session on real Supabase, for its user only
(specs/features/tutor/session-end-db.md · AC-tenant, AC-6 on real rows).

Same setup as test_room_answers_db.py (#132): the API reads and writes with the user's JWT.
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

LINES = ["วันนี้ทำลิมิตไปแล้ว", "ครั้งหน้ามาต่อกัน"]


def scripted_gateway() -> Gateway:
    fake = FakeProvider(
        {
            "generate_problem": [PROBLEM],
            "open_session": ["สวัสดี"],
            "session_summary": [json.dumps({"lines": LINES}, ensure_ascii=False)],
        }
    )
    return Gateway(
        config=get_settings().ai, prompts_dir=get_settings().env.prompts_dir, provider=fake
    )


def test_SA06_PM05_a_session_is_ended_by_its_user_only(
    admin: Client, make_user, client: TestClient
) -> None:
    owner, other = make_user(), make_user()
    prep, _ = seed_prep_with_topic(admin, owner)
    gateway = scripted_gateway()
    app.dependency_overrides[get_gateway] = lambda: gateway
    opened = parse_sse(client.post(f"/exam-preps/{prep}/sessions", headers=owner.headers).text)
    session_id = next(d for n, d in opened if n == "session")["session_id"]

    intruder = client.post(f"/sessions/{session_id}/end", headers=other.headers)
    ended = parse_sse(client.post(f"/sessions/{session_id}/end", headers=owner.headers).text)
    again = client.post(f"/sessions/{session_id}/end", headers=owner.headers)

    assert intruder.status_code == 404
    assert next(d for n, d in ended if n == "session_end") == {"summary_lines": LINES}
    [row] = (
        user_client(owner).table("tutor_sessions").select("*").eq("id", session_id).execute().data
    )
    assert row["ended_at"] is not None
    assert (row["end_reason"], row["summary"]) == ("user", "\n".join(LINES))
    assert again.status_code == 409
    mine = user_client(owner).table("messages").select("content").eq("session_id", session_id)
    assert "\n".join(LINES) in [m["content"] for m in mine.execute().data]
    theirs = user_client(other).table("messages").select("id").eq("session_id", session_id)
    assert theirs.execute().data == []
