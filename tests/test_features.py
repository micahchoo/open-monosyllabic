"""Onset classes (roadmap E1): a valid IPA onset never lands in "other".

Before 2026-09-29, 588 shapes sat in the heatmap's "other" row, nearly all of
them valid IPA the small character sets did not know: prenasalized and
pre-glottalized stops, the alveolo-palatal series, lateral fricatives,
approximants. "other" is kept for letters that are not IPA at all.
"""

import unittest

from oms.features import onset_class


class TestOnsetClass(unittest.TestCase):

    CORPUS = [
        # a leading modifier letter marks the consonant; the consonant decides
        ("ⁿba", "stop", "prenasalized stop"),
        ("ᵐba", "stop", "prenasalized stop, labial"),
        ("ᵑɡa", "stop", "prenasalized velar"),
        ("ᶯɖa", "stop", "prenasalized retroflex"),
        ("ʰka", "stop", "pre-aspirated stop"),
        ("ᶮje", "glide", "prenasalized palatal glide"),
        ("ˀda", "stop", "pre-glottalized stop"),
        # a glottal-stop letter before the vowel is the onset itself
        ("ˀa", "stop", "glottal onset written as a modifier"),
        # the alveolo-palatal series and lateral fricatives are fricatives
        ("ɕa", "fricative", "alveolo-palatal fricative"),
        ("ʑa", "fricative", "voiced alveolo-palatal fricative"),
        ("ɬa", "fricative", "lateral fricative"),
        ("ɮi", "fricative", "voiced lateral fricative"),
        ("ʍɛ", "fricative", "voiceless labial-velar fricative"),
        # ligature affricates
        ("ʨaː", "affricate", "alveolo-palatal affricate ligature"),
        ("ʥi", "affricate", "voiced alveolo-palatal affricate ligature"),
        # approximants and flaps
        ("ʋa", "glide", "labiodental approximant"),
        ("ɹa", "liquid", "alveolar approximant"),
        ("ɻe", "liquid", "retroflex approximant"),
        ("ɺa", "liquid", "lateral flap"),
        ("ɲ̟a", "nasal", "Sinological ȵ after canon"),
        ("c̟a", "stop", "Sinological ȶ after canon"),
        # unchanged cases
        ("ma", "nasal", "plain nasal"),
        ("a", "none", "vowel-initial"),
        ("ɡa", "stop", "IPA script g"),
        # not IPA: still "other"
        ("ßa", "other", "German eszett is not IPA"),
    ]

    def test_corpus(self):
        for form, expected, note in self.CORPUS:
            with self.subTest(note=note, form=form):
                self.assertEqual(onset_class(form), expected)


if __name__ == "__main__":
    unittest.main()
