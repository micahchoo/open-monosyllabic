"""Regressions for the 2026-10-01 robustness audit (see HANDOFF.md)."""

import csv
import tempfile
import unittest
from pathlib import Path

from oms.canon import canonicalize, is_clean_ipa
from oms.features import onset_class
from oms.ingest_cldf import _ipa
from oms.openness import classify_openness
from oms.pipeline import run_datasets
from oms.scaleout import _glottolog_families


class TestCanon(unittest.TestCase):
    def test_ascii_length_is_length_not_a_coda(self):
        # graphemes() split "ma:" before ":" became ː: 802 forms excluded as closed
        c = canonicalize("ma:")
        self.assertEqual(c.segments, ("m", "aː"))
        self.assertTrue(classify_openness(c.segments).is_open)
        self.assertEqual(canonicalize("tʰi·").segmental, "tʰiː")

    def test_precomposed_affricates_fold(self):
        self.assertEqual(canonicalize("ʥi").segmental, canonicalize("dʑ i", segmented=True).segmental)
        self.assertEqual(canonicalize("ʧa").segments, ("tʃ", "a"))

    def test_one_segment_nasal_stop_is_prenasalized(self):
        self.assertEqual(canonicalize("mb a", segmented=True).segmental, "ᵐba")
        self.assertEqual(canonicalize("n d a", segmented=True).segmental, "nda", "two segments stay a cluster")

    def test_punctuation_is_not_ipa(self):
        for s in ("n-ma", "ma,", "ma’"):
            self.assertFalse(is_clean_ipa(canonicalize(s).segmental), s)


class TestFeatures(unittest.TestCase):
    def test_affricate_segment_is_an_affricate(self):
        self.assertEqual(onset_class("tʃa", ("tʃ", "a")), "affricate")
        self.assertEqual(onset_class("tsʰi", ("tsʰ", "i")), "affricate")
        self.assertEqual(onset_class("tʃa"), "stop", "without segments the key reads t + ʃ")
        self.assertEqual(onset_class("ᵐba", ("ᵐb", "a")), "stop")


class TestIngest(unittest.TestCase):
    def test_clitic_and_affix_marks_rejected(self):
        for raw in ("+lɔˀ", "='u", "ka-", "-ka"):
            self.assertEqual(_ipa({"Form": raw, "Segments": ""}), "", raw)


class TestDisagreement(unittest.TestCase):
    def test_same_word_open_in_one_source_closed_in_another_is_under_review(self):
        # ABVD maa (two vowels: excluded) vs Walworth maː (open), one word
        ds = [{"sources": [{"id": "a", "tier": "curated", "license": "CC-BY-4.0"},
                           {"id": "b", "tier": "curated", "license": "CC-BY-4.0"}],
               "languages": [{"glottocode": "xxxx1234", "name": "X", "macroarea": "", "latitude": None,
                              "longitude": None, "doc_status": "moderate", "prosodic_type": "unknown"}],
               "entries": [
                   {"glottocode": "xxxx1234", "ipa": "m a a", "gloss": "sea", "concepticon_id": 1, "source": "a", "segmented": True},
                   {"glottocode": "xxxx1234", "ipa": "m aː", "gloss": "sea", "concepticon_id": 1, "source": "b", "segmented": True},
                   {"glottocode": "xxxx1234", "ipa": "t a", "gloss": "one", "concepticon_id": 2, "source": "a", "segmented": True},
                   {"glottocode": "xxxx1234", "ipa": "t a ŋ", "gloss": "one", "concepticon_id": 2, "source": "b", "segmented": True},
               ]}]
        out = run_datasets(ds)
        forms = {f.segmental: f for f in out["forms"]}
        self.assertTrue(forms["maː"].under_review)
        self.assertFalse(forms["ta"].under_review, "taŋ is another word, not the same one spelled differently")
        self.assertEqual(out["disagreements"], 1)


class TestGlottologFamilies(unittest.TestCase):
    def test_family_from_family_id_and_isolates_alone(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sources/glottolog-cldf/cldf/languages.csv"
            path.parent.mkdir(parents=True)
            with path.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["ID", "Name", "Level", "Family_ID"])
                w.writerows([["aust1307", "Austronesian", "family", ""], ["maor1246", "Maori", "language", "aust1307"],
                             ["abun1252", "Abun", "language", ""], ["mpur1239", "Mpur", "language", ""]])
            fam = _glottolog_families(Path(d))
        self.assertEqual(fam, {"maor1246": "Austronesian", "abun1252": "Abun", "mpur1239": "Mpur"})


if __name__ == "__main__":
    unittest.main()
