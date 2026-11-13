"""Ingestion: the files of an exam prep → pages, chunks, past exam questions → topics + stars
(specs/features/scope/ingestion.md · ai-orchestration §2.3.2 to 2.3.5 · PoC P3).

Entry points for the material endpoints (Junior, demo step 3 · spec §2.1):
`classify_material`, `start_ingestion` (through `IngestionRunner`), `retry_material`. The job
writes with the service role and puts `tenant_id` on every row itself.

Code decides, the AI speaks (CLAUDE.md rule 1): the models read pages, split exams, name topics
and map questions in checked schemas; code reads the files, chunks, maps keys back to files,
drops bad sources, picks the weight of an exam and computes the stars (`domain/stars.py`). The AI
never writes to the database (rule 2).
"""

import asyncio
import json
import logging
import uuid
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID

from app.ai.gateway import AIProviderError, AISchemaError, Gateway, Image, get_gateway
from app.db.ingestion import (
    IngestionSnapshot,
    IngestionStore,
    MaterialRow,
    SupabaseIngestionStore,
)
from app.domain.ingestion import (
    ChunkDraft,
    chunk_pages,
    clean_file_name,
    file_detail,
    file_keys,
    file_status,
    pages_text,
    read_method,
    resolve_sources,
    thai_share,
)
from app.domain.stars import ExamIn, TopicIn, compute_importance
from app.models.scope import Ingestion, IngestionFile, IngestionStep
from app.models.scope_ai import (
    ClassifyMaterialResult,
    ExtractTopicsLocalResult,
    MapQuestionsResult,
    MergeTopicsResult,
    SplitPastExamResult,
    VisionExtractPagesResult,
    VisionExtractResult,
)
from app.services.documents import Documents, PyMuPdfDocuments
from app.services.material_files import MaterialFiles, SupabaseMaterialFiles
from app.settings import get_settings

log = logging.getLogger(__name__)

# Short texts the user may see in S10 / S11 (spec §2.2 item 4, §2.6 item 4); details go to the log.
UNREADABLE = "เปิดไฟล์นี้ไม่ได้"
TRY_AGAIN = "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้"
NO_SHEET = "ยังไม่มีชีทหรือสไลด์ให้หาหัวข้อ"
SCOPE_FAILED = "หาหัวข้อไม่สำเร็จ ลองใหม่ได้"
NO_NOTE = "ไม่มี"  # the prompts' word for "none"
# Bucket of uploaded files (ai-orchestration §2.3.2 step 1 · Junior names it in demo step 3).
MATERIALS_BUCKET = "materials"
_IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_JOB_ERROR_CHARS = 500  # an internal note in ingestion_jobs.error, not shown to the user


@dataclass(frozen=True)
class IngestionDeps:
    gateway: Gateway
    store: IngestionStore
    files: MaterialFiles
    documents: Documents


class _FileFailed(Exception):
    """A file cannot go on; ``message`` is what the user sees."""

    def __init__(self, message: str, detail: str) -> None:
        super().__init__(detail)
        self.message = message


async def _db[R](fn: Callable[..., R], *args: Any, **kwargs: Any) -> R:
    """The Supabase client blocks: run store calls in a worker thread."""
    return await asyncio.to_thread(fn, *args, **kwargs)


def _name(material: MaterialRow) -> str:
    return clean_file_name(material.file_name, get_settings().ai.guards.max_attachment_name_chars)


async def _read(deps: IngestionDeps, material: MaterialRow) -> bytes:
    try:
        return await deps.files.read(material.storage_path)
    except Exception as error:  # Storage down or the object is missing
        raise _FileFailed(TRY_AGAIN, f"read {material.storage_path}: {error}") from error


def _text_layer(deps: IngestionDeps, data: bytes) -> list[str]:
    try:
        return deps.documents.pages_text(data)
    except ValueError as error:
        raise _FileFailed(UNREADABLE, f"not a PDF: {error}") from error


# --- §2.2 · classify (CM-06) ----------------------------------------------------------------------


async def classify_material(material_id: UUID, deps: IngestionDeps) -> None:
    """A1: kind, confidence and the weight of a past exam; the user confirms them in S10."""
    material = await _db(deps.store.get_material, material_id)
    if material is None:
        log.warning("classify: material %s not found", material_id)
        return
    settings = get_settings()
    job = {
        "tenant_id": material.tenant_id,
        "exam_prep_id": material.exam_prep_id,
        "material_id": material.id,
    }
    await _db(deps.store.set_job, stage="classify", status="running", **job)
    try:
        data = await _read(deps, material)
        first = _first_pages(deps, material, data)
        result = await deps.gateway.call(
            "classify_material",
            {
                "file_name": _name(material),
                "pages_text": pages_text(first),
                "user_note": material.user_note or NO_NOTE,
            },
            ClassifyMaterialResult,
        )
    except _FileFailed as failure:
        await _fail_file(deps, material, "classify", failure.message, str(failure))
        return
    except (AIProviderError, AISchemaError) as error:
        await _fail_file(deps, material, "classify", TRY_AGAIN, f"classify_material: {error}")
        return
    except Exception as error:  # the database or a bug: never leave the file "running"
        log.exception("ingestion: classify of %s failed", material.id)
        await _fail_file(deps, material, "classify", TRY_AGAIN, f"classify: {error!r}")
        return
    stars = settings.learning.stars
    other = result.kind == "past_exam" and result.other_instructor
    weight = stars.weight_other_instructor if other else stars.weight_same_instructor
    await _db(
        deps.store.update_material,
        material.id,
        {
            "kind": result.kind,
            "kind_confidence": result.confidence,
            "relevance_weight": weight,
            "status": "classified",
            "error": None,
        },
    )
    await _db(deps.store.set_job, stage="classify", status="done", **job)


def _first_pages(deps: IngestionDeps, material: MaterialRow, data: bytes) -> list[tuple[int, str]]:
    """The text layer of the first pages only: no vision call while classifying (spec §2.2)."""
    if _image_type(material) is not None:
        return []
    pages = _text_layer(deps, data)[: get_settings().ai.ingestion.classify_pages]
    return [(n, text.strip()) for n, text in enumerate(pages, start=1)]


# --- §2.3 · one file (SM-01, AI-08)


async def ingest_material(material_id: UUID, deps: IngestionDeps) -> None:
    """Read → (past exam: split into questions | otherwise: chunk + embed). A failure stops this
    file only (spec §2.3 item 5)."""
    material = await _db(deps.store.get_material, material_id)
    if material is None:
        log.warning("ingest: material %s not found", material_id)
        return
    job = {
        "tenant_id": material.tenant_id,
        "exam_prep_id": material.exam_prep_id,
        "material_id": material.id,
    }
    await _db(deps.store.update_material, material.id, {"status": "ingesting", "error": None})
    await _db(deps.store.clear_file, material.id)  # a re-run starts clean (spec §2.3 item 6)
    stage = "extract"
    try:
        await _db(deps.store.set_job, stage=stage, status="running", **job)
        pages, method = await _extract(deps, material)
        await _db(
            deps.store.insert,
            "material_pages",
            [
                {
                    "tenant_id": material.tenant_id,
                    "material_id": material.id,
                    "page_no": n,
                    "text": text,
                    "extract_method": method,
                }
                for n, text in pages
            ],
        )
        await _db(deps.store.set_job, stage=stage, status="done", **job)
        if material.kind == "past_exam":
            stage = "split_exam"
            await _db(deps.store.set_job, stage=stage, status="running", **job)
            await _split_exam(deps, material, pages)
            await _db(deps.store.set_job, stage=stage, status="done", **job)
        else:
            stage = "chunk"
            await _db(deps.store.set_job, stage=stage, status="running", **job)
            drafts = chunk_pages(pages, get_settings().ai.ingestion)
            await _db(deps.store.set_job, stage=stage, status="done", **job)
            stage = "embed"
            await _db(deps.store.set_job, stage=stage, status="running", **job)
            await _embed(deps, material, drafts)
            await _db(deps.store.set_job, stage=stage, status="done", **job)
    except _FileFailed as failure:
        await _fail_file(deps, material, stage, failure.message, str(failure))
        return
    except (AIProviderError, AISchemaError) as error:
        await _fail_file(deps, material, stage, TRY_AGAIN, f"{stage}: {error}")
        return
    except Exception as error:  # the database or a bug: never leave the file "ingesting"
        log.exception("ingestion: %s of %s failed", stage, material.id)
        await _fail_file(deps, material, stage, TRY_AGAIN, f"{stage}: {error!r}")
        return
    await _db(deps.store.update_material, material.id, {"status": "ready", "error": None})


def _image_type(material: MaterialRow) -> str | None:
    """A photo by the extension of the user's file name: `storage_path` is
    `{tenant}/{prep}/{material}` with no extension (0001_init.sql · self-review PR #130)."""
    name = material.file_name.strip().lower()
    return _IMAGE_TYPES.get("." + name.rsplit(".", 1)[-1]) if "." in name else None


async def _extract(deps: IngestionDeps, material: MaterialRow) -> tuple[list[tuple[int, str]], str]:
    data = await _read(deps, material)
    image_type = _image_type(material)
    if image_type is not None:  # a single photo of a page: A2
        result = await deps.gateway.call(
            "vision_extract",
            {
                "image": Image(data=data, mime_type=image_type),
                "file_name": _name(material),
                "page_no": "1",
            },
            VisionExtractResult,
        )
        return [(1, result.text)], "vision"
    layer = _text_layer(deps, data)
    cfg = get_settings().ai.ingestion
    if read_method(thai_share("".join(layer)), cfg) == "text_layer":
        return [(n, text.strip()) for n, text in enumerate(layer, start=1)], "text_layer"
    images = deps.documents.page_images(data, cfg.render_dpi)
    result = await deps.gateway.call(
        "vision_extract_pages",
        {
            "images": [Image(data=png, mime_type="image/png") for png in images],
            "file_name": _name(material),
            "page_count": str(len(images)),
        },
        VisionExtractPagesResult,
    )
    if len(result.pages) != len(images):
        raise _FileFailed(
            TRY_AGAIN, f"vision: {len(images)} pages sent, {len(result.pages)} returned"
        )
    return [(p.page, p.text) for p in result.pages], "vision"


async def _split_exam(
    deps: IngestionDeps, material: MaterialRow, pages: list[tuple[int, str]]
) -> None:
    result = await deps.gateway.call(
        "split_past_exam",
        {"file_name": _name(material), "pages_text": pages_text(pages)},
        SplitPastExamResult,
    )
    await _db(
        deps.store.insert,
        "past_exam_questions",
        [
            {
                "tenant_id": material.tenant_id,
                "material_id": material.id,
                "q_no": q.q_no,
                "page_no": q.page,
                "text": q.text,
                "topic_id": None,
                "skill_id": None,
                "trap": None,
                "map_note": None,
            }
            for q in result.questions
        ],
    )


async def _embed(deps: IngestionDeps, material: MaterialRow, drafts: list[ChunkDraft]) -> None:
    vectors = await deps.gateway.embed([d.text for d in drafts], role="document")
    await _db(
        deps.store.insert,
        "chunks",
        [
            {
                "tenant_id": material.tenant_id,
                "material_id": material.id,
                "page_from": d.page_from,
                "page_to": d.page_to,
                "text": d.text,  # always next to the vector (AI-08)
                "content_hash": d.content_hash,
                "embedding": vector,
            }
            for d, vector in zip(drafts, vectors, strict=True)
        ],
    )


async def _fail_file(
    deps: IngestionDeps, material: MaterialRow, stage: str, message: str, detail: str
) -> None:
    log.warning("ingestion: %s of %s failed: %s", stage, material.id, detail)
    try:
        await _db(
            deps.store.set_job,
            tenant_id=material.tenant_id,
            exam_prep_id=material.exam_prep_id,
            material_id=material.id,
            stage=stage,
            status="failed",
            error=detail[:_JOB_ERROR_CHARS],
        )
        await _db(deps.store.update_material, material.id, {"status": "failed", "error": message})
    except Exception:
        log.exception("ingestion: could not mark %s as failed", material.id)


# --- §2.4 · the prep: topics, question map, stars (SM-01, SM-03, SM-04)


async def build_scope(prep_id: UUID, deps: IngestionDeps) -> None:
    """A5 per sheet → A6 → A7 per exam → write → stars. Starts only when every confirmed file is
    ready (a failed file waits for the user · spec §2.4). An unexpected error (the database, a
    bug) fails the step that was running instead of leaving it "running"."""
    try:
        await _build_scope(prep_id, deps)
    except Exception as error:
        log.exception("ingestion: the scope of %s stopped", prep_id)
        try:
            tenant = await _db(deps.store.prep_tenant, prep_id)
            jobs = await _db(
                deps.store.select, "ingestion_jobs", exam_prep_id=prep_id, material_id=None
            )
            for job in jobs:
                if job["status"] == "running" and tenant is not None:
                    await _db(
                        deps.store.set_job,
                        tenant_id=tenant,
                        exam_prep_id=prep_id,
                        stage=job["stage"],
                        status="failed",
                        error=repr(error)[:_JOB_ERROR_CHARS],
                    )
        except Exception:
            log.exception("ingestion: could not mark the scope of %s as failed", prep_id)


async def _build_scope(prep_id: UUID, deps: IngestionDeps) -> None:
    tenant = await _db(deps.store.prep_tenant, prep_id)
    if tenant is None:
        return
    materials = [m for m in await _db(deps.store.list_materials, prep_id) if m.kind_confirmed]
    if not materials or any(m.status != "ready" for m in materials):
        return
    job = {"tenant_id": tenant, "exam_prep_id": prep_id, "material_id": None}
    keys = file_keys([str(m.id) for m in materials])
    key_of = {material_id: key for key, material_id in keys.items()}
    sheets = [m for m in materials if m.kind != "past_exam"]
    exams = [m for m in materials if m.kind == "past_exam"]

    await _db(deps.store.set_job, stage="topics", status="running", **job)
    if not sheets:
        await _db(deps.store.set_job, stage="topics", status="failed", error=NO_SHEET, **job)
        return
    pages = {m.id: await _pages(deps, m.id) for m in materials}
    try:
        local = [await _local_topics(deps, m, key_of[str(m.id)], pages[m.id]) for m in sheets]
        merged = await deps.gateway.call(
            "merge_topics",
            {
                "files_topics": json.dumps(local, ensure_ascii=False, indent=1),
                "user_notes": _user_notes(materials, key_of),
            },
            MergeTopicsResult,
        )
    except (AIProviderError, AISchemaError) as error:
        log.warning("ingestion: topics of %s failed: %s", prep_id, error)
        await _db(
            deps.store.set_job,
            stage="topics",
            status="failed",
            error=str(error)[:_JOB_ERROR_CHARS],
            **job,
        )
        return
    await _db(deps.store.set_job, stage="topics", status="done", **job)

    await _db(deps.store.set_job, stage="stars", status="running", **job)
    try:
        questions = {
            m.id: await _db(deps.store.select, "past_exam_questions", material_id=m.id)
            for m in exams
        }
        mappings = await _map_questions(deps, merged, exams, key_of, questions)
    except (AIProviderError, AISchemaError) as error:
        log.warning("ingestion: question map of %s failed: %s", prep_id, error)
        await _db(
            deps.store.set_job,
            stage="stars",
            status="failed",
            error=str(error)[:_JOB_ERROR_CHARS],
            **job,
        )
        return
    new_ids: list[UUID] = []
    try:
        await _write_scope(
            deps, tenant, prep_id, merged, keys, pages, exams, questions, mappings, new_ids
        )
    except Exception as error:  # DbUnavailableError or a bug: no half scope stays behind
        log.warning("ingestion: writing the scope of %s failed: %s", prep_id, error)
        if new_ids:
            try:
                await _db(deps.store.delete_topics, new_ids)
            except Exception:
                log.exception("ingestion: could not remove the half-written scope of %s", prep_id)
        await _db(deps.store.set_job, stage="stars", status="failed", error=SCOPE_FAILED, **job)
        return
    await _db(deps.store.set_job, stage="stars", status="done", **job)


async def _pages(deps: IngestionDeps, material_id: UUID) -> list[tuple[int, str]]:
    rows = await _db(deps.store.select, "material_pages", material_id=material_id)
    return sorted((r["page_no"], r["text"]) for r in rows)


async def _local_topics(
    deps: IngestionDeps, material: MaterialRow, key: str, pages: list[tuple[int, str]]
) -> dict[str, Any]:
    result = await deps.gateway.call(
        "extract_topics_local",
        {
            "file_name": _name(material),
            "material_kind": material.kind or "other",
            "pages_text": pages_text(pages),
        },
        ExtractTopicsLocalResult,
    )
    return {
        "file": key,
        "notes": result.notes,
        "topics": [
            {**t.model_dump(), "pages": [f"{key}:{r}" for r in t.pages]} for t in result.topics
        ],
    }


def _user_notes(materials: list[MaterialRow], key_of: dict[str, str]) -> str:
    lines = [
        f"{key_of[str(m.id)]}: {m.user_note.strip()}"
        for m in materials
        if m.user_note and m.user_note.strip()
    ]
    return "\n".join(lines) or NO_NOTE


async def _map_questions(
    deps: IngestionDeps,
    merged: MergeTopicsResult,
    exams: list[MaterialRow],
    key_of: dict[str, str],
    questions: dict[UUID, list[dict[str, Any]]],
) -> dict[str, Any]:
    scope = [
        {"id": t.id, "name": t.name, "skills": [{"id": s.id, "name": s.name} for s in t.skills]}
        for t in merged.topics
    ]
    found: dict[str, Any] = {}
    for exam in exams:
        batch = [
            {"q_id": f"{key_of[str(exam.id)]}:{q['q_no']}", "text": q["text"]}
            for q in questions[exam.id]
        ]
        if not batch:
            continue
        result = await deps.gateway.call(
            "map_questions",
            {
                "topics": json.dumps(scope, ensure_ascii=False, indent=1),
                "questions": json.dumps(batch, ensure_ascii=False, indent=1),
            },
            MapQuestionsResult,
        )
        sent = {b["q_id"] for b in batch}
        if missing := sent - {m.q_id for m in result.mappings}:
            log.warning("ingestion: map_questions left out %s", sorted(missing))
        found.update({m.q_id: m for m in result.mappings if m.q_id in sent})
    return found


async def _write_scope(
    deps: IngestionDeps,
    tenant: UUID,
    prep_id: UUID,
    merged: MergeTopicsResult,
    keys: dict[str, str],
    pages: dict[UUID, list[tuple[int, str]]],
    exams: list[MaterialRow],
    questions: dict[UUID, list[dict[str, Any]]],
    mappings: dict[str, Any],
    new_ids: list[UUID],
) -> None:
    """New topics first, the old draft ones last, so a failure leaves the old scope (spec §2.4
    item 4). ``new_ids`` collects the topics written so far, for the caller to remove."""
    old = [
        t["id"]
        for t in await _db(deps.store.select, "topics", exam_prep_id=prep_id, origin="doc")
        if t["status"] in ("draft", "excluded")
    ]
    topic_ids = {t.id: uuid.uuid4() for t in merged.topics}
    skill_ids = {s.id: uuid.uuid4() for t in merged.topics for s in t.skills}
    key_by_material = {material_id: key for key, material_id in keys.items()}
    page_counts = {material_id: len(pages[UUID(material_id)]) for material_id in keys.values()}

    # Question links and how often each skill was asked (spec §2.4 item 4).
    links: dict[UUID, dict[str, Any]] = {}
    asked: Counter[str] = Counter()
    for exam in exams:
        for q in questions[exam.id]:
            m = mappings.get(f"{key_by_material[str(exam.id)]}:{q['q_no']}")
            known = m is not None and m.topic_id in topic_ids and m.skill_id in skill_ids
            if known:
                asked[m.skill_id] += 1
            links[q["id"]] = {
                "topic_id": topic_ids[m.topic_id] if known else None,
                "skill_id": skill_ids[m.skill_id] if known else None,
                "trap": m.trap if m is not None else None,
                "map_note": m.note if m is not None else None,
            }

    # Stars before anything is written (compute-importance.md §2 "ผู้เรียก"), so the topics go in
    # once with their stars and the writes are as few as possible (self-review PR #130).
    ranges = {t.id: resolve_sources(t.sources, keys, page_counts) for t in merged.topics}
    appearances = {
        (str(links[q["id"]]["topic_id"]), str(exam.id))
        for exam in exams
        for q in questions[exam.id]
        if links[q["id"]]["topic_id"] is not None
    }
    importance = {
        UUID(r.topic_id): r
        for r in compute_importance(
            [
                TopicIn(
                    id=str(topic_ids[t.id]),
                    name=t.name,
                    prereq_ids=[str(topic_ids[p]) for p in t.prereqs],
                    excluded=t.excluded_by_note,
                    importance_source="computed",
                    current_importance=None,
                    current_reason=None,
                    page_count=len(
                        {
                            (r.material_id, p)
                            for r in ranges[t.id]
                            for p in range(r.page_from, r.page_to + 1)
                        }
                    ),
                )
                for t in sorted(merged.topics, key=lambda t: t.order)
            ],
            [ExamIn(str(e.id), e.relevance_weight) for e in exams],
            appearances,
            get_settings().learning.stars,
        )
    }

    topic_rows = []
    for t in merged.topics:
        stars = importance[topic_ids[t.id]]
        topic_rows.append(
            {
                "id": topic_ids[t.id],
                "tenant_id": tenant,
                "exam_prep_id": prep_id,
                "name": t.name,
                "order_index": t.order,
                "prereq_ids": [topic_ids[p] for p in t.prereqs],
                "importance": stars.importance,
                "importance_reason": stars.reason,
                "importance_source": "computed",
                "signal_r": stars.signal_r,
                "origin": "doc",
                "status": "excluded" if t.excluded_by_note else "draft",
            }
        )
    new_ids.extend(topic_ids.values())
    await _db(deps.store.insert, "topics", topic_rows)
    await _db(
        deps.store.insert,
        "topic_skills",
        [
            {
                "id": skill_ids[s.id],
                "tenant_id": tenant,
                "topic_id": topic_ids[t.id],
                "name": s.name,
                "exam_freq": asked[s.id],
                "common_mistakes": [c.model_dump() for c in s.common_mistakes],
                "excluded": False,
            }
            for t in merged.topics
            for s in t.skills
        ],
    )
    await _db(
        deps.store.insert,
        "topic_sources",
        [
            {
                "tenant_id": tenant,
                "topic_id": topic_ids[tid],
                "material_id": UUID(r.material_id),
                "page_from": r.page_from,
                "page_to": r.page_to,
            }
            for tid, rs in ranges.items()
            for r in rs
        ],
    )
    # The question links last, in one call: until here a failure leaves the old links as they
    # were (the caller removes the new topics only).
    await _db(
        deps.store.upsert,
        "past_exam_questions",
        [{**q, **links[q["id"]]} for exam in exams for q in questions[exam.id]],
    )
    await _db(deps.store.delete_topics, old)


# --- §2.6 · what S11 shows (CM-07)

# Labels of the prep's steps (api.md `Ingestion.steps`).
STEP_NOTES = "อ่านสิ่งที่คุณเขียนกำกับไว้"
STEP_TOPICS = "หาหัวข้อและลำดับการเรียน"
STEP_EXAMS = "เทียบกับข้อสอบเก่า {n} ชุด"
_STEP_STATUS = {"queued": "pending", "running": "running", "done": "done", "failed": "failed"}


def ingestion_view(snapshot: IngestionSnapshot) -> Ingestion:
    files = []
    for f in snapshot.files:
        status = file_status(f.jobs, f.material.kind)
        running = next((stage for stage, s in f.jobs if s == "running"), None)
        is_exam = f.material.kind == "past_exam"
        files.append(
            IngestionFile(
                material_id=f.material.id,
                file_name=f.material.file_name,
                status=status,
                detail=file_detail(
                    status, running, f.page_count, f.question_count if is_exam else None
                ),
                error=f.material.error if status == "failed" else None,
            )
        )
    statuses = {f.status for f in files}
    if files and statuses == {"done"}:
        notes = "done"
    elif "failed" in statuses:
        notes = "failed"
    elif statuses & {"running", "done"}:
        notes = "running"
    else:
        notes = "pending"
    topics = _STEP_STATUS.get(snapshot.prep_jobs.get("topics", "queued"), "pending")
    stars = _STEP_STATUS.get(snapshot.prep_jobs.get("stars", "queued"), "pending")
    steps = [
        IngestionStep(label=STEP_NOTES, status=notes),
        IngestionStep(label=STEP_TOPICS, status=topics),
    ]
    exams = sum(1 for f in snapshot.files if f.material.kind == "past_exam")
    if exams:
        steps.append(IngestionStep(label=STEP_EXAMS.format(n=exams), status=stars))
    ready = notes == "done" and topics == "done" and stars == "done"
    return Ingestion(scope_ready=ready, files=files, steps=steps)


# --- §2.1, §2.7 · the runner


class IngestionRunner:
    """One background task per prep (demo on one machine · spec §2.7); a second start while it
    runs returns the same task."""

    def __init__(self, deps: IngestionDeps) -> None:
        self._deps = deps
        self._tasks: dict[UUID, asyncio.Task[None]] = {}

    def start(self, prep_id: UUID) -> asyncio.Task[None]:
        running = self._tasks.get(prep_id)
        if running is not None and not running.done():
            return running
        task = asyncio.create_task(self._run(prep_id), name=f"ingestion {prep_id}")
        self._tasks[prep_id] = task
        return task

    async def _queued(self, prep_id: UUID) -> list[MaterialRow]:
        materials = await _db(self._deps.store.list_materials, prep_id)
        return [m for m in materials if m.kind_confirmed and m.status == "confirmed"]

    async def _run(self, prep_id: UUID) -> None:
        try:
            first = True
            # A file confirmed (or retried) while the scope is being built is picked up by the
            # next pass, and the scope is built again with it (self-review PR #130).
            while (queued := await self._queued(prep_id)) or first:
                first = False
                if queued:
                    await self._restart_steps(prep_id)
                for material in queued:
                    await ingest_material(material.id, self._deps)
                await build_scope(prep_id, self._deps)
        except Exception:
            log.exception("ingestion of %s stopped", prep_id)

    async def _restart_steps(self, prep_id: UUID) -> None:
        """New files: the prep's steps are pending again, so S11 does not show an old scope as
        ready while they are read."""
        tenant = await _db(self._deps.store.prep_tenant, prep_id)
        if tenant is None:
            return
        for stage in ("topics", "stars"):
            await _db(
                self._deps.store.set_job,
                tenant_id=tenant,
                exam_prep_id=prep_id,
                stage=stage,
                status="queued",
            )

    async def retry(self, material_id: UUID) -> None:
        """`POST /materials/{id}/retry`: classify again, or read the file again and build the
        scope once every file is ready (spec §2.1 item 3)."""
        material = await _db(self._deps.store.get_material, material_id)
        if material is None or material.status != "failed":
            return
        if not material.kind_confirmed:
            await classify_material(material_id, self._deps)
            return
        await _db(
            self._deps.store.update_material, material_id, {"status": "confirmed", "error": None}
        )
        # Not awaited: the request returns, and a cancelled request cannot cancel the job.
        self.start(material.exam_prep_id)


@lru_cache
def get_ingestion_runner() -> IngestionRunner:
    """The runner of this API process, with the service role (spec §2.1 item 4). For the
    material endpoints (Junior): `get_ingestion_runner().start(prep_id)` after confirm."""
    from supabase import create_client

    env = get_settings().env

    def connect() -> Any:
        return create_client(env.supabase_url, env.supabase_service_role_key.get_secret_value())

    return IngestionRunner(
        IngestionDeps(
            gateway=get_gateway(),
            store=SupabaseIngestionStore(connect),
            files=SupabaseMaterialFiles(connect, MATERIALS_BUCKET),
            documents=PyMuPdfDocuments(),
        )
    )
