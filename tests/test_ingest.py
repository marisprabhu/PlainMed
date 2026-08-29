import pytest

from plainmed.ingest import (
    EmptyReportError,
    ReportTooLargeError,
    ScannedPdfError,
    load_pdf,
    load_text,
)
from tests.pdf_utils import make_text_pdf


def test_load_text_normalizes_newlines_and_controls():
    text = load_text("Hemoglobin: 13.5\r\nWBC: 5.0\rEnd\x00here")
    assert "\r" not in text
    assert "\x00" not in text
    assert text.splitlines()[0] == "Hemoglobin: 13.5"


def test_load_text_rejects_empty():
    with pytest.raises(EmptyReportError):
        load_text("   \n  ")


def test_load_text_rejects_oversized():
    with pytest.raises(ReportTooLargeError):
        load_text("x" * 101, max_chars=100)


def test_load_pdf_extracts_text():
    pdf = make_text_pdf(
        ["Synthetic lab report", "Hemoglobin: 13.5 g/dL (13.0 - 17.0)"]
    )
    text = load_pdf(pdf)
    assert "Hemoglobin: 13.5 g/dL" in text


def test_load_pdf_rejects_pdf_without_text_layer():
    from pypdf import PdfWriter
    import io

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(ScannedPdfError):
        load_pdf(buffer.getvalue())


def test_pdf_to_parser_roundtrip():
    from plainmed.extract import parse_report

    pdf = make_text_pdf(
        ["SYNTHETIC DATA", "Glucose 108 mg/dL 70-99 High", "Sodium 140 mmol/L 135-145"]
    )
    doc = parse_report(load_pdf(pdf), source="pdf")
    assert [v.analyte for v in doc.values] == ["Glucose", "Sodium"]
