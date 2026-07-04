# Spike: the versioned canonicalization scheme (v1)

**Item:** `canonicalization-scheme` — the ADR-0002 **stage-3** spec. Its expected-canonical column **is** the
corpus (IMPLEMENTATION-STRATEGY §4/§5, first-move step 2). This is a DESIGN item: the deliverable is a
concrete, versioned rule table a linguist ratifies line-by-line, plus the exact residual that still needs a
human. It does **not** claim final linguistic authority; it converts "unbounded judgment" into "a specified
rule + a bounded review queue".

**Locked inputs respected (not relitigated):** CLDF/CLTS backbone; tone-blind Shape; `/a/ ≠ /ɑ/` and all
contrastive segments preserved (do **not** merge); versioned scheme stamped into the Form key (CONTEXT.md
Identity). Runner-ups are named, not hidden.

---

## Findings (what CLTS/BIPA actually does — web-verified)

Verified against the CLTS paper (Anderson, List et al. 2018), the `pyclts`/`clts-legacy` README, and the CLTS
2.3.0 catalog. Sources listed at the end. These are the mechanisms the scheme rides on — we adopt them, we do
not reinvent them.

1. **BIPA is the canonical representative.** CLTS "chooses the BIPA grapheme as canonical representative of
   the graphemes mapped to a sound." For each parsed sound, `str(bipa[g])` / `__unicode__()` returns **the
   fully-normalized, alias-resolved BIPA string**. Example: `str(bipa['ʦ']) == 'ts'` — the tie-bar/ligature
   variant resolves to the bare BIPA grapheme. **This string is what we bake.**
2. **CLTS parses through explicit stages** (README feature table), each individually addressable:
   `.source` (raw input) → `._norm()`/`.normalized` (one-to-one replacement of wrong Unicode look-alikes,
   e.g. `λ`→`ʎ`, Latin `g`→script `ɡ`) → alias resolution (`+`-marked free variants collapse to the accepted
   one, `ʦ`→`ts`) → `.grapheme` (normalized, alias-unresolved) → `str()` (normalized **and** alias-resolved)
   → `.name` (feature bundle in canonical order, sound-class last). This staging is what lets heterogeneous
   sources converge — it **is** the Shape-fragmentation fix.
3. **CLTS auto-reorders diacritics to a canonical order.** `bipa['dʱʷ']` → `str` = `dʷʱ`; a user querying
   `kʰʷ` gets the sound generated and its `str()` returns the correct order `kʷʰ`. We do **not** author our own
   ordering table — CLTS owns it.
4. **Tone is a first-class, separate sound *type*.** CLTS "distinguishes the basic sound types consonant,
   vowel, tone, and marker" (plus `diphthong`, `cluster`). Tone letters/marks parse to `type == 'tone'` and
   markers (stress, boundaries) to `type == 'marker'` — so tone-stripping is a **clean type filter**, not a
   fragile regex over the string.
5. **Generated = review flag.** When a source grapheme is not in the catalog, CLTS synthesizes the sound from
   base + diacritics and sets `.generated == True`; the README states generated sounds "need to be
   double-checked by the experts." This attribute **is** our bounded review-queue trigger.
6. **Pre-posed-diacritic hazard is at TOKENIZE, not at CLTS.** research.md: the `segments` library historically
   mis-segments pre-posed diacritics (pre-aspiration `ʰ`, pre-nasalization `ⁿ`, pre-glottalization) — attaching
   them to the *preceding* segment. CLTS itself parses `ʰbʰ` correctly **once it receives the whole grapheme**.
   So the hazard lives in the per-Source orthography profile (stage 2), which must list pre-posed sequences as
   single graphemes; if it doesn't, the wrong segment reaches stage 3 and the nucleus classification corrupts.

---

## Proposal — Canonicalization Scheme v1 (`oms-canon-v1`)

### The rule table (ratify line-by-line)

Applied at ADR-0002 **stage 3**, on the stage-2 orthography-profile token stream, per Form. "Emit" = does the
class appear in the canonical segmental string that becomes the Shape/Form key.

| # | Segment class | Input examples | v1 rule | CLTS/tooling mechanism | Emit to canonical string? |
|---|---|---|---|---|---|
| R1 | **Unicode form** | precomposed `ã`, look-alike `λ`,`g`,`:` ,`'` | **NFD-normalize input**, then let CLTS `._norm()` fix look-alikes to BIPA | `unicodedata.normalize('NFD')` at ingest → `ts._norm()` | (feeds all below) |
| R2 | **Base C / V segments** | `p t k a ɑ e o u ɛ ɔ` | map to BIPA canonical grapheme; **preserve every contrastive segment** — `/a/`,`/ɑ/`,`/e/`,`/ɛ/` stay distinct | alias + `str()` | **yes** |
| R3 | **Tone (marks & letters)** | `˥ ˩ ˧`, `¹²`, `á à ā`, chao digits | **STRIP from segmental string; collect into `Form.tones` set** (tone-blind Shape) | filter `sound.type == 'tone'` | **no** → separate field |
| R4 | **Length** `ː` (full) | `aː`, `iː` | **PRESERVE** — length is contrastive in many languages (Finnish *tuli*/*tuuli*); merging violates the locked contrastive-preservation rule | pass through as vowel `+long` | **yes** |
| R4b | **Half-long** `ˑ` | `aˑ` | **v1 default: fold `ˑ`→`ː`** (treat as long) — but see review queue Q-c | profile alias `ˑ`→`ː` | yes (as `ː`) |
| R5 | **Nasalization** `◌̃` | `ã`, `õ` | **PRESERVE** — phonemic in many languages (French, Hindi) | pass through as vowel `+nasalized` | **yes** |
| R6 | **Stress** `ˈ ˌ` | `ˈba` | **STRIP** — never a segmental contrast in the nucleus sense | filter `type == 'marker'` | **no** |
| R7 | **Syllabicity** `◌̩` `◌̯` | `m̩`, `a̯`/`ai̯` | **PRESERVE — load-bearing.** `◌̩` (syllabic) and `◌̯` (non-syllabic) are exactly what the ADR-0001 openness classifier reads (syllabic-consonant → excluded; `◌̯` → diphthong glide). Stripping them would silently corrupt the openness call. | pass through | **yes** |
| R8 | **Diacritic ORDER** | `dʱʷ` vs `dʷʱ`, `kʰʷ` vs `kʷʰ` | **REORDER to CLTS canonical order** (do not author our own) | `str(bipa[g])` | **yes** (reordered) |
| R9 | **Affricate tie-bar** | `t͡s`, `t͜ʃ`, `ʦ` | **STRIP tie-bar → bare BIPA digraph** `ts`,`tʃ` | alias resolution | **yes** (untied) |
| R10 | **Pre-posed diacritics** | `ʰb`, `ⁿd`, `ˀa` | keep attached to host segment; **the per-Source orthography profile MUST list each as a single grapheme** (mitigates the `segments` mis-segmentation hazard) | stage-2 profile grapheme; CLTS parses whole | **yes** (if profile correct) |
| R11 | **Source notation variants** | `g`↔`ɡ`, `:`↔`ː`, `'`↔`ʼ`, `ǝ`↔`ə` | resolve to BIPA via CLTS look-alike + alias tables — this is the cross-Source unifier | `._norm()` + alias | **yes** (unified) |
| R12 | **Unknown / unparseable** | grapheme CLTS can't map; `sound.generated == True` | **REJECT to review queue; emit NO Form** until an expert confirms the grapheme, then add it to the profile | check `.generated` / unknown | **no** → review queue |

**Serialization contract:** the canonical string = `"".join(str(bipa[g]) for g in profile_tokens if
bipa[g].type not in ('tone','marker'))`, tone/markers siphoned to their own fields, computed **after** NFD +
profile tokenization. Use `str()` (alias-resolved), **never** `.grapheme` (alias-unresolved) — see runner-up.

### Version-stamping mechanism

`oms-canon-v1` is a **compound pin**, not a bare label. It fixes the tuple:

```
oms-canon-v1 = ( pyclts==X.Y.Z, clts-data==2.3.0, profile-set==vN, ruletable(R1..R12)==v1 )
```

- **Form key** = `{glottocode} : {canonical-string} : oms-canon-v1`
- **Shape key** = `{canonical-string} : oms-canon-v1`

The scheme id sits in **both** keys so cross-language grouping never collides strings produced under different
schemes, and so a scheme bump (§3 canonicalization-version gate) re-stamps keys and rotates the
`data/{canon-version}/` path (§10) without rotting deep links. Any change to R1–R12, to the CLTS data release,
or to the pyclts version **bumps the version** — that is the gate's trigger condition, made concrete.

### Runner-ups (named, rejected)

- **Emit `.grapheme` instead of `str()`** — rejected: `.grapheme` leaves aliases unresolved, so `ʦ` and `ts`
  from two sources would fragment into two Shapes — the exact bug canonicalization exists to kill.
- **Author our own diacritic-ordering table** — rejected: reinvents CLTS's normalizer, adds a maintenance
  surface, and desyncs from the catalog we pin to. Adopt CLTS order (R8).
- **Global length neutralization** (`aː`→`a`) — rejected: violates the locked contrastive-preservation rule;
  destroys minimal pairs in quantity languages. Length is preserved (R4); only the *half-long* symbol and
  specific over-transcribing sources are review-queue items, not a blanket merge.

---

## What still needs a human (the bounded residual)

The scheme above is mechanical **except** these — each is a *bounded queue*, not open-ended judgment:

- **Q-a · Per-language length contrast (the headline contested normalization).** R4 preserves `ː` globally.
  But some Sources over-transcribe predictable/allophonic length. **Queue = languages where PHOIBLE shows no
  length contrast yet the Source carries `ː`** (stage-7 validation surfaces exactly this set). Linguist rules
  per language: keep (contrastive) vs fold `ː`→plain (allophonic). Finite, PHOIBLE-filtered — not every form.
- **Q-b · Nasalization: phonemic vs coda-assimilation.** R5 preserves `◌̃`. Where nasalization is really a
  trace of an elided nasal *coda*, that is an **openness/coda** decision — hand to the openness corpus
  (ADR-0001), not resolved here. Flag the intersection so the two corpora don't disagree.
- **Q-c · Half-long `ˑ` policy.** R4b defaults to fold→`ː`; a linguist ratifies that global default and names
  any language where `ˑ` is a third contrastive degree (rare; e.g. Estonian is a candidate) that must stay
  distinct.
- **Q-d · Pre-posed-diacritic grapheme lists, per Source.** R10 depends on each orthography profile listing
  pre-posed sequences correctly. This is authored **per Source** and spot-checked (the mis-segmentation is
  silent). One-time per Source, not per form.
- **Q-e · Diphthong tokenization boundary.** Whether `ai` tokenizes as **one** diphthong segment or `a`+`i̯`
  (vowel+glide) is set in the profile and is the **same fork** as the diphthong-vs-glide openness verdicts —
  owned by that spike/corpus. Canonicalization's only rule here: tokenize per profile, **never auto-split or
  auto-merge** a vowel sequence. Cross-reference, don't duplicate.
- **Q-f · CLTS `.generated` review queue (R12).** Every synthesized/unknown sound is expert-double-checked
  before its grapheme enters a profile. Bounded by the actual unknown-grapheme count from the seed run.

**Recommend minting these as Q-N decision records** when the seed pipeline (first-move step 3) surfaces the
real queues; promote the whole scheme to its own ADR at that point (ADR-0002 flags it for promotion).

---

## Consequences for the strategy

- **Closes gap 4.1** (tone-blind derivation) with a concrete spec; ADR-0002's stage-3 open sub-decision and
  §4/§5's "canonicalization" authoring prerequisite now have a ratifiable table. `oms-canon-v1` is the string
  that first-move step 3 makes green.
- **Confirms the §5 deceptively-simple framing:** unify only true notational variants (R8/R9/R11), never
  contrastive segments (R2/R4/R5). The scheme is a *stable-per-segment* normalizer, not a vowel-space collapse.
- **Sharpens the §3 canonicalization-version gate** into a concrete trigger: any edit to R1–R12 **or** to the
  pinned pyclts/clts-data versions bumps `oms-canon-v1` and rotates `data/{canon-version}/`.
- **Adds one stage-2 acceptance criterion:** every per-Source orthography profile must be checked for
  pre-posed-diacritic graphemes (Q-d) before its Forms are trusted — a new item for the Phase-1 profile tasks.
- **The keystone corpus is now authorable:** the expected-canonical column = apply R1–R12; the contested cells
  are exactly Q-a…Q-f, pre-marked for the linguist. A small model can turn the normalizer green against it.

---

## Sources (web-verified 2026-07)

- Anderson, List et al. (2018), *A Cross-Linguistic Database of Phonetic Transcription Systems* —
  http://lingulist.de/documents/papers/anderson-et-al-2018-cross-linguistic-transcription-systems.pdf
- `cldf-clts/clts-legacy` README (pyclts algorithm stages, `str()`/`.grapheme`/`.name`, diacritic reordering,
  `.generated` flag) — https://github.com/cldf-clts/clts-legacy/blob/master/README.md
- `pyclts` — https://github.com/cldf-clts/pyclts · https://pypi.org/project/pyclts/
- CLTS 2.3.0 catalog (sound types consonant/vowel/tone/marker; BIPA as canonical) — https://clts.clld.org/
- research.md (segments pre-posed-diacritic mis-segmentation hazard; Rec 3 "write down decisions as explicit
  versioned rules"; diphthong-vs-glide as a genuine fork) — repo-local.
