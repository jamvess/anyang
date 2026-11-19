"""The real PDF reader behind `Documents` (specs/features/scope/ingestion.md §2.3 item 1, §8).

An English PDF made here with PyMuPDF: CI has no Thai font, so Thai text is checked on the
real course files in step 4 of the worklog (MTH10101).

Interfaces these tests expect (to be built by /implement-feature):
- `app.services.documents.PyMuPdfDocuments` with `pages_text(data) -> list[str]` and
  `page_images(data, dpi) -> list[bytes]` (PNG); a file that is not a PDF raises `ValueError`
"""

import pymupdf
import pytest

from app.services.documents import PyMuPdfDocuments


def pdf(*texts: str) -> bytes:
    doc = pymupdf.open()
    for text in texts:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    return doc.tobytes()


def test_SM01_pages_text_reads_each_page_in_order():
    pages = PyMuPdfDocuments().pages_text(pdf("first page", "second page"))

    assert len(pages) == 2
    assert "first page" in pages[0]
    assert "second page" in pages[1]


def test_SM01_page_images_are_one_png_per_page():
    images = PyMuPdfDocuments().page_images(pdf("a", "b", "c"), dpi=72)

    assert len(images) == 3
    assert all(image.startswith(b"\x89PNG") for image in images)


def test_SM01_a_file_that_is_not_a_pdf_raises_value_error():
    with pytest.raises(ValueError):
        PyMuPdfDocuments().pages_text(b"not a pdf at all")
