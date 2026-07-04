# What counts as an open monosyllable

A form is included in the catalog when it is exactly one syllable, its nucleus is a **vowel or diphthong**, and it has **no coda** (no consonant after the nucleus). Diphthong-final words ("bye" /baɪ/, "now" /naʊ/, "go" /goʊ/) are treated as open — the diphthong is a single complex vowel nucleus, not vowel+glide. Vowel-less **syllabic-consonant** words ("mm" /m̩/, "shh") are **excluded** — the nucleus must be a vowel.

## Why this is recorded

Whether a short word "counts as open" is genuinely theory-dependent, and defensible frameworks disagree (the diphthong-vs-vowel+glide split alone can roughly double or halve a language's yield). The choice is hard to reverse (it defines the entire catalog's contents), surprising without context (a purist reader will expect diphthongs analyzed as CVG and excluded), and the result of a real trade-off.

## Considered options

- **Strict (diphthong = vowel+glide → closed):** rejected — excludes common everyday monosyllables ("bye", "now"), shrinking the catalog against the project's purpose of surveying open monosyllables broadly.
- **Track both analyses, user-filterable:** rejected for now — real value but significant added data and UI complexity; can be revisited if a strict-vs-inclusive toggle is later wanted.
- **Include syllabic consonants (no-coda = open):** rejected — theoretically consistent but the vowel-less nucleus cuts against the everyday sense of "ends in a vowel" and adds rare, confusing entries for a broad audience.

## Consequences

- Per-language yield skews larger than a strict analysis would give; English and other diphthong-rich languages contribute heavily.
- The nucleus classifier must reliably distinguish a diphthong nucleus from a vowel+glide sequence — a known hard case in automatic transcription, and a place where machine-guessed data will need extra scrutiny.
