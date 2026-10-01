"""Typology joins: why a language has many or few open monosyllables.

Two reference datasets, read from sparse clones under sources/ and joined on
glottocode. Neither supplies Forms; they explain the ones we have.

- WALS 12A, Syllable Structure (Maddieson 2013, cldf-datasets/wals, CC-BY-4.0):
  simple (CV only) / moderate / complex. research.md: only the simple group is
  dominated by open syllables, so it should carry the highest rates.
  Re-fetch: git clone --depth 1 --filter=blob:none --sparse
  https://github.com/cldf-datasets/wals sources/wals, then
  git sparse-checkout set --no-cone /cldf/languages.csv /cldf/values.csv

- PHOIBLE 2.0 (cldf-datasets/phoible, CC-BY-SA-3.0): sound inventories. A
  language's inventory says which onset classes and vowel buckets it HAS, so the
  heatmap's chance comparison can count, per cell, only the families whose
  languages could fill it. Inventories of one glottocode are unioned: a sound any
  description lists is a sound the language may have. No PHOIBLE segment is ever
  published as a Form, so share-alike does not reach the catalog.
  Re-fetch as above with https://github.com/cldf-datasets/phoible and /cldf/.
"""

from __future__ import annotations

import csv
from pathlib import Path

from oms.canon import canonicalize
from oms.features import nucleus_bucket, onset_class
from oms.openness import _VOWELS

SYLLABLE_STRUCTURE = {"1": "simple", "2": "moderate", "3": "complex"}


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def wals_syllable_structure(wals_dir: Path) -> dict[str, str]:
    """glottocode -> simple | moderate | complex. Where WALS gives one
    glottocode two values (two doculects), it is left out: no single answer."""
    cldf = wals_dir / "cldf"
    if not (cldf / "values.csv").exists():
        return {}
    gc = {r["ID"]: r["Glottocode"] for r in _rows(cldf / "languages.csv") if r.get("Glottocode")}
    seen: dict[str, set[str]] = {}
    for r in _rows(cldf / "values.csv"):
        if r["Parameter_ID"] == "12A" and r["Language_ID"] in gc and r["Value"] in SYLLABLE_STRUCTURE:
            seen.setdefault(gc[r["Language_ID"]], set()).add(SYLLABLE_STRUCTURE[r["Value"]])
    return {g: v.pop() for g, v in seen.items() if len(v) == 1}


def segment_classes(segment: str, segment_class: str) -> tuple[str | None, str | None]:
    """(onset class, vowel bucket) one inventory segment contributes, through
    the same canon + feature functions the Forms go through."""
    canon = canonicalize(segment, segmented=True)   # one inventory entry = one segment
    seg = canon.segmental
    if not seg:
        return None, None
    if segment_class == "consonant":
        o = onset_class(seg, canon.segments)
        return (o if o not in ("none", "other") else None), None
    if segment_class == "vowel":
        vowels = sum(1 for ch in seg if ch in _VOWELS)
        return None, nucleus_bucket(seg, "diphthong" if vowels > 1 else "monophthong")
    return None, None   # tone


def phoible_inventories(phoible_dir: Path) -> dict[str, dict[str, list[str]]]:
    """glottocode -> {"onsets": [...], "nuclei": [...]} from every inventory."""
    cldf = phoible_dir / "cldf"
    if not (cldf / "values.csv").exists():
        return {}
    klass = {r["ID"]: r["SegmentClass"] for r in _rows(cldf / "parameters.csv")}
    memo: dict[tuple[str, str], tuple] = {}
    inv: dict[str, tuple[set, set]] = {}
    for r in _rows(cldf / "values.csv"):
        key = (r["Value"], klass.get(r["Parameter_ID"], ""))
        if key not in memo:
            memo[key] = segment_classes(*key)
        o, n = memo[key]
        ons, nucs = inv.setdefault(r["Language_ID"], (set(), set()))
        if o:
            ons.add(o)
        if n and n != "other":
            nucs.add(n)
    return {g: {"onsets": sorted(o), "nuclei": sorted(n)} for g, (o, n) in inv.items() if o and n}


def attach(languages: dict, root: Path) -> tuple[int, int]:
    """Set syllable_structure and inventory on each Language that the reference
    data covers. Returns (languages with WALS 12A, languages with an inventory)."""
    wals = wals_syllable_structure(root / "sources" / "wals")
    phoible = phoible_inventories(root / "sources" / "phoible")
    for g, lang in languages.items():
        lang.syllable_structure = wals.get(g, "")
        lang.inventory = phoible.get(g)
    return (sum(1 for g in languages if g in wals), sum(1 for g in languages if g in phoible))
