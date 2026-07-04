"""Openness classifier (ADR-0001 rule; ADR-0002 stage 4b/5).

Decides whether a canonicalized single-syllable form is an OPEN monosyllable, and
emits the Classification Confidence honesty axis.

ADR-0001 inclusion rule: exactly one syllable, nucleus is a vowel or diphthong,
NO coda. Diphthongs are IN; vowel-less syllabic-consonant words are OUT.

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

from dataclasses import dataclass
import unicodedata

# IPA vowel base characters (monophthong nuclei). Length/nasalization/syllabicity
# ride as trailing marks on the base and do not change the class.
_VOWELS = set("aeiouyɨʉɯɪʏʊøɘɵɤəɛœɜɞʌɔæɐɶɑɒɚɝ")
# Glides — the diphthong-vs-glide crux.
_GLIDES = set("jwɥɰ")
# Spacing modifier letters that attach to the preceding phoneme, not new segments.
_ATTACH = set("ːˑʰʲʷˠˤⁿˡʼˀ̚˞")

HIGH, MEDIUM, LOW = "high", "medium", "low"


@dataclass(frozen=True)
class Openness:
    is_open: bool
    confidence: str          # high | medium | low  (Classification Confidence)
    nucleus_type: str        # monophthong | diphthong | diphthong(V+glide) | none
    contested: bool          # True when the verdict rests on the diphthong analysis
    reason: str


def _segment(form: str) -> list[str]:
    """Group a canonical string into phoneme tokens (base + trailing marks/modifiers)."""
    tokens: list[str] = []
    for ch in form:
        attaches = ch in _ATTACH or unicodedata.combining(ch) != 0
        if attaches and tokens:
            tokens[-1] += ch
        else:
            tokens.append(ch)
    return tokens


def _classify(token: str) -> str:
    # Canonical forms are NFC, so a nasal/precomposed vowel like "ã" (U+00E3) must
    # be decomposed to read its base letter ("a") before classifying.
    base = unicodedata.normalize("NFD", token)[0]
    if base in _VOWELS:
        return "V"
    if base in _GLIDES:
        return "G"
    return "C"


def classify_openness(form: str) -> Openness:
    """Classify a canonicalized, tone-blind single-syllable form."""
    tokens = _segment(form)
    types = [_classify(t) for t in tokens]

    if "V" not in types:
        return Openness(False, HIGH, "none", False,
                        "no vowel nucleus (syllabic consonant / all-consonant) — excluded (ADR-0001)")

    first_v = min(i for i, t in enumerate(types) if t == "V")
    last_v = max(i for i, t in enumerate(types) if t == "V")
    # ADR-0001 requires exactly ONE syllable: the nucleus is a single contiguous
    # vowel run. A non-vowel (consonant or glide) BETWEEN vowels marks a second
    # syllable, so the form is polysyllabic and excluded.
    if any(t != "V" for t in types[first_v:last_v + 1]):
        return Openness(False, HIGH, "none", False,
                        "more than one syllable (non-vowel between vowels) — excluded (ADR-0001)")

    after = types[last_v + 1:]

    if "C" in after:
        return Openness(False, HIGH, "monophthong", False,
                        "coda consonant after nucleus — closed, excluded (ADR-0001)")

    if after:  # only glides can be here
        return Openness(True, MEDIUM, "diphthong(V+glide)", True,
                        "final glide analyzed as diphthong nucleus → open (ADR-0001, contested)")

    # ends in a vowel: count the nucleus vowel run for monophthong vs VV diphthong
    run = 0
    i = last_v
    while i >= 0 and types[i] == "V":
        run += 1
        i -= 1
    if run == 2:
        return Openness(True, HIGH, "diphthong", False,
                        "vowel+vowel diphthong nucleus, no coda → open (ADR-0001)")
    if run >= 3:
        # 3+ contiguous vowels: a genuine triphthong or (more often) hiatus =
        # multiple syllables. Contested — open but lower confidence, routed to review.
        return Openness(True, MEDIUM, "diphthong", True,
                        "3+ vowel sequence (triphthong vs hiatus) — open but contested (ADR-0001)")
    return Openness(True, HIGH, "monophthong", False,
                    "monophthong nucleus, no coda → open (ADR-0001)")
