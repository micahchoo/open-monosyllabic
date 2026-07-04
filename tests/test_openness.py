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
        # VV diphthong nucleus (source segmented as two vowels) — open, high
        ("ai", True, HIGH, False, "vowel+vowel diphthong — open, uncontested"),
        ("nau", True, HIGH, False, "CVV diphthong — open, uncontested"),
        # 3+ vowels: triphthong-vs-hiatus contested — open but medium/review
        ("aua", True, MEDIUM, True, "3-vowel sequence — contested (triphthong vs hiatus)"),
        # V+glide — the contested case: ADR-0001 rules OPEN but medium confidence
        ("baj", True, MEDIUM, True, "bye /baj/ — final glide → diphthong, contested"),
        ("naw", True, MEDIUM, True, "now /naw/ — final glide → diphthong, contested"),
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
        self.assertTrue(classify_openness("ai").is_open)
        self.assertTrue(classify_openness("baj").is_open)

    def test_syllabic_consonants_are_out(self):
        # ADR-0001: vowel-less syllabic consonants are excluded.
        self.assertFalse(classify_openness("m̩").is_open)


if __name__ == "__main__":
    unittest.main()
