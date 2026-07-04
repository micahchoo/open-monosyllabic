# Spike: map-and-misc — gaps 7.1 · 6.3 · 4.3 · 8.2 · 8.3

**Status:** complete (2026-07-03). Time-boxed spike closing the remaining small-but-real gap cluster
from [implementation-gaps.md](../implementation-gaps.md). Respects all locked decisions (UI-first,
two honesty axes, generated-never-hidden, juxtaposition-only compare, CLDF/CLTS backbone).
Verification method: web-verified where marked; anything unverifiable online is marked
*unverified — training knowledge (cutoff Jan 2026)*.

---

## Findings

### 7.1 Map tech (~2,000–3,000 dots, live recolor + click)

**Verified bundle sizes** (bundlephobia API, 2026-07-03):

| Library | Version | Minified | Gzipped | Renderer |
|---|---|---|---|---|
| `maplibre-gl` | 5.24.0 | 1,008 KB | **268 KB** | WebGL |
| `leaflet` | 1.9.4 | 145 KB | **42 KB** | DOM/SVG, opt-in canvas |
| `d3-geo` | 3.1.1 | 36 KB | **~12 KB** (API returned an implausible 1 KB; ~12 KB is the well-known figure — treat as approximate) | none (you render SVG or canvas yourself) |
| `topojson-client` | 3.1.0 | 7 KB | 2 KB | — |

- MapLibre's own docs note the tree-shaken minimum (Map + one control) is still ~210 KB gz
  ([issue #7255 / docs](https://github.com/maplibre/maplibre-gl-js/issues/7255)). It also requires a
  style + tile/glyph assets and a WebGL context — heavy machinery for a dot-distribution map.
- Leaflet at 2–3k markers is fine **only** with `L.canvas()` renderer + `CircleMarker` (DOM markers
  choke; canvas handles 12k+ per multiple field reports —
  [Leaflet #1507](https://github.com/Leaflet/Leaflet/issues/1507),
  [12k-marker writeup](https://dev.to/azyzz/performance-optimization-when-adding-12000-markers-to-the-map-that-renders-fast-with-elixir-liveview-and-leafletjs-54pf)).
  But Leaflet is tile-oriented: the default path pulls external raster tiles (an external runtime
  dependency, and a visual style that fights the locked near-monochrome "data journalism"
  direction), and it is effectively locked to Web-Mercator.
- **Projection is a mission-relevant fact, not aesthetics:** Web-Mercator visually inflates
  high-latitude (Global-North) landmass and shrinks the equatorial belt where linguistic diversity
  concentrates. An equal-area projection (Equal Earth, `d3.geoEqualEarth()`) is the honest default
  for a global language map — the same logic as the locked "observed-vs-expected, not raw count"
  heatmap rule. Only d3-geo gives this for free; Leaflet does not; MapLibre 5 has globe/adaptive
  projections but at 268 KB gz.
- 2–3k SVG circles with class-toggle recolor is comfortably within budget (this is standard d3
  territory; recolor = one attribute pass, no re-projection). If scale-out ever pushes past ~10k
  dots, the dot layer swaps to a canvas layer under the same d3-geo projection — an internal
  refactor, not a library change.
- **Static-export friendliness:** d3-geo is pure computation — no tiles, no WebGL, no external
  requests; the world outline ships as a self-hosted 110m TopoJSON (~100 KB raw, ~30 KB gz —
  *unverified, training knowledge*). SSR/prerender to SVG is trivial. Best of the three by a wide
  margin.

**Glottolog coordinates — confirmed.** Glottolog's downloads ship
`glottolog_languoid.csv` and `languages_and_dialects_geo.csv` with `latitude`, `longitude`
(WGS 84 decimal degrees, one point per languoid) and `macroarea`
(Africa / Eurasia / Papunesia / North America / South America / Australia)
([downloads](https://glottolog.org/meta/downloads),
[pyglottolog languoid docs](https://pyglottolog.readthedocs.io/en/latest/languoids.html),
[glottolog-cldf](https://github.com/glottolog/glottolog-cldf/blob/master/cldf/README.md)).
Caveats: some languoids (families, some dialects/isolates) lack coordinates or macroarea
([glottolog-cldf #31](https://github.com/glottolog/glottolog-cldf/issues/31)) — the pipeline's
stage 8 ATTACH must treat missing coords as "not mappable, still listed", never dropped.

### 6.3 Spelling→IPA search aliases

No external dependency exists or is needed: the alias index is **derived mechanically from the
canonical shape string at build time** — a pure function of data the pipeline already emits.
Derivation per shape string:

1. **NFD-decompose and strip combining diacritics** (nasalization, syllabicity marks, etc.) and
   length marks (`ː`) — the alias layer is deliberately lossier than the canonical key.
2. **Map each IPA base glyph to nearest-ASCII via one fixed table**, emitting *all* variants when
   lay spelling is ambiguous: ŋ→`ng`, ʃ→`sh`, tʃ→`ch`/`tsh`, dʒ→`j`, ʒ→`zh`, θ/ð→`th`, ɲ→`ny`/`ñ`,
   ɡ→`g`, ɾ/ɹ/ʀ→`r`, x→`kh`/`x`, ʔ→`'`/∅, j→`y`/`j`, β→`b`/`v`; vowels collapse to their base
   letter (ɑ→`a`, ɛ→`e`, ɔ→`o`, ɪ→`i`, ʊ→`u`, ə→`e`/`uh`, ø/œ→`oe`, y→`u`/`ue`).
3. **Add common lay-spelling variants** generated from the ASCII form (e.g. `oo` for `u`, `ee` for
   `i`) — a short static list, not per-language orthography (that would be a curation project, out
   of scope; the promise in ux-design.md is "plain-spelling tolerance", not orthographic search).

Result: a many-to-many `alias → {canonical shapes}` map baked into the search index. Typing `ma`
matches /ma/, /mã/, /maː/, /mɑ/; typing `nga` matches /ŋa/. Properties worth stating: **derived,
read-only, regenerated every build** (never hand-edited — it quarantines cleanly as derived
material); collisions are a feature (an alias fans out to several shapes and autocomplete shows
all, IPA-first); size is trivial (≤ ~4 aliases per distinct shape, shapes plausibly 10³–10⁴).
The alias table itself is versioned alongside the canonicalization scheme since it consumes its
output. *Mechanics unverified online — this is a design proposal, but each glyph mapping is
standard practice (cf. X-SAMPA/romanization conventions).*

### 4.3 Word row shape (polysemy)

CONTEXT.md currently holds two mildly conflicting statements: Identity says a Word is
"(Form + tone + Gloss)", Relationships says "a Word may carry more than one Gloss (polysemy)
without splitting". Resolution (per the flagged "one Word, many Glosses" default): **Word identity
= (Form + tone); glosses are a set hanging off the Word.** Proposed row:

```
Word {
  word_id:    "w:{form_id}:{tone|∅}"        # deterministic surrogate; form_id already carries
                                             # the canonicalization-scheme version → stable
  form_id:    FK → Form                      # exactly one Form (CONTEXT.md relationship)
  tone:       canonical tone label | null    # null for atonal languages; pinned value (Form
                                             # carries the *set* of tones; Word pins one)
  gloss_set:  [ { gloss: text,               # ≥1 entry
                  concepticon_id: int|null,  # null when only free-text (Wiktextract) — gap 1.6
                  source_id: FK } ]          # per-gloss provenance: different Sources
                                             # contribute different glosses
  tier:       curated|mined|generated        # per-Word tier — may differ from the Form's
                                             # (ux-design: per-Word tier badges); ratchets up only
  sources:    [source_id], one preferred     # same multi-Source/preferred pattern as Form
}
```

- Mandarin *mā* 'mother' vs *mǎ* 'horse': two Word rows (tones differ) on one Form — matches the
  CONTEXT.md dialogue exactly.
- Mandarin *mā* 'mother' vs *mā* 'to wipe' (same tone, genuinely distinct lexemes): **collapse
  into one Word row with both glosses in `gloss_set`.** Accepted v1 limitation: sources rarely
  distinguish homophony from polysemy reliably, and splitting on source-lemma would make word_id
  unstable across sources. Document it on the methodology page.
- Gloss-link UX ("same concept elsewhere") keys on `concepticon_id`; null-concepticon glosses
  render as plain text (already the accepted degradation, gap 6.2).
- CLDF mapping: Words materialize from CLDF FormTable rows (which are form+meaning pairs) grouped
  by (form, tone); `concepticon_id` rides the standard Concepticon `parameterReference`. A custom
  WordTable component in the emitted CLDF carries `gloss_set` as JSON. *(Mapping detail unverified
  online; CLDF FormTable/parameterReference semantics are standard — training knowledge.)*

### 8.2 Dataset versioning & release cadence

- **Pinning — confirmed supported by the adopted toolchain.** cldfbench takes explicit catalog
  versions (`cldfbench lexibank.makecldf --glottolog-version=v4.4 --concepticon-version=v2.5.0
  --clts-version=v2.1.0`) and records catalog/source provenance in the emitted CLDF metadata;
  `catinfo`/`catupdate` manage local clones
  ([cldfbench catalogs docs](https://cldfbench.readthedocs.io/en/latest/catalogs.html),
  [cldfbench repo](https://github.com/cldf/cldfbench)). So "source versions pinned in the CLDF
  metadata" is a native capability, not custom work: every raw Source (Lexibank dataset tags,
  NorthEuraLex release, WikiPron commit, Epitran version) is pinned in the wrap stage (stage 1)
  and lands in the metadata JSON-LD.
- **Release model:** the catalog is a **versioned build** — "data vN" — produced by a full
  pipeline re-run against a frozen pin-set. Nothing updates in place; the tier ratchet and any
  source upgrades happen only at release boundaries (which makes the ratchet auditable: diff vN →
  vN+1).
- **Cadence:** quarterly, plus ad-hoc correction releases (a preferred-tier downgrade is a
  correction event per CONTEXT.md Lifecycle and shouldn't wait a quarter). Quarterly is chosen
  over "whenever a source releases" because sources release on uncorrelated schedules and each
  build is a full re-validation.
- **Surfacing:** UI footer carries "data as of v3 · built 2026-09-30"; the About/Data-sources page
  lists the full pin-set per release (this doubles as license compliance surface, gap 8.1). Each
  release archived as a tagged artifact (GitHub release; Zenodo DOI if/when citations matter).
- **Key stability interaction (gap 4.2, already decided):** Form keys carry the
  canonicalization-scheme version, which versions **independently** of data releases — a data
  release under an unchanged scheme keeps every key stable. A Form absent from vN+1 (source
  correction) gets a tombstone state ("not in the current release") on deep-link arrival, never a
  404.

### 8.3 Segment-class / nucleus-type annotation — confirmed feasible

- **CLTS capability — confirmed.** CLTS defines sound types consonant / vowel / **diphthong** /
  cluster / tone, and each sound as a feature bundle: consonants carry manner features
  (**nasal, stop, fricative, …** — exactly the onset classes the filter UI needs); vowels carry a
  duration feature (**long / ultra-long**); diphthongs are first-class sounds with trajectory
  features ([pyclts](https://github.com/cldf-clts/pyclts),
  [CLTS feature-vector paper](https://arxiv.org/html/2405.04271v1)). `pyclts` exposes
  `sound.type` and the featureset directly.
- **CL Toolkit — confirmed.** cltoolkit is the CLDF-native layer that turns segments into Python
  objects and extracts phonological features from CLTS-linked wordlists — it's how Lexibank 2
  computes its own precomputed features ([cltoolkit](https://github.com/cldf/cltoolkit),
  [Lexibank paper](https://www.nature.com/articles/s41597-022-01432-0)). Our derivations are then
  trivial: **onset class** = manner feature of the onset segment(s); **onset complexity** =
  onset segment count (V / CV / CCV); **nucleus type** = `diphthong` if CLTS type is diphthong,
  `long` if the vowel carries the long/ultra-long feature, else `monophthong`.
- **Pipeline slot — an annotation sub-step of stage 4 (ADR-0002)**, as proposed. Stage 4 becomes:
  4a PARSE (syllabify, nucleus/coda identification — LingPy, unchanged) · **4b ANNOTATE (pyclts
  feature join: per-segment class, onset complexity, nucleus type)**. It must sit *after* stage 3
  canonicalization (features are looked up on canonical BIPA segments) and *before* stage 5
  (the openness filter consumes "nucleus is vowel/diphthong" — same join). Annotations are
  attributes emitted on the Form at stage 9. No new stage number; ADR-0002's stage list gains one
  sub-bullet, not a renumbering.
- **One real hazard:** nucleus typing is only as good as segmentation — e.g. NorthEuraLex
  transcribes some diphthongs as *sequences of simple vowels*
  ([lexibank/northeuralex #11](https://github.com/lexibank/northeuralex/issues/11)). Whether /ai/
  is one diphthong segment or two vowels is decided by the orthography profile + canonicalization
  scheme (stages 2–3) — i.e. it lands in the already-flagged human-authored corpus, not in this
  mechanical join. The annotation step itself is Adopted/mechanical.

---

## Options considered

### 7.1 Map (the one real shootout)

| | d3-geo (SVG dots, canvas-ready) | Leaflet + canvas layer | MapLibre GL JS |
|---|---|---|---|
| Gzipped cost | ~12 KB + 2 KB topojson + ~30 KB world outline | 42 KB + tile dependency | 268 KB (210 KB tree-shaken min) + style assets |
| 2–3k dots, live recolor | Yes — attribute pass on SVG; canvas swap if ever >10k | Yes — requires `L.canvas()` + CircleMarker | Yes — trivially (WebGL overkill) |
| Static export / self-contained | Best: zero external requests, SSR to SVG | Needs tiles (external) or fights the library tileless | Needs style+glyphs; WebGL context; no SSR |
| Projection honesty | Equal Earth et al. — free | Web-Mercator only (Global-North inflation) | Globe/adaptive in v5, at full cost |
| Fits locked monochrome editorial style | Fully custom — yes | Raster tiles clash; custom = fighting defaults | Custom style JSON — yes, with effort |
| Keyboard nav / ARIA on dots | SVG elements — natural | Canvas dots — manual | Canvas — manual |

Also considered and set aside: **cldfviz.map** (research.md's pointer) — its interactive output is
a standalone Leaflet HTML document, not an embeddable live-recoloring component; useful as a
QA/inspection tool during Phase 1, not as the product map.

### Other gaps
- **6.3:** per-language orthographic search (rejected — a curation project; the promise is only
  lay-IPA tolerance) vs mechanical build-time alias table (chosen).
- **4.3:** Word identity including Gloss (rejected — contradicts one-Word-many-Glosses and makes
  polysemy split Words) vs identity = (Form + tone) with gloss_set (chosen). Source-lemma split
  for same-tone homophones (rejected for v1 — unstable IDs).
- **8.2:** rolling in-place updates (rejected — unauditable ratchet, link rot) vs versioned builds
  (chosen); per-source-release cadence (rejected — uncorrelated schedules) vs quarterly + ad-hoc
  corrections (chosen).
- **8.3:** custom feature table (rejected — duplicates CLTS) vs pyclts/cltoolkit join (chosen);
  new pipeline stage (rejected — renumbering ripple) vs stage-4 sub-step (chosen).

---

## Recommendation

**7.1 — d3-geo, Equal Earth projection, SVG dot layer** (world outline from self-hosted 110m
TopoJSON via topojson-client), with a documented internal upgrade path to a canvas dot layer if
dots ever exceed ~10k. Total map cost ≈ 45 KB gz vs Leaflet's 42 KB library alone — and it is the
only option that is simultaneously static-export-clean, projection-honest (no Mercator
Global-North inflation), on-brand for the monochrome editorial direction, and SVG-accessible
(keyboard nav + ARIA per dot, a standing accessibility gate). **Runner-up: MapLibre GL JS** — pick
it only if slippy-map interaction (deep zoom to dialect clusters, basemap detail) becomes a real
requirement; Leaflet is third (tile orientation and Mercator-lock buy nothing here).

**6.3** — build-time mechanical alias index: NFD-strip diacritics + fixed IPA→ASCII table
(all-variants on ambiguity) + short lay-spelling variant list; alias → shapes map baked into the
search index; derived read-only, versioned with the canonicalization scheme. Runner-up: none
serious (per-language orthography search is out of scope by the ux-design promise).

**4.3** — Word identity = (form_id, tone); row = `{word_id (deterministic), form_id, tone|null,
gloss_set: [{gloss, concepticon_id|null, source_id}], tier, sources[] (one preferred)}`; same-tone
homophones collapse into one Word (documented limitation). Runner-up: identity including Gloss —
rejected as it contradicts the one-Word-many-Glosses resolution.

**8.2** — pin all source/catalog versions in CLDF metadata via cldfbench (native support,
verified); ship the catalog as versioned builds "data vN" on a quarterly cadence + ad-hoc
correction releases; surface "data as of vN · built date" in the UI footer and the full pin-set on
About/Data-sources; tombstone (never 404) Forms absent from the current release. Runner-up:
release-driven cadence.

**8.3** — confirmed: pyclts/cltoolkit provide segment class (nasal/stop/fricative…), diphthong as
a first-class sound type, and long-vowel duration features. Adopt as **stage 4b ANNOTATE**, a
sub-step of ADR-0002's stage 4 (after canonicalization, before the stage-5 openness filter, which
consumes the same join). Runner-up: none — this is a confirmation, not a fork.

---

## Consequences for the strategy

1. **IMPLEMENTATION-STRATEGY §4 (Adopted row):** replace "cldfviz **interactive/Leaflet** map
   rendering" with "d3-geo + topojson-client map rendering (Equal Earth; SVG dots)"; cldfviz.map
   demotes to a Phase-1 QA/inspection tool. Still Adopted-tier (donor examples abundant), so the
   reducibility classification is unchanged.
2. **ADR-0002:** add stage 4b ANNOTATE (pyclts feature join) as a sub-bullet; note Glottolog
   coordinate/macroarea gaps handled at stage 8 ("no coords ⇒ listed but unmapped, never
   dropped"); note source-version pinning at stage 1 is the 8.2 mechanism.
3. **Phase 0:** the versioning/release policy (8.2) folds into the delivery-model decision — a
   quarterly-rebuilt static bake is now the coherent default posture (versioned builds are
   *native* to static delivery).
4. **Phase 1 schema work** picks up the Word row (4.3) directly; CONTEXT.md's Identity section
   needs its one-line amendment (Word = Form + tone; Gloss moves out of the identity key) and the
   polysemy "not yet resolved" flags clear.
5. **Phase 2/3:** search index build gains the alias-derivation step (6.3) — a pure build-time
   function, no new pipeline stage; map component tasks cite d3-geo donors.
6. **Three-state map + Equal Earth** reinforce the honesty spine: the projection choice should be
   one line on the About/methodology page (it *is* an observed-vs-expected style decision).

## Open questions

- **Homophone collapse (4.3):** is "same Form + same tone ⇒ one Word, merged gloss_set"
  acceptable to the domain owner, or should source-lemma distinctions split Words despite ID
  instability? (Proposed default: collapse; needs a nod.)
- **Tone label canonicalization:** the `tone` field needs a canonical label scheme (Chao digits
  vs diacritics vs source-native) — belongs with the canonicalization-scheme authoring (already a
  flagged human task), not decided here.
- **World-outline asset size** (~30 KB gz for 110m TopoJSON) is from training knowledge,
  unverified online; confirm when the asset is actually vendored.
- **Quarterly cadence** is a proposal about team capacity, not a technical fact — the human should
  confirm the rhythm once real re-ingestion cost is known (after Phase 5's first scale-out).

## Sources

- [Glottolog downloads](https://glottolog.org/meta/downloads) · [pyglottolog languoid docs](https://pyglottolog.readthedocs.io/en/latest/languoids.html) · [glottolog-cldf README](https://github.com/glottolog/glottolog-cldf/blob/master/cldf/README.md) · [glottolog-cldf #31 (missing macroareas)](https://github.com/glottolog/glottolog-cldf/issues/31)
- [bundlephobia: maplibre-gl](https://bundlephobia.com/package/maplibre-gl) · [bundlephobia: leaflet](https://bundlephobia.com/package/leaflet) · [MapLibre bundle-size issue #7255](https://github.com/maplibre/maplibre-gl-js/issues/7255) · [MapLibre GL JS docs](https://maplibre.org/maplibre-gl-js/docs/)
- [Leaflet #1507 canvas perf](https://github.com/Leaflet/Leaflet/issues/1507) · [12k-marker Leaflet canvas writeup](https://dev.to/azyzz/performance-optimization-when-adding-12000-markers-to-the-map-that-renders-fast-with-elixir-liveview-and-leafletjs-54pf) · [leaflet-marker-booster](https://github.com/oliverheilig/leaflet-marker-booster)
- [pyclts](https://github.com/cldf-clts/pyclts) · [CLTS](https://github.com/cldf-clts/clts) · [CLTS feature vectors (arXiv 2405.04271)](https://arxiv.org/html/2405.04271v1) · [cltoolkit](https://github.com/cldf/cltoolkit) · [Lexibank paper (Sci Data)](https://www.nature.com/articles/s41597-022-01432-0) · [northeuralex #11 (diphthongs as vowel sequences)](https://github.com/lexibank/northeuralex/issues/11)
- [cldfbench catalogs docs](https://cldfbench.readthedocs.io/en/latest/catalogs.html) · [cldfbench](https://github.com/cldf/cldfbench)
