"""Openness classifier (ADR-0001 rule; ADR-0002 stage 4b/5).

Decides whether a canonicalized single-syllable form is an OPEN monosyllable, and
emits the Classification Confidence honesty axis.

ADR-0001 inclusion rule: exactly one syllable, nucleus is a vowel or diphthong,
NO coda. Diphthongs are IN; vowel-less syllabic-consonant words are OUT.

The unit is the SEGMENT, not the letter. A nucleus is one vowel segment, so an
unmarked vowel pair ("r u a", or the bare string "rua") is two nuclei and two
syllables — hiatus — and is excluded. Only the source can make two vowels one
nucleus: a single segment ("ai" in CLDF Segments), a tie bar, or a non-syllabic
mark on the second vowel. Before 2026-09-29 any two adjacent vowel LETTERS were
called a diphthong with high confidence, which admitted ~22k two-syllable forms
(Polynesian rua 'two' among them).

The hard case (research.md / diphthong-glide spike): a final glide (Vj, Vw) —
is it a diphthong nucleus (open) or a coda glide (closed)? ADR-0001 rules it a
diphthong → OPEN, but the verdict *rests on that contested analysis*, so it earns
a LOWER Classification Confidence and, at the pipeline level, may be routed to the
per-(language, pattern) review queue.

Classification Confidence (CONTEXT.md): high = uncontested; medium = contested but
source/expert-resolved; low = editorial-rule only. `under_review` is orthogonal
(an expert ruling is pending) and is set by the pipeline, not here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
import unicodedata

from oms.canon import graphemes

# IPA vowel base characters (monophthong nuclei). Length/nasalization/syllabicity
# ride as trailing marks on the base and do not change the class.
_VOWELS = set("aeiouyɨʉɯɪʏʊøɘɵɤəɛœɜɞʌɔæɐɶɑɒɚɝ")
# Glides — the diphthong-vs-glide crux.
_GLIDES = set("jwɥɰ")
_NON_SYLLABIC = {"̯", "̑"}   # a vowel with this mark is an offglide, not a nucleus
_SYLLABIC_MARKS = {"̩", "̍"}  # combining vertical line below / above
_NASALS = set("mnŋɲɳɴɱ")

HIGH, MEDIUM, LOW = "high", "medium", "low"

# Kept for callers that group a canonical string into phoneme tokens.
_segment = graphemes


@dataclass(frozen=True)
class Openness:
    is_open: bool
    confidence: str          # high | medium | low  (Classification Confidence)
    nucleus_type: str        # monophthong | diphthong | diphthong(V+glide) | none
    contested: bool          # True when the verdict rests on the diphthong analysis
    reason: str


def _classify(token: str) -> str:
    # NFD so a precomposed vowel like "ã" (U+00E3) reads as its base letter ("a").
    nfd = unicodedata.normalize("NFD", token)
    if nfd[0] in _VOWELS:
        return "G" if any(m in nfd for m in _NON_SYLLABIC) else "V"
    if nfd[0] in _GLIDES:
        return "G"
    return "C"


def _bare_nasal(token: str) -> bool:
    """A segment whose only full letter is a nasal (m, n̥, mʷ). "mb" is not one:
    a second letter makes it a prenasalized stop. Modifier letters (ʷ ʰ) are
    category Lm and do not count."""
    nfd = unicodedata.normalize("NFD", token)
    return nfd[0] in _NASALS and not any(unicodedata.category(c) in ("Ll", "Lo", "Lu") for c in nfd[1:])


def _vowel_count(token: str) -> int:
    return sum(1 for ch in unicodedata.normalize("NFD", token) if ch in _VOWELS)


def classify_openness(segments: Sequence[str] | str) -> Openness:
    """Classify a tone-blind form given as its SEGMENTS. A bare string is split
    per grapheme, so its adjacent vowels count as separate segments."""
    tokens = graphemes(segments) if isinstance(segments, str) else list(segments)
    types = [_classify(t) for t in tokens]

    # A consonant/glide carrying a syllabicity mark IS a nucleus (kr̩ba = kr̩ + ba).
    # Alone -> consonant nucleus (out per ADR-0001); next to a vowel -> a second
    # syllable (also out). Without this check the mark folds into the token and a
    # syllabic nucleus masquerades as an onset consonant (2026-07-04 leak: kr̩ba,
    # r̩kʂi shipped as "open monophthongs").
    if any(ty in ("C", "G") and any(m in unicodedata.normalize("NFD", tok) for m in _SYLLABIC_MARKS)
           for tok, ty in zip(tokens, types)):
        return Openness(False, HIGH, "none", False,
                        "syllabic consonant nucleus — excluded (ADR-0001)")

    nuclei = [i for i, t in enumerate(types) if t == "V"]
    if not nuclei:
        return Openness(False, HIGH, "none", False,
                        "no vowel nucleus (syllabic consonant / all-consonant) — excluded (ADR-0001)")
    # ADR-0001 requires exactly ONE syllable, so exactly one vowel segment.
    if len(nuclei) > 1:
        return Openness(False, HIGH, "none", False,
                        "more than one vowel segment (hiatus or second syllable) — excluded (ADR-0001)")

    nucleus = nuclei[0]
    verdict = _verdict(tokens, types, nucleus)
    # A nasal written as its OWN segment before a consonant is ambiguous: a
    # syllabic nasal (Bantu n̩.ku — two syllables), a pre-initial (Tibeto-Burman
    # m.dza — one) or a prenasalized stop the source's profile did not merge.
    # Segmentation does not settle it: excluding these on 2026-09-29 removed
    # ~350 Tibeto-Burman pre-initial forms. So the form stays, contested
    # (ADR-0001 addendum). One segment ("mb") or a superscript ("ⁿb") is plain.
    if verdict.is_open and any(_bare_nasal(tok) and nxt == "C"
                               for tok, nxt in zip(tokens[:nucleus], types[1:nucleus + 1])):
        return replace(verdict, confidence=MEDIUM, contested=True,
                       reason=verdict.reason + "; nasal segment before a consonant — syllabic or pre-initial, contested")
    return verdict


def _verdict(tokens: list[str], types: list[str], nucleus: int) -> Openness:
    """Coda and nucleus analysis for a form with exactly one vowel segment."""
    after = types[nucleus + 1:]
    if "C" in after:
        return Openness(False, HIGH, "monophthong", False,
                        "coda consonant after nucleus — closed, excluded (ADR-0001)")

    if after:  # only glides can be here
        return Openness(True, MEDIUM, "diphthong(V+glide)", True,
                        "final glide analyzed as diphthong nucleus → open (ADR-0001, contested)")

    vowels = _vowel_count(tokens[nucleus])
    if vowels == 2:
        return Openness(True, MEDIUM, "diphthong", False,
                        "the source writes one diphthong segment, no coda → open (ADR-0001)")
    if vowels >= 3:
        return Openness(True, MEDIUM, "diphthong", True,
                        "one segment of 3+ vowels (triphthong vs hiatus) — open but contested (ADR-0001)")
    return Openness(True, HIGH, "monophthong", False,
                    "monophthong nucleus, no coda → open (ADR-0001)")
