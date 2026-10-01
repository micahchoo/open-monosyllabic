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
import unicodedata
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


# Datasets that ship SPELLINGS in Form and no Segments, with the few rules that
# turn their orthography into IPA. ABVD (2026-09-29): 0 of 346,662 rows carry
# Segments; ' / ʻ / ’ write the glottal stop, y is /j/, ng is /ŋ/ across
# Austronesian orthographies. Only the respelled string is read as IPA, and as
# graphemes: an unmarked vowel pair stays two nuclei (hiatus), so ABVD keeps
# its single-vowel forms and loses its vowel sequences (user decision "A").
_RESPELL = {
    "abvd": (("ng", "ŋ"), ("'", "ʔ"), ("ʻ", "ʔ"), ("’", "ʔ"), ("`", "ʔ"), ("y", "j")),
}


# Marks that write VOWEL QUALITY in a spelling, differently per orthography:
# circumflex (Yabem ê), breve (ă), horn (Vietnamese-based ư ơ), caron (ǎ).
# Canon would read ̂ as tone and strip it, merging vowels. 4,360 ABVD rows in 338
# languages (2026-09-29); excluded, counted, and outside `examined` (decision "A").
_SPELLING_MARKS = {"\u0302", "\u0306", "\u031b", "\u030c"}


# Acute and grave: on a longer word a stress mark (13,437 ABVD rows), stripped
# harmlessly. On a ONE-vowel word stress cannot contrast, so the accent writes
# vowel quality or tone — Chuukese pe / pé merged when it was stripped (12
# languages had both). 207 such forms, measured 2026-09-29.
_ACCENTS = {"\u0301", "\u0300"}
_VOWEL_LETTERS = set("aeiouyɨʉɯɪʏʊøɘɵɤəɛœɜɞʌɔæɐɶɑɒ")


def _spelling_exclusion(dataset: str, form: str) -> str | None:
    if dataset not in _RESPELL:
        return None
    nfd = unicodedata.normalize("NFD", form)
    if any(m in nfd for m in _SPELLING_MARKS):
        return "spelling mark with no fixed IPA reading (vowel-quality ê ă ư ǎ) — excluded"
    # count vowels in the RESPELLED form: ABVD y is /j/, so ráy has one vowel
    respelled = unicodedata.normalize("NFD", _respell(dataset, form)).lower()
    if any(a in nfd for a in _ACCENTS) and sum(ch in _VOWEL_LETTERS for ch in respelled) == 1:
        return "accent on a one-vowel spelling: quality or tone, no fixed IPA reading — excluded"
    return None


# A macron writes vowel LENGTH across Pacific spellings (ā = aː); canon would
# strip it as a tone mark and merge /maː/ with /ma/ (4,458 ABVD rows).
_MACRON_IS_LENGTH = {"abvd"}


def _respell(dataset: str, form: str) -> str:
    if dataset in _MACRON_IS_LENGTH:
        form = unicodedata.normalize("NFC", unicodedata.normalize("NFD", form).replace("\u0304", "ː"))
    for old, new in _RESPELL.get(dataset, ()):
        form = form.replace(old, new)
    return form


def _ipa(row: dict) -> str:
    """Prefer tokenized Segments (CLTS grapheme/BIPA tokens resolved to the BIPA
    side). Reject entries that are not attested free single words: reconstructions
    (*-marked in Form even when Segments strip the star), bound morphemes
    (edge hyphen in Form — Segments often lose it), polymorphemic entries
    (boundary tokens + _ # — joining across them mints fake monosyllables),
    multi-word phrases, and uncertain/alternation annotations.

    With Segments the result keeps the source's segment boundaries as spaces
    ("m ai" vs "m a i"): they are the source's syllable analysis."""
    raw = (row.get("Form") or row.get("Value") or "").strip()
    if raw.startswith("*"):
        return ""   # reconstruction (proto-form), not an attested word
    if raw and (raw[0] in "-+=" or raw[-1] in "-+="):
        return ""   # bound morpheme (affix/clitic: -ka, +lɔˀ, ='u), not a free word
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
        joined = " ".join(out)
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
        # Name by Glottolog: a source's Name is a doculect label ("A151_Nkongho",
        # lowercase "anam") and two sources can give two glottocodes one name.
        # The source's name stays as the alias, so a search still finds it.
        gname = (r.get("Glottolog_Name") or "").strip()
        languages.append({
            "glottocode": gc, "name": gname or r["Name"],
            "alias": r["Name"] if gname and gname != r["Name"] else "",
            "macroarea": r.get("Macroarea", ""),
            "latitude": float(r["Latitude"]) if r.get("Latitude") else None,
            "longitude": float(r["Longitude"]) if r.get("Longitude") else None,
            "doc_status": r.get("Doc_Status", "moderate"),
            "prosodic_type": r.get("Prosodic_Type", "unknown"),
            "family": (r.get("Family") or "").strip(),
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
        segmented = bool(r.get("Segments"))
        exclude = None
        if not segmented and meta["id"] not in _RESPELL:
            # no Segments and no respelling rules: a spelling, never read as IPA
            # (.claude/rules/oms-syllables-are-segments.md; papuanvoices has 10)
            exclude = "no segments and no respelling rules for this source — spelling, not IPA"
        elif not segmented:
            exclude = _spelling_exclusion(meta["id"], ipa)
            ipa = ipa if exclude else _respell(meta["id"], ipa)
        param = params.get(r["Parameter_ID"], {})
        cid = param.get("Concepticon_ID") or None
        entries.append({
            "glottocode": gc,
            "ipa": ipa,
            "gloss": param.get("Name") or param.get("Concepticon_Gloss") or r["Parameter_ID"],
            "concepticon_id": int(cid) if cid else None,
            "concepticon_gloss": param.get("Concepticon_Gloss") or None,
            "source": meta["id"],
            "segmented": segmented,
            **({"exclude": exclude} if exclude else {}),
        })
    return {"sources": [meta], "languages": languages, "entries": entries}
