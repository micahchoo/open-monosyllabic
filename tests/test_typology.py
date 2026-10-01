"""Typology joins (WALS 12A, PHOIBLE) and Concepticon gloss linking."""

import csv
import tempfile
import unittest
from pathlib import Path

from oms import concepticon
from oms.typology import phoible_inventories, segment_classes, wals_syllable_structure


def _csv(path: Path, header: list[str], rows: list[list], delimiter=","):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=delimiter)
        w.writerow(header)
        w.writerows(rows)


class TestWals(unittest.TestCase):
    def test_12a_by_glottocode_and_conflicts_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _csv(root / "cldf/languages.csv", ["ID", "Glottocode"],
                 [["haw", "hawa1245"], ["eng", "stan1293"], ["x1", "dupl1234"], ["x2", "dupl1234"]])
            _csv(root / "cldf/values.csv", ["ID", "Language_ID", "Parameter_ID", "Value"],
                 [["1", "haw", "12A", "1"], ["2", "eng", "12A", "3"], ["3", "haw", "13A", "2"],
                  ["4", "x1", "12A", "1"], ["5", "x2", "12A", "2"]])
            got = wals_syllable_structure(root)
        self.assertEqual(got, {"hawa1245": "simple", "stan1293": "complex"})


class TestPhoible(unittest.TestCase):
    def test_segments_classed_like_forms(self):
        self.assertEqual(segment_classes("m", "consonant"), ("nasal", None))
        self.assertEqual(segment_classes("ɓ", "consonant"), ("implosive", None))
        self.assertEqual(segment_classes("ɨ", "vowel"), (None, "ə"))
        self.assertEqual(segment_classes("aɪ", "vowel"), (None, "diphthong"))
        self.assertEqual(segment_classes("˥", "tone"), (None, None))

    def test_inventories_union(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _csv(root / "cldf/parameters.csv", ["ID", "SegmentClass"],
                 [["M", "consonant"], ["A", "vowel"], ["S", "consonant"], ["I", "vowel"]])
            _csv(root / "cldf/values.csv", ["ID", "Language_ID", "Parameter_ID", "Value", "Inventory_ID"],
                 [["1", "aaaa1111", "M", "m", "1"], ["2", "aaaa1111", "A", "a", "1"],
                  ["3", "aaaa1111", "S", "s", "2"], ["4", "aaaa1111", "I", "i", "2"],
                  ["5", "bbbb2222", "M", "m", "3"]])   # no vowel: no usable inventory
            got = phoible_inventories(root)
        self.assertEqual(got, {"aaaa1111": {"onsets": ["fricative", "nasal"], "nuclei": ["a", "i"]}})


class TestConcepticonLink(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "concepticon.tsv"
        _csv(path, ["ID", "GLOSS", "ONTOLOGICAL_CATEGORY", "REPLACEMENT_ID"],
             [["948", "WATER", "Person/Thing", ""], ["1449", "GO", "Action/Process", ""],
              ["1258", "NAIL", "Person/Thing", ""], ["2112", "NAIL (TOOL)", "Person/Thing", ""],
              ["1", "SUN", "Person/Thing", ""], ["9", "OLD", "Property", "10"]], delimiter="\t")
        self.table = concepticon.load(path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_only_unambiguous_current_glosses(self):
        self.assertIn("water", self.table)
        self.assertNotIn("nail", self.table, "two senses share the head word")
        self.assertNotIn("old", self.table, "replaced concept")

    def test_links_only_into_meanings_the_catalog_has(self):
        ds = [{"entries": [
            {"gloss": "water", "concepticon_id": 948},                # a word list linked it
            {"gloss": "Water", "concepticon_id": None},                # -> linked
            {"gloss": "to go", "concepticon_id": None},                # GO not in catalog -> stays
            {"gloss": "nail", "concepticon_id": None},                 # ambiguous -> stays
            {"gloss": "sun", "concepticon_id": None},                  # SUN not in catalog -> stays
            {"gloss": "to water", "concepticon_id": None},             # a verb is not WATER -> stays
            {"gloss": "the water", "concepticon_id": None},            # -> linked
        ]}]
        self.assertEqual(concepticon.link(ds, self.table), 2)
        self.assertIsNone(ds[0]["entries"][5]["concepticon_id"])
        e = ds[0]["entries"][1]
        self.assertEqual((e["concepticon_id"], e["concepticon_gloss"], e["linked_by"]), (948, "WATER", "gloss"))
        self.assertIsNone(ds[0]["entries"][2]["concepticon_id"])
        self.assertIsNone(ds[0]["entries"][3]["concepticon_id"])


if __name__ == "__main__":
    unittest.main()
