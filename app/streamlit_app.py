"""PlainMed - Streamlit interface.

One screen, three sections:
- Left: the original report with highlighted source passages.
- Right: plain-language explanation cards.
- Bottom: understanding check and questions for the clinician.

Report content lives only in st.session_state (memory) and is removed by
"Clear session". Nothing is written to disk or to logs.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st

# Allow running straight from a checkout without installing the package.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from plainmed import __version__
from plainmed.config import AppConfig
from plainmed.ingest import (
    EmptyReportError,
    EncryptedPdfError,
    PdfTooLargeError,
    ReportTooLargeError,
    ScannedPdfError,
    load_pdf,
    load_text,
)
from plainmed.pipeline import analyze, extract
from plainmed.safety import DISCLAIMER, RANGE_CAUTION
from plainmed.schemas import ATTENTION_STATUSES, STATUS_LABELS, CardKind

TEAL = "#0F766E"
NAVY = "#16324F"
OFFWHITE = "#F8FAFC"

st.set_page_config(page_title="PlainMed", page_icon="📄", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {OFFWHITE}; }}
    .stApp, .stApp p, .stApp li, .stApp label {{ color: {NAVY}; }}
    h1, h2, h3 {{ color: {NAVY}; }}
    .plainmed-report {{
        font-family: ui-monospace, Consolas, monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        line-height: 1.7;
    }}
    .plainmed-span-id {{
        color: {TEAL};
        font-size: 0.7rem;
        margin-right: 0.4rem;
    }}
    .plainmed-parsed {{ background: #CCFBF1; border-radius: 3px; }}
    .plainmed-unparsed {{ background: #FEF3C7; border-radius: 3px; }}
    .plainmed-card {{
        background: white;
        border: 1px solid #E2E8F0;
        border-left: 4px solid {TEAL};
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.75rem;
    }}
    .plainmed-card.glossary {{ border-left-color: #64748B; }}
    .plainmed-card.gap {{ border-left-color: #D97706; }}
    .plainmed-card h4 {{ margin: 0 0 0.3rem 0; color: {NAVY}; font-size: 0.95rem; }}
    .plainmed-card p {{ margin: 0.2rem 0; font-size: 0.9rem; }}
    .plainmed-badge {{
        display: inline-block;
        font-size: 0.7rem;
        padding: 0.1rem 0.5rem;
        border-radius: 999px;
        background: #E2E8F0;
        color: {NAVY};
        margin-left: 0.4rem;
    }}
    .plainmed-badge.attention {{ background: #FEF3C7; color: #92400E; }}
    .plainmed-source {{ color: #64748B; font-size: 0.75rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _reset_session() -> None:
    for key in ("report_text", "doc", "result", "stage"):
        st.session_state.pop(key, None)
    st.session_state["stage"] = "input"


if "stage" not in st.session_state:
    st.session_state["stage"] = "input"


# ---------------------------------------------------------------- header
left, right = st.columns([3, 1])
with left:
    st.title("PlainMed")
    st.caption("Clear reports. Private by design. · Everything runs on this device.")
with right:
    if st.button("🗑️ Clear session", use_container_width=True):
        _reset_session()
        st.rerun()

st.warning(DISCLAIMER, icon="⚠️")

with st.sidebar:
    st.subheader("About this session")
    st.write(f"PlainMed v{__version__}")
    config = AppConfig()
    st.write(f"Explanation backend setting: `{config.backend}`")
    st.write(
        "Your report is processed locally and kept only in this session's "
        "memory. Use **Clear session** when you are done."
    )
    st.caption(RANGE_CAUTION)


# ---------------------------------------------------------------- stage: input
if st.session_state["stage"] == "input":
    st.subheader("1 · Provide your report")
    tab_paste, tab_pdf = st.tabs(["Paste text", "Upload a text-based PDF"])

    raw_text = None
    source = "pasted"
    error = None

    with tab_paste:
        pasted = st.text_area(
            "Paste the text of your blood-test report",
            height=260,
            placeholder="Hemoglobin: 13.5 g/dL (13.0 - 17.0)\nWBC: 11.2 x10^9/L (4.0 - 11.0) H\n...",
        )
        if st.button("Read pasted text", type="primary"):
            try:
                raw_text = load_text(pasted, max_chars=config.max_report_chars)
            except (EmptyReportError, ReportTooLargeError) as exc:
                error = str(exc)

    with tab_pdf:
        uploaded = st.file_uploader(
            "Upload a PDF that contains selectable text (not a scan)",
            type=["pdf"],
        )
        if uploaded is not None and st.button("Read PDF", type="primary"):
            try:
                raw_text = load_pdf(
                    uploaded.getvalue(),
                    max_pages=config.max_pdf_pages,
                    max_chars=config.max_report_chars,
                )
                source = "pdf"
            except (
                ScannedPdfError,
                EncryptedPdfError,
                PdfTooLargeError,
                EmptyReportError,
                ReportTooLargeError,
            ) as exc:
                error = str(exc)
            except Exception:
                error = "This file could not be read as a PDF."

    if error:
        st.error(error)
    if raw_text is not None:
        st.session_state["report_text"] = raw_text
        st.session_state["doc"] = extract(raw_text, source=source)
        st.session_state["stage"] = "review"
        st.rerun()


# ------------------------------------------------------------- stage: review
elif st.session_state["stage"] == "review":
    doc = st.session_state["doc"]
    st.subheader("2 · Check what PlainMed read")
    st.write(
        "Confirm that the values below match your report before any "
        "explanation is generated. Nothing has been interpreted yet."
    )

    if doc.values:
        st.table(
            [
                {
                    "Source": v.span_id,
                    "Test": v.analyte,
                    "Value": v.raw_value,
                    "Unit": v.unit or "—",
                    "Reference range": v.ref_raw or "not listed",
                    "Report flag": v.flag or "—",
                }
                for v in doc.values
            ]
        )
    else:
        st.info(
            "No test results could be read from this text. You can go back "
            "and paste a clearer version of the report."
        )

    if doc.unparsed_span_ids:
        with st.expander(
            f"{len(doc.unparsed_span_ids)} line(s) could not be read as results"
        ):
            for span_id in doc.unparsed_span_ids:
                span = doc.span_by_id(span_id)
                if span:
                    st.text(f"[{span.id}] {span.text}")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⬅ Start over"):
            _reset_session()
            st.rerun()
    with col_b:
        if doc.values and st.button("This matches my report — explain it", type="primary"):
            with st.spinner("Generating explanations locally..."):
                st.session_state["result"] = analyze(doc, config=config)
            st.session_state["stage"] = "results"
            st.rerun()


# ------------------------------------------------------------ stage: results
elif st.session_state["stage"] == "results":
    doc = st.session_state["doc"]
    result = st.session_state["result"]

    for issue in result.issues:
        if issue.severity == "error":
            st.error(issue.message)
        else:
            st.info(issue.message)

    col_report, col_cards = st.columns([1, 1], gap="large")

    with col_report:
        st.subheader("Original report")
        parsed_spans = {v.span_id for v in doc.values}
        unparsed_spans = set(doc.unparsed_span_ids)
        lines = []
        for span in doc.spans:
            css = (
                "plainmed-parsed"
                if span.id in parsed_spans
                else "plainmed-unparsed"
                if span.id in unparsed_spans
                else ""
            )
            text = html.escape(span.text)
            lines.append(
                f'<div><span class="plainmed-span-id">{span.id}</span>'
                f'<span class="{css}">{text}</span></div>'
            )
        st.markdown(
            f'<div class="plainmed-report">{"".join(lines)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Green: read as a test result. Yellow: not interpreted — review "
            "these lines yourself."
        )

    with col_cards:
        st.subheader("Plain-language explanation")

        if result.narrative:
            st.markdown(
                f'<p class="plainmed-source">Summary '
                f"(backend: {result.narrative.backend})</p>",
                unsafe_allow_html=True,
            )
            for item in result.narrative.items:
                sources = ", ".join(item.span_ids)
                st.markdown(
                    f'<div class="plainmed-card"><p>{html.escape(item.text)}</p>'
                    f'<p class="plainmed-source">Sources: {sources}</p></div>',
                    unsafe_allow_html=True,
                )

        for card in result.cards:
            css = card.kind.value
            badge = ""
            if card.status is not None:
                attention = "attention" if card.status in ATTENTION_STATUSES else ""
                badge = (
                    f'<span class="plainmed-badge {attention}">'
                    f"{html.escape(STATUS_LABELS[card.status])}</span>"
                )
            if card.kind == CardKind.report:
                source_line = "Sources: " + ", ".join(card.span_ids)
            elif card.kind == CardKind.glossary:
                source_line = "Source: PlainMed local glossary"
            else:
                source_line = (
                    "Sources: " + ", ".join(card.span_ids)
                    if card.span_ids
                    else "Not specified in your report"
                )
            body = html.escape(card.body).replace("\n\n", "</p><p>")
            st.markdown(
                f'<div class="plainmed-card {css}">'
                f"<h4>{html.escape(card.title)}{badge}</h4>"
                f"<p>{body}</p>"
                f'<p class="plainmed-source">{source_line}</p></div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Understand and prepare")
    col_quiz, col_questions = st.columns([1, 1], gap="large")

    with col_quiz:
        st.markdown("**Check your understanding**")
        if not result.comprehension_questions:
            st.write("Not enough readable results to build an understanding check.")
        for i, question in enumerate(result.comprehension_questions):
            st.write(f"{i + 1}. {question.question}")
            choice = st.radio(
                "Choose one:",
                question.options,
                index=None,
                key=f"quiz_{i}",
                label_visibility="collapsed",
            )
            if choice is not None:
                if question.options.index(choice) == question.answer_index:
                    st.success("That matches your report.")
                else:
                    st.warning(
                        "That does not match your report. "
                        f"{question.explanation}"
                    )

    with col_questions:
        st.markdown("**Questions to take to your clinician**")
        for question in result.clinician_questions:
            sources = ", ".join(question.span_ids)
            st.markdown(f"- {question.text}  \n  *Sources: {sources}*")

    st.divider()
    if st.button("🗑️ Clear session and remove this report"):
        _reset_session()
        st.rerun()
