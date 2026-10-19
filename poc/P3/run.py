"""PoC P3 step 2 · topics and stars (ai-orchestration.md §2.3.4-2.3.5).

A5 extract_topics_local per sheet -> A6 merge_topics -> A7 map_questions per exam -> stars.
Needs ingest.py first.

    cd apps/api && uv run python ../../poc/P3/run.py [--force]

Writes results/<model>/topics.json, mapping.json and run.json (committed: topic names, page
ranges, stars and timings only, no course text). A5 results are cached in out/a5/<model>/.
"""

import argparse
import asyncio
import json
import time

from common import OUT, RESULTS, Run, read_json, write_json
from stars import Topic, stars

from app.models.scope_ai import ExtractTopicsLocalResult, MapQuestionsResult, MergeTopicsResult
from app.settings import get_settings

# File kinds from evals/topics/mth10101/sources.md (classification A1 is out of P3's scope).
EXERCISE_FILES = {"sheet-03", "sheet-04"}
NO_USER_NOTES = "ไม่มี"


def pages_text(pages: list[dict]) -> str:
    return "\n\n".join(f"[p.{p['page']}]\n{p['text']}" for p in pages)


async def extract_local(run: Run, stem: str, model: str, force: bool) -> dict:
    cache = OUT / "a5" / model / f"{stem}.json"
    if cache.exists() and not force:
        return read_json(cache)
    pages = read_json(OUT / "pages" / f"{stem}.json")["pages"]
    result = await run.call(
        f"run:{stem}:a5",
        "extract_topics_local",
        {
            "file_name": f"{stem}.pdf",
            "material_kind": "exercise" if stem in EXERCISE_FILES else "lecture",
            "pages_text": pages_text(pages),
        },
        ExtractTopicsLocalResult,
    )
    data = {
        "file": stem,
        "notes": result.notes,
        "topics": [
            {**t.model_dump(), "pages": [f"{stem}:{r}" for r in t.pages]} for t in result.topics
        ],
    }
    write_json(cache, data)
    return data


async def main(force: bool) -> None:
    settings = get_settings()
    run = Run()
    model = run.model.partition(":")[2]
    ingest = read_json(OUT / "ingest.json")
    sheets = [f["file"].removesuffix(".pdf") for f in ingest["files"] if f["kind"] == "lecture"]
    exams = [f["file"].removesuffix(".pdf") for f in ingest["files"] if f["kind"] == "past_exam"]
    print(f"model {run.model} · sheets {sheets} · exams {exams}", flush=True)
    started = time.perf_counter()

    local = [await extract_local(run, stem, model, force) for stem in sheets]

    merged = await run.call(
        "run:merge",
        "merge_topics",
        {
            "files_topics": json.dumps(local, ensure_ascii=False, indent=1),
            "user_notes": NO_USER_NOTES,
        },
        MergeTopicsResult,
    )
    scope = [
        {"id": t.id, "name": t.name, "skills": [{"id": s.id, "name": s.name} for s in t.skills]}
        for t in merged.topics
    ]

    mapping: dict[str, dict] = {}
    for stem in exams:
        questions = read_json(OUT / "questions" / f"{stem}.json")["questions"]
        batch = [{"q_id": f"{stem}:{q['q_no']}", "text": q["text"]} for q in questions]
        result = await run.call(
            f"run:{stem}:a7",
            "map_questions",
            {
                "topics": json.dumps(scope, ensure_ascii=False, indent=1),
                "questions": json.dumps(batch, ensure_ascii=False, indent=1),
            },
            MapQuestionsResult,
        )
        sent = {q["q_id"] for q in batch}
        got = {m.q_id for m in result.mappings}
        if sent != got:
            print(f"  {stem}: A7 missing {sorted(sent - got)} extra {sorted(got - sent)}")
        mapping.update({m.q_id: m.model_dump(exclude={"q_id"}) for m in result.mappings})

    known = {t.id for t in merged.topics}
    appearances = {
        (m["topic_id"], q.split(":")[0]) for q, m in mapping.items() if m["topic_id"] in known
    }
    weights = {e: settings.learning.stars.weight_same_instructor for e in exams}
    importance = stars(
        [Topic(t.id, t.prereqs, t.excluded_by_note, t.name) for t in merged.topics],
        weights,
        appearances,
        settings.learning.stars,
    )

    folder = RESULTS / model
    write_json(
        folder / "topics.json",
        [
            {
                "id": t.id,
                "name": t.name,
                "order": t.order,
                "sources": t.sources,
                "prereqs": t.prereqs,
                "stars": importance[t.id].importance,
                "signal_r": round(importance[t.id].signal_r, 3),
                "reason": importance[t.id].reason,
                "skills": [s.name for s in t.skills],
            }
            for t in merged.topics
        ],
    )
    write_json(folder / "mapping.json", mapping)
    calls = []
    for tag, r in run.records:
        parts = tag.split(":")
        calls.append(
            {
                "tag": tag,
                "file": parts[1] if len(parts) == 3 else "",
                "purpose": r.purpose,
                "status": r.status,
                "latency_ms": round(r.latency_ms),
                "tokens_in": r.tokens_in,
                "tokens_out": r.tokens_out,
                "schema_retries": r.schema_retries,
            }
        )
    # Ingest calls belong to the same files; add them so minutes per file cover the whole path.
    for f in ingest["files"]:
        if f["method"] == "vision" or f["kind"] == "past_exam":
            calls.append(
                {
                    "tag": f"ingest:{f['file'].removesuffix('.pdf')}",
                    "file": f["file"].removesuffix(".pdf"),
                    "purpose": "ingest",
                    "status": "ok",
                    "latency_ms": round(f["ai_seconds"] * 1000),
                    "tokens_in": f["tokens_in"],
                    "tokens_out": f["tokens_out"],
                    "schema_retries": 0,
                }
            )
    write_json(
        folder / "run.json",
        {
            "model": run.model,
            "wall_seconds": round(time.perf_counter() - started, 1),
            "tokens_in": sum(c["tokens_in"] for c in calls),
            "tokens_out": sum(c["tokens_out"] for c in calls),
            "calls": calls,
            "notes": {"a5": {d["file"]: d["notes"] for d in local}, "a6": merged.notes},
        },
    )
    print(f"{len(merged.topics)} topics, {len(mapping)} questions mapped -> {folder}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="redo A5 even if cached")
    asyncio.run(main(parser.parse_args().force))
