"""The attack from the self-review of #140, against real Supabase: a user writes a `materials`
row through PostgREST (anon key + their JWT) whose `storage_path` points at another tenant's
object, so ingestion (service role) would read it (specs/features/exam-prep/materials-db.md
§2.2 item 7 · AC-29, AC-30 · SA-06). Needs migration 0009 on the target project.

Users, objects and cleanup come from test_materials_storage_db.py unchanged (already reviewed).
"""

# ruff: noqa: F811  (tests take the imported fixtures `admin` and `make_user` as arguments)

import uuid
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from postgrest.exceptions import APIError
from supabase import Client

from app.services.ingestion import MATERIALS_BUCKET
from tests.integration.test_materials_storage_db import (  # noqa: F401  admin, make_user: fixtures
    PDF_BYTES,
    User,
    admin,
    make_user,
)


def _prep(user: User) -> str:
    exam = (date.today() + timedelta(days=14)).isoformat()
    row = {
        "tenant_id": user.tenant_id,
        "user_id": user.user_id,
        "title": "path guard",
        "exam_date": exam,
    }
    return user.client().table("exam_preps").insert(row).execute().data[0]["id"]


def _own_row(user: User, prep: str) -> dict[str, Any]:
    """A material row written the way the API writes it (repo.create, the user's JWT)."""
    material = str(uuid.uuid4())
    row = {
        "id": material,
        "tenant_id": user.tenant_id,
        "exam_prep_id": prep,
        "storage_path": f"{user.tenant_id}/{prep}/{material}",
        "file_name": "mine.pdf",
    }
    return user.client().table("materials").insert(row).execute().data[0]


def _victim_object(admin: Client, victim: User, prep: str) -> str:
    """A real object in B's prefix, under B's prep; returns its path."""
    path = f"{victim.tenant_id}/{prep}/{uuid.uuid4()}"
    admin.storage.from_(MATERIALS_BUCKET).upload(
        path, PDF_BYTES, {"content-type": "application/pdf"}
    )
    return path


def _rows(admin: Client, **match: str) -> list[dict[str, Any]]:
    query = admin.table("materials").select("*")
    for column, value in match.items():
        query = query.eq(column, value)
    return query.execute().data


@pytest.fixture(scope="module")
def world(admin: Client, make_user: Callable[[], User]) -> dict[str, Any]:
    a, b = make_user(), make_user()
    prep_b = _prep(b)
    return {
        "a": a,
        "b": b,
        "prep_a": _prep(a),
        "other_prep_a": _prep(a),
        "prep_b": prep_b,
        "victim_path": _victim_object(admin, b, prep_b),
    }


@pytest.mark.parametrize(
    "case", ["victim object", "own tenant, other prep", "other id", "other tenant's prep"]
)
def test_SA06_user_cannot_insert_material_pointing_elsewhere(
    admin: Client, world: dict[str, Any], case: str
) -> None:
    a: User = world["a"]
    material = str(uuid.uuid4())
    path = {
        "victim object": world["victim_path"],
        "own tenant, other prep": f"{a.tenant_id}/{world['other_prep_a']}/{material}",
        "other id": f"{a.tenant_id}/{world['prep_a']}/{uuid.uuid4()}",
        # the path has the right shape, but the prep belongs to B (an FK ignores RLS)
        "other tenant's prep": f"{a.tenant_id}/{world['prep_b']}/{material}",
    }[case]
    prep = world["prep_b"] if case == "other tenant's prep" else world["prep_a"]
    row = {
        "id": material,
        "tenant_id": a.tenant_id,
        "exam_prep_id": prep,
        "storage_path": path,
        "file_name": "attack.pdf",
        "status": "confirmed",
        "kind": "sheet",
        "kind_confirmed": True,
    }

    with pytest.raises(APIError) as refused:
        a.client().table("materials").insert(row).execute()

    assert refused.value.code == "42501", refused.value
    assert _rows(admin, id=material) == []


def test_SA06_user_can_insert_the_path_of_the_row(admin: Client, world: dict[str, Any]) -> None:
    a: User = world["a"]
    row = _own_row(a, world["prep_a"])

    assert row["storage_path"] == f"{a.tenant_id}/{world['prep_a']}/{row['id']}"
    assert len(_rows(admin, id=row["id"])) == 1


@pytest.mark.parametrize("column", ["storage_path", "exam_prep_id", "tenant_id"])
def test_SA06_user_cannot_repoint_own_material(
    admin: Client, world: dict[str, Any], column: str
) -> None:
    a, b = world["a"], world["b"]
    row = _own_row(a, world["prep_a"])
    value = {
        "storage_path": world["victim_path"],
        "exam_prep_id": world["other_prep_a"],
        "tenant_id": b.tenant_id,
    }[column]

    with pytest.raises(APIError) as refused:
        a.client().table("materials").update({column: value}).eq("id", row["id"]).execute()

    # tenant_id may also be stopped by RLS (with check) before the trigger: either refuses.
    assert refused.value.code == "42501", refused.value
    [after] = _rows(admin, id=row["id"])
    for name in ("storage_path", "exam_prep_id", "tenant_id"):
        assert after[name] == row[name]


def test_SA06_user_can_still_edit_note(admin: Client, world: dict[str, Any]) -> None:
    a: User = world["a"]
    row = _own_row(a, world["prep_a"])

    a.client().table("materials").update({"user_note": "บทที่ 1-3"}).eq("id", row["id"]).execute()

    assert _rows(admin, id=row["id"])[0]["user_note"] == "บทที่ 1-3"


def test_SA06_service_role_is_not_guarded(admin: Client, world: dict[str, Any]) -> None:
    a: User = world["a"]
    row = _own_row(a, world["prep_a"])

    admin.table("materials").update({"storage_path": "seeded/elsewhere"}).eq(
        "id", row["id"]
    ).execute()

    assert _rows(admin, id=row["id"])[0]["storage_path"] == "seeded/elsewhere"
