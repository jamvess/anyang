"""The file type comes from materials.content_type, not from the user's file name
(specs/features/scope/ingestion.md §2.5 item 3 · AC-35 to AC-39 · CM-03).

Interfaces these tests expect (built by /implement-feature):
- `InMemoryIngestionStore.add_material(..., content_type: str | None = None)` and
  `MaterialRow.content_type`
- `app.services.ingestion` reads the type from it; a row without one falls back to the file
  name's extension, as before.

"Not read as a PDF" is checked by marking the file's bytes broken: reading its text layer would
fail it with "เปิดไฟล์นี้ไม่ได้"."""

import json
import uuid
from typing import Any

import pytest

from app.services.ingestion import classify_material, ingest_material
from tests.unit.test_ingestion_pipeline import THAI_PAGE, World, classified

PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
NOT_YET = "ไฟล์ชนิดนี้ยังอ่านไม่ได้ ส่งเป็น PDF หรือรูปแทนได้"
VISION = json.dumps({"text": "x^2", "latex_blocks": [], "notes": ""})


def upload(world: World, name: str, content_type: str | None, **kw: Any) -> uuid.UUID:
    """A file at classify (uploaded, not confirmed) unless kw says otherwise."""
    kw.setdefault("status", "uploaded")
    kw.setdefault("kind_confirmed", False)
    return world.add(name, kw.pop("kind", "other"), [THAI_PAGE], content_type=content_type, **kw)


def confirmed(world: World, name: str, content_type: str | None) -> uuid.UUID:
    return world.add(name, "notes", [THAI_PAGE], content_type=content_type)


def no_text_layer(world: World, material_id: uuid.UUID) -> None:
    """Reading this file's text layer would fail it, so passing proves it was not read."""
    path = world.rows("materials", id=material_id)[0]["storage_path"]
    world.broken.add(world.blobs[path])


def row(world: World, material_id: uuid.UUID) -> dict[str, Any]:
    return world.rows("materials", id=material_id)[0]


# --- AC-35 · a photo is a photo by its content type -------------------------------------------

IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic"]


@pytest.mark.parametrize("content_type", IMAGE_TYPES)
async def test_CM03_photo_is_classified_without_a_text_layer(content_type: str):
    world = World({"classify_material": [classified("notes")]})
    photo = upload(world, "scan", content_type)
    no_text_layer(world, photo)

    await classify_material(photo, world.deps)

    assert row(world, photo)["status"] == "classified"
    [request] = world.requests("classify_material")
    assert request.prompt.count("[p.") == 0


@pytest.mark.parametrize("content_type", IMAGE_TYPES)
async def test_CM03_photo_is_read_by_vision_with_its_own_type(content_type: str):
    world = World({"vision_extract": [VISION]})
    photo = confirmed(world, "scan", content_type)
    no_text_layer(world, photo)

    await ingest_material(photo, world.deps)

    [request] = world.requests("vision_extract")
    assert request.images[0].mime_type == content_type
    pages = world.rows("material_pages", material_id=photo)
    assert [(p["page_no"], p["extract_method"]) for p in pages] == [(1, "vision")]
    assert row(world, photo)["status"] == "ready"


# --- AC-36 · the name does not decide ------------------------------------------------------------


async def test_CM03_pdf_named_like_a_photo_is_read_as_a_pdf():
    world = World({"classify_material": [classified("sheet")]})
    sheet = upload(world, "photo.png", "application/pdf")

    await classify_material(sheet, world.deps)

    [request] = world.requests("classify_material")
    assert request.prompt.count("[p.") >= 1

    reading = World({})
    pdf = confirmed(reading, "photo.png", "application/pdf")
    await ingest_material(pdf, reading.deps)
    assert reading.requests("vision_extract") == []
    pages = reading.rows("material_pages", material_id=pdf)
    assert {p["extract_method"] for p in pages} == {"text_layer"}


# --- AC-37 · slides and documents cannot be read yet ------------------------------------------


@pytest.mark.parametrize("content_type", [PPTX, DOCX], ids=["pptx", "docx"])
async def test_CM03_slides_and_documents_fail_at_classify_with_what_to_send(content_type: str):
    world = World({"classify_material": [classified("slides")]})
    deck = upload(world, "lecture", content_type)
    no_text_layer(world, deck)

    await classify_material(deck, world.deps)

    assert (row(world, deck)["status"], row(world, deck)["error"]) == ("failed", NOT_YET)
    assert world.requests("classify_material") == []


# --- AC-38 · rows from before #140 keep the extension rule -------------------------------------


async def test_CM03_row_without_a_content_type_uses_the_extension_as_before():
    world = World({"vision_extract": [VISION]})
    photo = confirmed(world, "sheet.JPG", None)
    sheet = confirmed(world, "sheet", None)

    await ingest_material(photo, world.deps)
    await ingest_material(sheet, world.deps)

    [request] = world.requests("vision_extract")
    assert request.images[0].mime_type == "image/jpeg"
    pages = world.rows("material_pages", material_id=sheet)
    assert {p["extract_method"] for p in pages} == {"text_layer"}


# --- AC-39 · case and parameters do not matter -------------------------------------------------


async def test_CM03_content_type_with_capitals_and_a_parameter_is_still_a_photo():
    world = World({"vision_extract": [VISION]})
    photo = confirmed(world, "scan", "Image/PNG; x=1")
    no_text_layer(world, photo)

    await ingest_material(photo, world.deps)

    [request] = world.requests("vision_extract")
    assert request.images[0].mime_type == "image/png"
