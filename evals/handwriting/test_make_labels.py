"""Tests for make_labels.py.

uv run --project apps/api pytest evals/handwriting
"""

import json
import shutil
from pathlib import Path

import pytest
from make_labels import load_problems, main

HERE = Path(__file__).parent


@pytest.fixture
def base(tmp_path: Path) -> Path:
    shutil.copy(HERE / "problems.md", tmp_path / "problems.md")
    (tmp_path / "raw").mkdir()
    return tmp_path


def add_photos(base: Path, rows: list[str]) -> None:
    (base / "photos.csv").write_text(
        "id,writer,problem,tool\n" + "\n".join(rows) + "\n"
    )
    for row in rows:
        (base / "raw" / f"{row.split(',')[0]}.jpg").write_bytes(b"")


def read_labels(base: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (base / "labels.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_handwriting_readme_problems_table_has_all_17_problems():
    problems = load_problems(HERE / "problems.md")
    assert len(problems) == 17
    assert {p.answer_format for p in problems.values()} == {
        "expression",
        "factored",
        "equation",
    }
    assert problems["P08"].latex == r"\frac{d}{dx}\left(x^{2}\sin(x)\right)"


def test_handwriting_readme_creates_skeleton_entries(base: Path):
    add_photos(base, ["hw_001,w01,P08,pen", "hw_002,w02,P01,pencil"])
    assert main([], base) == 0
    labels = read_labels(base)
    assert [e["id"] for e in labels] == ["hw_001", "hw_002"]
    assert labels[0] == {
        "id": "hw_001",
        "image": "raw/hw_001.jpg",
        "writer": "w01",
        "problem": r"\frac{d}{dx}\left(x^{2}\sin(x)\right)",
        "lines": [],
        "unclear_lines": [],
        "labeled_by": None,
    }


def test_handwriting_readme_rerun_keeps_existing_labels(base: Path):
    add_photos(base, ["hw_001,w01,P08,pen"])
    main([], base)
    labeled = read_labels(base)[0] | {"lines": ["2x\\sin(x)"], "labeled_by": "May"}
    (base / "labels.jsonl").write_text(json.dumps(labeled))  # no trailing newline
    add_photos(base, ["hw_001,w01,P08,pen", "hw_002,w01,P05,pen"])
    assert main([], base) == 0
    labels = read_labels(base)
    assert labels[0] == labeled
    assert [e["id"] for e in labels] == ["hw_001", "hw_002"]


def test_handwriting_readme_check_writes_nothing(base: Path):
    add_photos(base, ["hw_001,w01,P08,pen"])
    assert main(["--check"], base) == 0
    assert not (base / "labels.jsonl").exists()


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("hw_1,w01,P08,pen", "id must look like hw_001"),
        ("hw_001,Somchai,P08,pen", "never a real name"),
        ("hw_001,w01,P99,pen", "not in problems.md"),
        ("hw_001,w01,P08,marker", "tool must be"),
    ],
)
def test_handwriting_readme_rejects_bad_rows(
    base: Path, capsys, row: str, message: str
):
    add_photos(base, [row])
    assert main([], base) == 1
    assert message in capsys.readouterr().err
    assert not (base / "labels.jsonl").exists()


def test_handwriting_readme_rejects_missing_image_and_duplicate(base: Path, capsys):
    add_photos(base, ["hw_001,w01,P08,pen"])
    (base / "photos.csv").write_text(
        "id,writer,problem,tool\nhw_001,w01,P08,pen\nhw_001,w01,P05,pen\nhw_002,w01,P05,pen\n"
    )
    assert main([], base) == 1
    err = capsys.readouterr().err
    assert "duplicate id" in err
    assert "no image raw/hw_002.jpg" in err
