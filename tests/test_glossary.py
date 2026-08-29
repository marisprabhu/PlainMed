from plainmed.glossary import load_glossary


def test_lookup_by_display_name_and_alias():
    glossary = load_glossary()
    assert glossary.lookup("Hemoglobin").key == "hemoglobin"
    assert glossary.lookup("HGB").key == "hemoglobin"
    assert glossary.lookup("haemoglobin").key == "hemoglobin"


def test_lookup_with_parenthesized_abbreviation():
    glossary = load_glossary()
    assert glossary.lookup("Hemoglobin (Hgb)").key == "hemoglobin"
    assert glossary.lookup("Something Unknown (TSH)").key == "tsh"


def test_lookup_unknown_term_returns_none():
    glossary = load_glossary()
    assert glossary.lookup("Reticulocyte hemoglobin equivalent") is None
    assert glossary.lookup("") is None


def test_definitions_make_no_diagnostic_claims():
    from plainmed.safety import forbidden_hits

    glossary = load_glossary()
    for entry in glossary.entries:
        assert forbidden_hits(entry.definition) == [], entry.key
