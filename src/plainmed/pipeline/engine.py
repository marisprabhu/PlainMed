"""Pipeline orchestration: text in, validated ExplanationResult out."""

from __future__ import annotations

from typing import Optional

from plainmed.config import AppConfig
from plainmed.extract import parse_report
from plainmed.glossary import Glossary, load_glossary
from plainmed.llm.base import (
    ModelOutputError,
    ModelUnavailableError,
    get_backend,
)
from plainmed.pipeline.explain import build_cards
from plainmed.pipeline.questions import (
    build_clinician_questions,
    build_comprehension_questions,
)
from plainmed.pipeline.validate import validate_cards, validate_narrative_items
from plainmed.schemas import (
    ExplanationResult,
    Narrative,
    ReportDocument,
    ValidationIssue,
)


def extract(text: str, source: str = "pasted") -> ReportDocument:
    """Parse normalized report text into a reviewable document."""
    return parse_report(text, source=source)


def analyze(
    doc: ReportDocument,
    config: Optional[AppConfig] = None,
    glossary: Optional[Glossary] = None,
) -> ExplanationResult:
    """Produce validated cards, narrative, and questions for a document."""
    config = config or AppConfig()
    glossary = glossary or load_glossary()
    issues: list[ValidationIssue] = []

    cards, card_issues = validate_cards(build_cards(doc, glossary), doc)
    issues.extend(card_issues)

    narrative = None
    backend = None
    try:
        backend = get_backend(config)
        items = backend.generate(doc)
    except (ModelUnavailableError, ModelOutputError) as exc:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="backend_fallback",
                message=f"The language model was not used: {exc}",
            )
        )
        items = []

    if backend is not None and items:
        kept, item_issues = validate_narrative_items(items, doc)
        issues.extend(item_issues)
        if kept:
            narrative = Narrative(items=kept, backend=backend.name)

    if narrative is None and (backend is None or backend.name != "deterministic"):
        # Model missing or its entire output failed validation: fall back to
        # the deterministic engine rather than showing nothing.
        from plainmed.llm.deterministic import DeterministicBackend

        fallback = DeterministicBackend()
        kept, item_issues = validate_narrative_items(fallback.generate(doc), doc)
        issues.extend(item_issues)
        if kept:
            narrative = Narrative(items=kept, backend=fallback.name)

    return ExplanationResult(
        cards=cards,
        narrative=narrative,
        clinician_questions=build_clinician_questions(doc, glossary),
        comprehension_questions=build_comprehension_questions(doc),
        issues=issues,
    )
