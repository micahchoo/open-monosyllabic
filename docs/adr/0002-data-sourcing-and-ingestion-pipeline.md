# Data sourcing & ingestion pipeline

**Status:** accepted (pipeline architecture + Source precedence); sub-decisions flagged Open below.

We ingest lexical/pronunciation data through a **CLDF-standard pipeline** with a fixed **quality-tier Source precedence**, **canonicalize every transcription to CLTS BroadIPA before any matching**, apply the [ADR-0001](0001-open-monosyllable-inclusion-rule.md) openness filter at a defined pipeline stage, and emit **CLDF Forms tagged with a Confidence Tier, a Classification Confidence, and one-or-more Sources**. This closes the #1 gap named by both design audits (`implementation-gaps` §1, `multi-viewpoint-analysis` Priority #1). It is derived from research.md's Stage 1 recommendations.

## Why this is recorded (ADR criteria)

Hard to reverse (the toolchain and CLDF alignment carry lock-in; re-sourcing under a different stack is a rebuild), surprising without context (a reader will ask why G2P is last, not first, when it gives uniform coverage), and the result of a real trade-off (coverage vs. reliability, uniformity vs. honesty).

## Decision

### Source → Confidence Tier

| Tier | Sources (Forms/pronunciations) | Role |
|---|---|---|
| **curated** | **Lexibank** CLDF datasets, **NorthEuraLex** (unified IPA). ~~CELEX~~ **dropped** — LDC license bars redistribution (see Consequences) | primary Form source |
| **mined** | **WikiPron**, **Wiktextract/Kaikki** (mined from Wiktionary; Wiktextract also carries Commons `sounds` audio) | fill where no curated data |
| **generated** | **Epitran** / **Transphone** G2P *engines*, fed by orthographic wordlists **IDS › PanLex › Crubadan › eBible(PD/BY-SA) › Wikipedia-frequency** (ASJP excluded — lossy phonetic reduction, not orthography) | last resort, flagged |

**The generated tier has a double gate:** a language yields Forms only where an *orthographic wordlist* AND a *G2P model for its script* both exist. Form-bearing coverage = **curated ∪ mined ∪ (wordlist ∩ G2P)**; several thousand Glottolog languages (disproportionately mission-priority unwritten ones) yield **zero Forms** and ship as documentation-status / no-data Language entries. (`sourcing-leftovers` spike, closing gaps 1.5/1.6.)

Not a Form source: **PHOIBLE** (segment *inventories*) — used to **validate** which nuclei/tones a language contrasts, not to produce Forms. **Glottolog** (language identity, coordinates, macroarea), **Concepticon** (gloss alignment), **CLTS** (transcription system + canonicalization) are reference catalogs, not Sources.

**Per-language precedence:** for each target language take the **highest-tier Source available**; **retain lower-tier Sources that also exist** (multi-Source, one marked preferred — CONTEXT.md Source). G2P is generated *only where no curated/mined data exists*.

### Tooling stack (adopted — research.md §Execution)

`PyLexibank` / `CLDFBench` wrap each raw Source into CLDF · `segments` + orthography profiles for tokenization · `CLTS` for the fixed transcription system + canonicalization · `LingPy` for syllabification / sonority / prosodic strings · `CL Toolkit` for feature extraction · `Glottolog` / `Concepticon` / `PHOIBLE` as reference/validation.

### Pipeline stages — and where openness & canonicalization compute

```
1. WRAP       raw Source → CLDF (PyLexibank/CLDFBench), linked to Glottolog + Concepticon
2. TOKENIZE   IPA → segments, via a per-Source orthography profile
3. CANONICALIZE  → CLTS BroadIPA under the VERSIONED scheme `oms-canon-v1` (R1–R12; tone split off for the tone-blind Shape key)   ← canonicalization here
4.  PARSE     syllabify; identify nucleus type (vowel / diphthong / syllabic-consonant) + coda presence (LingPy)
4b. ANNOTATE  CLTS/cltoolkit feature join → onset-class + nucleus-type; + the diphthong-vs-glide DECISION FUNCTION over CLTS sound objects (diphthong is a first-class CLTS sound type ≠ glide=consonant), consulting the versioned per-language rule table
5.  FILTER    apply ADR-0001: 1 syllable · vowel/diphthong nucleus · no coda → include;
              set CLASSIFICATION CONFIDENCE {high, medium, low} + under_review flag (high = uncontested; medium = source/expert-resolved; low = editorial-rule; generated tier auto-low/under_review)   ← openness here
6.  TAG       assign CONFIDENCE TIER from the Source table; attach all Sources; set `preferred` deterministically (Q-N: BIPA-conformance rank → exceptions → recency → id); emit per-Source `bipa_conformance`
7.  VALIDATE  check segment inventory against PHOIBLE; for generated (G2P) forms apply the manual spot-check threshold
8.  ATTACH    Language attributes: region/coords (Glottolog), documentation-status, prosodic type / word-minimality
9.  EMIT      canonical CLDF Form set (+ Words/Glosses where available), each Form carrying a per-Form source_license field
```

Openness is computed at **stage 5**, on the **canonicalized, syllabified** form — never on raw source strings. Canonicalization (stage 3) precedes and enables both the Shape identity key and the openness filter.

## Considered options

- **G2P-first for uniform coverage** — rejected. research.md is explicit that G2P errors *concentrate in exactly the vowel/final-segment decisions that determine openness*; a G2P-first pipeline would corrupt the core classification. G2P is last-resort and always `generated`-tagged.
- **Skip canonicalization / raw-string matching** — rejected; fragments Shapes across sources (the identity bug in CONTEXT.md).
- **Merge conflicting sources into one "best" transcription** — rejected; follows PHOIBLE multi-inventory practice instead (retain all, mark preferred).
- **Bespoke non-CLDF store** — rejected; forfeits FAIR reuse and the entire adopted toolchain.

## Consequences

- **Yield is uneven by design** — a language's tier depends on which Source had it; that is why prosodic-type is a first-class Language attribute (so low yield reads as a finding, not noise).
- **Generated forms concentrate on under-documented (Global-South) languages** and are least reliable precisely at the openness-determining segments → they *require* the Classification Confidence signal, the stage-7 spot-check, and the "never rendered as bare fact" UI rule (CONTEXT.md, ux-design.md).
- **Licensing (resolved — `licensing-audit` spike; widened by user decision 2026-07-04).** Originally CC-BY-SA 4.0. Per an explicit user decision ("any CC licence is fine"), the gate now **also accepts CC-BY-NC / CC-BY-NC-SA**, which unblocks large Global-South corpora (Grollemund Bantu 424 langs, Papuan/Vanuatu Voices). Consequence: the catalog's own release licence becomes **CC-BY-NC-SA 4.0** (non-commercial). **ND / NC-ND stay blocked** — "no derivatives" legally forbids the catalog's core act (extracting + republishing canonicalized Forms is a derivative). App code stays MIT; each Form carries a `source_license` (stage 9) so reusers can extract a commercial-safe (CC0/BY/BY-SA-only) subset. **CELEX is dropped** (LDC redistribution ban). Unlicensed Lexibank datasets are **quarantined** behind a Phase-0 allowlist (allow CC0/BY/BY-SA/dual-Wiktionary/MIT/Apache; block NC/ND/research-only). **`NOASSERTION` is not a block — it means the GitHub API didn't read the dataset's `metadata.json`;** clearance reads `metadata.json`'s `license` field (fallback `.zenodo.json` › README › cldf metadata), never the API. The 28 flagged repos resolved to 6 allow / 16 block (mostly CC-BY-NC) / 3 manual / 4 N/A; NC loss concentrates in the **Voices** audio sets. Any audio synthesis engine (e.g. espeak-ng, GPLv3) runs **build-/server-side only**, never linked into shipped app code.
- The pipeline is **re-runnable**; the canonicalization-scheme **version stamps Form keys** so reprocessing doesn't rot deep links. Catalog releases are **cldfbench-version-pinned** ("data as of vN").

## Sub-decisions — resolved by the second spike round (`docs/spikes/`)

- **Versioned canonicalization scheme** → **`oms-canon-v1`** (`canonicalization-scheme` spike): 12-rule table (R1–R12); preserve length/nasalization/syllabicity, strip tone/stress/tie-bars, NFD-normalize before profile tokenization; compound version pin (pyclts + clts-data + profile-set + ruletable). Mechanical except six contested cells (Q-a…Q-f) a linguist ratifies. **Do not** merge contrastive segments (e.g. /a/ vs /ɑ/).
- **Same-tier Source tiebreak** → **minted Q-N** (`same-tier-tiebreak` spike): deterministic `preferred-for-display` pick ranked by CLTS BIPA-conformance rate → linguist exceptions table → intra-Source recency → lexicographic id; escalate-to-manual *only* on same-tier disagreement about the openness verdict or nucleus-vs-coda structure (pure vowel-quality disagreements auto-pick). Supersedes the old `STOP + escalate` stub.
- **Per-case diphthong-vs-glide verdicts** → **specified stage-4b pipeline** (`diphthong-glide-procedure` spike): CLTS decision function + versioned per-language rule table + `(glottocode, pattern)`-keyed review queue (~5–20 seed rulings; generated tier auto-`low`/`under_review`), not per-Form judgment. Its escalation queue shares one review lane with the tiebreak queue.

## Still genuinely open

- **Per-language G2P spot-check threshold** — orthographic depth determines G2P reliability (deep orthographies err most); the manual-review threshold per language is an operational policy TBD (research.md "Thresholds").
- The six `oms-canon-v1` contested cells, the tiebreak exceptions table, and the seed diphthong verdicts — all **human ratification**, retired during the Phase-1 seed run (one shared review queue).
