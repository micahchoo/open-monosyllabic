"""Fetch Wiktionary glosses for WikiPron-mined languages (wiktextract/kaikki.org).

WikiPron gives word→IPA with no meanings; kaikki.org publishes wiktextract's parse
of the same Wiktionary as JSONL (word + senses[].glosses). Joining on the headword
(both native-script) attaches meanings to mined forms. Licence: Wiktionary content
is CC-BY-SA 3.0 — same gate verdict as WikiPron itself (PASS, share-alike).

Emits sources/wikipron/gloss/{iso}.json  ({word: [up to 3 short glosses]}), which
`ingest_wikipron.load` picks up when present. Run:  python3 -m oms.fetch_glosses
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

from oms.ingest_wikipron import LANGMAP

# kaikki.org per-language dump names (English-Wiktionary extraction)
KAIKKI = {
    "hin": "Hindi", "ben": "Bengali", "tam": "Tamil", "tel": "Telugu",
    "mal": "Malayalam", "mar": "Marathi", "yor": "Yoruba", "hau": "Hausa",
}
_MAX_GLOSSES = 3
_MAX_LEN = 80


def _url(lang: str) -> str:
    return (f"https://kaikki.org/dictionary/{lang}/kaikki.org-dictionary-{lang}.jsonl")


def build_gloss_map(jsonl_lines) -> dict[str, list[str]]:
    """word -> up to _MAX_GLOSSES concise senses. Skips senses with no gloss text
    and form-of cross-references (they gloss the inflection, not the meaning)."""
    out: dict[str, list[str]] = {}
    for line in jsonl_lines:
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        word = e.get("word")
        if not word:
            continue
        gs = out.setdefault(word, [])
        for sense in e.get("senses", []):
            if len(gs) >= _MAX_GLOSSES:
                break
            if sense.get("form_of") or sense.get("alt_of"):
                continue
            for g in sense.get("glosses", []):
                g = g.strip()
                if g and len(g) <= _MAX_LEN and g not in gs:
                    gs.append(g)
                    break
    return {w: gs for w, gs in out.items() if gs}


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    outdir = root / "sources" / "wikipron" / "gloss"
    outdir.mkdir(parents=True, exist_ok=True)
    langmap = json.loads(LANGMAP.read_text(encoding="utf-8"))
    for iso, lang in KAIKKI.items():
        if iso not in langmap or not (root / "sources" / "wikipron" / "tsv" / f"{iso}.tsv").exists():
            continue
        dest = outdir / f"{iso}.json"
        if dest.exists():
            print(f"{iso}: gloss/{iso}.json exists, skipping (delete to refetch)")
            continue
        print(f"{iso}: fetching kaikki {lang} …", flush=True)
        try:
            with urllib.request.urlopen(_url(lang), timeout=600) as r:
                gloss = build_gloss_map(line.decode("utf-8") for line in r)
        except Exception as e:  # noqa: broad — a missing dump must not kill the rest
            print(f"{iso}: FAILED ({e}) — mined forms stay gloss-less", file=sys.stderr)
            continue
        dest.write_text(json.dumps(gloss, ensure_ascii=False), encoding="utf-8")
        print(f"{iso}: {len(gloss)} glossed headwords -> gloss/{iso}.json")


if __name__ == "__main__":
    main()
