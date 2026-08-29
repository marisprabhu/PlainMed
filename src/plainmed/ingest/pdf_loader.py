"""Text extraction from text-based PDFs.

Scanned (image-only) PDFs are rejected explicitly rather than producing an
empty report, per the v1 scope.
"""

from __future__ import annotations

import io
from typing import Union

from pypdf import PdfReader

from plainmed.ingest.text_loader import load_text


class ScannedPdfError(ValueError):
    """The PDF has no extractable text layer (likely a scan/image)."""


class EncryptedPdfError(ValueError):
    """The PDF is password-protected."""


class PdfTooLargeError(ValueError):
    """The PDF exceeds the supported page count."""


# A real text-based lab report yields far more than this; below it, the file
# is treated as scanned/image-only.
_MIN_EXTRACTED_CHARS = 40


def load_pdf(
    data: Union[bytes, io.IOBase],
    max_pages: int = 20,
    max_chars: int = 200_000,
) -> str:
    """Extract and normalize text from a text-based PDF."""
    if isinstance(data, bytes):
        data = io.BytesIO(data)
    reader = PdfReader(data)
    if reader.is_encrypted:
        raise EncryptedPdfError(
            "This PDF is password-protected. Remove the password and try again."
        )
    if len(reader.pages) > max_pages:
        raise PdfTooLargeError(
            f"This PDF has {len(reader.pages)} pages; up to {max_pages} are supported."
        )
    page_texts = []
    for page in reader.pages:
        page_texts.append(page.extract_text() or "")
    text = "\n".join(page_texts)
    if len(text.strip()) < _MIN_EXTRACTED_CHARS:
        raise ScannedPdfError(
            "No readable text was found in this PDF. Scanned or image-based "
            "PDFs are not supported in this version; paste the report text instead."
        )
    return load_text(text, max_chars=max_chars)
