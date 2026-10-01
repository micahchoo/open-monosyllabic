"""Link unlinked glosses to Concepticon by their English gloss (roadmap item 9).

WikiPron words get meanings from Wiktionary as free English ("water", "to go"),
with no Concepticon id, so 'water' from Yoruba and WATER from a word list were
two meanings. A gloss is linked only when the match cannot mean two things:

- its text, without a leading "to"/"a"/"an"/"the", equals one Concepticon gloss;
- no other Concepticon concept shares that head word ("nail": NAIL and
  NAIL (TOOL); "cold": four senses) — those stay unlinked;
- "to X" links only to an action, "a/an/the X" only to a thing ("to fire" is
  not FIRE, "To smart" is not SMART);
- the concept is already in the catalog from a source that linked it itself, so
  a link only ever merges a gloss into a meaning curated data already has.

A linked gloss keeps `linked_by: "gloss"`, so the UI can say how it was joined.
Data: concepticon/concepticon-data (CC-BY-4.0), a sparse clone at
sources/concepticon-data (only concepticondata/concepticon.tsv).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

_LEAD = re.compile(r"^(to|a|an|the)\s+", re.I)
_QUAL = re.compile(r"\s*\(.*\)$")
# what a leading word says the gloss is, as Concepticon's ONTOLOGICAL_CATEGORY
_LEAD_CATEGORY = {"to": "Action/Process", "a": "Person/Thing", "an": "Person/Thing", "the": "Person/Thing"}


def _norm(gloss: str) -> tuple[str, str | None]:
    """(gloss without its leading word, the category that word demands)."""
    g = gloss.strip()
    m = _LEAD.match(g)
    return _LEAD.sub("", g).strip().casefold(), _LEAD_CATEGORY[m.group(1).lower()] if m else None


def load(path: Path) -> dict[str, tuple[int, str, str]]:
    """casefolded gloss -> (id, GLOSS, category), only for unambiguous, current concepts."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t") if not r.get("REPLACEMENT_ID")]
    heads: dict[str, int] = {}
    for r in rows:
        h = _QUAL.sub("", r["GLOSS"]).casefold()
        heads[h] = heads.get(h, 0) + 1
    return {r["GLOSS"].casefold(): (int(r["ID"]), r["GLOSS"], (r.get("ONTOLOGICAL_CATEGORY") or "").strip())
            for r in rows
            if heads[_QUAL.sub("", r["GLOSS"]).casefold()] == 1}


def link(datasets: list[dict], table: dict[str, tuple[int, str, str]]) -> int:
    """Set concepticon_id on unlinked entries whose gloss matches; returns how many."""
    curated = {e["concepticon_id"] for ds in datasets for e in ds["entries"] if e.get("concepticon_id")}
    n = 0
    for ds in datasets:
        for e in ds["entries"]:
            if e.get("concepticon_id") or not e.get("gloss"):
                continue
            word, wants = _norm(e["gloss"])
            hit = table.get(word)
            if hit and hit[0] in curated and (wants is None or hit[2] == wants):
                e["concepticon_id"], e["concepticon_gloss"], e["linked_by"] = hit[0], hit[1], "gloss"
                n += 1
    return n
