"""Two-tier boundary tests.

The commercial argument for a commodity GPU rests on one claim: the model
tier never receives PHI. These tests hold that claim to the wire format
actually sent, not to intent.
"""

import json

import pytest
from fastapi.testclient import TestClient

from plainmed.api.app import create_app
from plainmed.api.security import CONSENT_VERSION
from plainmed.config import AppConfig
from plainmed.llm.remote import RemoteBackend
from plainmed.pipeline import extract

IDENTIFIED = (
    "Patient Name: Jane Q Doe\n"
    "DOB: 04/11/1978  MRN: 88213-4\n"
    "Glucose 108 mg/dL 70-99 H\n"
    "Sodium 140 mmol/L 135-145\n"
)


@pytest.fixture
def model_tier():
    """A client standing in for the GPU tier."""
    with TestClient(create_app(warmup=False)) as c:
        yield c


def test_remote_backend_sends_only_deidentified_lines(monkeypatch):
    """Inspect the actual request body leaving the trusted tier."""
    sent = {}

    class _FakeResponse:
        def read(self):
            return json.dumps({"items": []}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout=None):
        sent["body"] = request.data.decode("utf-8")
        return _FakeResponse()

    monkeypatch.setenv("PLAINMED_MODEL_TIER_URL", "http://model:8001")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    backend = RemoteBackend(AppConfig())
    backend.generate(extract(IDENTIFIED))

    body = sent["body"]
    for identifier in ("Jane", "Doe", "04/11/1978", "88213"):
        assert identifier not in body, f"{identifier!r} was sent to the model tier"
    assert "Glucose" in body and "108" in body


def test_remote_backend_requires_a_configured_url(monkeypatch):
    from plainmed.llm.base import ModelUnavailableError

    monkeypatch.delenv("PLAINMED_MODEL_TIER_URL", raising=False)
    with pytest.raises(ModelUnavailableError):
        RemoteBackend(AppConfig())


def test_model_tier_accepts_deidentified_lines(model_tier):
    response = model_tier.post(
        "/api/v1/internal/generate",
        json={"lines": ["[S1] Glucose 108 mg/dL (ref 70-99) [H]"]},
    )
    assert response.status_code == 200
    assert "items" in response.json()


def test_model_tier_refuses_input_containing_identifiers(model_tier):
    """Defence in depth: a tier that accepts PHI will eventually be sent it."""
    response = model_tier.post(
        "/api/v1/internal/generate",
        json={"lines": ["[S1] Patient Jane Doe DOB 04/11/1978"]},
    )
    assert response.status_code == 422


def test_model_tier_needs_no_session(model_tier):
    """It is reached from the trusted tier, not from a browser."""
    response = model_tier.post(
        "/api/v1/internal/generate",
        json={"lines": ["[S1] Sodium 140 mmol/L (ref 135-145)"]},
    )
    assert response.status_code != 401


def test_model_tier_token_is_enforced_when_set(monkeypatch):
    monkeypatch.setenv("PLAINMED_MODEL_TIER_TOKEN", "s3cret")
    with TestClient(create_app(warmup=False)) as client:
        denied = client.post(
            "/api/v1/internal/generate",
            json={"lines": ["[S1] Sodium 140 mmol/L (ref 135-145)"]},
        )
        assert denied.status_code == 401

        allowed = client.post(
            "/api/v1/internal/generate",
            json={"lines": ["[S1] Sodium 140 mmol/L (ref 135-145)"]},
            headers={"x-plainmed-internal": "s3cret"},
        )
        assert allowed.status_code == 200


def test_statements_from_the_model_tier_are_still_validated(model_tier):
    """A compromised model tier must not be able to inject a claim.

    The trusted tier validates whatever comes back against the source
    document, so an unsupported statement is dropped even though it arrived
    from an internal service.
    """
    from plainmed.pipeline.validate import validate_narrative_items
    from plainmed.schemas import NarrativeItem

    doc = extract(IDENTIFIED)
    hostile = [
        NarrativeItem(text="Your Glucose of 999 means you have diabetes.", span_ids=["S3"]),
        NarrativeItem(text="Your report lists Glucose as 108 mg/dL.", span_ids=["S3"]),
    ]
    kept, issues = validate_narrative_items(hostile, doc)
    assert len(kept) == 1
    assert "108" in kept[0].text
    assert issues
