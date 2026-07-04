# Spike — Heatmap Bucketing (gaps 5.1 + 5.2)

**Status:** spike complete — candidate structure + decision framework, pending Phase-1 validation (per terms of reference: designed WITHOUT real data; §Phase-1 checks below lists what would overturn it).
**Closes:** `implementation-gaps.md` §5.1 (unbounded axes) and §5.2 (cell-vs-class contradiction).
**Respects (locked):** UI-first · never-a-bare-count · tier composition in every count · observed-vs-expected intensity preferred · filtered cells dim **in place** (spatial stability) · `generated` never hidden · list toggle as accessible fallback · single-hue sequential color owned by the heatmap.

---

## Findings

### F1 — The axes are genuinely unbounded, but the *class* layer is not

PHOIBLE registers **3,183 segment types across 2,186 languages** (research.md §Methodology; [PHOIBLE 2.0](https://phoible.org/)). Even after CLTS BroadIPA canonicalization collapses notational variants, a full cross-language onset axis is hundreds of rows — unrenderable and unglanceable, as gap 5.1 states. But CLTS assigns every sound a **feature bundle** — e.g. [p] = ('voiceless', 'bilabial', 'stop', 'consonant') — via the `pyclts` API ([Anderson et al. 2018](http://lingulist.de/documents/papers/anderson-et-al-2018-cross-linguistic-transcription-systems.pdf); [CLTS catalog](https://clts.clld.org/); [cldf-clts/clts](https://github.com/cldf-clts/clts); [SoundVectors/CLTS feature vectors](https://calc.hypotheses.org/7224)). So a **manner-class row axis (~7 classes + ∅ + complex)** and a **height/backness vowel-bucket column axis (~6 buckets + diphthongs)** are *mechanically derivable from the pipeline we already adopted* (ADR-0002 stage 3 canonicalizes into CLTS; gap 8.3's feature-join stage produces exactly these tags). The class layer is closed and small; only the segment layer is open-ended.

### F2 — A "top-N pan-language segments" axis is feasible but mission-inverting

The most frequent segments are extremely concentrated: **/m/ in ~96% of languages, /k/ ~90%, /i/ ~94%, /u/ ~88%** in PHOIBLE ([PHOIBLE FAQ](https://phoible.github.io/faq/); [Everett 2021, Phil. Trans. R. Soc. B](https://royalsocietypublishing.org/rstb/article/376/1824/20200198/31472/Inferring-recent-evolutionary-changes-in-speech); [vowel inventory statistics](https://www.eksss.org/archive/view_article?pid=pss-16-3-1)). A fixed top-20-onsets × top-10-vowels grid would therefore cover most attestations. **But** frequency-ranked axes push exactly the segments concentrated in under-documented languages — clicks, implosives, ejectives — into an "other" gutter. ux-design.md already rules that "a raw scale rewards data-dense (Global-North) languages and inverts the mission"; a frequency-ranked *axis* does the same thing structurally. This disqualifies top-N as the *primary* organizing principle, while leaving it valid as the *within-class truncation* rule (F4).

### F3 — The 5.2 contradiction dissolves once the grid has two levels

"Cell = one Shape" and "rows = onset class" are only contradictory on a single-level grid. On a two-level grid they are statements about different levels: at the **class level** a cell is a *bucket of Shapes* (an aggregate with tier composition), and at the **segment level** a cell is *one Shape* (the IPA-picker semantics). The Filter UI's onset-class checkboxes then map 1:1 onto row groups — one vocabulary across landing and filters, which is what gap 5.2 (c) asks for.

### F4 — Expansion must itself be bounded

A naïve "expand class → all member segments" re-imports the unbounded axis (fricatives alone can exceed 30 BroadIPA types across languages). Expansion needs the same discipline: **top ~12 segments by attested-language count + an "other ‹class›" gutter row inside the expansion**, with the gutter expandable to a list. Gutters *defer*, never *hide* — clicking one opens the full ranked list (the list-toggle machinery reused).

### F5 — "Observed-vs-expected" has a concrete, already-planned denominator

The honest intensity ux-design asks for needs an expectation baseline. The pipeline already produces one: ADR-0002 **stage 7** validates against PHOIBLE inventories and **stage 8** attaches prosodic-type/word-minimality. So *expected(cell)* = languages whose PHOIBLE inventory contains ≥1 segment in the cell's row class **and** ≥1 vowel in its column bucket, **and** whose prosodic type permits open light monosyllables (research.md §1: minimality bans are structural, not noise). Intensity = observed/expected languages; the raw tier-composition counts stay in the cell label/hover. This turns "structurally can't have it" into a low denominator instead of a misleading dark cell — the same three-state honesty the map already commits to.

### F6 — Structural homes exist for every awkward shape class

- **V-only (∅-onset) forms** (ADR-0001 includes them; the complexity toggle already names "V"): a dedicated **∅ row**, pinned first.
- **Diphthong-final shapes** (ADR-0001 includes them; they carry lower Classification Confidence): a **"diphthongs" column group** after the monophthong buckets, expanding to individual diphthongs grouped by first-element quality. Keeping them a *column* group is right because the diphthong is the *nucleus* — the vowel axis is where it belongs.
- **CCV+ complex onsets**: a **"CC+" row group** pinned last, expanding to attested clusters ranked by attestation + gutter. A row group (not a gutter) because onset complexity is a first-class filter dimension (V/CV/CCV toggle).
- **Non-pulmonic onsets** (clicks, implosives, ejectives): their **own class row**, not a gutter — the mission-sensitive case from F2.
- **Long/nasalized vowels**: bucketed by *base quality* (bucket assignment reads CLTS height/backness only); whether they are distinct Shapes at segment level is the canonicalization-scheme decision (ADR-0002 open sub-decision) — the bucketing is robust to either outcome.

---

## Options considered

| | Scheme | Max cells (default → worst) | Diphthongs | V-only | CCV+ | Glanceable? | Honest intensity? |
|---|---|---|---|---|---|---|---|
| **A** | **Two-level drill**: class rows × vowel-bucket columns, expand-in-place to segments (top-12 + gutter per class) | **63 → ~300** | column group → expands by first element | ∅ row | CC+ row group → expands to clusters | **Yes** — 9×7; class labels match filter vocabulary | Yes — obs/exp per cell (F5); tier glyphs at both levels |
| B | **Fixed top-N segment grid**: top ~20 onsets × top ~10 vowels + "other" gutters | ~230 fixed | one gutter column | ∅ row | gutter row | Borderline — 200+ cells of bare IPA glyphs assumes IPA fluency | Yes mechanically, but axis itself is frequency-biased (F2) |
| C | **Per-language / per-filter adaptive grid**: axes recomputed from current selection | varies | wherever data puts them | varies | varies | Locally yes | **Violates locked decision**: axes reflow under filters — "cells dim in place, spatial map stays stable" becomes impossible; no stable spatial memory across states |
| D | **Sonority-ordered continuous full-segment axes** (dense zoomable matrix) | hundreds × dozens | ambiguous (glide-adjacent?) | edge row | no 2-D home | No — a pixel-density texture, not a picker; research.md notes ~half of languages violate sonority ordering anyway | Per-cell yes, but unreadable at grid scale |
| E | **Asymmetric single-level**: class rows × *individual* vowel-quality columns (~9 × ~15) | ~150 fixed | column group (unexpanded) | ∅ row | CC+ row | Marginal — 15 IPA vowel columns up front | Yes, same as A |

**Why A over the runner-up (B):** B is simpler to build and its cell semantics are uniform ("cell = one Shape" everywhere), but (i) it structurally gutters the under-documented languages' segments (F2), quietly re-introducing the raw-count mission inversion ux-design explicitly forbids at the *encoding* level; (ii) 200+ raw IPA glyph headers make the grid a specialist tool, while class rows ("nasal", "stop") are the no-IPA-fluency-required vocabulary the Filter UI already committed to; (iii) B has no graceful path to the long tail — "other" is a dead end, whereas A's expansion *is* the drill.
**Why not C:** direct conflict with the locked spatial-stability decision. **Why not D:** discards glanceability, the hero's entire job; sonority survives as a *row-ordering* principle inside A, not a scheme. **Why not E:** pays A's worst-case cost on every load without A's progressive disclosure.

---

## Recommendation

**Adopt Scheme A — a two-level drill grid, class-level by default, expanding in place to segments.**

### Default (level 1) — 9 rows × 7 columns = 63 cells

**Rows** (onset classes, ordered by sonority distance from the nucleus — a gradient, using D's ordering insight):

1. **∅** (no onset — V-only shapes)
2. Glides/approximants
3. Liquids (laterals + rhotics)
4. Nasals
5. Fricatives
6. Affricates
7. Plosives
8. Non-pulmonic (clicks, implosives, ejectives)
9. **CC+** (complex onsets — row group)

**Columns** (nucleus buckets, front→back then diphthongs): i-type (high front) · e-type (mid front) · a-type (low) · central (ə-type) · o-type (mid back) · u-type (high back) · **Diphthongs** (column group).

Class/bucket assignment is a **mechanical CLTS feature join** (F1) — it is the gap-8.3 stage made concrete, and its mapping corpus is authorable *now* (segment → class, vowel → bucket), not blocked on Phase 1.

### Expansion (level 2)

- Clicking a **row-group header** (or a class-level cell) expands that class in place into its member segments: **top 12 by attested-language count + "other ‹class›" gutter row**; the gutter opens a ranked list. Same for a vowel bucket (→ qualities) and the diphthong group (→ diphthongs grouped by first element). Expansion is an in-place accordion: unexpanded groups keep their order and identity, so filter-dimming stays spatially stable.
- Worst case (one row group + one column group expanded): ≈ 21 × 14 ≈ **300 cells** — bounded, renderable (GitHub's contribution graph is 371).

### Cell semantics (resolves 5.2)

| Level | Cell is | Click does | Count shown |
|---|---|---|---|
| Class × bucket (default) | a **bucket of Shapes** | **expands** (zooms into the region) — never "picks" | "N shapes · M languages" + tier glyphs (● ◐ ○) |
| Segment × quality (expanded) | **one Shape** — the ux-design "cell = one Shape" holds *here* | **picks** the shape (IPA-picker semantics; map lights) | "M languages" + tier glyphs |

The onset-class filter checkboxes and the V/CV/CCV toggle map 1:1 onto row groups (∅ row = "V"; CC+ group = "CCV"). One vocabulary everywhere.

### Honest intensity

- **Intensity = observed/expected languages** per cell, denominator from the PHOIBLE-inventory join × prosodic-type attribute (F5). Until that join is validated, fall back to tier-composition display with raw density explicitly labeled provisional (never a bare count in either mode).
- Aggregated (class-level) cells count each language **once, at the highest tier of any contributing Form** in that cell; tier glyphs render at both levels; gutter cells carry identical treatment.

**Runner-up:** Scheme B (fixed top-N segment grid + gutters) — adopt it wholesale only if Phase-1 check P1-1 below fires; its top-N ranking already lives inside A's expansions.

---

## Consequences for the strategy

1. **Phase 2's blocking OPEN item becomes a validation, not a design.** IMPLEMENTATION-STRATEGY §2 Phase 2 ("heatmap-bucketing decision resolved against the seed's real distribution") and §8 ("discovered later") should now read: *validate Scheme A against the seed using the P1 checks below*; the design pass is done.
2. **Reducibility reclassification (§4/§5):** the class/bucket **mapping function** graduates from "greenfield-after-invented-gate" to **greenfield-specifiable now** — its corpus (segment → class row, vowel → bucket, diphthong → first-element group) reads off CLTS features and can be authored alongside the canonicalization corpus. Only the **threshold validations** (below) still wait on Phase 1.
3. **Pipeline emit gains one requirement (gap 8.3 made concrete):** the CLTS feature join must emit, per Form: onset class · onset complexity (∅/C/CC+) · nucleus bucket · nucleus type (monophthong/diphthong) · and, per Language, the inventory-derived *expected-cell flags* (F5) so the heatmap's denominator ships with the data, not computed client-side from raw PHOIBLE.
4. **ux-design.md §Landing needs a wording amendment** (provenance-tracked): "cell = one Shape" scoped to the expanded level; default level declared class × bucket; the ⚠️ UNRESOLVED block replaced by a pointer to this spike + Phase-1 validation.
5. **The list toggle inherits the same two-level structure** (class-grouped list → segments) — accessible fallback comes free, no separate IA.
6. **UI scaffolding can start** (the Phase-1-parallel exception in §2): the accordion-grid component's shape is now known; it binds to the seed emit when green.

---

## Phase-1 data checks that would overturn this choice

| # | Check on the seed distribution | Threshold | If it fires |
|---|---|---|---|
| P1-1 | **Concentration:** share of Shapes in the busiest quartile of level-1 cells | ≥ 80% | Class default is mostly dead cells → switch to Scheme B (top-N grid), keep gutters |
| P1-2 | **Expansion width:** within-class "other" gutter mass after top-12 truncation | gutter > 20% of a class's attestations | Re-cut that class (e.g. split fricatives by place) or raise N for it |
| P1-3 | **Diphthong mass:** diphthong-final share of all Shapes | > 25% | One column group under-serves them → promote to per-first-element column groups at level 1 |
| P1-4 | **Complex-onset mass:** CCV+ share | < 2% → collapse CC+ to a single gutter row; > 15% → CC+ gets its own cluster-type sub-axis | either way, row-group design changes |
| P1-5 | **Denominator coverage:** seed languages with usable PHOIBLE inventories + prosodic-type attribute | < ~80% | Observed-vs-expected intensity infeasible at launch → ship tier-composition intensity, labeled provisional (already the fallback) |
| P1-6 | **Non-pulmonic row:** empty in seed *and* projected empty at scale | — | Demote to gutter (keep at seed stage regardless; the seed set may just lack click languages) |
| P1-7 | **Tier homogeneity per cell:** most cells single-tier vs mixed | mostly mixed | In-cell tier glyphs mandatory (not hover-only); mostly single-tier → glyphs may move to hover, badge stays |

## Open questions

- **Class-boundary calls** a linguist should bless: do glides and liquids merge into one "approximant" row? Where does /h/ sit (fricative row vs a laryngeal home)? Small, but they change row count.
- **Long/nasalized vowels as distinct Shapes** — owned by the open canonicalization-scheme sub-decision (ADR-0002); bucketing is robust either way, but the expanded column inventory depends on it.
- **Diphthong expansion grouping** — first-element quality is the default here; second-element grouping is defensible; validate against seed which reads better.
- **Level-1 click affordance** — expand-on-cell-click vs expand-only-on-header (cells could instead *preview* the bucket on the map); an interaction-design call for Phase 2's `interface-design` pass, not a structure call.

---

*Sources:* [PHOIBLE 2.0](https://phoible.org/) · [PHOIBLE FAQ](https://phoible.github.io/faq/) · [Everett 2021, Phil. Trans. R. Soc. B](https://royalsocietypublishing.org/rstb/article/376/1824/20200198/31472/Inferring-recent-evolutionary-changes-in-speech) · [Anderson et al. 2018, CLTS](http://lingulist.de/documents/papers/anderson-et-al-2018-cross-linguistic-transcription-systems.pdf) · [CLTS catalog](https://clts.clld.org/) · [cldf-clts/clts (GitHub)](https://github.com/cldf-clts/clts) · [SoundVectors & CLTS](https://calc.hypotheses.org/7224) · [Vowel inventory statistics (Phonetics Speech Sci.)](https://www.eksss.org/archive/view_article?pid=pss-16-3-1) · project docs (CONTEXT.md, ADR-0001/0002, ux-design.md, research.md, implementation-gaps.md §5).
