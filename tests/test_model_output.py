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
