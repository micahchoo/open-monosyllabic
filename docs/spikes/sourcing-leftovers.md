# Spike: sourcing-leftovers — G2P input wordlists (gap 1.5) & gloss→Concepticon mapping (gap 1.6)

**Date:** 2026-07-03 · **Status:** complete · **Terms of reference:** `docs/implementation-gaps.md` §1.5, §1.6 (touching §6.2)
**Respects locked decisions:** ADR-0002 Source→Tier table and 9-stage pipeline; generated-never-hidden; CLDF/CLTS backbone; juxtaposition-only compare.

---

## Findings

### A. The generated tier has a *double* gate, not a single one

ADR-0002 treats G2P as the coverage backstop, but a generated Form requires **two** independent resources per language:

1. **An orthographic wordlist** (Epitran/Transphone consume graphemes) — the hole named in gap 1.5.
2. **A G2P model for that language–script pair.** Epitran's LREC paper covers [61 languages](https://aclanthology.org/L18-1429/); the current repo ships roughly 80–90 distinct language–script pairs (~150 map files, per [third-party analysis](https://arxiv.org/pdf/2601.06932); exact current count unverified — check `epitran/data/map/` at pin time). [Transphone](https://github.com/xinjli/transphone) advertises models for ~7,546 Glottolog languages, but ~900 of those are **nearest-language approximations**, and accuracy for the long tail is essentially unvalidated — exactly the vowel/final-segment error concentration ADR-0002 already flags.

Either gate failing ⇒ no generated Forms for that language. The strategy currently assumes only gate 2 exists.

### B. Candidate input-wordlist sources, assessed

| Source | Coverage | License | Orthography quality | Verdict |
|---|---|---|---|---|
| **IDS** (Intercontinental Dictionary Series) | [319 varieties × 1,310 concepts, ~438k lexemes](https://github.com/intercontinental-dictionary-series/ids) | **CC-BY 4.0** (verified on the [CLDF repo](https://github.com/intercontinental-dictionary-series/ids)) | Curated elicitation lists; per-contributor transcription varies (orthographic vs. broad phonemic — check per dataset) | **First choice.** Already CLDF + **Concepticon-linked**, so generated Forms from IDS inputs arrive *with gloss links* — directly mitigates gaps 6.1/6.2. Modest language count but skews toward exactly the under-documented (esp. South American) varieties the mission prioritizes. |
| **PanLex** | [~20M lexemes, ~9,000 varieties](https://aclanthology.org/L14-1023/) (2014 figure; long tail of tiny lists) | **CC0** ([database snapshots](https://panlex.org/license/), [monthly dumps](https://panlex.org/snapshot/)) | Dictionary lemmas in native orthography; noisy variety-mapping, multiword expressions, no frequency | **Second choice.** Widest lexeme coverage under the most permissive license in the whole plan. Needs: variety→Glottocode mapping, single-token filter, script detection. |
| **Crúbadán** | [~2,000 languages](https://kevinscannell.com/files/wac3.pdf), word-frequency lists from web crawls | **CC BY 4.0** (per [OLAC archive record](http://www.language-archives.org/archive/crubadan.org); confirm per-file at pin time) | Web-crawled: real orthography but polluted by names, loanwords, misidentified text; frequency rank enables top-N filtering | **Third choice / coverage extender.** Precedent exists: the [XPF Corpus](https://cohenpr-xpf.github.io/XPF/About.html) built phoneme frequencies for 200+ languages from **Crúbadán wordlists + rule-based G2P** — this exact pipeline shape is proven. Note XPF could *not* redistribute the underlying frequency lists; we must fetch Crúbadán directly. |
| **Bible-derived** ([eBible corpus](https://github.com/BibleNLP/ebible)) | 1,009 translations / 833 languages | **Mixed**: 84 PD + 113 CC-BY-SA usable; ~800 files are ND/NC variants — **a derived wordlist is a derivative work; ND subset is unusable** | Clean published orthography; archaic/domain-skewed vocabulary (acceptable — we extract word *forms*, not meanings) | **Fourth choice, PD/BY-SA subset only.** The larger [Parallel Bible Corpus](https://aclanthology.org/L14-1215/) (1,335+ languages) is **not redistributable** (no explicit license; only co-occurrence matrices public) — excluded. |
| **Wikipedia / OSCAR frequency lists** | Wikipedia ~330 editions (CC-BY-SA); [OSCAR ~150–168 languages](https://huggingface.co/datasets/oscar-corpus/OSCAR-2301) | CC-BY-SA / CC0-ish (OSCAR) | [Documented low quality for the smallest subcorpora](https://arxiv.org/pdf/2006.06202) — language-ID errors compound at the tail | **Last resort, mid-resource only.** For low-resource languages these are dominated by Crúbadán; for well-resourced ones curated/mined tiers already win. |
| **ASJP** | [11,540 wordlists / 6,126 Glottocodes](../../research.md) (v21) | CC-BY 4.0 (lexibank/asjp) | **Not orthography.** [ASJPcode](https://en.wikipedia.org/wiki/Automated_Similarity_Judgment_Program) is a 41-symbol phonetic reduction: 7 vowel classes, no length, no tone, one click symbol | **Rejected as G2P input** (answering the ToR question directly): Epitran maps *a language's orthography* → IPA; ASJPcode is neither the language's orthography nor recoverable to it. Also rejected as a direct pseudo-IPA Form source: the 7-vowel collapse merges contrastive vowels, violating ADR-0002's "do not merge contrastive segments," and coda/openness judgments on 40-item lists add nothing curated tiers don't already give. **Keep only as a coverage/validation aid** (which Glottocodes have any lexical attestation at all). |

### C. Which priority languages still yield NOTHING

The generated tier's realistic ceiling is the **union of orthographic-wordlist coverage ∩ G2P coverage**:

- Wordlist union (IDS ∪ PanLex-substantial ∪ Crúbadán ∪ eBible-PD/BY-SA) ≈ **2,000–4,000 languages** with more than a token handful of words (unverified aggregate — the seed-phase audit should compute the exact join against Glottolog).
- Glottolog registers ~8,000 languages. **Several thousand languages — disproportionately the unwritten and barely-written ones the mission prioritizes — have no orthographic wordlist anywhere**, and for unwritten languages G2P is category-inapplicable (no graphemes exist).
- Even inside the wordlist union, languages whose script/orthography Epitran lacks and whose Transphone output would be nearest-language guesswork may be *policy-excluded* (see Open questions).

**Consequence the strategy must absorb:** "generated tier fills the long tail" is false at the tail's end. Those languages appear in the Explorer only as Language entries with `documentation-status = no data sourced` — which the design already handles honestly via the three-state map (present / no-data / structurally-absent). No new UI is needed; what's needed is that Phase 5 planning and the scale estimate (gap 3.2) stop counting those languages as Form-bearing.

### D. Gloss→Concepticon tooling (gap 1.6)

- **Lexibank-native links**: curated-tier CLDF datasets (incl. IDS, NorthEuraLex) already carry Concepticon parameter IDs — zero work, high trust.
- **[pyconcepticon](https://github.com/concepticon/pyconcepticon) `map_concepts`**: automated candidate mapping for *elicitation-style concept lists*, designed for the [Concepticon curation workflow](https://calc.hypotheses.org/1844) — which explicitly includes a **human review step** before links are accepted. Built for hundreds-of-items lists, not millions of free-text definitions.
- **[pysem](https://github.com/lingpy/pysem) `to_concepticon`**: fast fuzzy gloss→concept lookup returning candidates **with confidence scores**; the published usage pattern is "map automatically, then filter to clear mappings." Suitable for batch enrichment, not for unsupervised trust.
- **Wiktextract free-text glosses** are full definition sentences ("first person singular pronoun; used by a speaker to refer to himself"), not elicitation glosses. No established pipeline maps arbitrary Wiktionary definitions to Concepticon at scale with high precision. Any automated link here would be a *machine guess presented as a cross-language identity* — a third honesty axis the locked two-axis design deliberately does not have.

---

## Options considered

### (a) Input-wordlist priority chain for the generated tier

1. **IDS → PanLex → Crúbadán → eBible(PD/BY-SA) → Wikipedia** *(recommended)* — orders by curation quality and by how much each input carries for free (IDS: Concepticon links; PanLex: permissive license + breadth; Crúbadán: frequency + tail coverage).
2. Crúbadán-first (maximal coverage per XPF precedent) — rejected: web noise would dominate the generated tier for languages where IDS/PanLex offer curated lemmas; frequency lists put misidentified junk directly into the openness classifier.
3. PanLex-only (one source, one license, one adapter) — runner-up: simplest engineering, CC0, widest; rejected as sole source because it forfeits IDS's free gloss links and Crúbadán's tail coverage.

### (b) Gloss→Concepticon v1 posture

1. **Lexibank-native links only; unmapped glosses render as plain text, no link** *(recommended)*.
2. Automated pysem mapping of Wiktextract glosses above a confidence threshold — runner-up: real tooling exists, but it manufactures a new provenance axis (machine-mapped concept links) the locked design has no honest place for, and precision on definition-sentences is unvalidated. Defer to v2 as a ratchet-like enrichment *with human review*, mirroring the tier-upgrade lifecycle.
3. Manual curation of high-frequency Wiktextract glosses — rejected for v1: unbounded linguist time against a feature the UX already classifies as secondary.

---

## Recommendation

**(a)** Adopt the input-wordlist chain **IDS › PanLex › Crúbadán › eBible (PD/CC-BY-SA subset only) › Wikipedia-frequency**, applied per language after curated/mined tiers are exhausted, with ASJP explicitly excluded as G2P input (wrong representation) and retained only as a coverage checklist. Amend the strategy to state that the generated tier bottoms out at roughly 2,000–4,000 languages; every remaining language ships as a Form-less Language entry (documentation-status + no-data map state), which is a designed outcome, not a failure. **(b)** For v1, use **Lexibank-native Concepticon links only**; every non-linked Word displays its plain-text gloss unlinked (per gap 6.2), visually distinct from linked glosses. Automated pysem/`map_concepts` enrichment is a v2 candidate behind a human-review gate.

Runner-ups: (a) PanLex-only chain; (b) thresholded pysem auto-mapping.

---

## Consequences for the strategy

1. **§2 Phase 5 and the gap-3.2 scale estimate** must count Form-bearing languages as `(curated ∪ mined ∪ [wordlist ∩ G2P])`, not "all of Glottolog." The no-wordlist outcome becomes an explicit, expected Phase-5 category.
2. **Phase 1 seed set (§9 step 0)**: include one language expected to yield *zero* Forms, so the Form-less Language state is exercised end-to-end from the seed onward (it is hero content for the hero audience, per gap 6.1).
3. **New adapters enter the licensing gate**: PanLex (CC0 — trivial), IDS (CC-BY), Crúbadán (CC-BY — confirm per-file), eBible (per-translation triage; ND/NC files never ingested). All compatible with a CC-BY-SA-infected catalog if the mined tier forces share-alike.
4. **ADR-0002 amendment (small)**: add an "input wordlists for the generated tier" row naming the chain; record ASJP's rejection so it isn't re-proposed; note the double gate (wordlist + G2P model) in stage 1.
5. **Gloss handling in the pipeline**: stage 1 (WRAP) keeps Concepticon links where the source has them; Wiktextract glosses pass through as plain text with no mapping stage in v1 — no new pipeline stage needed.
6. **A free win recorded**: generated Forms whose input came from IDS inherit Concepticon-linked glosses, so *some* generated-tier entries will have linked Words — the tiers and the gloss-link feature are not perfectly correlated, which slightly softens gap 6.2's "near-nothing" prognosis.

---

## Open questions

1. **Transphone admission policy**: do nearest-language-approximated G2P outputs (~900 languages) enter the catalog at all, or only languages with a trained model? A linguist call; interacts with the ADR-0002 spot-check threshold. (Recommend: exclude approximated-model languages from v1.)
2. **Exact coverage join**: the 2,000–4,000-language ceiling is an estimate; compute the real `wordlist ∩ G2P ∩ Glottolog` join as a Phase-0/1 script before the Phase-5 plan is written.
3. **IDS transcription heterogeneity**: per-contributor forms may be broad-phonemic rather than orthographic (unverified — from training knowledge, cutoff Jan 2026); each IDS sub-dataset needs a one-time "orthographic enough for G2P / already phonemic (skip G2P)" triage.
4. **PanLex variety→Glottocode mapping quality** for the long tail — sample-audit during seed phase.
5. **Crúbadán per-file licensing**: the archive-level CC-BY claim should be confirmed against the actual downloadable files (crubadan.org availability has historically fluctuated; mirror early).
