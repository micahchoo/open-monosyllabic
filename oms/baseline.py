"""Chance baseline for shared shapes (roadmap B1, recalibrated 2026-10-01).

The Meanings view shows how many language families use one shape for one
meaning. Whether that is more than chance depends on how common the shape is
in those languages, so the null is the data itself: each language's words
shuffled among its own meanings. The shuffle keeps every language's sounds and
meanings and breaks only the pairing between them.

Until 2026-10-01 this ran 200 shuffles and called a pair "beyond chance" when it
beat all of them, testing only pairs already seen in 2+ families. That selects
on the outcome: on data shuffled so it holds NO real link, the same procedure
still passed ~260 pairs (the audit's null-as-observed replicates), while the UI
said ~14. Two changes fix it:

1. The shuffle distribution is computed exactly, not sampled. In a language
   with N words, a meaning written k times, and a shape occurring n times, the
   shuffle gives that meaning that shape with probability 1 - C(N-n, k)/C(N, k).
   Languages are shuffled independently, so a family shares the pair with
   probability 1 - prod(1 - p_language), and the number of families sharing it
   is a sum of independent Bernoullis (Poisson-binomial): its tail is exact.
2. Every meaning–shape pair that MIN_COULD or more families could share under
   the shuffle is a hypothesis, observed or not. "Beyond chance" is the
   Benjamini–Hochberg cut at a 5% false-discovery rate over all of them, so
   about 1 in 20 marked pairs may still be chance — and the UI says so.

Families, not languages, are counted, so a word inherited by a hundred related
languages counts once. Beyond the band still does not mean "not inherited" or
"sound symbolism"; loans and nursery words pass too. No similarity score is
derived from it.
"""

from __future__ import annotations

from collections import Counter, defaultdict

FDR = 0.05
MIN_FAMILIES = 2  # a pair one family uses is not a shared shape
# A pair is a hypothesis only if at least this many families COULD share it:
# some language of each has the meaning and, somewhere among its words, the
# shape. That depends on the inventories, not on the pairing the shuffle
# breaks, so filtering on it keeps the false-discovery rate valid (independent
# filtering). 5 matches the heatmap's MIN_FAMILIES. Measured 2026-10-01: 2, 3,
# 5 and 8 give 2, 3, 4 and 2 pairs beyond chance — the verdict does not hang on it.
MIN_COULD = 5


def _hit_probability(n_words: int, k_meaning: int, n_shape: int) -> float:
    """P(at least one of a meaning's k words gets the shape) when the language's
    N words are shuffled: 1 - C(N-n, k) / C(N, k)."""
    miss = 1.0
    for i in range(k_meaning):
        if n_words - n_shape - i <= 0:
            return 1.0
        miss *= (n_words - n_shape - i) / (n_words - i)
    return 1.0 - miss


def _poisson_binomial(ps: list[float]) -> list[float]:
    """Distribution of the number of successes among independent Bernoullis."""
    dist = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dist) + 1)
        for j, q in enumerate(dist):
            nxt[j] += q * (1 - p)
            nxt[j + 1] += q * p
        dist = nxt
    return dist


def _quantile(dist: list[float], f: float) -> int:
    acc = 0.0
    for j, q in enumerate(dist):
        acc += q
        if acc >= f - 1e-12:
            return j
    return len(dist) - 1


def chance_bands(concepts: dict, families: list[str], fdr: float = FDR) -> tuple[dict, dict]:
    """({concept: {shape: (observed, lo, hi, q)}}, summary) for every meaning–shape
    pair at least MIN_FAMILIES families share. lo/hi = 5th/95th percentile of
    the families that would share it under the shuffle; q = Benjamini–Hochberg
    adjusted p-value over every pair the shuffle could make shared; "beyond
    chance" is q <= fdr. summary = {"hypotheses", "tested", "beyond", "fdr"}."""
    fam = [f or f"lang:{i}" for i, f in enumerate(families)]   # no family given: counts alone
    words: dict[int, list[tuple[str, str]]] = defaultdict(list)
    observed: dict[tuple, set] = defaultdict(set)
    for ckey, c in concepts.items():
        for li, shape, *_ in c["entries"]:
            words[li].append((ckey, shape))
            observed[(ckey, shape)].add(fam[li])

    # per language: word count, meaning multiplicities, shape multiplicities
    stats = {li: (len(ws), Counter(c for c, _ in ws), Counter(s for _, s in ws)) for li, ws in words.items()}

    # hypotheses: pairs that 2+ families could share (some language of each has
    # both the meaning and the shape). Counted with integer pair ids.
    cid = {c: i for i, c in enumerate(concepts)}
    sid: dict[str, int] = {}
    for _, _, sc in stats.values():
        for s in sc:
            sid.setdefault(s, len(sid))
    ns = len(sid) or 1
    by_family: dict[str, list[int]] = defaultdict(list)
    for li in stats:
        by_family[fam[li]].append(li)
    could: Counter = Counter()
    for lis in by_family.values():
        pairs: set[int] = set()
        for li in lis:
            _, mc, sc = stats[li]
            ss = [sid[s] for s in sc]
            for c in mc:
                base = cid[c] * ns
                pairs.update(base + s for s in ss)
        could.update(pairs)
    hypotheses = sum(1 for v in could.values() if v >= MIN_COULD)

    tested = [p for p, fs in observed.items()
              if len(fs) >= MIN_FAMILIES and could[cid[p[0]] * ns + sid[p[1]]] >= MIN_COULD]
    langs_with_meaning: dict[str, set] = defaultdict(set)
    langs_with_shape: dict[str, set] = defaultdict(set)
    for li, (_, mc, sc) in stats.items():
        for c in mc:
            langs_with_meaning[c].add(li)
        for s in sc:
            langs_with_shape[s].add(li)

    rows = []
    for ckey, shape in tested:
        miss: dict[str, float] = defaultdict(lambda: 1.0)
        for li in langs_with_meaning[ckey] & langs_with_shape[shape]:
            n, mc, sc = stats[li]
            miss[fam[li]] *= 1 - _hit_probability(n, mc[ckey], sc[shape])
        dist = _poisson_binomial([1 - m for m in miss.values()])
        obs = len(observed[(ckey, shape)])
        p = min(1.0, sum(dist[obs:]))
        rows.append((p, ckey, shape, obs, _quantile(dist, 0.05), _quantile(dist, 0.95)))

    # Benjamini–Hochberg over all hypotheses; untested ones (fewer than 2
    # families observed) are treated as p = 1, which only makes this stricter.
    # Pairs fewer than MIN_COULD families could share get no band and no verdict.
    rows.sort()
    m = max(hypotheses, len(rows), 1)
    q_running, qs = 1.0, [0.0] * len(rows)
    for rank in range(len(rows), 0, -1):
        q_running = min(q_running, rows[rank - 1][0] * m / rank)
        qs[rank - 1] = q_running
    bands: dict[str, dict] = defaultdict(dict)
    beyond = 0
    for (p, ckey, shape, obs, lo, hi), q in zip(rows, qs):
        bands[ckey][shape] = (obs, lo, hi, round(q, 6))
        beyond += q <= fdr
    return dict(bands), {"hypotheses": hypotheses, "tested": len(rows), "beyond": beyond, "fdr": fdr}
