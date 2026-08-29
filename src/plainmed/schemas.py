"""Pydantic schemas shared across the PlainMed pipeline.

Every piece of user-facing output is one of these validated models, so the UI
never renders free-form model text that skipped validation.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ValueStatus(str, Enum):
    """How a lab value relates to its reference information.

    'flagged_*' means the report itself carried a flag (H/L/etc.); the
    'above/below/within' statuses are computed from the listed range. Being
    within a listed range is deliberately NOT called 'normal'.
    """

    flagged_high = "flagged_high"
    flagged_low = "flagged_low"
    flagged_abnormal = "flagged_abnormal"
    above_range = "above_range"
    below_range = "below_range"
    within_range = "within_range"
    no_range = "no_range"


STATUS_LABELS = {
    ValueStatus.flagged_high: "Marked high in your report",
    ValueStatus.flagged_low: "Marked low in your report",
    ValueStatus.flagged_abnormal: "Marked abnormal in your report",
    ValueStatus.above_range: "Above the reference range listed in your report",
    ValueStatus.below_range: "Below the reference range listed in your report",
    ValueStatus.within_range: "Within the reference range listed in your report",
    ValueStatus.no_range: "No reference range listed in your report",
}

# Fallback review threshold. Each OCR backend declares its own, because
# confidence scales are not comparable between engines.
OCR_REVIEW_THRESHOLD = 0.60

ATTENTION_STATUSES = frozenset(
    {
        ValueStatus.flagged_high,
        ValueStatus.flagged_low,
        ValueStatus.flagged_abnormal,
        ValueStatus.above_range,
        ValueStatus.below_range,
    }
)


class SourceSpan(BaseModel):
    """A stable, citable region of the original report (one line)."""

    id: str
    line_no: int  # 1-based line number in the normalized text
    start: int  # character offset in the normalized text
    end: int
    text: str
    # Lowest OCR word confidence on this line (camera path only). None for
    # typed or PDF text, which is exact.
    ocr_confidence: Optional[float] = None
    # True once a person has edited this line on the review screen. A span is
    # only ever PlainMed's best reading of the report; a correction replaces
    # that reading, and the UI shows the difference in provenance.
    user_corrected: bool = False


class LabValue(BaseModel):
    """One extracted result. Raw strings are preserved verbatim."""

    analyte: str
    raw_value: str  # exactly as written, e.g. "13.5" or "<0.1"
    value: Optional[Decimal] = None  # numeric form when unambiguous
    unit: Optional[str] = None
    ref_low: Optional[Decimal] = None
    ref_high: Optional[Decimal] = None
    ref_raw: Optional[str] = None  # range exactly as written, e.g. "13.0-17.0"
    flag: Optional[str] = None  # report's own flag, e.g. "H"
    status: ValueStatus
    span_id: str
    ocr_confidence: Optional[float] = None
    # Set by the ingestion layer, which knows the recognizing engine's
    # calibration. A misread digit is the camera path's central risk, so
    # these are surfaced for confirmation rather than shown as fact.
    needs_review: bool = False


class ReportDocument(BaseModel):
    """The extracted report: normalized text, citable spans, parsed values."""

    raw_text: str
    source: str  # "pasted", "pdf", or "camera"
    spans: List[SourceSpan]
    values: List[LabValue]
    unparsed_span_ids: List[str] = Field(default_factory=list)

    def span_by_id(self, span_id: str) -> Optional[SourceSpan]:
        for span in self.spans:
            if span.id == span_id:
                return span
        return None


class CardKind(str, Enum):
    report = "report"  # "Your report says..." - supported by the document
    glossary = "glossary"  # "What this term means..." - from the local glossary
    gap = "gap"  # information the report does not provide


class ExplanationCard(BaseModel):
    kind: CardKind
    title: str
    body: str
    span_ids: List[str] = Field(default_factory=list)
    glossary_key: Optional[str] = None
    status: Optional[ValueStatus] = None


class ClinicianQuestion(BaseModel):
    text: str
    span_ids: List[str] = Field(default_factory=list)


class ComprehensionQuestion(BaseModel):
    question: str
    options: List[str]
    answer_index: int
    span_ids: List[str] = Field(default_factory=list)
    explanation: str = ""


class NarrativeItem(BaseModel):
    """One validated summary statement, with the spans that support it."""

    text: str
    span_ids: List[str] = Field(min_length=1)


class Narrative(BaseModel):
    items: List[NarrativeItem]
    backend: str  # which backend produced it, e.g. "deterministic", "medgemma"


class ValidationIssue(BaseModel):
    severity: str  # "error" or "warning"
    code: str
    message: str


class ExplanationResult(BaseModel):
    cards: List[ExplanationCard]
    narrative: Optional[Narrative] = None
    clinician_questions: List[ClinicianQuestion] = Field(default_factory=list)
    comprehension_questions: List[ComprehensionQuestion] = Field(default_factory=list)
    issues: List[ValidationIssue] = Field(default_factory=list)
