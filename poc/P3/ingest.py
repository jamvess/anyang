"""PoC P3 step 1 · ingest (ai-orchestration.md §2.3.3).

Sheets: text per page with PyMuPDF. Every file gets a text-quality check, because the scanned
exams carry an English-only OCR layer that looks like text but is junk (sources.md).
Files that fail the check are rendered page by page and read by vision_extract_pages (all
pages in one call; see vision_pages for why this differs from A2 in the spec).
Past exams are then split into sub-questions by A4 split_past_exam.

    cd apps/api && uv run python ../../poc/P3/ingest.py [--force]

Writes out/pages/<file>.json, out/questions/<file>.json and out/ingest.json. Files already in
out/ are reused unless --force, so a re-run does not pay for the same calls twice.
"""

import argparse
import asyncio
import re
import time
from pathlib import Path

import pymupdf
from common import OUT, RAW, Run, read_json, write_json

from app.ai.gateway import Image
from app.models.scope_ai import SplitPastExamResult, VisionExtractPagesResult

# A page of Thai course text has far more Thai than Latin letters; the junk OCR layer of the
# scanned exams has none. Measured per file on MTH10101 and reported in out/ingest.json; the
# value is a PoC choice to be confirmed by the numbers, not a learning-model threshold.
MIN_THAI_SHARE = 0.3
RENDER_DPI = 150

_THAI = re.compile(r"[฀-๿]")
_LATIN = re.compile(r"[A-Za-z]")


def thai_share(text: str) -> float:
    thai, latin = len(_THAI.findall(text)), len(_LATIN.findall(text))
    return thai / (thai + latin) if thai + latin else 0.0


def kind_of(path: Path) -> str:
    # Classification (A1) is out of P3's scope; the file names already say what each file is.
    return "past_exam" if path.stem.startswith("midterm") else "lecture"


async def vision_pages(run: Run, path: Path) -> tuple[list[dict], str]:
    """All pages in one vision_extract_pages call: the free tier allows only 20 requests per
    day per model, so one call per page (vision_extract, as in the spec) does not fit."""
    doc = pymupdf.open(path)
    images = [
        Image(data=page.get_pixmap(dpi=RENDER_DPI).tobytes("png"), mime_type="image/png")
        for page in doc
    ]
    result = await run.call(
        f"ingest:{path.stem}:vision",
        "vision_extract_pages",
        {"images": images, "file_name": path.name, "page_count": str(len(images))},
        VisionExtractPagesResult,
    )
    if len(result.pages) != len(images):
        raise ValueError(f"{path.name}: {len(images)} pages sent, {len(result.pages)} returned")
    return [{"page": p.page, "text": p.text} for p in result.pages], result.notes


def pages_text(pages: list[dict]) -> str:
    return "\n\n".join(f"[p.{p['page']}]\n{p['text']}" for p in pages)


async def ingest_file(run: Run, path: Path, force: bool) -> dict:
    started = time.perf_counter()
    pages_path = OUT / "pages" / f"{path.stem}.json"
    doc = pymupdf.open(path)
    layer = [page.get_text() for page in doc]
    share = thai_share("".join(layer))
    method = "text_layer" if share >= MIN_THAI_SHARE else "vision"

    if pages_path.exists() and not force:
        cached = read_json(pages_path)
        pages, notes = cached["pages"], cached["notes"]
    elif method == "text_layer":
        pages, notes = [{"page": i, "text": t.strip()} for i, t in enumerate(layer, 1)], ""
    else:
        pages, notes = await vision_pages(run, path)
    write_json(pages_path, {"file": path.name, "method": method, "notes": notes, "pages": pages})

    kind = kind_of(path)
    questions = None
    if kind == "past_exam":
        questions_path = OUT / "questions" / f"{path.stem}.json"
        if questions_path.exists() and not force:
            questions = read_json(questions_path)["questions"]
        else:
            result = await run.call(
                f"ingest:{path.stem}:split",
                "split_past_exam",
                {"file_name": path.name, "pages_text": pages_text(pages)},
                SplitPastExamResult,
            )
            questions = result.model_dump(mode="json")["questions"]
            write_json(
                questions_path,
                {"file": path.name, "notes": result.notes, **result.model_dump(mode="json")},
            )

    tokens_in, tokens_out = run.tokens(f"ingest:{path.stem}:")
    summary = {
        "file": path.name,
        "kind": kind,
        "pages": len(doc),
        "thai_share_text_layer": round(share, 3),
        "method": method,
        "questions": len(questions) if questions is not None else None,
        "seconds": round(time.perf_counter() - started, 1),  # includes free-tier waiting
        "ai_seconds": round(run.ai_seconds(f"ingest:{path.stem}:"), 1),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }
    print(f"{path.name}: {summary}", flush=True)
    return summary


async def main(force: bool) -> None:
    run = Run()
    files = sorted(RAW.glob("*.pdf"))
    print(f"model {run.model} · {len(files)} files", flush=True)
    summaries = []
    for path in files:  # one file at a time so seconds per file stay comparable
        summaries.append(await ingest_file(run, path, force))
    write_json(OUT / "ingest.json", {"model": run.model, "files": summaries})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="redo files already in out/")
    asyncio.run(main(parser.parse_args().force))
