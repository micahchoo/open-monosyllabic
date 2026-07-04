# Implementation Gaps — Open Monosyllabic

Audit of the four design docs (`CONTEXT.md`, `docs/adr/0001`, `docs/ux-design.md`, `research.md`)
for knowledge that would **block or mislead an implementer**. No code exists yet.
Gaps are grouped by area and ranked by how much they threaten the build (biggest first).

Each gap gives: **(a)** what's missing · **(b)** why it blocks/risks the build · **(c)** the decision that closes it.

---

## Executive summary — the most critical gaps

- **The ingestion pipeline is entirely unspecified.** The docs name Confidence Tiers and Sources but never say which datasets are pulled in what order, with what tooling, or how a raw source becomes a Form. This is the make-or-break phase and it is a blank.
- **The "open monosyllable" filter has no defined computation.** Segmentation, syllabification, and the diphthong-vs-glide classifier (the entire ADR-0001 inclusion rule) are described as *decisions* but never as *code* — and research.md flags this as the noisiest, hardest step, concentrated exactly where machine data errs.
- **Shape identity by "exact string match" is unsafe across heterogeneous sources.** Lexibank, WikiPron, and Epitran transcribe the same word differently (/a/ vs /ɑ/, diacritics, length). Without a canonicalization step (CLTS BroadIPA), "every language with /ma/" will silently fragment.
- **Audio is a large, wholly unaddressed dependency.** UX mandates pervasive audio "synthesized from IPA," but no synthesis engine, no source of real recordings, and no generation pipeline are named anywhere. IPA-input TTS is a genuinely hard capability, not a checkbox.
- **The hero heatmap is unbuildable as specced.** Onset and vowel axes are unbounded across languages (hundreds of onsets, diphthongs, CV/CCV/V shapes). Nothing says how the matrix is bucketed to stay renderable, and "cell = one Shape" contradicts "rows = onset class."
- **The mission contradicts the data the UX leans on.** Global-South / under-documented languages are prioritized first — but those are precisely where Words, glosses, and verified tiers are sparse. The Form-detail view makes "example Words the headline" and glosses clickable; for the priority languages that headline will be empty and the tier badges mostly "generated."
- **Tech stack, delivery model, and scale are all open.** Static-baked dataset vs live backend is undecided, and nobody has estimated language/form/word counts — yet that count determines the entire architecture.
- **Data licensing is unexamined.** Wiktextract/Wiktionary is CC-BY-SA (copyleft); redistributing derived data may force share-alike on the whole catalog. A "Data sources" credit page is planned but license *compliance* is not.

---

## 1. Data sourcing & ingestion pipeline — CRITICAL (make-or-break)

The single largest hole. `CONTEXT.md` defines Confidence Tier / Source as *concepts*; `research.md`
§Recommendations Stage 1 gives a *recommended* priority (Lexibank/NorthEuraLex → WikiPron/Wiktextract → Epitran G2P),
but no design doc commits to an actual pipeline. Everything downstream depends on this.

### 1.1 No ingestion pipeline is specified
- **(a)** Which datasets are ingested, in what order, with what tooling (PyLexibank/CLDFBench? custom?) — undefined in the design docs; only *surveyed* in research.md.
- **(b)** Without a committed source list and order, there is no dataset to build the UI over; every UI decision is speculative.
- **(c)** Ratify research.md's Stage-1 priority as an ADR: enumerate the exact datasets + versions, the tool that reads each, and the order of precedence.

### 1.2 The "open monosyllable" filter is never computed
- **(a)** How raw IPA becomes an included Form — segmentation (`segments`/orthography profiles), syllabification, coda detection, single-syllable check — is described nowhere.
- **(b)** This filter *defines the entire catalog's contents* (ADR-0001). research.md warns the `segments` library mis-segments pre-posed diacritics and that G2P errors concentrate in exactly the vowel/final-segment region that decides "openness." Get this wrong and the catalog is wrong.
- **(c)** Specify the transcription level (CLTS BroadIPA), the tokenizer, and the syllabification/coda-detection algorithm as versioned rules. Decide how ambiguous syllable counts are resolved.

### 1.3 The diphthong-vs-glide classifier has no home
- **(a)** ADR-0001 hinges on distinguishing a diphthong nucleus (included) from vowel+glide/CVG (excluded), but *where* and *how* this is computed — and its expected error rate — is unstated.
- **(b)** research.md: this split "can roughly double or halve a language's yield" and is "a known hard case in automatic transcription." It is the load-bearing classifier for inclusion, and machine data is least reliable here.
- **(c)** Decide: is the diphthong/VG call taken from the source's own transcription, from a per-language rule table, or computed? What is the fallback when sources disagree? Should generated-tier diphthong calls be flagged for manual spot-check?

### 1.4 Source→Tier mapping and cross-source merge are undefined
- **(a)** `CONTEXT.md` says "one Source maps to exactly one tier" and the tier "ratchets up only," but the actual Source→Tier table, and the logic that recognizes two sources describe the *same* Form (to upgrade its tier), are missing.
- **(b)** The ratchet rule (§Lifecycle) is unimplementable without a stable match key across sources — and that key is the shape string, which is itself unnormalized (see 4.1). Merge/dedup is where duplicate Forms silently multiply.
- **(c)** Author the Source→Tier lookup. Define the merge key and precedence: when Lexibank and Epitran both yield /ma/ for language X, is that one Form (tier upgraded) or two?

### 1.5 Where do input wordlists for under-documented languages come from?
- **(a)** Epitran (generated tier) is grapheme-to-phoneme — it needs orthographic wordlists as input. No source of those input words is named.
- **(b)** The Global-South-first mission targets languages with the least data. If there's no wordlist to feed Epitran, "generated tier" produces nothing — the priority languages may have *no* Forms at all, not merely low-confidence ones.
- **(c)** Identify the graphemic wordlist source per under-documented language (PanLex? IDS? field wordlists?) before assuming G2P fills the gap.

### 1.6 Free-text gloss → Concepticon mapping is unaddressed
- **(a)** `CONTEXT.md` requires each Gloss to be a Concepticon concept, but WikiPron gives no gloss and Wiktextract gives free-text glosses. Mapping free text → Concepticon is a real curation/NLP step.
- **(b)** The UX "tap a gloss → same concept everywhere" delight (see 6.2) only works for Concepticon-linked Words. Most mined Words won't be linked; the feature degrades to near-nothing.
- **(c)** Decide the gloss-linking approach (Concepticon's mapping tools? manual? only Lexibank-native links?) and accept that non-Concepticon Words carry a plain-text gloss with no cross-language link.

---

## 2. Audio — CRITICAL (large unaddressed dependency)

`docs/ux-design.md` §Audio makes audio pervasive ("present everywhere via synthesis-from-IPA"),
badged recorded vs synthesized. **No technology is named for either side.** This is a whole subsystem the design assumes exists.

### 2.1 No IPA-to-speech synthesis engine
- **(a)** "Synthesized from IPA" names no engine. Most TTS consumes graphemes, not arbitrary IPA; IPA-input synthesis (espeak-ng and similar) is niche, per-language, and robotic.
- **(b)** Audio is specced as ubiquitous (big play button in the Form-detail header, per-Word inline play, per-column in compare). If synthesis is infeasible or low-quality, a headline UX affordance breaks everywhere at once.
- **(c)** Choose and prototype an IPA→audio path (espeak-ng phoneme input? a neural TTS with a phoneme frontend?). Confirm it accepts the tone-blind segmental strings the catalog stores, and decide build-time pre-rendering vs on-the-fly.

### 2.2 No source of real recordings
- **(a)** "Recorded (a genuine recording from an archive)" names no archive. None of the cited standards (PHOIBLE, Lexibank, Glottolog) ships per-word audio.
- **(b)** The recorded/synthesized provenance axis is a stated honesty pillar, but with no recording source *every* clip is synthesized — the axis collapses to a constant and the badge is pointless.
- **(c)** Either identify a recording archive keyed to forms/languages, or explicitly scope v1 as synthesis-only and state that the "recorded" badge is aspirational.

---

## 3. Tech stack, delivery model & scale — HIGH (constrains everything)

Nothing is decided; the design docs are deliberately domain/UX-only. But several UX choices silently constrain the architecture.

### 3.1 Static-baked dataset vs live backend is open
- **(a)** No decision on web framework, static vs dynamic, hosting, or whether the dataset is build-time-baked JSON or served by a backend.
- **(b)** This is the top architectural fork and it gates every other implementation choice. It can't stay open past the first sprint.
- **(c)** Decide against the scale estimate (3.2). Note the constraints already baked in: filters "reflected in the URL" + "deep links to any state" push toward client-routable state; the heatmap aggregate is tiny and static-friendly, but per-shape/per-language drill-down data may be too large to ship client-side.

### 3.2 No scale estimate (languages / forms / words)
- **(a)** No count of realistic languages, Forms, or Words. research.md gives raw hints: Lexibank ~2,400 varieties, PHOIBLE 2,186 languages, Vietnamese alone ~6,500 syllables.
- **(b)** Total Forms plausibly reach 10^5–10^6 and Words more; that decides whether a static JSON blob is viable or a queryable index/backend is mandatory. Architecture can't be chosen without it.
- **(c)** Produce a back-of-envelope estimate (languages × mean open-monosyllable yield, adjusted for minimality bias per research.md §1) before picking the delivery model.

### 3.3 No query/index substrate for Shape grouping
- **(a)** "Every language with /ma/" is "computed at query time" (`CONTEXT.md`) — but on what? A precomputed inverted index (shape → languages), an in-browser dataset, or a DB query is unspecified.
- **(b)** The primary UI axis (Shape) depends on this lookup being fast; the implementation differs entirely between static (bake the inverted index) and backend (index a table).
- **(c)** Falls out of 3.1/3.2; specify the shape→language index once the delivery model is chosen.

---

## 4. Storage & schema / identity keys — HIGH

The domain model is language-level, not physical (`CONTEXT.md` is explicit). Turning it into storage exposes unresolved keys.

### 4.1 The tone-blind segmental string is never defined as a derivation
- **(a)** Form identity and Shape grouping both key on "tone-blind segmental IPA," but the function that turns a full IPA transcription into that string — strip which tone marks? length marks? nasalization? stress? — is undefined. research.md notes nasality-as-nucleus-vs-syllable is itself unresolved.
- **(b)** "Cross-language sameness is exact string match" (`CONTEXT.md`) means this derivation *is* the identity function. If /ma/ from Lexibank and /ma/ from Epitran normalize differently, they become different Shapes and the hero feature under-counts. Is nasalized /ã/ the same Shape as /a/? The docs can't answer.
- **(c)** Specify a canonicalization to a fixed level (CLTS BroadIPA is research.md's recommendation), enumerate exactly which diacritics/marks are stripped, and make it the single source of the key. This is arguably the highest-leverage schema decision.

### 4.2 Is (Language + tone-blind IPA) a stable storage key?
- **(a)** If the canonicalization in 4.1 ever changes (reprocessing, better rules), every Form key changes — breaking deep links, compare pins, and stored audio filenames.
- **(b)** URLs are shareable and filters live in the URL (`ux-design.md`); a churning key silently rots every shared link.
- **(c)** Decide whether the key is the raw derived string or a versioned/surrogate ID, and how reprocessing migrates existing links.

### 4.3 Word/tone/gloss physical storage unresolved
- **(a)** How Words (Form + tone + Gloss), the set of tones a Form takes, and multi-gloss polysemy are physically stored is untouched (polysemy is explicitly "not yet resolved" in `CONTEXT.md`).
- **(b)** The Form-detail and compare views render per-Word tone glyphs and per-Word tier badges; the schema must carry tone and tier *per Word*, distinct from the Form.
- **(c)** Resolve polysemy (one Word many Glosses) and define the Word row shape before schema work.

---

## 5. The heatmap — HIGH (hero UI, unbuildable as specced)

`ux-design.md` §Landing makes the onset × vowel heatmap the hero and the primary IPA picker. Its axes are unbounded.

### 5.1 Both axes are unbounded and unbucketed
- **(a)** Rows = onsets, columns = vowels, "cell = one Shape," "whole shape space visible at a glance." Across languages there are hundreds of onset segments and many vowels — plus diphthongs (included by ADR-0001) and V-only (no-onset) and CCV/CCCV shapes that a 2-D onset×vowel grid has no place for.
- **(b)** A matrix of hundreds × dozens is neither renderable nor glanceable; the hero object as literally described cannot be drawn.
- **(c)** Decide the bucketing: are rows onset *classes* (nasal/stop/… — as the filter implies) or individual segments? Are columns individual vowels, and where do diphthongs, complex onsets, and onset-less shapes live? This must be pinned before any landing-page work.

### 5.2 "cell = one Shape" contradicts "rows = onset class"
- **(a)** §Landing says each cell is one Shape (a specific onset+vowel like /ma/); §Filter UI offers "onset-class checkboxes (nasal, stop, fricative…)." A row can't be both a single onset and a class.
- **(b)** The two sections describe incompatible matrices; an implementer can't tell whether a row is /m/ or "nasals."
- **(c)** Reconcile: pick segment-level or class-level rows (or a two-level expand/collapse), consistently across landing and filters.

---

## 6. UX decisions that assume data the sourcing plan won't reliably provide — HIGH

Cross-cutting contradictions between the mission/UX and what Global-South-first sourcing yields.

### 6.1 "Example Words are the headline" — but the priority languages have none
- **(a)** Form-detail body makes example Words the headline (`ux-design.md`); `CONTEXT.md` says Words are "absent for under-documented languages, which still appear as Forms."
- **(b)** The mission prioritizes under-documented languages *first*. For exactly those, the headline of the detail view is empty and tier badges skew "generated." The hero content is missing for the hero audience.
- **(c)** Design the Words-absent detail state as a first-class layout (not a degraded one), and decide whether the honesty framing openly surfaces "no verified words yet" rather than looking broken.

### 6.2 Gloss links assume Concepticon-mapped Words that will be sparse
- **(a)** "Glosses are links → same concept across every language" depends on Concepticon mapping, which only Lexibank-style basic-vocabulary Words reliably have (see 1.6). research.md: Lexibank concepts are 40–2,000-item basic vocab.
- **(b)** The "same meaning elsewhere" delight will fire for a small minority of Words and dead-end for most — including nearly all mined/generated content.
- **(c)** Accept the feature as secondary (the doc already says so) and define the non-linked-gloss fallback; set expectations that cross-concept jumps work mainly within the verified basic-vocabulary core.

### 6.3 Search "plain-spelling tolerance" needs a spelling→IPA map
- **(a)** The search bar promises autocomplete with "plain-spelling tolerance" (type "ma" → find /ma/), but nothing provides the plain-spelling↔IPA mapping.
- **(b)** Autocomplete over IPA glyphs alone won't match lay typing; the affordance needs a transliteration/alias index that doesn't exist in the plan.
- **(c)** Decide the mapping source (romanization of the shape string? per-language orthography?) or narrow the promise to IPA/click entry.

---

## 7. Map — MEDIUM

`ux-design.md` §Landing: world map, dots = languages with the selected shape, "recolors live on selection."

### 7.1 Rendering tech unspecified, and "live recolor" rules out static
- **(a)** research.md offers CLDFViz *static* PNG or clld/Leaflet interactive; the design names neither.
- **(b)** "Dots recolor live on selection" requires an interactive vector map (Leaflet / d3-geo / vector tiles) — the static PNG path research.md highlighted for the stated static preference is incompatible with the UX.
- **(c)** Choose an interactive map library and confirm geo-coordinates come per-language from Glottolog (available — one point per language).

---

## 8. Cross-cutting gaps no doc answers — MEDIUM

### 8.1 Data licensing / redistribution
- **(a)** A "Data sources" credit page is planned, but license *compliance* for redistributing derived data is unexamined. Wiktextract/Wiktionary is CC-BY-SA (copyleft); Lexibank datasets vary.
- **(b)** CC-BY-SA can force share-alike on the entire derived catalog, and some sources may bar redistribution — a legal blocker discovered late is expensive.
- **(c)** Audit each intended source's license before ingestion; decide whether the baked dataset can be redistributed and under what terms.

### 8.2 Data refresh / versioning cadence
- **(a)** Sources are versioned (research.md stresses "cite the version you actually use"), but no re-ingestion/update cadence or dataset-version surfacing is planned.
- **(b)** The tier ratchet (§1.4) and stable keys (§4.2) both interact with re-ingestion; without a versioning story, upgrades and link stability are undefined.
- **(c)** Decide dataset version pinning, refresh cadence, and whether the app surfaces "data as of version N."

### 8.3 Onset-class and nucleus-type attribute derivation
- **(a)** Filters need each onset mapped to a class (nasal/stop/fricative) and each Form's nucleus type (monophthong/diphthong/long) as a displayed attribute — the CLTS feature join that produces these is never mentioned.
- **(b)** The onset-class filter and nucleus-type display are specced UI that depend on a feature-annotation step absent from the pipeline.
- **(c)** Add a CLTS/feature-annotation stage to the pipeline (§1) that tags each segment with class and each nucleus with type.

---

## Ranked area summary

| Rank | Area | Threat |
|------|------|--------|
| 1 | Data sourcing & ingestion pipeline (§1) | Make-or-break; nothing exists |
| 2 | Audio synthesis + recordings (§2) | Large subsystem assumed, not designed |
| 3 | Tech stack, delivery & scale (§3) | Top architectural fork, undecided |
| 4 | Storage & identity keys (§4) | Shape-string derivation is the identity function, undefined |
| 5 | Heatmap axis bounding (§5) | Hero UI unbuildable as literally specced |
| 6 | UX-assumes-missing-data contradictions (§6) | Hero content empty for the hero audience |
| 7 | Map rendering (§7) | Tech unspecified; static vs live conflict |
| 8 | Licensing / versioning / feature-annotation (§8) | Late-discovery blockers |
