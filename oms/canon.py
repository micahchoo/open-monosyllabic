"""oms-canon-v1 — the versioned canonicalization scheme (ADR-0002 stage 3).

Turns a heterogeneous source IPA transcription into a stable, tone-blind
canonical string (the Shape / Form identity key) plus a separately-stored tone
string. This is the identity function behind "every language with /ma/": two
transcriptions that mean the same sound MUST canonicalize to the same string,
or Shapes fragment silently.

This is the self-contained v1 skeleton. The ADR names pyclts/CLTS BroadIPA as the
production backend (`str(bipa[g])`); the `Canonicalizer` seam below lets a
CLTS-backed implementation drop in without touching callers. The rule table
(R1-R12) is faithful to the `canonicalization-scheme` spike; the six contested
cells it flags (Q-a..Q-f) are marked in tests as pending linguist ratification.

Locked invariant: NEVER merge contrastive segments. /a/ (U+0061) and /ɑ/ (U+0251)
are distinct base letters and stay distinct; length, nasalization, and
syllabicity are contrastive and preserved. Only true notational variants unify.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

SCHEME_VERSION = "oms-canon-v1"

# --- R-rule character classes (spike table, self-contained subset) ------------

# R7: tone is stripped from the segmental key and siphoned into Form.tones.
# CLTS BroadIPA encodes tone as tone letters / Chao digits, NOT vowel diacritics,
# so vowel diacritics are left to their segmental meaning (no false tone strip).
_TONE_LETTERS = {chr(c) for c in range(0x02E5, 0x02EA)}  # ˥ ˦ ˧ ˨ ˩
_TONE_STEP = {"ꜛ", "ꜜ", "ꜝ"}              # ꜛ ꜜ (up/down/mid step)
_TONE_SUPERS = set("⁰¹²³⁴⁵⁶⁷⁸⁹")                          # superscript Chao digits
_TONE = _TONE_LETTERS | _TONE_STEP | _TONE_SUPERS

# Combining tone DIACRITICS (Yoruba/Igbo/Vietnamese-style orthographic tone marks):
# grave/acute/macron/circumflex/caron/double + the below-tone marks. Siphoned to
# tone so /ba/ groups tone-blind whether tone is written as a letter or a diacritic.
# CRITICAL: the combining tilde U+0303 (nasalization) is NOT here — it is segmental
# and contrastive, so it is preserved. This ratifies canonicalization contested-cell
# Q (tone-diacritic policy); caveat: a diacritic marking pitch-accent (not tone) is
# also siphoned, which is acceptable for a tone-blind catalog.
_TONE_COMBINING = {chr(c) for c in
                   (0x0300, 0x0301, 0x0302, 0x0304, 0x030B, 0x030C, 0x030F, 0x0316, 0x0317)}
# ASCII tone digits: Sino-Tibetan/Kra-Dai datasets write Chao tones as plain digits
# (e.g. "tsa33", "sa53"). Siphon them to tone so the shape stays clean and tone-blind.
_TONE_ASCII = set("0123456789")
_TONE_ALL = _TONE | _TONE_COMBINING | _TONE_ASCII

# Non-IPA notation that must NOT survive into a Shape (hygiene). A canonical string
# containing any of these is not a clean attested open monosyllable: reconstruction
# markers (*), morpheme/cover-symbol boundaries (+ = | / < > brackets), and ASCII
# UPPERCASE letters (A-Z) — real IPA is lowercase; ASCII caps are cover symbols
# (V=vowel, N=nasal) or tone-class labels, never segments. (IPA small-caps like ɪ ɴ ʀ
# are separate non-ASCII codepoints and are unaffected.)
_NON_IPA = set("*+=|/\\<>[]{}()~^?!") | {chr(c) for c in range(0x41, 0x5B)}


def is_clean_ipa(segmental: str) -> bool:
    """True if the canonical string is clean IPA — no reconstruction/cover-symbol
    /annotation noise. Forms failing this are excluded by the pipeline (hygiene)."""
    return bool(segmental) and not any(c in _NON_IPA for c in segmental)

# R8: stress + prosodic separators are discarded (not contrastive at segment level).
_STRIP = {
    "ˈ", "ˌ",   # ˈ ˌ primary/secondary stress
    "͡", "͜",   # ◌͡ ◌͜ tie bars (R9: drop bar, keep both segments)
    ".", " ", "‿",   # syllable break, space, undertie
    "ˈ",
}

# R6: half-long folds to long (v1 policy; Q-c flags third-degree-length exceptions).
_FOLD = {"ˑ": "ː"}   # ˑ -> ː


@dataclass(frozen=True)
class Canon:
    """Result of canonicalization: the tone-blind key + the siphoned tone."""
    segmental: str   # the canonical, tone-blind Shape/Form key
    tone: str        # tone letters/digits in source order ("" if atonal)


class Canonicalizer:
    """Seam (ADR-0002): swap this for a pyclts/CLTS-backed impl in production."""

    version = SCHEME_VERSION

    def __call__(self, ipa: str) -> Canon:
        return canonicalize(ipa)


def canonicalize(ipa: str) -> Canon:
    """Apply oms-canon-v1 R1-R12 to a source IPA string."""
    # R1: NFD gives Unicode canonical ordering of combining marks by combining
    # class — so diacritic ORDER is normalized for free (R10). We recompose to
    # NFC at the end for a compact, human-readable key.
    s = unicodedata.normalize("NFD", ipa.strip())

    tone_chars: list[str] = []
    out: list[str] = []
    for ch in s:
        if ch in _TONE_ALL:        # R7: siphon tone (letters, Chao digits, AND diacritics)
            tone_chars.append(ch)
            continue
        if ch in _STRIP:           # R8/R9: drop stress, tie bars, separators
            continue
        if ch in _FOLD:            # R6: half-long -> long
            out.append(_FOLD[ch])
            continue
        out.append(ch)            # R2-R5: preserve base + contrastive diacritics

    segmental = unicodedata.normalize("NFC", "".join(out))
    return Canon(segmental=segmental, tone="".join(tone_chars))
