"""Reading uploaded PDFs: the text layer of each page, or each page as an image for vision
(specs/features/scope/ingestion.md §2.3 item 1).

Behind the `Documents` protocol so the ingestion tests can use page texts without a real PDF:
Thai PDFs need a Thai font that CI does not have (spec §8).
"""

from typing import Protocol

import pymupdf


class Documents(Protocol):
    def pages_text(self, data: bytes) -> list[str]:
        """The text layer of each page, in order. Not a PDF → ``ValueError``."""
        ...

    def page_images(self, data: bytes, dpi: int) -> list[bytes]:
        """Each page as a PNG, in order."""
        ...


class PyMuPdfDocuments:
    def _open(self, data: bytes) -> pymupdf.Document:
        try:
            return pymupdf.open(stream=data, filetype="pdf")
        except Exception as error:  # FileDataError, EmptyFileError and others
            raise ValueError("not a readable PDF") from error

    def pages_text(self, data: bytes) -> list[str]:
        with self._open(data) as doc:
            return [page.get_text() for page in doc]

    def page_images(self, data: bytes, dpi: int) -> list[bytes]:
        with self._open(data) as doc:
            return [page.get_pixmap(dpi=dpi).tobytes("png") for page in doc]
