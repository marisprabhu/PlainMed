"""Verify that the full pipeline works with networking blocked.

Blocks all socket creation in this process, then runs every synthetic sample
through extraction, explanation, validation, and question generation. Any
attempted network call raises immediately and fails the check.

Usage:
    python scripts/offline_check.py
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plainmed.config import AppConfig, enforce_offline_env
from plainmed.ingest import load_text
from plainmed.pipeline import analyze, extract


class _NetworkBlocked(RuntimeError):
    pass


def _block_network() -> None:
    def _blocked(*args, **kwargs):
        raise _NetworkBlocked("A network call was attempted during offline check.")

    socket.socket = _blocked  # type: ignore[misc,assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.getaddrinfo = _blocked  # type: ignore[assignment]


def main() -> int:
    enforce_offline_env()
    _block_network()
    config = AppConfig()

    samples = sorted((ROOT / "samples").glob("*.txt"))
    if not samples:
        print("FAIL: no sample reports found.")
        return 1

    failures = 0
    for sample in samples:
        try:
            text = load_text(sample.read_text(encoding="utf-8"))
            doc = extract(text)
            result = analyze(doc, config=config)
            errors = [i for i in result.issues if i.severity == "error"]
            status = "ok" if doc.values and not errors else "PROBLEM"
            if status != "ok":
                failures += 1
            print(
                f"{status:8} {sample.name}: {len(doc.values)} values, "
                f"{len(result.cards)} cards, "
                f"{len(result.narrative.items) if result.narrative else 0} summary items "
                f"(backend {result.narrative.backend if result.narrative else 'none'}), "
                f"{len(errors)} validation errors"
            )
        except _NetworkBlocked:
            print(f"FAIL     {sample.name}: attempted a network call")
            failures += 1
        except Exception as exc:
            print(f"FAIL     {sample.name}: {exc}")
            failures += 1

    if failures:
        print(f"\nOFFLINE CHECK FAILED ({failures} problem(s)).")
        return 1
    print("\nOFFLINE CHECK PASSED: full pipeline ran with networking blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
