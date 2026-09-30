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

## Addendum 2026-09-29 — syllables are counted from the source's segments

**Vowels.** A nucleus is one vowel *segment*. Two vowel segments are two syllables (hiatus: Polynesian *ru.a* 'two') and the form is excluded. Two vowels are one diphthong nucleus only when the source says so: one segment (`ai` in CLDF Segments), a tie bar (`a͡i`), or a non-syllabic mark (`aɪ̯`). A source-marked diphthong is *medium* Classification Confidence. Sources without segments (ABVD) are respelled first, and their vowel pairs drop out, because a spelling cannot tell the two cases apart. Before this, any two adjacent vowel letters counted as a high-confidence diphthong, which admitted ~22k two-syllable postings.

**Nasals.** A nasal written as its own segment before a consonant (`m b a`, `n k u`, `m dz a`) is *contested*, not excluded: the form stays, at medium confidence, under review. The first ruling excluded these as syllabic nasals (Bantu *n̩.ku*). Measured on the build, that removed ~350 Tibeto-Burman forms whose nasal is a pre-initial inside one syllable (*m.dza*), and Bantu and Chadic sources split prenasalized stops for reasons of dataset preparation, not analysis. Segmentation is evidence for vowels here but not for nasals. One segment (`mb`) or a superscript nasal (`ⁿb`) reads as a prenasalized stop and is uncontested.
