"""Phase 5 scale-out: CLDF ingestion adapter + dataset merge + chunked bake."""

import json
import unittest
from pathlib import Path

from oms.ingest_cldf import load as load_cldf, clearance_ok
from oms.pipeline import run_datasets
from oms.bake import write_build, tripwires
from oms.scaleout import collect

ROOT = Path(__file__).resolve().parent.parent


class TestScaleOut(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.seed = json.loads((ROOT / "seed" / "seed.json").read_text(encoding="utf-8"))
        cls.cldf = load_cldf(ROOT / "seed" / "cldf_demo")
        cls.out = run_datasets([cls.seed, cls.cldf])
        cls.bykey = {f.key: f for f in cls.out["forms"]}

    def test_cldf_adapter_reads_metadata_and_forms(self):
        self.assertEqual(self.cldf["sources"][0]["license"], "CC-BY-4.0")
        self.assertIn("thai1261", [l["glottocode"] for l in self.cldf["languages"]])
        self.assertTrue(any(e["ipa"] == "m aː ˧" and e["segmented"] for e in self.cldf["entries"]))

    def test_licence_clearance_gate(self):
        self.assertTrue(clearance_ok("CC-BY-SA-4.0"))
        self.assertTrue(clearance_ok("CC-BY-NC-4.0"))     # NC now allowed (user decision 2026-07-04)
        self.assertTrue(clearance_ok("CC-BY-NC-SA-4.0"))
        self.assertFalse(clearance_ok("CC-BY-ND-4.0"))    # ND blocked — forbids derivatives
        self.assertFalse(clearance_ok("CC-BY-NC-ND-4.0")) # NC-ND blocked
        self.assertFalse(clearance_ok(""))                 # unset blocked

    def test_merge_grows_coverage(self):
        langs = {l for l in self.out["languages"]}
        self.assertGreaterEqual(len(langs), 10, "seed + CLDF = 10 languages")
        self.assertIn("thai1261", {f.glottocode for f in self.out["forms"]})

    def test_source_segmentation_decides_the_syllable_count(self):
        # The demo writes Maori wai as "w a i": two vowel segments, two syllables.
        # Hawaiian wai in the seed is marked one diphthong (wa͡i) and stays.
        wai = {f.glottocode for f in self.out["forms"] if f.segmental == "wai"}
        self.assertNotIn("maor1246", wai)
        self.assertIn("hawa1245", wai)
        self.assertIn(("maor1246", "w a i"), {(x["glottocode"], x["ipa"]) for x in self.out["excluded"]})

    def test_tone_blind_across_datasets(self):
        # Thai /maː˧/ is a long-vowel shape /maː/, distinct from the short /ma/,
        # and its tone is siphoned off (tone-blind key).
        f = self.bykey["thai1261|maː"]
        self.assertEqual(f.segmental, "maː")
        self.assertTrue(f.tones, "Thai tone recorded on the Form")
        self.assertNotIn("thai1261|ma", self.bykey, "long vowel is a different shape than short")

    def test_chunked_bake_and_tripwires(self):
        # bake into a temp dir — writing into the repo root leaves stray build
        # dirs behind (a real 'data-scaled/' orphan shipped before this fix)
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            self._bake_and_assert(Path(td) / self.out["scheme_version"])

    def _bake_and_assert(self, outdir):
        core, n_chunks, warns = write_build(self.out, outdir, chunk=True)
        # one gloss file per language, so its shape cards carry meanings at once
        ma = json.loads((outdir / "lang" / "stan1290.json").read_text(encoding="utf-8"))
        self.assertIn("mother", ma["ma"])
        self.assertIn("horse", ma["ma"])
        self.assertEqual(len(list((outdir / "lang").glob("*.json"))),
                         sum(1 for L in core["languages"] if L["form_count"]))
        b = core["meta"]["baseline"]
        self.assertEqual(set(b), {"method", "hypotheses", "tested", "beyond", "fdr"})
        self.assertGreaterEqual(b["hypotheses"], b["tested"])
        self.assertEqual(b["beyond"], sum(c["beyond"] for c in core["concepts"]))
        # every meaning carries its chance comparison (roadmap B1)
        for c in core["concepts"]:
            self.assertIn("beyond", c)
            self.assertIn("gap", c)
            chunk = json.loads((outdir / "concept" / f"{c['ckey']}.json").read_text(encoding="utf-8"))
            self.assertIn("baseline", chunk)
            for obs, lo, hi, top in chunk["baseline"].values():
                self.assertLessEqual(lo, hi)
                self.assertLessEqual(hi, top)
        self.assertGreater(n_chunks, 0, "per-shape chunks written")
        self.assertTrue((outdir / "shape").is_dir())
        self.assertEqual(warns, [], "static-baked hybrid holds at seed+demo scale")
        # tripwire fires on an oversized core
        fake = {"x": "y" * 6_000_000}
        self.assertTrue(tripwires(fake, 0), "core > 5MB trips")
        self.assertTrue(tripwires({}, 20_000), ">15k chunks trips")


class TestBuildInputs(unittest.TestCase):
    """The published catalog is made of real sources only. The seed and the CLDF
    demo are test inputs: before 2026-09-29 they shipped, citing tools that never
    ran (epitran) and datasets never ingested (northeuralex-0.9)."""

    def test_fixtures_never_reach_the_build(self):
        import shutil, tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(ROOT / "seed", root / "seed")
            real = root / "sources" / "realset" / "cldf"
            real.mkdir(parents=True)
            (real / "metadata.json").write_text('{"id": "realset", "license": "CC-BY-4.0"}')
            (real / "languages.csv").write_text("ID,Name,Glottocode,Family\nm,Maori,maor1246,Austronesian\n")
            (real / "parameters.csv").write_text("ID,Name,Concepticon_ID\nsun,sun,1343\n")
            (real / "forms.csv").write_text("ID,Language_ID,Parameter_ID,Form,Segments\n1,m,sun,ra,r a\n")
            ids = {s["id"] for ds in collect(root) for s in ds["sources"]}
        self.assertEqual(ids, {"realset"})

    def test_glottolog_names_the_languages_when_present(self):
        # grollemundbantu's Glottolog_Name column called three glottocodes "Tuki";
        # Glottolog itself says Tuki, Bebele, Eton-Mengisa
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "sources" / "realset" / "cldf"
            real.mkdir(parents=True)
            (real / "metadata.json").write_text('{"id": "realset", "license": "CC-BY-4.0"}')
            (real / "languages.csv").write_text("ID,Name,Glottocode,Glottolog_Name\n"
                                                "a,A61_Ngoro,eton1253,Tuki\nb,Tuki,tuki1240,Tuki\n")
            (real / "parameters.csv").write_text("ID,Name\n")
            (real / "forms.csv").write_text("ID,Language_ID,Parameter_ID,Form,Segments\n")
            g = root / "sources" / "glottolog-cldf" / "cldf"
            g.mkdir(parents=True)
            (g / "languages.csv").write_text("ID,Name,Level\neton1253,Eton-Mengisa,language\ntuki1240,Tuki,language\n")
            langs = {l["glottocode"]: l for ds in collect(root) for l in ds["languages"]}
        self.assertEqual((langs["eton1253"]["name"], langs["eton1253"]["alias"]), ("Eton-Mengisa", "A61_Ngoro"))
        self.assertEqual(langs["tuki1240"]["name"], "Tuki")

    def test_wikipron_language_map_is_tracked(self):
        import subprocess
        path = ROOT / "config" / "wikipron-langmap.json"
        self.assertTrue(path.exists())
        ignored = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=ROOT).returncode == 0
        self.assertFalse(ignored, "the hand-made language map must not sit in a gitignored folder")


if __name__ == "__main__":
    unittest.main()
