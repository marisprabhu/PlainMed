"""Camera path: photo bytes to a parsed, confidence-annotated report.

Runs entirely in memory. The image is never written to disk, and neither
the image nor the recognized text is logged.
"""

from __future__ import annotations

import threading
from typing import Optional

from plainmed.extract import parse_report
from plainmed.ingest.text_loader import EmptyReportError, load_text
from plainmed.ocr import get_ocr_backend, prepare_image, reconstruct_lines
from plainmed.schemas import OCR_REVIEW_THRESHOLD, ReportDocument


class NoTextFoundError(ValueError):
    """OCR found no usable text in the photo."""


# Below this, the photo is too blurry or too far away to trust at all.
_MIN_USABLE_LINES = 2

# Engine construction costs ~0.5s and dominates a single call, so the
# default engine is built once and reused. Callers that manage their own
# lifecycle (the API keeps a warm one per process) still pass ``backend``.
_default_backend = None
_default_lock = threading.Lock()


def _shared_backend(name: str):
    global _default_backend
    if _default_backend is None:
        with _default_lock:
            if _default_backend is None:
                _default_backend = get_ocr_backend(name)
    return _default_backend


def load_camera_image(
    data: bytes,
    backend_name: str = "auto",
    backend=None,
    max_chars: int = 200_000,
) -> ReportDocument:
    """Decode a photo, OCR it, and parse it into a reviewable document.

    ``backend`` may be supplied to reuse a warm engine across requests -
    model loading dominates latency otherwise.
    """
    image = prepare_image(data)
    engine = backend if backend is not None else _shared_backend(backend_name)

    words = engine.recognize(image)
    lines, confidences = reconstruct_lines(words)

    if len(lines) < _MIN_USABLE_LINES:
        raise NoTextFoundError(
            "No readable text was found in this photo. Make sure the whole "
            "report is in frame, well lit, and in focus, then try again."
        )

    try:
        text = load_text("\n".join(lines), max_chars=max_chars)
    except EmptyReportError as exc:
        raise NoTextFoundError(
            "No readable text was found in this photo."
        ) from exc

    return parse_report(
        text,
        source="camera",
        line_confidence=confidences,
        review_threshold=getattr(engine, "review_threshold", OCR_REVIEW_THRESHOLD),
    )
