# Multi-Viewpoint Design Review — Open Monosyllabic

Synthesis of six independent lens reports plus the separate `docs/implementation-gaps.md` audit,
over the four design docs (`CONTEXT.md`, `docs/adr/0001`, `docs/ux-design.md`, `research.md`).
No code exists yet — this reviews the design before the build.

The six lenses: **linguistic-rigor**, **data-honesty**, **broad-audience-accessibility**,
**mission-fidelity**, **scope-minimalism**, **scholarly-power-use**.

---

## Executive Summary

- **The data model is the strong part; the hero surface is the weak part.** Every lens praises the same spine — separate-per-language Forms, query-time Shape (no stored relatedness), the no-similarity-score decision citing Ringe/Tresoldi, and the tiered provenance honesty axis. The criticism converges just as hard on one object: the onset×vowel **raw cross-language count heatmap** that the design makes the hero.
- **Four lenses independently condemn the hero count**, and implementation-gaps says it is literally unbuildable as specced (unbounded axes, "cell = one Shape" contradicts "rows = onset class"). This is the single highest-confidence finding in the review.
- **The whole UX is designed before any data exists.** research.md's own Stage 1/2/3 gate is not honored: the pipeline, the "open" classifier, and the transcription level are surveyed but never committed. Scope-minimalism and implementation-gaps both say the design is a bet on a data distribution nobody has measured.
- **The Confidence Tier certifies the *source of the IPA string*, not the *openness classification* the tool itself applies** — the single most theory-dependent decision (diphthong-vs-glide, "can double or halve a language's yield") is invisible to the user. Three lenses want a second, orthogonal confidence axis.
- **Shape identity ("exact string match") has no defined canonicalization.** Without CLTS BroadIPA normalization, /ma/ from Lexibank and /ma/ from Epitran silently become different Shapes and the hero feature under-counts. The derivation *is* the identity function and it is undefined.
- **The Global-South-first priority is one sentence and is encoded nowhere** — not in the model, sourcing order, or any surface. Worse, every flagship experience (density heatmap, words-as-headline, pervasive audio, gloss links) rewards exactly the data richness the priority languages lack, and the quality-first sourcing order routes them straight to the least-reliable "generated" tier.
- **Two whole subsystems are assumed but undesigned:** audio (no synthesis engine, no recording archive named) and the ingestion pipeline (no datasets/order/tooling committed). A licensing blocker (Wiktextract is CC-BY-SA copyleft) is unexamined.
- **IPA-as-hero is a wall for the stated broad audience** and has no screen-reader, keyboard, or deaf-user story for its two headline channels (IPA text and audio).

---

## Cross-Lens Consensus

Ranked by how many independent lenses flagged it (consensus = confidence).

### C1. The raw cross-language count heatmap is misleading and/or unbuildable — **5 signals**
*linguistic-rigor · data-honesty · mission-fidelity · scholarly-power · implementation-gaps*

- **rigor:** bright cells are just the unmarked high-frequency CV segments present by base rate; no chance/expected-count baseline, so intensity is not interpretable — the base-rate trap sitting in the hero after being carefully excluded from compare (`ux-design.md §Landing`; `research.md §4`).
- **honesty:** the cell count silently sums verified+mined+generated; "47 languages" could be 40 machine-guesses. The most prominent number in the app has zero honesty signal (`ux-design.md §Landing`).
- **mission:** density rewards well-documented (Global-North) languages and renders priority languages as empty cells — the showcase inverts the mission's ordering (`ux-design.md §Landing 17-18`).
- **scholarly:** research.md's headline caveat is that per-language yield is structurally biased, so "counts are not directly comparable"; the hero presents exactly these uncontrolled counts as the payoff (`research.md §Caveats`).
- **implementation-gaps §5:** onset and vowel axes are unbounded across languages; a hundreds×dozens matrix is neither renderable nor glanceable, and diphthongs / V-only / CCV shapes have no home on a 2-D onset×vowel grid.

### C2. Word-minimality / prosodic type must be a first-class Language attribute — **4 lenses**
*linguistic-rigor · data-honesty · mission-fidelity · scholarly-power* (research.md Rec 4)

Absence of a dot / a low cell conflates three distinct things — the language *structurally bans* the shape (a real typological finding), the shape *isn't sourced yet*, or a *parse failure*. Without the minimality variable the central metric is uninterpretable and the map libels under-documented languages. The Language entity currently carries only a Glottocode.

### C3. Confidence Tier certifies source, not the openness classification — **3 lenses**
*linguistic-rigor · data-honesty · scholarly-power* (reinforced by implementation-gaps §1.3)

The diphthong-vs-glide + coda call — which ADR-0001 admits "can double or halve a language's yield" and is "a known hard case" — is applied to every entry regardless of tier and is invisible. Errors concentrate exactly in the vowel/final region that *defines* openness. One badge hides the higher-stakes uncertainty.

### C4. No committed transcription level / Shape canonicalization — **3 signals**
*linguistic-rigor · scholarly-power · implementation-gaps §4.1*

"segmental IPA" is never pinned to CLTS BroadIPA + versioned orthography profiles — which research.md Rec 3 calls "the single highest-leverage quality step." Since "sameness is exact string match," this derivation IS the identity function; if it changes, every Form key, deep link, and compare pin rots (implementation-gaps §4.2).

### C5. The map conflates "no data" with "shape structurally absent" — **3 lenses**
*linguistic-rigor · data-honesty · mission-fidelity*

Absence-of-evidence renders as evidence-of-absence, and it falls hardest on exactly the under-documented Global-South languages the mission prioritizes. Needs an explicit third "no data" rendering.

### C6. Single Source per entry is weaker than the field standard — **2 lenses**
*data-honesty · scholarly-power*

PHOIBLE deliberately retains conflicting inventories; the ratchet-up-only model discards the losing inventory as data. When sources disagree on whether /ma/ exists, the model silently picks a winner. Store multiple Sources per Form; make "ratchet" mean *preferred display*, never deletion.

### C7. Audio is a large, wholly unaddressed dependency — **2 lenses + gaps**
*scope-minimalism (cut it) · broad-audience (deaf users need a visual channel) · implementation-gaps §2*

No IPA-to-speech engine and no recording archive is named anywhere; the recorded-vs-synthesized honesty axis collapses to a constant if every clip is synthesized.

### C8. The Global-South priority is aspirational, not architectural — **mission + honesty + gaps**

The "generated" tier concentrates on the priority languages, and their inclusion itself is a machine guess (`data-honesty`); the words-as-headline detail view is empty for exactly the hero audience (`implementation-gaps §6.1`).

---

## Sharpest Conflicts

### K1. Build the UX now vs build the data first
**Viewpoints:** scope-minimalism (design is premature) vs the five lenses that critique/extend the UX as if it ships.

**Trade-off:** scope-minimalism says freeze `ux-design.md` as a v2 vision, run research.md Stage 1, and let real per-language yield and tier mix decide whether the hero is a heatmap, a list, or a map. Crucially, **linguistic-rigor and implementation-gaps independently agree the heatmap may be uninterpretable *and* unbuildable** — which strengthens scope's sequencing argument beyond mere minimalism.

**Resolution:** Scope-minimalism wins on sequencing. Ship Stage 1 (a CLDF dataset of Forms-per-Language with tier + Source) before committing the hero visualization. Most of C1's fixes (base-rate coloring, minimality normalization) are moot or trivial depending on whether cells turn out densely or sparsely populated. **This is not a compromise — the other lenses' fixes are cheaper and better-targeted after the data exists.**

### K2. IPA-as-hero vs the broad audience that can't read IPA
**Viewpoints:** broad-audience-accessibility (IPA is a wall; demote it) vs linguistic-rigor + scholarly-power + the editorial "IPA as hero" visual identity.

**Trade-off:** the stated audience "mostly can't read IPA," yet the load-bearing entry object is an onset×vowel IPA matrix and IPA is declared the visual identity. Rigor/scholarly need IPA precision; accessibility needs everyday words and sound.

**Resolution:** Not mutually exclusive. Keep IPA as the *canonical* layer but make it an **annotated enhancement**: every glyph on axes, cells, and headers carries a plain keyword ("/ɛ/ — as in bed") and inline audio; ARIA grid semantics speak the keyword, not the raw glyph. Costs editorial purity and build effort; serves accessibility without sacrificing rigor. IPA becomes the thing users grow into, not the gate they must pass.

### K3. Hide "generated" by default vs never hide the Global-South data — **GENUINE HUMAN DECISION**
**Viewpoints:** data-honesty (default the tier filter to verified+mined; generated is opt-IN) vs mission-fidelity (the tier filter is "a Global-South erase button" — most under-documented-language data IS generated-tier).

**Trade-off:** both lenses are protecting the *same* priority languages and pull in opposite directions. Honesty: a casual user must never see a machine-guess counted as fact. Mission: defaulting generated OFF makes the prioritized languages vanish from the first impression — the mission's languages erased in the name of honesty.

**Resolution — HUMAN DECISION, with a recommended synthesis:** Do **not** default-hide generated. Instead, (a) never render a generated entry as a bare fact — carry the classification-confidence signal (K/C3) inline and per-entry, (b) show tier composition on every count so "47" is never alone, and (c) when a user *does* filter out generated, show a count of what/where it removes ("hides 213 forms across 68 languages, mostly S-Asia/Africa"). This keeps the priority languages visible (mission) while never laundering a guess as fact (honesty). The human must decide the default filter state; the synthesis leans mission-visible-with-honesty-signal over honesty-by-subtraction.

### K4. Make the priority visible vs keep the editorial tone neutral — **GENUINE HUMAN DECISION**
**Viewpoints:** mission-fidelity (ship a coverage/equity view + About statement so the priority is auditable) vs the design's explicit choice to keep the priority "implicit… not foregrounded," partially backed by scope-minimalism (cut the extra surface).

**Trade-off:** mission-fidelity's point is sharp — a priority with no data-model and no interface presence "is indistinguishable from not having the priority at all." But the design deliberately conflated *neutral tone* with *invisible accountability*.

**Resolution:** Separate the two axes, which dissolves most of the conflict: keep the editorial tone factual/neutral (no advocacy copy) **and** add the structural accountability mission needs — region/macroarea + documentation-status as Language attributes (cheap, also serves C2/C5), plus a coverage view showing tier-distribution-by-macroarea. Whether the coverage view ships in v1 or as a fast-follow is the human call; the *attributes* should be non-negotiable because four other findings depend on them.

### K5. Scholarly power features vs scope-minimalism vs lay simplicity
**Viewpoints:** scholarly-power (export/CLDF/DOI, multi-source provenance, nucleus/tone/family/area/minimality filters, gated SCA/LexStat research mode) vs scope-minimalism (cut compare, gloss-links, most filters, URL state) vs broad-audience (fewer entry paths, plainer vocabulary).

**Trade-off:** scholarly wants *more* power surfaces; scope and accessibility want *fewer*. All three are legitimate for different users.

**Resolution:** Sequence, don't choose. v1 ships the honesty-load-bearing minimum (tier filter, About/Data-sources, a browsable shape→language view). **Data export (CSV/CLDF) and dataset versioning/DOI are the exception** — they are cheap once the CLDF dataset exists (K1 produces it anyway) and turn a dead-end website into reusable infrastructure, so pull them forward. Advanced filters and gated research-mode (SCA/LexStat *with* a mandatory null baseline — which resolves the apparent conflict with the no-similarity-score rule, since scholarly explicitly wants it *gated*, not ungated) go in an advanced drawer as fast-follows. Costs scholarly some immediacy; serves scope and accessibility now.

### K6. Diphthong-IN inclusion rule vs count neutrality
**Viewpoints:** linguistic-rigor + mission-fidelity (the rule inflates diphthong-rich Global-North yield and is presented as ground truth) vs ADR-0001's deliberate single-analysis simplicity (backed by scope-minimalism).

**Trade-off:** ADR-0001 correctly rejected the "track both analyses, user-filterable" option as too much complexity — scope agrees. But the chosen analysis silently sets every count with no signal that numbers shift under a strict CVG reading.

**Resolution:** Don't reopen the toggle (scope wins there). Instead **annotate**: tag diphthong-derived Forms so a future strict/inclusive view stays cheap, and label counts as "attested-in-our-data / analysis-relative," not a neutral census. Low cost, keeps ADR-0001's rejected option revivable, keeps the numbers honest.

---

## Per-Lens Highlights

**linguistic-rigor** — The model is claim-free but the rhetoric isn't: a "payoff" that "lights up" at page load frames chance co-occurrence of short shapes as discovery — the exact naive inference Ringe warns of, staged before any methodology page is seen. Fix the hero with a base-rate defense (observed-vs-expected coloring) and make minimality a real variable.

**data-honesty** — Honesty is strongest where it costs nothing (a removed compare score, secondary pages) and weakest where the eye lands (the hero count). "Verified" is the strongest false claim in the vocabulary — it asserts an entry-level check nobody performed; rename to *curated/attested*. Move provenance out from behind hover to the point of consumption.

**broad-audience-accessibility** — Real seeds (colorblind-safe scale, ●◐○ redundancy, list fallback, plain-spelling search, "surprise me") but the two headline channels — IPA text and audio — have no non-visual and no non-auditory path. No screen-reader model for IPA, no map data-table equivalent, no deaf-user respelling, no responsive/mobile story for a dual-pane dense grid.

**mission-fidelity** — The priority is one sentence, encoded nowhere; the sourcing order (Lexibank/NorthEuraLex → WikiPron → Epitran) routes Global-South languages to the generated tier *by construction*. Add region + documentation-status attributes, a coverage view, and spend mission-weighted human effort (spot-checks, recordings) Global-South-first while keeping quality-tier automation order.

**scope-minimalism** — The UX is a fully-walked six-surface product speced with zero data; ~half is deferrable. MVP = one heatmap-or-list of shape→languages-with-tier-badge, plus the honesty pages. Cut (in cost order): audio, compare route, gloss-links, live map (use a static PNG), URL state, extra filters, extra entry paths, editorial font system. Re-derive the hero after Stage 1 numbers exist.

**scholarly-power-use** — Right standards backbone (Glottocode, Concepticon, provenance tiers) but stops at "trustworthy display," never crossing to "reusable data": no export, no versioning/DOI, no programmatic access, and single-Source provenance is weaker than PHOIBLE. As specced it's a citable-*looking* website, not a citable dataset. Add CLDF export + DOI + multi-source retention + a gated research mode with a mandatory chance baseline.

---

## Prioritized Actions

Ordered most-important first. Tags: **serves** / **costs** the named values.

### 1. Build research.md Stage 1 data first; ratify the pipeline as an ADR
Enumerate exact datasets + versions, the tool reading each, the precedence/merge order, and the Source→Tier table. **No hero-visualization decision is real until this produces the actual shape and tier distribution.**
- **serves:** scope-minimalism, linguistic-rigor, data-honesty, scholarly-power, implementation-gaps (§1)
- **costs:** mission-fidelity (quality-first order deprioritizes Global-South) — *mitigate by layering a Global-South-first human-effort pass on top of the automated order (see #6)*

### 2. Fix Shape identity: canonicalize to CLTS BroadIPA before string-match
Pin the transcription level, enumerate exactly which diacritics/tone/length/nasalization marks are stripped, and make it a versioned key (surrogate ID, not the raw string) so reprocessing doesn't rot deep links. This derivation *is* the identity function.
- **serves:** linguistic-rigor, scholarly-power, data-honesty, implementation-gaps (§4)
- **costs:** minimal — a foundational decision, not a feature

### 3. Add three first-class Language attributes: word-minimality/prosodic type, macroarea/region, documentation-status
One cheap schema change unblocks four downstream findings: interpretable counts (C2), the map "no data" vs "structurally absent" third state (C5), count normalization, and mission expressibility (K4). Pull from Glottolog macroarea + endangerment + a WALS/minimality join.
- **serves:** linguistic-rigor, mission-fidelity, scholarly-power, data-honesty
- **costs:** scope-minimalism (small)

### 4. Split the honesty signal into two orthogonal axes
Keep source provenance (rename **verified→curated/attested**) AND add a **classification-confidence** signal for whether an entry's openness rests on the contested diphthong-vs-VG / coda call. One badge cannot carry two independent uncertainties.
- **serves:** data-honesty, linguistic-rigor, scholarly-power
- **costs:** broad-audience (more vocabulary to plain-language), scope (small)

### 5. Redesign every count so a bare number never appears
Show tier composition inline ("47 languages: 12 curated · 20 mined · 15 generated"); color cells by observed-vs-expected-under-a-phonotactic-null OR minimality-normalized, not raw popularity; label intensity "coverage in our data," not a neutral census; give the map an explicit "no data" state. **Defer the exact encoding until #1 shows whether cells are dense or sparse.**
- **serves:** linguistic-rigor, data-honesty, mission-fidelity, scholarly-power
- **costs:** scope-minimalism (build weight), editorial punch, broad-audience (density)

### 6. Decide the Global-South accountability posture — **HUMAN DECISION (K3, K4)**
Keep editorial tone neutral, but (a) decide the default tier-filter state (recommend: generated visible, never bare, with a removal-count on filtering), and (b) decide whether a coverage/equity view (tier-distribution-by-macroarea + "languages we cover worst") ships in v1 or as a fast-follow. Add a mission-weighted human-effort pass (spot-checks, recordings, upgrades) spent Global-South-first, with a per-language "coverage debt" field.
- **serves:** mission-fidelity, data-honesty
- **costs:** neutral-editorial-tone framing, scope-minimalism

### 7. Resolve licensing before ingestion — **BLOCKER**
Wiktextract/Wiktionary is CC-BY-SA copyleft; redistributing derived data may force share-alike on the whole catalog, and some sources may bar redistribution. Audit each intended source's license *before* building on it.
- **serves:** everyone (legal blocker discovered late is expensive) — from implementation-gaps §8.1
- **costs:** none — pure risk reduction

### 8. Pin the delivery model against a scale estimate
Back-of-envelope languages × mean yield (adjusted for minimality bias); decide static-baked JSON vs queryable backend; specify the shape→language index. URL-state and live-recolor UX silently assume a client-routable, interactive architecture.
- **serves:** scope-minimalism, implementation-gaps (§3), scholarly-power (export falls out of the CLDF substrate)
- **costs:** none — unblocks all architecture

### 9. Make IPA an annotated enhancement + build the a11y model
Every glyph gets a plain keyword + inline audio; ARIA grid semantics speak keywords not glyphs; ship a data-table equivalent of the map result; pair every audio control with an everyday respelling for deaf/HoH users; specify keyboard nav + bottom-sheet focus; specify responsive stacking.
- **serves:** broad-audience-accessibility
- **costs:** editorial "IPA as hero" purity (K2), scope-minimalism

### 10. Add data export (CSV + full CLDF) and dataset versioning/DOI
Cheap once #1's CLDF dataset exists; turns a dead-end website into citable research infrastructure. Retain multiple Sources per Form (PHOIBLE-style) rather than deleting the losing inventory via the ratchet.
- **serves:** scholarly-power, data-honesty (multi-source), mission-fidelity (auditability)
- **costs:** scope-minimalism (defer multi-source retention if needed; keep export)

### 11. Cut for v1 (per scope-minimalism, reinforced by implementation-gaps)
In cost-saved order: (1) synthesized/tiered **audio** — no engine or archive named; (2) **compare** route/tray/table; (3) **gloss-links + concept index** — Concepticon data sparse for priority languages; (4) **live map** — use a static CLDFViz PNG if geography is needed; (5) **URL/deep-link state**; (6) **onset-class/complexity filters**; (7) **extra entry paths** (autocomplete/surprise-me); (8) **editorial font system** (keep only ●◐○ iconography).
- **serves:** scope-minimalism, implementation-gaps
- **costs:** broad-audience (loses gloss delight, audio channel), scholarly-power (loses compare), mission (loses gloss cross-links) — *revisit each as a fast-follow once Stage 1/2 data proves coverage*

### 12. Annotate, don't reopen, the diphthong inclusion choice (K6)
Tag diphthong-derived Forms; label counts "analysis-relative." Keep ADR-0001's single-analysis simplicity; keep a future strict/inclusive view cheap.
- **serves:** linguistic-rigor, mission-fidelity, scope-minimalism (no toggle)
- **costs:** minimal

---

*Consensus is the confidence signal; conflicts K3 and K4 are flagged as genuine human decisions and must not be silently resolved by the implementer.*
