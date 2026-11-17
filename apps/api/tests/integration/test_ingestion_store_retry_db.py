"""The repeat of an insert, against real PostgREST: rows written by the first try are not written
again, and nothing fails (specs/features/scope/ingestion.md §2.1 item 4 · AC-29 · CM-07).

The unit tests (tests/unit/test_ingestion_store_retry.py) check that the repeat is an
`upsert(on_conflict="id", ignore_duplicates=True)` with the same ids. This checks that PostgREST
and Postgres really skip ids already there: the real client is wrapped so its first `execute()`
drops the connection, either after the insert reached the database (the answer was lost) or
before it was sent. Users, preps and cleanup come from test_materials_storage_db.py (reviewed).
"""

# ruff: noqa: F811  (tests take the imported fixtures `admin` and `make_user` as arguments)

import uuid
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import httpx
import pytest
from supabase import Client

from app.db.ingestion import SupabaseIngestionStore
from tests.integration.test_materials_storage_db import (  # noqa: F401  admin, make_user: fixtures
    User,
    admin,
    make_user,
)


class DropOnce:
    """Wraps a query chain of the real client; the first `execute()` of the whole client drops
    the connection, after or before running for real."""

    def __init__(self, inner: Any, state: dict[str, Any]) -> None:
        self._inner, self._state = inner, state

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr

        def call(*args: Any, **kwargs: Any) -> Any:
            result = attr(*args, **kwargs)
            return DropOnce(result, self._state) if hasattr(result, "execute") else result

        return call

    def execute(self) -> Any:
        self._state["calls"].append(self._inner)
        if self._state["drops"] == 0:
            return self._inner.execute()
        self._state["drops"] -= 1
        if self._state["when"] == "after commit":
            self._inner.execute()  # the insert reaches the database, its answer does not
        raise httpx.RemoteProtocolError("Server disconnected")


def flaky_connect(admin: Client, when: str) -> tuple[Callable[[], Any], dict[str, Any]]:
    state: dict[str, Any] = {"drops": 1, "when": when, "calls": []}

    class Flaky:
        postgrest = admin.postgrest

        def table(self, name: str) -> DropOnce:
            return DropOnce(admin.table(name), state)

    return Flaky, state


def material(admin: Client, user: User) -> str:
    exam = (date.today() + timedelta(days=14)).isoformat()
    prep = (
        admin.table("exam_preps")
        .insert(
            {
                "tenant_id": user.tenant_id,
                "user_id": user.user_id,
                "title": "store retry",
                "exam_date": exam,
            }
        )
        .execute()
        .data[0]["id"]
    )
    material_id = str(uuid.uuid4())
    admin.table("materials").insert(
        {
            "id": material_id,
            "tenant_id": user.tenant_id,
            "exam_prep_id": prep,
            "storage_path": f"{user.tenant_id}/{prep}/{material_id}",
            "file_name": "sheet.pdf",
            "status": "ingesting",
        }
    ).execute()
    return material_id


@pytest.mark.parametrize("when", ["after commit", "before send"])
def test_CM07_insert_repeated_on_postgrest_writes_each_row_once(
    admin: Client, make_user: Callable[[], User], when: str
) -> None:
    user = make_user()
    material_id = material(admin, user)
    connect, state = flaky_connect(admin, when)
    store = SupabaseIngestionStore(connect, attempts=3, backoff_s=0)
    rows = [
        {
            "tenant_id": user.tenant_id,
            "material_id": material_id,
            "page_no": n,
            "text": f"หน้า {n}",
            "extract_method": "text_layer",
        }
        for n in (1, 2)
    ]

    store.insert("material_pages", rows)  # no error: the repeat skips what is already there

    assert len(state["calls"]) == 2, "one dropped try, then the repeat"
    written = (
        admin.table("material_pages")
        .select("id,page_no")
        .eq("material_id", material_id)
        .order("page_no")
        .execute()
        .data
    )
    assert [r["page_no"] for r in written] == [1, 2], "each row exactly once"
    assert len({r["id"] for r in written}) == 2
