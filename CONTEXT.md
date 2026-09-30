# Open Monosyllabic

An interactive Explorer for examining **open monosyllables** — one-syllable words ending in a vowel sound — across the world's languages. The mission is factual and neutral: look at open monosyllabic words across the globe. Global South / under-documented languages are prioritized first, but this is an *implicit* value that guides sourcing order, not an explicit advocacy message the interface foregrounds.

Data honesty is a first-class concern along **two independent axes**: (1) *source provenance* — machine-guessed pronunciations must be visibly distinguished from curated ones; and (2) *classification confidence* — whether an entry's status as an open monosyllable rests on the contested diphthong-vs-glide / coda call (ADR-0001). Neither may be hidden, so the catalog never misrepresents the languages it covers.

## Language

**Open Monosyllable**:
A word (or permitted word-shape) of exactly one syllable whose nucleus is a **vowel or diphthong** and which has **no coda** (no consonant after the nucleus). Diphthong-final words ("bye", "now", "go") count. Syllabic-consonant words with no vowel ("mm", "shh") do **not**. See [ADR-0001](docs/adr/0001-open-monosyllable-inclusion-rule.md).

**Language**:
A single language variety, identified by its Glottolog code (a standard registry of the world's languages). Carries three first-class metadata/typological attributes: **macroarea/region + coordinates** (from Glottolog), **documentation-status** (how well-described the variety is — lets the tool distinguish "no data sourced yet" from "genuinely absent"), and **prosodic type / word-minimality** (whether the language structurally permits open *light* monosyllables at all; research.md §1). These make an uneven per-language yield interpretable rather than noise. _(These are data-quality/typological metadata; the Global-South priority remains implicit — no mission-accountability surface is built on them.)_
_Avoid_: dialect (a variety may or may not be a separate Glottolog entry — don't conflate), tongue.

**Family**:
The Glottolog top-level family of a Language (e.g. Austronesian), read from each source's `Family` column. Languages in one family share history, so a count of languages that share a Shape is shown with its count of families: 134 Austronesian languages agreeing is one fact, not 134.
_Avoid_: stock, phylum, group.

**Examined**:
The number of distinct words of a Language that the openness rule judged — the denominator of its yield. A Language with no Forms has "none among N examined", which is a statement about the sample, never about the language.
_Avoid_: total, vocabulary size.

**Form**:
The backbone entity — an open monosyllable as attested in **one specific Language** (e.g. /ma/ in Mandarin), identified by its **canonicalized (CLTS BroadIPA) tone-blind segmental IPA**. Belongs to exactly one Language. Meaning-agnostic and always present: a Language is represented by its Forms even when no meaning data exists. Carries language-specific facts (which tones occur; a **Confidence Tier** for source provenance and a **Classification Confidence** for the openness call; one or more **Sources**; example Words).
_Avoid_: word (a Form has no meaning attached), syllable (too general).

**Shape**:
Not a stored entity — the **canonicalized (CLTS BroadIPA)** tone-blind segmental IPA **string** of a Form (e.g. "/ma/"), used to group Forms across languages *at query time* ("every language with /ma/"). Cross-language sameness is exact string match **on the canonical form** — canonicalization *is* the identity function, so it must run before matching, or /a/ vs /ɑ/ vs length-marked variants silently fragment the group.
_Avoid_: treating Shape as an entity; pattern, template.

**Tone**:
A pitch-based contrast that distinguishes words in tonal languages. Not part of the Shape string. Recorded at the **Form** level (which tones occur with this form in this language) and pinned to a specific value at the **Word** level.
_Avoid_: accent, pitch.

**Word**:
An actual attested word: a Form paired with a meaning in a language (e.g. Mandarin _mā_ 'mother'). Layered on top of Forms *where data is available*; absent for under-documented languages, which still appear as Forms.
_Avoid_: lexeme, entry, term.

**Gloss**:
The meaning of a Word, given in a shared reference vocabulary (Concepticon) so the same concept lines up across languages.
_Avoid_: definition, translation.

**Confidence Tier**:
An ordered trust level for the **source provenance** of an entry's IPA — *where the data came from*, NOT whether its openness classification holds (that is Classification Confidence). Shown as a badge. Three tiers, most-to-least trusted: **curated** (a curated linguistic dataset, e.g. Lexibank / NorthEuraLex, PHOIBLE-validated) › **mined** (dictionary-mined, e.g. WikiPron / Wiktextract) › **generated** (machine-guessed by grapheme-to-phoneme, e.g. Epitran). See Lifecycle for the ratchet rule, and [ADR-0002](docs/adr/0002-data-sourcing-and-ingestion-pipeline.md) for the Source→Tier table and precedence.
_Avoid_: quality, score, rating; **verified** (renamed to _curated_ — "verified" wrongly implied the openness call was checked).

**Classification Confidence**:
A second, independent honesty axis: whether an entry's status *as an open monosyllable* rests on the contested analytic call (diphthong-vs-glide, coda-hood) from [ADR-0001](docs/adr/0001-open-monosyllable-inclusion-rule.md). A three-level enum plus a flag: **high** (uncontested — a clean monophthong-final form like /ma/) › **medium** (contested but resolved by the source's own transcription or an expert ruling) › **low** (resolved only by our editorial rule — e.g. a silent-phonology default), with an orthogonal **`under_review`** flag when an expert ruling is still pending (rendered visibly, never hidden). Orthogonal to Confidence Tier — a _curated_-tier form can still be classification-`low`. Generated (G2P) forms ship `low` / `under_review=auto` and never enqueue a human.
_Avoid_: quality; tier (that word means source provenance here).

**Source**:
A specific dataset or tool an entry's data came from (e.g. "NorthEuraLex 0.9", "Epitran"). An entry may cite **more than one Source** — conflicting sources are all retained (PHOIBLE multi-inventory practice), with one marked *preferred for display*. Each Source maps to exactly one Confidence Tier. Concrete Sources, precedence, and the ingestion pipeline: [ADR-0002](docs/adr/0002-data-sourcing-and-ingestion-pipeline.md).
_Avoid_: origin, provenance (use Source).

**Audio**:
A spoken rendering of a Form or Word, badged by its own provenance — **recorded** (a genuine recording from an archive) vs **synthesized** (generated from IPA). An independent axis from Confidence Tier: a Form may have _curated_ data but only _synthesized_ audio. Synthesized audio is a machine guess and must be labeled as such, never passed off as a recording.
_Avoid_: sound, clip, pronunciation (ambiguous with the IPA).

## Relationships

_Model: separate-per-language (no shared Shape entity). Confirmed by user._

- A **Language** has many **Forms**; a **Form** belongs to exactly one **Language**.
- A **Language** carries **macroarea/region + coordinates**, **Family**, **Examined**, **documentation-status**, and **prosodic type / word-minimality** attributes.
- A **Form** has zero or many **Words** (example words carrying meaning); a **Word** belongs to exactly one **Form**.
- Every sourced entry (**Form**, **Word**) carries one **Confidence Tier**, one **Classification Confidence**, and **one or more Sources** (conflicts retained; one marked preferred for display).
- A **Form** or **Word** may have **Audio**, badged **recorded** or **synthesized** — a provenance axis independent of the two confidence axes.
- A **Word** carries at least one **Gloss** (its meaning). _(Polysemy — one Word, many Glosses — not yet resolved.)_
- Cross-language grouping ("every language with /ma/") is by **Shape** = the canonicalized tone-blind segmental IPA string, matched at query time. Not a stored relationship.
- Deleting a **Language** cascades to its **Forms** and their **Words** (they cannot exist orphaned). _(Proposed default — obvious cascade; correct if wrong.)_

## Lifecycle

- **Confidence Tier ratchets up only; Sources are never discarded.** When better data arrives, the entry gains the new **Source** and its *preferred-for-display* Tier is upgraded (generated → mined → curated). Earlier Sources are retained, not deleted — the ratchet governs which Source is *shown*, not which *exist*. A downgrade of the preferred Tier means the better source was wrong — treat as a correction event, not a routine update.

## Identity

- A **Form** is identified by (**Language** + **canonicalized (CLTS BroadIPA)** tone-blind segmental IPA). Canonicalization runs *before* the key is formed, under a **versioned scheme** stamped into the key so reprocessing under a new scheme doesn't silently rot deep links. Same language + same canonical string ⇒ same Form (tone differences do not split it; they are recorded as the set of tones the Form takes).
- **Shape** grouping key = the canonical tone-blind segmental IPA string alone; same canonical string across languages ⇒ same Shape group.
- **Inclusion rule** (what counts as an open monosyllable): one syllable · nucleus is a vowel or diphthong · no coda. The syllable count is read from the source's SEGMENTS: two vowel segments are two syllables; a diphthong is one nucleus only when the source writes it as one segment, with a tie bar, or with a non-syllabic mark. A nasal written as its own segment before a consonant is contested (syllabic nasal or pre-initial) — kept, under review. Diphthongs in, syllabic consonants out. See [ADR-0001](docs/adr/0001-open-monosyllable-inclusion-rule.md). The per-entry uncertainty of this call is carried as **Classification Confidence**.
- A **Word** is identified by (**Form** + tone + **Gloss**); _mā_ 'mother' and _mǎ_ 'horse' are distinct Words sharing one Form. A Word may carry more than one **Gloss** (polysemy) without splitting into two Words. _(Proposed default; correct if wrong.)_

## Example dialogue

> **Dev:** "A visitor searches /ma/ and sees Mandarin, Yoruba, and Fijian. Is /ma/ one thing stored once?"
> **Domain:** "No — /ma/ isn't stored. Each language has its own **Form** /ma/. The search groups Forms by their tone-blind IPA **Shape** string at query time."
> **Dev:** "Mandarin /ma/ has four tones and means several things. One Form or four?"
> **Domain:** "One **Form**. It records that all four tones occur. Each tone-plus-meaning — _mā_ 'mother', _mǎ_ 'horse' — is a separate **Word** hanging off that Form, each with its **Gloss**."
> **Dev:** "And if the Yoruba /ma/ came from an automatic guesser?"
> **Domain:** "Then its **Confidence Tier** is _generated_ and its **Source** names the tool. If a curated dataset later confirms it, we add that Source and upgrade the preferred tier to _curated_ — the earlier source is kept, and it never ratchets the other way."
> **Dev:** "And 'bye' /baɪ/ from that same curated dataset — same confidence?"
> **Domain:** "Different axis. Its **Confidence Tier** is _curated_, but its **Classification Confidence** is lower — whether it counts as *open* rests on analyzing /aɪ/ as a diphthong nucleus (ADR-0001), which is a contested call. Both badges show."

## Flagged ambiguities

- **"Open monosyllable" is partly theory-dependent.** — RESOLVED by [ADR-0001](docs/adr/0001-open-monosyllable-inclusion-rule.md): vowel/diphthong nucleus, no coda; diphthongs in, syllabic consonants out.
