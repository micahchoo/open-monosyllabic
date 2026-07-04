"""Scale-out driver (IMPLEMENTATION-STRATEGY Phase 5).

Merges the hand seed with one or more CLDF datasets and bakes a CHUNKED build
(per-shape chunks, the DataStore contract for scale). Demonstrates that the same
Form output + BAKE swap invisibly from single-blob (seed) to chunked (scale), and
reports the tripwire checks. Real Phase 5 points this at the full ingested corpus;
here it points at seed + the CLDF demo fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

from oms.pipeline import run_datasets
from oms.ingest_cldf import load as load_cldf
from oms.ingest_wikipron import load as load_wikipron
from oms.bake import write_build


# Orthography-only datasets: their transcriptions are SPELLINGS, not IPA — every
# shape minted from them is garbage (audit 2026-07-04: dyenindoeuropean shipped
# 'boyau', 'cle', 'krow' as canonical shapes; Segments empty in 100% of rows).
# Excluded until a per-source orthography→IPA profile exists.
_ORTHOGRAPHIC = {"dyenindoeuropean"}


def _discover_cldf(root: Path) -> list[Path]:
    """CLDF datasets = dirs with forms.csv + languages.csv + a metadata file.
    Covers the demo fixture and any real dataset cloned under sources/."""
    dirs = []
    for base in [root / "seed" / "cldf_demo", *sorted((root / "sources").glob("*/cldf")), *sorted((root / "sources").glob("*"))]:
        if {base.name, base.parent.name} & _ORTHOGRAPHIC:
            print(f"  EXCLUDE {base.relative_to(root)}: orthography-only (no IPA), see _ORTHOGRAPHIC")
            continue
        if base.is_dir() and (base / "forms.csv").exists() and (base / "languages.csv").exists():
            if base not in dirs:
                dirs.append(base)
    return dirs


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    seed = json.loads((root / "seed" / "seed.json").read_text(encoding="utf-8"))
    datasets = [seed]
    for d in _discover_cldf(root):
        try:
            datasets.append(load_cldf(d))
            print(f"  ingested {d.relative_to(root)}")
        except (ValueError, FileNotFoundError) as e:
            print(f"  SKIP {d.relative_to(root)}: {e}")
    # mined tier: WikiPron (a different format than CLDF)
    if (root / "sources" / "wikipron" / "langmap.json").exists():
        datasets.append(load_wikipron(root / "sources" / "wikipron"))
        print("  ingested sources/wikipron (mined tier)")
    out = run_datasets(datasets)

    version = out["scheme_version"]
    reldir = f"scaled/{version}"
    outdir = root / "data" / reldir
    core, n_chunks, warns = write_build(out, outdir, chunk=True)
    # point the web at the scaled (chunked) build via the build descriptor
    (root / "data" / "current.json").write_text(
        json.dumps({"version": version, "dir": reldir, "chunked": True}), encoding="utf-8")

    shapes = {}
    for f in out["forms"]:
        shapes.setdefault(f.segmental, []).append(f.glottocode)
    cross = {s: len(gs) for s, gs in shapes.items() if len(gs) > 1}

    print(f"scale-out: {len(out['languages'])} languages, {len(core['shapes'])} shapes, "
          f"{sum(len(p) for p in core['postings'].values())} postings")
    print(f"chunked build → data/{reldir}/ ({n_chunks} per-shape chunks + core.json); web now serves this build")
    print(f"cross-language shapes (≥2 langs): {cross}")
    print("tripwires:", warns or "none (static-baked hybrid holds at this scale)")


if __name__ == "__main__":
    main()
