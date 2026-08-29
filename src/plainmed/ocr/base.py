"""OCR backend abstraction.

Mirrors the LLM backend pattern: one interface, a dev backend that runs
anywhere, and a production GPU backend. Swapping engines must never change
what the rest of the pipeline sees.

Every backend returns positioned words with confidences. Turning those into
report lines is the job of ``layout.reconstruct_lines`` - shared by all
backends so table handling is identical regardless of engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol, Sequence, Tuple


class OcrUnavailableError(RuntimeError):
    """The requested OCR backend cannot run in this environment."""


@dataclass(frozen=True)
class OcrWord:
    """One recognized text box.

    ``box`` is (x0, y0, x1, y1) in pixels of the prepared image.
    ``confidence`` is 0.0-1.0 as reported by the engine.
    """

    text: str
    box: Tuple[float, float, float, float]
    confidence: float

    @property
    def y_center(self) -> float:
        return (self.box[1] + self.box[3]) / 2.0

    @property
    def height(self) -> float:
        return self.box[3] - self.box[1]


@dataclass
class OcrResult:
    lines: List[str] = field(default_factory=list)
    # Parallel to ``lines``: the lowest word confidence on each line.
    line_confidence: List[float] = field(default_factory=list)
    backend: str = "unknown"

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class OcrBackend(Protocol):
    name: str
    # Below this, a recognized value is sent for human confirmation.
    # Engine-specific: confidence scales are not comparable across engines,
    # so each backend calibrates its own rather than sharing a constant.
    review_threshold: float

    def recognize(self, image_bytes: bytes) -> Sequence[OcrWord]: ...


def get_ocr_backend(name: str = "auto") -> "OcrBackend":
    """Select an OCR backend without ever reaching the network."""
    if name in ("paddle", "auto"):
        try:
            from plainmed.ocr.paddle import PaddleOcrBackend

            return PaddleOcrBackend()
        except OcrUnavailableError:
            if name == "paddle":
                raise

    from plainmed.ocr.rapid import RapidOcrBackend

    return RapidOcrBackend()
