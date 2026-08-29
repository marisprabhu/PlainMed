"""Normalization for pasted report text.

The output of this module is the canonical text every source span offsets
into, so normalization happens exactly once, here.
"""

from __future__ import annotations

import re


class EmptyReportError(ValueError):
    """The input contained no usable text."""


class ReportTooLargeError(ValueError):
    """The input exceeded the configured size limit."""


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def load_text(text: str, max_chars: int = 200_000) -> str:
    """Normalize pasted text: consistent newlines, no control characters.

    Raises EmptyReportError / ReportTooLargeError instead of silently
    truncating or accepting garbage.
    """
    if text is None:
        raise EmptyReportError("No report text was provided.")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.lstrip("﻿")
    normalized = _CONTROL_CHARS.sub(" ", normalized)
    if len(normalized) > max_chars:
        raise ReportTooLargeError(
            f"The report is longer than the supported limit of {max_chars} characters."
        )
    if not normalized.strip():
        raise EmptyReportError("The report text is empty.")
    return normalized
