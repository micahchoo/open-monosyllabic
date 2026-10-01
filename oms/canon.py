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
_NON_IPA = set("*+=|/\\<>[]{}()~^?!◌đȥ-,’") | {chr(c) for c in range(0x41, 0x5B)}
# - , ’ (2026-10-01 audit): 34 shapes carried a hyphen (n-ma), others a comma or a
# typographic apostrophe — punctuation from the source's spelling, never a segment.
# ◌ U+25CC: dotted-circle placeholder from Wiktionary combining-sign entries —
# leaked into shapes like "◌jɐ" (2026-07-04); a placeholder is never a segment.
# đ ȥ: ABVD-only spelling letters (Vietnamese đường; ȥ has no reading we can
# confirm). Respelling đ alone would leave ư, â wrong in the same words.


# Letters with no IPA reading (the last 12 "other" shapes, 2026-09-29): ß ǥ ɩ Ɉ
# are orthographic; ɿ ʅ are the Sinological apical vowels, with no single IPA
# equivalent; a dash is punctuation. By category: IPA has no capital letters
# (Ɵ, Ŋ — not only ASCII A–Z) and no private-use characters (U+F182).
_NON_IPA_LETTERS = set("ßǥɩɈɿʅ–—")


def is_clean_ipa(segmental: str) -> bool:
    """True if the canonical string is clean IPA — no reconstruction/cover-symbol
    /annotation noise. Forms failing this are excluded by the pipeline (hygiene)."""
    return bool(segmental) and not any(
        c in _NON_IPA or c in _NON_IPA_LETTERS or unicodedata.category(c) in ("Lu", "Co")
        for c in segmental)

# R8: stress + prosodic separators are discarded (not contrastive at segment level).
_STRIP = {
    "ˈ", "ˌ",   # ˈ ˌ primary/secondary stress
    "͡", "͜",   # ◌͡ ◌͜ tie bars (R9: drop bar, keep both segments)
    ".", " ", "‿",   # syllable break, space, undertie
    "ˈ",
}

# R6: half-long folds to long (v1 policy; Q-c flags third-degree-length exceptions).
# Notational variants of one sound fold to the IPA letter, or one sound gets two
# Shape keys: ASCII g (U+0067) is IPA ɡ (U+0261) — 21 shapes were split in two,
# /go/ 66 languages beside /ɡo/ 2 — and ASCII ":" and "·" write length.
# Sinological letters (suntb, castrosui keep them in their Segments) have one
# fixed meaning, the alveolo-palatal series; IPA writes it with the advanced
# mark, which keeps them distinct from plain ɲ / c / ɟ (never merge contrasts).
_FOLD = {"ˑ": "ː", ":": "ː", "·": "ː", "g": "ɡ",
         "ȵ": "ɲ̟", "ȶ": "c̟", "ȡ": "ɟ̟",
         # precomposed affricate letters are the two-letter affricate, one segment
         # (2026-10-01: /ʥi/ in 1 language beside /dʑi/ in 69)
         "ʦ": "ts", "ʣ": "dz", "ʧ": "tʃ", "ʤ": "dʒ", "ʨ": "tɕ", "ʥ": "dʑ"}

# A nasal and a stop written as ONE segment is a prenasalized stop, which IPA
# writes with a superscript nasal: segmented "mb a" and "ᵐba" are one word
# (2026-10-01: 133 twin shapes, /ⁿda/ 88 languages beside /nda/ 25). Two
# segments ("n d a") stay a cluster: only the source's segmentation decides.
_PRENASAL = {"m": "ᵐ", "n": "ⁿ", "ŋ": "ᵑ", "ɲ": "ᶮ", "ɳ": "ᶯ"}
_STOP_BASES = set("pbtdʈɖcɟkɡqɢ")


# Spacing modifier letters that attach to the preceding phoneme, not new segments.
_ATTACH = set("ːˑʰʲʷˠˤⁿˡʼˀ̚˞:·")   # ASCII ":" "·" write length too: "ma:" is m + aː, never a coda
_TIE = {"͡", "͜"}


def graphemes(ipa: str) -> list[str]:
    """Split an UNSEGMENTED transcription into segments: a base letter plus its
    combining marks and attached modifiers; a tie bar joins the next base into
    the same segment (t͡s, a͡i). Adjacent plain vowels stay separate segments, so
    an unmarked "ai" reads as two nuclei — only the source can make it one."""
    tokens: list[str] = []
    join = False
    for ch in unicodedata.normalize("NFD", ipa):
        if tokens and (join or ch in _TIE or ch in _ATTACH or unicodedata.combining(ch)):
            tokens[-1] += ch
            join = ch in _TIE
        else:
            tokens.append(ch)
            join = False
    return tokens


@dataclass(frozen=True)
class Canon:
    """Result of canonicalization: the tone-blind key + the siphoned tone."""
    segmental: str   # the canonical, tone-blind Shape/Form key
    tone: str        # tone letters/digits in source order ("" if atonal)
    segments: tuple[str, ...] = ()   # the segments behind the key; decide syllable count


class Canonicalizer:
    """Seam (ADR-0002): swap this for a pyclts/CLTS-backed impl in production."""

    version = SCHEME_VERSION

    def __call__(self, ipa: str) -> Canon:
        return canonicalize(ipa)


def canonicalize(ipa: str, segmented: bool = False) -> Canon:
    """Apply oms-canon-v1 R1-R12 to a source IPA string.

    `segmented` means the source already split the word into segments with
    spaces (CLDF Segments, WikiPron); those boundaries are kept as they are.
    Otherwise the string is split per grapheme (see `graphemes`)."""
    # R1: NFD gives Unicode canonical ordering of combining marks by combining
    # class — so diacritic ORDER is normalized for free (R10). We recompose to
    # NFC at the end for a compact, human-readable key.
    s = unicodedata.normalize("NFD", ipa.strip())
    tokens = s.split() if segmented else graphemes(s)

    tone_chars: list[str] = []
    segments: list[str] = []
    for tok in tokens:
        out: list[str] = []
        for ch in tok:
            if ch in _TONE_ALL:        # R7: siphon tone (letters, Chao digits, AND diacritics)
                tone_chars.append(ch)
                continue
            if ch in _STRIP:           # R8/R9: drop stress, tie bars, separators
                continue
            if ch in _FOLD:            # R6: half-long -> long
                out.append(_FOLD[ch])
                continue
            out.append(ch)            # R2-R5: preserve base + contrastive diacritics
        if out:                        # a tone- or stress-only token is no segment
            seg = "".join(out)
            if len(seg) > 1 and seg[0] in _PRENASAL and seg[1] in _STOP_BASES:
                seg = _PRENASAL[seg[0]] + seg[1:]
            segments.append(unicodedata.normalize("NFC", seg))

    return Canon(segmental="".join(segments), tone="".join(tone_chars), segments=tuple(segments))
