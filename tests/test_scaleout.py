"""Phase 5 scale-out: CLDF ingestion adapter + dataset merge + chunked bake."""

import json
import unittest
from pathlib import Path

from oms.ingest_cldf import load as load_cldf, clearance_ok
from oms.pipeline import run_datasets
from oms.bake import write_build, tripwires

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
        self.assertTrue(any(e["ipa"] == "maː˧" for e in self.cldf["entries"]))

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
        # /wai/ now spans Fijian, Hawaiian, Maori
        wai = sorted(f.glottocode for f in self.out["forms"] if f.segmental == "wai")
        self.assertIn("maor1246", wai)
        self.assertGreaterEqual(len(wai), 3)

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
        self.assertGreater(n_chunks, 0, "per-shape chunks written")
        self.assertTrue((outdir / "shape").is_dir())
        self.assertEqual(warns, [], "static-baked hybrid holds at seed+demo scale")
        # tripwire fires on an oversized core
        fake = {"x": "y" * 6_000_000}
        self.assertTrue(tripwires(fake, 0), "core > 5MB trips")
        self.assertTrue(tripwires({}, 20_000), ">15k chunks trips")


if __name__ == "__main__":
    unittest.main()
