"""Second-reader verification using MedGemma's vision encoder.

Why a second reader rather than a replacement
---------------------------------------------
MedGemma 1.5 is multimodal and its 1.5 release specifically improves medical
*document* understanding, so the obvious move is to hand it the photo and
skip OCR entirely. That would be a mistake here.

The property PlainMed sells is that numbers are exact: they are parsed
deterministically and every statement is checked against the line it cites.
A language model reading the image directly produces numbers by generation,
and a generated "13.5" cannot be distinguished from a hallucinated one. The
deterministic parser must stay the source of truth.

So the vision model is used the way a second radiologist is used: an
independent reading of the same source, valuable precisely because it can
disagree. Two readers that agree on a value give real confidence. Two that
disagree surface a value a human should look at - which is exactly the
signal the camera path was missing, because OCR confidence tells you how
sure the engine was, not whether it was right.

Disagreement is a flag, never an overwrite. The model cannot change a value;
it can only cause a human to be asked.

Deployment consequence
----------------------
This sends the *image* to the model, and a lab report image carries the
patient's name. That breaks the de-identification boundary that lets the
text path run on a commodity GPU. Vision cross-check therefore runs only on
trusted-tier infrastructure. It is off by default for that reason - see
deploy/ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from plainmed.schemas import LabValue, ReportDocument

log = logging.getLogger("plainmed.verify")

_VISION_PROMPT = """You are reading a photograph of a laboratory report.

For each test name listed below, find it in the image and report the numeric
value printed next to it, exactly as printed. Do not convert units, do not
round, and do not infer a value that is not visible.

If a test is not visible in the image, or you cannot read its value with
confidence, use null. A null is always better than a guess.

Tests to find:
{analytes}

Respond with ONLY a JSON object mapping each test name to the value as a
string, or null:
{{"Test name": "12.3", "Other test": null}}
"""

_NUMBER_RE = re.compile(r"[<>]?\d+(?:\.\d+)?")


@dataclass(frozen=True)
class VisionDisagreement:
    """Two readers, one value, different answers."""

    span_id: str
    analyte: str
    parsed_value: str
    vision_value: Optional[str]
    reason: str


@dataclass
class VisionCheckResult:
    agreed: List[str] = field(default_factory=list)
    disagreements: List[VisionDisagreement] = field(default_factory=list)
    unread: List[str] = field(default_factory=list)
    backend: str = "none"

    @property
    def checked(self) -> int:
        return len(self.agreed) + len(self.disagreements) + len(self.unread)


def _normalise(raw: Optional[str]) -> Optional[Decimal]:
    if raw is None:
        return None
    match = _NUMBER_RE.search(str(raw))
    if not match:
        return None
    token = match.group(0)
    if token.startswith(("<", ">")):
        return None
    try:
        return Decimal(token)
    except InvalidOperation:
        return None


def _parse_response(raw: str) -> Dict[str, Optional[str]]:
    start = raw.find("{")
    if start == -1:
        raise ValueError("vision model returned no JSON object")
    payload, _ = json.JSONDecoder().raw_decode(raw[start:])
    if not isinstance(payload, dict):
        raise ValueError("vision model returned a non-object")
    return {str(k): (None if v is None else str(v)) for k, v in payload.items()}


def build_prompt(values: List[LabValue]) -> str:
    analytes = "\n".join(f"- {v.analyte}" for v in values)
    return _VISION_PROMPT.format(analytes=analytes)


def compare(
    values: List[LabValue], readings: Dict[str, Optional[str]], backend: str = "vision"
) -> VisionCheckResult:
    """Compare deterministic parsing against the vision model's reading.

    Comparison is on numeric equality, not string equality: "13.50" and
    "13.5" are the same reading and should not alarm anyone.
    """
    result = VisionCheckResult(backend=backend)
    lowered = {k.strip().lower(): v for k, v in readings.items()}

    for value in values:
        seen = lowered.get(value.analyte.strip().lower(), "__missing__")
        if seen == "__missing__" or seen is None:
            result.unread.append(value.span_id)
            continue

        ours = _normalise(value.raw_value)
        theirs = _normalise(seen)

        if ours is None or theirs is None:
            # A comparator value like "<0.1" cannot be compared numerically.
            # Fall back to exact string comparison rather than guessing.
            if str(seen).strip() == value.raw_value.strip():
                result.agreed.append(value.span_id)
            else:
                result.disagreements.append(
                    VisionDisagreement(
                        span_id=value.span_id,
                        analyte=value.analyte,
                        parsed_value=value.raw_value,
                        vision_value=str(seen),
                        reason="values could not be compared numerically",
                    )
                )
            continue

        if ours == theirs:
            result.agreed.append(value.span_id)
        else:
            result.disagreements.append(
                VisionDisagreement(
                    span_id=value.span_id,
                    analyte=value.analyte,
                    parsed_value=value.raw_value,
                    vision_value=str(seen),
                    reason="the two readings of this value differ",
                )
            )
    return result


def apply_to_document(
    doc: ReportDocument, result: VisionCheckResult
) -> ReportDocument:
    """Flag disagreements for human review.

    The model never overwrites a parsed value. It can only raise
    ``needs_review``, so the worst a wrong vision reading can do is ask a
    person to look at a value that was already correct.
    """
    flagged = {d.span_id for d in result.disagreements}
    if not flagged:
        return doc
    updated = [
        v.model_copy(update={"needs_review": True}) if v.span_id in flagged else v
        for v in doc.values
    ]
    return doc.model_copy(update={"values": updated})


def cross_check_with_vision(
    doc: ReportDocument, image_bytes: bytes, backend
) -> tuple[ReportDocument, VisionCheckResult]:
    """Read the image with the vision model and compare against the parse.

    Any failure is non-fatal: a second opinion that cannot be obtained
    leaves the first opinion standing, which is the safe direction.
    """
    if not doc.values:
        return doc, VisionCheckResult()

    try:
        raw = backend.read_image(image_bytes, build_prompt(doc.values))
        readings = _parse_response(raw)
    except Exception as exc:
        log.warning("vision cross-check unavailable: %s", type(exc).__name__)
        return doc, VisionCheckResult(backend="unavailable")

    result = compare(doc.values, readings, backend=getattr(backend, "name", "vision"))
    log.info(
        "vision cross-check agreed=%d disagreed=%d unread=%d",
        len(result.agreed),
        len(result.disagreements),
        len(result.unread),
    )
    return apply_to_document(doc, result), result
