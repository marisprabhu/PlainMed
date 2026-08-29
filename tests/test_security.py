"""Access control, consent, and audit tests.

These cover the controls that make the API safe to expose publicly, and the
evidence trail a HIPAA audit would ask for.
"""

import logging
import time

import pytest
from fastapi.testclient import TestClient

from plainmed.api.app import create_app
from plainmed.api.security import (
    CONSENT_VERSION,
    ConsentRequiredError,
    RateLimiter,
    RateLimitedError,
    issue_session,
    verify_session,
)

REPORT = "Glucose 108 mg/dL 70-99 High\nSodium 140 mmol/L 135-145\n"


@pytest.fixture
def raw_client():
    """A client with no session, for testing the gate itself."""
    with TestClient(create_app(warmup=False)) as c:
        yield c


def _consent(client):
    return client.post(
        "/api/v1/session",
        json={"accepted": True, "consent_version": CONSENT_VERSION, "age_confirmed": True},
    )


# ------------------------------------------------------------------ gate

def test_work_endpoints_require_a_session(raw_client):
    for path, payload in (
        ("/api/v1/scan/text", {"text": REPORT}),
        ("/api/v1/explain", {"document": {}, "corrections": []}),
    ):
        response = raw_client.post(path, json=payload)
        assert response.status_code == 401, path


def test_health_does_not_require_a_session(raw_client):
    """Load balancers cannot present a consent token."""
    assert raw_client.get("/api/v1/health").status_code == 200


def test_session_requires_accepting_consent(raw_client):
    response = raw_client.post(
        "/api/v1/session",
        json={"accepted": False, "consent_version": CONSENT_VERSION},
    )
    assert response.status_code == 400


def test_stale_consent_version_is_refused(raw_client):
    response = raw_client.post(
        "/api/v1/session",
        json={"accepted": True, "consent_version": "1999-01-01"},
    )
    assert response.status_code == 409


def test_consented_session_unlocks_the_api(raw_client):
    token = _consent(raw_client).json()["session"]
    response = raw_client.post(
        "/api/v1/scan/text",
        json={"text": REPORT},
        headers={"x-plainmed-session": token},
    )
    assert response.status_code == 200


def test_health_publishes_the_current_consent_version(raw_client):
    assert raw_client.get("/api/v1/health").json()["consent_version"] == CONSENT_VERSION


# ---------------------------------------------------------------- tokens

def test_tampered_token_is_rejected():
    token = issue_session()
    body, signature = token.split(".", 1)
    with pytest.raises(ConsentRequiredError):
        verify_session(f"{body}x.{signature}")


def test_forged_token_without_signature_is_rejected():
    with pytest.raises(ConsentRequiredError):
        verify_session("eyJzaWQiOiJhdHRhY2tlciJ9.notasignature")


def test_missing_token_is_rejected():
    with pytest.raises(ConsentRequiredError):
        verify_session(None)


def test_expired_session_is_rejected(monkeypatch):
    token = issue_session()
    later = time.time() + 10_000  # well past the one-hour TTL
    monkeypatch.setattr(time, "time", lambda: later)
    with pytest.raises(ConsentRequiredError):
        verify_session(token)


def test_session_carries_no_identifying_information():
    """A session must not become a record of a person.

    'adult' is a boolean assertion that the age gate was satisfied, not a
    date of birth or an age - it evidences the check without recording
    anything about the individual.
    """
    import base64
    import json

    body = issue_session().split(".", 1)[0]
    payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    assert set(payload.keys()) == {"sid", "iat", "cv", "adult"}
    assert payload["adult"] is True


def test_sessions_are_unique():
    assert issue_session() != issue_session()


# ----------------------------------------------------------- rate limits

def test_rate_limiter_allows_a_burst_then_blocks():
    limiter = RateLimiter(rate_per_minute=60, burst=3)
    for _ in range(3):
        limiter.check("k")
    with pytest.raises(RateLimitedError):
        limiter.check("k")


def test_rate_limiter_is_per_key():
    limiter = RateLimiter(rate_per_minute=60, burst=2)
    limiter.check("a")
    limiter.check("a")
    limiter.check("b")  # different key, own budget


def test_rate_limiter_refills_over_time(monkeypatch):
    limiter = RateLimiter(rate_per_minute=60, burst=1)
    limiter.check("k")
    with pytest.raises(RateLimitedError):
        limiter.check("k")
    base = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: base + 5)
    limiter.check("k")


def test_rate_limiter_prunes_idle_buckets():
    limiter = RateLimiter()
    limiter.check("k")
    limiter.prune(max_age_seconds=-1)
    assert limiter._buckets == {}


def test_api_returns_429_with_retry_after(raw_client):
    token = _consent(raw_client).json()["session"]
    headers = {"x-plainmed-session": token}
    codes = [
        raw_client.post(
            "/api/v1/scan/text", json={"text": REPORT}, headers=headers
        ).status_code
        for _ in range(40)
    ]
    assert 429 in codes
    limited = raw_client.post(
        "/api/v1/scan/text", json={"text": REPORT}, headers=headers
    )
    if limited.status_code == 429:
        assert "retry-after" in {k.lower() for k in limited.headers}


# ----------------------------------------------------------------- audit

def test_audit_records_actions_without_report_content(raw_client, caplog):
    token = _consent(raw_client).json()["session"]
    with caplog.at_level(logging.INFO, logger="plainmed.audit"):
        raw_client.post(
            "/api/v1/scan/text",
            json={"text": REPORT},
            headers={"x-plainmed-session": token},
        )
    entries = [r.getMessage() for r in caplog.records if r.name == "plainmed.audit"]
    assert entries, "no audit entries recorded"
    joined = " ".join(entries)
    assert "/scan/text" in joined
    # The audit trail must not itself become a PHI store.
    assert "Glucose" not in joined
    assert "108" not in joined


def test_audit_records_denied_access(raw_client, caplog):
    with caplog.at_level(logging.INFO, logger="plainmed.audit"):
        raw_client.post("/api/v1/scan/text", json={"text": REPORT})
    joined = " ".join(
        r.getMessage() for r in caplog.records if r.name == "plainmed.audit"
    )
    assert "denied_no_consent" in joined


# ------------------------------------------------------------ DPDP: age

def test_session_refused_without_age_confirmation(raw_client):
    """DPDP requires verifiable parental consent for under-18s.

    PlainMed does not implement that, so it excludes under-18s - and the
    exclusion is enforced rather than left as a line in the terms.
    """
    response = raw_client.post(
        "/api/v1/session",
        json={
            "accepted": True,
            "consent_version": CONSENT_VERSION,
            "age_confirmed": False,
        },
    )
    assert response.status_code == 403


def test_token_forged_without_the_adult_claim_is_rejected():
    token = issue_session(age_confirmed=False)
    with pytest.raises(ConsentRequiredError):
        verify_session(token)


def test_audit_records_the_age_denial(raw_client, caplog):
    with caplog.at_level(logging.INFO, logger="plainmed.audit"):
        raw_client.post(
            "/api/v1/session",
            json={
                "accepted": True,
                "consent_version": CONSENT_VERSION,
                "age_confirmed": False,
            },
        )
    joined = " ".join(
        r.getMessage() for r in caplog.records if r.name == "plainmed.audit"
    )
    assert "denied_age" in joined


# ---------------------------------------------------------- DPDP: notice

def test_notice_is_itemised(raw_client):
    """Rule 3 requires the data and its purpose, itemised - not a policy link."""
    body = raw_client.get("/api/v1/notice").json()
    assert body["items"]
    for item in body["items"]:
        assert item["data"] and item["purpose"]


def test_notice_is_available_in_an_eighth_schedule_language(raw_client):
    hindi = raw_client.get("/api/v1/notice?lang=hi").json()
    assert hindi["language"] == "hi"
    assert hindi["title"] != raw_client.get("/api/v1/notice").json()["title"]
    assert "hi" in hindi["available_languages"]


def test_notice_falls_back_to_english_for_unsupported_language(raw_client):
    assert raw_client.get("/api/v1/notice?lang=xx").json()["language"] == "en"


def test_notice_states_withdrawal_and_grievance_and_board(raw_client):
    body = raw_client.get("/api/v1/notice").json()
    assert body["withdraw"] and body["grievance"]
    assert "Data Protection Board" in body["board"]


def test_notice_carries_the_consent_version_the_client_must_send(raw_client):
    assert raw_client.get("/api/v1/notice").json()["consent_version"] == CONSENT_VERSION


def test_production_refuses_a_notice_without_a_grievance_contact(monkeypatch):
    """A placeholder contact reaching a patient is worse than failing loudly."""
    monkeypatch.setenv("PLAINMED_ENV", "production")
    monkeypatch.setenv("PLAINMED_SECRET_KEY", "test-key-for-this-test-only")
    with TestClient(create_app(warmup=False)) as client:
        assert client.get("/api/v1/notice").status_code == 503


def test_all_five_languages_render(raw_client):
    """A language in the picker must actually produce a notice in it."""
    for lang in ("en", "hi", "ta", "zh", "nl"):
        body = raw_client.get(f"/api/v1/notice?lang={lang}").json()
        assert body["language"] == lang, lang
        assert body["items"] and len(body["rights"]) == 5
        assert body["title"] and body["withdraw"] and body["age"]


def test_translated_notices_are_not_english(raw_client):
    """Guards against a language silently falling back and looking fine."""
    english = raw_client.get("/api/v1/notice?lang=en").json()["title"]
    for lang in ("hi", "ta", "zh", "nl"):
        assert raw_client.get(f"/api/v1/notice?lang={lang}").json()["title"] != english
