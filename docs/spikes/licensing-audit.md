# Spike: licensing-audit (Gap 8.1 — BLOCKER)

**Date:** 2026-07-03 · **Scope:** every source/tool in ADR-0002's tier table and reference set. · **Verification:** each claim marked ✅ (verified online this spike, source linked) or ⚠️ (unverified — training knowledge, cutoff Jan 2026). GitHub license fields were read via the GitHub API; site footers and the CELEX agreement PDF were fetched directly.

**Question set (terms of reference):** (a) per source — may we ingest, derive, and redistribute derived Forms? (b) does the mined tier force share-alike on the whole catalog? (c) must anything be dropped/quarantined? (d) attribution requirements. Ends with one catalog-license recommendation.

---

## Findings

### Per-source license table

| Source | Role (ADR-0002) | License | Verified | Ingest | Derive | Redistribute Forms |
|---|---|---|---|---|---|---|
| **Lexibank datasets** | curated | **CC-BY-4.0 is the norm**: of 191 repos in the `lexibank` GitHub org, 155 are CC-BY-4.0, 15 NOASSERTION, 13 no license, 2 GPL-3.0, 2 MIT, 4 Apache-2.0 | ✅ GitHub API org survey | Yes | Yes | **Yes** (attribution) — *per-dataset check still required for the ~15% without a clear license* |
| **NorthEuraLex** | curated | **CC-BY-SA 4.0** per the authors ([LREC paper / northeuralex.org](https://link.springer.com/article/10.1007/s10579-019-09480-6)). ⚠️ Conflict: the [lexibank/northeuralex](https://github.com/lexibank/northeuralex) CLDF wrapper README says "licensed under a CC-BY-4.0 license" (✅ fetched). Treat conservatively as **CC-BY-SA 4.0** | ✅ both readings | Yes | Yes | **Yes, share-alike attaches** |
| **CELEX2** | curated (en/nl/de + frequency) | **Research-only, no redistribution.** [CELEX2 User Agreement](https://catalog.ldc.upenn.edu/license/celex-user-agreement.pdf) (LDC96L14): "agrees to use this material only for research purposes… agrees not to copy or re-distribute the material to the others outside of User's research group." Copyright held by the Centre for Lexical Information | ✅ agreement PDF text extracted | ⚠️ dubious (a public web product exceeds "research purposes") | dubious | **NO — hard bar** |
| **WikiPron** | mined | Code **Apache-2.0** (✅ GitHub API); **data CC-BY-SA 3.0 Unported inherited from Wiktionary** ([README](https://github.com/CUNY-CL/wikipron)) | ✅ | Yes | Yes | **Yes, share-alike attaches** |
| **Wiktextract / Kaikki** | mined | Code **MIT** (✅ LICENSE fetched — "MIT License… Certain files under tests/ are under Wiktionary license"); **data dual CC-BY-SA + GFDL** "same licenses as Wiktionary" ([kaikki.org](https://kaikki.org/dictionary/index.html)) | ✅ | Yes | Yes | **Yes, share-alike attaches** (elect the CC-BY-SA arm of the dual license) |
| *Wiktionary upstream* | (mined tier's origin) | Dual **CC-BY-SA + GFDL**; text is BY-SA **3.0 for pre-June-2023 content, 4.0 for edits since** ([Wikimedia ToU update 2023](https://creativecommons.org/2023/06/29/wikipedia-moves-to-cc-4-0-licenses/), [Meta-Wiki](https://meta.wikimedia.org/wiki/Terms_of_use/Creative_Commons_4.0)) | ✅ | — | — | — |
| **Epitran** | generated | **MIT** | ✅ GitHub API | Yes | Yes | **Yes.** MIT places no restriction on program *output*; a rule-generated pronunciation of a word is a machine-produced statement of fact — effectively unencumbered (⚠️ US "facts uncopyrightable" doctrine — training knowledge, standard view). **But the input wordlist's license passes through**: G2P output inherits whatever encumbers the words fed in (ties to gap 1.5) |
| **Transphone** | generated | **MIT** (repo) | ✅ GitHub API | Yes | Yes | **Yes**, same logic as Epitran. ⚠️ Model *weights*' training-data provenance unverified |
| **PHOIBLE** | validation only | Site footer: **CC-BY-SA 3.0 Unported** (✅ [phoible.org](https://phoible.org/) fetched). Conflict: [cldf-datasets/phoible](https://github.com/cldf-datasets/phoible) repo license file is CC-BY-4.0 (✅ GitHub API); phoible/dev repo shows GPL-3.0 | ✅ | Yes | Yes (validate) | **N/A — we redistribute nothing from it.** Validation verdicts (stage 7) are our own facts; SA does not attach. Attribute anyway |
| **Glottolog** | reference | **CC-BY 4.0** (✅ [glottolog.org](https://glottolog.org/) footer; glottolog-cldf repo CC-BY-4.0) | ✅ | Yes | Yes | **Yes** (attribution) — coords/macroarea/doc-status attached to Languages are redistributed, so Glottolog must be credited |
| **Concepticon** | reference | **CC-BY 4.0** (✅ concepticon-cldf repo license; [concepticon.clld.org](https://concepticon.clld.org/contributions)) | ✅ | Yes | Yes | **Yes** (attribution) |
| **CLTS** | reference | **CC-BY 4.0** (✅ [clts.clld.org](https://clts.clld.org/) footer); pyclts code Apache-2.0 | ✅ | Yes | Yes | **Yes** (attribution) |
| **espeak-ng** | audio (gaps §2) | **GPL-3.0** (✅ GitHub API) | ✅ | see below | see below | audio output: see below |
| *Pipeline tools* | tooling | pylexibank / cldfbench / segments **Apache-2.0**, LingPy **GPL-3.0** (✅ GitHub API) | ✅ | — | — | Tool licenses do **not** propagate to data outputs; LingPy's GPL matters only if we redistribute LingPy-derived *code*, which we don't |

### espeak-ng (GPLv3) — the three usage modes

1. **Server-side / build-time synthesis (run the binary, ship only WAV/OGG):** GPLv3 does not restrict *running* the program, and no conveyance occurs → **zero obligations**.
2. **Distributing the synthesized audio:** GPLv3 §2: "output from running a covered work is covered by this License **only if** the output, given its content, constitutes a covered work" (✅ [GPLv3 text](https://www.gnu.org/licenses/gpl-3.0.en.html)). A formant-synthesized WAV of one word does not embody the program's source → **audio is ours to license, distributable under the catalog license**. (⚠️ Residual minority argument that voice data embedded in output taints it — standard interpretation says no; accepted risk, note it on the Data-sources page.)
3. **Shipping espeak-ng itself (e.g., WASM in the browser):** that *is* conveyance → full GPLv3 obligations (source offer, license text), and **anything linking libespeak-ng becomes GPL**. Avoid linking it into the app bundle; if in-browser TTS is ever wanted, isolate it as a separately-delivered GPL component or pick a permissive engine.

### The share-alike question (b) — answered

- Mined-tier Forms are extractions/adaptations of Wiktionary content → the aggregate is share-alike encumbered (CC-BY-SA 3.0/4.0). Individual IPA strings are arguably uncopyrightable facts in the US (⚠️), but EU sui generis database rights and community norms make "comply as if copyrighted" the only defensible public posture.
- **Decisive finding: dropping the mined tier would NOT free the catalog from share-alike anyway** — NorthEuraLex, a *curated*-tier pillar, is CC-BY-SA 4.0 by its authors. SA is in the catalog's bloodstream on both tiers.
- License arithmetic works cleanly in exactly one direction: CC-BY-SA 3.0 material may be adapted under BY-SA 4.0 (3.0 permits "later versions"); CC-BY 4.0 material may be incorporated into a BY-SA 4.0 work (one-way compatibility); the GFDL arm of Wiktionary's dual license is simply not elected. **CC-BY-SA 4.0 is the unique common denominator.**
- Is that acceptable? Yes: BY-SA permits commercial use and redistribution, forbids nothing this project plans, and share-alike actively matches the project's honesty ethos (generated-never-hidden; the data stays open downstream).

### Drop / quarantine list (c)

| Source | Verdict |
|---|---|
| **CELEX2** | **DROP from the catalog** (confirmed casualty). The agreement bars redistribution outright, and "research purposes only" makes even ingestion-for-a-public-web-product legally shaky. Do not ingest, even internally, for this product. English/Dutch/German Form coverage is fine without it (Lexibank + mined tier are strong exactly there). Casualty's real cost is **Stage-2 frequency data** — needs an open substitute (open question #1; note [CityLex](https://pypi.org/project/citylex/) as a model for free English lexical data). |
| **Lexibank NOASSERTION/no-license datasets (~28 of 191)** | **Quarantine by default**: a dataset only enters ingestion once its individual license is read and cleared. Encode as a Phase-0 gate rule, not a one-time check. |
| Any CC-BY-**NC** or ND source encountered later | **Blocked** — NC is incompatible with BY-SA redistribution and with not constraining downstream reuse. |
| PHOIBLE | Not dropped — stays exactly where ADR-0002 put it: validation-only, never a Form source. If inventory data is ever *displayed*, its CC-BY-SA 3.0 re-enters scope (non-issue under a BY-SA 4.0 catalog). |

### Attribution requirements for the Data-sources page (d)

CC-BY(-SA) 4.0 requires: creator credit, copyright/license notice with link, "changes were made" indication, and no implied endorsement. Concretely:

1. **Per source, on the Data-sources page:** dataset name + exact version/DOI (Lexibank datasets have Zenodo DOIs — cite the versioned DOI, which research.md already demands), authors, license name linked to its legal code, link to the source, and a standing "transcriptions were canonicalized to CLTS BroadIPA and filtered; changes were made" notice.
2. **Wiktionary-derived Forms:** attribution via link to the source (per-Form link to the Wiktionary entry is derivable from the word + language and satisfies BY-SA 4.0's "reasonable to the medium" standard); page-level credit "Contains pronunciation data mined from Wiktionary (CC-BY-SA) via WikiPron and Wiktextract/Kaikki".
3. **Reference catalogs:** credit Glottolog, Concepticon, CLTS (CC-BY 4.0) — their content ships inside Language/Gloss/segment attributes.
4. **Machine-readable:** the released CLDF package carries `LICENSE` (CC-BY-SA 4.0), a `SOURCES.md`/`CITATION.cff` enumerating the same table, and — since Forms already carry Sources — a **per-Form source-license column at stage 9 (EMIT)** so downstream users can mechanically extract a permissive-only (CC-BY-only) subset.
5. Generated audio labeled: "synthesized with eSpeak NG (GPLv3 engine; audio © this project, CC-BY-SA 4.0)".

---

## Options considered

**Catalog data license:**

1. **CC-BY-SA 4.0 for the whole released dataset** — *chosen.* Legally the unique common denominator (see arithmetic above); simplest for reusers; one license, one notice; matches project ethos. Cost: downstream users must share alike — acceptable, and the per-Form license column gives them a permissive-subset escape hatch.
2. **Per-record licensing (collection doctrine)** — catalog structure CC-BY 4.0, each Form retaining its source license. *Runner-up.* Legally defensible (a CLDF dataset is a collection/database, SA arguably attaches per-item) but reuser-hostile, fragile in the EU (database right covers the whole), and it buys nothing since the flagship UI mixes tiers everywhere.
3. **CC-BY 4.0 catalog by excluding all SA sources** — rejected: loses the mined tier *and* NorthEuraLex; guts long-tail coverage, which is the mission.
4. **CC0/public-domain assertion ("pronunciations are facts")** — rejected: US-centric, ignores EU database rights, violates upstream community norms, and would poison relations with the CLDF ecosystem the project depends on.

**CELEX handling:** (i) drop — *chosen*; (ii) quarantine for internal research-only analysis feeding published *statistics* — rejected as still outside "research purposes" for a product and a compliance trap; (iii) seek a commercial license from LDC ($150–300 tier seen on the catalog page) — rejected: the agreement shown still bars redistribution; not worth pursuing.

**espeak-ng:** (i) server-/build-side synthesis, distribute audio only — *chosen*; (ii) browser WASM — rejected for now (GPL conveyance + linking implications); (iii) permissive alternative engines — revisit only if in-browser synthesis becomes a requirement.

---

## Recommendation

**Release the catalog (the baked CLDF dataset and every derived data artifact) under CC-BY-SA 4.0, with per-Form source + source-license metadata emitted at stage 9; keep application code under a separate permissive license (MIT); DROP CELEX entirely; run espeak-ng server-/build-side only and distribute the audio under the catalog license.** Rationale: share-alike is unavoidable the moment either NorthEuraLex or the mined tier is in (and both are load-bearing), BY-SA 4.0 is the only license every cleared source can legally flow into, and it costs the project nothing it wants to do. Runner-up: per-record collection licensing (option 2) — keep it in reserve only if a future partner demands a permissive core, which the per-Form license column already approximates.

---

## Consequences for the strategy

- **Phase 0 licensing gate becomes a concrete allowlist rule**, closing gap 8.1: *allowed* = CC0, CC-BY 3.0/4.0, CC-BY-SA 3.0/4.0, Wiktionary dual (elect BY-SA), MIT/Apache data; *blocked* = NC, ND, research-only, NOASSERTION-until-read. Every Source cleared at seed-set selection (§0/§1 of the strategy's first move) records its license in the Source registry.
- **ADR-0002 amendment needed:** remove CELEX from the curated tier row (en/nl/de Forms come from Lexibank + mined; note added that tier assignment is unaffected). Flag the Stage-2 frequency dependency as an open sourcing question.
- **Stage 9 (EMIT) gains a per-Form `source_license` field**; the Data-sources page spec (ux-design) gains the attribution block from Findings (d).
- **The Data-sources page is now a compliance surface, not just credits** — it must render license names, links, versions/DOIs, and the changes-made notice.
- **Audio subsystem (gaps §2):** espeak-ng constrained to server-/build-side; no libespeak-ng linkage in shipped app code; generated audio labeled and BY-SA 4.0.
- **No impact on locked decisions:** UI-first, honesty axes, generated-never-hidden, juxtaposition-compare, CLDF/CLTS backbone all untouched; BY-SA strengthens the honesty posture.

## Open questions

1. **Frequency source to replace CELEX for Stage-2 analyses** — SUBTLEX is NC (⚠️ training knowledge), wordfreq aggregates mixed-license corpora; needs its own mini-audit when Stage 2 approaches.
2. **The ~28 unlicensed/NOASSERTION Lexibank datasets** — per-dataset clearance deferred to seed-set selection; some may be clarified upstream on request.
3. **NorthEuraLex conflict** (authors say BY-SA 4.0; Lexibank wrapper says BY-4.0) — worth one upstream issue to lexibank/northeuralex maintainers; until answered, BY-SA assumed.
4. **Transphone model weights** — repo is MIT, but the weights' training-data licensing is unverified; low risk (outputs treated as facts) but note it.
5. **Counsel review before public launch** — this audit is diligent but not legal advice; a one-hour review of the BY-SA 4.0 posture + espeak-ng audio stance is cheap insurance.
