"""Build the skeleton of evals/handwriting/labels.jsonl from photos.csv.

Appends one entry per photo that is not labeled yet and never rewrites existing entries,
so it is safe to run again after new photos arrive. See evals/handwriting/README.md.

    uv run --project apps/api python evals/handwriting/make_labels.py          # write
    uv run --project apps/api python evals/handwriting/make_labels.py --check  # validate only
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).parent
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
TOOLS = ("pen", "pencil")
ANSWER_FORMATS = ("expression", "factored", "equation")

# Dataset targets from the table "เป้าของชุดรูป" in README.md. Keep the two in sync.
MIN_IMAGES = 30
MIN_WRITERS = 5
MAX_IMAGES_PER_WRITER = 10
MIN_IMAGES_PER_FORMAT = 5

ROW = re.compile(
    r"^\|\s*(P\d{2})\s*\|[^|]*\|\s*(\w+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|$"
)
PHOTO_ID = re.compile(r"^hw_\d{3}$")
WRITER = re.compile(r"^w\d{2}$")


@dataclass(frozen=True)
class Problem:
    answer_format: str
    latex: str
    reference: str


def load_problems(path: Path) -> dict[str, Problem]:
    problems = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if m := ROW.match(line.strip()):
            pid, answer_format, latex, reference = m.groups()
            problems[pid] = Problem(answer_format, latex, reference)
    return problems


def find_image(raw_dir: Path, photo_id: str) -> Path | None:
    for ext in IMAGE_EXTENSIONS:
        path = raw_dir / f"{photo_id}{ext}"
        if path.exists():
            return path
    return None


def validate(
    photos: list[dict[str, str]], problems: dict[str, Problem], raw_dir: Path
) -> list[str]:
    errors = []
    seen: set[str] = set()
    for n, row in enumerate(photos, start=2):  # line 1 is the header
        pid = row.get("id", "")
        where = f"photos.csv line {n} ({pid or 'no id'})"
        if not PHOTO_ID.match(pid):
            errors.append(f"{where}: id must look like hw_001")
        elif pid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(pid)
        if not WRITER.match(row.get("writer", "")):
            errors.append(f"{where}: writer must be a code like w01, never a real name")
        if row.get("problem") not in problems:
            errors.append(
                f"{where}: problem {row.get('problem')!r} is not in problems.md"
            )
        if row.get("tool") not in TOOLS:
            errors.append(f"{where}: tool must be one of {', '.join(TOOLS)}")
        if PHOTO_ID.match(pid) and find_image(raw_dir, pid) is None:
            errors.append(f"{where}: no image raw/{pid}.jpg (or .jpeg/.png)")
    return errors


def read_labels(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def new_entries(
    photos: list[dict[str, str]],
    problems: dict[str, Problem],
    raw_dir: Path,
    labeled_ids: set[str],
) -> list[dict]:
    entries = []
    for row in photos:
        if row["id"] in labeled_ids:
            continue
        image = find_image(raw_dir, row["id"])
        assert image is not None  # validate() ran first
        entries.append(
            {
                "id": row["id"],
                "image": f"raw/{image.name}",
                "writer": row["writer"],
                "problem": problems[row["problem"]].latex,
                "lines": [],
                "unclear_lines": [],
                "labeled_by": None,
            }
        )
    return entries


def summarize(photos: list[dict[str, str]], problems: dict[str, Problem]) -> list[str]:
    per_writer = Counter(row["writer"] for row in photos)
    per_format = Counter(problems[row["problem"]].answer_format for row in photos)
    per_tool = Counter(row["tool"] for row in photos)

    def mark(ok: bool) -> str:
        return "OK  " if ok else "TODO"

    busiest = per_writer.most_common(1)[0] if per_writer else ("-", 0)
    report = [
        f"{mark(len(photos) >= MIN_IMAGES)} images: {len(photos)} (target >= {MIN_IMAGES})",
        (
            f"{mark(len(per_writer) >= MIN_WRITERS)} writers: {len(per_writer)}"
            f" (target >= {MIN_WRITERS})"
        ),
        (
            f"{mark(busiest[1] <= MAX_IMAGES_PER_WRITER)} most images by one writer:"
            f" {busiest[1]} by {busiest[0]} (target <= {MAX_IMAGES_PER_WRITER})"
        ),
    ]
    for answer_format in ANSWER_FORMATS:
        count = per_format[answer_format]
        report.append(
            f"{mark(count >= MIN_IMAGES_PER_FORMAT)} {answer_format}: {count}"
            f" (target >= {MIN_IMAGES_PER_FORMAT})"
        )
    report.append(
        f"{mark(all(per_tool[t] for t in TOOLS))} tools: "
        + ", ".join(f"{t} {per_tool[t]}" for t in TOOLS)
    )
    report.append("     wrong lines (>= 8) and crossed-out lines (>= 3): check by eye")
    return report


def main(argv: list[str] | None = None, base: Path = HERE) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="validate only, write nothing"
    )
    args = parser.parse_args(argv)

    problems = load_problems(base / "problems.md")
    with (base / "photos.csv").open(encoding="utf-8", newline="") as f:
        photos = list(csv.DictReader(f))
    raw_dir = base / "raw"

    errors = validate(photos, problems, raw_dir)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    labels_path = base / "labels.jsonl"
    labels = read_labels(labels_path)
    labeled_ids = {entry["id"] for entry in labels}
    photo_ids = {row["id"] for row in photos}
    for orphan in sorted(labeled_ids - photo_ids):
        print(
            f"warning: {orphan} is in labels.jsonl but not in photos.csv",
            file=sys.stderr,
        )

    entries = new_entries(photos, problems, raw_dir, labeled_ids)
    if not args.check and entries:
        text = labels_path.read_text(encoding="utf-8") if labels_path.exists() else ""
        with labels_path.open("a", encoding="utf-8", newline="\n") as f:
            if text and not text.endswith("\n"):
                f.write("\n")
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    verb = "would add" if args.check else "added"
    print(f"{verb} {len(entries)} new entries, {len(labels)} already in labels.jsonl")
    print("\n".join(summarize(photos, problems)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
