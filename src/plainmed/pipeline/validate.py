"""Deterministic checks applied to every statement before it is shown.

A statement survives only if:
1. Every cited span ID exists in the document.
2. Every number it contains appears in the cited passages (compared as
   Decimals, so "13.5" matches "13.50" but not "13.6").
3. It contains no forbidden claim (diagnosis, treatment advice, reassurance)
   unless the report passage itself says it.

Failures are reported as ValidationIssues and the statement is dropped -
never silently shown.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Sequence, Tuple

from plainmed.safety import forbidden_hits
from plainmed.schemas import (
    CardKind,
    ExplanationCard,
    NarrativeItem,
    ReportDocument,
    ValidationIssue,
)

_NUMBER_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?")


def _decimals(text: str) -> set:
    found = set()
    for token in _NUMBER_TOKEN_RE.findall(text):
        try:
            found.add(Decimal(token))
        except InvalidOperation:
            continue
    return found


def _check_statement(
    text: str, span_ids: Sequence[str], doc: ReportDocument, what: str
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    spans = []
    for span_id in span_ids:
        span = doc.span_by_id(span_id)
        if span is None:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="unknown_source",
                    message=f"A {what} cited a passage that does not exist ({span_id}).",
                )
            )
        else:
            spans.append(span)
    if issues:
        return issues

    context = " ".join(span.text for span in spans)

    unsupported = _decimals(text) - _decimals(context)
    if unsupported:
        numbers = ", ".join(str(n) for n in sorted(unsupported))
        issues.append(
            ValidationIssue(
                severity="error",
                code="number_mismatch",
                message=(
                    f"A {what} contained numbers not present in its cited "
                    f"passages ({numbers}) and was removed."
                ),
            )
        )

    hits = forbidden_hits(text, allowed_context=context)
    if hits:
        issues.append(
            ValidationIssue(
                severity="error",
                code="forbidden_claim",
                message=(
                    f"A {what} contained a claim PlainMed must not make "
                    f"({hits[0]!r}) and was removed."
                ),
            )
        )
    return issues


def validate_narrative_items(
    items: Iterable[NarrativeItem], doc: ReportDocument
) -> Tuple[List[NarrativeItem], List[ValidationIssue]]:
    kept: List[NarrativeItem] = []
    issues: List[ValidationIssue] = []
    for item in items:
        item_issues = _check_statement(item.text, item.span_ids, doc, "summary statement")
        if item_issues:
            issues.extend(item_issues)
        else:
            kept.append(item)
    return kept, issues


def validate_cards(
    cards: Iterable[ExplanationCard], doc: ReportDocument
) -> Tuple[List[ExplanationCard], List[ValidationIssue]]:
    """Validate report-kind cards. Glossary/gap cards are not report-sourced,
    so number checks against the report do not apply to them."""
    kept: List[ExplanationCard] = []
    issues: List[ValidationIssue] = []
    for card in cards:
        if card.kind != CardKind.report:
            kept.append(card)
            continue
        card_issues = _check_statement(card.body, card.span_ids, doc, "finding card")
        if card_issues:
            issues.extend(card_issues)
        else:
            kept.append(card)
    return kept, issues
