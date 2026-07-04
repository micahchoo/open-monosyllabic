"""WikiPron ingestion adapter — the MINED tier (IMPLEMENTATION-STRATEGY Phase 5).

WikiPron (github CUNY-CL/wikipron) mines word→IPA pairs from Wiktionary: one TSV
per language/script, lines of `word<TAB>ipa` (ipa space-separated phonemes). No
gloss, no Concepticon. This is the route to families with NO CLDF coverage —
Yoruboid, Igboid, Chadic beyond single tokens — so it is the key to West Africa.

Tier = `mined`; licence = CC-BY-SA-3.0 (Wiktionary-derived; gate PASS, share-alike
attaches). Reads a `langmap.json` mapping each TSV's ISO-639-3 code to a Glottocode
+ metadata (WikiPron keys on ISO, the catalog keys on Glottocode). Forms-only:
Words/glosses are absent, so these languages appear as Forms with no example Words
— exactly the graceful degradation the domain model was built for.
"""

from __future__ import annotations

import json
from pathlib import Path

SOURCE = {"id": "wikipron", "tier": "mined", "license": "CC-BY-SA-3.0"}


def _is_noise_word(w: str) -> bool:
    """WikiPron mines Wiktionary, which has non-lexical entries — alphabet/letter
    pages ("A", "B"), acronyms, punctuation — that surface as bare vowels/consonants.
    Drop those; KEEP genuine one-vowel words (Yoruba/Igbo lowercase pronouns like 'a')."""
    w = w.strip()
    if not w:
        return True
    if not any(c.isalpha() for c in w):          # pure digits / punctuation
        return True
    if len(w) == 1 and w.isascii() and w.isupper():   # letter-name entry: "A", "B"
        return True
    if w.isascii() and w.isupper() and len(w) <= 4 and w.isalpha():   # acronym: "USA"
        return True
    # Brahmic-script single characters (Devanagari..Thai block start) are Wiktionary
    # alphabet-letter pages ("क", "க"), not words — standalone letters aren't lexemes
    # in these scripts. Latin/African one-char words (Yoruba 'ó') are unaffected.
    if len(w) == 1 and 0x0900 <= ord(w) < 0x0E00:
        return True
    return False


def load(wikipron_dir: str | Path) -> dict:
    d = Path(wikipron_dir)
    langmap = json.loads((d / "langmap.json").read_text(encoding="utf-8"))
    languages, entries = [], []
    for iso, meta in langmap.items():
        tsv = d / "tsv" / f"{iso}.tsv"
        if not tsv.exists():
            continue
        # Optional wiktextract join (oms/fetch_glosses.py): headword -> [glosses].
        # Present -> mined forms carry meanings; absent -> forms-only, as before.
        gloss_file = d / "gloss" / f"{iso}.json"
        glosses = json.loads(gloss_file.read_text(encoding="utf-8")) if gloss_file.exists() else {}
        languages.append({
            "glottocode": meta["glottocode"], "name": meta["name"],
            "macroarea": meta.get("macroarea", ""),
            "latitude": meta.get("latitude"), "longitude": meta.get("longitude"),
            "doc_status": meta.get("doc_status", "moderate"),
            "prosodic_type": meta.get("prosodic_type", "unknown"),
        })
        for line in tsv.read_text(encoding="utf-8").splitlines():
            if not line.strip() or "\t" not in line:
                continue
            word, ipa = line.split("\t", 1)
            if _is_noise_word(word):             # drop letter-name / acronym noise
                continue
            ipa = ipa.replace(" ", "").strip()   # WikiPron space-separates phonemes
            if not ipa:
                continue
            # keep the first comma/semicolon segment: wiktextract senses are prose
            # ("fear, dread, fright, …") but concept grouping needs concise labels
            # ("fear") or every phrasing mints its own near-duplicate concept.
            word_glosses = [g.split(",")[0].split(";")[0].strip() or None
                            for g in (glosses.get(word.strip()) or [])] or [None]
            for g in word_glosses:               # >1 gloss -> entries merge into one Word's gloss_set
                entries.append({
                    "glottocode": meta["glottocode"], "ipa": ipa,
                    "gloss": g, "concepticon_id": None, "source": SOURCE["id"],
                })
    return {"sources": [SOURCE], "languages": languages, "entries": entries}
