"""Seed ingestion pipeline (ADR-0002 stages 1-9 over the seed fixture).

Reads seed/seed.json, canonicalizes, classifies openness, dedups into Forms,
tags Confidence Tier + Classification Confidence, attaches Words. Emits the Form
set the BAKE step turns into core.json. This is the corpus-first mechanical core
(IMPLEMENTATION-STRATEGY §9 step 3); real CLDF ingestion swaps in behind the same
Form output at scale (§10 DataStore contract).
"""

from __future__ import annotations

import json
from pathlib import Path

from oms.canon import canonicalize, is_clean_ipa, SCHEME_VERSION
from oms.openness import classify_openness
from oms.features import onset_class, nucleus_bucket
from oms.model import Form, Word, Language, Source, ratchet, tier_better, TIERS

_CC_RANK = {"high": 0, "medium": 1, "low": 2}


def _bipa_conformance(segmental: str) -> float:
    """Cheap CLTS-conformance proxy (same-tier tiebreak Q-N): fraction of tokens
    whose base is a recognized IPA symbol. Production uses pyclts BIPA conformance."""
    from oms.openness import _segment, _VOWELS, _GLIDES
    from oms.features import _NASAL, _STOP, _FRICATIVE, _LIQUID, _IMPLOSIVE, _base
    known = _VOWELS | _GLIDES | _NASAL | _STOP | _FRICATIVE | _LIQUID | _IMPLOSIVE
    toks = _segment(segmental)
    if not toks:
        return 0.0
    return sum(1 for t in toks if _base(t) in known) / len(toks)


def run(seed_path: str | Path) -> dict:
    """Run over a single JSON dataset (back-compat; the seed path)."""
    return run_datasets([json.loads(Path(seed_path).read_text(encoding="utf-8"))])


def run_datasets(datasets: list[dict]) -> dict:
    """Run over one or more datasets (seed JSON and/or CLDF adapters, Phase 5).

    Each dataset is {sources, languages, entries}; they are merged (later datasets
    add languages/entries; the Confidence-Tier ratchet + multi-Source logic dedups
    Forms across datasets exactly as within one)."""
    sources: dict[str, Source] = {}
    languages: dict[str, Language] = {}
    entries: list[dict] = []
    for data in datasets:
        for s in data["sources"]:
            sources[s["id"]] = Source(s["id"], s["tier"], s["license"])
        for l in data["languages"]:
            languages.setdefault(l["glottocode"], Language(**l))
        entries.extend(data["entries"])

    forms: dict[str, Form] = {}
    excluded: list[dict] = []

    for e in entries:
        src = sources[e["source"]]
        canon = canonicalize(e["ipa"])
        if not is_clean_ipa(canon.segmental):   # hygiene: drop reconstruction/cover-symbol/annotation noise
            excluded.append({"ipa": e["ipa"], "glottocode": e["glottocode"],
                             "reason": "non-IPA notation (reconstruction/cover-symbol/annotation)"})
            continue
        op = classify_openness(canon.segmental)
        if not op.is_open:
            excluded.append({"ipa": e["ipa"], "glottocode": e["glottocode"], "reason": op.reason})
            continue

        key = f"{e['glottocode']}|{canon.segmental}"
        f = forms.get(key)
        if f is None:
            f = Form(
                glottocode=e["glottocode"],
                segmental=canon.segmental,
                nucleus_type=op.nucleus_type,
                onset_class=onset_class(canon.segmental),
                nucleus_bucket=nucleus_bucket(canon.segmental, op.nucleus_type),
            )
            forms[key] = f

        # tier ratchets up; sources retained (CONTEXT.md)
        f.tier = ratchet(f.tier, src.tier) if f.sources else src.tier
        if src.id not in f.sources:
            f.sources.append(src.id)
        if canon.tone:
            f.tones.add(canon.tone)

        # Classification Confidence: generated tier -> low/under_review; contested -> medium/under_review
        base_cc = op.confidence
        if f.tier == "generated":
            f.classification_confidence, f.under_review = "low", True
        else:
            # keep the least-confident (most cautious) verdict seen for this form
            cur, new = _CC_RANK[f.classification_confidence], _CC_RANK[base_cc]
            f.classification_confidence = base_cc if new > cur else f.classification_confidence
            f.under_review = f.under_review or op.contested

        # attach Word (homophones collapse on (form,tone); merge gloss_set)
        if e.get("gloss"):
            w = next((w for w in f.words if w.tone == canon.tone), None)
            if w is None:
                w = Word(form_key=key, tone=canon.tone, tier=src.tier)
                f.words.append(w)
            w.tier = ratchet(w.tier, src.tier) if w.sources else src.tier
            if src.id not in w.sources:
                w.sources.append(src.id)
            g = {"gloss": e["gloss"], "concepticon_id": e.get("concepticon_id"), "source_id": src.id}
            if g not in w.gloss_set:   # sources repeat rows (synonym/variant rows); don't ship duplicates
                w.gloss_set.append(g)

    # preferred source per form: best tier, then BIPA-conformance, then id (Q-N)
    for f in forms.values():
        f.preferred_source = min(
            f.sources,
            key=lambda sid: (TIERS.index(sources[sid].tier), -_bipa_conformance(f.segmental), sid),
        )

    form_list = sorted(forms.values(), key=lambda f: (f.glottocode, f.segmental))
    zero_form_langs = [g for g in languages if not any(f.glottocode == g for f in form_list)]

    return {
        "scheme_version": SCHEME_VERSION,
        "languages": languages,
        "sources": sources,
        "forms": form_list,
        "excluded": excluded,
        "zero_form_languages": zero_form_langs,
    }


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parent.parent
    out = run(root / "seed" / "seed.json")
    print(f"scheme:  {out['scheme_version']}")
    print(f"forms:   {len(out['forms'])} open monosyllables across {len(out['languages'])} languages")
    print(f"excluded:{len(out['excluded'])} (closed / vowel-less)")
    print(f"zero-form languages (no-data, ships as Language entry): {out['zero_form_languages']}")
    shapes = {}
    for f in out["forms"]:
        shapes.setdefault(f.segmental, []).append(f.glottocode)
    cross = {s: gs for s, gs in shapes.items() if len(gs) > 1}
    print(f"cross-language shapes (same shape, ≥2 languages): {cross}")
