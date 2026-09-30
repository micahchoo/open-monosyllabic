"""Chance baseline for shared shapes (roadmap B1).

For a meaning and a shape, how many language families would share it if each
language's words were shuffled among its own meanings? The shuffle keeps every
language's sounds and every language's meanings, and breaks only the link
between them. A shape shared beyond that band is a fact worth a look; one
inside it is what chance alone gives.
"""

import unittest

from oms.baseline import chance_bands

CONCEPTS = ["mother", "water", "fire", "eye", "stone"]


def _concepts(word_of):
    """word_of(lang, concept) -> shape; ten languages, each its own family."""
    out = {c: {"entries": []} for c in CONCEPTS}
    for li in range(10):
        for c in CONCEPTS:
            out[c]["entries"].append([li, word_of(li, c), "", 0, 0, 0])
    return out


FAMILIES = [f"fam{i}" for i in range(10)]


class TestChanceBands(unittest.TestCase):

    def test_a_real_sound_meaning_link_is_beyond_chance(self):
        # every language says /ma/ for 'mother' and something unique elsewhere
        cs = _concepts(lambda li, c: "ma" if c == "mother" else f"{c}{li}")
        obs, lo, hi, top = chance_bands(cs, FAMILIES)["mother"]["ma"]
        self.assertEqual(obs, 10)
        self.assertLess(top, obs, "beyond every shuffle, not only the 95th percentile")

    def test_a_shape_a_language_uses_everywhere_is_not_beyond_chance(self):
        # every language says /ta/ for every meaning: shuffling changes nothing
        cs = _concepts(lambda li, c: "ta")
        obs, lo, hi, top = chance_bands(cs, FAMILIES)["mother"]["ta"]
        self.assertEqual(obs, 10)
        self.assertGreaterEqual(top, obs)

    def test_only_pairs_shared_by_two_families_are_tested(self):
        cs = _concepts(lambda li, c: "ma" if c == "mother" else f"{c}{li}")
        self.assertNotIn("water0", chance_bands(cs, FAMILIES).get("water", {}))

    def test_one_family_counts_once(self):
        cs = _concepts(lambda li, c: "ma" if c == "mother" else f"{c}{li}")
        obs, *_ = chance_bands(cs, ["same"] * 5 + FAMILIES[5:])["mother"]["ma"]
        self.assertEqual(obs, 6)

    def test_the_same_seed_gives_the_same_bands(self):
        cs = _concepts(lambda li, c: "ma" if c in ("mother", "water") else f"{c}{li}")
        self.assertEqual(chance_bands(cs, FAMILIES, seed=3), chance_bands(cs, FAMILIES, seed=3))


if __name__ == "__main__":
    unittest.main()
