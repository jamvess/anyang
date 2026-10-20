"""Cut sheet pages into chunks for the P3b embedding spike (ai-orchestration.md §2.3.3).

Pages are joined in order until a chunk reaches ``min_tokens``, without going past
``max_tokens`` or spanning more than ``max_pages`` pages. A page longer than ``max_tokens`` is
split on its line breaks into parts that stay on that page. Each chunk keeps its text next to a
sha256 of the text, so its vector can be rebuilt if the embedding model changes (AI-08).
"""

import hashlib
from dataclasses import dataclass

CHARS_PER_TOKEN = 3  # rough estimate for Thai text; PoC only, no tokenizer call


@dataclass(frozen=True)
class Chunk:
    id: str
    file: str
    page_from: int
    page_to: int
    text: str
    content_hash: str


def estimate_tokens(text: str) -> int:
    return -(-len(text) // CHARS_PER_TOKEN)  # ceiling division


def _split_long_page(text: str, max_tokens: int) -> list[str]:
    """Parts of one page, each at most ``max_tokens``, cut at line breaks where possible."""
    max_chars = max_tokens * CHARS_PER_TOKEN
    parts: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        while len(line) > max_chars:  # a single line longer than a chunk: cut it hard
            if current:
                parts.append("\n".join(current))
                current = []
            parts.append(line[:max_chars])
            line = line[max_chars:]
        if current and estimate_tokens("\n".join([*current, line])) > max_tokens:
            parts.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        parts.append("\n".join(current))
    return parts


def chunk_pages(
    file: str, pages: list[dict], min_tokens: int, max_tokens: int, max_pages: int
) -> list[Chunk]:
    pieces: list[tuple[int, str]] = []
    for page in pages:
        text = page["text"]
        if not text.strip():
            continue
        if estimate_tokens(text) > max_tokens:
            pieces.extend((page["page"], part) for part in _split_long_page(text, max_tokens))
        else:
            pieces.append((page["page"], text))

    chunks: list[Chunk] = []
    buffer: list[tuple[int, str]] = []

    def flush() -> None:
        if not buffer:
            return
        text = "\n".join(part for _, part in buffer)
        first, last = buffer[0][0], buffer[-1][0]
        chunks.append(
            Chunk(
                id=f"{file}:{first}-{last}#{len(chunks)}",
                file=file,
                page_from=first,
                page_to=last,
                text=text,
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
        )
        buffer.clear()

    for page_no, text in pieces:
        if buffer:
            joined = "\n".join([*(part for _, part in buffer), text])
            pages_spanned = page_no - buffer[0][0] + 1
            full = estimate_tokens("\n".join(part for _, part in buffer)) >= min_tokens
            if full or pages_spanned > max_pages or estimate_tokens(joined) > max_tokens:
                flush()
        buffer.append((page_no, text))
    flush()
    return chunks


if __name__ == "__main__":
    import json
    from dataclasses import asdict
    from pathlib import Path

    out = Path(__file__).parent / "out"  # gitignored: contains text of the course files
    rules = {"min_tokens": 400, "max_tokens": 800, "max_pages": 2}  # ai-orchestration §2.3.3
    all_chunks: list[Chunk] = []
    for path in sorted((out / "pages").glob("sheet-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks = chunk_pages(path.stem, data["pages"], **rules)
        sizes = sorted(estimate_tokens(c.text) for c in chunks)
        pages = len(data["pages"])
        print(f"{path.stem}: {pages} pages -> {len(chunks)} chunks, tokens {sizes[0]}-{sizes[-1]}")
        all_chunks.extend(chunks)
    target = out / "chunks.json"
    target.write_text(
        json.dumps([asdict(c) for c in all_chunks], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{len(all_chunks)} chunks -> {target}")
