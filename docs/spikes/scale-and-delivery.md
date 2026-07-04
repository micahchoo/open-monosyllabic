# Spike: Scale & Delivery Model (gaps 3.1 + 3.2 + 3.3)

**Date:** 2026-07-03 · **Status:** complete · **Decision proposed:** delivery model = **static-baked hybrid** (build-time core index + lazy per-shape chunks; no backend).

Terms of reference: [implementation-gaps.md](../implementation-gaps.md) §3.1 (static vs live), §3.2 (scale estimate), §3.3 (shape→languages query substrate). Respects the locked decisions (UI-first, URL-state deep links, live heatmap+map recolor, client-side filters, generated-never-hidden, CLDF/CLTS backbone per [ADR-0002](../adr/0002-data-sourcing-and-ingestion-pipeline.md)).

---

## Findings

### F1 — Verified source magnitudes

| Fact | Value | Verification |
|---|---|---|
| Lexibank 2 coverage | **>3,100 languages, >1.5M word forms** (up from ~2,400 varieties / 100 datasets in Lexibank 1) | Verified via [Lexibank 2 data note (Blum et al. 2025, PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12134731/), [Zenodo record](https://zenodo.org/records/15726826) |
| WikiPron | **>3M word/pronunciation pairs** (paper figure: 1.7M / 165 languages) | Verified via [CUNY-CL/wikipron README](https://github.com/CUNY-CL/wikipron) |
| PHOIBLE 2.0 | 2,186 languages / 3,020 inventories | From research.md (previously verified; not re-checked) |
| NorthEuraLex | 1,016 concepts × 107 languages | From research.md |
| Vietnamese syllables | ~6,500 in use (of ~19,000 possible), **tone included** | From research.md (Nguyen et al., arXiv:1904.05569) |
| Cloudflare Pages static limits | **max 20,000 files; 25 MiB per file** (hard limits) | Verified via [Cloudflare Pages limits docs](https://developers.cloudflare.com/pages/platform/limits/) |
| WALS syllable-structure split | simple 12.5% · moderate 56.5% · complex 30.9% | From research.md (Maddieson, WALS ch. 12) |

### F2 — Back-of-envelope catalog scale (gap 3.2)

**Estimation logic** (all per-language yields are estimates — unverified, reasoned from the verified magnitudes above and research.md §1's minimality bias):

- **Languages.** Ceiling = union of Lexibank 2 (>3,100) + mined (WikiPron ~165–500 langs) + G2P long tail. Realistic full catalog: **~2,000–3,000 languages with ≥1 Form** (many Lexibank varieties will yield zero after the openness filter). v1 = the 6–10 seed languages (IMPLEMENTATION-STRATEGY §9); first scale-out realistically **~1,500–2,500**.
- **Forms per language — three structural regimes** (this is the minimality-bias adjustment):
  - **Banned/thin** (~30–40%: complex-syllable and bimoraic-minimality languages): **0–5** Forms. Low yield is a finding, not noise (ADR-0002 consequence).
  - **Moderate** (~50%: curated-wordlist-only, 100–400 concepts sampled): **5–30** Forms. Sanity check: Lexibank 2's ~1.5M forms / ~3,100 languages ≈ ~500 forms per language sampled; if 3–10% survive the open-monosyllable filter → 15–50/language, consistent.
  - **Mined-rich monosyllabic** (~100–300 languages with deep Wiktionary lexicons, esp. SEA/Sinitic/West African): **hundreds each**. Worked example — Vietnamese: ~6,500 tonal syllables ÷ ~6 tones ≈ ~1,100 segmental syllables; zero-coda fraction ~25–45% → **~300–500 Forms** (up to ~700 if contested vowel+glide finals are analyzed as diphthong nuclei per ADR-0001 — exactly where Classification Confidence concentrates). Mandarin: ~400 toneless syllables, ~60% open (no -n/-ŋ) → **~250 Forms**.
- **Words per Form:** curated ≈ 1 (one Concepticon-linked Word per wordlist hit); mined-rich ≈ 2–6 (homophony + tone splits concentrate in monosyllables — Mandarin /ma/ alone is 4+ Words); generated ≈ 0 (no gloss). Mean **~1.2–3 where Words exist**.
- **Distinct Shapes** (cross-language canonical strings): bounded by attested BroadIPA onset union (low hundreds) × nucleus union (~50–100 incl. diphthongs), sparsely attested → **~3k–20k distinct Shapes**, mid ~8–12k.

**Totals:**

| Scenario | Languages | Forms | Words | Raw JSON | Gzip (measured, optimistic) | Gzip (realistic budget) |
|---|---|---|---|---|---|---|
| **Low** (v1 scale-out, curated-heavy) | ~1,500 | **~25k** | ~30k | ~5 MB | ~0.5 MB | ~1–2 MB |
| **Mid** (full curated + mined) | ~2,500 | **~125k** | ~250k | ~34 MB | ~3.4 MB | ~6–12 MB |
| **High** (full + G2P long tail + deep mined) | ~3,000 | **~500k** | ~1.5M | ~177 MB | ~19 MB | ~40–80 MB |

Payload sizes were **measured** on synthetic full-fidelity records (form: lang, shape, tones, tier, classification confidence, sources; word: tone, gloss, Concepticon id, tier, source) via a local script: **~90 bytes raw JSON per record**; gzip on synthetic data compressed to ~9 B/record, which is optimistic because synthetic glosses/sources repeat — the "realistic budget" column doubles-to-quadruples it. Either way the shape of the conclusion is robust (see F4).

### F3 — What the UX constraints force (gap 3.1 inputs)

- **URL-state deep links + shareability** → client-routable state; any model must resolve a URL to a view without server session state.
- **Live heatmap recolor + live map recolor + live match counts with tier composition on every filter change** → the *aggregate layer* (per-shape language lists with tiers, per-language attributes) must be **in browser memory**. A round-trip per filter tick is a Doherty violation and is strictly worse than a client-side groupby. This holds **regardless of whether a backend exists** — so a backend could only ever serve the drill-down layer.
- **Dataset is read-only between ingestion runs** (ADR-0002: pipeline is re-runnable batch; tier ratchet happens at re-ingestion, not at request time). No user writes, no auth, no personalization anywhere in the locked UX.

### F4 — Measured artifact sizes for the hybrid split (gap 3.3 inputs)

Measured with the same script, at **mid** scale (125k form-entries, 2,500 languages):

- **Core inverted index** (language table with glottocode/name/coords/macroarea/doc-status/prosodic-type + shape→postings map with per-posting `[langIdx, tierCode]`): **~1.3 MB raw / ~0.35 MB gzip**. Even at high scale with 20k distinct shape keys this stays **≤ ~4 MB raw / ~1 MB gzip** — comfortably a single first-load fetch.
- **Per-shape detail chunk** (40 languages' Forms with ~2.5 Words each, realistic gloss entropy): **~12.5 KB raw / ~1.5 KB gzip**. Popular shapes (/ma/ everywhere) might reach 10–30 KB gzip; the long tail is <2 KB.
- Total static footprint at high scale: ~20–80 MB gzip across all chunks — trivial for any static host/CDN. Only constraint found: **Cloudflare Pages' 20,000-file limit** collides with 3k–20k shape chunks + language chunks + concept chunks at the high end (mitigate: shard multiple shapes per file, or host data on R2/a bucket; Netlify/GitHub Pages don't share this limit).

---

## Options considered

### A — Fully static, single baked blob
One `catalog.json` shipped to every client. **Viable at Low only** (~1–2 MB gz); at Mid it's a 6–12 MB gz / 34 MB-in-memory parse on first paint; at High it's dead (40–80 MB gz). Also re-downloads everything on any data version bump. *Correct as the Phase-2 seed-scale degenerate case, wrong as the model.*

### B — Live backend (API + DB: Postgres/clld, or serverless SQLite e.g. Datasette)
Indexes and queries scale effortlessly; shape→languages is one indexed query. But: F3 shows the hot loop (filters, recolor, counts) must be client-side anyway, so the backend only serves what lazy static chunks already serve at CDN speed; the dataset is read-only batch-updated, so there is *nothing for a server to compute at request time that a build step can't precompute*; and it adds permanent ops cost, a failure domain, and a threat surface to a project whose spine is a permanent, citable, FAIR reference (deep links should outlive any server). clld exists as prior art for the *ecosystem*, but our UX (client-side live interaction) is exactly what clld's server-rendered model is not.

### C — Static-baked hybrid: core index up front + lazy per-shape/per-language chunks ✅
Ship the ~≤1 MB-gz core inverted index at load (powers heatmap, map, filters, counts, list view, autocomplete seed — every "live" surface); lazy-fetch immutable per-shape chunks (~1.5–30 KB gz) when a bottom sheet/compare/gloss-jump needs Forms+Words detail. Scales from seed (where core index ≈ the whole dataset, i.e. option A falls out for free) to High (500k Forms) without changing the model. CDN-cacheable, offline-friendly, zero ops, deep links resolve entirely client-side.

*(Parquet/Arrow instead of JSON was considered for the core index: rejected for v1 — needs a wasm reader and the measured JSON-gz sizes don't justify it. Revisit only if the core index exceeds ~5 MB gzip.)*

---

## Recommendation

**Delivery model (FIRM): static-baked hybrid — build-time-baked data artifacts served as static files: one eagerly-loaded core inverted index + lazily-fetched per-shape (and per-language, per-concept) detail chunks. No backend, no database at request time.** Runner-up: fully-static single blob (option A) — it is in fact the same architecture at seed scale and Phase 2 should literally ship it; it merely fails to survive Mid scale as the end state. Live backend (option B) is rejected: the numbers never require it, the UX forbids depending on it for the hot loop, and it taxes the project's permanence.

### The inverted-index specification (gap 3.3)

A **BAKE step downstream of ADR-0002 stage 9** (a consumer of the emitted CLDF, not a 10th pipeline stage — the CLDF output stays delivery-agnostic per IMPLEMENTATION-STRATEGY §9) produces three artifact families under a **canonicalization-versioned path** `data/{canon-version}/…` (immutable, cache-forever; protects deep links per ADR-0002's key-versioning consequence and gap 4.2):

1. **`core.json`** (split into `languages.json` / `shapes.json` / `heatmap.json` if parallel loading helps):
   - **Language table** (array; array index = `langIdx` used everywhere else): glottocode, name, lat/lon, macroarea, documentation-status, prosodic-type/word-minimality. Powers the map's three states (present / no-data / structurally-absent) and all filter facets.
   - **Shape table**: canonical BroadIPA string, `onsetClassId`, `onsetComplexity` (V/CV/CCV…), `nucleusTypeId` (monophthong/diphthong/long), and **postings** — a packed array of `[langIdx, tierCode, ccCode]` triples (columnar arrays of ints, gzip-friendly). Storing onset-class/nucleus-type *per shape in the index* means the still-OPEN heatmap bucketing scheme is a client-side groupby — the bucketing decision stays cheap to change and never forces a re-bake.
   - Everything "live" derives from this in memory: heatmap cells with tier composition (never a bare count), live match counts, removal counts ("would remove 8 languages"), map recolor, list toggle, filter chips.
2. **`shape/{slug}.json`** — all Forms for that Shape across languages, each with tones, both honesty axes, Sources (all, preferred marked), and embedded Words (tone, gloss, Concepticon id, per-Word tier). Powers the bottom sheet and the compare route. Slug = deterministic URL-safe encoding of the canonical string (NFC + percent-encoding, or a short content hash with the string inside the file); shard into subdirectories (e.g. by first segment) to stay under per-directory and host file-count limits.
3. **`lang/{glottocode}.json`** and **`concept/{concepticonId}.json`** — the per-language deep-dive fast-follow and the gloss-link jump ("same meaning elsewhere"), same chunk pattern.

Client contract: a single `DataStore` loader abstracts "core index in memory + chunk fetch with LRU cache"; at seed scale the loader is handed one blob and the UI cannot tell the difference — Phase 2 ships against the same API Phase 5 scales under.

Search-bar autocomplete runs over the in-memory shape table (plus the plain-spelling alias map, gap 6.3 — out of this spike's scope but it lives in the same core index when decided).

### Stack candidates (loosely held — the delivery model above is the firm decision)

- **Framework:** Astro (islands; content/editorial-friendly, matches the data-journalism direction) › SvelteKit `adapter-static` › Next.js static export. All three satisfy static export + client routing for URL state; choose at Phase-2 decomposition via `interface-design`/donor criteria.
- **Hosting:** Netlify or GitHub Pages (no file-count ceiling of note) or Cloudflare Pages **with data on R2** if chunk count nears the verified 20k-file limit.
- **Map:** MapLibre GL JS › Leaflet › d3-geo (interactive vector, satisfies "recolors live"; gap 7.1's static-PNG path is confirmed dead).

---

## Consequences for the strategy

- **Phase 0's "tech/delivery decision" closes: static-baked hybrid.** The Phase-2 gate (delivery model gates UI consumption) lifts. Framework choice remains a Phase-2 leaf decision, deliberately loosely held.
- **Add the BAKE step** as a Phase-1/Phase-2 seam deliverable: Greenfield-specifiable (corpus: CLDF fixture → expected `core.json`/`shape/*.json` artifacts; binary acceptance). It consumes stage-9 CLDF and never reaches back into the pipeline.
- **Phase 2 builds against the `DataStore` contract** with the seed baked as a single blob — honoring UI-first while making the Phase-5 chunking swap invisible to every UI component.
- **Phase 5 gains two measurable tripwires:** core index > ~5 MB gzip → move postings to packed binary (typed arrays / Arrow), not to a backend; chunk-file count > ~15k on Cloudflare Pages → shard or move data to R2. Re-run this spike's estimate against the real Phase-1 distribution at Phase-5 entry.
- **Deep-link permanence is structural:** versioned `data/{canon-version}/` paths + client-side resolution mean shared URLs survive reprocessing (closes the delivery-side of gap 4.2) and the site can be archived/mirrored whole — aligned with the FAIR/citable spine.
- **Licensing (Phase-0 gate) now explicitly covers redistribution:** a static bake *is* redistribution of derived data; the CC-BY-SA share-alike question (gap 8.1) must be cleared for every baked Source — unchanged in substance, but the static model makes it unambiguous.

## Open questions

1. **Real yield distribution** — the Low/Mid/High estimates are reasoned, not measured; Phase 1's seed pipeline produces the first real numbers, and Phase-5 entry should re-check Mid (~125k Forms) before scale-out.
2. **Plain-spelling alias index** (gap 6.3) — size and source of the spelling→IPA map are unestimated; it must fit the core-index budget or become its own lazy chunk.
3. **Audio storage** — thousands of clips are outside this spike; they will want a bucket (R2/S3) regardless of the delivery model. Feeds the Phase-4 spike.
4. **Same-tier tiebreak & polysemy** (ADR-0002 open items) — affect chunk record shape (preferred-Source marking, multi-gloss Words) but not the delivery model.

---

*Method note: payload figures measured locally (Python, synthetic full-fidelity records, gzip level 6); synthetic gzip ratios are optimistic and the report budgets 2–4× above them. External magnitudes verified 2026-07-03 via: [Lexibank 2 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12134731/) · [Lexibank 2 (Zenodo)](https://zenodo.org/records/15726826) · [WikiPron (GitHub)](https://github.com/CUNY-CL/wikipron) · [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/). Per-language yield regimes, Vietnamese/Mandarin worked examples, and Words-per-Form means are estimates — unverified, from reasoning over research.md's verified figures.*
