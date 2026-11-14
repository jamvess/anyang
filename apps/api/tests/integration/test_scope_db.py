"""The scope page on real Supabase, for its user only
(specs/features/scope/scope-db.md · AC-tenant, AC-6 on real rows).

Same setup as test_room_problems_db.py: the prep and its topic are seeded with the service role,
the API reads and writes with the user's JWT, so RLS decides.
"""

from fastapi.testclient import TestClient
from supabase import Client

from app.ai.gateway import get_gateway
from app.main import app
from tests.integration import test_room_sessions_db as room_db
from tests.integration.test_room_problems_db import (
    scripted_gateway,
    seed_prep_with_topic,
    user_client,
)
from tests.unit.test_tutor_reply_stream_api import parse_sse

admin = room_db.admin
make_user = room_db.make_user
client = room_db.client


def test_SA06_SM09_the_scope_is_read_and_confirmed_by_its_user_only(
    admin: Client, make_user, client: TestClient
) -> None:
    owner, other = make_user(), make_user()
    prep, topic = seed_prep_with_topic(admin, owner)
    app.dependency_overrides[get_gateway] = scripted_gateway

    read = client.get(f"/exam-preps/{prep}/scope", headers=owner.headers)
    theirs = client.get(f"/exam-preps/{prep}/scope", headers=other.headers)
    intruder = client.post(f"/exam-preps/{prep}/scope/confirm", headers=other.headers)
    confirmed = client.post(f"/exam-preps/{prep}/scope/confirm", headers=owner.headers)

    assert read.status_code == 200
    assert [t["id"] for t in read.json()["topics"]] == [topic]
    assert theirs.status_code == 404
    assert intruder.status_code == 404
    assert confirmed.status_code == 200
    version_id = confirmed.json()["scope_version_id"]
    [row] = user_client(owner).table("scope_versions").select("*").execute().data
    assert (row["id"], row["tenant_id"], row["status"], row["version"]) == (
        version_id,
        owner.tenant_id,
        "confirmed",
        1,
    )
    assert user_client(other).table("scope_versions").select("id").execute().data == []
    [prep_row] = (
        user_client(owner).table("exam_preps").select("active_scope_version_id").execute().data
    )
    assert prep_row["active_scope_version_id"] == version_id
    opened = parse_sse(client.post(f"/exam-preps/{prep}/sessions", headers=owner.headers).text)
    session_id = next(d for n, d in opened if n == "session")["session_id"]
    [session] = (
        user_client(owner)
        .table("tutor_sessions")
        .select("scope_version_id")
        .eq("id", session_id)
        .execute()
        .data
    )
    assert session["scope_version_id"] == version_id
