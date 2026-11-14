"""Pure rules of the scope page on the database (specs/features/scope/scope-db.md §2.1 · api.md
v1.6 รอตัดสินข้อ 1-2). No I/O: labels the page shows as they are, the order of past exam
questions and whether the scope is confirmed.
"""

import re
from collections.abc import Sequence
from datetime import datetime
from typing import Literal
from uuid import UUID

ScopeStatus = Literal["draft", "confirmed"]

_EXTENSION = re.compile(r"\.[A-Za-z0-9]+$")
_PARTS = re.compile(r"\d+|\D+")
# A page range as the scope page reads it: an en dash, as api.md v1.6 writes it.
_RANGE = chr(0x2013)


def file_stem(file_name: str) -> str:
    """The file name without its last extension (`sheet-01.pdf` → `sheet-01`)."""
    return _EXTENSION.sub("", file_name)


def source_label(ranges: Sequence[tuple[str, int, int]]) -> str:
    """§2.1 item 5: `(file_name, page_from, page_to)` already in file then page order →
    `{stem} น.{from}<en dash>{to}` (one page `น.{n}`), joined by `, `; no range → `""`."""
    parts = []
    for file_name, page_from, page_to in ranges:
        pages = f"{page_from}" if page_from == page_to else f"{page_from}{_RANGE}{page_to}"
        parts.append(f"{file_stem(file_name)} น.{pages}")
    return ", ".join(parts)


def question_label(file_name: str, q_no: str) -> str:
    """§2.1 item 6: `{stem} ข้อ {q_no}`."""
    return f"{file_stem(file_name)} ข้อ {q_no}"


def question_order(q_no: str) -> tuple[tuple[int, int, str], ...]:
    """A natural sort key for `q_no`: runs of digits compare as numbers, the rest as text, so
    `2` < `10`, `ก2` < `ก10`, `1.2` < `1.10` and `1` < `1b` (self-review PR #137)."""
    return tuple(
        (0, int(part), "") if part.isdigit() else (1, 0, part) for part in _PARTS.findall(q_no)
    )


def scope_status(
    active_version_id: UUID | None, confirmed_at: datetime | None, changed_after: bool
) -> ScopeStatus:
    """§2.1 item 3: confirmed while the prep points at a confirmed version and nothing in
    `scope_changes` came after it; otherwise a draft."""
    if active_version_id is None or confirmed_at is None or changed_after:
        return "draft"
    return "confirmed"
