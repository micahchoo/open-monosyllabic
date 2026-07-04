"""BAKE step (IMPLEMENTATION-STRATEGY §10) — Form set -> static core index.

Emits data/{canon-version}/core.json (the shape->languages inverted index that
powers every live surface client-side) and forms.json (drill detail). The seed
ships as a single blob; the DataStore contract lets Phase 5 swap in per-shape
chunking invisibly.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from oms.model import TIERS
from oms.pipeline import run

_CC = ("high", "medium", "low")


def bake(pipeline_out: dict) -> tuple[dict, dict]:
    langs = list(pipeline_out["languages"].values())
    lang_idx = {l.glottocode: i for i, l in enumerate(langs)}
    forms = pipeline_out["forms"]

    form_count = {g: 0 for g in lang_idx}
    for f in forms:
        form_count[f.glottocode] += 1

    # shape table: unique shapes with their (language-independent) features
    shapes: dict[str, dict] = {}
    postings: dict[str, list] = {}
    for f in forms:
        if f.segmental not in shapes:
            shapes[f.segmental] = {
                "shape": f.segmental,
                "onset_class": f.onset_class,
                "nucleus_bucket": f.nucleus_bucket,
                "nucleus_type": f.nucleus_type,
            }
            postings[f.segmental] = []
        # packed posting: [langIdx, tierRank, ccRank, under_review]
        postings[f.segmental].append([
            lang_idx[f.glottocode],
            TIERS.index(f.tier),
            _CC.index(f.classification_confidence),
            1 if f.under_review else 0,
        ])

    core = {
        "meta": {
            "scheme_version": pipeline_out["scheme_version"],
            "tiers": list(TIERS),
            "classification_confidence": list(_CC),
            "note": "seed build — single blob; shape->languages inverted index",
        },
        "languages": [
            {
                "glottocode": l.glottocode, "name": l.name, "macroarea": l.macroarea,
                "latitude": l.latitude, "longitude": l.longitude,
                "doc_status": l.doc_status, "prosodic_type": l.prosodic_type,
                "form_count": form_count[l.glottocode],
            }
            for l in langs
        ],
        "shapes": sorted(shapes.values(), key=lambda s: s["shape"]),
        "postings": postings,
        "sources": [
            {"id": s.id, "tier": s.tier, "license": s.license}
            for s in sorted(pipeline_out["sources"].values(), key=lambda s: (TIERS.index(s.tier), s.id))
        ],
    }

    forms_detail = {
        f.key: {
            "glottocode": f.glottocode, "shape": f.segmental, "tones": sorted(f.tones),
            "tier": f.tier, "classification_confidence": f.classification_confidence,
            "under_review": f.under_review, "preferred_source": f.preferred_source,
            "sources": f.sources, "onset_class": f.onset_class,
            "nucleus_bucket": f.nucleus_bucket, "nucleus_type": f.nucleus_type,
            "words": [
                {"tone": w.tone, "tier": w.tier, "sources": w.sources, "gloss_set": w.gloss_set}
                for w in f.words
            ],
        }
        for f in forms
    }
    return core, forms_detail


def _slug(shape: str) -> str:
    return "u" + "-".join(f"{ord(c):04x}" for c in shape)


def build_concepts(pipeline_out: dict) -> dict:
    """Meaning index (the hero axis): concept → the open monosyllables that express
    it across languages. Grouped so the sound↔meaning convergence is visible."""
    langs = list(pipeline_out["languages"].values())
    lang_idx = {l.glottocode: i for i, l in enumerate(langs)}
    concepts: dict[str, dict] = {}
    for f in pipeline_out["forms"]:
        li = lang_idx[f.glottocode]
        tr, cr, ur = TIERS.index(f.tier), _CC.index(f.classification_confidence), 1 if f.under_review else 0
        for w in f.words:
            for g in w.gloss_set:
                cid = g.get("concepticon_id")
                # gloss-keyed ckey is HASHED, not char-slugged: wiktextract glosses
                # are sentence-length and a per-char slug blows past the 255-byte
                # filename limit. ckey is opaque to the frontend; gloss text lives
                # inside the chunk.
                ckey = str(cid) if cid else "g-" + hashlib.sha1(g["gloss"].encode("utf-8")).hexdigest()[:16]
                c = concepts.setdefault(ckey, {
                    "ckey": ckey, "gloss": g["gloss"], "concepticon_id": cid,
                    "langs": set(), "shapes": set(), "entries": []})
                c["langs"].add(li)
                c["shapes"].add(f.segmental)
                # entry: [langIdx, shape, tone, tierRank, ccRank, under_review]
                c["entries"].append([li, f.segmental, w.tone, tr, cr, ur])
    return concepts


def _concept_summary(concepts: dict) -> list[dict]:
    rows = [{"ckey": c["ckey"], "gloss": c["gloss"], "concepticon_id": c["concepticon_id"],
             "lang_count": len(c["langs"]), "shape_count": len(c["shapes"])}
            for c in concepts.values()]
    # hero ordering: broadest reach first, then tightest sound↔meaning convergence
    rows.sort(key=lambda r: (-r["lang_count"], r["shape_count"], r["gloss"]))
    return rows


def tripwires(core: dict, n_chunks: int) -> list[str]:
    """DataStore tripwires (§10): when to abandon the plain-JSON static path."""
    warns = []
    core_bytes = len(json.dumps(core, ensure_ascii=False).encode())
    if core_bytes > 5_000_000:
        warns.append(f"core index {core_bytes} B > 5 MB → switch to packed binary postings (still no backend)")
    if n_chunks > 15_000:
        warns.append(f"{n_chunks} chunk files > 15k → shard or move data to object storage (R2/S3)")
    return warns


def _sweep_stale(dirpath: Path, keep: set[str]) -> int:
    """Remove chunk files a previous bake wrote that this build no longer emits.
    Without this, renamed/removed shapes and concepts pile up as orphans that
    clients can still fetch (audit 2026-07-04: 2,018 stale shape chunks)."""
    stale = [p for p in dirpath.glob("*.json") if p.name not in keep]
    for p in stale:
        p.unlink()
    return len(stale)


def write_build(pipeline_out: dict, outdir: Path, chunk: bool = False) -> tuple[dict, int, list[str]]:
    """Emit a versioned build. Seed = single forms.json blob; scale = per-shape
    chunks (DataStore contract §10). Returns (core, n_chunks, tripwire warnings)."""
    core, forms_detail = bake(pipeline_out)
    # meaning is a hero axis: concept summary in core, concept detail as chunks
    concepts = build_concepts(pipeline_out)
    core["concepts"] = _concept_summary(concepts)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "core.json").write_text(json.dumps(core, ensure_ascii=False, indent=1), encoding="utf-8")
    cdir = outdir / "concept"
    cdir.mkdir(exist_ok=True)
    for c in concepts.values():
        (cdir / f"{c['ckey']}.json").write_text(
            json.dumps({"gloss": c["gloss"], "concepticon_id": c["concepticon_id"], "entries": c["entries"]},
                       ensure_ascii=False), encoding="utf-8")
    swept = _sweep_stale(cdir, {f"{c['ckey']}.json" for c in concepts.values()})
    n_chunks = 0
    if chunk:
        shapedir = outdir / "shape"
        shapedir.mkdir(exist_ok=True)
        by_shape: dict[str, dict] = {}
        for key, fd in forms_detail.items():
            by_shape.setdefault(fd["shape"], {})[key] = fd
        for shape, forms in by_shape.items():
            (shapedir / f"{_slug(shape)}.json").write_text(
                json.dumps(forms, ensure_ascii=False), encoding="utf-8")
        n_chunks = len(by_shape)
        swept += _sweep_stale(shapedir, {f"{_slug(s)}.json" for s in by_shape})
    else:
        (outdir / "forms.json").write_text(json.dumps(forms_detail, ensure_ascii=False, indent=1), encoding="utf-8")
    if swept:
        print(f"swept {swept} stale chunk files from {outdir}")
    return core, n_chunks, tripwires(core, n_chunks)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out = run(root / "seed" / "seed.json")
    version = out["scheme_version"]
    core, _, _ = write_build(out, root / "data" / version, chunk=False)
    (root / "data" / "current.json").write_text(
        json.dumps({"version": version, "dir": version, "chunked": False}), encoding="utf-8")
    print(f"baked {len(core['shapes'])} shapes, {sum(len(p) for p in core['postings'].values())} postings "
          f"→ data/{version}/core.json")


if __name__ == "__main__":
    main()
