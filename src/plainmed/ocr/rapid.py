"""RapidOCR (ONNX Runtime) backend.

Runs on CPU with no system dependencies, so the camera path works on a
laptop and in CI. Production uses the Paddle GPU backend; both feed the
same layout reconstruction.
"""

from __future__ import annotations

import io
from typing import List, Sequence

from plainmed.ocr.base import OcrUnavailableError, OcrWord


class RapidOcrBackend:
    name = "rapidocr"
    # This engine scores short numeric tokens conservatively - a correctly
    # read "41" lands near 0.53 - so a higher bar would flag every row.
    review_threshold = 0.60

    def __init__(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:  # pragma: no cover - depends on install
            raise OcrUnavailableError(
                "rapidocr-onnxruntime is not installed."
            ) from exc
        self._engine = RapidOCR()

    def recognize(self, image_bytes: bytes) -> Sequence[OcrWord]:
        import numpy as np
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        array = np.array(image.convert("RGB"))

        result, _ = self._engine(array)
        if not result:
            return []

        words: List[OcrWord] = []
        for entry in result:
            box, text, score = entry[0], entry[1], entry[2]
            xs = [float(point[0]) for point in box]
            ys = [float(point[1]) for point in box]
            words.append(
                OcrWord(
                    text=str(text),
                    box=(min(xs), min(ys), max(xs), max(ys)),
                    confidence=float(score),
                )
            )
        return words
