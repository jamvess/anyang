"""PoC P1 step 1 · read every handwriting image with extract_answer (prompts/extract_answer/v1).

    cd apps/api
    uv run python ../../poc/P1/run.py --model gemini:gemini-3.5-flash-lite [--limit 15]

One call per image through the AI gateway. Answers are cached in out/<model>/hw_NNN.json, so a
run stopped by the free-tier quota (20 requests per day per model) continues the next day
without paying twice. --exclude-writer drops writers who did not agree to the free tier.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "poc" / "P3"))  # Run: free-tier spacing, raw answers, call log

from common import Run, write_json  # noqa: E402

from app.ai.gateway import AIProviderError, AISchemaError, Image  # noqa: E402
from app.models.scope_ai import ExtractAnswerResult  # noqa: E402

LABELS = REPO / "evals" / "handwriting" / "labels.jsonl"
IMAGES = REPO / "evals" / "handwriting"
OUT = HERE / "out"  # gitignored
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


def load_labels() -> list[dict]:
    lines = LABELS.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


async def read_one(run: Run, entry: dict, folder: Path) -> dict:
    path = IMAGES / entry["image"]
    data = path.read_bytes()
    # Some files are JPEG with a .PNG name; trust the bytes.
    mime = "image/jpeg" if data[:2] == b"\xff\xd8" else MIME[path.suffix.lower()]
    started = time.perf_counter()
    result = await run.call(
        f"p1:{entry['id']}",
        "extract_answer",
        {"image": Image(data=data, mime_type=mime), "problem_text": entry["problem"]},
        ExtractAnswerResult,
    )
    record = run.records[-1][1]
    answer = {
        "id": entry["id"],
        "model": run.model,
        "lines": [line.model_dump() for line in result.lines],
        "notes": result.notes,
        "latency_ms": round(record.latency_ms),
        "wall_ms": round((time.perf_counter() - started) * 1000),
        "tokens_in": record.tokens_in,
        "tokens_out": record.tokens_out,
        "schema_retries": record.schema_retries,
    }
    write_json(folder / f"{entry['id']}.json", answer)
    return answer


async def main(model: str, limit: int | None, exclude: set[str]) -> None:
    run = Run(out=OUT, model=model)
    folder = OUT / model.partition(":")[2]
    todo = [
        e
        for e in load_labels()
        if e["writer"] not in exclude and not (folder / f"{e['id']}.json").exists()
    ]
    if limit is not None:
        todo = todo[:limit]
    print(f"{model}: {len(todo)} images to read", flush=True)
    for entry in todo:  # one at a time: Run spaces requests for the free tier
        try:
            answer = await read_one(run, entry, folder)
            print(f"  {entry['id']}: {len(answer['lines'])} lines, {answer['latency_ms']} ms")
        except (AIProviderError, AISchemaError) as error:
            print(f"  {entry['id']}: {type(error).__name__}: {str(error)[:150]}")
            if "429" in str(error):
                print("  daily quota reached; run again tomorrow to continue")
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="e.g. gemini:gemini-3.5-flash-lite")
    parser.add_argument("--limit", type=int, help="read at most N images in this run")
    parser.add_argument(
        "--exclude-writer", action="append", default=[], help="writer code to skip, e.g. w04"
    )
    args = parser.parse_args()
    asyncio.run(main(args.model, args.limit, set(args.exclude_writer)))
