"""String types for model output fields that hold LaTeX (ai-orchestration.md §2.9 Output).

A model that writes ``"\\frac"`` in JSON without escaping the backslash gets a form feed +
``rac`` from the JSON parser, and the result still passes the schema (found in PoC P1). Only
fields typed here are repaired, so ordinary text keeps its newlines and tabs (review of PR #15):

- ``LatexStr``: the whole string is LaTeX, e.g. ``AnswerLine.latex``.
- ``MathTextStr``: text with math between ``$...$`` or ``$$...$$``; only the math is repaired.
"""

import re
from typing import Annotated

from pydantic import AfterValidator

__all__ = ["LatexStr", "MathTextStr", "repair_latex", "repair_math_spans"]

# A LaTeX backslash the model forgot to escape that JSON read as a control character:
# form feed and backspace always, tab and CR before a letter, newline before a command name.
# \ne \ni \nu \not are left out: a line starting with e^{x}, i), u = or "not" looks the same.
_LOST_BACKSLASH = re.compile(
    r"[\f\b]|[\t\r](?=[A-Za-z])"
    r"|\n(?=(?:abla|eg|eq|exists|geq|leq|mid|otin)(?![A-Za-z]))"
)
_ESCAPES = {"\f": r"\f", "\b": r"\b", "\t": r"\t", "\r": r"\r", "\n": r"\n"}
_MATH_SPAN = re.compile(r"\$\$.*?\$\$|\$[^$]*\$", re.DOTALL)


def repair_latex(text: str) -> str:
    """Put back the backslashes JSON turned into control characters."""
    return _LOST_BACKSLASH.sub(lambda match: _ESCAPES[match.group()], text)


def repair_math_spans(text: str) -> str:
    """``repair_latex`` inside ``$...$`` and ``$$...$$`` only; the text around is untouched."""
    return _MATH_SPAN.sub(lambda match: repair_latex(match.group()), text)


LatexStr = Annotated[str, AfterValidator(repair_latex)]
MathTextStr = Annotated[str, AfterValidator(repair_math_spans)]
