"""Application configuration.

All settings come from environment variables with safe offline defaults.
Nothing here ever enables a network call: the model backend only reads local
files, and the download step is a separate, explicit setup script.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "medgemma-1.5-4b-it"

MODEL_REPO_ID = "google/medgemma-1.5-4b-it"


def enforce_offline_env() -> None:
    """Force Hugging Face libraries into offline mode for this process.

    Called before any transformers import so that even a misconfigured
    machine cannot silently reach out to a hub.
    """
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


@dataclass
class AppConfig:
    # "auto" uses MedGemma when its weights and dependencies are present,
    # otherwise the deterministic engine. "deterministic" / "medgemma" force one.
    backend: str = field(
        default_factory=lambda: os.environ.get("PLAINMED_BACKEND", "auto")
    )
    model_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("PLAINMED_MODEL_DIR", str(DEFAULT_MODEL_DIR))
        )
    )
    max_report_chars: int = field(
        default_factory=lambda: int(os.environ.get("PLAINMED_MAX_CHARS", "200000"))
    )
    max_pdf_pages: int = field(
        default_factory=lambda: int(os.environ.get("PLAINMED_MAX_PDF_PAGES", "20"))
    )
    # 768 was too small once MedGemma's reasoning trace was in play: the
    # trace consumed the budget and the answer was cut off mid-JSON. Thinking
    # is now disabled where the template allows it, but headroom is cheap
    # insurance against a truncated response.
    max_new_tokens: int = field(
        default_factory=lambda: int(os.environ.get("PLAINMED_MAX_NEW_TOKENS", "1536"))
    )
    # "auto" prefers the Paddle GPU engine and falls back to the ONNX CPU one.
    ocr_backend: str = field(
        default_factory=lambda: os.environ.get("PLAINMED_OCR_BACKEND", "auto")
    )
    # Hard ceiling on a single request's model time, so one pathological
    # report cannot occupy a GPU worker indefinitely.
    request_timeout_s: float = field(
        default_factory=lambda: float(os.environ.get("PLAINMED_REQUEST_TIMEOUT", "60"))
    )
    # Weight precision. "auto" uses the checkpoint's own dtype (~8-9 GB for
    # a 4B model). "4bit" cuts that to roughly a third, which is what makes
    # a 16 GB commodity GPU viable; quality cost must be measured, not
    # assumed. "8bit" sits between the two.
    quantization: str = field(
        default_factory=lambda: os.environ.get("PLAINMED_QUANTIZATION", "auto")
    )
