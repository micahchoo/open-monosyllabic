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
data**: five CC-BY Lexibank CLDF datasets cloned and run through the pipeline →
**63 languages · 1,004 open-monosyllable shapes · 819 audio clips**, spanning
Polynesian (Papunesia), Tai-Kadai (China), Kho-Bwa (NE India), and Nepal. A sixth
dataset (Grollemund Bantu, 424 languages) is **correctly blocked** by the Phase-0
licence gate because it is CC-BY-NC — a live demonstration of the ADR-0002 clearance
rule. Fetch more with `git clone --depth 1 https://github.com/lexibank/<name> sources/<name>`
then `python3 -m oms.scaleout`. Full-scale ingestion (WikiPron mining, Epitran G2P
for the unwritten long tail) is the remaining work; the curated-tier CLDF path is live.

| Phase | What | State |
|---|---|---|
| 0 Foundations | scaffold, licence gate (reads `metadata.json`), delivery model | ✓ |
| 1 Seed pipeline | canonicalize → openness → tier/confidence → Form set | ✓ 20 tests |
| 2 Hero surface | two-level heatmap + Equal-Earth map, honesty-first | ✓ browser-verified |
| 3 Drill/filters/compare | detail sheet, onset+tier filters, compare, About/Sources | ✓ browser-verified |
| 4 Audio | real espeak-ng pre-rendered per-Shape clips, synthesized provenance | ✓ 16 clips |
| 5 Scale-out | CLDF ingestion adapter + dataset merge + chunked bake + tripwires | ✓ 5 tests |

```
oms/canon.py       oms-canon-v1 canonicalizer (ADR-0002 stage 3) — tone-blind Shape key
oms/openness.py    openness classifier + Classification Confidence (ADR-0001, one-syllable rule)
oms/features.py    onset-class + nucleus-bucket annotation (stage 4b) — the heatmap axes
oms/model.py       Language / Form / Word, identity keys, Confidence-Tier ratchet
oms/pipeline.py    the 9-stage pipeline; run_datasets() merges seed + CLDF
oms/bake.py        BAKE step (§10): core.json inverted index; single-blob or chunked + tripwires
oms/audio.py       Phase 4: espeak-ng → per-Shape .webm, recorded-vs-synthesized provenance
oms/ingest_cldf.py Phase 5: CLDF Wordlist adapter (reads metadata.json licence)
oms/scaleout.py    Phase 5 driver: merge seed + CLDF, chunked build, tripwire report
seed/seed.json     hand seed (7 languages, incl. a zero-Forms language)
seed/cldf_demo/    CLDF-format demo dataset (Thai/Maori/Swahili) for scale-out
web/               static Explorer: heatmap · map · detail sheet · filters · compare · About · Sources
tests/             canonicalization + openness corpora, pipeline + scale-out invariants (20 tests)
```

## Run it

```bash
python3 -m unittest discover -s tests    # 20 tests
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
(5 cloned under `sources/`), but the *mined* (WikiPron) and *generated* (Epitran G2P)
tiers and the full multi-thousand-language corpus are not yet fetched; canonicalization
is a faithful subset
of the pyclts/CLTS BroadIPA backend the ADR names; feature sets are explicit rather than
the full CLTS join; heatmap intensity uses observed language count (observed-vs-expected
needs real PHOIBLE inventories); `bipa_conformance` is a proxy; ToucanTTS (the ADR's
ratified upgrade) is not wired — espeak-ng is the built baseline behind the same seam.

## Human ratifications still pending (IMPLEMENTATION-STRATEGY §11)

The six `oms-canon-v1` contested cells, the seed diphthong-vs-glide verdicts, and the
tiebreak exceptions table are ratifications retired during a full Phase-1 seed run — the
code implements the *procedures*; a linguist signs off the *verdicts*.
