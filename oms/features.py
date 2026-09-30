"""Feature annotation (ADR-0002 stage 4b) — onset class + nucleus bucket.

Derives the two heatmap axes from a canonical form. The production pipeline uses
the CLTS/cltoolkit feature join; this is the self-contained v1 that yields the
~9 onset classes × ~7 nucleus buckets the two-level heatmap grid needs
(heatmap-bucketing spike). Both are computed mechanically from CLTS features in
production; here from small, explicit sets.
"""

from __future__ import annotations

import unicodedata

from oms.openness import _segment, _VOWELS, _GLIDES

# Onset manner classes (sonority-ordered-ish), ~9 rows for the heatmap.
_NASAL = set("mnŋɲɳɴ")
_STOP = set("pbtdʈɖcɟkgɡqɢʔ")
_IMPLOSIVE = set("ɓɗʄɠʛ")          # kept a visible class, never a gutter (mission)
# ɕ ʑ: alveolo-palatal; ɬ ɮ: lateral fricatives; ʍ: voiceless labial-velar
_FRICATIVE = set("fvθðszʃʒʂʐçʝxɣχʁħʕhɦɸβɕʑɬɮʍ")
_AFFRICATE_HINT = set("ʦʣʧʤʨʥ")     # precomposed affricates (post-tie-bar-drop)
_LIQUID = set("lrɾɽɭʎʟɫʀɹɻɺ")        # laterals, rhotics, and the r-like approximants
_APPROXIMANT_GLIDE = set("ʋ")        # labiodental approximant: a glide, like w
_GLOTTAL_MODIFIER = "ˀ"
_CLICK = set("ǀǁǂǃʘ")


def _base(token: str) -> str:
    return unicodedata.normalize("NFD", token)[0]


def onset_class(form: str) -> str:
    """Class of the FIRST onset consonant; 'none' for a vowel/glide-initial form.

    A leading modifier letter (ⁿ ᵐ ᵑ ʰ ˀ — category Lm) marks the consonant after
    it: prenasalized, pre-aspirated, pre-glottalized. It is skipped, so the
    consonant decides. A lone ˀ before a vowel IS the onset: a glottal stop."""
    toks = _segment(form)
    for k, tok in enumerate(toks):
        b = _base(tok)
        if unicodedata.category(b) == "Lm":
            if b == _GLOTTAL_MODIFIER and k + 1 < len(toks) and _base(toks[k + 1]) in _VOWELS:
                return "stop"
            continue
        if b in _VOWELS:
            return "none"          # vowel-initial (∅ onset) — the null-onset row
        if b in _GLIDES or b in _APPROXIMANT_GLIDE:
            return "glide"
        if b in _NASAL:
            return "nasal"
        if b in _IMPLOSIVE:
            return "implosive"
        if b in _CLICK:
            return "click"
        if b in _STOP:
            return "stop"
        if b in _AFFRICATE_HINT:
            return "affricate"
        if b in _FRICATIVE:
            return "fricative"
        if b in _LIQUID:
            return "liquid"
        return "other"
    return "none"


# Nucleus quality buckets, ~7 columns. Diphthongs get their own group upstream.
_FRONT_HIGH = set("iyɪʏ")
_FRONT_MID = set("eøɛœ")
_CENTRAL = set("əɨʉɘɵɜɞɐ")
_BACK_HIGH = set("uʊɯ")
_BACK_MID = set("oɔɤ")
_LOW = set("aæɑɒɶʌ")


def nucleus_bucket(form: str, nucleus_type: str) -> str:
    """Vowel-quality bucket of the nucleus, or 'diphthong' for diphthong nuclei."""
    if nucleus_type.startswith("diphthong"):
        return "diphthong"
    # nucleus = last vowel base
    for tok in reversed(_segment(form)):
        b = _base(tok)
        if b in _VOWELS:
            for name, s in (("i", _FRONT_HIGH), ("e", _FRONT_MID), ("ə", _CENTRAL),
                            ("u", _BACK_HIGH), ("o", _BACK_MID), ("a", _LOW)):
                if b in s:
                    return name
            return "other"
    return "other"
