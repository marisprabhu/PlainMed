from decimal import Decimal

from plainmed.extract import parse_report
from plainmed.schemas import ValueStatus


def test_colon_format_with_paren_range():
    doc = parse_report("Hemoglobin: 13.5 g/dL (13.0 - 17.0)")
    assert len(doc.values) == 1
    v = doc.values[0]
    assert v.analyte == "Hemoglobin"
    assert v.raw_value == "13.5"
    assert v.value == Decimal("13.5")
    assert v.unit == "g/dL"
    assert v.ref_low == Decimal("13.0")
    assert v.ref_high == Decimal("17.0")
    assert v.flag is None
    assert v.status == ValueStatus.within_range


def test_whitespace_format_with_flag():
    doc = parse_report("WBC  11.8 x10^9/L  4.0-11.0  H")
    v = doc.values[0]
    assert v.unit == "x10^9/L"
    assert v.ref_low == Decimal("4.0")
    assert v.ref_high == Decimal("11.0")
    assert v.flag == "H"
    assert v.status == ValueStatus.flagged_high


def test_word_flag_and_ref_prefix():
    doc = parse_report("Glucose 108 mg/dL Ref: 70-99 High")
    v = doc.values[0]
    assert v.flag == "High"
    assert v.status == ValueStatus.flagged_high
    assert v.ref_raw == "70-99"


def test_report_flag_takes_precedence_over_computed_range():
    # The report's own flag wins even if the numbers disagree.
    doc = parse_report("Potassium 4.0 mmol/L 3.5-5.1 L")
    assert doc.values[0].status == ValueStatus.flagged_low


def test_computed_above_and_below_range():
    doc = parse_report("ALT: 90 U/L (7 - 56)\nAlbumin: 3.0 g/dL (3.5 - 5.0)")
    assert doc.values[0].status == ValueStatus.above_range
    assert doc.values[1].status == ValueStatus.below_range


def test_no_range_status():
    doc = parse_report("Total Cholesterol: 212 mg/dL")
    v = doc.values[0]
    assert v.status == ValueStatus.no_range
    assert v.ref_raw is None


def test_comparator_value_preserved_verbatim():
    doc = parse_report("TSH receptor antibody: <0.1 IU/L")
    v = doc.values[0]
    assert v.raw_value == "<0.1"
    assert v.value is None


def test_percent_unit():
    doc = parse_report("Hematocrit: 41 % (40 - 52)")
    assert doc.values[0].unit == "%"


def test_metadata_and_date_lines_are_not_values():
    text = (
        "Patient Name: Jane Synthetic\n"
        "Collected: 12/03/2026\n"
        "Hemoglobin: 13.5 g/dL (13.0 - 17.0)\n"
    )
    doc = parse_report(text)
    assert [v.analyte for v in doc.values] == ["Hemoglobin"]
    assert len(doc.unparsed_span_ids) == 2


def test_unparsed_lines_are_tracked_not_dropped():
    doc = parse_report("Interpretation pending review\nGlucose 90 mg/dL 70-99")
    assert len(doc.values) == 1
    assert len(doc.unparsed_span_ids) == 1
    span = doc.span_by_id(doc.unparsed_span_ids[0])
    assert "Interpretation" in span.text


def test_spans_offset_into_raw_text():
    text = "Header line\nGlucose 90 mg/dL 70-99"
    doc = parse_report(text)
    for span in doc.spans:
        assert text[span.start : span.end] == span.text


def test_unit_L_is_not_misread_as_flag():
    doc = parse_report("Reticulocytes 60 x10^9/L 25-105")
    v = doc.values[0]
    assert v.flag is None
    assert v.status == ValueStatus.within_range
