"""Turn positioned OCR words into report lines.

This is the highest-risk code in the camera path. A lab report is a table:
if words are joined in raw reading order, a value from one row can end up
beside a reference range from another, and the rest of the pipeline would
happily validate the wrong pairing.

The approach:
1. Group words into rows by vertical overlap, using the median word height
   as the tolerance so it adapts to image resolution.
2. Sort each row left to right.
3. Insert a wide gap (two spaces) where the horizontal distance between
   neighbours is large, so column boundaries survive into the text and the
   lab parser sees "Glucose 108 mg/dL 70-99 High" rather than a run-on.

Confidence is carried per line so the review screen can flag a value the
engine was unsure about instead of presenting a possibly-misread number as
fact. It is scored over the *digit-bearing* words only: a fuzzy "Hematocrit"
changes nothing, a fuzzy "13.5" changes everything. Scoring whole lines
flagged every row on real input, and a warning that fires always is a
warning nobody reads.
"""

from __future__ import annotations

import re
import statistics
from typing import List, Sequence, Tuple

from plainmed.ocr.base import OcrWord

# A word joins a row when its vertical centre is within this fraction of the
# median word height of the row's centre. Tuned to keep sub/superscripts with
# their row while keeping adjacent table rows apart.
_ROW_TOLERANCE = 0.6

# Horizontal gap, as a multiple of median word height, above which a column
# break is assumed and a double space is emitted.
_COLUMN_GAP = 1.2

_HAS_DIGIT = re.compile(r"\d")


def _line_confidence(row: Sequence[OcrWord]) -> float:
    """Lowest confidence among words carrying digits, else over all words."""
    digit_words = [w for w in row if _HAS_DIGIT.search(w.text)]
    return min(w.confidence for w in (digit_words or row))


def _median_height(words: Sequence[OcrWord]) -> float:
    heights = [w.height for w in words if w.height > 0]
    if not heights:
        return 1.0
    return statistics.median(heights)


def _group_rows(
    words: Sequence[OcrWord], tolerance: float
) -> List[List[OcrWord]]:
    rows: List[List[OcrWord]] = []
    for word in sorted(words, key=lambda w: w.y_center):
        placed = False
        for row in rows:
            row_center = statistics.mean(w.y_center for w in row)
            if abs(word.y_center - row_center) <= tolerance:
                row.append(word)
                placed = True
                break
        if not placed:
            rows.append([word])
    # Order rows top to bottom by their final centres.
    rows.sort(key=lambda r: statistics.mean(w.y_center for w in r))
    return rows


def _join_row(row: Sequence[OcrWord], column_gap: float) -> str:
    ordered = sorted(row, key=lambda w: w.box[0])
    parts: List[str] = []
    previous_right = None
    for word in ordered:
        text = word.text.strip()
        if not text:
            continue
        if previous_right is not None:
            gap = word.box[0] - previous_right
            parts.append("  " if gap >= column_gap else " ")
        parts.append(text)
        previous_right = word.box[2]
    return "".join(parts).strip()


def reconstruct_lines(
    words: Sequence[OcrWord],
) -> Tuple[List[str], List[float]]:
    """Return (lines, per-line confidence over digit-bearing words)."""
    usable = [w for w in words if w.text and w.text.strip()]
    if not usable:
        return [], []

    height = _median_height(usable)
    rows = _group_rows(usable, tolerance=height * _ROW_TOLERANCE)

    lines: List[str] = []
    confidences: List[float] = []
    for row in rows:
        text = _join_row(row, column_gap=height * _COLUMN_GAP)
        if not text:
            continue
        lines.append(text)
        confidences.append(_line_confidence(row))
    return lines, confidences
