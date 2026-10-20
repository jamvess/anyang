"""P3b embedding spike: embed sheet chunks and questions, then measure recall@4.

Step 4 scaffold: the tests in test_embed.py come first; the implementation follows after review.
"""

from dataclasses import dataclass

from chunking import Chunk


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    pages: list[tuple[str, int]]


def parse_questions(markdown: str) -> list[Question]:
    raise NotImplementedError


def rank(query: list[float], chunk_vectors: list[list[float]]) -> list[int]:
    raise NotImplementedError


def hit_at_k(question: Question, ranking: list[int], chunks: list[Chunk], k: int) -> bool:
    raise NotImplementedError


def recall_at_k(
    questions: list[Question], rankings: list[list[int]], chunks: list[Chunk], k: int
) -> float:
    raise NotImplementedError
