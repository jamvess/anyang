"""Answer-leak check, step 1: the math of a tutor reply and a string match against the answer
(specs/features/ai/answer-leak-check.md §2.1, §2.2 · AM-13).

Pure functions: no AI call, no SymPy. Step 2 (SymPy, in the worker pool) is
app/math/answer_leak.py.
"""

import re
from collections.abc import Callable, Sequence
from itertools import pairwise

from app.domain.checker import AnswerFormat
from app.domain.room import _plain  # the room's "same LaTeX" rules (room-problems-db.md §2.3)

# `$$…$$` or `$…$`; `\$` is a dollar sign, not math (tutor_reply/v2 output rules).
_MATH = re.compile(r"(?<!\\)\$\$(.+?)(?<!\\)\$\$|(?<!\\)\$(.+?)(?<!\\)\$", re.DOTALL)
_OPEN, _CLOSE = "({[", ")}]"
# §2.1 item 2: LaTeX spacing is taken out; words and wide spaces separate parts like `,`.
_LATEX_SPACE = re.compile(r"\\[,;:!]")
_SEPARATOR = re.compile(r"\\text\{[^{}]*\}|\\q?quad(?![A-Za-z])")
# §2.1 item 3: what step 2 gets besides the LaTeX spacing (spaces stay, `\cos x` is not `\cosx`).
_LEFT_RIGHT = re.compile(r"\\(?:left|right)(?![A-Za-z])")
# §2.1 item 2 (§10 item 6 D): `x = 0`, `x_1 = \pm 7` put a value in; on normalized sides.
_LONE_VARIABLE = re.compile(r"[A-Za-z](?:_[A-Za-z0-9]|_\{[A-Za-z0-9]+\})?")
_LATEX_COMMAND = re.compile(r"\\[A-Za-z]+")
_LETTER = re.compile(r"[A-Za-z]")


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


def _as_written(side: str) -> str:
    return _LEFT_RIGHT.sub("", side).strip()


def _substitution(sides: Sequence[str]) -> bool:
    """A variable on its own on the left and no letter on the right (normalized sides)."""
    if len(sides) != 2:
        return False
    left, right = sides
    return bool(_LONE_VARIABLE.fullmatch(left)) and not _LETTER.search(
        _LATEX_COMMAND.sub("", right)
    )


def _parts(reply: str, form: Callable[[str], str]) -> list[str]:
    parts: list[str] = []
    for match in _MATH.finditer(reply):
        block = _SEPARATOR.sub(",", _LATEX_SPACE.sub("", match.group(1) or match.group(2)))
        for piece in _split_top_level(block, ","):
            raw = _split_top_level(piece, "=")
            sides = [form(side) for side in raw]
            if not _substitution([_plain(side) for side in raw]):
                parts.extend(side for side in sides if side)
            parts.extend(f"{a}={b}" for a, b in pairwise(sides) if a and b)
    return list(dict.fromkeys(parts))


def math_parts(reply: str) -> list[str]:
    """§2.1: every side of `,` and `=` in every math block (not the sides of a substitution),
    and every `lhs=rhs` pair, normalized with the room's rules; in order, without repeats."""
    return _parts(reply, _plain)


def math_parts_as_written(reply: str) -> list[str]:
    r"""The same parts for step 2 (§2.1 item 3): spaces kept, `\left`/`\right` taken out."""
    return _parts(reply, _as_written)


def text_match(
    parts: Sequence[str], reference_answer: str, answer_format: AnswerFormat
) -> str | None:
    """§2.2 on parts from ``math_parts``: the part that is the answer as written, or None."""
    if answer_format == "equation":  # one root is enough (§10 item 2)
        answers = {_plain(piece) for piece in _split_top_level(reference_answer, ",")}
    else:
        answers = {_plain(reference_answer)}
    return next((part for part in parts if part in answers), None)


def leaking_part_by_text(
    reply: str, reference_answer: str, answer_format: AnswerFormat
) -> str | None:
    """§2.2: the part of the reply that is the answer as written, or None."""
    return text_match(math_parts(reply), reference_answer, answer_format)


def leaks_by_text(reply: str, reference_answer: str, answer_format: AnswerFormat) -> bool:
    return leaking_part_by_text(reply, reference_answer, answer_format) is not None
