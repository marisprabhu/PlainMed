"""Builds explanation cards from a parsed report.

The interface distinction the product depends on lives here:
- CardKind.report  -> "Your report says..."  (supported by the document)
- CardKind.glossary -> "What this term means..." (from the local glossary)
- CardKind.gap     -> information the report does not provide

A report may name a test without defining it; the glossary explanation is
never presented as coming from the report.
"""

from __future__ import annotations

from typing import List

from plainmed.glossary import Glossary
from plainmed.safety import GLOSSARY_SOURCE_NOTE
from plainmed.schemas import (
    CardKind,
    ExplanationCard,
    LabValue,
    ReportDocument,
    ValueStatus,
)


def _finding_body(value: LabValue) -> str:
    body = f"Your report lists {value.analyte} as {value.raw_value}"
    if value.unit:
        body += f" {value.unit}"
    body += "."
    if value.ref_raw:
        body += f" The reference range listed next to it is {value.ref_raw}."
    if value.flag:
        body += f' The report marks this result with the flag "{value.flag}".'
    return body


def build_cards(doc: ReportDocument, glossary: Glossary) -> List[ExplanationCard]:
    cards: List[ExplanationCard] = []
    seen_glossary_keys = set()

    for value in doc.values:
        cards.append(
            ExplanationCard(
                kind=CardKind.report,
                title=value.analyte,
                body=_finding_body(value),
                span_ids=[value.span_id],
                status=value.status,
            )
        )

        entry = glossary.lookup(value.analyte)
        if entry is not None:
            if entry.key not in seen_glossary_keys:
                seen_glossary_keys.add(entry.key)
                cards.append(
                    ExplanationCard(
                        kind=CardKind.glossary,
                        title=f"What {entry.display_name} means",
                        body=f"{entry.definition}\n\n{GLOSSARY_SOURCE_NOTE}",
                        glossary_key=entry.key,
                    )
                )
        else:
            cards.append(
                ExplanationCard(
                    kind=CardKind.gap,
                    title=f"No explanation available for {value.analyte}",
                    body=(
                        f"Your report names “{value.analyte}” without "
                        "defining it, and this term is not in PlainMed's local "
                        "glossary, so no explanation is added. This is a good "
                        "question for your clinician."
                    ),
                    span_ids=[value.span_id],
                )
            )

        if value.status == ValueStatus.no_range and value.flag is None:
            cards.append(
                ExplanationCard(
                    kind=CardKind.gap,
                    title=f"No reference range given for {value.analyte}",
                    body=(
                        f"Your report does not list a reference range or a flag "
                        f"for {value.analyte}. PlainMed does not add its own "
                        "reference ranges, because ranges differ between "
                        "laboratories and depend on the person."
                    ),
                    span_ids=[value.span_id],
                )
            )

    if doc.unparsed_span_ids:
        cards.append(
            ExplanationCard(
                kind=CardKind.gap,
                title="Lines PlainMed could not read",
                body=(
                    "Some lines of your report could not be interpreted as test "
                    "results and were left out of the explanation. They are "
                    "highlighted in the original report panel so you can review "
                    "them yourself."
                ),
                span_ids=list(doc.unparsed_span_ids),
            )
        )

    return cards
