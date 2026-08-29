"""Safety wording and content rules.

The report text is untrusted data. The model's output is untrusted until
validated. These constants centralize the wording and checks that keep both
of those true in the UI.
"""

from __future__ import annotations

import re

DISCLAIMER = (
    "Research prototype. May make mistakes. Explains report content; "
    "does not diagnose or recommend treatment. "
    "Confirm interpretation with a qualified clinician."
)

GLOSSARY_SOURCE_NOTE = (
    "This explanation comes from PlainMed's local glossary, not from your report."
)

RANGE_CAUTION = (
    "A value inside a reference range is not by itself a statement about "
    "health, and ranges can differ between laboratories."
)

# Phrases the application must never generate on its own. A match is allowed
# only when the same text already appears in the cited report passage (i.e.
# the report itself says it); otherwise the statement is rejected.
FORBIDDEN_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bdiagnos\w*",
        r"\byou\s+(?:have|are\s+suffering|likely\s+have)\b",
        r"\bthis\s+means\s+you\s+have\b",
        r"\b(?:start|stop|take|increase|decrease)\s+(?:taking\s+)?(?:your\s+)?\w*\s*(?:medication|medicine|drug|dose|supplement)s?\b",
        r"\byou\s+should\s+(?:not\s+)?(?:take|use|start|stop)\b",
        r"\bnothing\s+to\s+worry\s+about\b",
        r"\bdangerous\b",
        r"\byou\s+are\s+(?:healthy|fine|sick|ill)\b",
    )
]


def forbidden_hits(text: str, allowed_context: str = "") -> list[str]:
    """Return forbidden phrases found in ``text``.

    A hit is excused when the exact matched text already occurs in
    ``allowed_context`` (the cited report passages), because then the
    statement is quoting the report rather than inventing a claim.
    """
    context_lower = allowed_context.lower()
    hits = []
    for pattern in FORBIDDEN_PATTERNS:
        for match in pattern.finditer(text):
            if match.group(0).lower() not in context_lower:
                hits.append(match.group(0))
    return hits
