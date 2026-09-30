---
scope: "oms/**"
tags: [openness, canonicalization, ingestion]
priority: 9
source: hand-written
---

# oms: the syllable count is read from SEGMENTS, never from letters

A nucleus is one vowel segment. `classify_openness` takes `Canon.segments`, and
two vowel segments are two syllables (hiatus): excluded. Only the source can make
a vowel pair one nucleus — one CLDF token (`m ai`), a tie bar (`wa͡i`), or a
non-syllabic mark (`aɪ̯`).

Before 2026-09-29 `ingest_cldf._ipa` joined `Segments` into one string and the
classifier called any two adjacent vowel letters a high-confidence diphthong.
That admitted 21,812 two-syllable postings of 53,346 — Polynesian `r u a` 'two'
was the flagship "look-alike" in 134 languages. Rebaked: 7,599 shapes, 33,156
postings, 1,358 diphthong postings.

- **Never join tokens before classifying.** An ingester passes the source's
  boundaries as spaces and sets `"segmented": True` on the entry.
- **A source with no Segments is spelling.** It gets a `_RESPELL` entry in
  `ingest_cldf.py` or an `_ORTHOGRAPHIC` exclusion in `scaleout.py` — never
  read as IPA directly. ABVD is respelled (`ng→ŋ`, `'→ʔ`, `y→j`); its vowel
  sequences then split per grapheme and drop out, by decision.
- **Nasals are the exception: segmentation is NOT evidence there.** A bare
  nasal segment before a consonant is flagged contested, never excluded.
  Excluding it (tried 2026-09-29) removed ~350 Tibeto-Burman pre-initial forms
  (`m dz a`, one syllable). See ADR-0001 addendum.
- The Shape key is still the joined string. Two segmentations of one string
  cannot both survive, because only one of them is a single nucleus.

Verify with `python3 -m pytest -q`, then `python3 -m oms.scaleout` and check
that `rua` has no postings in `data/scaled/oms-canon-v1/core.json`.
