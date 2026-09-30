"""Chance baseline for shared shapes (roadmap B1).

The Meanings view shows how many language families use one shape for one
meaning. Whether that is more than chance depends on how common the shape is in
those languages, so the baseline is computed from the data itself: shuffle each
language's words among its own meanings, many times, and count again.

The shuffle keeps every language's sounds and every language's meanings; it
breaks only the pairing between them. Families, not languages, are counted, so
an inherited word shared by a hundred related languages counts once. Beyond the
band still does not mean "not inherited" or "sound symbolism" — it means the
pairing is not what the inventories alone would give. No similarity score is
derived from it.
"""

from __future__ import annotations

import random
from collections import defaultdict

RUNS = 200       # shuffles per build; the 5–95% band of 200 draws is stable to ±1 family
MIN_FAMILIES = 2  # a pair one family uses is not a shared shape


def chance_bands(concepts: dict, families: list[str], runs: int = RUNS, seed: int = 0) -> dict:
    """{concept: {shape: (observed, lo, hi, top)}} for every meaning–shape pair
    at least MIN_FAMILIES families share. lo/hi = 5th/95th percentile of the
    families sharing it across `runs` within-language shuffles — the band to
    show; top = the most any shuffle gave. "Beyond chance" is observed > top:
    with ~1,100 pairs tested, the 95th percentile alone would pass ~55 by
    chance, beating every one of 200 shuffles passes about 1 in 200."""
    fam = [f or f"lang:{i}" for i, f in enumerate(families)]   # no family given: counts alone
    by_lang: dict[int, tuple[list, list]] = defaultdict(lambda: ([], []))
    observed: dict[tuple, set] = defaultdict(set)
    for ckey, c in concepts.items():
        for li, shape, *_ in c["entries"]:
            by_lang[li][0].append(ckey)
            by_lang[li][1].append(shape)
            observed[(ckey, shape)].add(fam[li])
    tested = {p for p, fs in observed.items() if len(fs) >= MIN_FAMILIES}

    null: dict[tuple, list[int]] = {p: [] for p in tested}
    rng = random.Random(seed)
    langs = sorted(by_lang)
    for _ in range(runs):
        hits: dict[tuple, set] = defaultdict(set)
        for li in langs:
            meanings, shapes = by_lang[li]
            shuffled = shapes[:]
            rng.shuffle(shuffled)
            for pair in zip(meanings, shuffled):
                if pair in tested:
                    hits[pair].add(fam[li])
        for p in tested:
            null[p].append(len(hits.get(p, ())))

    bands: dict[str, dict] = defaultdict(dict)
    for (ckey, shape), draws in null.items():
        draws.sort()
        lo, hi = draws[int(0.05 * (runs - 1))], draws[int(0.95 * (runs - 1))]
        bands[ckey][shape] = (len(observed[(ckey, shape)]), lo, hi, draws[-1])
    return dict(bands)
