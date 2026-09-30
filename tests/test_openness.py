"""The openness corpus (ADR-0001; IMPLEMENTATION-STRATEGY §4-5).

form -> (is_open, confidence, contested). The corpus is the enumeration; each
row is a mechanical case except the diphthong-vs-glide rows, which encode the
ADR-0001 contested ruling (open, but medium confidence).
"""

import unittest

from oms.openness import classify_openness, HIGH, MEDIUM


class TestOpennessCorpus(unittest.TestCase):

    # (form, is_open, confidence, contested, note)
    CORPUS = [
        # clear opens — monophthong nucleus, no coda
        ("ma", True, HIGH, False, "CV open"),
        ("to", True, HIGH, False, "CV open"),
        ("a", True, HIGH, False, "bare V open"),
        ("ɓa", True, HIGH, False, "implosive-onset CV open"),
        ("sta", True, HIGH, False, "CCV cluster onset, open"),
        ("kwa", True, HIGH, False, "onset glide /w/ before nucleus — open"),
        ("ja", True, HIGH, False, "onset glide /j/ before nucleus — open"),
        ("mã", True, HIGH, False, "nasal vowel nucleus — open"),
        ("maː", True, HIGH, False, "long vowel nucleus — open"),
        # A diphthong is ONE nucleus only when the source says so: one segment
        # (CLTS token "ai"), a tie bar, or a non-syllabic mark. Resolved by the
        # source's own transcription -> medium, not pending review.
        (["ai"], True, MEDIUM, False, "one-segment diphthong — open, source-resolved"),
        (["n", "au"], True, MEDIUM, False, "CV diphthong segment — open, source-resolved"),
        ("na͡u", True, MEDIUM, False, "tie bar joins the vowels into one segment"),
        # Two vowel SEGMENTS are two nuclei: hiatus, two syllables (ru.a).
        ("ai", False, HIGH, False, "unmarked vowel pair — two segments, two syllables"),
        (["r", "u", "a"], False, HIGH, False, "Polynesian rua 'two' — ru.a, excluded"),
        (["m", "a", "i"], False, HIGH, False, "source split the vowels — excluded"),
        ("aua", False, HIGH, False, "three vowel segments — excluded"),
        # 3+ vowels inside ONE segment: triphthong the source asserts — contested
        (["aua"], True, MEDIUM, True, "one-segment triphthong — contested"),
        # a non-syllabic vowel after the nucleus is a glide (Wiktionary aɪ̯)
        ("aɪ̯", True, MEDIUM, True, "non-syllabic mark = offglide, like /aj/"),
        # V+glide — the contested case: ADR-0001 rules OPEN but medium confidence
        ("baj", True, MEDIUM, True, "bye /baj/ — final glide → diphthong, contested"),
        ("naw", True, MEDIUM, True, "now /naw/ — final glide → diphthong, contested"),
        # A nasal written as its OWN segment before a consonant is ambiguous: a
        # syllabic nasal (Bantu n̩.ku, two syllables), a pre-initial (Tibeto-Burman
        # m.dza, one syllable) or an unmerged prenasalized stop. Segmentation does
        # not settle it (measured 2026-09-29), so the form stays, contested.
        (["m", "b", "a"], True, MEDIUM, True, "separate nasal before a stop — contested"),
        (["n", "k", "u"], True, MEDIUM, True, "Bantu n̩.ku? — contested, pending review"),
        (["m", "dz", "a"], True, MEDIUM, True, "Tibeto-Burman pre-initial — contested, not excluded"),
        (["n", "n", "j", "a"], True, MEDIUM, True, "separate nasal before a nasal — contested"),
        (["mb", "a"], True, HIGH, False, "prenasalized stop, one segment — open"),
        ("ⁿba", True, HIGH, False, "superscript nasal marks prenasalization — open"),
        (["m", "w", "a"], True, HIGH, False, "nasal before a glide is an ordinary onset — open"),
        # closed — coda consonant → excluded
        ("mat", False, HIGH, False, "CVC coda — closed, excluded"),
        ("man", False, HIGH, False, "CVC nasal coda — closed, excluded"),
        ("staːk", False, HIGH, False, "long vowel + coda — closed, excluded"),
        # no vowel nucleus — excluded (syllabic consonant)
        ("m̩", False, HIGH, False, "syllabic nasal, no vowel — excluded"),
        ("s", False, HIGH, False, "bare consonant — excluded"),
        # more than one syllable — excluded (ADR-0001: exactly one syllable)
        ("kissa", False, HIGH, False, "disyllable (consonant between vowels) — excluded"),
        ("maja", False, HIGH, False, "disyllable (glide between vowels) — excluded"),
        ("ɔmɔ", False, HIGH, False, "disyllable Yoruba /ɔmɔ/ 'child' — excluded"),
    ]

    def test_corpus(self):
        for form, is_open, conf, contested, note in self.CORPUS:
            with self.subTest(note=note, form=form):
                o = classify_openness(form)
                self.assertEqual(o.is_open, is_open, f"is_open[{note}]: {o.reason}")
                self.assertEqual(o.confidence, conf, f"confidence[{note}]")
                self.assertEqual(o.contested, contested, f"contested[{note}]")

    def test_diphthongs_are_in(self):
        # ADR-0001: diphthongs count as open (inclusive posture).
        self.assertTrue(classify_openness(["ai"]).is_open)
        self.assertTrue(classify_openness("baj").is_open)

    def test_syllabic_consonants_are_out(self):
        # ADR-0001: vowel-less syllabic consonants are excluded.
        self.assertFalse(classify_openness("m̩").is_open)

    def test_syllabic_nucleus_beside_vowel_is_out(self):
        # 2026-07-04 leak: the syllabicity mark folded into its consonant token, so
        # kr̩ba (= kr̩ + ba, two syllables) shipped as an "open monophthong".
        self.assertFalse(classify_openness("kr̩ba").is_open)
        self.assertFalse(classify_openness("r̩kʂi").is_open)

    def test_voiceless_ring_is_not_syllabicity(self):
        # U+0325 (voiceless) must not trip the syllabic-nucleus exclusion.
        self.assertTrue(classify_openness("l̥i").is_open)


if __name__ == "__main__":
    unittest.main()
