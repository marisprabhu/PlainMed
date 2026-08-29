"""Measure what MedGemma actually costs on your GPU.

Three numbers decide whether the unit economics work, and none of them can
be guessed:

  1. seconds of GPU time per report
  2. peak GPU memory (which GPU you can rent)
  3. how many statements the validator rejects (quality at this precision)

Run this on the GPU box before choosing an instance type or setting a price.
Run it once per quantization level you are considering.

Usage:
    python scripts/benchmark_model.py                 # current settings
    PLAINMED_QUANTIZATION=4bit python scripts/benchmark_model.py
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plainmed.config import AppConfig  # noqa: E402
from plainmed.ingest import load_text  # noqa: E402
from plainmed.llm.base import ModelUnavailableError, get_backend  # noqa: E402
from plainmed.pipeline import extract  # noqa: E402
from plainmed.pipeline.validate import validate_narrative_items  # noqa: E402

WARMUP_RUNS = 2


def _peak_gpu_gb() -> float | None:
    try:
        import torch

        if not torch.cuda.is_available():
            return None
        return torch.cuda.max_memory_allocated() / (1024**3)
    except Exception:
        return None


def main() -> int:
    config = AppConfig()
    samples = sorted((ROOT / "samples").glob("*.txt"))
    if not samples:
        print("No sample reports found.")
        return 1

    print(f"backend setting : {config.backend}")
    print(f"quantization    : {config.quantization}")
    print(f"model dir       : {config.model_dir}")

    try:
        backend = get_backend(config)
    except ModelUnavailableError as exc:
        print(f"\nFAILED: {exc}")
        print("This benchmark needs a working model backend. On a GPU host:")
        print("  pip install -e '.[gpu]' && python scripts/download_model.py")
        return 1

    print(f"backend loaded  : {backend.name}\n")
    if backend.name == "deterministic":
        print("NOTE: the deterministic backend needs no GPU, so these numbers")
        print("say nothing about model cost. Set PLAINMED_BACKEND=medgemma.\n")

    docs = [extract(load_text(s.read_text(encoding="utf-8"))) for s in samples]

    for doc in docs[:WARMUP_RUNS]:
        try:
            backend.generate(doc)
        except Exception:
            pass

    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
    except Exception:
        pass

    latencies: list[float] = []
    generated = kept_total = 0

    for sample, doc in zip(samples, docs):
        started = time.perf_counter()
        try:
            items = backend.generate(doc)
        except Exception as exc:
            print(f"  {sample.name}: generation failed - {exc}")
            continue
        elapsed = (time.perf_counter() - started) * 1000
        latencies.append(elapsed)

        kept, issues = validate_narrative_items(items, doc)
        generated += len(items)
        kept_total += len(kept)
        print(
            f"  {sample.name:38} {elapsed:7.0f} ms  "
            f"{len(kept)}/{len(items)} statements kept"
        )

    if not latencies:
        print("\nNo successful generations.")
        return 1

    rejected = generated - kept_total
    rejection_rate = (rejected / generated * 100) if generated else 0.0
    peak = _peak_gpu_gb()

    print("\n--- results ---")
    print(f"reports              : {len(latencies)}")
    print(f"median latency       : {statistics.median(latencies):.0f} ms")
    print(f"mean latency         : {statistics.mean(latencies):.0f} ms")
    print(f"max latency          : {max(latencies):.0f} ms")
    print(f"peak GPU memory      : {f'{peak:.2f} GB' if peak else 'n/a (no CUDA)'}")
    print(f"statements generated : {generated}")
    print(f"rejected by validator: {rejected} ({rejection_rate:.1f}%)")

    print("\n--- what to do with these ---")
    if backend.name == "deterministic":
        print("These are CPU template timings, NOT model cost. They do not")
        print("belong on a GPU evidence slide. Re-run with a real model:")
        print("  PLAINMED_BACKEND=medgemma python scripts/benchmark_model.py")
        return 0

    median_s = statistics.median(latencies) / 1000
    print(f"One GPU sustains roughly {1 / median_s:.1f} reports/second at")
    print("concurrency 1. Re-run under realistic concurrency before sizing:")
    print("throughput, not single-request latency, sets your instance count.")
    if peak:
        print(f"Peak {peak:.1f} GB fits a {'16' if peak < 13 else '24'} GB card.")
    if rejection_rate > 20:
        print(
            f"\nWARNING: {rejection_rate:.0f}% of statements failed validation. "
            "That is high - users would see a thin summary. Try a higher "
            "precision before accepting this quantization level."
        )
    print("\nPut these numbers on the evidence slide. Do not ship estimates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
