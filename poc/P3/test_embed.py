"""Tests for embed.py: score retrieval for the P3b embedding spike (specs/poc/README.md P3).

recall@4 = share of questions where at least one of the 4 best chunks covers a page the
question writer marked as holding the answer.

    cd apps/api && uv run pytest ../../poc/P3 -q
"""

import pytest
from chunking import Chunk
from embed import Question, hit_at_k, parse_questions, rank, recall_at_k

TABLE = """\
## ตัวอย่างรูปแบบ (สมมติ ไม่ต้องใช้)

| # | คำถาม | หน้าที่มีคำตอบ | หัวข้อ | แบบ |
|---|---|---|---|---|
| ตัวอย่าง | ถ้าเจอ 0/0 ต้องทำยังไงต่อ | sheet-02:9, sheet-02:10 | t24 | วิธีทำ |

## คำถาม (เติมให้ครบ 20 แถว)

| # | คำถาม | หน้าที่มีคำตอบ | หัวข้อ | แบบ |
|---|---|---|---|---|
| 1 | chain rule ใช้ตอนไหน | sheet-01:41 | t07 | ความหมาย |
| 2 | implicit diff ทำยังไง | sheet-01:84, sheet-01:85-86 | t14 | วิธีทำ |
| 3 | | | | |

## หัวข้อของวิชา

| id | หัวข้อ | หน้าโดยประมาณ |
|---|---|---|
| t01 | ลิมิต | sheet-01:2-6 |
"""


def chunk(file: str, first: int, last: int) -> Chunk:
    return Chunk(f"{file}:{first}-{last}#0", file, first, last, "text", "hash")


def test_P3_questions_are_read_from_the_filled_rows_only():
    questions = parse_questions(TABLE)

    assert questions == [
        Question(id="1", text="chain rule ใช้ตอนไหน", pages=[("sheet-01", 41)]),
        Question(
            id="2",
            text="implicit diff ทำยังไง",
            pages=[("sheet-01", 84), ("sheet-01", 85), ("sheet-01", 86)],
        ),
    ]


def test_P3_rank_orders_chunks_by_cosine_similarity():
    chunk_vectors = [[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]]

    assert rank([0.0, 2.0], chunk_vectors) == [1, 2, 0]


def test_P3_hit_when_a_top_k_chunk_covers_an_answer_page():
    chunks = [chunk("sheet-01", 40, 41), chunk("sheet-01", 1, 2), chunk("sheet-02", 41, 41)]
    question = Question(id="1", text="q", pages=[("sheet-01", 41)])

    assert hit_at_k(question, [1, 0, 2], chunks, k=2)
    assert not hit_at_k(question, [1, 2, 0], chunks, k=2)  # same page number, other file


def test_P3_recall_at_k_is_the_share_of_questions_hit():
    chunks = [chunk("sheet-01", 41, 41), chunk("sheet-01", 84, 85)]
    questions = [
        Question(id="1", text="q1", pages=[("sheet-01", 41)]),
        Question(id="2", text="q2", pages=[("sheet-01", 90)]),
    ]

    assert recall_at_k(questions, [[0, 1], [0, 1]], chunks, k=2) == pytest.approx(0.5)
