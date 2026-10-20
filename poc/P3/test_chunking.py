"""Tests for chunking.py: cut sheet pages into chunks for the P3b embedding spike.

Rules from ai-orchestration.md §2.3.3: about 400-800 tokens per chunk, never across more than
2 pages, keep page numbers (SM-04) and keep the text next to its hash so vectors can be rebuilt
(AI-08). Tokens are estimated from characters (PoC only, no tokenizer call).

    cd apps/api && uv run pytest ../../poc/P3 -q
"""

from chunking import Chunk, chunk_pages, estimate_tokens

RULES = {"min_tokens": 400, "max_tokens": 800, "max_pages": 2}


def page(no: int, tokens: int) -> dict:
    """A page whose text is estimated at exactly ``tokens`` tokens."""
    return {"page": no, "text": "ก" * (tokens * 3)}


def spans(chunks: list[Chunk]) -> list[tuple[int, int]]:
    return [(c.page_from, c.page_to) for c in chunks]


def test_P3_estimate_tokens_is_about_three_characters_each():
    assert estimate_tokens("ก" * 300) == 100
    assert estimate_tokens("") == 0


def test_P3_small_pages_are_joined_until_min_tokens():
    chunks = chunk_pages("sheet-02", [page(1, 250), page(2, 250), page(3, 250)], **RULES)

    assert spans(chunks) == [(1, 2), (3, 3)]


def test_P3_a_chunk_never_spans_more_than_two_pages():
    chunks = chunk_pages("sheet-02", [page(n, 100) for n in range(1, 6)], **RULES)

    assert all(c.page_to - c.page_from + 1 <= 2 for c in chunks)
    assert spans(chunks) == [(1, 2), (3, 4), (5, 5)]


def test_P3_a_chunk_does_not_grow_past_max_tokens():
    chunks = chunk_pages("sheet-02", [page(1, 500), page(2, 500)], **RULES)

    assert spans(chunks) == [(1, 1), (2, 2)]


def test_P3_a_page_longer_than_max_tokens_is_split_on_its_own_page():
    long_page = {"page": 7, "text": "\n".join(["ก" * 300] * 10)}  # 10 lines x 100 tokens

    chunks = chunk_pages("sheet-01", [long_page], **RULES)

    assert spans(chunks) == [(7, 7), (7, 7)]
    assert all(estimate_tokens(c.text) <= 800 for c in chunks)
    assert "".join(c.text.replace("\n", "") for c in chunks) == long_page["text"].replace("\n", "")


def test_P3_empty_pages_are_skipped():
    chunks = chunk_pages("sheet-03", [page(1, 500), {"page": 2, "text": "  \n"}], **RULES)

    assert spans(chunks) == [(1, 1)]


def test_P3_chunk_keeps_file_text_and_hash():
    chunks = chunk_pages("sheet-04", [page(1, 450)], **RULES)

    chunk = chunks[0]
    assert chunk.file == "sheet-04"
    assert chunk.text == page(1, 450)["text"]
    assert len(chunk.content_hash) == 64  # sha256 of the text, so the vector can be rebuilt
    assert chunk.id == "sheet-04:1-1#0"
