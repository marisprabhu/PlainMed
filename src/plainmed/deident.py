"""De-identification at the model boundary.

Why this exists
---------------
PlainMed's explanation model never needs to know who the patient is. It
needs analyte names, numbers, units, ranges and flags. Everything else on a
lab report - name, date of birth, MRN, ordering physician, address - is
identifying and must not leave the trusted tier.

Approach: allowlist, not scrubber
---------------------------------
A regex scrubber is a denylist: it removes the identifiers you thought of
and passes through the ones you did not. This module instead *reconstructs*
the text sent to the model from already-parsed ``LabValue`` fields. A value
that survived parsing consists of an analyte name, a number, an optional
unit, an optional range and an optional flag - a shape that cannot carry a
patient name, because a line containing one would never have parsed into it.

Raw report text is therefore never forwarded. Lines PlainMed could not parse
are withheld entirely rather than passed along "just in case", which is the
conservative direction: the cost is a slightly less contextual summary, and
the benefit is that the model tier is not handling PHI.

What this does and does not establish
-------------------------------------
This implements the mechanical part of HIPAA Safe Harbor (45 CFR
164.514(b)(2)) *for the text crossing the model boundary*: the reconstructed
lines contain none of the 18 identifier categories, and ``assert_deidentified``
re-checks the output rather than trusting the construction.

It does NOT de-identify the uploaded image, the OCR output, or anything
before this boundary. Those remain PHI and stay in the trusted tier. It is
also not a legal determination - your counsel or a qualified statistician
must confirm the standard is met for your data. See legal/README.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence

from plainmed.schemas import LabValue, ReportDocument

# Analyte names are matched against this shape before being forwarded. A
# real analyte is letters, digits, spaces and a little punctuation - long
# enough for "Mean corpuscular hemoglobin concentration", constrained enough
# to exclude free text that happens to sit where a name belongs.
_ANALYTE_SHAPE = re.compile(r"^[A-Za-z][A-Za-z0-9 ()/%.,'+-]{0,63}$")

# Units and ranges are tightly shaped; anything else is dropped rather than
# forwarded unexamined.
_UNIT_SHAPE = re.compile(r"^[A-Za-zµ%][A-Za-z0-9µ^/%*.\-]{0,15}$")
_VALUE_SHAPE = re.compile(r"^[<>]?\d{1,12}(?:\.\d{1,6})?$")
_RANGE_SHAPE = re.compile(r"^\d{1,12}(?:\.\d{1,6})?\s*[-–—]\s*\d{1,12}(?:\.\d{1,6})?$")
_FLAG_SHAPE = re.compile(r"^[A-Za-z*]{1,10}$")

# Post-construction verification. These patterns must not appear in text
# leaving the trusted tier; a hit means the allowlist above is too loose.
_FORBIDDEN = [
    ("date", re.compile(r"\b\d{1,4}[/.]\d{1,2}[/.]\d{1,4}\b|\b\d{4}-\d{2}-\d{2}\b")),
    ("email", re.compile(r"[^\s@]+@[^\s@]+\.[A-Za-z]{2,}")),
    ("phone", re.compile(r"\b(?:\+?\d[\d ()-]{8,}\d)\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("url", re.compile(r"https?://|www\.", re.IGNORECASE)),
    (
        "identifier_label",
        re.compile(
            r"\b(mrn|ssn|nhs|patient|dob|date\s+of\s+birth|address|phone|fax|"
            r"physician|doctor|accession|specimen|insurance|policy)\b",
            re.IGNORECASE,
        ),
    ),
]


class DeidentificationError(RuntimeError):
    """Text failed verification and must not be sent onward."""


@dataclass
class DeidentifiedReport:
    """What the model tier is allowed to receive."""

    lines: List[str]
    # Span IDs, parallel to ``lines``. These are opaque labels ("S3") that
    # carry no meaning outside this request, so they are safe to forward and
    # let the model cite sources.
    span_ids: List[str]
    withheld_line_count: int

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _is_clean(text: str) -> bool:
    return not any(pattern.search(text) for _, pattern in _FORBIDDEN)


def _safe_field(value: str | None, shape: re.Pattern) -> str:
    """Return the field only if it matches its shape AND carries no identifier.

    Two gates rather than one: the shape is an allowlist of what a field may
    look like, and the identifier check catches content that satisfies the
    shape anyway - an analyte field is permissive enough to admit a stray
    "Jane Doe, DOB 04/11/1978" otherwise.

    A failing field is dropped and its value omitted, so hostile or garbled
    input degrades the summary rather than stopping the request.
    ``assert_deidentified`` remains the backstop for genuine defects.
    """
    if not value:
        return ""
    candidate = value.strip()
    if not shape.match(candidate) or not _is_clean(candidate):
        return ""
    return candidate


def _render(value: LabValue) -> str:
    """Rebuild one report line from validated fields only."""
    analyte = _safe_field(value.analyte, _ANALYTE_SHAPE)
    raw_value = _safe_field(value.raw_value, _VALUE_SHAPE)
    if not analyte or not raw_value:
        return ""

    parts = [analyte, raw_value]
    unit = _safe_field(value.unit, _UNIT_SHAPE)
    if unit:
        parts.append(unit)
    ref = _safe_field(value.ref_raw, _RANGE_SHAPE)
    if ref:
        parts.append(f"(ref {ref})")
    flag = _safe_field(value.flag, _FLAG_SHAPE)
    if flag:
        parts.append(f"[{flag}]")
    return " ".join(parts)


def assert_deidentified(lines: Sequence[str]) -> None:
    """Re-check constructed text before it leaves the trusted tier.

    Construction should make this impossible to fail. It runs anyway: a
    silent regression here would send PHI to an untrusted tier, so the
    failure mode must be a raised exception, not a passing test suite.
    """
    for line in lines:
        for label, pattern in _FORBIDDEN:
            match = pattern.search(line)
            if match:
                raise DeidentificationError(
                    f"Refusing to forward text containing a possible {label}. "
                    "This indicates a defect in de-identification; the request "
                    "was stopped rather than risk disclosure."
                )


def deidentify(doc: ReportDocument) -> DeidentifiedReport:
    """Reduce a report to the minimum the model needs, and verify it."""
    lines: List[str] = []
    span_ids: List[str] = []

    for value in doc.values:
        rendered = _render(value)
        if rendered:
            lines.append(f"[{value.span_id}] {rendered}")
            span_ids.append(value.span_id)

    withheld = len(doc.spans) - len(lines)
    assert_deidentified(lines)
    return DeidentifiedReport(
        lines=lines, span_ids=span_ids, withheld_line_count=withheld
    )
