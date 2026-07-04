# UX / UI Design Decisions

Companion to [CONTEXT.md](../CONTEXT.md) (domain model) — captures interface decisions as they crystallize during grilling. Product/IA decisions, not domain facts; feeds the eventual IMPLEMENTATION-STRATEGY.

## Primary axis

Enter by **Shape** (e.g. /ma/) → see every Language that has it. Shape is a query-time grouping, not a stored entity, but it is the primary UI object.

> **REVISED (post-implementation, real-data feedback).** Meaning is now the **hero axis**, sound the secondary lens. The original Shape-first choice was made when we feared gloss data would be too sparse to lead with; real ingestion disproved that (93% of glosses are Concepticon-linked, 521 concepts). The delight is meaning-first — "**41 languages express 'water' as an open monosyllable, using just 13 sound-shapes**". So the app now defaults to a **Meanings** view (concepts ranked by cross-language reach, showing sound↔meaning convergence) with the onset×vowel heatmap kept as the **Sounds** lens, and meaning↔sound cross-links both ways. Implemented: concept index in `core.json` + `concept/{ckey}.json` chunks (`oms/bake.build_concepts`); shareable `#c=<ckey>` deep links.

## First-class filters

**Onset** (initial consonant / onset class) and **Confidence Tier**. Nucleus type and tone are displayed attributes, not primary filters.

## Landing screen — heatmap hero + map result

A single-screen "pick a shape → see it on the globe" loop:

- **Hero: onset × vowel heatmap** — a **two-level drill grid** (RESOLVED by the `heatmap-bucketing` spike; see IMPLEMENTATION-STRATEGY Phase 2). Default view = **~9 onset-class rows × ~7 nucleus buckets = 63 cells**, with structural homes for every awkward shape (V-only = null-onset row; diphthongs = a nucleus column group; CCV+ = a complex-onset row group; non-pulmonic = its own row, never a gutter).
  - **"Cell = one Shape" is scoped to the *expanded* level** — this resolves the old contradiction with "rows = onset class". A **class-level cell is a Shape *bucket*** (click expands it in place to its segments); an **expanded segment-level cell is one Shape** (click picks it). The class rows map 1:1 onto the onset-class filter + V/CV/CCV toggle. Expansion is an in-place accordion, so the filter-dimming spatial stability holds.
  - **Never a bare count.** A cell's number mixes tiers; it must never render as a plain integer. Show **tier composition** (e.g. 28● 11◐ 8○) and colour by **observed-vs-expected** intensity (denominator = PHOIBLE-inventory × prosodic-type = languages that *could* have the cell), not raw count — a raw scale rewards data-dense (Global-North) languages and inverts the mission. Only the intensity *thresholds* wait on Phase-1 seed data; the grid *structure* is authorable now from CLTS features.
- **Result canvas: world map** — a **d3-geo Equal-Earth** interactive SVG (RESOLVED; `map-and-misc` spike), beside the heatmap. Dots = languages that have the selected shape; recolors live on selection. Equal Earth over Mercator so the projection does not visually inflate the Global North. One lat/long per languoid from Glottolog; languoids lacking coordinates render "listed but unmapped", never dropped. Preselected to the most widespread shape so the cross-globe payoff is on screen at load.
  - **Explicit third state — "no data" ≠ "structurally absent".** A missing dot must distinguish *not sourced yet* (documentation-status) from *the language structurally bans this shape* (prosodic type / word-minimality) from *present*. Rendering absence-of-evidence as evidence-of-absence lands hardest on the under-documented languages the mission prioritizes. Requires the Language attributes added to CONTEXT.md.
- **Search bar** (with autocomplete + plain-spelling tolerance) and a **"surprise me"** random-shape button on top — directed and serendipitous entry alongside browsing.
- **List toggle** — an IPA-ordered list of shapes with language counts, as an alternate view over the heatmap (linear scan + accessible fallback).

Four ways in (heatmap click · search · list · surprise), one payoff (map lights up).

_Synthesized from landing options 3+4+7+8+11+12; layout resolved to heatmap-hero._

## Form detail — bottom sheet over the live map

Reached by: heatmap cell → shape selected, map lights → click a language → sheet rises. Map stays visible above (context never lost).

- **Container:** bottom sheet rising from the bottom (mobile-friendly), over the dimmed-but-visible map.
- **Header:** big play button + IPA + language name + **two honesty badges** — a **Confidence Tier** badge (source provenance: curated/mined/generated) and a **Classification Confidence** badge (is its openness contested? — ADR-0001); hover each = meaning + exact Source(s).
- **Body — example Words are the headline:** each Word shows its own inline play button, its gloss, its tone, and its own tier badge (per-Word tier can differ from the Form's). _(Note: for the Global-South-first priority languages this headline is often empty — Words are sparse; the Form still stands on its own. Flagged as the mission-vs-data tension.)_
- **Glosses are links:** tapping a gloss ('mother') jumps to that concept across every language that has a word for it — the "same meaning elsewhere" delight, as a *secondary* path; the primary axis stays Shape. Degrades gracefully where Word data is thin.
- **Compare pin:** drops this Form into a compare tray to hold against the same shape in another language. _(Opens a new branch — the compare surface — to be grilled.)_

_Synthesized from detail options 3+7+8+15+16+20._

### Audio — a second provenance axis

Audio is present everywhere via synthesis-from-IPA, but a **synthesized** voice is badged distinctly from a **real recording** — the same honesty discipline as the data Confidence Tier, on an independent axis (a Form may have _curated_ data but _synthesized_ audio). See CONTEXT.md **Audio**. _(Audio is a wholly-undesigned dependency — no synthesis engine or recording archive is named yet; flagged as a v1 risk in Open decisions below.)_

## Compare surface — its own route, juxtaposition only

Pinning Forms fills a **compare tray** (on-ramp); expanding it opens a dedicated **compare route**.

- **Unit:** the same Shape across languages (Mandarin /ma/ vs Yoruba /ma/ vs Fijian /ma/).
- **Layout:** side-by-side **columns**, one per pinned Form, aligned by an **attribute table** (rows = features).
- **Rows surfaced:** audio (play each), tones (contour glyphs aligned), example Words + glosses, Confidence Tier + Classification Confidence + audio provenance.
- **Framing:** **pure juxtaposition — no similarity score.** The eye does the comparing.

### Why no similarity score (load-bearing)

Ringe (1992) / Tresoldi (2019): open monosyllables are the worst case for cross-linguistic similarity claims — a /ma/≈/ma/ match across unrelated languages is overwhelmingly chance. A scored readout would manufacture false discoveries and contradict the data-honesty spine. A real similarity claim needs an explicit chance-baseline (a Stage-3 research task per research.md), not a UI feature. **Excluded by decision.**

_Synthesized from compare options 1+5+7+10+11+12+13+15+20; option 16 (similarity score) explicitly excluded._

## Filter UI

On the heatmap-hero landing:

- **Placement:** a **top bar** spanning heatmap + map that spawns **removable filter chips** as you select (active filters always visible and reversible).
- **Onset filter:** **onset-class checkboxes** (nasal, stop, fricative…) + an **onset-complexity toggle** (V / CV / CCV). No IPA fluency required.
- **Tier filter:** **Confidence-Tier checkboxes** (curated / mined / generated) — the honesty filter, explicit. **`generated` is NOT default-hidden** (user decision): it is most of the Global-South data the mission prioritizes, so hiding it by default would empty the map for exactly those languages. Instead it is never rendered as bare fact (per-entry classification signal), and filtering it out shows a **removal count** ("would remove 8 languages") so the user sees what they're excluding.
- **Effect on views:** filtered-out heatmap cells **recolor/dim in place** (spatial map stays stable, users don't lose their place); map updates; a **live match count** with tier composition ("312 shapes · 47 languages — 28● 11◐ 8○") gives immediate feedback.
- **State:** filters reflected in the **URL** — any filtered view is shareable.

_Synthesized from filter options 2+5+6+8+12+15+18+19._

## Shell / navigation

- **Structure:** a few **routes** (landing / compare / about) under a **persistent top nav** (logo · global search · floating compare button with count badge).
- **Drill:** shape → language → word happens as **progressive overlays within the landing** (heatmap → map lights → bottom sheet → gloss link), with a **breadcrumb** (Shapes › /ma/ › Mandarin) so depth is always legible.
- **Honesty destinations (non-negotiable):** an **About / methodology** page (explains Confidence Tiers, the inclusion rule, the honesty stance) and a **Data sources** page (credits every dataset). These are where the project's spine is made legible.
- **Deep links** to any state (shareable).
- **Fast-follows:** per-language deep-dive pages, concept index. **Deferred:** UI-language i18n.

_Synthesized from shell options 2+3+6+7+11+13+14+19._

## Visual + typographic direction — "data journalism"

> **REVISED (2026-07-04, Rams redesign).** The editorial serif frame is replaced by
> **SK-63 "The Calibrated Instrument"** — a Dieter Rams / Braun functionalist system chosen by a
> 3-proposal / 2-judge design panel and formalized in [`.interface-design/system.md`](../.interface-design/system.md)
> (tokens, laws, component registry — UI leaf tasks cite those tokens the way code cites ADRs).
> What carries over unchanged: IPA-as-hero (now enforced structurally — serif *means* phonetic data,
> all chrome is grotesque), single-hue heatmap, ● ◐ ○ tier iconography, near-monochrome discipline.
> What changes: parchment/Georgia → warm-grey instrument surfaces + system grotesque; pills/shadows →
> 2px rectangles + drawn depth; tier-composition bars → the **calibration strip** (curated solid ·
> mined solid · generated hollow — no ungraduated bar may exist); selection is achromatic (pressed
> surface + ink + square notch) so tier colors are never stolen; the map's rogue amber review dot is
> unified into the single `--review` red as an annotation square, never a recolor. The sections below
> record the original direction for history.

An **editorial / magazine** frame around a rigorous data core:

- **Mood:** editorial — serif headlines, generous whitespace, longform calm. Warms the factual tool for a broad audience without sacrificing credibility.
- **Typography:** a **display + phonetic font pairing** (display face for UI, a dedicated IPA-capable phonetic face for transcriptions), with **IPA as hero** — the /ma/ glyphs are the visual identity, not decoration.
- **Color discipline:** the **heatmap owns the color** — a **single-hue, colorblind-safe sequential scale** (intensity = language count); everything else stays near-monochrome so the one colored surface is the one carrying data.
- **Honesty visual language:** a neutral base plus **tier semantic colors**, and a **consistent ● ◐ ○ tier iconography** (solid · half · open) used *identically* everywhere data appears — trustworthiness legible at a glance app-wide.

_Synthesized from visual options 2+7+9+11+12+15+17+20._

> When UI is actually built, this direction is formalized into concrete tokens (spacing scale, type scale, exact palette values) via the `interface-design` skill — UI leaf tasks cite those tokens the way code cites ADRs.

## Post-audit corrections (multi-viewpoint review, 2026-07-02)

Six competing value-lenses + an implementation-gaps pass reviewed these docs. Full findings:
[docs/multi-viewpoint-analysis.md](multi-viewpoint-analysis.md) and [docs/implementation-gaps.md](implementation-gaps.md).
Applied above:

- **Two honesty axes** everywhere (Confidence Tier = source; Classification Confidence = openness call); `verified` renamed `curated`.
- **Never a bare count** — heatmap cells and match counts show tier composition; intensity should be observed-vs-expected, not raw.
- **Map "no data" third state** — distinguishes unsourced from structurally-absent (needs the new Language attributes).
- **`generated` never default-hidden** (user decision) — shown, never as bare fact; filtering it shows a removal count.

## Build order — UI-first (USER OVERRIDE, risk flagged)

The audit's unanimous recommendation was **data-first** (ship research.md Stage 1 CLDF dataset, then design the hero from the real distribution). The user chose **UI-first**. Recorded consequences:

- The heatmap axes/encoding is **RESOLVED** (two-level drill grid — see Landing), built against a **small real seed dataset**, not pure mock; only intensity thresholds are re-tuned when full data lands.

## Decisions — now RESOLVED by spikes (`docs/spikes/`)

- **Heatmap bucketing** — ✅ two-level drill grid (class → segment); structure authorable now from CLTS features. `spikes/heatmap-bucketing`.
- **Audio subsystem** — ✅ pre-rendered per-Shape clips; espeak-ng → ToucanTTS; `recorded` badge real via Wiktextract Commons audio; Lingua Libre fast-follow; deaf-user path free (visible IPA carries the signal). `spikes/audio-subsystem`.
- **Map tech** — ✅ d3-geo Equal-Earth interactive SVG. `spikes/map-and-misc`.
- **Search plain-spelling** — ✅ build-time ASCII alias index (pure function of the shape string). `spikes/map-and-misc`.
- **Source licensing** — ✅ catalog releases CC-BY-SA 4.0; CELEX dropped; unlicensed Lexibank quarantined. `spikes/licensing-audit`.
- **Delivery/scale** — ✅ static-baked hybrid; ~2.5k langs / ~125k Forms mid-estimate. `spikes/scale-and-delivery`.

## Still open (need the human)

- **IPA-as-hero accessibility** — pair every glyph with a plain keyword ("as in bed") + audio; ARIA speaks the keyword, not the glyph; keyboard nav for heatmap/map. (A continuous accessibility gate in the strategy, not a one-shot decision.)
- **Words-absent detail state** — design the no-example-Words layout as first-class (not degraded) for the priority languages; Phase 3.
- **Mission stays implicit** (user decision) — Language attributes added for data-quality/rigor only; no coverage/equity surface built.

## Status

UX/UI design tree fully walked: landing · Form detail · compare · filters · shell · visual direction — hardened against a multi-viewpoint audit, then every open UX decision closed by a spike. See [IMPLEMENTATION-STRATEGY.md](IMPLEMENTATION-STRATEGY.md) §11 for the full gap-closure ledger.
