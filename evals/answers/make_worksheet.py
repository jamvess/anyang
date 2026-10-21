"""Golden set of P2: the worksheet a labeler fills, and the labels.jsonl built from it.

    uv run --project apps/api python evals/answers/make_worksheet.py           # new worksheet.md
    uv run --project apps/api python evals/answers/make_worksheet.py --build   # -> labels.jsonl

The worksheet has one section per answer: first the handwriting photos already labeled for P1
(lines copied from evals/handwriting/labels.jsonl), then typed answers up to TOTAL. Problem,
reference and answer_format come from the problems table in evals/handwriting/problems.md by
`problem_id`. --build writes only the answers whose verdict is filled, and writes nothing when
any of them breaks the rules of evals/README.md ("คู่มือ label golden set คำตอบ · P2").
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "handwriting"))
from make_labels import WRITER, Problem, load_problems  # noqa: E402

TOTAL = 50  # specs/poc/README.md P2: evals/answers/ 50 answers
VERDICTS = ("correct", "correct_with_flaw", "incomplete", "incorrect")
ERROR_TYPES = ("calculation", "sign", "wrong_method", "concept", "prerequisite", "no_answer")
METHODS = ("doc", "other")
DEFAULT_METHOD = "doc"  # evals/README.md: "ค่าปกติคือ doc"
JUDGMENT_FIELDS = ("verdict", "error_type", "first_wrong_line", "method", "labeled_by")

SECTION = re.compile(r"^## (ans_\d{3})$", re.M)
FIELD = re.compile(r"^- (\w+):(.*)$", re.M)
LINE = re.compile(r"^\d+\.\s*`(.*)`\s*$", re.M)

HEADER = """\
# ใบงาน golden set คำตอบ · P2

คู่มือ: `evals/README.md` หัวข้อ "คู่มือ label golden set คำตอบ · P2"
· คน label ต้องไม่ใช่ Jam (คนทำ P2)

- กรอกเฉพาะช่องหลัง `lines:` (verdict, error_type, first_wrong_line, method, labeled_by)
  · ช่องที่ว่างไว้ = ยังไม่ label
- ข้อที่มาจากรูป: ห้ามแก้ image, writer, problem_id, lines
  · problem, answer_format, reference แสดงไว้ให้ดูเท่านั้น
- ข้อพิมพ์ (`image: none`): ใส่ `problem_id` (P01-P17 ใน `evals/handwriting/problems.md`),
  `writer` (w01, w02, ...) และบรรทัดคำตอบทีละบรรทัด เช่น 1. `x(x^{2}-1)`
- method ว่าง = `doc` · กรอกเสร็จแล้วรัน `--build` เพื่อตรวจกติกาและสร้าง `labels.jsonl`
"""


def _section(
    ans_id: str,
    image: str,
    writer: str,
    problem_id: str,
    problem: Problem | None,
    lines: list[str],
) -> str:
    out = [f"## {ans_id}", "", f"- image: {image}", f"- writer: {writer}".rstrip()]
    out.append(f"- problem_id: {problem_id}".rstrip())
    if problem is not None:
        out += [
            f"- answer_format: {problem.answer_format}",
            f"- problem: `{problem.latex}`",
            f"- reference: `{problem.reference}`",
        ]
    numbered = [f"{i}. `{line}`" for i, line in enumerate(lines, start=1)] or ["1. ``"]
    out += ["", "lines:", "", *numbered, ""]
    out += [f"- {name}:" for name in JUDGMENT_FIELDS]
    return "\n".join(out) + "\n"


def make_worksheet(handwriting: Path) -> str:
    problems = load_problems(handwriting / "problems.md")
    with (handwriting / "photos.csv").open(encoding="utf-8", newline="") as f:
        problem_of = {row["id"]: row["problem"] for row in csv.DictReader(f)}
    photos = sorted(
        (
            json.loads(line)
            for line in (handwriting / "labels.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ),
        key=lambda row: row["id"],
    )
    photos = [row for row in photos if row.get("labeled_by")]

    sections = []
    for n, row in enumerate(photos, start=1):
        pid = problem_of[row["id"]]
        sections.append(
            _section(
                f"ans_{n:03}",
                f"../handwriting/{row['image']}",
                row["writer"],
                pid,
                problems[pid],
                row["lines"],
            )
        )
    for n in range(len(photos) + 1, TOTAL + 1):
        sections.append(_section(f"ans_{n:03}", "none", "", "", None, []))
    return HEADER + "\n" + "\n".join(sections)


def parse_worksheet(text: str) -> list[tuple[str, dict[str, str | None], list[str]]]:
    """(id, fields, lines) per section. Blank fields are None; empty `` lines are dropped."""
    parts = SECTION.split(text)
    answers = []
    for ans_id, body in zip(parts[1::2], parts[2::2], strict=True):
        fields = {name: (value.strip() or None) for name, value in FIELD.findall(body)}
        lines = [line for line in LINE.findall(body) if line.strip()]
        answers.append((ans_id, fields, lines))
    return answers


def to_label(
    ans_id: str, fields: dict[str, str | None], lines: list[str], problems: dict[str, Problem]
) -> tuple[dict | None, list[str]]:
    errors: list[str] = []

    def bad(message: str) -> None:
        errors.append(f"{ans_id}: {message}")

    verdict = fields.get("verdict")
    error_type = fields.get("error_type")
    method = fields.get("method") or DEFAULT_METHOD
    raw_line = fields.get("first_wrong_line")
    pid = fields.get("problem_id")
    writer = fields.get("writer")

    if verdict not in VERDICTS:
        bad(f"verdict must be one of {', '.join(VERDICTS)}, got {verdict!r}")
    if not fields.get("labeled_by"):
        bad("labeled_by is empty")
    if pid not in problems:
        bad(f"problem_id must be one of P01-P{len(problems):02}, got {pid!r}")
    if not writer or not WRITER.match(writer):
        bad(f"writer must look like w01, got {writer!r}")
    if method not in METHODS:
        bad(f"method must be one of {', '.join(METHODS)}, got {method!r}")

    if verdict == "correct":
        if error_type is not None:
            bad("error_type must be empty when verdict is correct")
    elif error_type not in ERROR_TYPES:
        bad(f"error_type must be one of {', '.join(ERROR_TYPES)}, got {error_type!r}")
    if verdict == "incomplete" and error_type != "concept":
        bad("error_type must be concept when verdict is incomplete")
    if not lines and error_type != "no_answer":
        bad("an answer without lines must have error_type no_answer")

    first_wrong_line: int | None = None
    if verdict in ("correct", "incomplete") or error_type == "no_answer":
        if raw_line is not None:
            bad("first_wrong_line must be empty for correct, incomplete or no_answer")
    elif raw_line is None:
        bad("first_wrong_line is empty")
    elif not raw_line.isdigit() or not 1 <= int(raw_line) <= len(lines):
        bad(f"first_wrong_line must be a line number from 1 to {len(lines)}, got {raw_line!r}")
    else:
        first_wrong_line = int(raw_line)

    if errors:
        return None, errors
    problem = problems[pid]
    image = fields.get("image")
    return {
        "id": ans_id,
        "image": None if image in (None, "none") else image,
        "writer": writer,
        "problem": problem.latex,
        "answer_format": problem.answer_format,
        "reference": problem.reference,
        "lines": lines,
        "verdict": verdict,
        "error_type": error_type,
        "first_wrong_line": first_wrong_line,
        "method": method,
        "labeled_by": fields["labeled_by"],
    }, []


def build(text: str, problems: dict[str, Problem]) -> tuple[list[dict], list[str]]:
    rows, errors = [], []
    for ans_id, fields, lines in parse_worksheet(text):
        if fields.get("verdict") is None:
            continue  # not labeled yet
        row, row_errors = to_label(ans_id, fields, lines, problems)
        errors += row_errors
        if row is not None:
            rows.append(row)
    return rows, errors


def main(
    argv: list[str] | None = None,
    base: Path = HERE,
    handwriting: Path = HERE.parent / "handwriting",
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true", help="worksheet.md -> labels.jsonl")
    args = parser.parse_args(argv)
    worksheet = base / "worksheet.md"

    if not args.build:
        if worksheet.exists():
            print(f"{worksheet} already exists; not overwriting labels in progress")
            return 1
        worksheet.write_text(make_worksheet(handwriting), encoding="utf-8")
        print(f"wrote {worksheet} ({TOTAL} answers)")
        return 0

    rows, errors = build(
        worksheet.read_text(encoding="utf-8"), load_problems(handwriting / "problems.md")
    )
    if errors:
        print("\n".join(errors))
        print(f"{len(errors)} problems, labels.jsonl not written")
        return 1
    (base / "labels.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    print(f"wrote {base / 'labels.jsonl'} ({len(rows)} labeled of {TOTAL})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
