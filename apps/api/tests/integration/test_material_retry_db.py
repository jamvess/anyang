"""`MaterialRepository.retry` against real Supabase: another tenant's failed file is invisible,
and the owner's update passes RLS and the `0009` trigger
(specs/features/exam-prep/material-retry.md §2.2 items 2, 5 · AC-12 · SA-06).

Users and the admin client come from test_materials_storage_db.py unchanged (already reviewed).
"""

# ruff: noqa: F811  (tests take the imported fixtures `admin` and `make_user` as arguments)

import uuid
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from supabase import Client

from app.db.materials import SupabaseMaterialRepository
from tests.integration.test_materials_storage_db import (  # noqa: F401  admin, make_user: fixtures
    User,
    admin,
    make_user,
)

TRY_AGAIN = "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้"


def _failed_file(admin: Client, user: User, **change: Any) -> dict[str, Any]:
    """A prep and a file that failed, written with the service role like ingestion does."""
    exam = (date.today() + timedelta(days=14)).isoformat()
    prep = (
        admin.table("exam_preps")
        .insert(
            {
                "tenant_id": user.tenant_id,
                "user_id": user.user_id,
                "title": "retry",
                "exam_date": exam,
            }
        )
        .execute()
        .data[0]["id"]
    )
    material = str(uuid.uuid4())
    row = {
        "id": material,
        "tenant_id": user.tenant_id,
        "exam_prep_id": prep,
        "storage_path": f"{user.tenant_id}/{prep}/{material}",
        "file_name": "midterm.pdf",
        "status": "failed",
        "error": TRY_AGAIN,
        **change,
    }
    return admin.table("materials").insert(row).execute().data[0]


def _row(admin: Client, material: str) -> dict[str, Any]:
    return admin.table("materials").select("*").eq("id", material).single().execute().data


@pytest.fixture(scope="module")
def users(make_user: Callable[[], User]) -> tuple[User, User]:
    return make_user(), make_user()


def test_SA06_retry_of_another_tenants_file_is_404_on_supabase(
    admin: Client, users: tuple[User, User]
) -> None:
    a, b = users
    file_a = _failed_file(admin, a)
    as_b = SupabaseMaterialRepository(b.client())

    assert as_b.get(uuid.UUID(file_a["id"])) is None  # the router answers 404
    assert as_b.retry(uuid.UUID(file_a["id"]), status="uploaded") is None
    after = _row(admin, file_a["id"])
    assert (after["status"], after["error"]) == ("failed", TRY_AGAIN)


@pytest.mark.parametrize(
    ("change", "status"),
    [({}, "uploaded"), ({"kind": "past_exam", "kind_confirmed": True}, "confirmed")],
    ids=["classify", "ingest"],
)
def test_CM07_owner_retry_passes_rls_and_the_path_trigger(
    admin: Client, users: tuple[User, User], change: dict[str, Any], status: str
) -> None:
    a, _ = users
    file_a = _failed_file(admin, a, **change)
    as_a = SupabaseMaterialRepository(a.client())

    record = as_a.retry(uuid.UUID(file_a["id"]), status=status)

    assert record is not None
    assert (record.status, record.error) == (status, None)
    after = _row(admin, file_a["id"])
    assert (after["status"], after["error"]) == (status, None)
    assert after["kind"] == file_a["kind"]
    # only while failed: a second call changes nothing (spec §2.2 item 5)
    assert as_a.retry(uuid.UUID(file_a["id"]), status=status) is None
