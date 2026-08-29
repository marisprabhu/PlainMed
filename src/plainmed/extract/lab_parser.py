"""Deterministic extraction of lab values from report text.

Design constraints:
- Numbers, units, ranges, and flags are preserved verbatim (raw strings kept
  alongside any numeric interpretation).
- Every extracted value points at a stable SourceSpan (one report line).
- Lines that cannot be parsed are surfaced for user review, never dropped
  silently.
- No model involvement: extraction must be reproducible and testable.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Sequence

from plainmed.schemas import (
    OCR_REVIEW_THRESHOLD,
    LabValue,
    ReportDocument,
    SourceSpan,
    ValueStatus,
)

# Lines that are report metadata, not results.
_METADATA_RE = re.compile(
    r"\b(date|dob|birth|patient|name|mrn|phone|fax|page|specimen|collected|"
    r"received|reported|ordered|physician|doctor|provider|address|accession|"
    r"report\s*(?:no|number|id)|lab\s*(?:no|number|id))\b",
    re.IGNORECASE,
)

# Date-like tokens (12/03/2026, 2026-08-27, 12.03.26) mean the line's numbers
# are probably not lab values.
_DATE_LIKE_RE = re.compile(r"\b\d{1,4}[/.]\d{1,2}[/.]\d{1,4}\b|\b\d{4}-\d{2}-\d{2}\b")

_NUMBER_RE = re.compile(r"[<>]?\d+(?:\.\d+)?")
_RANGE_RE = re.compile(
    r"(?<![\d.^])(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)(?![\d.])"
)
_UNIT_RE = re.compile(r"^[A-Za-zµ%][A-Za-z0-9µ^/%*.\-]*$")

_FLAG_TOKENS = {
    "h": "H",
    "l": "L",
    "hh": "HH",
    "ll": "LL",
    "high": "High",
    "low": "Low",
    "abn": "Abnormal",
    "abnormal": "Abnormal",
    "crit": "Critical",
    "critical": "Critical",
    "*": "*",
}

_FLAG_RE = re.compile(
    r"(?:^|[\s(\[])(\*|HH?|LL?|HIGH|LOW|High|Low|Abn(?:ormal)?|Crit(?:ical)?)"
    r"(?=$|[\s)\].,;])"
)


def _to_decimal(token: str) -> Optional[Decimal]:
    if token.startswith(("<", ">")):
        return None
    try:
        return Decimal(token)
    except InvalidOperation:
        return None


def _clean_name(raw: str) -> str:
    name = raw.strip().strip(":;,.-–").strip()
    return re.sub(r"\s+", " ", name)


def _compute_status(
    flag: Optional[str],
    value: Optional[Decimal],
    ref_low: Optional[Decimal],
    ref_high: Optional[Decimal],
) -> ValueStatus:
    if flag:
        upper = flag.upper()
        if upper in {"H", "HH", "HIGH"}:
            return ValueStatus.flagged_high
        if upper in {"L", "LL", "LOW"}:
            return ValueStatus.flagged_low
        return ValueStatus.flagged_abnormal
    if value is not None and ref_low is not None and ref_high is not None:
        if value < ref_low:
            return ValueStatus.below_range
        if value > ref_high:
            return ValueStatus.above_range
        return ValueStatus.within_range
    return ValueStatus.no_range


def _parse_line(
    line: str,
    span_id: str,
    confidence: Optional[float] = None,
    review_threshold: float = OCR_REVIEW_THRESHOLD,
) -> Optional[LabValue]:
    if not re.search(r"[A-Za-z]{2}", line):
        return None
    if _METADATA_RE.search(line):
        return None
    if _DATE_LIKE_RE.search(line):
        return None

    value_match = _NUMBER_RE.search(line)
    if value_match is None:
        return None

    name = _clean_name(line[: value_match.start()])
    if len(re.sub(r"[^A-Za-z]", "", name)) < 2:
        return None

    raw_value = value_match.group(0)
    value = _to_decimal(raw_value)
    rest = line[value_match.end() :]

    # Reference range: first "low - high" pattern after the value.
    ref_low = ref_high = None
    ref_raw = None
    range_match = _RANGE_RE.search(rest)
    if range_match:
        ref_low = _to_decimal(range_match.group(1))
        ref_high = _to_decimal(range_match.group(2))
        ref_raw = range_match.group(0).strip()

    # Unit: the first token after the value, unless it is a flag or a range.
    unit = None
    unit_zone = rest[: range_match.start()] if range_match else rest
    for token in unit_zone.replace("(", " ").replace(")", " ").split():
        stripped = token.strip(":;,")
        if not stripped:
            continue
        if stripped.lower() in _FLAG_TOKENS:
            break
        if _UNIT_RE.match(stripped):
            unit = stripped
        break

    # Flag: a standalone flag token anywhere after the value.
    flag = None
    flag_zone = rest
    if unit is not None:
        # Avoid re-reading the unit itself (e.g. "L" inside "g/dL" is already
        # excluded by token boundaries; this guards units like plain "L").
        idx = rest.find(unit)
        if idx >= 0:
            flag_zone = rest[: idx] + " " + rest[idx + len(unit) :]
    flag_match = _FLAG_RE.search(flag_zone)
    if flag_match:
        flag = _FLAG_TOKENS.get(flag_match.group(1).lower(), flag_match.group(1))

    status = _compute_status(flag, value, ref_low, ref_high)
    return LabValue(
        analyte=name,
        raw_value=raw_value,
        value=value,
        unit=unit,
        ref_low=ref_low,
        ref_high=ref_high,
        ref_raw=ref_raw,
        flag=flag,
        status=status,
        span_id=span_id,
        ocr_confidence=confidence,
        needs_review=confidence is not None and confidence < review_threshold,
    )


def parse_report(
    text: str,
    source: str = "pasted",
    line_confidence: Optional[Sequence[float]] = None,
    review_threshold: float = OCR_REVIEW_THRESHOLD,
) -> ReportDocument:
    """Split normalized text into citable spans and extract lab values.

    ``line_confidence`` is the per-line OCR confidence from the camera path,
    indexed by 0-based line number, and ``review_threshold`` is the
    recognizing engine's calibration. Both are omitted for typed or PDF
    text, which is exact rather than recognized.
    """
    spans: List[SourceSpan] = []
    values: List[LabValue] = []
    unparsed: List[str] = []

    offset = 0
    span_counter = 0
    for line_no, line in enumerate(text.split("\n"), start=1):
        start = offset
        end = offset + len(line)
        offset = end + 1  # account for the newline
        if not line.strip():
            continue
        confidence = None
        if line_confidence is not None and line_no - 1 < len(line_confidence):
            confidence = float(line_confidence[line_no - 1])

        span_counter += 1
        span_id = f"S{span_counter}"
        spans.append(
            SourceSpan(
                id=span_id,
                line_no=line_no,
                start=start,
                end=end,
                text=line,
                ocr_confidence=confidence,
            )
        )
        parsed = _parse_line(line, span_id, confidence, review_threshold)
        if parsed is not None:
            values.append(parsed)
        else:
            unparsed.append(span_id)

    return ReportDocument(
        raw_text=text,
        source=source,
        spans=spans,
        values=values,
        unparsed_span_ids=unparsed,
    )
