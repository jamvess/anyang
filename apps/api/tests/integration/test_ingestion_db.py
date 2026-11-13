"""Ingestion against real Supabase (specs/features/scope/ingestion.md · AC-tenant, AC-18).

The job writes with the service role and sets `tenant_id` itself (spec §2.1 item 4); the API
reads with the user's JWT, so RLS decides. Same user setup as test_room_sessions_db.py. The AI
and the documents are the fakes of test_ingestion_pipeline.py (no network, no real PDF).
Needs migration 0005 (`ingestion_jobs.material_id` may be null, `exam_prep_id`).

Interfaces these tests expect (to be built by /implement-feature):
- `app.db.ingestion.SupabaseIngestionStore(connect)` (service-role client), implementing the
  same store protocol as `InMemoryIngestionStore`
"""

import uuid
from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from supabase import Client, ClientOptions, create_client

from app.auth import TokenVerifier, get_auth_required, get_verifier
from app.db.ingestion import SupabaseIngestionStore
from app.main import app
from app.services.ingestion import IngestionDeps, build_scope, ingest_material
from app.services.material_files import InMemoryMaterialFiles
from tests.integration import test_room_sessions_db as room_db
from tests.integration.test_room_sessions_db import _ANON_KEY, _NO_SESSION, _URL, User
from tests.unit.test_ingestion_pipeline import (
    JUNK_PAGE,
    THAI_PAGE,
    TWO_TOPICS,
    FakeDocuments,
    Provider,
    local,
    make_gateway,
    mapping,
    split,
    vision_pages,
)

# Fixtures of test_room_sessions_db.py: users from the admin API, deleted afterwards.
admin = room_db.admin
make_user = room_db.make_user


def user_client(user: User) -> Client:
    client = create_client(_URL, _ANON_KEY, ClientOptions(**_NO_SESSION))
    client.postgrest.auth(user.token)
    return client


@pytest.fixture
def api() -> Iterator[TestClient]:
    verifier = TokenVerifier(_URL, _ANON_KEY)
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_auth_required] = lambda: True
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def seed(admin: Client, user: User, blobs: dict[str, bytes], pages: dict[bytes, list[str]]) -> str:
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
    for name, kind, texts in (
        ("sheet-01.pdf", "sheet", [THAI_PAGE, THAI_PAGE]),
        ("sheet-02.pdf", "sheet", [THAI_PAGE]),
        ("midterm.pdf", "past_exam", [JUNK_PAGE, JUNK_PAGE]),
    ):
        path = f"{user.tenant_id}/{prep}/{name}"
        data = f"{prep} {name}".encode()
        blobs[path] = data
        pages[data] = texts
        admin.table("materials").insert(
            {
                "tenant_id": user.tenant_id,
                "exam_prep_id": prep,
                "storage_path": path,
                "file_name": name,
                "kind": kind,
                "kind_confirmed": True,
                "status": "confirmed",
            }
        ).execute()
    return prep


def deps_for(admin: Client, blobs, pages, rounds: int = 1) -> IngestionDeps:
    provider = Provider(
        {
            "vision_extract_pages": [vision_pages(2)],
            "split_past_exam": [split("1", "2")],
            "extract_topics_local": [local(("ลิมิต", "1-2")), local(("อนุพันธ์", "1-1"))] * rounds,
            "merge_topics": [TWO_TOPICS] * rounds,
            "map_questions": [mapping(("f3:1", "t01", ""), ("f3:2", "t02", ""))] * rounds,
        }
    )
    return IngestionDeps(
        gateway=make_gateway(provider),
        store=SupabaseIngestionStore(lambda: admin),
        files=InMemoryMaterialFiles(blobs),
        documents=FakeDocuments(pages),
    )


async def ingest_all(admin: Client, prep: str, deps: IngestionDeps) -> None:
    materials = (
        admin.table("materials")
        .select("id")
        .eq("exam_prep_id", prep)
        .order("created_at")
        .execute()
        .data
    )
    for row in materials:
        await ingest_material(uuid.UUID(row["id"]), deps)
    await build_scope(uuid.UUID(prep), deps)


async def test_SA06_the_job_writes_rows_of_the_preps_tenant_only(admin, make_user, api):
    # AC-tenant
    owner, other = make_user(), make_user()
    blobs: dict[str, bytes] = {}
    pages: dict[bytes, list[str]] = {}
    prep = seed(admin, owner, blobs, pages)

    await ingest_all(admin, prep, deps_for(admin, blobs, pages))

    for table in (
        "material_pages",
        "chunks",
        "past_exam_questions",
        "topics",
        "topic_skills",
        "topic_sources",
        "ingestion_jobs",
    ):
        rows = admin.table(table).select("tenant_id").execute().data
        mine = [r for r in rows if r["tenant_id"] == owner.tenant_id]
        assert mine, f"{table}: nothing written"
    for table in ("topics", "chunks", "past_exam_questions"):
        assert user_client(other).table(table).select("id").execute().data == []
        assert user_client(owner).table(table).select("id").execute().data
    assert api.get(f"/exam-preps/{prep}/ingestion", headers=other.headers).status_code == 404
    body = api.get(f"/exam-preps/{prep}/ingestion", headers=owner.headers).json()
    assert body["scope_ready"] is True
    assert [f["status"] for f in body["files"]] == ["done", "done", "done"]


async def test_SM01_building_the_scope_again_on_the_database_does_not_duplicate(admin, make_user):
    # AC-18
    owner = make_user()
    blobs: dict[str, bytes] = {}
    pages: dict[bytes, list[str]] = {}
    prep = seed(admin, owner, blobs, pages)
    deps = deps_for(admin, blobs, pages, rounds=2)
    await ingest_all(admin, prep, deps)

    await build_scope(uuid.UUID(prep), deps)

    names = sorted(
        r["name"]
        for r in admin.table("topics").select("name").eq("exam_prep_id", prep).execute().data
    )
    assert names == ["ลิมิต", "อนุพันธ์"]
