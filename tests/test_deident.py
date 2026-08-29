"""De-identification tests.

These guard the boundary that decides whether the model tier is processing
PHI. A regression here is not a cosmetic bug: it would send identifiers to
an untrusted tier, so several tests assert on *absence*, and one asserts
that verification raises rather than passing bad text along.
"""

import pytest

from plainmed.deident import (
    DeidentificationError,
    assert_deidentified,
    deidentify,
)
from plainmed.pipeline import extract

IDENTIFIED_REPORT = (
    "CITYLAB DIAGNOSTICS\n"
    "Patient Name: Jane Q Doe\n"
    "DOB: 04/11/1978   MRN: 88213-4\n"
    "Address: 123 Elm Street, Springfield\n"
    "Phone: (555) 213-9987\n"
    "Email: jane.doe@example.com\n"
    "Ordering physician: Dr A Smith\n"
    "Accession: ACC-2026-114\n"
    "Collected: 12/03/2026\n"
    "Glucose 108 mg/dL 70-99 H\n"
    "Sodium 140 mmol/L 135-145\n"
)


def test_no_identifiers_survive_to_the_model():
    text = deidentify(extract(IDENTIFIED_REPORT)).text
    for identifier in (
        "Jane",
        "Doe",
        "04/11/1978",
        "88213",
        "Elm Street",
        "555",
        "example.com",
        "Smith",
        "ACC-2026-114",
        "12/03/2026",
    ):
        assert identifier not in text, f"{identifier!r} leaked to the model"


def test_clinical_content_does_survive():
    """De-identification must not gut the thing the model is for."""
    text = deidentify(extract(IDENTIFIED_REPORT)).text
    assert "Glucose" in text and "108" in text and "70-99" in text
    assert "Sodium" in text and "140" in text


def test_withheld_lines_are_counted():
    result = deidentify(extract(IDENTIFIED_REPORT))
    assert len(result.lines) == 2
    assert result.withheld_line_count == 9


def test_span_ids_are_preserved_so_citations_still_work():
    doc = extract(IDENTIFIED_REPORT)
    result = deidentify(doc)
    for span_id in result.span_ids:
        assert doc.span_by_id(span_id) is not None
    for span_id in result.span_ids:
        assert f"[{span_id}]" in result.text


def test_unparsed_lines_are_withheld_not_forwarded():
    """Anything that did not parse is withheld, including free text that
    might contain a name in a position the parser did not recognise."""
    doc = extract("Comment: call Mrs Henderson about these results\nSodium 140 mmol/L 135-145")
    text = deidentify(doc).text
    assert "Henderson" not in text
    assert "Sodium" in text


def test_a_name_smuggled_into_an_analyte_field_is_dropped():
    """The analyte shape is an allowlist, so free text cannot ride along."""
    doc = extract("Sodium 140 mmol/L 135-145")
    doc.values[0].analyte = "Sodium for patient Jane Doe, DOB 04/11/1978"
    text = deidentify(doc).text
    assert "04/11/1978" not in text


def test_verification_rejects_a_date():
    with pytest.raises(DeidentificationError):
        assert_deidentified(["[S1] Collected 12/03/2026"])


def test_verification_rejects_an_email():
    with pytest.raises(DeidentificationError):
        assert_deidentified(["[S1] contact jane.doe@example.com"])


def test_verification_rejects_an_identifier_label():
    with pytest.raises(DeidentificationError):
        assert_deidentified(["[S1] MRN 88213"])


def test_verification_accepts_clean_clinical_text():
    assert_deidentified(
        ["[S1] Glucose 108 mg/dL (ref 70-99) [H]", "[S2] Sodium 140 mmol/L (ref 135-145)"]
    )


def test_model_prompt_contains_no_identifiers():
    """End-to-end: the actual prompt builder, not just the helper."""
    from plainmed.llm.medgemma import _build_prompt

    prompt = _build_prompt(extract(IDENTIFIED_REPORT))
    for identifier in ("Jane", "Doe", "88213", "Elm Street", "Smith"):
        assert identifier not in prompt


def test_deidentified_report_of_an_empty_document():
    doc = extract("Some prose with no results.")
    result = deidentify(doc)
    assert result.lines == []
    assert result.text == ""
