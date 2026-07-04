# Design system — SK-63 "The Calibrated Instrument"

Rams/Braun functionalist system for the Open Monosyllabic Explorer (`web/`).
Chosen 2026-07-04 by a 3-proposal / 2-judge panel; supersedes the "data
journalism" editorial direction in `docs/ux-design.md` (revision note there).
The product is a bench instrument for phonology: IPA is the specimen, every
quantity is read off a calibrated gauge, and nothing is colored unless the
color IS the signal.

## Laws (check every new component against these)

1. **Serif = phonetic data, nothing else.** `--ipa` (Charis SIL stack) only on
   IPA/transcriptions, via `.ipa` / `.ipa17` / `.ipa22` / `code`. IPA is never
   bold, italic, uppercase, or letter-spaced. All chrome is the `--ui` grotesque.
2. **Color = signal only.** Tier trio (`--curated` ● / `--mined` ◐ /
   `--generated` ○), one alarm (`--review`, means "a human must check this",
   nothing else may use it), one quantitative hue (`--data`, heatmap ramp +
   lit map dots). Everything else achromatic.
3. **Selection is achromatic.** Pressed surface (`--pressed`) + 1.5px ink
   outline + 6px square notch (nav `::after`, chip `::before`, `.cell.on::after`,
   `.crow.sel::before`). There is deliberately NO accent/selected token to
   reach for. Square marks = interface state; round glyphs = evidence.
4. **Depth is drawn, never blurred.** Surface ladder `--page → --panel →
   --raised` (+`--pressed` for ON); two line weights `--line-1`/`--line-2`;
   the third border step is always ink. No box-shadows. Radius ≤ 2px.
5. **One animation** in the whole product: the sheet slide (160ms ease-out).
   Hover changes line weight/ink only, never fills, no transitions.
   **Drawn at rest (amendment, 2026-07-04):** every pressable element is
   identifiable at rest by exactly one of four drawn carriers; hover *confirms*
   an affordance (line/ink change), never *reveals* it. Static data never wears
   a carrier. The carriers, all achromatic: **KEY** (standalone control:
   `--line-2` border + one surface step above its ground — chip, shape plate,
   play, pin/go, search, plate, close); **INDEX ROW** (selects in place, owns
   `.sel`: hollow gutter square at rest, `.crow:not(.sel)::before`, solid when
   selected — hollow = selectable, solid = selected, the chip vocabulary);
   **PORTAL** (acts elsewhere: `.langrow::after` terminal `›`; grotesque text
   uses the anchor/`.wlink` hairline underline; pressable serif IPA is PLATED
   (`.lshape`), never underlined — underlines collide with diacritics; bare
   serif = inert specimen); **KEYED CELL** (`td.cell` rest outline `--line-1`).
   Rams P4 (understandable) outranks austerity — that is why this clause exists.
6. **No bar without graduation.** The calibration strip (`.bar` + `.s-cur`
   solid green / `.s-min` solid brass / `.s-gen` hollow-outlined) is the only
   proportion bar. The tabular composition text (`tierCompHTML`) always
   accompanies it — redundant encoding is load-bearing. Zero count still draws
   the hairline track ("absence is drawn"). `.s-data` (single-hue) is allowed
   only where tier composition genuinely isn't in the data (concept reach —
   see Debts).
7. **Never a bare count.** Heatmap: count numeral in cell + full composition
   in the dial window (`.dial`, hover/focus/selection) + title attr. Stamps and
   plates carry composition where available.
8. **Kitsch guardrail.** Permitted skeuomorphs: pressed surface, plate, strip,
   square notch — that's the complete list. No textures, grilles, rivets,
   knurling, key-travel transforms, or a second animation. No flag/emoji
   iconography for languages (flags conflate nation with language). No fake
   affordances (e.g. a grab handle that doesn't drag). Clarification: the
   "no grilles" ban targets decorative texture; a functional drawn boundary on
   an interactive cell is an affordance and is *required* by law 5's amendment.
9. **Hierarchy: the display unit sets the lead, not the view.** Wherever the
   unit is a form/shape (cards, Sounds result rows, compare columns, the
   sheet), order is WORD (serif ink, the unit's largest step) → MEANING (gloss,
   one step down, never demoted to a `--text-3` note) → LANGUAGE (attribution,
   smaller than both). The pane's subject (`.convhd`) is its largest text.
   Language-first is correct only where the selection target IS the
   language/region entity: the Languages and Regions pickers.
10. **Click contract: a surface opens the thing it names; inner keys always
   win over the container.** Picker rows (`.crow`) select in place. A row or
   card that names ONE form (Sounds `.langrow`, Languages `.cshape.portal`,
   lit map dots, card entries `.wlink` = word+name) opens the form sheet from
   its whole surface. A row that names a language (Regions `.langrow`,
   Compare's language field) opens the Languages view. Cards that merely GROUP
   forms (Meanings/Look-alikes shape cards) are leaf containers: no pressable
   styling on the container — only their entries and keys act. Never give the
   same visual component two different click meanings without a different
   carrier (portal cards wear the `›`; leaf cards wear nothing).

## Tokens (defined in web/index.html `:root`)

Surfaces `#E6E4DF / #F2F1ED / #FBFAF8 / #DDDAD4` · ink `#21201C / #4A4841 /
#64615A / #8B877E` (text-4 = disabled only, never information) · lines
`#C9C6BF / #A39F96` · data `#2F5E6C` · tiers `#2E5E4E / #7A5A1C / #605D56`
(generated darkened from the panel's #6E6A61 after contrast audit: 4.71:1 even
on `--pressed`) · review `#A63A22` · map land `#CFCCC4`.

- **Floor pair invariant:** `--text-3` on `--page` ≈ 4.8:1 — re-check contrast
  before darkening any surface or lightening this ink.
- **Heatmap ramp** (in app.js `RAMP`): `#DDE4E2 #C0D2D3 #98B8BD #62909D
  #2F5E6C` = color-mix(in oklab, --data N%, --panel) at 15/35/55/78/100%,
  precomputed (no runtime color-mix — no-build site). Cell numerals stay
  `--text-1` through step 4 and invert to `--raised` only on the deepest step
  (`.deep`). Ramp steps are never reused outside the heatmap.

## Type scale (px)

11 engraved labels (caps, +0.08em, text-3, 600) · 12.5 chips/nav/meta ·
13 inputs/attrs · 14 rows/body-adjacent · 15 body · 17/22/28 IPA (plates /
compare / sheet header). Tabular lining numerals on every count.

## Component registry

- `.plate` — the maker's plate: engraved caps in a hairline rectangle; nav
  right edge (`#navplate`, click → Sources) + per-view stamps. Styling never
  varies by context.
- `.dial` — heatmap readout window; hover/keyboard-focus reads a cell,
  leaving reverts to the locked selection.
- `.chip` — switch keys: filled 6px square = included, hollow square +
  dimmed = excluded. Never strikethrough (fights IPA diacritics), never colored.
- `.play` — 24px square transport key, ▶ only; `.play.inline` borderless
  glyph variant for dense lists.
- `.bar`(+segments) — calibration strip, see law 6. `.bar.mini` in compare
  column headers (evidence comparable before forms are read).
- Sheet — `--raised`, machined edge (1px ink rule + 1px hairline 2px below),
  no shadow, no scrim, map stays live behind it.
- Map — ocean = page (chart-paper); land `--map-land`; lit dot = `--data`
  fill; hollow ring (1.3px `--text-2` stroke) = structural zero, firmly inked;
  unsourced = no mark at all; review = 4px `--review` square annotation beside
  the dot, never a recolor.
- Keyboard: every clickable row/cell/chip has `tabindex="0"`; global Enter
  delegation in `boot()`; `:focus-visible` = 1.5px ink outline.

## Debts / deferred

- Sources table shows bare pipeline slugs — `title` + `url` (and per-source
  counts) belong in core.json's sources array (`oms/bake.py`); until baked, the
  credits are not independently verifiable.
- Languages-detail glosses read from `FORMS`, so in the chunked build they only
  appear for already-fetched shapes — top-3 glosses belong in the postings
  index (`oms/bake.py`), same class as the concept-strip debt.
- Compare pins are memory-only; a `#p=gc|shape,…` deep link would match the
  other axes (`ux-design.md` promises deep links to any state).
- License discrepancy needs the owner: the Sources page says CC-BY-NC-SA 4.0
  (forced by NC sources) but `docs/ux-design.md` §spikes records "catalog
  releases CC-BY-SA 4.0". Legally load-bearing — verify, then fix the stale one.

- Concept rows (`.s-data` strips) lack tier composition because `core.json`'s
  concept index doesn't carry it — needs a bake change (`oms/bake.py
  build_concepts`) to graduate those strips. Until then they encode reach only.
- "Structurally impossible" heatmap cells (45° hatch) await a CLTS
  impossibility matrix from the pipeline; claiming impossibility without data
  would itself violate the honesty spine, so empty ≠ hatched for now.
- Dark mode not designed; map SVG colors are literals in app.js.
- Hairline/hollow-segment rendering should be spot-checked at 1.25×/1.5×
  fractional DPR.
