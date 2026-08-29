"""One-time model download for MedGemma (setup step, requires network).

This is the ONLY part of PlainMed that touches the network, and it is run
explicitly by the operator during setup - never by the application.

Usage:
    pip install huggingface_hub
    hf auth login          # MedGemma is a gated model; accept its terms first
    python scripts/download_model.py

Note: MedGemma is released under Google's Health AI Developer Foundations
terms, which are separate from this application's license. Review and accept
them at https://huggingface.co/google/medgemma-1.5-4b-it before downloading.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from plainmed.config import DEFAULT_MODEL_DIR, MODEL_REPO_ID


def main() -> int:
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Install the downloader first:  pip install huggingface_hub")
        return 1

    print(f"Downloading {MODEL_REPO_ID} to {DEFAULT_MODEL_DIR} ...")
    print("This model is gated: you must have accepted its terms on Hugging Face.")
    snapshot_download(
        repo_id=MODEL_REPO_ID,
        local_dir=str(DEFAULT_MODEL_DIR),
    )
    print("Done. PlainMed will now find the model automatically (backend 'auto').")
    print("You can disconnect from the network before starting the app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
