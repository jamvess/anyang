"""Cut sheet pages into chunks for the P3b embedding spike (ai-orchestration.md §2.3.3).

Step 1 scaffold: the tests in test_chunking.py come first; the implementation follows after review.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: str
    file: str
    page_from: int
    page_to: int
    text: str
    content_hash: str


def estimate_tokens(text: str) -> int:
    raise NotImplementedError


def chunk_pages(
    file: str, pages: list[dict], min_tokens: int, max_tokens: int, max_pages: int
) -> list[Chunk]:
    raise NotImplementedError
