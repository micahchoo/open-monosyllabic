"""WikiPron ingestion adapter — the MINED tier (IMPLEMENTATION-STRATEGY Phase 5).

WikiPron (github CUNY-CL/wikipron) mines word→IPA pairs from Wiktionary: one TSV
per language/script, lines of `word<TAB>ipa` (ipa space-separated phonemes). No
gloss, no Concepticon. This is the route to families with NO CLDF coverage —
Yoruboid, Igboid, Chadic beyond single tokens — so it is the key to West Africa.

Tier = `mined`; licence = CC-BY-SA-3.0 (Wiktionary-derived; gate PASS, share-alike
attaches). Reads `config/wikipron-langmap.json`, mapping each TSV's ISO-639-3 code to a Glottocode
+ metadata (WikiPron keys on ISO, the catalog keys on Glottocode). Forms-only:
Words/glosses are absent, so these languages appear as Forms with no example Words
— exactly the graceful degradation the domain model was built for.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

SOURCE = {"id": "wikipron", "tier": "mined", "license": "CC-BY-SA-3.0", "kind": "dictionary"}


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
    # Conjunct/ligature pages (ന്ധ "ligature of na and dha"): all-Brahmic, joined by
    # a virama, with NO vowel anywhere (no independent vowel, no vowel sign). Real
    # words always carry a vowel character or skip the virama (inherent vowel: कल);
    # a vowel-less virama cluster is a letter entry whose "pronunciation" is just
    # the letter name with an epenthetic vowel (shipped /n̪d̪ʱɐ/ as a Malayalam word).
    if w and all(0x0900 <= ord(c) < 0x0E00 for c in w):
        names = [unicodedata.name(c, "") for c in w]
        if any("VIRAMA" in n for n in names) and not any("VOWEL" in n for n in names):
            return True
    return False


# Hand-made (families, coordinates), so it lives under git — not beside the TSVs
# in the gitignored sources/ clone.
LANGMAP = Path(__file__).resolve().parent.parent / "config" / "wikipron-langmap.json"


def load(wikipron_dir: str | Path, langmap_path: str | Path = LANGMAP) -> dict:
    d = Path(wikipron_dir)
    langmap = json.loads(Path(langmap_path).read_text(encoding="utf-8"))
    langmap.pop("_note", None)
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
            "family": meta.get("family", ""),
        })
        for line in tsv.read_text(encoding="utf-8").splitlines():
            if not line.strip() or "\t" not in line:
                continue
            word, ipa = line.split("\t", 1)
            if _is_noise_word(word):             # drop letter-name / acronym noise
                continue
            ipa = ipa.strip()   # WikiPron space-separates segments; the boundaries are kept
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
                    "segmented": True,
                })
    return {"sources": [SOURCE], "languages": languages, "entries": entries}
