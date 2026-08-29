"""Template-based narrative generation.

Statements are assembled only from parsed values and their verbatim raw
strings, so they cite real spans and quote real numbers by construction.
They still pass through the same validator as model output (defense in
depth).
"""

from __future__ import annotations

from typing import List

from plainmed.schemas import (
    ATTENTION_STATUSES,
    LabValue,
    NarrativeItem,
    ReportDocument,
    ValueStatus,
)


def _describe(value: LabValue) -> str:
    parts = [f"{value.analyte} at {value.raw_value}"]
    if value.unit:
        parts.append(value.unit)
    return " ".join(parts)


class DeterministicBackend:
    name = "deterministic"

    def generate(self, doc: ReportDocument) -> List[NarrativeItem]:
        items: List[NarrativeItem] = []

        if doc.values:
            # No digits here: the validator requires every number in a
            # statement to appear in its cited passages.
            items.append(
                NarrativeItem(
                    text=(
                        "PlainMed read the test results listed here directly "
                        "from your report."
                    ),
                    span_ids=[v.span_id for v in doc.values],
                )
            )

        attention = [v for v in doc.values if v.status in ATTENTION_STATUSES]
        if attention:
            described = "; ".join(_describe(v) for v in attention)
            items.append(
                NarrativeItem(
                    text=(
                        "The following results are flagged in your report or fall "
                        f"outside the reference range it lists: {described}. "
                        "Your clinician can explain what these mean in your situation."
                    ),
                    span_ids=[v.span_id for v in attention],
                )
            )

        within = [v for v in doc.values if v.status == ValueStatus.within_range]
        if within:
            names = ", ".join(v.analyte for v in within)
            items.append(
                NarrativeItem(
                    text=(
                        f"These results are within the reference ranges listed in "
                        f"your report: {names}."
                    ),
                    span_ids=[v.span_id for v in within],
                )
            )

        no_range = [v for v in doc.values if v.status == ValueStatus.no_range]
        if no_range:
            names = ", ".join(v.analyte for v in no_range)
            items.append(
                NarrativeItem(
                    text=(
                        f"Your report does not list a reference range (or a flag) "
                        f"for: {names}. PlainMed does not add its own ranges."
                    ),
                    span_ids=[v.span_id for v in no_range],
                )
            )

        return items
