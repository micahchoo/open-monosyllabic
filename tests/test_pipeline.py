"""Pipeline + bake invariants (IMPLEMENTATION-STRATEGY §9/§10).

Locks the load-bearing behaviours: cross-language Shape grouping, tone-blind
Form collapse, the no-data (zero-Forms) language, and the generated-tier honesty
rule (low confidence + under_review).
"""

import unittest
from pathlib import Path

from oms.pipeline import run
from oms.bake import bake

ROOT = Path(__file__).resolve().parent.parent


class TestPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.out = run(ROOT / "seed" / "seed.json")
        cls.forms = {f.key: f for f in cls.out["forms"]}

    def test_cross_language_shape_grouping(self):
        # /ma/ is a Shape shared across several languages (the flagship feature).
        langs = sorted(f.glottocode for f in self.out["forms"] if f.segmental == "ma")
        self.assertGreaterEqual(len(langs), 4, "/ma/ should appear in multiple languages")
        self.assertIn("stan1290", langs)
        self.assertIn("yoru1245", langs)

    def test_tone_blind_form_collapse(self):
        # Mandarin ma˥ 'mother' and ma˨˩˦ 'horse' collapse to ONE Form /ma/ with 2 tones.
        f = self.forms["stan1290|ma"]
        self.assertEqual(f.segmental, "ma")
        self.assertGreaterEqual(len(f.tones), 2, "both Mandarin tones recorded on one Form")
        self.assertGreaterEqual(len(f.words), 2, "mother and horse are distinct Words on one Form")

    def test_zero_form_language_is_no_data(self):
        # Nuxalk's consonant-only entries yield NO open monosyllables -> ships as no-data.
        self.assertIn("bell1243", self.out["zero_form_languages"])
        self.assertFalse(any(f.glottocode == "bell1243" for f in self.out["forms"]))

    def test_excluded_cover_closed_vowelless_and_polysyllabic(self):
        excl = {(x["glottocode"], x["ipa"]) for x in self.out["excluded"]}
        # Nuxalk consonant-heavy words: closed / vowel-less
        self.assertIn(("bell1243", "pʰtʰ"), excl)   # no vowel
        self.assertIn(("bell1243", "kʷas"), excl)    # coda /s/ -> closed
        # polysyllables excluded by the one-syllable rule
        self.assertIn(("finn1318", "kissa"), excl)   # disyllable
        self.assertIn(("yoru1245", "ɔmɔ"), excl)     # disyllable
        # Finnish keeps its genuine open monosyllables
        self.assertTrue(any(f.glottocode == "finn1318" and f.segmental == "puː"
                            for f in self.out["forms"]), "puu 'tree' survives")

    def test_generated_tier_honesty_rule(self):
        # Fijian /ma/ came only from Epitran (generated) -> low confidence + under_review.
        f = self.forms["fiji1243|ma"]
        self.assertEqual(f.tier, "generated")
        self.assertEqual(f.classification_confidence, "low")
        self.assertTrue(f.under_review, "generated-tier forms ship under_review (never bare fact)")

    def test_multi_source_ratchets_tier(self):
        # A form seen from a curated source is curated-tier regardless of order.
        f = self.forms["stan1290|ma"]
        self.assertEqual(f.tier, "curated")

    def test_bake_core_index(self):
        core, forms_detail = bake(self.out)
        self.assertEqual(core["meta"]["scheme_version"], "oms-canon-v1")
        # every posting is the packed 4-tuple
        for shape, posts in core["postings"].items():
            for p in posts:
                self.assertEqual(len(p), 4, "posting = [langIdx, tierRank, ccRank, under_review]")
        # /ma/ is in the index across languages
        self.assertGreaterEqual(len(core["postings"]["ma"]), 4)


if __name__ == "__main__":
    unittest.main()
