"""Request and response models for the PlainMed API.

The client never sends back free text for explanation: it returns the
document PlainMed itself produced (optionally with values the user
corrected). That keeps the source spans authoritative - a client cannot
invent a citation that the validator would then accept.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from plainmed.schemas import (
    ExplanationResult,
    NarrativeItem,
    ReportDocument,
)


class ConsentRequest(BaseModel):
    """Acceptance of the current notice, exchanged for a session.

    ``age_confirmed`` is a separate affirmation, not folded into
    ``accepted``: DPDP requires verifiable parental consent for under-18s,
    which PlainMed avoids by excluding them, and a bundled checkbox would
    make that exclusion unevidenced.
    """

    accepted: bool
    consent_version: str
    age_confirmed: bool = False


class NoticeResponse(BaseModel):
    """The itemised pre-consent notice (DPDP Rule 3)."""

    language: str
    version: str
    consent_version: str
    title: str
    intro: str
    items: List[Dict[str, str]]
    retention: str
    sharing: str
    rights: List[str]
    withdraw: str
    grievance: str
    board: str
    age: str
    not_medical_advice: str
    contact: Dict[str, str]
    available_languages: List[str]


class SessionResponse(BaseModel):
    session: str
    consent_version: str
    expires_in: int


class InternalGenerateRequest(BaseModel):
    """De-identified lab lines sent from the trusted tier to the model tier."""

    lines: List[str] = Field(min_length=1, max_length=300)


class InternalGenerateResponse(BaseModel):
    items: List[NarrativeItem] = Field(default_factory=list, max_length=20)


class ScanResponse(BaseModel):
    """What the review screen needs after a scan or paste."""

    document: ReportDocument
    ocr_backend: Optional[str] = None
    # Values the user should confirm before anything is explained.
    low_confidence_span_ids: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0


class PasteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)


class ValueCorrection(BaseModel):
    """A single field the user fixed on the review screen."""

    span_id: str
    analyte: Optional[str] = None
    raw_value: Optional[str] = None
    unit: Optional[str] = None


class ExplainRequest(BaseModel):
    document: ReportDocument
    corrections: List[ValueCorrection] = Field(default_factory=list, max_length=200)


class ExplainResponse(BaseModel):
    result: ExplanationResult
    backend: str
    duration_ms: float = 0.0


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_backend: str
    ocr_backend: str
    retention: str = "none"
    consent_version: str = ""


class ErrorResponse(BaseModel):
    error: str
    detail: str
