"""Answer-leak check, step 1: the math of a tutor reply and a string match against the answer
(specs/features/ai/answer-leak-check.md §2.1, §2.2 · AM-13).

Pure functions: no AI call, no SymPy. Step 2 (SymPy, in the worker pool) is
app/math/answer_leak.py.
"""

import re
from itertools import pairwise

from app.domain.checker import AnswerFormat
from app.domain.room import _plain  # the room's "same LaTeX" rules (room-problems-db.md §2.3)

# `$$…$$` or `$…$`; `\$` is a dollar sign, not math (tutor_reply/v2 output rules).
_MATH = re.compile(r"(?<!\\)\$\$(.+?)(?<!\\)\$\$|(?<!\\)\$(.+?)(?<!\\)\$", re.DOTALL)
_OPEN, _CLOSE = "({[", ")}]"


def _split_top_level(text: str, separator: str) -> list[str]:
    """Split on ``separator`` where it is not inside (), {} or [] (as sympy_service does)."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        elif ch == separator and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def math_parts(reply: str) -> list[str]:
    """§2.1: every side of `,` and `=` in every math block, and every `lhs=rhs` pair, normalized
    with the room's rules; in order, without repeats."""
    parts: list[str] = []
    for match in _MATH.finditer(reply):
        block = match.group(1) or match.group(2)
        for piece in _split_top_level(block, ","):
            sides = [_plain(side) for side in _split_top_level(piece, "=")]
            parts.extend(side for side in sides if side)
            parts.extend(f"{a}={b}" for a, b in pairwise(sides) if a and b)
    return list(dict.fromkeys(parts))


def leaking_part_by_text(
    reply: str, reference_answer: str, answer_format: AnswerFormat
) -> str | None:
    """§2.2: the part of the reply that is the answer as written, or None."""
    if answer_format == "equation":  # one root is enough (§10 item 2)
        answers = {_plain(piece) for piece in _split_top_level(reference_answer, ",")}
    else:
        answers = {_plain(reference_answer)}
    return next((part for part in math_parts(reply) if part in answers), None)


def leaks_by_text(reply: str, reference_answer: str, answer_format: AnswerFormat) -> bool:
    return leaking_part_by_text(reply, reference_answer, answer_format) is not None
