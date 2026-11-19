"""The fake mode (AI_PROVIDER=fake) answers every ingestion purpose, so the upload path reaches
the scope with no real model (specs/features/scope/ingestion.md §2.7 item 4 · AC-40 to AC-43 ·
AI-03). Found in #151: in fake mode every file failed with "no scripted response".

Interfaces these tests expect (built by /implement-feature):
- `app.stubs.fake_ingestion() -> dict[str, str | Callable[[ProviderRequest], str]]`: the fixed
  answer of each ingestion purpose; a callable answers from the request (vision_extract_pages
  counts the images it was sent)
- `FakeProvider` accepts such a callable as a script or default item, and has `embed`
- `app.ai.gateway._build_gateway()` with AI_PROVIDER=fake uses them
"""

import asyncio
import dataclasses
from collections.abc import Iterator

import pytest
from pydantic import BaseModel

import app.ai.gateway as gateway_module
import app.settings as settings_module
from app import stubs
from app.ai.gateway import Gateway, Image
from app.ai.providers.base import ProviderRequest
from app.models.scope_ai import (
    ClassifyMaterialResult,
    ExtractTopicsLocalResult,
    MapQuestionsResult,
    MergeTopicsResult,
    SplitPastExamResult,
    VisionExtractPagesResult,
    VisionExtractResult,
)
from app.services.ingestion import IngestionRunner, classify_material
from app.settings import get_settings
from tests.unit.test_ingestion_pipeline import JUNK_PAGE, THAI_PAGE, World

SCHEMAS: dict[str, type[BaseModel]] = {
    "classify_material": ClassifyMaterialResult,
    "vision_extract": VisionExtractResult,
    "vision_extract_pages": VisionExtractPagesResult,
    "split_past_exam": SplitPastExamResult,
    "extract_topics_local": ExtractTopicsLocalResult,
    "merge_topics": MergeTopicsResult,
    "map_questions": MapQuestionsResult,
}
DIMENSIONS = get_settings().ai.embedding.dimensions


@pytest.fixture
def fake_gateway(monkeypatch: pytest.MonkeyPatch) -> Iterator[Gateway]:
    """The gateway the app builds with AI_PROVIDER=fake."""
    settings = get_settings()
    fake = settings.model_copy(
        update={"env": settings.env.model_copy(update={"ai_provider": "fake"})}
    )
    monkeypatch.setattr(settings_module, "get_settings", lambda: fake)

    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", no_sleep)
    yield gateway_module._build_gateway()


def request_with_images(purpose: str, count: int) -> ProviderRequest:
    images = [Image(data=b"png-%d" % i, mime_type="image/png") for i in range(count)]
    return ProviderRequest(
        purpose=purpose, model="fake", prompt="x", temperature=0.0, max_tokens=100, images=images
    )


# --- AC-40 · every ingestion purpose has an answer that passes its schema ------------------------


@pytest.mark.parametrize("purpose", sorted(SCHEMAS))
def test_AI03_fake_answer_of_each_ingestion_purpose_passes_its_schema(purpose: str):
    answers = stubs.fake_ingestion()
    assert purpose in answers
    answer = answers[purpose]
    text = answer(request_with_images(purpose, 2)) if callable(answer) else answer

    SCHEMAS[purpose].model_validate_json(text)


def test_AI03_fake_answers_say_they_are_test_data():
    # Spec §2.7 item 4.2: nobody should take them for a model's output.
    for purpose in ("merge_topics", "extract_topics_local"):
        answer = stubs.fake_ingestion()[purpose]
        assert "โหมด fake" in (answer if isinstance(answer, str) else "")


# --- AC-41 · a fake embed -----------------------------------------------------------------------


async def test_AI03_fake_embed_gives_one_fixed_vector_per_text(fake_gateway: Gateway):
    first = await fake_gateway.embed(["ก", "ข", "ค"], role="document")
    again = await fake_gateway.embed(["ก", "ข", "ค"], role="document")

    assert len(first) == 3
    assert all(len(v) == DIMENSIONS for v in first)
    assert first == again


# --- AC-42 · as many pages as images ------------------------------------------------------------


async def test_AI03_fake_vision_pages_answers_one_page_per_image(fake_gateway: Gateway):
    images = [Image(data=b"png-%d" % i, mime_type="image/png") for i in range(4)]

    result = await fake_gateway.call(
        "vision_extract_pages",
        {"images": images, "file_name": "scan.pdf", "page_count": "4"},
        VisionExtractPagesResult,
    )

    assert [p.page for p in result.pages] == [1, 2, 3, 4]


# --- AC-43 · upload to scope in fake mode -------------------------------------------------------


async def test_SM01_fake_mode_takes_a_prep_from_upload_to_a_ready_scope(fake_gateway: Gateway):
    world = World({})
    world.deps = dataclasses.replace(world.deps, gateway=fake_gateway)
    sheet = world.add(
        "sheet-01.pdf", "other", [THAI_PAGE, THAI_PAGE], status="uploaded", kind_confirmed=False
    )
    exam = world.add(
        "midterm.pdf", "other", [JUNK_PAGE, JUNK_PAGE], status="uploaded", kind_confirmed=False
    )

    await classify_material(sheet, world.deps)
    await classify_material(exam, world.deps)
    assert {r["status"] for r in world.rows("materials", exam_prep_id=world.prep)} == {"classified"}

    # The user confirms: the sheet as a sheet, the exam as a past exam.
    world.store.update_material(
        sheet, {"kind": "sheet", "kind_confirmed": True, "status": "confirmed"}
    )
    world.store.update_material(
        exam, {"kind": "past_exam", "kind_confirmed": True, "status": "confirmed"}
    )
    await asyncio.wait_for(IngestionRunner(world.deps).start(world.prep), timeout=30)

    assert {r["status"] for r in world.rows("materials", exam_prep_id=world.prep)} == {"ready"}
    topics = world.rows("topics", exam_prep_id=world.prep)
    assert len(topics) == 3
    assert all(t["importance"] is not None for t in topics)
