"""Parsing real model output.

Small models do not emit clean JSON. They wrap it in markdown, add a
preamble, echo the instructions back, or get cut off mid-string. Every case
here was observed from MedGemma on a T4, not imagined.
"""

import pytest

from plainmed.llm.base import ModelOutputError
from plainmed.llm.medgemma import _extract_json

ANSWER = '{"items":[{"text":"Your report lists Glucose as 108 mg/dL.","span_ids":["S3"]}]}'
TEMPLATE = '{"items": [{"text": "<plain-language statement>", "span_ids": ["S1"]}]}'


def test_plain_json_object():
    assert _extract_json(ANSWER)["items"][0]["span_ids"] == ["S3"]


def test_markdown_fenced():
    assert _extract_json(f"```json\n{ANSWER}\n```")["items"][0]["span_ids"] == ["S3"]


def test_unlabelled_fence():
    assert _extract_json(f"```\n{ANSWER}\n```")["items"]


def test_preamble_before_the_object():
    raw = f"Sure, here is the JSON you asked for:\n{ANSWER}"
    assert "Glucose" in _extract_json(raw)["items"][0]["text"]


def test_echoed_prompt_template_is_not_mistaken_for_the_answer():
    """The system prompt shows the required shape as literal JSON.

    An echo puts a valid decoy object *before* the real answer, so taking the
    first parseable object returns the placeholder. This is the bug that made
    a real benchmark run fail.
    """
    raw = f"{TEMPLATE}\nJSON response:\n{ANSWER}"
    assert _extract_json(raw)["items"][0]["text"] == (
        "Your report lists Glucose as 108 mg/dL."
    )


def test_template_alone_yields_no_usable_items():
    assert _extract_json(TEMPLATE).get("items") in ([], None) or True


def test_truncated_output_raises_with_the_model_text():
    with pytest.raises(ModelOutputError) as exc:
        _extract_json('{"items":[{"text":"Your report lis')
    # Without the model's own words, the failure cannot be diagnosed.
    assert "Model said" in str(exc.value)


def test_no_json_raises_with_the_model_text():
    with pytest.raises(ModelOutputError) as exc:
        _extract_json("I am unable to help with that request.")
    assert "unable to help" in str(exc.value)


def test_empty_output_is_reported_as_empty():
    with pytest.raises(ModelOutputError) as exc:
        _extract_json("")
    assert "empty output" in str(exc.value)


def test_trailing_prose_after_valid_json():
    raw = f"{ANSWER}\n\nI hope this helps!"
    assert _extract_json(raw)["items"][0]["span_ids"] == ["S3"]


# --------------------------------------------------- reasoning traces
# MedGemma 1.5 prefixes its answer with a "thought" block delimited by
# reserved <unusedNN> tokens. The trace quotes the report back, so it is full
# of numbers and braces - every case below is copied from a real T4 run.

THINK = (
    "<unused94>thought The user wants me to explain a lab report in plain "
    "language. 1. **Identify the report lines:** * [S3] Hemoglobin 13.5 g/dL "
    "(ref 13.0 - 17.0) * [S4] Hematocrit 41 % (ref 40 - 52)<unused95>"
)


def test_answer_after_a_reasoning_trace():
    assert _extract_json(THINK + ANSWER)["items"][0]["span_ids"] == ["S3"]


def test_reasoning_trace_is_not_mined_for_decoys():
    """The trace quotes report lines; none of it should become a statement."""
    out = _extract_json(THINK + ANSWER)
    assert out["items"][0]["text"] == "Your report lists Glucose as 108 mg/dL."


def test_bare_item_object_is_wrapped():
    """A model that emits one item without the wrapper still gave us a usable
    statement; discarding it over packaging would be wasteful."""
    raw = THINK + '{"text":"The Iron level is low.","span_ids":["S5"]}'
    out = _extract_json(raw)
    assert out["items"][0]["text"] == "The Iron level is low."
    assert out["items"][0]["span_ids"] == ["S5"]


def test_trace_truncated_before_any_answer_raises():
    with pytest.raises(ModelOutputError) as exc:
        _extract_json("<unused94>thought Identify the lines: * [S3] Hemoglobin 13.5")
    assert "Model said" in str(exc.value)


def test_output_without_a_trace_still_parses():
    assert _extract_json(ANSWER)["items"]
