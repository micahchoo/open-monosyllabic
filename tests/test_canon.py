"""The canonicalization corpus (ADR-0002 / IMPLEMENTATION-STRATEGY §4-5).

Each row is `source IPA -> (expected canonical segmental, expected tone)`.
The corpus IS the enumeration: implement the canonicalizer to make it green.
Contested cells (Q-a..Q-f) are flagged as pending linguist ratification.
"""

import unittest

from oms.canon import canonicalize, is_clean_ipa, SCHEME_VERSION


class TestCanonCorpus(unittest.TestCase):

    # (source, expected_segmental, expected_tone, note)
    CORPUS = [
        # --- R7 tone siphoning: same segment, tone split off, tone-blind key ---
        ("ma˥", "ma", "˥", "high-tone /ma/ -> tone-blind /ma/"),
        ("ma˧˥", "ma", "˧˥", "rising contour -> same key, contour tone"),
        ("ma", "ma", "", "atonal /ma/ keys identically to any toned /ma/"),
        ("to²", "to", "²", "Chao superscript digit tone siphoned"),
        # tone as combining DIACRITICS (Yoruba/Igbo): siphoned, shape tone-blind
        ("bá", "ba", "́", "Yoruba high tone (acute diacritic) siphoned"),
        ("bà", "ba", "̀", "Yoruba low tone (grave) siphoned"),
        ("kɔ̄", "kɔ", "̄", "Yoruba mid tone (macron) siphoned"),
        ("ɔ̃́", "ɔ̃", "́", "nasal vowel + high tone: nasal KEPT, tone siphoned"),
        # --- contrastive segments are NEVER merged (locked invariant) ---
        ("a", "a", "", "/a/ front"),
        ("ɑ", "ɑ", "", "/ɑ/ back — distinct from /a/, must not merge"),
        # --- R2/R4/R5 preserve contrastive diacritics ---
        ("aː", "aː", "", "length is contrastive — preserved"),
        ("ã", "ã", "", "nasalization is contrastive — preserved"),
        ("ɓa", "ɓa", "", "implosive onset preserved (Global-South segment)"),
        # --- R6 half-long folds to long ---
        ("aˑ", "aː", "", "half-long -> long (v1 policy; Q-c)"),
        # --- R9 tie bars dropped, both segments kept ---
        ("t͡sa", "tsa", "", "affricate tie bar dropped, /ts/ kept"),
        # --- R8 stress + separators discarded ---
        ("ˈma", "ma", "", "primary stress discarded"),
        ("ma.ba"[:2], "ma", "", "syllable-break char never reaches a monosyllable key"),
        # --- R10 diacritic order normalized: nasal+long in either input order
        #     canonicalizes identically ---
        ("ãː", "ãː", "", "nasal + long"),
        ("ãː", "ãː", "", "same, decomposed input order -> same key"),
        # --- one key per sound: notational variants fold (2026-09-29) ---
        ("ga", "ɡa", "", "ASCII g is the IPA script g — /go/ and /ɡo/ were split"),
        ("ma:", "maː", "", "ASCII colon writes length"),
        ("ma·", "maː", "", "middle dot writes length"),
        # Sinological letters have one fixed meaning: the alveolo-palatal series.
        # Written as IPA with the advanced mark, so they stay distinct from ɲ, c.
        ("ȵa", "ɲ̟a", "", "Sinological ȵ = alveolo-palatal nasal ɲ̟"),
        ("ȶa", "c̟a", "", "Sinological ȶ = alveolo-palatal stop c̟"),
        ("ȡa", "ɟ̟a", "", "Sinological ȡ = voiced alveolo-palatal stop ɟ̟"),
    ]

    def test_scheme_version(self):
        self.assertEqual(SCHEME_VERSION, "oms-canon-v1")

    def test_corpus(self):
        for src, exp_seg, exp_tone, note in self.CORPUS:
            with self.subTest(note=note, src=src):
                got = canonicalize(src)
                self.assertEqual(got.segmental, exp_seg, f"segmental[{note}]")
                self.assertEqual(got.tone, exp_tone, f"tone[{note}]")

    def test_tone_blind_grouping(self):
        # The Shape group is the segmental key: all Mandarin /ma/ tones collapse.
        keys = {canonicalize(f"ma{t}").segmental for t in ("˥", "˧˥", "˨˩˦", "˥˩", "")}
        self.assertEqual(keys, {"ma"}, "all tones of /ma/ share one Shape key")

    def test_contrastive_not_merged(self):
        self.assertNotEqual(
            canonicalize("a").segmental, canonicalize("ɑ").segmental,
            "/a/ and /ɑ/ are contrastive — canonicalization must not merge them",
        )
        self.assertNotEqual(
            canonicalize("a").segmental, canonicalize("aː").segmental,
            "length is contrastive",
        )

    def test_idempotent(self):
        # Canonicalizing a canonical string is a no-op (stable key).
        for src, *_ in self.CORPUS:
            once = canonicalize(src).segmental
            twice = canonicalize(once).segmental
            self.assertEqual(once, twice, f"idempotent[{src}]")


    def test_ascii_tone_digits_siphoned(self):
        # Sino-Tibetan/Kra-Dai Chao tones written as ASCII digits → siphoned, shape clean.
        c = canonicalize("tsa33")
        self.assertEqual(c.segmental, "tsa")
        self.assertEqual(c.tone, "33")

    def test_hygiene_rejects_non_ipa(self):
        self.assertTrue(is_clean_ipa("ma"))
        self.assertTrue(is_clean_ipa("t͡sa"))
        self.assertFalse(is_clean_ipa("*ha"), "reconstruction marker")
        self.assertFalse(is_clean_ipa("h<m>a"), "infix bracket")
        self.assertFalse(is_clean_ipa("Vwa"), "cover symbol V (ASCII uppercase)")
        self.assertFalse(is_clean_ipa("b|a"), "pipe / boundary")
        self.assertFalse(is_clean_ipa("wa+ba"), "morpheme boundary")
        # a tone-digit-labelled polysyllable canonicalizes to an ASCII-cap cover string → rejected
        self.assertFalse(is_clean_ipa(canonicalize("A31nA31dzɨ").segmental))
        self.assertFalse(is_clean_ipa("◌jɐ"), "dotted-circle placeholder (Wiktionary sign entry)")


class TestHygiene(unittest.TestCase):
    def test_spelling_letters_without_a_confirmed_ipa_reading_are_not_ipa(self):
        # ABVD only: đ is Vietnamese spelling (đường), ȥ has no reading we can confirm
        self.assertFalse(is_clean_ipa("đa"))
        self.assertFalse(is_clean_ipa("ȥa"))
        self.assertTrue(is_clean_ipa("ɲ̟a"))

    def test_the_last_non_ipa_letters_are_not_ipa(self):
        # the 12 shapes left in the heatmap's "other" row on 2026-09-29
        for bad in ("ßɪj", "Ɵe", "ǥo", "ɩŋʌ", "ᶮɈa", "–mu", "\uf182ɡo", "ɿu", "ʅa", "Ŋa"):
            with self.subTest(bad=bad):
                self.assertFalse(is_clean_ipa(bad))
        for good in ("ɓa", "ʔa", "ǀa", "ʘa", "ɕa", "ⁿba"):
            with self.subTest(good=good):
                self.assertTrue(is_clean_ipa(good))


class TestSegments(unittest.TestCase):
    """Canon keeps the segment boundaries: a syllable count depends on them."""

    def test_segmented_input_keeps_source_tokens(self):
        c = canonicalize("m ai", segmented=True)
        self.assertEqual(c.segments, ("m", "ai"))
        self.assertEqual(c.segmental, "mai", "the Shape key stays the joined string")

    def test_unsegmented_input_splits_per_grapheme(self):
        self.assertEqual(canonicalize("mai").segments, ("m", "a", "i"))
        self.assertEqual(canonicalize("kʰã˥").segments, ("kʰ", "ã"))

    def test_tie_bar_joins_graphemes_into_one_segment(self):
        self.assertEqual(canonicalize("wa͡i").segments, ("w", "ai"))
        self.assertEqual(canonicalize("t͡sa").segments, ("ts", "a"))

    def test_tone_only_tokens_are_dropped(self):
        c = canonicalize("z ə ⁵⁵", segmented=True)
        self.assertEqual((c.segments, c.tone), (("z", "ə"), "⁵⁵"))


if __name__ == "__main__":
    unittest.main()
