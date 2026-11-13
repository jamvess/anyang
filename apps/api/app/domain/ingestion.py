"""Pure rules of ingestion (specs/features/scope/ingestion.md §2.3 to 2.6).

How a file is read (text layer or vision), how pages become chunks, how file names are cleaned
before a prompt, how A6 sources map back to files, and how job rows become the status a user
sees. No AI, no database, no file: the service (app/services/ingestion.py) does the I/O. Every
number comes from ``IngestionConfig`` (config/ai.yaml → ingestion), as the chunk rules of PoC P3
(poc/P3/chunking.py) did with constants.
"""

import hashlib
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import regex

from app.settings import IngestionConfig

ReadMethod = Literal["text_layer", "vision"]
FileStatus = Literal["queued", "running", "done", "failed"]

_THAI = re.compile(r"[฀-๿]")
_LATIN = re.compile(r"[A-Za-z]")
_SOURCE = re.compile(r"^(.+):(\d+)-(\d+)$")
_GRAPHEME = regex.compile(r"\X")
# Characters that could start a new line or hide text in a prompt (spec §2.5 item 1).
_UNSAFE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}
_SPACES = re.compile(r"\s+")

# The stages of one file (spec §2.3), by kind: a past exam is split, not chunked.
_EXAM_STAGES = ("extract", "split_exam")
_SHEET_STAGES = ("extract", "chunk", "embed")
# Text of `detail` while a stage runs (spec §2.6 item 3).
_RUNNING_DETAIL = {
    "extract": "กำลังอ่าน",
    "split_exam": "กำลังแยกรายข้อ",
    "chunk": "กำลังเตรียมเนื้อหา",
    "embed": "กำลังเตรียมเนื้อหา",
}


# --- §2.3 item 1 · how a file is read -------------------------------------------------------------


def thai_share(text: str) -> float:
    """Thai letters ÷ (Thai + Latin letters); 0 when there are none (PoC P3 `thai_share`)."""
    thai, latin = len(_THAI.findall(text)), len(_LATIN.findall(text))
    return thai / (thai + latin) if thai + latin else 0.0


def read_method(share: float, cfg: IngestionConfig) -> ReadMethod:
    """A text layer that is mostly Thai is real text; anything else is the junk OCR layer of a
    scan, read by vision instead."""
    return "text_layer" if share >= cfg.min_thai_share else "vision"


def pages_text(pages: Sequence[tuple[int, str]]) -> str:
    """Pages labelled `[p.N]`, as every prompt of flow 2.3 expects them."""
    return "\n\n".join(f"[p.{page}]\n{text}" for page, text in pages)


# --- §2.3 item 3 · chunks (AI-08) ----------------------------------------------------------------


@dataclass(frozen=True)
class ChunkDraft:
    page_from: int
    page_to: int
    text: str
    content_hash: str  # sha256 of text, so the vector can be rebuilt (AI-08)


def estimate_tokens(text: str, cfg: IngestionConfig) -> int:
    return math.ceil(len(text) / cfg.thai_chars_per_token)


def _split_long_page(text: str, cfg: IngestionConfig) -> list[str]:
    """Parts of one page, each at most ``chunk_max_tokens``, cut at line breaks where possible."""
    max_chars = math.floor(cfg.chunk_max_tokens * cfg.thai_chars_per_token)
    parts: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        while len(line) > max_chars:  # a single line longer than a chunk: cut it hard
            if current:
                parts.append("\n".join(current))
                current = []
            parts.append(line[:max_chars])
            line = line[max_chars:]
        if current and estimate_tokens("\n".join([*current, line]), cfg) > cfg.chunk_max_tokens:
            parts.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        parts.append("\n".join(current))
    return [part for part in parts if part.strip()]


def chunk_pages(pages: Sequence[tuple[int, str]], cfg: IngestionConfig) -> list[ChunkDraft]:
    """Pages in order are joined until a chunk reaches ``chunk_min_tokens``, without going past
    ``chunk_max_tokens`` or spanning more than ``chunk_max_pages`` pages (ai-orchestration
    §2.3.3 · the rules of poc/P3/chunking.py)."""
    pieces: list[tuple[int, str]] = []
    for page, text in pages:
        if not text.strip():
            continue
        if estimate_tokens(text, cfg) > cfg.chunk_max_tokens:
            pieces.extend((page, part) for part in _split_long_page(text, cfg))
        else:
            pieces.append((page, text))

    chunks: list[ChunkDraft] = []
    buffer: list[tuple[int, str]] = []

    def flush() -> None:
        if not buffer:
            return
        text = "\n".join(part for _, part in buffer)
        chunks.append(
            ChunkDraft(
                page_from=buffer[0][0],
                page_to=buffer[-1][0],
                text=text,
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
        )
        buffer.clear()

    for page, text in pieces:
        if buffer:
            so_far = "\n".join(part for _, part in buffer)
            full = estimate_tokens(so_far, cfg) >= cfg.chunk_min_tokens
            too_many_pages = page - buffer[0][0] + 1 > cfg.chunk_max_pages
            too_long = estimate_tokens(f"{so_far}\n{text}", cfg) > cfg.chunk_max_tokens
            if full or too_many_pages or too_long:
                flush()
        buffer.append((page, text))
    flush()
    return chunks


# --- §2.5 · file names from the user -------------------------------------------------------------


def clean_file_name(name: str, max_chars: int) -> str:
    """No line breaks or hidden characters, single spaces, at most ``max_chars`` graphemes with
    the extension kept (ai-orchestration §2.3.3 · data-model.md `attachment_name`)."""
    shown = "".join(
        " " if unicodedata.category(char) in _UNSAFE_CATEGORIES else char for char in name
    )
    shown = _SPACES.sub(" ", shown).strip()
    graphemes = _GRAPHEME.findall(shown)
    if len(graphemes) <= max_chars:
        return shown
    stem, dot, extension = shown.rpartition(".")
    if not dot or not stem:
        return "".join(graphemes[:max_chars])
    tail = f".{extension}"
    keep = max(0, max_chars - len(_GRAPHEME.findall(tail)))
    return "".join(_GRAPHEME.findall(stem)[:keep]) + tail


# --- §2.4 · files in A6 and its sources (SM-04) --------------------------------------------------


def file_keys(material_ids: Sequence[str]) -> dict[str, str]:
    """Short keys f1, f2, … in the given order (oldest file first), so the model sees a short
    name it can repeat and code maps it back without guessing (spec §2.4 item 2)."""
    return {f"f{n}": material_id for n, material_id in enumerate(material_ids, start=1)}


@dataclass(frozen=True)
class SourceRange:
    material_id: str
    page_from: int
    page_to: int


def resolve_sources(
    sources: Sequence[str], keys: Mapping[str, str], page_counts: Mapping[str, int]
) -> list[SourceRange]:
    """A6 `sources` (`<key>:<start>-<end>`) as page ranges of real files. An unknown key or a
    range that starts after the last page is dropped; one that ends after it is cut there."""
    ranges: list[SourceRange] = []
    for source in sources:
        match = _SOURCE.match(source)
        if not match or match.group(1) not in keys:
            continue
        material_id = keys[match.group(1)]
        last = page_counts.get(material_id, 0)
        start, end = int(match.group(2)), int(match.group(3))
        if start < 1 or start > last:
            continue
        ranges.append(SourceRange(material_id, start, min(end, last)))
    return ranges


# --- §2.6 · what GET /ingestion shows (CM-07) -----------------------------------------------------


def file_stages(kind: str | None) -> tuple[str, ...]:
    return _EXAM_STAGES if kind == "past_exam" else _SHEET_STAGES


def file_status(rows: Sequence[tuple[str, str]], kind: str | None) -> FileStatus:
    """Status of one file from its job rows (stage, status): any failed → failed, any running →
    running, every stage of its kind done → done, otherwise queued."""
    stages = file_stages(kind)
    mine = [(stage, status) for stage, status in rows if stage in stages]
    if any(status == "failed" for _, status in mine):
        return "failed"
    if any(status == "running" for _, status in mine):
        return "running"
    done = {stage for stage, status in mine if status == "done"}
    return "done" if done >= set(stages) else "queued"


def file_detail(
    status: str, running_stage: str | None, page_count: int | None, question_count: int | None
) -> str | None:
    """Text under a file in S11: what is happening now, or what was read."""
    if status == "running" and running_stage is not None:
        return _RUNNING_DETAIL.get(running_stage)
    if status == "done" and page_count is not None:
        detail = f"{page_count} หน้า"
        return f"{detail} · {question_count} ข้อ" if question_count is not None else detail
    return None
