"""CLDF Wordlist ingestion adapter (IMPLEMENTATION-STRATEGY Phase 5).

Reads a CLDF-style Wordlist directory (languages.csv, parameters.csv, forms.csv,
metadata.json) into the dataset dict the pipeline consumes — the real swap-in for
the hand seed behind the DataStore contract. Licence is read from metadata.json's
`license` field, NEVER inferred (ADR-0002 clearance rule).

This is a minimal, dependency-free reader over the CLDF column conventions; the
production path uses pycldf/pylexibank over full CLDF metadata. It reads the same
columns those emit (Language_ID, Parameter_ID, Form/Segments, Glottocode, ...).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

# Allowlist (ADR-0002, widened per user decision "any CC is fine"). NC variants are
# now allowed — but this forces the CATALOG's own release licence to CC-BY-NC-SA
# (non-commercial). ND variants stay BLOCKED: "no derivatives" legally forbids the
# catalog's core act (extracting + republishing canonicalized forms IS a derivative).
_ALLOWED = {
    "CC0-1.0", "CC-BY-4.0", "CC-BY-3.0", "CC-BY-SA-4.0", "CC-BY-SA-3.0", "MIT", "Apache-2.0",
    "CC-BY-NC-4.0", "CC-BY-NC-3.0", "CC-BY-NC-SA-4.0", "CC-BY-NC-SA-3.0",
}
# ND / NC-ND are intentionally absent from _ALLOWED (clearance blocks by omission):
# "no derivatives" forbids republishing canonicalized Forms.

# CLDF `dc:license` is a URL; map to the SPDX id the allowlist gate checks.
_LICENSE_URL = {
    "creativecommons.org/publicdomain/zero/1.0": "CC0-1.0",
    "creativecommons.org/licenses/by/4.0": "CC-BY-4.0",
    "creativecommons.org/licenses/by/3.0": "CC-BY-3.0",
    "creativecommons.org/licenses/by-sa/4.0": "CC-BY-SA-4.0",
    "creativecommons.org/licenses/by-sa/3.0": "CC-BY-SA-3.0",
    "creativecommons.org/licenses/by-nc/4.0": "CC-BY-NC-4.0",
    "creativecommons.org/licenses/by-nc/3.0": "CC-BY-NC-3.0",
    "creativecommons.org/licenses/by-nc-sa/4.0": "CC-BY-NC-SA-4.0",
    "creativecommons.org/licenses/by-nc-sa/3.0": "CC-BY-NC-SA-3.0",
    "creativecommons.org/licenses/by-nd/4.0": "CC-BY-ND-4.0",          # blocked (derivatives)
    "creativecommons.org/licenses/by-nc-nd/4.0": "CC-BY-NC-ND-4.0",    # blocked (derivatives)
}


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def clearance_ok(license: str) -> bool:
    """Phase-0 allowlist gate (ADR-0002): read the declared licence, allow only
    permissive/share-alike; block NC/ND/research-only/unset."""
    return license in _ALLOWED


def _normalize_license(raw: str) -> str:
    raw = (raw or "").strip().rstrip("/").replace("https://", "").replace("http://", "")
    if raw in _ALLOWED:
        return raw
    return _LICENSE_URL.get(raw, raw)


def _read_metadata(d: Path, default_tier: str) -> dict:
    """Support my demo `metadata.json` and real Lexibank `cldf-metadata.json`."""
    for name in ("metadata.json", "cldf-metadata.json"):
        p = d / name
        if p.exists():
            m = json.loads(p.read_text(encoding="utf-8"))
            return {
                "id": m.get("id") or m.get("rdf:ID") or d.parent.name,
                "tier": m.get("tier", default_tier),
                "license": _normalize_license(m.get("license") or m.get("dc:license", "")),
            }
    raise FileNotFoundError(f"no metadata.json / cldf-metadata.json in {d}")


# Source-annotation markers that mean "uncertain / alternation" in raw CLDF
# Segments (e.g. "b~p"). A real form carrying these is not a clean phoneme
# string — the orthography-profile audit (Phase-1 stage-2 acceptance criterion)
# would resolve them per source; until then we drop them honestly rather than
# mint a garbage Shape. ASCII '~' (U+007E) is distinct from the combining
# nasal tilde (U+0303), so nasalized vowels are unaffected.
# NOTE '/' is NOT an uncertainty marker inside a Segments token: CLTS writes
# "grapheme/BIPA" (source spelling left, normalized IPA right — e.g. "tʃ/tɕ",
# castrosui tone "₁/¹³"). Those are resolved per-token in _ipa below; a '/'
# is only annotation noise if it survives token resolution.
_ANNOTATION = set("/~<>[]{}()")


def _is_proto(name: str) -> bool:
    """Reconstructed proto-languages (e.g. 'Proto-Polynesian', 'Proto Malagasy')
    carry Glottolog family codes and reconstructed forms — never attested words,
    so they don't belong in a catalog of attested open monosyllables."""
    return bool(re.match(r"(?i)proto[-\s]", (name or "").strip()))


def _ipa(row: dict) -> str:
    """Prefer tokenized Segments (CLTS grapheme/BIPA tokens resolved to the BIPA
    side). Reject entries that are not attested free single words: reconstructions
    (*-marked in Form even when Segments strip the star), bound morphemes
    (edge hyphen in Form — Segments often lose it), polymorphemic entries
    (boundary tokens + _ # — joining across them mints fake monosyllables),
    multi-word phrases, and uncertain/alternation annotations."""
    raw = (row.get("Form") or row.get("Value") or "").strip()
    if raw.startswith("*"):
        return ""   # reconstruction (proto-form), not an attested word
    if raw.startswith("-") or raw.endswith("-"):
        return ""   # bound morpheme (affix/clitic), not a free word
    seg = row.get("Segments", "")
    if seg:
        toks = seg.split()
        if any(t in {"+", "_", "#"} for t in toks):
            return ""   # morpheme/word boundary: joining would mint a fake shape
        out = []
        for t in toks:
            if "/" in t:
                # CLTS "grapheme/BIPA": keep the normalized right side.
                t = t.split("/")[-1]
                if not t:
                    return ""   # "x/" — no BIPA normalization exists; skip row
            out.append(t)
        joined = "".join(out)
        if any(c in _ANNOTATION for c in joined):
            return ""   # uncertain/alternation form — skip (honest gap)
        return joined
    if " " in raw:
        return ""   # multi-word phrase — space-join would mint a fake shape
    return raw


def load(cldf_dir: str | Path, default_tier: str = "curated") -> dict:
    d = Path(cldf_dir)
    meta = _read_metadata(d, default_tier)
    if not clearance_ok(meta["license"]):
        raise ValueError(f"licence '{meta['license']}' not cleared for {meta['id']} — blocked at Phase-0 gate")

    langs_by_id = {r["ID"]: r for r in _rows(d / "languages.csv")}
    params = {r["ID"]: r for r in _rows(d / "parameters.csv")}

    languages, seen = [], set()
    for r in langs_by_id.values():
        gc = (r.get("Glottocode") or "").strip()
        if not gc or gc in seen or _is_proto(r.get("Name", "")):
            continue
        seen.add(gc)
        languages.append({
            "glottocode": gc, "name": r["Name"], "macroarea": r.get("Macroarea", ""),
            "latitude": float(r["Latitude"]) if r.get("Latitude") else None,
            "longitude": float(r["Longitude"]) if r.get("Longitude") else None,
            "doc_status": r.get("Doc_Status", "moderate"),
            "prosodic_type": r.get("Prosodic_Type", "unknown"),
        })

    entries = []
    for r in _rows(d / "forms.csv"):
        lang = langs_by_id.get(r["Language_ID"])
        gc = (lang or {}).get("Glottocode", "").strip() if lang else ""
        if lang and _is_proto(lang.get("Name", "")):
            continue   # reconstructed proto-language, not an attested doculect
        ipa = _ipa(r)
        if not gc or not ipa:
            continue
        param = params.get(r["Parameter_ID"], {})
        cid = param.get("Concepticon_ID") or None
        entries.append({
            "glottocode": gc,
            "ipa": ipa,
            "gloss": param.get("Name") or param.get("Concepticon_Gloss") or r["Parameter_ID"],
            "concepticon_id": int(cid) if cid else None,
            "source": meta["id"],
        })
    return {"sources": [meta], "languages": languages, "entries": entries}
