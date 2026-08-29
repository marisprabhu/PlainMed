from plainmed.extract import parse_report
from plainmed.pipeline.validate import validate_cards, validate_narrative_items
from plainmed.schemas import CardKind, ExplanationCard, NarrativeItem


DOC = parse_report("Hemoglobin: 13.5 g/dL (13.0 - 17.0)\nGlucose 108 mg/dL 70-99 High")


def test_valid_item_passes():
    items = [
        NarrativeItem(
            text="Your report lists Hemoglobin as 13.5 g/dL.", span_ids=["S1"]
        )
    ]
    kept, issues = validate_narrative_items(items, DOC)
    assert len(kept) == 1
    assert issues == []


def test_unknown_span_id_is_rejected():
    items = [NarrativeItem(text="Something.", span_ids=["S99"])]
    kept, issues = validate_narrative_items(items, DOC)
    assert kept == []
    assert issues[0].code == "unknown_source"


def test_number_not_in_cited_passage_is_rejected():
    items = [
        NarrativeItem(text="Your hemoglobin is 14.2 g/dL.", span_ids=["S1"])
    ]
    kept, issues = validate_narrative_items(items, DOC)
    assert kept == []
    assert issues[0].code == "number_mismatch"


def test_number_from_wrong_line_is_rejected():
    # 108 exists in the report, but not in the cited passage S1.
    items = [NarrativeItem(text="Your value is 108.", span_ids=["S1"])]
    kept, _ = validate_narrative_items(items, DOC)
    assert kept == []


def test_equivalent_decimal_forms_match():
    items = [
        NarrativeItem(text="Hemoglobin is 13.50 g/dL.", span_ids=["S1"])
    ]
    kept, issues = validate_narrative_items(items, DOC)
    assert len(kept) == 1


def test_forbidden_claim_is_rejected():
    items = [
        NarrativeItem(
            text="Your Glucose of 108 means you have diabetes.", span_ids=["S2"]
        )
    ]
    kept, issues = validate_narrative_items(items, DOC)
    assert kept == []
    assert any(i.code == "forbidden_claim" for i in issues)


def test_treatment_advice_is_rejected():
    items = [
        NarrativeItem(
            text="You should take a supplement for this.", span_ids=["S1"]
        )
    ]
    kept, issues = validate_narrative_items(items, DOC)
    assert kept == []
    assert any(i.code == "forbidden_claim" for i in issues)


def test_forbidden_word_allowed_when_report_itself_says_it():
    doc = parse_report("Note: discussed diagnosis at last visit\nGlucose 90 mg/dL 70-99")
    items = [
        NarrativeItem(
            text="Your report notes a diagnosis was discussed.", span_ids=["S1"]
        )
    ]
    kept, issues = validate_narrative_items(items, doc)
    assert len(kept) == 1
    assert issues == []


def test_glossary_cards_skip_report_number_check():
    cards = [
        ExplanationCard(
            kind=CardKind.glossary,
            title="What Vitamin B12 means",
            body="Vitamin B12 is needed to make red blood cells.",
        )
    ]
    kept, issues = validate_cards(cards, DOC)
    assert len(kept) == 1
    assert issues == []


def test_report_card_with_wrong_number_is_rejected():
    cards = [
        ExplanationCard(
            kind=CardKind.report,
            title="Hemoglobin",
            body="Your report lists Hemoglobin as 15.0 g/dL.",
            span_ids=["S1"],
        )
    ]
    kept, issues = validate_cards(cards, DOC)
    assert kept == []
    assert issues[0].code == "number_mismatch"
