"""Scale-out driver (IMPLEMENTATION-STRATEGY Phase 5).

Merges the hand seed with one or more CLDF datasets and bakes a CHUNKED build
(per-shape chunks, the DataStore contract for scale). Demonstrates that the same
Form output + BAKE swap invisibly from single-blob (seed) to chunked (scale), and
reports the tripwire checks. Real Phase 5 points this at the full ingested corpus;
here it points at seed + the CLDF demo fixture.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from oms.pipeline import run_datasets
from oms.ingest_cldf import load as load_cldf
from oms.ingest_wikipron import load as load_wikipron
from oms.bake import write_build
from oms import concepticon, typology


# Orthography-only datasets: their transcriptions are SPELLINGS, not IPA — every
# shape minted from them is garbage (audit 2026-07-04: dyenindoeuropean shipped
# 'boyau', 'cle', 'krow' as canonical shapes; Segments empty in 100% of rows).
# Excluded until a per-source orthography→IPA profile exists.
# IDS (triaged 2026-10-01): 0 of 437,902 rows carry Segments; its "Phonemic"
# transcriptions are each contributor's own notation, Americanist for most
# (č, ƛ̄ʼ, lʸ, x̣), its "phonetic" rows mix spelling with tone numbers
# (su'o'ng, le.41ʔ), and one variety of 329 is marked IPA. A profile per
# contributor would be needed; until then it is spelling, not IPA.
# satterthwaitetb (2026-10-01 audit): 0 of 6,778 rows segmented; Hani and
# Lahu orthography (hhe, yo deiv ssaq) read as IPA gave 732 curated forms.
_ORTHOGRAPHIC = {"dyenindoeuropean", "ids", "satterthwaitetb"}


def _discover_cldf(root: Path) -> list[Path]:
    """CLDF datasets = dirs with forms.csv + languages.csv + a metadata file,
    cloned under sources/. Never seed/: the seed and the CLDF demo are TEST
    inputs, and until 2026-09-29 they shipped in the catalog citing tools that
    never ran (epitran) and datasets never ingested (northeuralex-0.9)."""
    dirs = []
    for base in [*sorted((root / "sources").glob("*/cldf")), *sorted((root / "sources").glob("*"))]:
        if {base.name, base.parent.name} & _ORTHOGRAPHIC:
            print(f"  EXCLUDE {base.relative_to(root)}: orthography-only (no IPA), see _ORTHOGRAPHIC")
            continue
        if base.is_dir() and (base / "forms.csv").exists() and (base / "languages.csv").exists():
            if base not in dirs:
                dirs.append(base)
    return dirs


def _glottolog_names(root: Path) -> dict[str, str]:
    """Glottocode -> name from Glottolog itself (sources/glottolog-cldf, a sparse
    clone of glottolog/glottolog-cldf, CC-BY-4.0). A source's Glottolog_Name
    column can be stale: grollemundbantu named three glottocodes "Tuki"."""
    path = root / "sources" / "glottolog-cldf" / "cldf" / "languages.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["ID"]: r["Name"] for r in csv.DictReader(fh) if r.get("Name")}


def _glottolog_families(root: Path) -> dict[str, str]:
    """Glottocode -> top-level family name from Glottolog's Family_ID. An
    isolate is a family of its own, named after itself. Source Family columns
    disagreed with Glottolog for 73 languages (2026-10-01 audit): "Isolate"
    put Abun and Mpur in one family, and "South Bird's Head" was counted twice."""
    path = root / "sources" / "glottolog-cldf" / "cldf" / "languages.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    name = {r["ID"]: r["Name"] for r in rows}
    return {r["ID"]: name.get(r["Family_ID"], "") if r.get("Family_ID") else r["Name"]
            for r in rows if r.get("Level") in ("language", "dialect")}


def _apply_names(datasets: list[dict], names: dict[str, str], families: dict[str, str] | None = None) -> None:
    """Name every language by Glottolog; the name it had becomes the alias,
    unless the source's own doculect name is already there. Families too."""
    for ds in datasets:
        for lang in ds["languages"]:
            if families and families.get(lang["glottocode"]):
                lang["family"] = families[lang["glottocode"]]
            g = names.get(lang["glottocode"])
            if g and g != lang["name"]:
                lang["alias"] = lang.get("alias") or lang["name"]
                lang["name"] = g
            if lang.get("alias") == lang["name"]:
                lang["alias"] = ""


def collect(root: Path) -> list[dict]:
    """Every real dataset under root/sources/, loaded and named by Glottolog."""
    datasets = []
    for d in _discover_cldf(root):
        try:
            datasets.append(load_cldf(d))
            print(f"  ingested {d.relative_to(root)}")
        except (ValueError, FileNotFoundError) as e:
            print(f"  SKIP {d.relative_to(root)}: {e}")
    # mined tier: WikiPron (a different format than CLDF)
    if (root / "sources" / "wikipron" / "tsv").is_dir():
        datasets.append(load_wikipron(root / "sources" / "wikipron"))
        print("  ingested sources/wikipron (mined tier)")
    linked = concepticon.link(datasets, concepticon.load(
        root / "sources" / "concepticon-data" / "concepticondata" / "concepticon.tsv"))
    if linked:
        print(f"  linked {linked} glosses to Concepticon by their English gloss")
    names = _glottolog_names(root)
    if names:
        _apply_names(datasets, names, _glottolog_families(root))
        print(f"  named {len(names)} glottocodes from sources/glottolog-cldf")
    return datasets


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out = run_datasets(collect(root))
    n_wals, n_inv = typology.attach(out["languages"], root)
    print(f"  WALS syllable structure for {n_wals} languages; PHOIBLE inventory for {n_inv}")

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

    print(f"  {out['disagreements']} open forms under review: another source closed the same word")
    print(f"scale-out: {len(out['languages'])} languages, {len(core['shapes'])} shapes, "
          f"{sum(len(p) for p in core['postings'].values())} postings")
    print(f"chunked build → data/{reldir}/ ({n_chunks} per-shape chunks + core.json); web now serves this build")
    top = sorted(cross.items(), key=lambda kv: -kv[1])[:10]
    print(f"cross-language shapes (≥2 langs): {len(cross)}; widest: {top}")
    print("tripwires:", warns or "none (static-baked hybrid holds at this scale)")


if __name__ == "__main__":
    main()
