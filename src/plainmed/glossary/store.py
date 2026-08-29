"""Local, reviewed glossary of common blood-test terms.

Glossary text is the ONLY source for "What this term means..." cards. It is
shipped with the application, versioned in git, and never mixed with report
content or model output.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import resources
from typing import Dict, List, Optional


@dataclass(frozen=True)
class GlossaryEntry:
    key: str
    display_name: str
    aliases: List[str]
    definition: str


def _normalize(term: str) -> str:
    """Lowercase, drop punctuation and parenthesized abbreviations."""
    term = re.sub(r"\([^)]*\)", " ", term)
    term = re.sub(r"[^a-z0-9 ]", " ", term.lower())
    return re.sub(r"\s+", " ", term).strip()


class Glossary:
    def __init__(self, entries: List[GlossaryEntry]):
        self.entries = entries
        self._index: Dict[str, GlossaryEntry] = {}
        for entry in entries:
            for name in [entry.key, entry.display_name, *entry.aliases]:
                self._index[_normalize(name)] = entry

    def lookup(self, term: str) -> Optional[GlossaryEntry]:
        normalized = _normalize(term)
        if not normalized:
            return None
        hit = self._index.get(normalized)
        if hit:
            return hit
        # Also try the abbreviation inside parentheses, e.g. "Hemoglobin (Hgb)".
        paren = re.search(r"\(([^)]{1,15})\)", term)
        if paren:
            hit = self._index.get(_normalize(paren.group(1)))
            if hit:
                return hit
        return None


def load_glossary() -> Glossary:
    raw = (
        resources.files("plainmed.glossary")
        .joinpath("data/glossary.json")
        .read_text(encoding="utf-8")
    )
    payload = json.loads(raw)
    entries = [
        GlossaryEntry(
            key=item["key"],
            display_name=item["display_name"],
            aliases=item.get("aliases", []),
            definition=item["definition"],
        )
        for item in payload["entries"]
    ]
    return Glossary(entries)
