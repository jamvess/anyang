"""What the runner writes when S11's "ลองใหม่" is pressed, before the request returns, and the run
that follows (specs/features/exam-prep/ingestion-retry.md §2.2 item 4, §2.3 items 4 and 5 · AC-11,
AC-12, AC-17, AC-18 runner side · AC-22). Fake provider, in-memory store, fake documents: the
`World` of test_ingestion_pipeline.py.

Interfaces these tests expect (to be built by /implement-feature):
- `IngestionRunner.retry_file(material_id)` (async) · `IngestionRunner.retry_steps(prep_id)`
  (async) · see test_ingestion_retry_api.py. Both write before they return and do not wait for
  the AI work, which runs in the background (`classify` or `start`).
"""

import asyncio
import uuid
from collections.abc import Callable, Iterator

import pytest

import app.ai.gateway as gateway_module
from app.ai.providers.base import ProviderRateLimited
from app.services.ingestion import IngestionRunner, ingestion_view
from app.settings import get_settings
from tests.unit.test_ingestion_pipeline import (
    THAI_PAGE,
    TWO_TOPICS,
    World,
    classified,
    demo_world,
    local,
)

TRY_AGAIN = "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้"
# Every try of one call answers 429: the first, then one per wait of the gateway's table.
RATE_LIMITED_CALL = [ProviderRateLimited("429 RESOURCE_EXHAUSTED")] * (
    len(get_settings().ai.gateway.rate_limit_waits_seconds) + 1
)


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)
    yield


async def until(check: Callable[[], bool], timeout: float = 5.0) -> None:
    """Lets the background tasks run until `check()` holds."""
    async with asyncio.timeout(timeout):
        while not check():
            await asyncio.sleep(0.005)


def material(world: World, material_id: uuid.UUID) -> dict:
    return world.rows("materials", id=material_id)[0]


def steps(world: World) -> dict[str, str]:
    return {
        j["stage"]: j["status"]
        for j in world.rows("ingestion_jobs", exam_prep_id=world.prep, material_id=None)
    }


async def test_CM07_retry_file_failed_while_reading_resets_it_before_reading_again():
    """AC-11 (runner side): `confirmed`, no error, the failed job `queued` when `retry_file`
    returns; then the file is read and the scope built in the background."""
    world = World(
        {
            "extract_topics_local": [local(("ลิมิต", "1-1"))],
            "merge_topics": [TWO_TOPICS],
        }
    )
    sheet = world.add("sheet-01.pdf", "sheet", [THAI_PAGE], status="failed")
    world.store.set_error(sheet, TRY_AGAIN)
    world.store.add_job(world.prep, "extract", "failed", material_id=sheet, error="boom")
    runner = IngestionRunner(world.deps)

    await runner.retry_file(sheet)

    row = material(world, sheet)
    assert (row["status"], row["error"]) == ("confirmed", None)
    [job] = world.rows("ingestion_jobs", material_id=sheet, stage="extract")
    assert job["status"] == "queued"
    task = runner.start(world.prep)  # the task retry_file started
    assert not task.done()
    await asyncio.wait_for(task, timeout=20)
    assert material(world, sheet)["status"] == "ready"


async def test_CM07_retry_file_failed_while_classifying_resets_it_then_classifies():
    """AC-12 (runner side): `uploaded`, no error when `retry_file` returns, A1 not called yet;
    then A1 runs in the background."""
    world = World({"classify_material": [classified("sheet")]})
    sheet = world.add("sheet-01.pdf", "sheet", [THAI_PAGE], status="failed", kind_confirmed=False)
    world.store.set_error(sheet, TRY_AGAIN)
    world.store.add_job(world.prep, "classify", "failed", material_id=sheet, error="boom")
    runner = IngestionRunner(world.deps)

    await runner.retry_file(sheet)

    row = material(world, sheet)
    assert (row["status"], row["error"]) == ("uploaded", None)
    assert world.requests("classify_material") == []
    await until(lambda: material(world, sheet)["status"] == "classified")


@pytest.mark.parametrize(
    ("topics", "stars"), [("failed", "queued"), ("done", "failed")], ids=["topics", "stars"]
)
async def test_CM07_retry_steps_sets_topics_and_stars_back_to_queued(topics: str, stars: str):
    """AC-17, AC-18 (runner side): both steps `queued` when `retry_steps` returns, even when only
    `stars` failed (§2.3 item 4), and a run of the prep started."""
    world = demo_world()
    await world.run()  # every file ready, the scope built once
    world.store.add_job(world.prep, "topics", topics)
    world.store.add_job(world.prep, "stars", stars)
    world.provider._script.setdefault("extract_topics_local", []).extend(
        [local(("ลิมิต", "1-2")), local(("อนุพันธ์", "1-1"))]
    )
    world.provider._script.setdefault("merge_topics", []).append(TWO_TOPICS)
    runner = IngestionRunner(world.deps)

    await runner.retry_steps(world.prep)

    assert steps(world) == {"topics": "queued", "stars": "queued"}
    task = runner.start(world.prep)
    assert not task.done()


async def test_CM07_topics_failed_on_429_then_retried_reaches_a_ready_scope():
    """AC-22: the path of 19 Nov. A6 answers 429 on every try, `topics` fails; "ลองใหม่" on the
    step, A6 answers, and the scope is built."""
    world = World(
        {
            "extract_topics_local": [local(("ลิมิต", "1-1")), local(("ลิมิต", "1-1"))],
            "merge_topics": [*RATE_LIMITED_CALL, TWO_TOPICS],
        }
    )
    world.add("sheet-01.pdf", "sheet", [THAI_PAGE])
    await world.run()
    assert steps(world)["topics"] == "failed"
    assert world.rows("topics") == []
    runner = IngestionRunner(world.deps)

    await runner.retry_steps(world.prep)
    await asyncio.wait_for(runner.start(world.prep), timeout=20)

    assert steps(world) == {"topics": "done", "stars": "done"}
    assert len(world.rows("topics", exam_prep_id=world.prep)) == 2
    snapshot = world.store.reader_for(world.store.prep_tenant(world.prep)).snapshot(world.prep)
    assert ingestion_view(snapshot).scope_ready is True
