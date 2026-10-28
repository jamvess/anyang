"""Tests for make_worksheet.py: the golden set worksheet of P2 (evals/README.md
"คู่มือ label golden set คำตอบ · P2", specs/poc/README.md P2: 50 answers).

    uv run --project apps/api pytest evals/answers
"""

import json
import re
import shutil
import sys
from pathlib import Path

import pytest
from make_worksheet import main

HERE = Path(__file__).parent
HANDWRITING = HERE.parent / "handwriting"
sys.path.insert(0, str(HERE.parent))
from run_eval import score  # noqa: E402

LINES_001 = ["x^{3}-x", "=x(x^{2}-1)"]
LINES_002 = ["\\lim_{x \\to 2} \\frac{x^{2}-4}{x^{2}-3x+2}", "=\\frac{-4}{-6+2}", "=1"]


@pytest.fixture
def dirs(tmp_path: Path) -> tuple[Path, Path]:
    """(answers dir, handwriting dir) with 2 labeled photos: hw_001 is P01, hw_002 is P05."""
    answers = tmp_path / "answers"
    handwriting = tmp_path / "handwriting"
    answers.mkdir()
    handwriting.mkdir()
    shutil.copy(HANDWRITING / "problems.md", handwriting / "problems.md")
    (handwriting / "photos.csv").write_text(
        "id,writer,problem,tool,medium\nhw_001,w01,P01,stylus,paper\nhw_002,w03,P05,pen,paper\n",
        encoding="utf-8",
    )
    rows = [
        {"id": "hw_001", "image": "raw/hw_001.jpg", "writer": "w01", "lines": LINES_001},
        {"id": "hw_002", "image": "raw/hw_002.png", "writer": "w03", "lines": LINES_002},
    ]
    (handwriting / "labels.jsonl").write_text(
        "".join(
            json.dumps({**r, "problem": "", "unclear_lines": [], "labeled_by": "May"}) + "\n"
            for r in rows
        ),
        encoding="utf-8",
    )
    return answers, handwriting


def generate(dirs: tuple[Path, Path]) -> str:
    answers, handwriting = dirs
    assert main([], base=answers, handwriting=handwriting) == 0
    return (answers / "worksheet.md").read_text(encoding="utf-8")


def build(dirs: tuple[Path, Path], text: str) -> tuple[int, list[dict]]:
    answers, handwriting = dirs
    (answers / "worksheet.md").write_text(text, encoding="utf-8")
    code = main(["--build"], base=answers, handwriting=handwriting)
    path = answers / "labels.jsonl"
    rows = (
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if (path.exists())
        else []
    )
    return code, rows


def section(text: str, ans_id: str) -> str:
    match = re.search(rf"^## {ans_id}\n.*?(?=^## |\Z)", text, flags=re.M | re.S)
    assert match, f"no section {ans_id}"
    return match.group(0)


def fill(text: str, ans_id: str, lines: list[str] | None = None, **fields: object) -> str:
    """Fill one section the way a labeler would: `- name: value` and the numbered lines."""
    old = section(text, ans_id)
    new = old
    for name, value in fields.items():
        filled = f"- {name}: {value}"
        new, count = re.subn(rf"^- {name}:.*$", lambda _, s=filled: s, new, flags=re.M)
        assert count == 1, f"{ans_id} has no field {name}"
    if lines is not None:
        numbered = "\n".join(f"{i}. `{line}`" for i, line in enumerate(lines, start=1))
        new, count = re.subn(
            r"(?<=^lines:\n\n).*?(?=\n\n- )", lambda _: numbered, new, flags=re.M | re.S
        )
        assert count == 1, f"{ans_id} has no lines block"
    return text.replace(old, new)


# --- the worksheet ------------------------------------------------------------------------------


def test_evals_readme_p2_worksheet_has_50_answers(dirs):
    text = generate(dirs)

    ids = re.findall(r"^## (ans_\d{3})$", text, flags=re.M)
    assert ids == [f"ans_{i:03}" for i in range(1, 51)]


def test_evals_readme_p2_photo_answers_come_first_with_lines_from_handwriting(dirs):
    text = generate(dirs)

    first = section(text, "ans_001")
    assert "- image: ../handwriting/raw/hw_001.jpg" in first
    assert "- writer: w01" in first
    assert "- problem_id: P01" in first
    assert "- answer_format: factored" in first
    assert "x(x-1)(x+1)" in first  # reference of P01, shown to the labeler
    assert "1. `x^{3}-x`\n2. `=x(x^{2}-1)`" in first
    assert "- image: ../handwriting/raw/hw_002.png" in section(text, "ans_002")


def test_evals_readme_p2_typed_answers_fill_the_rest_and_start_empty(dirs):
    text = generate(dirs)

    typed = section(text, "ans_003")
    assert "- image: none" in typed
    assert re.search(r"^- problem_id: *$", typed, flags=re.M)
    assert re.search(r"^- writer: *$", typed, flags=re.M)


@pytest.mark.parametrize("field", ["verdict", "error_type", "first_wrong_line", "labeled_by"])
def test_evals_readme_p2_judgment_fields_start_empty_in_every_answer(dirs, field):
    text = generate(dirs)

    values = re.findall(rf"^- {field}:(.*)$", text, flags=re.M)
    assert len(values) == 50
    assert all(not v.strip() for v in values)


def test_evals_readme_p2_existing_worksheet_is_never_overwritten(dirs):
    answers, handwriting = dirs
    (answers / "worksheet.md").write_text("labels in progress", encoding="utf-8")

    assert main([], base=answers, handwriting=handwriting) == 1
    assert (answers / "worksheet.md").read_text(encoding="utf-8") == "labels in progress"


# --- --build ------------------------------------------------------------------------------------


def test_evals_readme_p2_build_writes_only_labeled_answers(dirs):
    text = generate(dirs)
    text = fill(text, "ans_001", verdict="incomplete", error_type="concept", labeled_by="May")

    code, rows = build(dirs, text)

    assert code == 0
    assert [r["id"] for r in rows] == ["ans_001"]


def test_evals_readme_p2_build_row_has_the_readme_fields(dirs):
    text = generate(dirs)
    text = fill(
        text,
        "ans_002",
        verdict="incorrect",
        error_type="prerequisite",
        first_wrong_line=2,
        labeled_by="Junior",
    )

    _, rows = build(dirs, text)

    assert rows == [
        {
            "id": "ans_002",
            "image": "../handwriting/raw/hw_002.png",
            "writer": "w03",
            "problem": "\\lim_{x \\to 2} \\frac{x^{2}-4}{x^{2}-3x+2}",
            "answer_format": "expression",
            "reference": "4",
            "lines": LINES_002,
            "verdict": "incorrect",
            "error_type": "prerequisite",
            "first_wrong_line": 2,
            "method": "doc",
            "labeled_by": "Junior",
        }
    ]


def test_evals_readme_p2_typed_answer_takes_problem_from_problem_id(dirs):
    text = generate(dirs)
    text = fill(
        text,
        "ans_003",
        lines=["\\cos(3x)"],
        problem_id="P06",
        writer="w02",
        verdict="incorrect",
        error_type="concept",
        first_wrong_line=1,
        labeled_by="May",
    )

    _, rows = build(dirs, text)

    row = rows[0]
    assert row["image"] is None
    assert row["problem"] == "\\lim_{x \\to 0} \\frac{\\sin(3x)}{x}"
    assert row["reference"] == "3"
    assert row["answer_format"] == "expression"
    assert row["lines"] == ["\\cos(3x)"]


def test_evals_readme_p2_method_other_is_kept(dirs):
    text = generate(dirs)
    text = fill(text, "ans_001", verdict="correct", method="other", labeled_by="May")

    _, rows = build(dirs, text)

    assert rows[0]["method"] == "other"
    assert rows[0]["error_type"] is None
    assert rows[0]["first_wrong_line"] is None


def test_evals_readme_p2_no_answer_may_have_no_lines(dirs):
    text = generate(dirs)
    text = fill(
        text,
        "ans_004",
        lines=[],
        problem_id="P15",
        writer="w02",
        verdict="incorrect",
        error_type="no_answer",
        labeled_by="May",
    )

    code, rows = build(dirs, text)

    assert code == 0
    assert rows[0]["lines"] == []


def test_evals_readme_p2_built_labels_are_read_by_run_eval(dirs):
    text = generate(dirs)
    text = fill(text, "ans_001", verdict="correct", labeled_by="May")
    text = fill(
        text,
        "ans_002",
        verdict="incorrect",
        error_type="sign",
        first_wrong_line=1,
        labeled_by="May",
    )

    _, rows = build(dirs, text)

    assert score(rows, rows)["passed"]


# --- --build refuses labels that break the README rules -----------------------------------------

BAD = [
    ("unknown verdict", {"verdict": "wrong", "labeled_by": "May"}),
    ("correct with error_type", {"verdict": "correct", "error_type": "sign", "labeled_by": "May"}),
    (
        "wrong without error_type",
        {"verdict": "incorrect", "first_wrong_line": 1, "labeled_by": "May"},
    ),
    (
        "unknown error_type",
        {"verdict": "incorrect", "error_type": "typo", "first_wrong_line": 1, "labeled_by": "May"},
    ),
    (
        "incomplete not concept",
        {"verdict": "incomplete", "error_type": "sign", "labeled_by": "May"},
    ),
    ("incorrect without line", {"verdict": "incorrect", "error_type": "sign", "labeled_by": "May"}),
    ("correct with line", {"verdict": "correct", "first_wrong_line": 1, "labeled_by": "May"}),
    (
        "incomplete with line",
        {
            "verdict": "incomplete",
            "error_type": "concept",
            "first_wrong_line": 1,
            "labeled_by": "May",
        },
    ),
    (
        "no_answer with line",
        {
            "verdict": "incorrect",
            "error_type": "no_answer",
            "first_wrong_line": 1,
            "labeled_by": "May",
        },
    ),
    (
        "line after the last line",
        {"verdict": "incorrect", "error_type": "sign", "first_wrong_line": 3, "labeled_by": "May"},
    ),
    (
        "line zero",
        {"verdict": "incorrect", "error_type": "sign", "first_wrong_line": 0, "labeled_by": "May"},
    ),
    ("unknown method", {"verdict": "correct", "method": "book", "labeled_by": "May"}),
    ("no labeled_by", {"verdict": "correct"}),
]


@pytest.mark.parametrize(("case", "fields"), BAD, ids=[case for case, _ in BAD])
def test_evals_readme_p2_build_refuses_labels_that_break_the_rules(dirs, case, fields):
    answers, _ = dirs
    text = fill(generate(dirs), "ans_001", **fields)  # ans_001 has 2 lines

    code, _ = build(dirs, text)

    assert code == 1
    assert not (answers / "labels.jsonl").exists()


@pytest.mark.parametrize(
    ("case", "fields"),
    [
        ("typed without problem_id", {"writer": "w02"}),
        ("typed with unknown problem_id", {"problem_id": "P99", "writer": "w02"}),
        ("typed without writer", {"problem_id": "P06"}),
    ],
)
def test_evals_readme_p2_build_refuses_typed_answers_without_their_problem(dirs, case, fields):
    answers, _ = dirs
    text = fill(
        generate(dirs),
        "ans_003",
        lines=["3"],
        verdict="correct",
        labeled_by="May",
        **fields,
    )

    code, _ = build(dirs, text)

    assert code == 1
    assert not (answers / "labels.jsonl").exists()


def test_evals_readme_p2_build_refuses_empty_lines_unless_no_answer(dirs):
    answers, _ = dirs
    text = fill(
        generate(dirs),
        "ans_003",
        lines=[],
        problem_id="P06",
        writer="w02",
        verdict="incorrect",
        error_type="concept",
        first_wrong_line=1,
        labeled_by="May",
    )

    code, _ = build(dirs, text)

    assert code == 1
    assert not (answers / "labels.jsonl").exists()


def test_evals_readme_p2_build_error_names_the_answer(dirs, capsys):
    text = fill(generate(dirs), "ans_002", verdict="wrong", labeled_by="May")

    build(dirs, text)

    assert "ans_002" in capsys.readouterr().out
