"""Classify never leaves a file stuck at "uploaded" (specs/features/scope/ingestion.md §2.2
item 5 · AC-29 to AC-34). Seen in #151: the row could not be read, the job died before it could
mark the file failed, and the page showed "AI กำลังดูไฟล์…" for good.

The in-memory store is wrapped by FlakyStore, which makes the chosen calls fail once; the app's
store is unchanged. Fake AI provider only (AI-03)."""

import dataclasses
import logging
import uuid
from collections.abc import Callable
from typing import Any

import pytest

from app.db.errors import DbUnavailableError
from app.services.ingestion import IngestionRunner, classify_material
from tests.unit.test_ingestion_pipeline import THAI_PAGE, World, classified

TRY_AGAIN = "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้"
LOGGER = "app.services.ingestion"


class FlakyStore:
    """Delegates to the in-memory store; `fail(method, when)` makes the next matching call raise
    DbUnavailableError, as a dropped connection to Supabase would."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._rules: list[list[Any]] = []

    def fail(self, method: str, when: Callable[..., bool] = lambda *a, **k: True) -> None:
        self._rules.append([method, when, 1])

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr

        def call(*args: Any, **kwargs: Any) -> Any:
            for rule in self._rules:
                method, when, left = rule
                if method == name and left > 0 and when(*args, **kwargs):
                    rule[2] = 0
                    raise DbUnavailableError(f"flaky {name}")
            return attr(*args, **kwargs)

        return call


def uploaded_file(script: list[Any]) -> tuple[World, FlakyStore, uuid.UUID]:
    world = World({"classify_material": script})
    sheet = world.add("sheet-01.pdf", "other", [THAI_PAGE], status="uploaded", kind_confirmed=False)
    flaky = FlakyStore(world.store)
    world.deps = dataclasses.replace(world.deps, store=flaky)
    return world, flaky, sheet


def material(world: World, material_id: uuid.UUID) -> dict[str, Any]:
    return world.rows("materials", id=material_id)[0]


def classify_jobs(world: World, material_id: uuid.UUID) -> list[dict[str, Any]]:
    return world.rows("ingestion_jobs", material_id=material_id, stage="classify")


# --- AC-29 · the row cannot be read ------------------------------------------------------------


async def test_CM07_row_that_cannot_be_read_still_ends_failed():
    world, flaky, sheet = uploaded_file([classified("sheet")])
    flaky.fail("get_material")

    await classify_material(sheet, world.deps)  # does not raise

    row = material(world, sheet)
    assert (row["status"], row["error"]) == ("failed", TRY_AGAIN)
    assert classify_jobs(world, sheet) == []  # no tenant known, so no job row
    assert world.requests("classify_material") == []


# --- AC-30 · the job cannot be started ---------------------------------------------------------


async def test_CM07_job_that_cannot_start_ends_failed():
    world, flaky, sheet = uploaded_file([classified("sheet")])
    flaky.fail("set_job", when=lambda *a, **k: k.get("status") == "running")

    await classify_material(sheet, world.deps)

    row = material(world, sheet)
    assert (row["status"], row["error"]) == ("failed", TRY_AGAIN)
    assert [j["status"] for j in classify_jobs(world, sheet)] == ["failed"]
    assert world.requests("classify_material") == []


# --- AC-31 · the result cannot be written ------------------------------------------------------


async def test_CM07_result_that_cannot_be_written_ends_failed():
    world, flaky, sheet = uploaded_file([classified("sheet")])
    flaky.fail("update_material", when=lambda *a, **k: a[1].get("status") == "classified")

    await classify_material(sheet, world.deps)

    row = material(world, sheet)
    assert (row["status"], row["error"]) == ("failed", TRY_AGAIN)
    assert [j["status"] for j in classify_jobs(world, sheet)] == ["failed"]


# --- AC-32 · the result is in, only the job's "done" is not -------------------------------------


async def test_CM07_classified_file_stays_classified_when_the_job_cannot_be_closed(
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(logging.WARNING, logger=LOGGER)
    world, flaky, sheet = uploaded_file([classified("sheet")])
    flaky.fail("set_job", when=lambda *a, **k: k.get("status") == "done")

    await classify_material(sheet, world.deps)

    row = material(world, sheet)
    assert (row["status"], row["error"], row["kind"]) == ("classified", None, "sheet")
    assert any(
        r.levelno == logging.WARNING and str(sheet) in r.getMessage() for r in caplog.records
    )


# --- AC-33 · nothing can be written ------------------------------------------------------------


async def test_CM07_database_down_is_logged_as_a_stuck_file(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger=LOGGER)
    world, _flaky, sheet = uploaded_file([classified("sheet")])
    world.store.down = True

    await classify_material(sheet, world.deps)  # does not raise

    errors = [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]
    assert any(str(sheet) in m and "stays at uploaded" in m for m in errors)


# --- AC-34 · a failed file can be tried again -----------------------------------------------------


async def test_CM07_file_failed_on_a_lost_row_can_be_retried():
    world, flaky, sheet = uploaded_file([classified("sheet")])
    flaky.fail("get_material")
    await classify_material(sheet, world.deps)
    assert material(world, sheet)["status"] == "failed"

    await IngestionRunner(world.deps).retry(sheet)

    row = material(world, sheet)
    assert (row["status"], row["error"], row["kind"]) == ("classified", None, "sheet")


# --- added by the self-review of PR #154 -------------------------------------------------------


async def test_CM07_file_ends_failed_even_when_the_job_table_cannot_be_written():
    # The job cannot be started, and its "failed" cannot be written either: the file must still
    # end at failed, which is what the page and /retry read.
    world, flaky, sheet = uploaded_file([classified("sheet")])
    flaky.fail("set_job", when=lambda *a, **k: k.get("status") == "running")
    flaky.fail("set_job", when=lambda *a, **k: k.get("status") == "failed")

    await classify_material(sheet, world.deps)

    row = material(world, sheet)
    assert (row["status"], row["error"]) == ("failed", TRY_AGAIN)
