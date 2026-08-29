"""Access control, consent, and audit for the public API.

Design constraint: PlainMed has no accounts and stores nothing. That rules
out per-user authentication, so abuse control has to work without knowing
who anyone is.

Sessions
--------
The client requests a short-lived, signed, anonymous session token. It
carries a random ID, an issue time, and the consent version accepted - no
identity, nothing derived from the user or their report. It is signed with
an HMAC so the server can trust its own claims without storing them.

This gives rate limiting and audit trails per session without creating a
record of a person, which is the point: a system that cannot identify its
users cannot leak their identities.

Consent
-------
Every regime expects evidence that the user agreed before processing began.
With no database, the honest version is: the token records which notice
version was accepted, that the user confirmed being 18 or over, and when.
The API refuses requests whose token predates the current notice, and the
audit log records the assertion against an anonymous session ID.

The age confirmation is not decorative. India's DPDP Act defines a child as
anyone under 18 and requires *verifiable* parental consent - via DigiLocker
or equivalent - before processing their data. Building that is a large
piece of work, so the product excludes under-18s instead, and the exclusion
has to be enforced rather than merely stated in the terms.

What this cannot do is prove *which person* consented - there is no person
on file. That is a deliberate trade, and it must be described accurately in
the notice rather than overstated. See legal/india/README.md.

Audit
-----
HIPAA §164.312(b) requires audit controls. The audit log records session
ID, endpoint, outcome, and timing - never report content, and never
anything identifying. It answers "was the system used as intended" without
becoming a PHI store itself.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

audit_log = logging.getLogger("plainmed.audit")

# Bump when the notice or terms change materially. Tokens issued against an
# older version are rejected, forcing the user to see the new notice.
CONSENT_VERSION = "2026-08-28"

SESSION_TTL_SECONDS = 60 * 60  # one hour: long enough to finish, short enough to expire


class ConsentRequiredError(RuntimeError):
    """No valid session, or consent predates the current version."""


class RateLimitedError(RuntimeError):
    """Too many requests from this session or address."""

    def __init__(self, retry_after: int):
        super().__init__("Too many requests.")
        self.retry_after = retry_after


def _signing_key() -> bytes:
    """Key for session signatures.

    In production this must be set: an ephemeral key invalidates every
    session on restart and differs per replica, so tokens issued by one
    worker would be rejected by another.
    """
    configured = os.environ.get("PLAINMED_SECRET_KEY")
    if configured:
        return configured.encode("utf-8")
    if os.environ.get("PLAINMED_ENV") == "production":
        raise RuntimeError(
            "PLAINMED_SECRET_KEY must be set in production. Without it, "
            "sessions break across restarts and across replicas."
        )
    return _DEV_KEY


_DEV_KEY = secrets.token_bytes(32)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


@dataclass(frozen=True)
class Session:
    sid: str
    issued_at: float
    consent_version: str
    age_confirmed: bool = False


class AgeRequirementError(RuntimeError):
    """The user did not confirm being 18 or over."""


def issue_session(
    consent_version: str = CONSENT_VERSION, age_confirmed: bool = True
) -> str:
    """Mint a signed anonymous session token."""
    payload = {
        "sid": secrets.token_urlsafe(12),
        "iat": time.time(),
        "cv": consent_version,
        "adult": bool(age_confirmed),
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_signing_key(), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64(signature)}"


def verify_session(token: Optional[str]) -> Session:
    """Validate a token's signature, age, and consent version."""
    if not token:
        raise ConsentRequiredError("A session is required.")
    try:
        body, signature = token.split(".", 1)
        expected = hmac.new(
            _signing_key(), body.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_unb64(signature), expected):
            raise ConsentRequiredError("Invalid session.")
        payload = json.loads(_unb64(body))
    except ConsentRequiredError:
        raise
    except Exception as exc:
        raise ConsentRequiredError("Invalid session.") from exc

    issued_at = float(payload.get("iat", 0))
    if time.time() - issued_at > SESSION_TTL_SECONDS:
        raise ConsentRequiredError("This session has expired. Please start again.")
    if payload.get("cv") != CONSENT_VERSION:
        raise ConsentRequiredError(
            "Our terms have been updated. Please review and accept them again."
        )
    if not payload.get("adult"):
        raise ConsentRequiredError(
            "PlainMed is only for people aged 18 or over."
        )
    return Session(
        sid=str(payload.get("sid", "")),
        issued_at=issued_at,
        consent_version=str(payload.get("cv", "")),
        age_confirmed=True,
    )


@dataclass
class _Bucket:
    tokens: float
    updated: float


class RateLimiter:
    """Token-bucket limiter, in memory.

    Single-process only. With more than one replica this limits per replica,
    not globally, so a shared store (Redis) is required before scaling out -
    otherwise the effective limit is N times what you configured.
    """

    def __init__(self, rate_per_minute: int = 20, burst: int = 10):
        self.rate = rate_per_minute / 60.0
        self.burst = burst
        self._buckets: Dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                self._buckets[key] = _Bucket(tokens=self.burst - 1, updated=now)
                return
            elapsed = now - bucket.updated
            bucket.tokens = min(self.burst, bucket.tokens + elapsed * self.rate)
            bucket.updated = now
            if bucket.tokens < 1:
                raise RateLimitedError(retry_after=int(1 / self.rate) + 1)
            bucket.tokens -= 1

    def prune(self, max_age_seconds: float = 3600) -> None:
        """Drop idle buckets so memory does not grow without bound."""
        cutoff = time.monotonic() - max_age_seconds
        with self._lock:
            for key in [k for k, b in self._buckets.items() if b.updated < cutoff]:
                del self._buckets[key]


def record_audit(
    session: Optional[Session],
    action: str,
    outcome: str,
    duration_ms: float = 0.0,
    **counts: int,
) -> None:
    """Append an audit entry.

    Only non-identifying operational facts: which anonymous session did
    what, when, and whether it worked. Never report content, never counts
    that could single out an individual report's contents.
    """
    entry = {
        "ts": time.time(),
        "sid": session.sid if session else "-",
        "action": action,
        "outcome": outcome,
        "duration_ms": round(duration_ms, 1),
        "consent": session.consent_version if session else "-",
        # Evidence that the age gate was satisfied for this session.
        "adult": bool(session.age_confirmed) if session else False,
    }
    entry.update(counts)
    audit_log.info(json.dumps(entry, separators=(",", ":")))
