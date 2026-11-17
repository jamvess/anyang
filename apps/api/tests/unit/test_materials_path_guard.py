"""`materials.storage_path` cannot point outside its own prep (specs/features/exam-prep/
materials-db.md §2.2 items 7-9 · AC-31, AC-32 · SA-06, CM-07).

Found in the self-review of #140 (2026-11-17): the `tenant_rows` policy checks only `tenant_id`,
so a user could write any `storage_path` through PostgREST, and ingestion reads it with the
service role, past the storage policies. Migration 0009 guards the column; ingestion checks the
path again before it reads (defense in depth, in Jam's file). The attack itself runs against
real Supabase in tests/integration/test_materials_path_guard_db.py (AC-29, AC-30).

The ingestion world comes from test_ingestion_pipeline.py unchanged (already reviewed).
"""

import json
import re
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import scripts.seed_scope_demo as seed
from app.services.ingestion import UNREADABLE, classify_material, ingest_material
from tests.unit.test_ingestion_pipeline import TENANT, THAI_PAGE, World, classified

MIGRATION = (
    Path(__file__).resolve().parents[4] / "supabase/migrations/0009_materials_path_guard.sql"
)


def _sql() -> str:
    """The migration without comments, whitespace collapsed, lower case."""
    text = re.sub(r"--[^\n]*", "", MIGRATION.read_text(encoding="utf-8"))
    return re.sub(r"\s+", " ", text).lower()


# --- AC-31 · ingestion refuses a path outside its prep -----------------------------------------

BAD_PATHS: dict[str, Callable[[uuid.UUID, str], str]] = {
    "other tenant": lambda prep, name: f"{uuid.uuid4()}/{prep}/{name}",
    "other prep": lambda prep, name: f"{TENANT}/{uuid.uuid4()}/{name}",
    "no prefix": lambda prep, name: name,
    "slash after prefix": lambda prep, name: f"{TENANT}/{prep}/../{uuid.uuid4()}/{name}",
    "empty after prefix": lambda prep, name: f"{TENANT}/{prep}/",
}


def _repoint(world: World, material: uuid.UUID, path: str) -> None:
    """Move the row to `path` and put real bytes there, so only the guard can stop the read."""
    old = world.rows("materials", id=material)[0]["storage_path"]
    world.store.update_material(material, {"storage_path": path})
    world.blobs[path] = world.blobs[old]


@pytest.mark.parametrize("stage", ["classify", "ingest"])
@pytest.mark.parametrize("case", list(BAD_PATHS))
async def test_SA06_ingestion_refuses_path_outside_its_prep(stage: str, case: str) -> None:
    world = World({"classify_material": [classified("sheet")]})
    material = world.add("sheet-01.pdf", "sheet", [THAI_PAGE])
    _repoint(world, material, BAD_PATHS[case](world.prep, "sheet-01"))

    run: Any = classify_material if stage == "classify" else ingest_material
    await run(material, world.deps)

    row = world.rows("materials", id=material)[0]
    assert (row["status"], row["error"]) == ("failed", UNREADABLE)
    assert world.provider.requests == []  # the bytes were never read, so no AI call either


async def test_SA06_ingestion_reads_a_good_path() -> None:
    world = World({"classify_material": [classified("sheet")]})
    material = world.add("sheet-01.pdf", "sheet", [THAI_PAGE])
    _repoint(world, material, f"{TENANT}/{world.prep}/{material}")

    await classify_material(material, world.deps)

    assert world.rows("materials", id=material)[0]["status"] == "classified"
    assert len(world.requests("classify_material")) == 1


# --- AC-32 · migration 0009 and the seed script ------------------------------------------------


def test_SA06_0009_guards_insert_and_update() -> None:
    sql = _sql()
    trigger = re.search(r"create trigger (\w+) before insert or update on public\.materials", sql)
    assert trigger, "one trigger, before insert or update, on public.materials"
    assert "for each row" in sql
    assert "current_user = 'authenticated'" in sql, "only the authenticated role is checked"
    assert "set search_path = ''" in sql
    # insert: the exact path of the row
    assert "new.tenant_id::text || '/' || new.exam_prep_id::text || '/' || new.id::text" in sql
    # update: the three columns cannot change
    for column in ("storage_path", "tenant_id", "exam_prep_id"):
        assert f"new.{column} is distinct from old.{column}" in sql
    # insert: the prep must be visible to the caller in the same tenant (RLS of exam_preps)
    assert re.search(
        r"exists \( ?select 1 from public\.exam_preps \w* ?where \w*\.?id = new\.exam_prep_id "
        r"and \w*\.?tenant_id = new\.tenant_id ?\)",
        sql,
    ), "an EXISTS over public.exam_preps for new.exam_prep_id and new.tenant_id"
    assert "security definer" not in sql, "the caller's rights, so RLS hides other tenants' preps"
    assert "errcode = '42501'" in sql


def test_CM07_0009_backfills_announced_rows_only() -> None:
    sql = _sql()
    assert (
        "update public.materials set uploaded_at = created_at "
        "where uploaded_at is null and status <> 'uploaded'"
    ) in sql


def test_CM07_seed_rows_are_announced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pages, questions, results = tmp_path / "pages", tmp_path / "questions", tmp_path / "results"
    for folder in (pages, questions, results):
        folder.mkdir()
    for key in ("sheet-01", "sheet-02"):
        doc = {"file": f"{key}.pdf", "method": "text", "pages": [{"page": 1, "text": "x"}]}
        (pages / f"{key}.json").write_text(json.dumps(doc), encoding="utf-8")
    (results / "topics.json").write_text("[]", encoding="utf-8")
    (results / "mapping.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(seed, "PAGES", pages)
    monkeypatch.setattr(seed, "QUESTIONS", questions)
    monkeypatch.setattr(seed, "RESULTS", results)
    tenant, prep = str(uuid.uuid4()), str(uuid.uuid4())

    materials = seed.build_rows(tenant, prep)["materials"]

    assert len(materials) == 2
    for row in materials:
        assert row.get("uploaded_at"), "GET /materials hides rows without uploaded_at"
        assert row["storage_path"] == f"{tenant}/{prep}/{row['id']}"
