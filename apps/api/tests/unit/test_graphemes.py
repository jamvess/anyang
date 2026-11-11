"""The shared grapheme counter (specs/features/exam-prep/create-exam-prep.md §2.6).

`app.text.count_graphemes` counts user-perceived characters with `regex` `\\X` (Unicode UAX #29),
so Thai vowels above/below and tone marks join their consonant. The exam prep title cap uses it
now; the attachment_name guard reuses it later.
"""

import pytest

from app.text import count_graphemes


@pytest.mark.parametrize(
    ("text", "graphemes"),
    [
        ("", 0),
        ("Calculus 1", 10),
        ("กี่", 1),  # ก + sara ii + mai ek: 3 code points, 1 grapheme
        ("กี่" * 5, 5),
        ("แคลคูลัส", 6),  # แ ค ล คู ลั ส
        ("น้ำ", 1),  # น + mai tho + sara am (a SpacingMark, so it extends the cluster)
        ("👩‍💻", 1),  # emoji ZWJ sequence
        ("แคล‍คูลัส", 6),  # a zero-width joiner extends the previous cluster
        ("é", 1),  # e + combining acute
    ],
)
def test_CM01_count_graphemes(text: str, graphemes: int) -> None:
    assert count_graphemes(text) == graphemes


def test_CM01_thai_with_marks_has_more_code_points_than_graphemes() -> None:
    text = "กี่" * 7

    assert len(text) == 21
    assert count_graphemes(text) == 7
