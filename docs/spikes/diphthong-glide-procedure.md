# Spike: diphthong-vs-glide decision procedure

**Item:** `diphthong-glide-procedure` (IMPLEMENTATION-STRATEGY §11 "genuinely still open"; ADR-0002 open sub-decision 4; ADR-0001 Consequences).
**Type:** DESIGN (linguistic-judgment). Output is a concrete v1 procedure a linguist *ratifies*, plus the bounded residual that still needs a human — **not** a set of authored verdicts.
**Status:** proposal, pending linguist ratification.
**Respects locked decisions:** ADR-0001 rule (diphthong = single nucleus → open; vowel+glide → coda → closed; syllabic consonant → excluded); CLTS/cltoolkit backbone; tone-blind Shape; Classification Confidence as an independent honesty axis; static-baked delivery.

---

## Findings

**F1 — CLTS already carries the disambiguation as data, not guesswork (verified).** CLTS/BIPA defines exactly five sound types: `consonant`, `vowel`, `tone`, `diphthong`, `cluster`. A `diphthong` is a *single* sound object with its own trajectory features (e.g. `from_open` → `to_near-close`); a glide (`j w ɥ ...`) is a `consonant`. So once a canonicalized Form is parsed by pyclts at stage 4b, the openness call is often already made by the source's transcription choice:
- final segment is a `diphthong` object → single complex nucleus → **open**;
- final segment is a `consonant` glide → coda → **closed → excluded**;
- final is a `vowel` preceded by a `vowel` (a two-object VV sequence, no `diphthong` unit) → **genuinely ambiguous** (tautosyllabic diphthong? hiatus/two syllables? rising diphthong?).
The contested call is therefore *localized* to the VV-sequence case plus cross-source disagreement — not spread across every diphthong-bearing Form. ([pyclts](https://github.com/cldf-clts/pyclts), [clts](https://github.com/cldf-clts/clts), [Feature-vector paper, arXiv:2405.04271](https://arxiv.org/html/2405.04271v1))

**F2 — Sources encode the same diphthong inconsistently (verified, load-bearing).** A curated Lexibank dataset transcribes Manchu (and other) diphthongs *as sequences of simple vowels*, not as diphthong segments ([lexibank/northeuralex issue #11](https://github.com/lexibank/northeuralex/issues/11)). So "trust the source" (branch a) is only safe **when the source resolved the segment itself**; a source that writes VV as two vowels has *not* disambiguated and must fall to the rule table (branch b). This is the exact seam that decides confidence.

**F3 — The `segments` tokenizer has a known diphthong hazard.** research.md §27: `segments` historically mis-segments pre-posed diacritics (pre-aspiration attaches to the preceding vowel), a documented nucleus-classification risk. Any VV parse must be taken from the *canonicalized* CLTS output (stage 3→4b), never a raw source string, and diacritic-order normalization is the canonicalization scheme's job (separate open item), not this procedure's.

**F4 — The verdict is per-(language × nucleus-pattern), not per-Form.** The ruling "English /aɪ/ final is an open diphthong" applies to *every* English /aɪ/-final Form at once. This is what converts "unbounded per-case judgment" into a **finite** queue: the human authors a rule keyed by `(glottocode, nucleus-pattern)`, and the pipeline fans it out over all matching Forms. research.md Rec 3 ("write decisions as explicit, versioned rules") is the same instruction.

**F5 — PHOIBLE gives a free prior for the rule table.** PHOIBLE inventories list which diphthongs a language *contrasts* (ADR-0002 already uses PHOIBLE to validate nuclei at stage 7). If a language's PHOIBLE inventory lists /ai/ as a diphthong segment, a VV /a i/ Form in that language is *probably* that diphthong → a defensible default, not a coin-flip.

---

## Proposal / Recommendation

### Classification-Confidence levels (v1)

Three ordered levels (mirroring the project's 3-tier honesty motif) **+ one orthogonal flag**. This is the concrete definition of the axis CONTEXT.md declares:

| Level | Meaning | Which branch produces it |
|---|---|---|
| **high** | Openness rested on **no** contested call. | Monophthong-final (open); unambiguous coda (excluded); syllabic-consonant (excluded). Pre-branch — never enters the diphthong procedure. |
| **medium** | A contested nucleus, resolved by an **authority**: the source's own transcription, or a linguist. | Branch **(a)** (source-disambiguated, no cross-source conflict) **and** branch **(c)-resolved** (linguist authored the verdict). |
| **low** | A contested nucleus, resolved by **our editorial rule** without source or expert confirmation. | Branch **(b)** (per-language rule table); also the provisional default of an un-reviewed branch-(c) item. |
| flag: **`under_review`** (bool, orthogonal) | This Form's verdict is a placeholder awaiting a linguist. Renders as "pending expert review". | Set on branch **(c)** while queued; cleared when the verdict is authored (level then becomes medium). |

CONTEXT.md's worked example holds: `/ma/` = **high**; `bye /baɪ/` from a curated source that marks /aɪ/ as one diphthong = branch (a) = **medium** ("lower than /ma/, both badges show"), exactly as written.

### Stage-4b decision function (mechanical; runs per Form, after the CLTS parse)

```
parse canonical Form → [CLTS sound objects]
final = last object

1. final.type == consonant (incl. glide j/w/ɥ)      → CODA → EXCLUDED,  conf=high
2. final.type == vowel AND no preceding vowel        → OPEN monophthong, conf=high
3. final.type == diphthong (single object)           → OPEN,             branch(a) → conf=medium*
4. final.type == vowel AND prev.type == vowel (VV)   → CONTESTED:
      a. if ANY other retained Source parses the same nucleus as a *diphthong object*
         or as *V+glide-consonant*, and they AGREE      → adopt it,      branch(a) → conf=medium*
      b. Sources silent/agree-as-bare-VV → consult per-language rule table:
            entry says diphthong→OPEN | V+glide→EXCLUDED | hiatus→NOT-MONOSYLLABLE
                                                          → branch(b) → conf=low
      c. no confident table entry, OR retained Sources DISAGREE (one diphthong,
         one V+glide) → branch(c): ship table-default (or OPEN if PHOIBLE lists
         the diphthong) at conf=low, set under_review, enqueue (glottocode,pattern)

*medium only if no cross-source conflict; any conflict caps at branch(b)/low.
```

Rule 1 is where ADR-0001's "vowel+glide → closed" is applied: a source that wrote a final glide *as a consonant* has chosen the closed analysis, and we honor it. Rule 3 is where "diphthong → open" is applied. The whole contested surface is **rule 4** (VV sequences + cross-source conflict).

### The per-language rule table (branch b) — an authored, versioned corpus artifact

Seeded, **not** hand-written from scratch: prefill from each language's PHOIBLE diphthong inventory (F5) + its Glottolog-linked phonology sketch. Schema:

```
glottocode | nucleus_pattern (e.g. "ai","au","ei") | verdict {diphthong|v_glide|hiatus}
           | assign_confidence (default: low) | evidence_ref (PHOIBLE id / grammar §)
           | contested (bool — if true, route to branch-c queue instead of resolving)
```

Versioned and stamped like the canonicalization scheme (research.md Rec 3). A row with `contested=true` is the seed's own admission that the table cannot settle it → branch (c).

### Branch-(c) queue — bounded by construction

- **Key = `(glottocode, nucleus_pattern)`, not Form** (F4). One verdict fans out to all matching Forms.
- **Fed only by curated + mined conflicts.** A **generated (G2P) tier** Form that reaches rule 4c is *not* enqueued for a human — Epitran/Transphone do not reliably mark diphthong-vs-sequence, so the long tail would swamp the queue. It ships `conf=low, under_review=auto` (a machine placeholder, honestly flagged) and is promoted to the human queue only if a curated/mined source later contests it. This scoping is what keeps the human queue finite.
- **Each verdict is logged into the openness ground-truth corpus** (the §4 corpus a small model later turns green) — reusable, audit-traceable, and it ratchets the Form from `low + under_review` → `medium` (expert-provenance note).

### Queue-size estimate

Reasoning, catalog-weighted (mid scale ≈ 2,500 langs / 125k Forms, ADR-0002 §3.2):

1. Open monosyllables are overwhelmingly CV/V **monophthong** (the unmarked syllable) → **high**, bypass the procedure. VV/diphthong-final Forms are a minority — near 0% in strict-CV languages, 40%+ in English/SEA; catalog-weighted call **~15–20% of Forms** are diphthong/VV-final.
2. Of those, most are resolved by branch (a)/(b): the source marks a diphthong object, an explicit glide, or the rule table's PHOIBLE-seeded default fires. Genuinely-contested **rule-4c curated/mined** residue is a small slice — **~5% of the contested population ≈ ~1% of all Forms** at the *Form* level.
3. **But the human queue is per-(language × pattern)** (F4), and distinct contested nucleus patterns per language are few (0–4). Estimate: ~30% of languages have any contested nucleus, ~2 patterns each → **~1,500 human verdicts at full scale**; realistically fewer, since one ruling often generalizes across related lects (re-checked, not blind-shared).
4. **Seed scale (6–10 languages, Phase 1):** if the seed spans the stress axes (incl. English + one SEA/tonal + one under-documented), expect **~5–20 human verdicts total** — a single ratification sitting, not an open-ended research program.

So: **branch (c) is ~1% of Forms but a low-thousands (full) / low-tens (seed) *ruling* queue** — finite, front-loadable, and mostly retired during Phase 1.

---

## What still needs a human

A linguist must (ratify the procedure above, then) supply the genuinely-authored residue — this spike deliberately does **not** invent these:

1. **The seed rule-table rows + the ~5–20 seed branch-(c) verdicts** — the actual per-(language, pattern) open/closed/hiatus calls for the Phase-1 seed languages. This is the openness corpus's contested column (STRATEGY §9 step 2).
2. **The default direction when the phonology sketch is silent** — proposal: *if PHOIBLE lists the pattern as a diphthong segment → default OPEN at `low`; else → branch (c)*. Confirm or invert.
3. **Confidence-cutoff ratification** — that branch (a) = medium (not high), and that an expert-resolved contested Form stays medium (not high). This encodes "high = no contested call"; a linguist may want expert verdicts to read as high.
4. **The generated-tier exclusion from the human queue** — confirm G2P VV-final Forms ship `low/under_review=auto` and never enqueue a human by default.
5. **Rising vs falling / on-glide diphthongs and /Vʔ/-type edge shapes** — whether an on-glide (/ja/, CLTS may parse glide-as-consonant onset) or a final glottal ever counts as contested here, or is out of scope (onset/coda, not nucleus).

---

## Consequences for the strategy

- **ADR-0002 open sub-decision 4** ("per-case diphthong-vs-glide verdicts … authored into the openness corpus") is upgraded from an unbounded task to: *a specified stage-4b decision function + a versioned per-language rule table + a `(glottocode, pattern)`-keyed review queue.* Fold this into ADR-0002 stage 4b/5 and promote the procedure to its own Q-N when the seed rule table is authored.
- **§4/§5 (deceptively-simple: openness classifier).** The classifier *code* stays mechanical; this spike defines the exact corpus shape it consumes (rule-table rows + branch-c verdicts) and confirms the human prerequisite is **bounded** (F4), not per-Form. The Classification-Confidence emission at stage 5 is now fully specified: `high | medium | low` + `under_review`.
- **CONTEXT.md Classification Confidence** gains concrete levels — recommend recording `{high, medium, low}` + `under_review` as the enum, replacing the prose "high/lower".
- **Honesty invariant (P4 / §3 gate).** Every Form ships a Classification-Confidence level and the `under_review` flag; `under_review` renders as a visible "pending expert review" note and is never hidden — same posture as `generated` never default-hidden.
- **Delivery (§10).** `classificationConfidence` (2-bit) + `under_review` (1 bit) pack into the `core.json` postings already carrying `[langIdx, tier, classificationConfidence]` — no schema growth beyond one flag bit.
- **Phase 1 gains a concrete deliverable:** the seed rule table + seed branch-(c) verdicts, authored alongside the canonicalization scheme in STRATEGY §9 step 2 — the human queue is retired at seed scale before Phase 2 builds on it.

Sources: [pyclts](https://github.com/cldf-clts/pyclts), [cldf-clts/clts](https://github.com/cldf-clts/clts), [Generating Feature Vectors from CLTS transcriptions (arXiv:2405.04271)](https://arxiv.org/html/2405.04271v1), [lexibank/northeuralex issue #11](https://github.com/lexibank/northeuralex/issues/11).
