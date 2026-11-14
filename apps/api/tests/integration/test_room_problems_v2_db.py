"""`recent_problems` on real Supabase: newest first, the limit, the topic, and RLS
(specs/features/tutor/room-problems-db.md §2.3 v2 · AC-15 on real rows · self-review PR #133).

Rows are seeded with the service role; the repository reads with the user's JWT.
"""

import uuid

from supabase import Client

from app.db.room_problems import SupabaseProblemRepository
from tests.integration import test_room_sessions_db as room_db
from tests.integration.test_room_problems_db import seed_prep_with_topic, user_client
from tests.integration.test_room_sessions_db import User

admin = room_db.admin
make_user = room_db.make_user


def seed_problems(admin: Client, user: User, prep: str, topic: str, texts: list[str]) -> None:
    session = (
        admin.table("tutor_sessions")
        .insert({"tenant_id": user.tenant_id, "user_id": user.user_id, "exam_prep_id": prep})
        .execute()
        .data[0]["id"]
    )
    for text in texts:  # one insert each, so created_at grows in this order
        admin.table("problems").insert(
            {
                "tenant_id": user.tenant_id,
                "session_id": session,
                "topic_id": topic,
                "source": "generated",
                "text": text,
                "reference_answer": "4",
                "answer_format": "expression",
                "difficulty": 3,
                "purpose": "practice",
            }
        ).execute()


def test_AM11_SA06_recent_problems_are_the_latest_of_the_topic_for_its_tenant_only(
    admin: Client, make_user
) -> None:
    owner, other = make_user(), make_user()
    prep, topic = seed_prep_with_topic(admin, owner)
    seed_problems(admin, owner, prep, topic, ["ข้อแรก", "ข้อสอง", "ข้อสาม"])

    mine = SupabaseProblemRepository(lambda: user_client(owner))
    theirs = SupabaseProblemRepository(lambda: user_client(other))

    latest = mine.recent_problems(uuid.UUID(prep), uuid.UUID(topic), 2)
    assert [p.text for p in latest] == ["ข้อสาม", "ข้อสอง"]
    assert mine.recent_problems(uuid.UUID(prep), uuid.UUID(topic), 0) == []
    assert theirs.recent_problems(uuid.UUID(prep), uuid.UUID(topic), 5) == []
