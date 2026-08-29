"""Second-reader cross-check tests.

The safety property under test: the vision model can raise a question but
can never change an answer. A wrong second reading costs a user one extra
confirmation; it must never alter a parsed value.
"""

from plainmed.pipeline import extract
from plainmed.verify.vision_check import (
    apply_to_document,
    compare,
    cross_check_with_vision,
)

REPORT = (
    "Glucose 108 mg/dL 70-99 H\n"
    "Sodium 140 mmol/L 135-145\n"
    "Hemoglobin 13.5 g/dL 13.0-17.0\n"
)


class FakeVision:
    """Stands in for MedGemma's vision encoder."""

    name = "fake-vision"

    def __init__(self, response):
        self.response = response
        self.calls = 0

    def read_image(self, image_bytes, prompt):
        self.calls += 1
        self.prompt = prompt
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_agreement_on_every_value():
    doc = extract(REPORT)
    result = compare(
        doc.values,
        {"Glucose": "108", "Sodium": "140", "Hemoglobin": "13.5"},
    )
    assert len(result.agreed) == 3
    assert result.disagreements == []


def test_numeric_equality_not_string_equality():
    """13.50 and 13.5 are the same reading and must not alarm anyone."""
    doc = extract(REPORT)
    result = compare(doc.values, {"Hemoglobin": "13.50"})
    assert "S3" in result.agreed


def test_disagreement_is_detected():
    doc = extract(REPORT)
    result = compare(doc.values, {"Glucose": "168"})
    assert len(result.disagreements) == 1
    assert result.disagreements[0].parsed_value == "108"
    assert result.disagreements[0].vision_value == "168"


def test_value_the_model_could_not_read_is_not_a_disagreement():
    """A null is the model declining to guess, which is the desired behaviour."""
    doc = extract(REPORT)
    result = compare(doc.values, {"Glucose": None, "Sodium": "140"})
    assert "S1" in result.unread
    assert result.disagreements == []


def test_missing_analyte_is_unread_not_disagreement():
    doc = extract(REPORT)
    result = compare(doc.values, {"Sodium": "140"})
    assert len(result.unread) == 2


def test_disagreement_flags_for_review_but_does_not_overwrite():
    """The central safety property of this module."""
    doc = extract(REPORT)
    result = compare(doc.values, {"Glucose": "168"})
    updated = apply_to_document(doc, result)

    glucose = next(v for v in updated.values if v.analyte == "Glucose")
    assert glucose.needs_review is True
    assert glucose.raw_value == "108"  # unchanged - the parser is authoritative


def test_agreement_leaves_the_document_untouched():
    doc = extract(REPORT)
    result = compare(doc.values, {"Glucose": "108", "Sodium": "140", "Hemoglobin": "13.5"})
    assert apply_to_document(doc, result) is doc


def test_cross_check_end_to_end_flags_the_wrong_value():
    doc = extract(REPORT)
    backend = FakeVision('{"Glucose":"168","Sodium":"140","Hemoglobin":"13.5"}')
    updated, result = cross_check_with_vision(doc, b"fake-image", backend)

    assert backend.calls == 1
    assert len(result.disagreements) == 1
    flagged = [v.analyte for v in updated.values if v.needs_review]
    assert flagged == ["Glucose"]


def test_prompt_lists_the_analytes_to_find():
    doc = extract(REPORT)
    backend = FakeVision('{"Glucose":"108"}')
    cross_check_with_vision(doc, b"img", backend)
    for analyte in ("Glucose", "Sodium", "Hemoglobin"):
        assert analyte in backend.prompt


def test_vision_failure_leaves_the_parse_standing():
    """A second opinion that cannot be obtained is not a reason to fail."""
    doc = extract(REPORT)
    updated, result = cross_check_with_vision(
        doc, b"img", FakeVision(RuntimeError("GPU busy"))
    )
    assert result.backend == "unavailable"
    assert [v.raw_value for v in updated.values] == ["108", "140", "13.5"]
    assert not any(v.needs_review for v in updated.values)


def test_unparseable_vision_response_is_survivable():
    doc = extract(REPORT)
    _, result = cross_check_with_vision(doc, b"img", FakeVision("not json at all"))
    assert result.backend == "unavailable"


def test_document_with_no_values_skips_the_model_entirely():
    doc = extract("Some prose with no results.")
    backend = FakeVision("{}")
    _, result = cross_check_with_vision(doc, b"img", backend)
    assert backend.calls == 0
    assert result.checked == 0


def test_comparator_values_compare_as_strings():
    doc = extract("TSH receptor antibody: <0.1 IU/L")
    assert compare(doc.values, {"TSH receptor antibody": "<0.1"}).agreed
    assert compare(doc.values, {"TSH receptor antibody": "<1.0"}).disagreements
