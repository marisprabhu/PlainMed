"""Tests for OCR line reconstruction.

These use synthetic word boxes rather than real images, so the geometry
logic is tested independently of any OCR engine. This is where a camera
scan most plausibly goes wrong: a value pairing with the wrong row's
reference range would be validated as correct by everything downstream.
"""

from plainmed.ocr.base import OcrWord
from plainmed.ocr.layout import reconstruct_lines


def w(text, x0, y0, x1=None, y1=None, conf=0.99):
    """A word box; defaults give a 20px-tall box of plausible width."""
    if x1 is None:
        x1 = x0 + 10 * len(text)
    if y1 is None:
        y1 = y0 + 20
    return OcrWord(text=text, box=(x0, y0, x1, y1), confidence=conf)


def test_words_group_into_rows_by_vertical_position():
    words = [
        w("Glucose", 10, 100), w("108", 200, 100), w("mg/dL", 300, 100),
        w("Sodium", 10, 140), w("140", 200, 140), w("mmol/L", 300, 140),
    ]
    lines, _ = reconstruct_lines(words)
    assert len(lines) == 2
    assert lines[0].startswith("Glucose")
    assert "108" in lines[0] and "140" not in lines[0]
    assert lines[1].startswith("Sodium")


def test_rows_are_ordered_top_to_bottom_regardless_of_input_order():
    words = [w("Second", 10, 200), w("Third", 10, 300), w("First", 10, 100)]
    lines, _ = reconstruct_lines(words)
    assert lines == ["First", "Second", "Third"]


def test_words_ordered_left_to_right_within_a_row():
    words = [w("mg/dL", 300, 100), w("Glucose", 10, 100), w("108", 200, 100)]
    lines, _ = reconstruct_lines(words)
    assert lines[0].split()[0] == "Glucose"
    assert lines[0].split()[1] == "108"


def test_slightly_misaligned_words_stay_on_one_row():
    # Real OCR boxes on one printed line are never perfectly aligned.
    words = [w("Glucose", 10, 100), w("108", 200, 104), w("High", 300, 97)]
    lines, _ = reconstruct_lines(words)
    assert len(lines) == 1


def test_adjacent_table_rows_do_not_merge():
    # Two rows 30px apart with 20px-tall text must stay separate, or a value
    # would pair with the neighbouring row's reference range.
    words = [
        w("Potassium", 10, 100), w("3.3", 200, 100), w("3.5-5.1", 300, 100),
        w("Chloride", 10, 130), w("102", 200, 130), w("98-107", 300, 130),
    ]
    lines, _ = reconstruct_lines(words)
    assert len(lines) == 2
    assert "3.5-5.1" in lines[0] and "98-107" not in lines[0]
    assert "98-107" in lines[1] and "3.5-5.1" not in lines[1]


def test_column_gaps_produce_wider_separation():
    words = [w("Glucose", 10, 100), w("108", 400, 100)]
    lines, _ = reconstruct_lines(words)
    assert "  " in lines[0]


def test_line_confidence_is_the_minimum_over_digit_words():
    words = [
        w("Glucose", 10, 100, conf=0.99),
        w("108", 200, 100, conf=0.42),
        w("mg/dL", 300, 100, conf=0.95),
    ]
    _, confidences = reconstruct_lines(words)
    assert confidences[0] == 0.42


def test_low_confidence_on_a_word_without_digits_is_ignored():
    """A fuzzy analyte name is harmless; only misread digits are dangerous.

    Scoring whole lines flagged every row on real OCR output, which makes
    the review warning meaningless.
    """
    words = [
        w("Haemoglobin", 10, 100, conf=0.31),  # engine unsure of the name
        w("13.5", 200, 100, conf=0.97),        # but certain of the number
    ]
    _, confidences = reconstruct_lines(words)
    assert confidences[0] == 0.97


def test_line_without_digits_falls_back_to_overall_confidence():
    words = [w("Interpretation", 10, 100, conf=0.44)]
    _, confidences = reconstruct_lines(words)
    assert confidences[0] == 0.44


def test_empty_and_whitespace_words_are_dropped():
    words = [w("Glucose", 10, 100), w("   ", 200, 100), w("108", 300, 100)]
    lines, _ = reconstruct_lines(words)
    assert lines == ["Glucose  108"] or lines[0].replace("  ", " ") == "Glucose 108"


def test_no_words_yields_no_lines():
    assert reconstruct_lines([]) == ([], [])


def test_reconstructed_lines_parse_into_lab_values():
    """The whole point: OCR geometry must feed the existing parser."""
    from plainmed.extract import parse_report

    words = [
        w("Glucose", 10, 100), w("108", 220, 100), w("mg/dL", 300, 100),
        w("70-99", 430, 100), w("High", 540, 100),
        w("Sodium", 10, 140), w("140", 220, 140), w("mmol/L", 300, 140),
        w("135-145", 430, 140),
    ]
    lines, confidences = reconstruct_lines(words)
    doc = parse_report("\n".join(lines), source="camera", line_confidence=confidences)

    assert [v.analyte for v in doc.values] == ["Glucose", "Sodium"]
    glucose = doc.values[0]
    assert glucose.raw_value == "108"
    assert glucose.unit == "mg/dL"
    assert glucose.ref_raw == "70-99"
    assert glucose.flag == "High"


def test_low_confidence_value_is_marked_for_review():
    from plainmed.extract import parse_report

    words = [
        w("Glucose", 10, 100, conf=0.99),
        w("108", 220, 100, conf=0.55),  # a digit the engine was unsure of
        w("mg/dL", 300, 100, conf=0.98),
        w("70-99", 430, 100, conf=0.97),
    ]
    lines, confidences = reconstruct_lines(words)
    doc = parse_report("\n".join(lines), source="camera", line_confidence=confidences)
    assert doc.values[0].needs_review is True


def test_high_confidence_value_is_not_marked_for_review():
    from plainmed.extract import parse_report

    words = [w("Sodium", 10, 100, conf=0.99), w("140", 220, 100, conf=0.97)]
    lines, confidences = reconstruct_lines(words)
    doc = parse_report("\n".join(lines), source="camera", line_confidence=confidences)
    assert doc.values[0].needs_review is False


def test_review_threshold_comes_from_the_recognizing_engine():
    """Confidence scales are not comparable across OCR engines.

    One global constant would flag every row on a conservative engine and
    nothing at all on a bold one, so each backend declares its own.
    """
    from plainmed.extract import parse_report

    strict = parse_report(
        "Glucose 108 mg/dL",
        source="camera",
        line_confidence=[0.70],
        review_threshold=0.80,
    )
    lenient = parse_report(
        "Glucose 108 mg/dL",
        source="camera",
        line_confidence=[0.70],
        review_threshold=0.60,
    )
    assert strict.values[0].needs_review is True
    assert lenient.values[0].needs_review is False


def test_backends_declare_a_review_threshold():
    from plainmed.ocr.rapid import RapidOcrBackend

    assert 0.0 < RapidOcrBackend.review_threshold < 1.0


def test_typed_text_is_never_marked_for_review():
    from plainmed.extract import parse_report

    doc = parse_report("Sodium 140 mmol/L 135-145")
    assert doc.values[0].ocr_confidence is None
    assert doc.values[0].needs_review is False
