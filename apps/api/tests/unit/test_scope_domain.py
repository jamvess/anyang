"""Pure rules of the scope page on the database (specs/features/scope/scope-db.md §2.1 items
3, 5, 6 · AC-2, AC-3, AC-8). Table-driven, no I/O.

Interfaces these tests expect (to be built by /implement-feature), in `app/domain/scope.py`:
- `file_stem(file_name) -> str`
- `source_label(ranges) -> str` with ranges of `(file_name, page_from, page_to)` already in file
  then page order
- `question_label(file_name, q_no) -> str`
- `question_order(q_no) -> tuple` (a sort key: number first, then text)
- `scope_status(active_version_id, confirmed_at, changed_after) -> "draft" | "confirmed"`
"""

import importlib
import uuid
from datetime import UTC, datetime

import pytest


def scope():
    return importlib.import_module("app.domain.scope")


@pytest.mark.parametrize(
    ("file_name", "stem"),
    [("sheet-01.pdf", "sheet-01"), ("final 2566.v2.PDF", "final 2566.v2"), ("notes", "notes")],
)
def test_SM04_the_file_name_without_its_extension(file_name, stem):
    assert scope().file_stem(file_name) == stem


@pytest.mark.parametrize(
    ("ranges", "label"),
    [
        (
            [("sheet-01.pdf", 2, 26), ("sheet-01.pdf", 30, 30), ("sheet-03.pdf", 1, 2)],
            "sheet-01 น.2–26, sheet-01 น.30, sheet-03 น.1–2",  # noqa: RUF001
        ),
        ([("ch3.pdf", 5, 5)], "ch3 น.5"),
        ([], ""),
    ],
    ids=["several", "one_page", "user_topic"],
)
def test_SM04_source_label(ranges, label):
    # AC-2
    assert scope().source_label(ranges) == label


def test_SM04_question_label():
    # AC-3
    assert scope().question_label("final-2566.pdf", "2") == "final-2566 ข้อ 2"


def test_SM04_questions_are_ordered_as_numbers():
    # AC-3: 2 before 10, and a text q_no after the numbers
    q_nos = ["10", "2", "1b", "1"]
    assert sorted(q_nos, key=scope().question_order) == ["1", "1b", "2", "10"]


NOW = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("active", "changed_after", "status"),
    [(None, False, "draft"), (uuid.uuid4(), False, "confirmed"), (uuid.uuid4(), True, "draft")],
    ids=["never_confirmed", "confirmed", "changed_after_confirming"],
)
def test_SM09_scope_status(active, changed_after, status):
    # §2.1 item 3 · AC-8
    assert scope().scope_status(active, NOW if active else None, changed_after) == status


# --- added by the self-review of PR #137 -----------------------------------------------------


@pytest.mark.parametrize(
    ("q_nos", "ordered"),
    [
        (["ก10", "ก2", "ก1.1"], ["ก1.1", "ก2", "ก10"]),
        (["1.10", "1.2", "1"], ["1", "1.2", "1.10"]),
        (["ข1", "ก3"], ["ก3", "ข1"]),
    ],
    ids=["thai_prefix", "sub_numbers", "thai_letters"],
)
def test_SM04_question_numbers_with_a_prefix_or_parts_are_in_number_order(q_nos, ordered):
    # MTH10101 past exams number their questions ก1.1, ก2, ...
    assert sorted(q_nos, key=scope().question_order) == ordered
