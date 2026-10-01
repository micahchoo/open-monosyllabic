"""BAKE step (IMPLEMENTATION-STRATEGY §10) — Form set -> static core index.

Emits data/{canon-version}/core.json (the shape->languages inverted index that
powers every live surface client-side) and forms.json (drill detail). The seed
ships as a single blob; the DataStore contract lets Phase 5 swap in per-shape
chunking invisibly.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from oms.baseline import chance_bands
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
        # packed posting: [langIdx, tierRank, ccRank, under_review, tones]
        # tones = how many tones the source gives this shape in this language:
        # Yoruba /ba/ with three tones is three words behind one shape (0 = unmarked)
        postings[f.segmental].append([
            lang_idx[f.glottocode],
            TIERS.index(f.tier),
            _CC.index(f.classification_confidence),
            1 if f.under_review else 0,
            len(f.tones),
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
                "glottocode": l.glottocode, "name": l.name, "alias": l.alias, "macroarea": l.macroarea,
                "latitude": l.latitude, "longitude": l.longitude,
                "doc_status": l.doc_status, "prosodic_type": l.prosodic_type,
                "family": l.family,
                "form_count": form_count[l.glottocode],
                "examined": pipeline_out["examined"].get(l.glottocode, 0),
                "sample": pipeline_out["sample"].get(l.glottocode, ""),
                "tone_marked": l.glottocode in pipeline_out.get("tone_marked", ()),
                "syllable_structure": l.syllable_structure,
                "inventory": l.inventory,
            }
            for l in langs
        ],
        "shapes": sorted(shapes.values(), key=lambda s: s["shape"]),
        "postings": postings,
        "sources": [
            {"id": s.id, "tier": s.tier, "license": s.license, "kind": s.kind}
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
                # casefolded, so "Go" and "go" are one unlinked gloss, not two
                ckey = str(cid) if cid else "g-" + hashlib.sha1(g["gloss"].strip().casefold().encode("utf-8")).hexdigest()[:16]
                c = concepts.setdefault(ckey, {
                    "ckey": ckey, "gloss": g["gloss"], "concepticon_id": cid,
                    "concepticon_gloss": g.get("concepticon_gloss"), "votes": Counter(),
                    "langs": set(), "shapes": set(), "entries": []})
                c["votes"][g["gloss"].strip()] += 1
                c["langs"].add(li)
                c["shapes"].add(f.segmental)
                # entry: [langIdx, shape, tone, tierRank, ccRank, under_review]
                c["entries"].append([li, f.segmental, w.tone, tr, cr, ur])
    labels = concept_labels(concepts)
    for k, c in concepts.items():
        c["gloss"] = labels[k]
    return concepts


def _commonest(votes: dict) -> str:
    """The commonest source gloss, ignoring case; shown in its commonest spelling."""
    by_fold: dict[str, Counter] = {}
    for g, n in votes.items():
        by_fold.setdefault(g.casefold(), Counter())[g] += n
    fold = max(by_fold, key=lambda f: (sum(by_fold[f].values()), f))
    return max(by_fold[fold], key=lambda g: (by_fold[fold][g], g))


def _concepticon_label(cg: str) -> str:
    # Concepticon glosses are upper case; lower them, but the pronoun stays "I"
    return re.sub(r"\bi\b", "I", cg.lower())


def concept_labels(concepts: dict) -> dict[str, str]:
    """One distinct label per concept (roadmap D4). A concept reads as its
    sources call it, written the Concepticon way when it is the Concepticon
    word ("Two" -> "two", "I" stays "I"). Where concepts would read alike:
    an unlinked gloss is marked "(unlinked)" and never merged; a lone linked
    concept keeps the word; among several linked ones, the concept whose
    Concepticon gloss IS the word keeps it and the others read as their own
    Concepticon gloss (IRRIGATE was listed as 'water' in 22 languages)."""
    base = {}
    for k, c in concepts.items():
        b, cg = _commonest(c["votes"]), c.get("concepticon_gloss")
        base[k] = _concepticon_label(cg) if cg and cg.casefold() == b.casefold() else b
    groups: dict[str, list[str]] = {}
    for k, b in base.items():
        groups.setdefault(b.casefold(), []).append(k)
    labels: dict[str, str] = {}
    for fold, keys in groups.items():
        linked = [k for k in keys if concepts[k].get("concepticon_id")]
        for k in keys:
            if k not in linked:
                labels[k] = f"{base[k]} (unlinked)" if len(keys) > 1 else base[k]
                continue
            cg = concepts[k].get("concepticon_gloss")
            if len(linked) == 1 or (cg and cg.casefold() == fold):
                labels[k] = base[k]
            else:
                labels[k] = _concepticon_label(cg) if cg else f"{base[k]} ({concepts[k]['concepticon_id']})"
    # A qualified label can still equal another concept's word. Mark the unlinked
    # side first; a linked concept is qualified only by its own Concepticon id.
    for _ in range(2):
        seen: Counter = Counter(l.casefold() for l in labels.values())
        for k, l in list(labels.items()):
            if seen[l.casefold()] > 1:
                if not concepts[k].get("concepticon_id"):
                    if not l.endswith("(unlinked)"):
                        labels[k] = f"{l} (unlinked)"
                elif any(not concepts[j].get("concepticon_id") and labels[j].casefold() == l.casefold() for j in labels):
                    continue   # the unlinked twin is marked on this pass
                else:
                    labels[k] = f"{l} ({concepts[k]['concepticon_id']})"
    return labels


def _concept_summary(concepts: dict, bands: dict, families: list[str] | None = None, fdr: float = 0.05) -> list[dict]:
    # beyond = shapes more families share than chance, at a 5% false-discovery
    # rate (baseline.chance_bands); gap = the largest excess over the band, for sorting (B1)
    def excess(k):
        return [obs - hi for obs, lo, hi, q in bands.get(k, {}).values() if q <= fdr]
    rows = [{"ckey": c["ckey"], "gloss": c["gloss"], "concepticon_id": c["concepticon_id"],
             "lang_count": len(c["langs"]), "shape_count": len(c["shapes"]),
             # families, as everywhere: languages without one count alone
             "fam_count": len({(families or [])[li] if families and families[li] else f"lang:{li}" for li in c["langs"]}),
             "beyond": len(excess(c["ckey"])), "gap": max(excess(c["ckey"]), default=0)}
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
    fams = [l.family for l in pipeline_out["languages"].values()]
    bands, summary = chance_bands(concepts, fams)
    core["concepts"] = _concept_summary(concepts, bands, fams, summary["fdr"])
    core["meta"]["baseline"] = {"method": "exact", **summary}
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "core.json").write_text(json.dumps(core, ensure_ascii=False, indent=1), encoding="utf-8")
    cdir = outdir / "concept"
    cdir.mkdir(exist_ok=True)
    for c in concepts.values():
        (cdir / f"{c['ckey']}.json").write_text(
            json.dumps({"gloss": c["gloss"], "concepticon_id": c["concepticon_id"], "entries": c["entries"],
                        "baseline": {s: list(b) for s, b in bands.get(c["ckey"], {}).items()}},
                       ensure_ascii=False), encoding="utf-8")
    swept = _sweep_stale(cdir, {f"{c['ckey']}.json" for c in concepts.values()})
    # One gloss file per language: shape -> its meanings. The Languages view
    # showed a card's meanings only once that shape's chunk happened to load;
    # this is one small request per language instead of one per shape.
    ldir = outdir / "lang"
    ldir.mkdir(exist_ok=True)
    by_lang: dict[str, dict[str, list[str]]] = {}
    for fd in forms_detail.values():
        gl = by_lang.setdefault(fd["glottocode"], {}).setdefault(fd["shape"], [])
        for w in fd["words"]:
            for g in w["gloss_set"]:
                if g["gloss"] and g["gloss"] not in gl:
                    gl.append(g["gloss"])
    for gc, shapes in by_lang.items():
        (ldir / f"{gc}.json").write_text(json.dumps(shapes, ensure_ascii=False), encoding="utf-8")
    swept += _sweep_stale(ldir, {f"{gc}.json" for gc in by_lang})
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
