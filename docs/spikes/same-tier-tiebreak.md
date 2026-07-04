# Spike: same-tier-tiebreak (ADR-0002 open sub-decision)

**Date:** 2026-07-03 · **Type:** DESIGN (produce a ratifiable v1 rule, not a verified fact). · **Scope:** the *within-tier* Source conflict policy only. The cross-tier rule (curated › mined › generated) is locked (ADR-0002); this closes "when two **same-tier** Sources give different IPA for the same language+word, how is *preferred-for-display* chosen." Until minted, ADR-0002 says `on-block STOP + escalate`; this replaces that stub with a bounded rule.

**Respected as locked:** CLDF/CLTS backbone; canonicalize-before-match; Form identity = (Language + canonicalized tone-blind BIPA); multi-Source retention (Sources are *never* discarded — the tiebreak governs which is *shown*, not which *exist*); the two honesty axes.

---

## Findings

### 1. Canonicalization collapses most "conflicts" before the tiebreak ever runs

Because canonicalization (ADR-0002 stage 3) runs *before* matching and *is* the identity function, **two Sources that canonicalize to the same string are not a conflict at all** — they are one Form with two Sources. Surface differences the scheme already neutralizes (diacritic ordering, tone marks, redundant length, sub-phonemic narrowness) never reach the tiebreak. The tiebreak fires only on a **residual canonical-string difference**, which by construction means a genuine *segmental* disagreement. This shrinks the conflict set to a small, meaningful core.

### 2. The stakes are asymmetric — and one slice touches ADR-0001's sacred zone

A residual canonical difference falls into exactly two kinds:

- **(A) Vowel-quality / segmental disagreement, both still open monosyllables.** Source X → /ma/, Source Y → /mɑ/ (or /e/ vs /ɛ/). Both pass ADR-0001; they differ only in *which* Shape the language joins. Stakes: which Form the Word points to as primary attestation, and default display order. **Low** — both Forms are legitimate and both are retained and shown (multi-Source), so the disagreement is self-disclosing.
- **(B) Openness-verdict disagreement.** The Sources disagree on nucleus-vs-coda or diphthong-vs-glide such that ADR-0001 would **include one and exclude the other** (e.g. one transcribes an open /CV(V)/, the other implies a coda /CVC/ or a consonantal offglide). Stakes: whether the word is *in the catalog at all* / under which openness classification. **High** — a silent auto-pick here would let a Source-ranking quietly decide an ADR-0001 verdict, the one call the whole project refuses to bury.

This split is the hinge of the recommendation: **auto-pick (A), escalate (B).**

### 3. Evaluation of the four candidate policies

| Policy | As PRIMARY? | Why |
|---|---|---|
| **(i) Fixed per-tier Source-priority list** | **Yes (refined)** | Deterministic, reproducible, re-runnable, version-stampable — matches the pipeline's whole ethos (it is just one more granularity level below the locked tier list). Only cost: a human must author the ranking. We cut that cost — see Recommendation. |
| (ii) Newest-dataset-version-wins (recency) | **No — as a cross-Source rule** | Non-reproducible: the "preferred" string silently flips whenever any dataset republishes, rotting version-stamped deep links and rewarding *whoever-updated-last*, not rigor. **Kept only intra-Source:** always take the newest *version of the same named Source* (NorthEuraLex 1.0 over 0.9) — that is "use current data," not a tiebreak, and is consistent with cldfbench-pinned builds. |
| (iii) Plurality / agreement across Sources | **No — as primary; yes as a pre-filter** | Undefined for the common N=2 curated split (the majority case, since curated Sources rarely triple-cover a language). Can also let several low-rigor Sources outvote one high-rigor one. Useful as a *pre-filter* when N≥3 and it does not contradict rank. |
| (iv) Escalate-to-manual on any disagreement | **No — as primary; yes as the bounded fallback** | Does not scale as a first move. But it is the *correct* move for slice (B), and (B) is bounded (see §4), so escalation becomes a small, targeted queue rather than an unbounded backlog. |

### 4. Escalation is provably bounded

Slice (B) fires only when **same-tier** Sources **co-cover** the same language+word **and** flip the ADR-0001 verdict. Curated-tier coverage is largely disjoint (Lexibank datasets vs NorthEuraLex cover mostly different languages; individual Lexibank datasets rarely overlap), so co-coverage is already a small set; the openness-flip subset of *that* is smaller still. The queue is bounded by design — this is the "specified rule + bounded review queue" the terms of reference ask for, not open-ended judgment.

### 5. A mechanical rigor proxy already exists in the pipeline

Ranking Sources by "transcription rigor" sounds like unbounded linguistic judgment. It need not be: the pipeline already runs CLTS/pyclts (stage 3), so every Source has a **measurable CLTS BIPA conformance rate** — the fraction of its segments that validate as clean BIPA sounds vs. those needing fallback/patching. This is a free, objective, self-updating rigor score. The human ratifies *the metric and a short exceptions table*, not a hand-ranked list of dozens of datasets.

---

## Recommendation

**Primary policy: deterministic per-Source priority, driven by a mechanically-measured rigor score, applied only to *pick preferred-for-display* (never to delete data). Fallbacks: intra-Source recency; plurality pre-filter; escalate-to-manual on openness-verdict disagreement.**

### The algorithm (runs per language+word where ≥2 same-tier Sources exist)

1. **Canonicalize all candidates.** All that share a canonical string → **one Form**, no conflict. Go to step 4 to order their display.
2. **Classify each residual canonical difference** as slice **(A)** vowel-quality/segmental, both open, or slice **(B)** openness-verdict flip (include-vs-exclude, or nucleus-vs-coda / diphthong-vs-glide) per ADR-0001.
3. **Route by slice:**
   - **(B) → ESCALATE.** Emit to the `tiebreak-review` queue; do **not** auto-pick a preferred among conflicting Forms. Both Forms remain provisional pending a linguist verdict (which reuses the *same* review lane as per-case diphthong-vs-glide verdicts — ADR-0002's other open item). This is the only manual path.
   - **(A) → AUTO-PICK.** Preferred-for-display Form = the one from the **higher-priority Source**. Both Forms and both Sources are **retained and shown**; the non-preferred Source is the built-in honesty disclosure (no new axis needed — the retained alternate *is* the "sources disagree" signal). Classification Confidence is **not** lowered (openness is not in question).
4. **Source priority order** (used in 3-A and to order display within one Form):
   1. **Higher CLTS BIPA conformance rate** (measured by the pipeline, per Source/dataset).
   2. **Linguist exceptions table** overrides the measured order for known cases (a gold field-based dataset the metric under-rates, etc.).
   3. **Ties → newest Source version** (intra-Source recency).
   4. Final tie → lexicographic Source id, so the result is always deterministic and reproducible.

### Escalation threshold — crisp and mechanical
Escalate **iff** the same-tier Sources disagree on the **ADR-0001 openness verdict itself** (one would be included, the other excluded) **or** on **nucleus-vs-coda structure**. Auto-pick everything else (pure vowel-quality/segmental disagreement that leaves *both* candidates open monosyllables). The trigger is computed from the stage-4/5 nucleus+coda annotation, not from a string-distance heuristic — it fires on *what* differs, tying the manual queue exactly to the project's one contested call.

### Runner-up (named, rejected)
A **plain hand-ranked fixed Source-priority list** (option i in its simplest form). Same determinism, but the human must hand-rank potentially dozens of heterogeneous Lexibank datasets and re-rank whenever a new dataset lands. The conformance-score variant dominates it: objective, self-maintaining, and it reduces the human's job to ratifying a metric plus a short exceptions table.

### Q-N-style decision record (to mint on ratification)

> **Q-N — Same-tier Source tiebreak.** *Scope:* ingestion pipeline (ADR-0002 stage 6 TAG / display-preference). *Decision:* within a Confidence Tier, `preferred-for-display` is chosen deterministically by (1) CLTS BIPA conformance rate, (2) a linguist exceptions table, (3) intra-Source newest version, (4) lexicographic id. Cross-Source recency and bare plurality are rejected as primary; plurality is a pre-filter for N≥3 only. Sources are never discarded (CONTEXT.md ratchet). *Escalation:* when same-tier Sources disagree on the ADR-0001 openness verdict or nucleus-vs-coda structure, do not auto-pick — emit to the `tiebreak-review` queue (shared with the diphthong-vs-glide lane). *Supersedes:* ADR-0002's `on-block STOP + escalate` stub. *Residual human input:* ratify the conformance metric and author the exceptions table (§What still needs a human).

---

## What still needs a human

1. **Ratify the rigor metric.** Confirm CLTS BIPA conformance rate is an acceptable v1 proxy for same-tier transcription rigor (vs. a hand-ranked list). This is the one linguistic-judgment call the spike cannot make for you; everything downstream is mechanical once it is set.
2. **Author the exceptions table** — the short list of Sources whose measured conformance mis-ranks them (known-gold fieldwork datasets to promote; known-noisy aggregations to demote). Starts empty; grows as conflicts surface. This *is* the "priority ranking" ADR-0002 flagged, reframed from "rank everything" to "correct the few the metric gets wrong."
3. **Work the `tiebreak-review` queue** (shared lane with per-case diphthong-vs-glide verdicts). Bounded by §4; each item is a same-tier openness-flip needing one verdict.
4. **Set the plurality-pre-filter switch** (optional): whether N≥3 agreement may override a single higher-ranked dissenter, or rank always wins. Default proposed: rank wins unless the plurality includes a Source ranked ≥ the dissenter.

## Consequences for the strategy

- **ADR-0002:** replace the "Same-tier Source tiebreak — Unresolved Q-N; until minted, `on-block STOP + escalate`" open sub-decision with a citation to the minted Q-N; keep the diphthong-vs-glide item, but note the two now share one `tiebreak-review` lane.
- **IMPLEMENTATION-STRATEGY §11:** move "same-tier Source tiebreak (Q-N)" out of *Genuinely still open* into the resolved ledger (row: "same-tier tiebreak → conformance-ranked deterministic pick + bounded escalate → `spikes/same-tier-tiebreak` · Q-N"), leaving only the *residual human* items (ratify metric, author exceptions table) flagged.
- **Pipeline (stage 6 TAG):** implement `preferred` selection as the deterministic function above; emit a per-Source `bipa_conformance` field (free from stage 3) to drive it; add a `tiebreak-review` escalation output alongside the stage-7 spot-check queue.
- **No CONTEXT.md change needed:** the rule is a concrete realization of "one marked preferred for display" + the never-discard ratchet — it fills the mechanism, it does not alter the model.
- **Cross-link:** this and the per-case diphthong-vs-glide verdicts should share one review tool/queue; do not build two.
