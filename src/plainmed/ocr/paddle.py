"""PaddleOCR GPU backend for production serving.

Chosen over the ONNX dev backend for cloud because PP-Structure handles
column layout on lab reports noticeably better, and because it runs on the
same GPU as MedGemma so a scan needs one accelerator, not two.

Not installed by default: the ``gpu`` extra pulls it in. Raises
OcrUnavailableError when absent so ``get_ocr_backend("auto")`` falls back.
"""

from __future__ import annotations

import io
import os
from typing import List, Sequence

from plainmed.ocr.base import OcrUnavailableError, OcrWord


class PaddleOcrBackend:
    name = "paddleocr"
    # PP-OCR reports higher, better-separated confidences than the ONNX dev
    # engine, so the bar sits higher. Re-check this against real photos
    # before launch rather than trusting the default.
    review_threshold = 0.80

    def __init__(self):
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise OcrUnavailableError(
                "paddleocr is not installed (pip install .[gpu])."
            ) from exc

        use_gpu = os.environ.get("PLAINMED_OCR_GPU", "1") != "0"
        try:
            self._engine = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                use_gpu=use_gpu,
                show_log=False,
            )
        except Exception as exc:  # driver missing, OOM, model files absent
            raise OcrUnavailableError(f"Could not initialise PaddleOCR: {exc}") from exc

    def recognize(self, image_bytes: bytes) -> Sequence[OcrWord]:
        import numpy as np
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        array = np.array(image.convert("RGB"))

        result = self._engine.ocr(array, cls=True)
        if not result or not result[0]:
            return []

        words: List[OcrWord] = []
        for box, (text, score) in result[0]:
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
