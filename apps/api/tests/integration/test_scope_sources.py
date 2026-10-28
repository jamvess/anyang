"""Schema for topic page ranges and past-exam mapping notes (migration 0003).

Decisions are in specs/system/data-model.md, "ผลการตัดสิน 2026-10-28" items 1 and 3.
Rows are written with the service role; tenant isolation of topic_sources is proven
in test_rls_isolation.py (SA-06).
"""

import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

import pytest
from supabase import Client, ClientOptions, create_client

from app.settings import EnvSettings

_env = EnvSettings()
_URL = _env.supabase_url
_SERVICE_KEY = _env.supabase_service_role_key.get_secret_value()

if not (_URL and _SERVICE_KEY):
    if os.environ.get("CI"):
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set")
    pytest.skip("Supabase is not configured", allow_module_level=True)


@dataclass
class Prep:
    admin: Client
    tenant_id: str
    exam_prep_id: str

    def insert(self, table: str, row: dict) -> str:
        data = {"tenant_id": self.tenant_id, **row}
        return self.admin.table(table).insert(data).execute().data[0]["id"]

    def material(self, file_name: str) -> str:
        return self.insert(
            "materials",
            {"exam_prep_id": self.exam_prep_id, "storage_path": file_name, "file_name": file_name},
        )

    def topic(self, name: str) -> str:
        return self.insert(
            "topics", {"exam_prep_id": self.exam_prep_id, "name": name, "order_index": 0}
        )


@pytest.fixture
def prep() -> Iterator[Prep]:
    admin = create_client(
        _URL, _SERVICE_KEY, ClientOptions(auto_refresh_token=False, persist_session=False)
    )
    user_id = admin.auth.admin.create_user(
        {"email": f"scope-{uuid.uuid4().hex}@example.test", "email_confirm": True}
    ).user.id
    tenant_id = (
        admin.table("memberships")
        .select("tenant_id")
        .eq("user_id", user_id)
        .single()
        .execute()
        .data["tenant_id"]
    )
    try:
        exam_prep_id = (
            admin.table("exam_preps")
            .insert(
                {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "title": "scope",
                    "exam_date": date.today().isoformat(),
                }
            )
            .execute()
            .data[0]["id"]
        )
        yield Prep(admin, tenant_id, exam_prep_id)
    finally:
        admin.auth.admin.delete_user(user_id)
        admin.table("tenants").delete().eq("id", tenant_id).execute()


def _sources(prep: Prep, topic_id: str) -> list[dict]:
    return (
        prep.admin.table("topic_sources")
        .select("material_id, page_from, page_to")
        .eq("topic_id", topic_id)
        .order("page_from")
        .execute()
        .data
    )


def test_SM04_topic_keeps_page_ranges_across_files(prep: Prep) -> None:
    # Shape seen in P3: t02 -> sheet-01:2-26, sheet-03:1-1, sheet-03:1-2
    sheet1, sheet3 = prep.material("sheet-01.pdf"), prep.material("sheet-03.pdf")
    topic = prep.topic("t02")
    for material_id, page_from, page_to in [(sheet1, 2, 26), (sheet3, 1, 1), (sheet3, 1, 2)]:
        prep.insert(
            "topic_sources",
            {
                "topic_id": topic,
                "material_id": material_id,
                "page_from": page_from,
                "page_to": page_to,
            },
        )

    got = sorted((r["material_id"], r["page_from"], r["page_to"]) for r in _sources(prep, topic))
    assert got == sorted([(sheet1, 2, 26), (sheet3, 1, 1), (sheet3, 1, 2)])


def test_CM10_deleting_a_file_removes_its_page_ranges(prep: Prep) -> None:
    kept, deleted = prep.material("kept.pdf"), prep.material("deleted.pdf")
    topic = prep.topic("t01")
    for material_id in (kept, deleted):
        prep.insert(
            "topic_sources",
            {"topic_id": topic, "material_id": material_id, "page_from": 1, "page_to": 3},
        )

    prep.admin.table("materials").delete().eq("id", deleted).execute()

    assert [r["material_id"] for r in _sources(prep, topic)] == [kept]


def test_CM10_deleting_a_topic_removes_its_page_ranges(prep: Prep) -> None:
    material = prep.material("sheet.pdf")
    topic = prep.topic("t01")
    prep.insert(
        "topic_sources",
        {"topic_id": topic, "material_id": material, "page_from": 1, "page_to": 1},
    )

    prep.admin.table("topics").delete().eq("id", topic).execute()

    assert _sources(prep, topic) == []


@pytest.mark.parametrize(
    ("mapped", "note"),
    [
        (True, "ใช้ Squeeze Theorem"),  # A7 returns a note for mapped questions too
        (False, "ถามเรื่องที่ไม่อยู่ในชีท"),  # unmapped: topic_id is null
        (True, None),  # A7 gave no note
    ],
)
def test_SM04_past_exam_question_keeps_map_note(prep: Prep, mapped: bool, note: str | None) -> None:
    exam = prep.material("midterm-2567.pdf")
    topic = prep.topic("t03") if mapped else None
    question = prep.insert(
        "past_exam_questions",
        {"material_id": exam, "q_no": "ก1.2", "text": "lim", "topic_id": topic, "map_note": note},
    )

    row = (
        prep.admin.table("past_exam_questions")
        .select("topic_id, map_note")
        .eq("id", question)
        .single()
        .execute()
        .data
    )
    assert row == {"topic_id": topic, "map_note": note}
