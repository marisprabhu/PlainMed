"""Delegate narrative generation to a separate model tier.

This is what lets the GPU live somewhere cheap. The trusted tier calls this
backend; this backend sends **de-identified values only** and gets back
statements, which the trusted tier then validates as usual.

Two properties make the arrangement safe:

1. De-identification happens here, before the request leaves the process.
   The remote tier is never sent a ReportDocument, only reconstructed lab
   lines, and ``assert_deidentified`` has already re-checked them.
2. The response is untrusted. It is parsed against a schema here and then
   validated against the source document by the caller, exactly as local
   model output is. A compromised model tier can therefore degrade the
   summary but cannot introduce an unsupported claim.

If the model tier is unreachable or slow, this raises
ModelUnavailableError and the pipeline falls back to the deterministic
backend rather than failing the request.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import List

from pydantic import BaseModel, Field, ValidationError

from plainmed.config import AppConfig
from plainmed.deident import deidentify
from plainmed.llm.base import ModelOutputError, ModelUnavailableError
from plainmed.schemas import NarrativeItem, ReportDocument


class _RemoteResponse(BaseModel):
    items: List[NarrativeItem] = Field(default_factory=list, max_length=20)


class RemoteBackend:
    name = "remote"

    def __init__(self, config: AppConfig):
        self.config = config
        self.url = os.environ.get("PLAINMED_MODEL_TIER_URL", "").rstrip("/")
        if not self.url:
            raise ModelUnavailableError(
                "PLAINMED_MODEL_TIER_URL is not set; no model tier to call."
            )
        # A shared secret so only the trusted tier can reach the model tier.
        # Not a substitute for network isolation - the model tier must not be
        # exposed to the public internet.
        self.token = os.environ.get("PLAINMED_MODEL_TIER_TOKEN", "")
        self.timeout = config.request_timeout_s

    def generate(self, doc: ReportDocument) -> List[NarrativeItem]:
        # De-identify before anything leaves this process. Sending the
        # document itself would defeat the entire tiering argument.
        payload = deidentify(doc)
        if not payload.lines:
            return []

        body = json.dumps({"lines": payload.lines}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["x-plainmed-internal"] = self.token

        request = urllib.request.Request(
            f"{self.url}/api/v1/internal/generate",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ModelUnavailableError(f"Model tier unreachable: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ModelOutputError(f"Model tier returned invalid JSON: {exc}") from exc

        try:
            return _RemoteResponse.model_validate(raw).items
        except ValidationError as exc:
            raise ModelOutputError(
                f"Model tier response did not match the expected schema: {exc}"
            ) from exc
