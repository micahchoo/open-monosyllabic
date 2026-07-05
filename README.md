# Open Monosyllabic

An interactive Explorer for **open monosyllables** — one-syllable words that end in a
vowel — across the world's languages. Pick a sound-shape (e.g. `/ma/`) and see every
language that has it. Built from the design corpus in [`docs/`](docs/): the domain
model ([CONTEXT.md](CONTEXT.md)), the inclusion rule and sourcing pipeline
([ADR-0001](docs/adr/0001-open-monosyllable-inclusion-rule.md),
[ADR-0002](docs/adr/0002-data-sourcing-and-ingestion-pipeline.md)), the UX
([docs/ux-design.md](docs/ux-design.md)), and the build plan
([docs/IMPLEMENTATION-STRATEGY.md](docs/IMPLEMENTATION-STRATEGY.md)).

## Status — all five phases implemented, running on real data

Every phase has running, tested code, and the Explorer now serves **real ingested
data**: 31 sources (CC0/BY/BY-SA/BY-NC/BY-NC-SA cleared) run through the pipeline →
**1,926 languages · 13,819 open-monosyllable shapes · 13,107 audio clips**. The
Phase-0 licence gate was widened (2026-07-04, user decision "any CC licence is
fine") to also admit CC-BY-NC/CC-BY-NC-SA sources — that's how Grollemund Bantu
(424 Bantu languages, CC-BY-NC) cleared and is now part of the served data; the
catalog's own release licence is accordingly CC-BY-NC-SA 4.0 (see
[Sources](web/) in the running app, or `oms/ingest_cldf.py`'s `_ALLOWED` set).
ND / NC-ND sources remain blocked (no-derivatives forbids the catalog's core act
of republishing canonicalized Forms). Fetch more with
`git clone --depth 1 https://github.com/lexibank/<name> sources/<name>` then
`python3 -m oms.scaleout`. Full-scale ingestion (WikiPron mining, Epitran G2P
for the unwritten long tail) is partially live (`wikipron`, `epitran` are already
among the 31 sources); growing the unwritten-language long tail further is the
remaining work.

| Phase | What | State |
|---|---|---|
| 0 Foundations | scaffold, licence gate (reads `metadata.json`), delivery model | ✓ |
| 1 Seed pipeline | canonicalize → openness → tier/confidence → Form set | ✓ 27 tests |
| 2 Hero surface | two-level heatmap + Equal-Earth map, honesty-first | ✓ browser-verified |
| 3 Drill/filters/compare | detail sheet, onset+tier filters, compare, About/Sources | ✓ browser-verified |
| 4 Audio | real espeak-ng pre-rendered per-Shape clips, synthesized provenance | ✓ 13,107 clips |
| 5 Scale-out | CLDF ingestion adapter + dataset merge + chunked bake + tripwires | ✓ 5 tests |

```
oms/canon.py           oms-canon-v1 canonicalizer (ADR-0002 stage 3) — tone-blind Shape key
oms/openness.py        openness classifier + Classification Confidence (ADR-0001, one-syllable rule)
oms/features.py        onset-class + nucleus-bucket annotation (stage 4b) — the heatmap axes
oms/model.py           Language / Form / Word, identity keys, Confidence-Tier ratchet
oms/pipeline.py        the 9-stage pipeline; run_datasets() merges seed + CLDF
oms/bake.py            BAKE step (§10): core.json inverted index; single-blob or chunked + tripwires
oms/audio.py           Phase 4: espeak-ng (+ ToucanTTS seam) → per-Shape .webm, provenance
oms/ingest_cldf.py     Phase 5: CLDF Wordlist adapter (reads metadata.json licence)
oms/ingest_wikipron.py Phase 5: WikiPron mined-tier adapter (word→IPA, no gloss)
oms/fetch_glosses.py   fetches Wiktionary glosses (kaikki.org) for WikiPron-mined forms
oms/toucan_infer.py    optional ToucanTTS subprocess wrapper (falls back to espeak-ng when unset)
oms/scaleout.py        Phase 5 driver: merge seed + CLDF, chunked build, tripwire report
seed/seed.json         hand seed (7 languages, incl. a zero-Forms language)
seed/cldf_demo/        CLDF-format demo dataset (Thai/Maori/Swahili) for scale-out
web/                   static Explorer: heatmap · map · detail sheet · filters · compare · About · Sources
tests/                 canonicalization + openness + wikipron + pipeline + scale-out invariants (27 tests)
```

## Run it

```bash
python3 -m unittest discover -s tests    # 27 tests
python3 -m oms.bake                        # seed build → data/oms-canon-v1/core.json (+ forms.json)
python3 -m oms.audio                       # pre-render per-Shape audio → web/audio/
python3 -m oms.scaleout                    # Phase-5: merge seed + CLDF demo, chunked build + tripwires
python3 -m http.server 8000                # then open http://localhost:8000/web/
```

## What's real vs. seed-stubbed

**Real & tested:** the tone-blind canonicalization (contrastive segments never merged),
the openness rule (diphthongs in, syllabic consonants out, **exactly one syllable**) with
three-level Classification Confidence + `under_review`, cross-language Shape grouping
(`/ma/` in 5 seed languages, `/wai/` in 3 after scale-out), the Confidence-Tier ratchet +
multi-Source + deterministic `preferred` pick, the zero-Forms / no-data language path,
the BAKE inverted index (single-blob and chunked), **real espeak-ng audio**, the **CLDF
ingestion adapter** with the `metadata.json` licence gate, and the honesty-first UI
(tier composition, never a bare count, `generated` shown with a pending badge, three-state
map, no similarity score).

**Seed-stubbed (flagged in code):** real ingestion is live for curated CLDF datasets
plus initial WikiPron (mined) and Epitran (generated) coverage (31 sources cloned
under `sources/`/wired via the adapters), but the full multi-thousand-language
corpus — especially the unwritten long tail — is not yet fetched; canonicalization
is a faithful subset
of the pyclts/CLTS BroadIPA backend the ADR names; feature sets are explicit rather than
the full CLTS join; heatmap intensity uses observed language count (observed-vs-expected
needs real PHOIBLE inventories); `bipa_conformance` is a proxy; ToucanTTS (the ADR's
ratified upgrade) is not wired — espeak-ng is the built baseline behind the same seam.

## Human ratifications still pending (IMPLEMENTATION-STRATEGY §11)

The six `oms-canon-v1` contested cells, the seed diphthong-vs-glide verdicts, and the
tiebreak exceptions table are ratifications retired during a full Phase-1 seed run — the
code implements the *procedures*; a linguist signs off the *verdicts*.
