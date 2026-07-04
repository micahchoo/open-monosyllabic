"""Noise filtering for the WikiPron mined tier (Wiktionary non-lexeme pages)."""

import unittest

from oms.ingest_wikipron import _is_noise_word


class TestWikipronNoise(unittest.TestCase):
    def test_letter_pages_dropped(self):
        self.assertTrue(_is_noise_word("A"), "Latin letter-name page")
        self.assertTrue(_is_noise_word("USA"), "acronym")
        self.assertTrue(_is_noise_word("க"), "Brahmic single letter")

    def test_conjunct_ligature_pages_dropped(self):
        # 2026-07-04 leak: ന്ധ ("ligature of na and dha") shipped /n̪d̪ʱɐ/ as a
        # Malayalam word. Virama cluster with no vowel = letter entry, not a lexeme.
        self.assertTrue(_is_noise_word("ന്ധ"))
        self.assertTrue(_is_noise_word("്യ"), "combining-sign entry")

    def test_real_words_kept(self):
        self.assertFalse(_is_noise_word("ma"))
        self.assertFalse(_is_noise_word("ó"), "Yoruba one-letter word")
        self.assertFalse(_is_noise_word("कल"), "inherent vowel, no virama")
        self.assertFalse(_is_noise_word("क्या"), "virama + vowel sign")
        self.assertFalse(_is_noise_word("हिन्दी"), "virama + vowel signs")


if __name__ == "__main__":
    unittest.main()
