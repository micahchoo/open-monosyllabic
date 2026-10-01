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


def _loose(segmental: str) -> str:
    """The word with length set aside: ː dropped and doubled letters single.
    Only for spotting that two sources wrote ONE word, never as a key."""
    out = []
    for ch in segmental.replace("ː", ""):
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


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
            sources[s["id"]] = Source(s["id"], s["tier"], s["license"], s.get("kind", "word list"))
        for l in data["languages"]:
            lang = languages.setdefault(l["glottocode"], Language(**l))
            if not lang.family and l.get("family"):   # WikiPron gives none; a CLDF set may
                lang.family = l["family"]
        entries.extend(data["entries"])

    forms: dict[str, Form] = {}
    excluded: list[dict] = []
    # The denominator: distinct canonical words per language that the openness
    # rule judged. A yield means "open forms of N examined" — a 200-word list and
    # a 5,000-word dictionary are not the same sample.
    judged: dict[str, set[str]] = {}
    kinds: dict[str, set[str]] = {}   # which kinds of source the judged words came from
    # tone-marked = most judged words carry tone. Per language the share is
    # bimodal (2026-10-01: 234 languages at 90%+, 2,659 under 10%), and a stray
    # accent is not a tone system: Hindi has 2 marked words of 43,423.
    tone_words: dict[str, list[int]] = {}
    verdicts: dict[tuple, list] = {}

    for e in entries:
        src = sources[e["source"]]
        if e.get("exclude"):   # decided at ingest (spelling with no fixed reading): counted, never examined
            excluded.append({"ipa": e["ipa"], "glottocode": e["glottocode"], "reason": e["exclude"]})
            continue
        canon = canonicalize(e["ipa"], segmented=e.get("segmented", False))
        if not is_clean_ipa(canon.segmental):   # hygiene: drop reconstruction/cover-symbol/annotation noise
            excluded.append({"ipa": e["ipa"], "glottocode": e["glottocode"],
                             "reason": "non-IPA notation (reconstruction/cover-symbol/annotation)"})
            continue
        op = classify_openness(canon.segments)
        judged.setdefault(e["glottocode"], set()).add(" ".join(canon.segments))
        # one word, two sources, two verdicts (ADR-0002 Q-N: escalate): the same
        # meaning in the same language, spelled alike once length is set aside
        # (ABVD maa, Walworth maː) — collected here, flagged after the loop
        concept = e.get("concepticon_id") or (e.get("gloss") or "").strip().casefold()
        if concept:
            loose = _loose(canon.segmental)
            verdicts.setdefault((e["glottocode"], concept, loose), []).append(
                (src.id, op.is_open, f"{e['glottocode']}|{canon.segmental}"))
        kinds.setdefault(e["glottocode"], set()).add(src.kind)
        tw = tone_words.setdefault(e["glottocode"], [0, 0])
        tw[0] += bool(canon.tone)
        tw[1] += 1
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
                onset_class=onset_class(canon.segmental, canon.segments),
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
            g = {"gloss": e["gloss"], "concepticon_id": e.get("concepticon_id"),
                 "concepticon_gloss": e.get("concepticon_gloss"), "source_id": src.id,
                 **({"linked_by": e["linked_by"]} if e.get("linked_by") else {})}
            if g not in w.gloss_set:   # sources repeat rows (synonym/variant rows); don't ship duplicates
                w.gloss_set.append(g)

    disagreements = 0
    for vs in verdicts.values():
        if len({sid for sid, _, _ in vs}) > 1 and len({ok for _, ok, _ in vs}) > 1:
            for _, ok, key in vs:
                if ok and key in forms and not forms[key].under_review:
                    forms[key].under_review = True
                    disagreements += 1

    # preferred source per form: best tier, then BIPA-conformance, then id (Q-N)
    for f in forms.values():
        f.preferred_source = min(
            f.sources,
            key=lambda sid: (TIERS.index(sources[sid].tier), -_bipa_conformance(f.segmental), sid),
        )

    # a language none of whose words could be judged (every row a spelling, a
    # phrase or a reconstruction) says nothing: "0 of 0" is not a data point
    languages = {g: l for g, l in languages.items() if g in judged}

    form_list = sorted(forms.values(), key=lambda f: (f.glottocode, f.segmental))
    zero_form_langs = [g for g in languages if not any(f.glottocode == g for f in form_list)]

    return {
        "scheme_version": SCHEME_VERSION,
        "languages": languages,
        "sources": sources,
        "forms": form_list,
        "excluded": excluded,
        "examined": {g: len(ws) for g, ws in judged.items()},
        "sample": {g: ks.pop() if len(ks) == 1 else "mixed" for g, ks in kinds.items()},
        "tone_marked": {g for g, (k, n) in tone_words.items() if k * 2 >= n},
        "disagreements": disagreements,   # open forms put under review because another source closed them
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
