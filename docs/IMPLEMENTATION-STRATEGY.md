# Implementation Strategy — Open Monosyllabic

**What this is.** The method and sequence for going from the locked design artifacts to a built system. It is *not* a task list — each phase gets its own detailed plan when it starts. It *is* the meta-level: the ordering principles, phase decomposition, reducibility classification, the mechanical execution system, and the first concrete move. A cold session reads this to know what to build, in what order, and why.

**Inputs (the sole design corpus — nothing here is invented, all derived):**
- [CONTEXT.md](../CONTEXT.md) — domain model (glossary, relationships, lifecycle, identity).
- [docs/adr/0001-open-monosyllable-inclusion-rule.md](adr/0001-open-monosyllable-inclusion-rule.md) — the inclusion rule.
- [docs/adr/0002-data-sourcing-and-ingestion-pipeline.md](adr/0002-data-sourcing-and-ingestion-pipeline.md) — the sourcing/ingestion pipeline (Source→Tier, precedence, stages, where openness computes).
- [docs/ux-design.md](ux-design.md) — the UX/UI decisions.
- [research.md](../research.md) — the linguistics literature survey (data sources, standards, methodological traps).
- [docs/multi-viewpoint-analysis.md](multi-viewpoint-analysis.md) and [docs/implementation-gaps.md](implementation-gaps.md) — the design audit.
- [docs/spikes/](spikes/) — six time-boxed investigations that closed the open gaps (audio, scale/delivery, heatmap bucketing, licensing, sourcing leftovers, map/misc), each web-verified.

**Build-order posture.** The audit's unanimous recommendation was *data-first*. The user chose **UI-first**, made safe by building against a **small real seed dataset** rather than mock. This document encodes that reconciliation: a thin real source slice first, the hero UI on top of it, full scale later.

**Gap-closure.** The gaps in `implementation-gaps.md` have been spiked (`docs/spikes/`); resolutions are folded into the phases below and catalogued in **§11**. Everything that was still "open" at first compile — delivery model, audio, heatmap bucketing, licensing posture — is now **decided**.

**Implementation status.** All five phases have running, tested code against a seed + a CLDF demo dataset (Phase 0 scaffold/licence gate · Phase 1 pipeline, 20 tests · Phase 2 heatmap+map, browser-verified · Phase 3 detail/filters/compare/pages · Phase 4 real espeak-ng audio · Phase 5 CLDF adapter + chunked bake + tripwires). The one step not executed is ingesting the *full real corpus* at scale — the adapter that consumes it is built. See [README.md](../README.md) for the status table and `oms/` for the code.

---

## 1. Ordering principles (derived from the design, not invented)

These are the design's structural constraints, surfaced explicitly. Everything downstream follows from them.

- **P1 — Sources before projections.** CONTEXT.md makes the **Form** the authoritative backbone; Shape, the heatmap, the map, detail, and compare are all *projections* off Forms. A projection built before its source is rework waiting to happen. Build the Form-producing pipeline before any view.
- **P2 — Adopted before invented.** research.md supplies the *proven infrastructure* (CLDF, PyLexibank/CLDFBench, Glottolog, CLTS, WikiPron, Epitran; cldfviz for maps — superseded by d3-geo per the `map-and-misc` spike, §4); ux-design.md supplies the *novel interactions* (heatmap-as-picker, compare, two-axis honesty UI, tiered audio). This adopted-vs-invented split is the strategy's own synthesis (§4), not a distinction research.md itself draws. Ship the adopted data core before gating inventions behind it; a slip on any invention must not block the core.
- **P3 — Highest-assumption-load first.** The keystone is hardest to retrofit: the **canonicalization scheme**, the **openness classifier** (ADR-0001), and the **Form identity key**. These are read off CONTEXT.md's Identity section; compilation derives from them, never redesigns them.
- **P4 — Honesty is a cross-cutting invariant, not a phase.** The two provenance axes (Confidence Tier = source; Classification Confidence = openness call) and the "never a bare count" rule must hold at *every* layer — ingestion tags them, storage carries them, every view renders them. This is a continuous gate (§4), fired by condition, not a milestone.
- **P5 — Seed before scale (the UI-first reconciliation).** UI-first is honored by building a **thin real source slice** (a handful of deliberately-chosen languages) end-to-end first, then the hero UI on it, then scaling ingestion. This keeps P1 intact — the source still precedes its projection — while getting a visible interface early, as the user chose.
- **Gate — Licensing before ingestion.** Audit-derived blocker (implementation-gaps §8 / multi-viewpoint Action #7, *not* research.md): Wiktionary/Wiktextract is CC-BY-SA copyleft; no Source is ingested before its license is cleared (§3).

---

## 2. Phase decomposition

Phases are serial at the phase level; parallelism lives *within* phases. **One deliberate exception honoring UI-first:** once Phase 1 fixes the CLDF Form *schema* (early in the phase), the schema-bound but data-agnostic UI scaffolding (heatmap shell, map component, interaction wiring) may start in parallel with the rest of Phase 1, integrating real seed output when it greens — so UI-first is honored structurally, not just relabeled onto a data-first order. Each phase declares what it builds, what shipping it **validates**, what it explicitly **does not validate** (so phase-N success is never misread as validating unbuilt phase-N+1 work), and the crisp boundary to the next.

### Phase 0 — Foundations & gates
- **Builds:** repo scaffold (CLDF-aligned data layer + web-app shell); apply the two spiked decisions below.
- **Decided by spikes (were open at first compile):**
  - **Delivery = static-baked hybrid** (`scale-and-delivery` spike, §10): one eager core inverted index (≤~1 MB gzip at all scales) + lazy per-shape/lang/concept chunks under a versioned `data/{canon-version}/` path; no request-time backend. Scale estimate (minimality-adjusted): mid ~2,500 langs / ~125k Forms / ~250k Words.
  - **Licensing = release the catalog under CC-BY-SA 4.0** (`licensing-audit` spike): the unavoidable common denominator — NorthEuraLex (a *curated* source) alone forces share-alike, so dropping the mined tier would not buy a permissive catalog. App code stays MIT; emit a per-Form `source_license` field so reusers can extract a permissive-only subset. **DROP CELEX** (LDC redistribution ban — costs only Stage-2 frequency data).
  - **Clearance reads `metadata.json`, never the GitHub licence API** (`lexibank-repo-clearance` spike): `NOASSERTION` means "licence declared in CLDFBench `metadata.json`, unread by the API" — an *unread* list, not a *block* list. The gate reads each dataset's `metadata.json` `license` field (fallback `.zenodo.json` › README › cldf metadata), allows CC0/BY/BY-SA/dual-Wiktionary/MIT/Apache, blocks NC/ND/research-only. The 28 flagged Lexibank repos resolved to **6 allow / 16 block (mostly CC-BY-NC) / 3 manual / 4 N/A**; the NC loss concentrates in the **Voices** audio sets (Vanuatu/Papuan/Amazonian/MixeZoquean) — a bounded, mission-relevant gap worth an upstream re-licensing ask, not a diffuse blocker.
- **Validates:** the legal and architectural ground is safe to build on.
- **Does NOT validate:** any data pipeline or UI. A green scaffold says nothing about whether a Form can be produced.
- **Boundary:** ends when a Source can be legally ingested under the allowlist gate. The delivery model is now decided, so it no longer *blocks* anything — it *shapes* Phase 2's BAKE step (§10).

### Phase 1 — Seed pipeline (the keystone source)  ← the critical path
- **Builds:** the Form-producing pipeline end-to-end (the 9 stages of [ADR-0002](adr/0002-data-sourcing-and-ingestion-pipeline.md), incl. the **stage-4b CLTS/cltoolkit feature-annotation** sub-step that tags onset-class + nucleus-type) for a **small seed set** (~6–10 languages chosen to span the stress axes: well-documented ↔ under-documented, tonal ↔ atonal, simple ↔ complex syllable structure — **include one expected-zero-Forms language** to exercise the no-data path). Includes source ingestion (≥1 curated + 1 mined + G2P, precedence per ADR-0002), **CLTS BroadIPA canonicalization** via the **`oms-canon-v1`** 12-rule scheme (`canonicalization-scheme` spike; compound-version-pinned), the **openness classifier** (ADR-0001, emitting the **Classification Confidence** enum + `under_review` flag via the stage-4b diphthong decision function), **Confidence Tier + multi-Source** tagging with the **deterministic same-tier `preferred` pick** (Q-N, conformance-ranked), and the three **Language attributes** (region/coordinates, documentation-status, prosodic type).
- **Acceptance criterion (stage-2 hazard):** every per-Source orthography profile is audited for **pre-posed-diacritic graphemes** before its Forms are trusted — the `segments` library silently mis-segments them, corrupting exactly the nucleus region that decides openness (`canonicalization-scheme` spike; research.md).
- **Generated-tier input chain** (`sourcing-leftovers` spike): G2P needs *orthographic* wordlists — chain **IDS › PanLex › Crubadan › eBible (PD/BY-SA only) › Wikipedia-frequency** (ASJP **excluded** — it is a lossy 41-symbol phonetic reduction, not orthography, and would merge contrastive segments). Form-bearing coverage = **curated ∪ mined ∪ (wordlist ∩ G2P)**; several thousand Glottolog languages (disproportionately the mission-priority *unwritten* ones) yield **zero Forms** and ship as documentation-status / no-data Language entries — a *designed outcome*, which the scale estimate and Phase 5 must stop counting as Form-bearing.
- **Validates:** that a raw source deterministically becomes a canonical, tier-tagged, classification-scored Form; that canonicalization actually *unifies* the same shape across heterogeneous sources; the **real shape/tier distribution** for the seed (the numbers that tune the heatmap intensity thresholds).
- **Does NOT validate:** scale (full ingestion), any UI, audio. A green seed pipeline says nothing about rendering 2,500 languages.
- **Boundary:** ends when the seed emits a canonical CLDF Form set with both honesty axes populated.

### Phase 2 — The hero surface on the seed
- **Builds:** the **BAKE step** (§10) that turns the seed CLDF into the static core index + chunks; then the **two-level heatmap** (specified by the `heatmap-bucketing` spike — ~9 onset-class rows × ~7 nucleus buckets = 63 cells default; a **class-level cell is a Shape *bucket* that expands in place**, a **segment-level cell is one Shape that picks** — this resolves the old "cell = one Shape" vs "rows = onset class" contradiction and maps 1:1 onto the onset-class filter; intensity = **observed-vs-expected** via the PHOIBLE-inventory × prosodic-type denominator, tier composition always shown, never a bare count); the **d3-geo Equal-Earth map** (three-state present / no-data / structurally-absent; Equal Earth over Mercator so the projection does not visually inflate the Global North); the pick→light browse loop.
- **Validates:** whether the heatmap is *buildable* and its display mechanism *legible* on seed data; whether the honesty display language reads at a glance; the core browse loop.
- **Does NOT validate:** **base-rate / observed-vs-expected legibility under real density** (a handful of seed languages with single-digit cell counts cannot exercise the density phenomenon that makes raw counts mislead — that is validated only in Phase 5, and the encoding stays *provisional-until-scale*); detail/compare/audio surfaces; full-scale rendering performance.
- **Boundary:** ends when a user can pick a shape and see it honestly across the seed languages.

### Phase 3 — Drill, filters, compare, honesty destinations
- **Builds:** Form-detail bottom sheet (two honesty badges, words-as-headline, gloss links); filters (onset-class + complexity, tier — **`generated` never default-hidden, removal-count shown**); compare route (columns, juxtaposition only); About/methodology + Data-sources pages. **Audio-control affordances are built here as inert placeholders** (disabled play buttons wired to a stub) so Phase 4 supplies only the engine and never re-edits these write-targets.
- **Validates:** the full **non-audio** drill path and the honesty-legibility surfaces.
- **Does NOT validate:** working audio (placeholders are inert); scaled ingestion.
- **Boundary:** ends when the whole non-audio product works on the seed.

### Phase 4 — Audio subsystem (additive; retrofits the Phase-3 placeholders)
- **Builds** (specified by the `audio-subsystem` spike): **pre-rendered per-Shape audio** behind an engine-agnostic static-asset seam (`{shape-key}.webm`, canonicalization-version-stamped) — the input set is a finite ~10³–10⁴ canonical syllables, so build-time pre-render (tens of MB) beats on-the-fly synthesis and fits the static delivery model. **Engine:** bootstrap with **espeak-ng** phoneme mode (build-side only — GPLv3, never linked into shipped app code), regenerate with **ToucanTTS** — **Apache-2.0** (repo *and* checkpoints; verified via the licence API — the earlier "MIT" label was a secondary-source mislabel — so generated clips are redistributable under the catalog's CC-BY-SA 4.0; the **ratified primary engine**) once it passes a seed ear-test; the bake emits an Apache-2.0 NOTICE and pins the release tag. **The `recorded` badge is real in v1** via Wiktextract's `sounds` field (Commons audio, already a mined-tier Source; per-file license captured at WRAP); **Lingua Libre** is the named fast-follow. One clip per Shape (tone-blind — the synthesized badge must disclose "tone not rendered"). **Deaf-user path is free**: every synthesized clip derives from the displayed IPA, so visible IPA + plain keyword + tone glyph already carry 100% of the audio signal.
- **Validates:** pervasive tiered audio.
- **Does NOT validate:** catalog correctness — audio is an enhancement; its absence must never block Phases 1–3.
- **Boundary:** ends when audio plays with honest provenance and an accessible fallback.

### Phase 5 — Scale-out ingestion
- **Builds:** expand the Phase-1 pipeline from seed to the full language set. The **automated sourcing order stays quality-tier** (curated → mined → generated); the Global-South-first priority is a **mission-weighted human-effort pass** (spot-checks, recordings, tier upgrades) spent Global-South-first *on top of* the automated order — kept implicit per the locked decision, never relabeled onto the automation. Monitor tier distribution and per-shape density.
- **Validates:** the full catalog at scale; **the heatmap's base-rate / observed-vs-expected legibility under real density** (the property Phase 2 could not, given the tiny seed); whether Phase-2 encoding choices survive real density.
- **Does NOT validate:** (terminal).
- **Boundary:** ships the full Explorer.

---

## 3. Continuous concerns (fire at their condition, not a phase)

- **Honesty invariant gate (P4).** On every view/PR: no bare counts; both provenance axes present and rendered; `generated` shown-not-hidden; **`under_review` (an entry whose openness verdict awaits an expert ruling) renders as a visible "pending review" note, never hidden** — same posture as generated-never-default-hidden. A count that renders as a plain integer fails the gate.
- **Accessibility gate.** On every UI PR: IPA paired with a plain keyword ("as in bed"); ARIA speaks the keyword, not the glyph; keyboard nav for heatmap + map; colorblind-safe encodings with the ● ◐ ○ redundancy.
- **Licensing gate.** On every new Source: license read from its `metadata.json` (not the GitHub API) and cleared before ingestion; share-alike implications recorded on the Data-sources page.
- **Canonicalization-version gate.** Any edit to the **`oms-canon-v1`** rule table (R1–R12) *or* to the pinned `pyclts` / `clts-data` / profile-set versions bumps the compound version and rotates `data/{canon-version}/`, re-stamping Form + Shape keys (protects deep links).

---

## 4. Reducibility classification

The central classifier: *can this work be specified as [pre-written test + donor reference + exact edit + binary acceptance]?* This drives model-tiering, parallelism, and gating.

| Kind | Examples in this project | Donor? | Binary "done"? | Terminus |
|---|---|---|---|---|
| **Adopted** | CLDF scaffolding (PyLexibank/CLDFBench), Glottolog metadata+coordinates, **CLTS/cltoolkit feature annotation** (onset-class + nucleus-type — ADR-0002 stage 4b), WikiPron/Epitran ingestion adapters, **d3-geo Equal-Earth** map rendering | yes | yes | small-model mechanical |
| **Greenfield-specifiable** (code, *after* its corpus/scheme is authored) | canonicalization *normalizer*, openness *classifier*, Form-identity keying, tier-from-Source assignment, count aggregation w/ tier composition, map three-state *logic*, three-state recolor glue | no | yes — **once the corpus exists** | small-model mechanical *after corpus* |
| **Invented / human-authored** | heatmap-as-picker comprehension, compare UX, two-axis honesty *visual language*, **three-state map comprehension** (grok "structurally-absent" vs "no-data"), tiered-audio interaction, editorial visual identity; **+ the authoring prerequisites below** | no | no — "does a user grok it" / a linguist's call | **human gate** |

**Three 'mechanical' items hid a human prerequisite — the second spike round bounded each into a *specified procedure + a finite human queue* (no longer open-ended judgment):**
- **Openness classifier.** The *code* is mechanical; the contested verdicts are now a **specified pipeline** (`diphthong-glide-procedure` spike): a stage-4b decision function over CLTS sound objects (CLTS carries `diphthong` as a first-class sound type), a versioned per-language rule table, and a review queue keyed by `(glottocode, nucleus_pattern)` — **not per Form**, so one ruling fans out across all matching Forms. The human queue is finite (**~5–20 rulings at seed scale**); the generated (G2P) long tail ships `low` / `under_review=auto` and never enqueues a human. Classification Confidence is a concrete enum `{high, medium, low}` + `under_review` flag.
- **Canonicalization.** The *normalizer* is mechanical; the scheme is now **`oms-canon-v1`** (`canonicalization-scheme` spike): a 12-rule table (preserve length/nasalization/syllabicity; strip tone/stress/tie-bars; NFD-normalize before profile tokenization) verified against `pyclts`/CLTS 2.3.0. Mechanical **except six pre-marked contested cells** (Q-a…Q-f) a linguist *ratifies* — a bounded review, not a design-from-scratch.
- **Multi-Source merge** — the same-tier tiebreak is now **minted as a Q-N** (`same-tier-tiebreak` spike): a deterministic `preferred-for-display` pick ranked by the pipeline's own **CLTS BIPA-conformance rate** (a free, objective rigor proxy) → exceptions table → intra-Source recency → lexicographic id. Escalate-to-manual fires *only* on same-tier disagreement about the **openness verdict or nucleus-vs-coda** structure; pure vowel-quality disagreements auto-pick. Its escalation queue **shares one review lane** with the diphthong queue above.
- **Heatmap bucketing fn** — the `heatmap-bucketing` spike **reclassified this from greenfield-after-invented-gate to greenfield-specifiable *now***: the class/bucket mapping corpus is authorable immediately from CLTS feature bundles (~9 onset classes, ~7 vowel buckets); only ~7 intensity-threshold checks wait on Phase-1 seed data. The *structure* no longer waits on a design pass.

**The domain model enumerates the corpus *skeleton*; contested verdicts are now a bounded authored queue.** For the *non-contested* greenfield items, the corpus reads straight off CONTEXT.md + ADR-0001. The *contested* cells — diphthong-vs-glide verdicts (per language+pattern), the six `oms-canon-v1` cells, and the tiebreak exceptions table — are authored by a human into a **single shared review queue**, retired during the Phase-1 seed run, then frozen into the corpus a small model turns green. Build **one** review tool for the shared lane, not two.

**Consequences:**
- Adopted + greenfield-with-*authored*-corpus → parallel small-model executors.
- Invented + every corpus/scheme authoring step → design-/linguistics-skilled human gate, never handed to a mechanical executor.

---

## 5. Deceptively-simple items (earn a corpus before a small model touches them)

Detector: *does the binary "done" test need more than a happy-path case?* Each of these hides an invariant, a mode transition, or a round-trip:

- **Canonicalization / "same string."** The whole Shape-fragmentation bug lives here — now specified as **`oms-canon-v1`** (§4). ⚠️ Do **not** merge contrastive segments: /a/ and /ɑ/ are distinct in CLTS BroadIPA and oppose in real languages — the goal is a stable canonical *per segment*, not collapsing the vowel space. Corpus: source-string → canonical-string pairs = apply R1–R12; contested cells = Q-a…Q-f (linguist-ratified).
- **Openness classifier (ADR-0001).** The diphthong-vs-glide call is the field's hardest and *drives* Classification Confidence — now a **specified stage-4b pipeline** with a bounded per-`(language, pattern)` review queue (~5–20 seed rulings; generated tier auto-`low`), not per-Form judgment (§4). Corpus: forms with expected open/closed + `{high,medium,low}` + `under_review`.
- **Tier ratchet + multi-Source merge.** A mode transition with conflict resolution (retain all, pick preferred). The same-tier tiebreak is now a **minted Q-N** (conformance-ranked deterministic pick; escalate only on openness/nucleus-vs-coda disagreement, §4). Corpus: source-conflict scenarios → expected preferred + retained set.
- **Count aggregation.** Must never be a bare number — the invariant is cross-view. Corpus: mixed-tier inputs → expected composition string.
- **Map three-state.** no-data vs structurally-absent vs present — trivially collapses to two and lies. Corpus: (language attrs × shape presence) → expected state.
- **Heatmap bucketing.** Unbounded axes → renderable grid — **now resolved** (`heatmap-bucketing` spike): two-level drill (class → segment) with a structural home for every awkward shape (V-only = null-onset row; diphthongs = a nucleus column group; CCV+ = a complex-onset row group; non-pulmonic = its own row, never a gutter). Corpus authorable now from CLTS features; only intensity thresholds wait on the seed.
- **Word identity / homophones** (`map-and-misc` spike). Word = (form_id, tone); same-Form same-tone homophones **collapse into one Word** with a merged `gloss_set` (a documented v1 limitation). Corpus: forms with tone+gloss variants → expected Word rows.

---

## 6. Mechanical execution system

Work flows design → done through four roles:

- **Decomposer** (strong model — Cognition): turns a phase into an ordered DAG of leaf tasks, writes each task's acceptance test first. All judgment lives here; runs once per phase. For **UI phases (2, 3, 4)** it invokes `interface-design` so tokens/spacing/depth/patterns constrain UI leaf tasks — a UI leaf without a design-system reference is under-specified.
- **Wave-builder** (mechanical): groups ready tasks whose `write-targets` are disjoint into parallel waves. Computable from the DAG, zero judgment.
- **Executor** (small model — mechanical): receives ONE leaf task; makes its pre-written test green; reports pass/fail. No decomposition, no design, no scope expansion.
- **Verifier** (mid-tier): at wave/phase close, audits that green tests are meaningful (not gamed) and cross-worker seams cohere — including the honesty invariant (§3).

**Leaf-task schema** (fill mechanically, execute mechanically):
```
TASK <id>
  implements:    <ADR / CONTEXT section / ux-design decision>   # cite, don't relitigate
  blocked-by:    [<task ids>]                                   # DAG edge → wave eligibility
  donor:         <file:line> | greenfield-per <corpus ref>      # exact, from Explore/spike
  write-targets: [<exact paths>]                                # wave-disjointness + edit-safety
  change:        <one precise instruction; no design choice left open>
  acceptance:    RUN <exact command> → MUST <binary pass condition>
  on-block:      STOP + escalate; do NOT improvise or expand scope
```
A task a small model can't execute mechanically is **under-specified** — send it back to the decomposer.

---

## 7. Skills, review, and context by level

- **Skills attach where judgment lives** (phases + decomposer + invented work). **Phases 1 & 5 are Adopted + Greenfield-with-corpus (corpus-first TDD)** — `characterization-testing` for the adopted library seams, but the two keystone corpora (canonicalization scheme, openness verdicts) must be **human-authored before any executor** touches the classifier/normalizer; not pure library integration. **Invented phases (2, 3, 4)** invert to design-skilled: `brainstorming` + `interface-design` first, then `gate-enforcer` + human.
- **Infra attaches where execution happens** (leaf tasks): pre-written tests, donor `file:line`, Docs MCP for library signatures, seeds issues as work orders, mulch Q-N for cited decisions, `write-targets` for edit-safety. A leaf needs no skill — it has no judgment by construction.
- **Review at every level:** TASK (test green · stayed in lane · honesty invariant holds) → WAVE (+ do parallel outputs cohere at the seams?) → PHASE (+ Pre-Ship Gate + state externalized for the next session).
- **Context-load tracks judgment:** decomposer reads broad (all ADRs + CONTEXT + relevant audit findings); leaf executor reads narrow (one task spec + one donor + one test). Loading the whole design into a leaf blows context and invites scope creep.

---

## 8. Enumeration strategy (just-in-time, not waterfall)

- **Enumerable now:** Phase 0 gates; Phase 1 pipeline tasks (corpus-defined once the canonicalization + openness corpora are written — the corpus *is* the enumeration); the **heatmap class/bucket mapping** (authorable now from CLTS features, per the spike); the **BAKE step** (index shape decided, §10).
- **Discovered later, only at named boundaries:**
  - Heatmap **intensity-threshold** tuning — after Phase 1 reveals the real distribution (~7 checks, not the whole structure).
  - Audio corpus generation — after the ToucanTTS ear-test on the seed.
  - Scale issues — from Phase-5 measurement events.
  - Any SNAG.
- The task graph is append-mostly; the live frontier is always the next wave + the phase skeleton, never the whole graph up front. Each new task cites what birthed it.

---

## 9. First concrete move

Not "write a plan" — that recurses. The single action that unblocks everything else, the keystone every projection depends on and most expensive to retrofit:

> **Stand up the seed Form pipeline to green.** Concretely, in order — note the first two steps are **Cognition/human**, not mechanical:
> 0. **Select the seed set** (Cognition/human). Pick ~6–10 Glottocodes spanning the stress axes (well- ↔ under-documented, tonal ↔ atonal, simple ↔ complex syllable structure) and **bind each to concrete candidate Sources** (≥1 curated + 1 mined + G2P, precedence per [ADR-0002](adr/0002-data-sourcing-and-ingestion-pipeline.md)). This defines *what* licensing must clear, so it is strictly upstream of everything.
> 1. **Clear licensing** for those now-named Sources (the blocking gate — you cannot ingest what you cannot legally use).
> 2. **Ratify the keystone corpora** (Cognition/human — now *ratification*, not design-from-scratch, thanks to the spikes): sign off the **`oms-canon-v1`** rule table and rule its six contested cells (Q-a…Q-f); author the **~5–20 seed diphthong-vs-glide verdicts** (per language+pattern) and the (initially empty) **same-tier Source exceptions table** — all into the **one shared review queue**. The canonicalization expected-column and the openness corpus fall out of these.
> 3. **Implement the seed pipeline** (mechanical, corpus-first) that ingests the chosen languages, applies the canonicalization normalizer, runs the openness classifier, assigns Confidence Tier + multi-Source, attaches the three Language attributes, and **makes both corpora green** — emitting a canonical CLDF Form set.

The **delivery model is now decided** (static-baked hybrid, §10), so it no longer gates anything — it shapes Phase 2's BAKE step. This is the keystone entity cluster from CONTEXT.md (highest relationship degree — Form — with the richest lifecycle — the tier ratchet and canonical identity). Every other surface projects off it, and until it exists, every heatmap, map, and compare decision is speculative. It also produces the one fact Phase 2 tunes against: the **real shape/tier distribution** behind the heatmap intensity thresholds.

---

## 10. Delivery architecture (decided — `scale-and-delivery` spike)

**Static-baked hybrid, no request-time backend.** A **BAKE** step sits downstream of ADR-0002 stage 9 and emits versioned `data/{canon-version}/` artifacts:

- **`core.json`** — the language table + shape table (with onset-class / nucleus-type per shape) + packed `[langIdx, tier, classificationConfidence (2-bit), under_review (1-bit)]` postings (one flag bit of growth to carry the openness-review state into every view). This *is* the shape→languages **inverted index**; ≤~1 MB gzip even at high scale, fetched once, powering *every* live surface (heatmap recolor, map, tier-composition counts, removal counts, URL state) **client-side**. Storing onset-class/nucleus-type here keeps the heatmap bucketing a client-side groupby.
- **lazy chunks** — `shape/{slug}.json`, `lang/{glottocode}.json`, `concept/{id}.json` (~1.5–30 KB gzip each), fetched on drill-down.
- A **`DataStore` loader contract** lets Phase 2 ship the seed as a single blob and Phase 5 swap in chunking invisibly. **Tripwires:** core index >5 MB gzip → packed *binary* postings (still not a backend); >~15k chunk files on a static host → shard or move data to object storage (R2/S3). Audio clips live in object storage regardless.
- A **live backend is rejected** by the numbers: the dataset is read-only and batch-updated, and the UX hot loop must run over an in-memory aggregate anyway — a backend would have nothing to do that CDN-served static chunks don't do faster. Framework stays loosely held (Astro / SvelteKit static / Next export); the firm decision is the **model**, not the framework.

---

## 11. Gap-closure ledger

Every gap in [implementation-gaps.md](implementation-gaps.md) now has a home; spikes wrote full web-verified reports to [`docs/spikes/`](spikes/).

| Gap | Resolution | Where |
|---|---|---|
| 1.1–1.4 pipeline / Source→Tier / merge | ratified pipeline | ADR-0002 |
| 1.5 G2P input wordlists | IDS › PanLex › Crubadan › eBible › Wiki-freq; ASJP excluded | `spikes/sourcing-leftovers` · Phase 1 |
| 1.6 / 6.2 gloss → Concepticon | v1 = Lexibank-native links only; unmapped = plain text, no cross-link | `spikes/sourcing-leftovers` |
| 2.1 IPA→speech | pre-render per-Shape; espeak-ng → **ToucanTTS (Apache-2.0, verified)** | `spikes/audio-subsystem` · `spikes/toucantts-license` · Phase 4 |
| 2.2 real recordings | Wiktextract `sounds` (v1) + Lingua Libre (fast-follow) | `spikes/audio-subsystem` |
| 3.1 delivery model | static-baked hybrid | `spikes/scale-and-delivery` · §10 |
| 3.2 scale estimate | mid ~2.5k langs / ~125k Forms / ~250k Words | `spikes/scale-and-delivery` |
| 3.3 query substrate | client-side core inverted index | `spikes/scale-and-delivery` · §10 |
| 4.1 tone-blind derivation | **`oms-canon-v1`** 12-rule scheme (6 cells pending ratification) | `spikes/canonicalization-scheme` · ADR-0002 stage 3 |
| 4.2 stable key | canonicalization-version-stamped surrogate key | §3 gate · CONTEXT.md |
| 4.3 Word/tone/gloss storage | Word = (form_id, tone) + `gloss_set`; homophones collapse (v1) | `spikes/map-and-misc` · §5 |
| 5.1 / 5.2 heatmap axes & contradiction | two-level drill grid (class → segment) | `spikes/heatmap-bucketing` · Phase 2 |
| 6.1 words-absent detail | first-class no-words state (Phase 3 design) | ux-design (mission-vs-data) |
| 6.3 spelling→IPA search | build-time ASCII alias index, pure fn of shape string | `spikes/map-and-misc` |
| 7.1 map tech | d3-geo Equal Earth (interactive SVG) | `spikes/map-and-misc` · §4 |
| 8.1 licensing | catalog CC-BY-SA 4.0; drop CELEX; quarantine gate | `spikes/licensing-audit` · Phase 0 |
| 8.2 versioning cadence | cldfbench-pinned versioned builds, "data as of vN" | `spikes/map-and-misc` |
| 8.3 feature annotation | CLTS/cltoolkit as ADR-0002 stage 4b | `spikes/map-and-misc` · ADR-0002 |

### Second spike round — the §11 residuals, now closed

The seven items previously flagged "still open" were spiked into concrete v1 specs or verified facts:

| Item | Resolution | Where |
|---|---|---|
| canonicalization scheme | **`oms-canon-v1`** — 12-rule table at stage 3; preserve length/nasalization/syllabicity, strip tone/stress/tie-bars, NFD-normalize; 6 contested cells (Q-a…Q-f) for ratification | `spikes/canonicalization-scheme` |
| same-tier Source tiebreak | **Q-N (minted)** — deterministic pick ranked by CLTS BIPA-conformance + exceptions table + recency + lexicographic; escalate only on openness / nucleus-vs-coda disagreement | `spikes/same-tier-tiebreak` |
| per-case diphthong-vs-glide | **specified pipeline** — stage-4b CLTS decision fn + per-language rule table + `(glottocode, pattern)`-keyed review queue (~5–20 seed rulings); Classification Confidence `{high,medium,low}` + `under_review`; generated tier auto-`low` | `spikes/diphthong-glide-procedure` |
| ToucanTTS weight licence | **RESOLVED — GO**: Apache-2.0 (repo *and* checkpoints; the "MIT" was a mislabel); clips redistributable under CC-BY-SA 4.0; espeak-ng fallback | `spikes/toucantts-license` |
| ~28 "unlicensed" Lexibank repos | **RESOLVED**: `NOASSERTION` = "`metadata.json` unread", not a block; read it → **6 allow / 16 block (mostly NC) / 3 manual / 4 N/A**; NC loss concentrated in the Voices audio sets | `spikes/lexibank-repo-clearance` |

**What genuinely remains — human *ratification*, not design.** Each is a yes/tweak on a concrete proposal, or a bounded queue retired during the Phase-1 seed run (§9 step 2):
- ratify the `oms-canon-v1` rule table and rule its 6 contested cells (Q-a…Q-f);
- ratify the tiebreak's BIPA-conformance rigor proxy and author the (initially empty) Source exceptions table;
- author the ~5–20 seed diphthong-vs-glide verdicts (into the shared review queue);
- owner risk-acceptance on the standard ToucanTTS open-weights training-data residual;
- one upstream issue each for the 3 manual-check Lexibank repos + an optional re-licensing ask for the four **Voices** datasets (unique small-language coverage + field audio).

**Two prior residuals stand unchanged:** the NorthEuraLex wrapper-vs-authors licence conflict (BY-SA assumed meanwhile); and whether Transphone nearest-language-approximated G2P models are admitted (spike recommends excluding from v1).
