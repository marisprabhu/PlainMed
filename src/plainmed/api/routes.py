"""API endpoints.

Two-step flow, deliberately preserved from the desktop app: /scan returns
what PlainMed read so the user can confirm it, and /explain only runs on a
document the user has seen. Nothing is explained that the user has not had
a chance to correct - which matters far more once OCR, not typing, is the
input.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from plainmed import __version__
from plainmed.api.dto import (
    ConsentRequest,
    NoticeResponse,
    InternalGenerateRequest,
    InternalGenerateResponse,
    ExplainRequest,
    ExplainResponse,
    HealthResponse,
    PasteRequest,
    ScanResponse,
    SessionResponse,
)
from plainmed.api.security import (
    CONSENT_VERSION,
    ConsentRequiredError,
    RateLimitedError,
    Session,
    issue_session,
    record_audit,
    verify_session,
)
from plainmed.ingest import (
    EmptyReportError,
    EncryptedPdfError,
    PdfTooLargeError,
    ReportTooLargeError,
    ScannedPdfError,
    load_pdf,
    load_text,
)
from plainmed.ingest.camera_loader import NoTextFoundError, load_camera_image
from plainmed.ocr.preprocess import (
    ImageTooLargeError,
    ImageTooSmallError,
    UnreadableImageError,
)
from plainmed.compliance import SUPPORTED_LANGUAGES, get_notice
from plainmed.compliance.notice import GrievanceContactMissingError
from plainmed.deident import DeidentificationError, assert_deidentified
from plainmed.pipeline import analyze, extract
from plainmed.schemas import LabValue, ReportDocument, SourceSpan

log = logging.getLogger("plainmed.api")
router = APIRouter()


def require_session(request: Request) -> Session:
    """Authenticate the caller and charge them a rate-limit token.

    Applied to every endpoint that does work. /health and /session are
    exempt - the first must answer for load balancers, the second is how a
    caller obtains a session in the first place.
    """
    try:
        session = verify_session(request.headers.get("x-plainmed-session"))
    except ConsentRequiredError as exc:
        record_audit(None, request.url.path, "denied_no_consent")
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    limiter = request.app.state.limiter
    # Limit on the session, and on the address too: a client that discards
    # and re-requests sessions would otherwise reset its own budget.
    client_ip = request.client.host if request.client else "unknown"
    try:
        limiter.check(f"sid:{session.sid}")
        limiter.check(f"ip:{client_ip}")
    except RateLimitedError as exc:
        record_audit(session, request.url.path, "rate_limited")
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    return session


_LINE_ID_RE = re.compile(r"^\[(S\d+)\]\s*(.*)$")


def _document_from_lines(lines: List[str]) -> ReportDocument:
    """Rebuild a minimal document from de-identified lines.

    The model tier is given text, not a document, so it reconstructs just
    enough for the backend to build a prompt and cite span IDs. No values
    are parsed here - the trusted tier already did that, and re-parsing
    would risk disagreeing with it.
    """
    spans: List[SourceSpan] = []
    offset = 0
    for index, line in enumerate(lines, start=1):
        match = _LINE_ID_RE.match(line)
        span_id = match.group(1) if match else f"S{index}"
        text = match.group(2) if match else line
        spans.append(
            SourceSpan(
                id=span_id,
                line_no=index,
                start=offset,
                end=offset + len(text),
                text=text,
            )
        )
        offset += len(text) + 1
    return ReportDocument(
        raw_text="\n".join(s.text for s in spans),
        source="deidentified",
        spans=spans,
        values=[],
    )


def _low_confidence_spans(doc: ReportDocument) -> List[str]:
    return [v.span_id for v in doc.values if v.needs_review]


def _scan_response(doc: ReportDocument, ocr_backend: str, started: float) -> ScanResponse:
    return ScanResponse(
        document=doc,
        ocr_backend=ocr_backend,
        low_confidence_span_ids=_low_confidence_spans(doc),
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    runtime = request.app.state.runtime
    return HealthResponse(
        status="ok",
        version=__version__,
        llm_backend=runtime.llm_backend_name,
        ocr_backend=runtime.ocr_backend_name,
        consent_version=CONSENT_VERSION,
    )


@router.post("/internal/generate", response_model=InternalGenerateResponse)
def internal_generate(
    request: Request, payload: InternalGenerateRequest
) -> InternalGenerateResponse:
    """Model-tier endpoint: de-identified lines in, statements out.

    Served only by the model tier, and only reachable from the trusted tier
    over a private network. It receives no document, no identifiers and no
    session - just lab lines - which is exactly why the GPU running it does
    not process PHI.

    The caller validates whatever comes back against the source document, so
    nothing here is trusted downstream.
    """
    expected = os.environ.get("PLAINMED_MODEL_TIER_TOKEN", "")
    if expected and request.headers.get("x-plainmed-internal") != expected:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    # Defence in depth: refuse to process anything carrying an identifier,
    # even though the caller de-identified it. A model tier that accepts PHI
    # is a model tier that will eventually be sent PHI.
    try:
        assert_deidentified(payload.lines)
    except DeidentificationError as exc:
        log.error("internal.generate rejected non-deidentified input")
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    runtime = request.app.state.runtime
    backend = runtime.llm
    if backend.name == "remote":
        raise HTTPException(
            status_code=500,
            detail="Model tier is misconfigured as a remote client.",
        )

    doc = _document_from_lines(payload.lines)
    started = time.perf_counter()
    try:
        items = backend.generate(doc)
    except Exception as exc:
        log.warning("internal.generate failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Generation failed.") from exc

    log.info(
        "internal.generate lines=%d items=%d %.0fms",
        len(payload.lines),
        len(items),
        (time.perf_counter() - started) * 1000,
    )
    return InternalGenerateResponse(items=items)


@router.post("/client-error", include_in_schema=False)
async def client_error(request: Request) -> dict:
    """Receive a browser-side error so it lands in the server log.

    Diagnosing a client fault normally means asking the user to open
    devtools. That is a poor ask, and it fails when the person reporting the
    bug is on a phone. The browser posts its errors here instead, so they
    appear in the log the operator is already reading.

    Deliberately unauthenticated: an error that happens before consent still
    needs to be reportable. Nothing here is trusted - fields are truncated
    and only ever logged, never echoed back or stored.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    def clip(key: str, limit: int = 300) -> str:
        text = str(payload.get(key, ""))[:limit]
        return " | ".join(text.splitlines())

    # A startup ping is not a fault. Logging it at ERROR made a healthy load
    # look broken, which is worse than not logging it at all.
    where = clip("where", 60)
    level = log.info if where == "startup" else log.error
    label = "CLIENT OK   " if where == "startup" else "CLIENT ERROR"
    level(
        label + " build=%s ua=%s where=%s msg=%s stack=%s",
        clip("build", 40),
        clip("ua", 120),
        where,
        clip("message"),
        clip("stack", 600),
    )
    return {"received": True}


@router.get("/notice", response_model=NoticeResponse)
def notice(request: Request, lang: str = "en") -> NoticeResponse:
    """The itemised notice a user must see before consenting.

    DPDP Rule 3 requires notice that stands on its own, in clear plain
    language, itemising the data collected and the purpose of each - not a
    link to a policy page. It must be available in English or an Eighth
    Schedule language, so the client sends its preferred language here.
    """
    require_contact = os.environ.get("PLAINMED_ENV") == "production"
    try:
        content = get_notice(lang, require_contact=require_contact)
    except GrievanceContactMissingError as exc:
        # Failing loudly beats serving a notice with a placeholder contact.
        log.error("notice unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return NoticeResponse(
        language=content.language,
        version=content.version,
        consent_version=CONSENT_VERSION,
        title=content.title,
        intro=content.intro,
        items=[{"data": i.data, "purpose": i.purpose} for i in content.items],
        retention=content.retention,
        sharing=content.sharing,
        rights=content.rights,
        withdraw=content.withdraw,
        grievance=content.grievance,
        board=content.board,
        age=content.age,
        not_medical_advice=content.not_medical_advice,
        contact=content.contact,
        available_languages=list(SUPPORTED_LANGUAGES),
    )


@router.post("/session", response_model=SessionResponse)
def create_session(request: Request, payload: ConsentRequest) -> SessionResponse:
    """Exchange acceptance of the current terms for an anonymous session.

    This is the consent gate: no session is issued without it, and no other
    endpoint works without a session.
    """
    if payload.consent_version != CONSENT_VERSION:
        raise HTTPException(
            status_code=409,
            detail="Our terms have been updated. Please reload and accept them.",
        )
    if not payload.accepted:
        raise HTTPException(
            status_code=400, detail="Consent is required to use PlainMed."
        )
    # DPDP treats anyone under 18 as a child and requires verifiable parental
    # consent before processing their data. PlainMed does not implement that,
    # so it excludes under-18s - and the exclusion is enforced here rather
    # than left as a line in the terms.
    if not payload.age_confirmed:
        record_audit(None, "/session", "denied_age")
        raise HTTPException(
            status_code=403,
            detail="PlainMed is only for people aged 18 or over.",
        )
    token = issue_session(payload.consent_version, age_confirmed=True)
    session = verify_session(token)
    record_audit(session, "/session", "consent_granted")
    return SessionResponse(
        session=token,
        consent_version=CONSENT_VERSION,
        expires_in=3600,
    )


@router.post("/scan/photo", response_model=ScanResponse)
async def scan_photo(
    request: Request,
    image: UploadFile = File(...),
    session: Session = Depends(require_session),
) -> ScanResponse:
    """Camera path: a photo of a report becomes a reviewable document."""
    started = time.perf_counter()
    runtime = request.app.state.runtime
    data = await image.read()

    try:
        doc = load_camera_image(
            data,
            backend=runtime.ocr,
            max_chars=runtime.config.max_report_chars,
        )
    except (
        UnreadableImageError,
        ImageTooLargeError,
        ImageTooSmallError,
        NoTextFoundError,
        ReportTooLargeError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Deliberately logs counts only - never the text.
    log.info(
        "scan.photo values=%d spans=%d low_confidence=%d",
        len(doc.values),
        len(doc.spans),
        len(_low_confidence_spans(doc)),
    )
    result = _scan_response(doc, runtime.ocr_backend_name, started)
    record_audit(
        session, "/scan/photo", "ok", result.duration_ms, values=len(doc.values)
    )
    return result


@router.post("/scan/pdf", response_model=ScanResponse)
async def scan_pdf(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(require_session),
) -> ScanResponse:
    started = time.perf_counter()
    runtime = request.app.state.runtime
    data = await file.read()

    try:
        text = load_pdf(
            data,
            max_pages=runtime.config.max_pdf_pages,
            max_chars=runtime.config.max_report_chars,
        )
    except (
        ScannedPdfError,
        EncryptedPdfError,
        PdfTooLargeError,
        EmptyReportError,
        ReportTooLargeError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail="This file could not be read as a PDF."
        ) from exc

    doc = extract(text, source="pdf")
    log.info("scan.pdf values=%d spans=%d", len(doc.values), len(doc.spans))
    result = _scan_response(doc, "none", started)
    record_audit(session, "/scan/pdf", "ok", result.duration_ms, values=len(doc.values))
    return result


@router.post("/scan/text", response_model=ScanResponse)
def scan_text(
    request: Request,
    payload: PasteRequest,
    session: Session = Depends(require_session),
) -> ScanResponse:
    started = time.perf_counter()
    runtime = request.app.state.runtime
    try:
        text = load_text(payload.text, max_chars=runtime.config.max_report_chars)
    except (EmptyReportError, ReportTooLargeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    doc = extract(text, source="pasted")
    log.info("scan.text values=%d spans=%d", len(doc.values), len(doc.spans))
    result = _scan_response(doc, "none", started)
    record_audit(session, "/scan/text", "ok", result.duration_ms, values=len(doc.values))
    return result


def _apply_corrections(doc: ReportDocument, corrections) -> ReportDocument:
    """Apply user edits from the review screen.

    A source span is only ever PlainMed's best *reading* of the report, not
    ground truth about the paper. So when a person corrects a misread value,
    the span text is updated to match: otherwise a card saying "your report
    lists Glucose as 88" would cite a line still reading "108" and the
    validator would - correctly - reject it.

    Two guards keep this narrow:
    - A correction must name a span that already exists.
    - Only the recognized value/unit substring is substituted, so a
      correction rewrites a reading rather than authoring arbitrary text.

    Corrected spans are marked ``user_corrected`` so provenance stays visible.

    Note on trust: the client posts the document, so the API cannot verify it
    matches a real piece of paper. The validator guarantees explanations are
    consistent with the document in hand - which is the property that keeps
    an explanation checkable by the person holding the report.
    """
    if not corrections:
        return doc

    from plainmed.extract.lab_parser import _compute_status, _to_decimal

    known_spans = {s.id for s in doc.spans}
    by_span = {c.span_id: c for c in corrections if c.span_id in known_spans}
    if not by_span:
        return doc

    updated_values: list[LabValue] = []
    span_text_edits: dict[str, list[tuple[str, str]]] = {}

    for value in doc.values:
        correction = by_span.get(value.span_id)
        if correction is None:
            updated_values.append(value)
            continue

        raw_value = (correction.raw_value or "").strip() or value.raw_value
        unit = correction.unit if correction.unit is not None else value.unit
        analyte = (correction.analyte or "").strip() or value.analyte
        numeric = _to_decimal(raw_value)

        edits = []
        if raw_value != value.raw_value:
            edits.append((value.raw_value, raw_value))
        if value.unit and unit and unit != value.unit:
            edits.append((value.unit, unit))
        if analyte != value.analyte:
            edits.append((value.analyte, analyte))
        if edits:
            span_text_edits.setdefault(value.span_id, []).extend(edits)

        updated_values.append(
            value.model_copy(
                update={
                    "analyte": analyte,
                    "raw_value": raw_value,
                    "value": numeric,
                    "unit": unit,
                    "status": _compute_status(
                        value.flag, numeric, value.ref_low, value.ref_high
                    ),
                    # The user has now confirmed this line, so it is no longer
                    # an unreviewed OCR guess.
                    "ocr_confidence": None,
                }
            )
        )

    updated_spans = []
    for span in doc.spans:
        edits = span_text_edits.get(span.id)
        if not edits:
            updated_spans.append(
                span.model_copy(update={"user_corrected": span.id in by_span})
                if span.id in by_span
                else span
            )
            continue
        text = span.text
        for old, new in edits:
            if old and old in text:
                text = text.replace(old, new, 1)
        updated_spans.append(
            span.model_copy(update={"text": text, "user_corrected": True})
        )

    # raw_text is rebuilt from the spans so the source panel and the spans
    # cannot drift apart.
    return doc.model_copy(
        update={
            "values": updated_values,
            "spans": updated_spans,
            "raw_text": "\n".join(s.text for s in updated_spans),
        }
    )


@router.post("/explain", response_model=ExplainResponse)
def explain(
    request: Request,
    payload: ExplainRequest,
    session: Session = Depends(require_session),
) -> ExplainResponse:
    """Explain a document the user has already reviewed."""
    started = time.perf_counter()
    runtime = request.app.state.runtime

    doc = _apply_corrections(payload.document, payload.corrections)
    if not doc.values:
        raise HTTPException(
            status_code=422,
            detail="No test results were found to explain.",
        )

    result = analyze(doc, config=runtime.config, glossary=runtime.glossary)
    backend = result.narrative.backend if result.narrative else "none"
    log.info(
        "explain cards=%d questions=%d issues=%d backend=%s",
        len(result.cards),
        len(result.clinician_questions),
        len(result.issues),
        backend,
    )
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    record_audit(
        session, "/explain", "ok", duration_ms, cards=len(result.cards)
    )
    return ExplainResponse(result=result, backend=backend, duration_ms=duration_ms)
