"""Warm, process-wide engines.

OCR and LLM model loading dominates request latency, so both are loaded
once and reused. Loading is lazy and failure-tolerant: a missing GPU engine
degrades to the CPU/deterministic path rather than taking the service down.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from plainmed.config import AppConfig
from plainmed.glossary import Glossary, load_glossary
from plainmed.llm.base import ModelUnavailableError, get_backend
from plainmed.llm.deterministic import DeterministicBackend
from plainmed.ocr.base import OcrUnavailableError, get_ocr_backend

log = logging.getLogger("plainmed.runtime")


class Runtime:
    """Holds the warm engines for the lifetime of the process."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self._lock = threading.Lock()
        self._glossary: Optional[Glossary] = None
        self._ocr = None
        self._ocr_name = "not-loaded"
        self._llm = None
        self._llm_name = "not-loaded"

    @property
    def glossary(self) -> Glossary:
        if self._glossary is None:
            with self._lock:
                if self._glossary is None:
                    self._glossary = load_glossary()
        return self._glossary

    @property
    def ocr(self):
        if self._ocr is None:
            with self._lock:
                if self._ocr is None:
                    self._ocr = get_ocr_backend(
                        self.config.ocr_backend
                    )
                    self._ocr_name = self._ocr.name
                    log.info("OCR backend ready: %s", self._ocr_name)
        return self._ocr

    @property
    def llm(self):
        if self._llm is None:
            with self._lock:
                if self._llm is None:
                    try:
                        self._llm = get_backend(self.config)
                    except ModelUnavailableError as exc:
                        log.warning(
                            "Model backend unavailable, using deterministic: %s", exc
                        )
                        self._llm = DeterministicBackend()
                    self._llm_name = self._llm.name
                    log.info("Explanation backend ready: %s", self._llm_name)
        return self._llm

    @property
    def ocr_backend_name(self) -> str:
        return self._ocr_name

    @property
    def llm_backend_name(self) -> str:
        return self._llm_name

    def warmup(self) -> None:
        """Load everything at startup so the first user request is not slow."""
        _ = self.glossary
        try:
            _ = self.ocr
        except OcrUnavailableError as exc:
            log.warning("No OCR backend available at startup: %s", exc)
        _ = self.llm
