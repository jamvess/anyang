"""Answer-leak check, step 1: string match on the math of a tutor reply
(specs/features/ai/answer-leak-check.md §2.1, §2.2 · AC-1 to AC-4 · AM-13).

No threshold is involved; the examples are the demo's problems.

Interface this file expects (built by /implement-feature), in app/domain/answer_leak.py:
- `leaks_by_text(reply, reference_answer, answer_format) -> bool`
"""

import pytest

from app.domain.answer_leak import leaks_by_text

FACTOR = "(x-7)(x+7)"
ROOTS = "x=7, x=-7"


# --- AC-1 · factored, written another way ---------------------------------------------------------


@pytest.mark.parametrize(
    "reply",
    [
        "คำตอบคือ $(x-7)(x+7)$ นะ",
        "คำตอบคือ $( x - 7 )( x + 7 )$",
        r"คำตอบคือ $\left(x-7\right)\left(x+7\right)$",
        "ได้ $$x^{2}-49=(x-7)(x+7)$$",
    ],
    ids=["same", "spaces", "left-right", "display-right-side"],
)
def test_AM13_a_factored_answer_in_the_reply_is_a_leak(reply):
    assert leaks_by_text(reply, FACTOR, "factored") is True


# --- AC-2 · expression ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("reply", "reference"),
    [
        (r"อนุพันธ์ $\frac{d}{dx}x^3 = 3x^2$", "3x^2"),
        (r"ได้ $\dfrac{1}{2}$", r"\frac{1}{2}"),
        ("ได้ $3x^{2}$", "3x^2"),
    ],
    ids=["right-of-equals", "dfrac", "braces"],
)
def test_AM13_an_expression_answer_in_the_reply_is_a_leak(reply, reference):
    assert leaks_by_text(reply, reference, "expression") is True


# --- AC-3 · equation, one root is enough ---------------------------------------------------------


@pytest.mark.parametrize(
    "reply",
    ["รากหนึ่งคือ $x = 7$", "ได้ $x=-7, x=7$", "ตอบ $x=7$ และ $x=-7$"],
    ids=["half", "both-reordered", "two-blocks"],
)
def test_AM13_a_root_of_the_equation_in_the_reply_is_a_leak(reply):
    assert leaks_by_text(reply, ROOTS, "equation") is True


# --- AC-4 · not a leak ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("reply", "reference", "answer_format"),
    [
        ("ลองแยกตัวประกอบดูก่อนนะ", FACTOR, "factored"),
        ("ลองแยกตัวประกอบ $x^2-49$ ดูนะ", FACTOR, "factored"),
        ("ใช้สูตร $$a^2-b^2=(a-b)(a+b)$$", FACTOR, "factored"),
        (r"ราคา \$7 ไม่ใช่คำตอบ", "7", "expression"),
        ("ได้ $17$ ไม่ใช่ $27$", "7", "expression"),
        ("ลองแก้ $x^2 = 49$ ดู", ROOTS, "equation"),
    ],
    ids=["no-math", "the-problem", "general-formula", "escaped-dollar", "inside-a-number", "eq"],
)
def test_AM13_math_that_is_not_the_answer_is_not_a_leak(reply, reference, answer_format):
    assert leaks_by_text(reply, reference, answer_format) is False
