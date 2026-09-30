"""Pipeline + bake invariants (IMPLEMENTATION-STRATEGY §9/§10).

Locks the load-bearing behaviours: cross-language Shape grouping, tone-blind
Form collapse, the no-data (zero-Forms) language, and the generated-tier honesty
rule (low confidence + under_review).
"""

import unittest
from pathlib import Path

from oms.pipeline import run, run_datasets
from oms.bake import bake, concept_labels

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

    def test_examined_counts_every_judged_word(self):
        # A language's yield is only readable against how many words were looked
        # at: Nuxalk has no open monosyllables among the words examined — that is
        # "0 of N", never a claim about the whole language.
        ex = self.out["examined"]
        self.assertGreater(ex["bell1243"], 0)
        self.assertIn("bell1243", self.out["zero_form_languages"])
        for g in self.out["languages"]:
            n = sum(1 for f in self.out["forms"] if f.glottocode == g)
            self.assertGreaterEqual(ex.get(g, 0), n, g)

    def test_bake_carries_family_and_examined(self):
        core, _ = bake(self.out)
        for L in core["languages"]:
            self.assertIn("family", L)
            self.assertGreaterEqual(L["examined"], L["form_count"])

    def test_an_ingest_exclusion_is_counted_and_never_examined(self):
        src = [{"id": "s", "tier": "curated", "license": "CC0-1.0"}]
        lang = [{"glottocode": "yabe1254", "name": "Yabem", "macroarea": "Papunesia", "latitude": None,
                 "longitude": None, "doc_status": "moderate", "prosodic_type": "unknown"}]
        entries = [{"glottocode": "yabe1254", "ipa": "bê", "gloss": None, "source": "s",
                    "exclude": "spelling mark with no fixed IPA reading"},
                   {"glottocode": "yabe1254", "ipa": "la", "gloss": None, "source": "s"}]
        out = run_datasets([{"sources": src, "languages": lang, "entries": entries}])
        self.assertEqual(out["examined"]["yabe1254"], 1)
        self.assertEqual([f.segmental for f in out["forms"]], ["la"])
        self.assertIn("no fixed IPA reading", out["excluded"][0]["reason"])


class TestSampleKind(unittest.TestCase):
    """A rate means different things from a 200-word list and a 30,000-word
    dictionary (roadmap B2), so each language records which kinds of source
    its examined words came from."""

    def _run(self, *kinds_per_entry):
        srcs = [{"id": "list", "tier": "curated", "license": "CC0-1.0"},
                {"id": "dict", "tier": "mined", "license": "CC0-1.0", "kind": "dictionary"}]
        lang = [{"glottocode": "yoru1245", "name": "Yoruba", "macroarea": "Africa", "latitude": None,
                 "longitude": None, "doc_status": "moderate", "prosodic_type": "unknown"}]
        entries = [{"glottocode": "yoru1245", "ipa": ipa, "gloss": None, "source": src}
                   for src, ipa in kinds_per_entry]
        out = run_datasets([{"sources": srcs, "languages": lang, "entries": entries}])
        core, _ = bake(out)
        return core["languages"][0]["sample"]

    def test_a_source_is_a_word_list_unless_it_says_otherwise(self):
        self.assertEqual(self._run(("list", "ba")), "word list")

    def test_a_dictionary_source_makes_a_dictionary_sample(self):
        self.assertEqual(self._run(("dict", "ba"), ("dict", "bi")), "dictionary")

    def test_both_kinds_make_a_mixed_sample(self):
        self.assertEqual(self._run(("list", "ba"), ("dict", "bi")), "mixed")


class TestFamilyMerge(unittest.TestCase):
    """A dataset without families (WikiPron) must not blank the family another
    dataset supplies for the same language, in either order."""

    SRC = [{"id": "s", "tier": "curated", "license": "CC0-1.0"}]
    LANG = {"glottocode": "yoru1245", "name": "Yoruba", "macroarea": "Africa",
            "latitude": 7.4, "longitude": 3.9, "doc_status": "moderate", "prosodic_type": "unknown"}

    def _run(self, first_family, second_family):
        ds = [{"sources": self.SRC, "entries": [],
               "languages": [dict(self.LANG, **({"family": f} if f is not None else {}))]}
              for f in (first_family, second_family)]
        return run_datasets(ds)["languages"]["yoru1245"].family

    def test_family_fills_from_a_later_dataset(self):
        self.assertEqual(self._run(None, "Atlantic-Congo"), "Atlantic-Congo")

    def test_family_survives_a_later_dataset_without_one(self):
        self.assertEqual(self._run("Atlantic-Congo", ""), "Atlantic-Congo")


class TestConceptLabels(unittest.TestCase):
    """No two meanings share a label (roadmap D4). A linked concept reads as its
    sources call it; where two concepts would read alike, the Concepticon gloss
    tells them apart. Unlinked glosses are never merged into a concept."""

    def c(self, cid, cg, **votes):
        return {"concepticon_id": cid, "concepticon_gloss": cg, "votes": votes}

    def test_label_is_the_commonest_source_gloss(self):
        self.assertEqual(concept_labels({"1209": self.c(1209, "I", I=5, i=1)}), {"1209": "I"})

    def test_a_different_concept_under_the_same_word_reads_as_itself(self):
        # 22 languages' IRRIGATE was listed as 'water' beside WATER
        got = concept_labels({"948": self.c(948, "WATER", water=30), "3078": self.c(3078, "IRRIGATE", water=22)})
        self.assertEqual(got, {"948": "water", "3078": "irrigate"})

    def test_no_winner_means_every_one_is_qualified(self):
        got = concept_labels({"658": self.c(658, "RAIN (PRECIPITATION)", rain=19),
                              "1253": self.c(1253, "RAIN (RAINING)", rain=4),
                              "2108": self.c(2108, "RAINING OR RAIN", RAIN=4)})
        self.assertEqual(got, {"658": "rain (precipitation)", "1253": "rain (raining)", "2108": "raining or rain"})

    def test_an_unlinked_gloss_is_marked_not_merged(self):
        got = concept_labels({"1498": self.c(1498, "TWO", two=230), "g-x": self.c(None, None, two=2)})
        self.assertEqual(got, {"1498": "two", "g-x": "two (unlinked)"})

    def test_the_unlinked_gloss_is_the_one_marked(self):
        # COME's sources mostly write "to come"; an unlinked "to come" and an
        # unlinked "come" must not push the linked concept off its own word
        got = concept_labels({"1446": self.c(1446, "COME", **{"to come": 197, "come": 137}),
                              "g-a": self.c(None, None, **{"to come": 3}),
                              "g-b": self.c(None, None, come=4)})
        self.assertEqual(got, {"1446": "to come", "g-a": "to come (unlinked)", "g-b": "come"})

    def test_a_concepticon_word_is_written_its_way(self):
        # ABVD writes "Two"; the concept is TWO, so it reads "two" — and "I" stays "I"
        got = concept_labels({"1498": self.c(1498, "TWO", Two=155, two=117),
                              "1209": self.c(1209, "I", I=5, i=1)})
        self.assertEqual(got, {"1498": "two", "1209": "I"})

    def test_case_is_not_a_difference(self):
        got = concept_labels({"g-a": self.c(None, None, One=1), "1493": self.c(1493, "ONE", one=247)})
        self.assertEqual(len(set(got.values())), 2)
        self.assertEqual(got["1493"], "one")


if __name__ == "__main__":
    unittest.main()
