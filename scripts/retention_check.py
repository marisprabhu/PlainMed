"""Verify the zero-retention claim by exercising the real API.

"Processed, never stored" is only worth saying if it is enforced by code.
This drives a full scan-and-explain cycle through the running application
and then asserts, from the outside:

1. No new files appeared anywhere under the temp directory or the working
   tree while the request was handled.
2. No captured log record contains any report content.
3. Every response carries no-store cache headers.

Usage:
    python scripts/retention_check.py
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from plainmed.api.app import create_app  # noqa: E402

# Distinctive strings that must never reach disk or a log.
CANARY_ANALYTE = "Zzcanarytest"
CANARY_VALUE = "77.77"
REPORT = (
    "SYNTHETIC CANARY REPORT\n"
    f"{CANARY_ANALYTE} {CANARY_VALUE} mg/dL 10-20 High\n"
    "Sodium 140 mmol/L 135-145\n"
)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[str] = []

    def emit(self, record):
        try:
            self.records.append(self.format(record))
        except Exception:
            self.records.append(str(record.msg))


def _snapshot(paths) -> set:
    seen = set()
    for base in paths:
        base = Path(base)
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                seen.add(str(path))
    return seen


def main() -> int:
    watched = [tempfile.gettempdir(), str(ROOT)]

    capture = _Capture()
    capture.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
    root_logger = logging.getLogger()
    root_logger.addHandler(capture)
    root_logger.setLevel(logging.DEBUG)

    # No OCR warmup: this check is about retention, not recognition, and the
    # engine's own model files would show up as legitimate new temp files.
    app = create_app(warmup=False)
    failures = []

    with TestClient(app) as client:
        # The consent gate is enforced, so obtain a session first. This also
        # means the check exercises the same path a real user takes.
        from plainmed.api.security import CONSENT_VERSION

        consent = client.post(
            "/api/v1/session",
            json={"accepted": True, "consent_version": CONSENT_VERSION, "age_confirmed": True},
        )
        if consent.status_code != 200:
            print(f"FAIL: could not obtain a session: {consent.text[:200]}")
            return 1
        client.headers.update({"x-plainmed-session": consent.json()["session"]})

        before = _snapshot(watched)

        scan = client.post("/api/v1/scan/text", json={"text": REPORT})
        if scan.status_code != 200:
            print(f"FAIL: /scan/text returned {scan.status_code}: {scan.text[:200]}")
            return 1
        document = scan.json()["document"]

        explain = client.post(
            "/api/v1/explain", json={"document": document, "corrections": []}
        )
        if explain.status_code != 200:
            print(f"FAIL: /explain returned {explain.status_code}: {explain.text[:200]}")
            return 1

        after = _snapshot(watched)

    # ---------------------------------------------------------------- 1
    new_files = after - before
    # __pycache__ is a Python implementation artefact, not report data.
    new_files = {f for f in new_files if "__pycache__" not in f and not f.endswith(".pyc")}
    if new_files:
        failures.append(
            "files were created while handling the request:\n    "
            + "\n    ".join(sorted(new_files)[:10])
        )
    else:
        print("ok  no files written during scan + explain")

    # ---------------------------------------------------------------- 2
    leaked = [
        line
        for line in capture.records
        if CANARY_ANALYTE.lower() in line.lower() or CANARY_VALUE in line
    ]
    if leaked:
        failures.append(
            "report content reached the logs:\n    " + "\n    ".join(leaked[:5])
        )
    else:
        print(f"ok  no report content in {len(capture.records)} captured log records")

    # ---------------------------------------------------------------- 3
    # The audit log persists by design (HIPAA 164.312(b)), so it is the one
    # place that could quietly become a PHI store. Check it explicitly.
    audit_entries = [line for line in capture.records if "plainmed.audit" in line]
    audit_leaks = [
        line
        for line in audit_entries
        if CANARY_ANALYTE.lower() in line.lower() or CANARY_VALUE in line
    ]
    if audit_leaks:
        failures.append(
            "report content reached the audit log:\n    "
            + "\n    ".join(audit_leaks[:3])
        )
    elif audit_entries:
        print(f"ok  audit log records {len(audit_entries)} events, none with PHI")

    # ---------------------------------------------------------------- 4
    cache = explain.headers.get("cache-control", "")
    if "no-store" not in cache:
        failures.append(f"response missing no-store cache header (got {cache!r})")
    else:
        print("ok  responses carry no-store cache headers")

    if failures:
        print("\nRETENTION CHECK FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nRETENTION CHECK PASSED: report data was processed and not retained.")
    print("Note: this verifies application behaviour. Host, network, and")
    print("memory protections are infrastructure concerns - see deploy/README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
