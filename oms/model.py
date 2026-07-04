"""Domain model (CONTEXT.md) — Language, Form, Word, Confidence Tier, Source.

Faithful to CONTEXT.md: separate-per-language Forms (no shared Shape entity);
Shape is the tone-blind canonical string, a query-time grouping key. Form identity
= (glottocode + canonical segmental). Confidence Tier ratchets up only; Sources
are retained, one preferred. Classification Confidence is the second honesty axis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Confidence Tier — source provenance, most→least trusted (CONTEXT.md).
TIERS = ("curated", "mined", "generated")
_TIER_RANK = {t: i for i, t in enumerate(TIERS)}  # 0 = best


def tier_better(a: str, b: str) -> bool:
    """True if tier a is strictly more trusted than b (curated < mined < generated)."""
    return _TIER_RANK[a] < _TIER_RANK[b]


def ratchet(current: str, incoming: str) -> str:
    """Confidence Tier ratchets UP only (CONTEXT.md Lifecycle): keep the best seen."""
    return incoming if tier_better(incoming, current) else current


@dataclass(frozen=True)
class Source:
    id: str
    tier: str          # one of TIERS
    license: str       # SPDX-ish, cleared at Phase-0 gate


@dataclass
class Language:
    glottocode: str
    name: str
    macroarea: str          # Glottolog macroarea
    latitude: float | None
    longitude: float | None
    doc_status: str         # well | moderate | under  (distinguishes no-data from absent)
    prosodic_type: str      # permits-open-light | bimoraic-min | unknown


@dataclass
class Word:
    """A Form + a specific tone + meaning (CONTEXT.md). Homophones collapse: same
    (form, tone) is one Word with a merged gloss_set."""
    form_key: str
    tone: str
    gloss_set: list[dict] = field(default_factory=list)  # [{gloss, concepticon_id|None, source_id}]
    tier: str = "generated"
    sources: list[str] = field(default_factory=list)


@dataclass
class Form:
    """An open monosyllable as attested in ONE language (the backbone entity)."""
    glottocode: str
    segmental: str                       # canonical, tone-blind — the Shape string
    tones: set[str] = field(default_factory=set)
    tier: str = "generated"              # preferred (ratcheted) source tier
    sources: list[str] = field(default_factory=list)
    preferred_source: str | None = None
    classification_confidence: str = "high"   # high | medium | low
    under_review: bool = False
    nucleus_type: str = "monophthong"
    onset_class: str = "none"
    nucleus_bucket: str = "other"
    words: list[Word] = field(default_factory=list)

    @property
    def key(self) -> str:
        """Form identity = (glottocode + canonical segmental) (CONTEXT.md Identity)."""
        return f"{self.glottocode}|{self.segmental}"

    @property
    def shape(self) -> str:
        """Shape grouping key = the canonical segmental alone (cross-language)."""
        return self.segmental
