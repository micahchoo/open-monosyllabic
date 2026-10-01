"""Chance baseline for shared shapes (roadmap B1, recalibrated 2026-10-01).

For a meaning and a shape, how many language families would share it if each
language's words were shuffled among its own meanings? The shuffle keeps every
language's sounds and every language's meanings, and breaks only the link
between them. "Beyond chance" is a 5% false-discovery cut over every pair the
shuffle could make shared, so data with no real link should pass almost none.
"""

import random
import unittest

from oms.baseline import _hit_probability, _poisson_binomial, chance_bands

CONCEPTS = ["mother", "water", "fire", "eye", "stone"]


def _concepts(word_of, n_langs=10, concepts=CONCEPTS):
    """word_of(lang, concept) -> shape; one entry per language and meaning."""
    out = {c: {"entries": []} for c in concepts}
    for li in range(n_langs):
        for c in concepts:
            out[c]["entries"].append([li, word_of(li, c), "", 0, 0, 0])
    return out


FAMILIES = [f"fam{i}" for i in range(10)]


def beyond(band, fdr=0.05):
    return band[3] <= fdr


class TestExactShuffle(unittest.TestCase):

    def test_hit_probability_matches_counting(self):
        # 4 words, the shape on 1 of them, the meaning on 1: 1 in 4
        self.assertAlmostEqual(_hit_probability(4, 1, 1), 0.25)
        # the meaning twice: 1 - (3/4 * 2/3) = 1/2
        self.assertAlmostEqual(_hit_probability(4, 2, 1), 0.5)
        self.assertEqual(_hit_probability(3, 1, 3), 1.0)

    def test_poisson_binomial_sums_to_one(self):
        d = _poisson_binomial([0.2, 0.5, 0.9])
        self.assertAlmostEqual(sum(d), 1.0)
        self.assertAlmostEqual(d[3], 0.2 * 0.5 * 0.9)


class TestChanceBands(unittest.TestCase):

    def test_a_real_sound_meaning_link_is_beyond_chance(self):
        # every language says /ma/ for 'mother' and something unique elsewhere
        cs = _concepts(lambda li, c: "ma" if c == "mother" else f"{c}{li}")
        bands, summary = chance_bands(cs, FAMILIES)
        obs, lo, hi, q = bands["mother"]["ma"]
        self.assertEqual(obs, 10)
        self.assertLess(hi, obs)
        self.assertTrue(beyond(bands["mother"]["ma"]))
        self.assertEqual(summary["beyond"], 1)

    def test_a_shape_a_language_uses_everywhere_is_not_beyond_chance(self):
        # every language says /ta/ for every meaning: shuffling changes nothing
        cs = _concepts(lambda li, c: "ta")
        obs, lo, hi, q = chance_bands(cs, FAMILIES)[0]["mother"]["ta"]
        self.assertEqual(obs, 10)
        self.assertEqual(hi, 10)
        self.assertFalse(beyond((obs, lo, hi, q)))

    def test_only_pairs_shared_by_two_families_are_tested(self):
        cs = _concepts(lambda li, c: "ma" if c == "mother" else f"{c}{li}")
        self.assertNotIn("water0", chance_bands(cs, FAMILIES)[0].get("water", {}))

    def test_pairs_too_few_families_could_share_get_no_verdict(self):
        # only 4 families: none could reach the 5 a verdict needs
        cs = _concepts(lambda li, c: "ma" if c == "mother" else f"{c}{li}", n_langs=4)
        bands, summary = chance_bands(cs, FAMILIES[:4])
        self.assertEqual(summary["tested"], 0)

    def test_one_family_counts_once(self):
        cs = _concepts(lambda li, c: "ma" if c == "mother" else f"{c}{li}")
        obs, *_ = chance_bands(cs, ["same"] * 5 + FAMILIES[5:])[0]["mother"]["ma"]
        self.assertEqual(obs, 6)

    def test_no_link_passes_almost_nothing(self):
        # 60 families of one language, 40 meanings each, shapes drawn from a
        # small pool so many pairs are shared by accident — and none by design.
        # The pre-2026-10-01 procedure passed rare pairs two families shared
        # by luck; at a 5% FDR the expected count here is ~0.
        rng = random.Random(7)
        pool = [f"{c}{v}" for c in "ptkmnsl" for v in "aeiou"]
        concepts = [f"c{i}" for i in range(40)]
        cs = _concepts(lambda li, c: rng.choice(pool), n_langs=60, concepts=concepts)
        bands, summary = chance_bands(cs, [f"f{i}" for i in range(60)])
        self.assertGreater(summary["tested"], 100)
        self.assertLessEqual(summary["beyond"], 2)


if __name__ == "__main__":
    unittest.main()
