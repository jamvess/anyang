"""Text helpers shared by API guards.

User-visible lengths are counted in grapheme clusters (Unicode UAX #29), not code points, so Thai
vowels above and below and tone marks count with their consonant
(specs/features/exam-prep/create-exam-prep.md §2.6 · data-model.md `attachment_name`).
"""

import unicodedata

import regex

_GRAPHEME = regex.compile(r"\X")


def count_graphemes(text: str) -> int:
    """Number of user-perceived characters in ``text``."""
    return sum(1 for _ in _GRAPHEME.finditer(text))


def has_control_characters(text: str) -> bool:
    """True when ``text`` has a Unicode control character (category Cc: \n, \t, \x00, \x7f…).

    Format characters (category Cf, such as a zero-width joiner) are not control characters."""
    return any(unicodedata.category(char) == "Cc" for char in text)
