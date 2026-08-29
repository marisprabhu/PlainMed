"""Verify that no identifier can reach the model tier.

This is the check the compliance pack points at when it claims the GPU tier
does not process PHI. It builds reports stuffed with every identifier
category a lab report realistically carries, runs the real prompt builder,
and fails if any of them appears in what would be sent to the model.

Run it in CI. If it ever fails, the trust boundary in legal/data-flow.md is
no longer accurate and the cheap-GPU deployment stops being lawful.

Usage:
    python scripts/deident_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plainmed.llm.medgemma import _build_prompt  # noqa: E402
from plainmed.pipeline import extract  # noqa: E402

# (label, report line, strings that must not survive)
CASES = [
    ("name", "Patient Name: Jane Q Doe", ["Jane", "Doe"]),
    ("dob", "DOB: 04/11/1978", ["04/11/1978", "1978"]),
    ("mrn", "MRN: 88213-4", ["88213"]),
    ("ssn", "SSN: 123-45-6789", ["123-45-6789"]),
    ("address", "Address: 123 Elm Street, Springfield IL 62704", ["Elm Street", "62704"]),
    ("phone", "Phone: (555) 213-9987", ["555", "213-9987"]),
    ("email", "Email: jane.doe@example.com", ["jane.doe@example.com"]),
    ("clinician", "Ordering physician: Dr A Smith", ["Smith"]),
    ("accession", "Accession: ACC-2026-114", ["ACC-2026-114"]),
    ("collected", "Collected: 12/03/2026 09:14", ["12/03/2026"]),
    ("facility", "CityLab Diagnostics, 9 Harbour Road", ["Harbour Road"]),
    ("insurance", "Policy number: BCBS-778120", ["BCBS-778120"]),
    ("url", "Results portal: https://portal.citylab.example/p/9912", ["portal.citylab"]),
    ("free_text", "Comment: call Mrs Henderson about these results", ["Henderson"]),
]

CLINICAL = [
    "Glucose 108 mg/dL 70-99 H",
    "Sodium 140 mmol/L 135-145",
    "Hemoglobin 13.5 g/dL 13.0-17.0",
]


def main() -> int:
    report = "\n".join([line for _, line, _ in CASES] + CLINICAL)
    prompt = _build_prompt(extract(report))

    # The block actually sent to the model.
    start = prompt.find("=== REPORT START")
    end = prompt.find("=== REPORT END")
    forwarded = prompt[start:end]

    failures = []
    for label, _, needles in CASES:
        leaked = [n for n in needles if n.lower() in forwarded.lower()]
        if leaked:
            failures.append(f"{label}: {', '.join(repr(n) for n in leaked)}")
        else:
            print(f"ok       {label} withheld")

    # De-identification is worthless if it also removes the clinical content.
    missing = [c.split()[0] for c in CLINICAL if c.split()[0] not in forwarded]
    if missing:
        failures.append(f"clinical content lost: {', '.join(missing)}")
    else:
        print(f"ok       {len(CLINICAL)} clinical values preserved")

    if failures:
        print("\nDE-IDENTIFICATION CHECK FAILED:")
        for f in failures:
            print(f"  - {f}")
        print("\nThe model tier would receive identifiers. The trust boundary in")
        print("legal/data-flow.md is no longer accurate. Do not deploy.")
        return 1

    print("\nDE-IDENTIFICATION CHECK PASSED.")
    print("What this establishes: the text crossing the model boundary carries")
    print("none of the identifier categories tested above.")
    print("What it does not: a legal determination that the result is")
    print("de-identified for your data. See legal/README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
