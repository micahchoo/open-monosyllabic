# Open Monosyllabic — Ingestion Study

**Date:** 2026-07-02
**Scope:** Which lexical datasets the Open Monosyllabic pipeline can ingest, ranked by open-monosyllable yield and Global-South mission-fit, gated by ADR-0002 licence rules.
**Method:** Synthesis of four parallel research strands (lexibank-catalog, beyond-lexibank-cldf, yield-typology, mission-and-licence). Live verification was via the GitHub API + raw `cldf-metadata.json`/`.zenodo.json` reads this session (2026-07-04); items relying on training knowledge (cutoff Jan 2026) are marked **unverified**.

---

## 1. Executive Summary

The pipeline already ingests 4 CLDF datasets (walworthpolynesian, castrosui, halenepal, bodtkhobwa → 63 languages) and correctly blocks grollemundbantu (CC-BY-NC). The reachable space is far larger and mostly gate-clean.

- **Ingestible NOW (zero adapter work):** the entire `lexibank` GitHub org is CLDF-Wordlist-ready — 191 repos, ~155 of them CC-BY-4.0. Every one is a drop-in for the existing adapter; **the only gate that matters is licence.** A clean ingestion plausibly lifts the catalog from 63 languages toward **~2,000–2,400 varieties** (unverified estimate — derived from the ~155/191 CC-BY norm, not a computed Glottolog join; the Form-bearing count after openness filtering will be lower and skewed toward high-yield families).
- **Biggest opportunity:** `lexibank/abvd` (Austronesian Basic Vocabulary Database, ~1000+ varieties, CC-BY-4.0, verified) — the single largest high-yield Global-South target, and the adapter is already proven on the Oceanic sibling walworthpolynesian. Behind it: the Hmong-Mien quartet (the purest CV+tone space, no codas), the Loloish/Ngwi cluster, Sinitic, and `bantubvd` as the licence-clean Bantu foothold.
- **Critical licence discovery (LICENCE INVERSION):** the GitHub API's `license` field mostly resolves correctly here, so `NOASSERTION` does **not** mean "unread, probably CC-BY." Metadata reads found three high-yield Global-South datasets that the API masked as NOASSERTION but are actually NC/ND: **luangthongkumkaren** (CC-BY-NC-ND), **sawkatokaleya** (CC-BY-NC), **vanuatuvoices** (CC-BY-NC). Always read `cldf-metadata.json` before clearing a NOASSERTION/null repo.
- **Biggest gaps/pains:** Bantu-scale Africa is NC-gated — `grollemundbantu` (424 languages) and `papuanvoices` (IPA-quality Papuan) are both mission-critical and BLOCKED, with no CC-BY substitute at their scale. West-African Yoruboid/Volta-Niger (structurally the richest African tonal-CV family after Bantu) has thin/no CLDF coverage and likely needs a new adapter.
- **Biggest yield lever outside CLDF:** WikiPron (3M+ pairs, 165+ langs) and Wiktextract/Kaikki (1000+ langs) — both CC-BY-SA (gate PASS, share-alike attaches), both need a new adapter.

---

## 2. Tier-1 ROADMAP — Ingest NOW

CLDF-ready + licence-clean (verified or Lexibank CC-BY norm) + high open-monosyllable yield + Global-South mission-fit. Ranked.

| # | Dataset | Coverage | Licence | Yield | Why |
|---|---------|----------|---------|-------|-----|
| 1 | `lexibank/abvd` | Austronesian/Oceanic, ~1000+ varieties | CC-BY-4.0 ✓ | High | Largest single high-yield Global-South pool; Oceanic core is canonical open CV/CVV, no coda; adapter already proven on walworthpolynesian sibling |
| 2 | `lexibank/chenhmongmien` | Hmong-Mien, 25 varieties (Chen 2012) | CC-BY-4.0 ✓ | High | Purest CV+tone space — most varieties allow NO coda; obligatorily monosyllabic morphemes |
| 3 | `lexibank/bantubvd` | Bantu, 10 varieties (Greenhill & Gray 2015) | CC-BY-4.0 ✓ | High | Licence-clean Bantu foothold; the ALLOWED rescue for the NC-blocked grollemundbantu (covers ~2% of its languages but under a passing licence) |
| 4 | `lexibank/castroyi` | Yi/Nisoic, Heqing (Castro 2010) | CC-BY-4.0 | High | Loloish/Ngwi = open CV(V) tonal, no coda; prime source; Global-South SW China |
| 5 | `lexibank/liusinitic` | Sinitic, ~18–40 dialects (Liú 2007) | CC-BY-4.0 ✓ | High/Med | Tonal monosyllabic Sinitic; large open-CV(V)+tone subset (codas limited to nasals) |
| 6 | `lexibank/wanghmongmien` | Hmong-Mien (Wang 2015) | CC-BY-4.0 ✓ | High | Open-CV tonal monosyllables; same coda-less profile as chenhmongmien |
| 7 | `lexibank/transnewguineaorg` | Trans-New Guinea + Papuan, ~1000+ | CC-BY-4.0 ✓ | Medium | Largest licence-clean lever on the Papuan gap; yield mixed but honest coverage of an under-documented macroarea |
| 8 | `lexibank/mcd` | Micronesian Comparative Dictionary | CC-BY-4.0 | High | Micronesian Oceanic, open CV; Global-South Pacific |
| 9 | `lexibank/tryonsolomon` | Solomon Islands (Tryon & Hackman 1983) | CC-BY-4.0 | High | Oceanic + some Papuan; strong open-syllable yield, under-documented Melanesia |
| 10 | `lexibank/leejaponic` | Japonic (Lee & Hasegawa) | CC-BY-4.0 | High | Japonic moraic open-CV; strong yield (bimoraic minimality → CVV-heavy) |
| 11 | `lexibank/starostinkaren` | Karen Swadesh lists (Starostin) | CC-BY-4.0 | High | Open-syllable tonal Tibeto-Burman; the OPEN alternative to the NC-ND-blocked luangthongkumkaren |
| 12 | `lexibank/tls` | Tanzania Language Survey (Bantu) | CC-BY-4.0 | High | Broad Tanzanian Bantu, open CV; strong East-Africa coverage — a second Bantu win beyond bantubvd |
| 13 | `lexibank/chaconbaniwa` | Arawakan, NW Amazonia | CC-BY-4.0 ✓ | Medium | Largely open-CV; rare licence-clean Amazonian coverage |
| 14 | `lexibank/chaconcolumbian` | Tukanoan, NW Amazonia (Chacon 2017) | CC-BY-4.0 ✓ | Medium | Simple CV + nasal harmony; rare clean Amazonian win |

**Verified CC-BY this session (✓):** abvd, chenhmongmien, wanghmongmien, bantubvd, liusinitic, transnewguineaorg, zgraggenmadang, chaconcolumbian, chaconbaniwa, servamalagasy, galuciotupi, WOLD, Dravlex, DiACL. Unmarked rows follow the Lexibank CC-BY norm but were not individually re-read — read `cldf-metadata.json dc:license` at pin time.

### Clone commands (top ~10)

```sh
git clone --depth 1 https://github.com/lexibank/abvd sources/abvd
git clone --depth 1 https://github.com/lexibank/chenhmongmien sources/chenhmongmien
git clone --depth 1 https://github.com/lexibank/bantubvd sources/bantubvd
git clone --depth 1 https://github.com/lexibank/castroyi sources/castroyi
git clone --depth 1 https://github.com/lexibank/liusinitic sources/liusinitic
git clone --depth 1 https://github.com/lexibank/wanghmongmien sources/wanghmongmien
git clone --depth 1 https://github.com/lexibank/transnewguineaorg sources/transnewguineaorg
git clone --depth 1 https://github.com/lexibank/mcd sources/mcd
git clone --depth 1 https://github.com/lexibank/tryonsolomon sources/tryonsolomon
git clone --depth 1 https://github.com/lexibank/leejaponic sources/leejaponic
```

---

## 3. Tier-2 — Ingestible, Lower Priority

Medium yield, smaller coverage, reconstruction-tier, or needs a metadata licence read before clearing.

**High-yield but needs metadata check (verify `cldf-metadata.json` — do NOT assume CC-BY; these are exactly where NC/ND hides):**
- `lexibank/abvdsouthernoceanic` — Southern Oceanic (Vanuatu/New Caledonia). API null, metadata not found at common paths. High yield BUT Southern Oceanic is frequently NC-blocked (cf. vanuatuvoices) — verify branch/path first.
- `lexibank/williamsonbenuecongo` — Benue-Congo, Nigeria. API null. High open-syllable Global-South yield if clean.
- `lexibank/huismanjaponic` — Japonic. API null. High open-CV yield.
- `lexibank/beidazihui` — Sinitic character readings (Zenodo 2632669). High tonal-CV yield if clean.
- `lexibank/sabor` — South American borrowing sample. High mission value (Amazonian/Andean); licence unread this pass.
- `lexibank/dhakalsouthwesttibetic` — SW Tibetic; medium (Tibetic has codas). Complements halenepal/bodtkhobwa.

**Medium yield, cleared or norm-CC-BY:**
- `lexibank/starostinhmongmien`, `lexibank/hsiuhmongmien` — Hmong-Mien; open-CV tonal, high yield actually — Tier-1-adjacent, listed here only for family de-duplication after chen/wang.
- `lexibank/yanglalo`, `lexibank/lamanisoic`, `lexibank/yangyi` — more Loloish/Ngwi; open-CV tonal, high yield; ingest after castroyi to broaden the family.
- `lexibank/wangbai`, `lexibank/allenbai`, `lexibank/zhaobai` — Bai; mostly open-CV tonal with some nasal codas → medium.
- `lexibank/beidasinitic`, `lexibank/beidazihui` — Sinitic; monosyllabic, pervasive nasal codas cut open share → medium.
- `lexibank/mitterhoferbena` — Bena (Bantu, Tanzania); open CV, Global-South.
- `lexibank/smithborneo` — Bornean Austronesian, open-syllable; under-documented Indonesia/Malaysia.
- `lexibank/polyglottaafricana` — Koelle 1854, ~100–150 African varieties; broadest licence-clean African count in Lexibank BUT 1854 transcription is noisy → medium yield, low confidence.
- `lexibank/zgraggenmadang` — Madang Papuan (verified CC-BY); complements transnewguineaorg.
- `lexibank/galuciotupi` + `tupian-language-resources/tuled` — Tupían, Amazonia; many open CV; galuciotupi verified CC-BY, confirm TuLeD.
- `lexibank/wold` (verified CC-BY), `lexibank/dravlex` (verified, Dravidian S-Asia), `lexibank/leekoreanic` (Korean, rich codas → medium-low).

**Reconstruction-tier (proto forms — flag Form-type, treat as reconstructions not attested speech):**
- `lexibank/tlopo` (Proto-Oceanic), `lexibank/acd` (Austronesian Comparative Dictionary — mixes reflexes + reconstructions), and the proto Sino-Tibetan repos (`sagartst`, `zhangst`, `peirosst`, `mannburmish`, `hillburmish`). High open-CV yield but asterisked.

**Aggregators:** `clics/clics3` bundles 30 individual lexibank CLDF Wordlists (castrosui, bodtkhobwa already ingested came from here). Not a separate source — enumerate the 30, gate each, ingest the open-syllable members (bantubvd, beidasinitic, allenbai already covered above). Also `intercontinental-dictionary-series/ids` (329 varieties, verified CC-BY) — **caveat:** per-contributor transcription is often orthographic/broad-phonemic not consistent IPA; needs an "IPA vs orthography" triage before the openness classifier trusts it.

**Low yield, ingest only for contrast/completeness:** `lexibank/bowernpny` (Pama-Nyungan — simple CV but bimoraic minimality bans light monosyllables → near-zero yield, keep as a minimality control case), `lexibank/diacl` (IE + Caucasus, complex codas), `lexibank/lsi` (Linguistic Survey of India — huge breadth, mixed types, historical noise), `lexibank/northeuralex` (N Eurasia, CC-BY-SA vs CC-BY conflict, mostly complex-coda).

**Excluded despite passing the gate:** `lexibank/asjp` (CC-BY-4.0, 6,126 Glottocodes) — ASJPcode is a 41-symbol reduction (7 vowel classes, no length/tone) that merges contrastive segments, violating ADR-0002. Use ONLY as a coverage/GAP checklist (which Glottocodes have any attestation), never as a Form source.

---

## 4. NEEDS A NEW ADAPTER — High-Value Non-CLDF Sources

These are the biggest yield levers outside the lexibank org. None is CLDF; each needs adapter work described below.

**WikiPron (CUNY-CL/wikipron) — MODERATE effort, highest single yield.** 3M+ word/pronunciation pairs across 165+ languages (unverified counts — README figures), data CC-BY-SA-3.0 (gate PASS, share-alike attaches), code Apache-2.0. Format is per-language TSV (`word<TAB>IPA`, phonemic `*.tsv`). Adapter: parse TSV, map the WikiPron language code (Wiktionary/ISO) → Glottocode, synthesize `forms.csv`/`languages.csv`/`parameters.csv`. IPA is already space-segmented so CLTS canonicalization is light. No Concepticon linkage (glosses absent — **forms-only**). Rich in tonal/CV languages, so high open-monosyllable density.

**Wiktextract / Kaikki (tatuylonen/wiktextract, kaikki.org) — HEAVIER effort.** 1000+ languages, full Wiktionary as JSON with IPA + glosses; data dual CC-BY-SA + GFDL (elect BY-SA, gate PASS), code MIT. Adapter: stream the large JSON, pull IPA from the `sounds` field, filter to single tokens, map language → Glottocode. Glosses are free-text definition sentences — **no reliable gloss→Concepticon mapping at scale**, so ship as plain-text glosses / forms-only. Heaviest of the mined tier because of JSON scale and the messy `sounds` field.

**Generated tier — PanLex + Crúbadán → Epitran/Transphone (G2P).** Needs an orthographic-wordlist adapter PLUS a G2P pass; a language yields nothing unless it has BOTH a wordlist AND a G2P model (double gate; realistic ceiling ~2,000–4,000 form-bearing languages, unverified). **PanLex** (CC0, ~20M lexemes / ~9000 varieties) is the most permissive licence in the whole plan and the widest Global-South breadth, but entries are native-orthography lemmas with no IPA — adapter maps variety→Glottocode, single-token filter, script detection, then G2P. **Crúbadán** (~2000 langs, CC-BY per OLAC — confirm per-file; mirror early, site availability fluctuates) is a web-crawl coverage extender (XPF Corpus precedent). G2P engines: **Epitran** (~80–90 lang-script pairs, MIT) and **Transphone** (~7546 Glottolog langs but ~900 are nearest-language approximations, MIT) — output inherits the input wordlist's licence (facts doctrine). **Recommendation: EXCLUDE Transphone's ~900 approximated models from v1** — their unvalidated vowel/coda errors hit exactly the openness decision the pipeline exists to make.

**PHOIBLE (cldf-datasets/phoible) — validator adapter only, never a Form source (ADR-0002).** 3020 inventories / 2186 languages of standardized IPA segment inventories. A validator adapter would check which nucleus types (long/nasal vowels, diphthongs, syllabic Cs) and tones a language contrasts. CC-BY-SA-3.0 (site) vs CC-BY-4.0 (repo) conflict; no forms redistributed so SA does not attach to our output. Attribute anyway.

---

## 5. BLOCKED BY LICENCE — Mission Cost

ADR-0002 blocks CC-BY-NC / CC-BY-ND / research-only / unlicensed-no-metadata. The casualties concentrate exactly where the Global-South mission cares most.

| Dataset | Coverage | Licence (verified) | Mission cost | Alternative / ask |
|---------|----------|--------------------|--------------|-------------------|
| `lexibank/grollemundbantu` | 424 Bantu languages | CC-BY-NC-4.0 | **Largest single Global-South corpus in Lexibank, high open-CV yield, gone.** No CC-BY substitute at scale | `bantubvd` (10 langs) + `tls` + `polyglottaafricana` (~100 historical) partially cover. File upstream re-licensing ask (NC likely inherited from the 2015 Nature paper's supplementary terms, not the CLDF wrapper — success uncertain) |
| `lexibank/papuanvoices` | Papuan, IPA-quality phonetic | CC-BY-NC-4.0 | IPA-quality Papuan transcription — exactly what the CC-BY transnewguineaorg lacks | `transnewguineaorg` + `zgraggenmadang` (CC-BY) match coverage but not transcription quality |
| `lexibank/vanuatuvoices` | Vanuatu Oceanic (Sound-Comparisons) | CC-BY-NC-4.0 (API said NOASSERTION) | High open-monosyllable Oceanic yield, Global-South Vanuatu, blocked | Oceanic coverage via abvd/abvdoceanic; the specific Vanuatu phonetic set has no clean twin |
| `lexibank/sawkatokaleya` | Toka-Leya (Bantu, Zambia) | CC-BY-NC-4.0 (API NOASSERTION) | Global-South Bantu, open-CV, blocked | Route Bantu through bantubvd/tls |
| `lexibank/luangthongkumkaren` | Proto-Karen (Luangthongkum 2019) | CC-BY-NC-ND-4.0 (API NOASSERTION) | High-yield Karen, both NC and ND — hard block | `starostinkaren` (CC-BY) is the open alternative |

**The masking pattern is the load-bearing finding:** grollemundbantu, luangthongkumkaren, sawkatokaleya, and vanuatuvoices all show `NOASSERTION` on the GitHub API but are NC/ND in metadata. Any NOASSERTION/null repo MUST be metadata-checked; a minority hide real blocks. The three high-yield needs-metadata-check repos above (abvdsouthernoceanic, williamsonbenuecongo, beidazihui) are the next candidates to clear or discover as blocks.

---

## 6. YIELD TYPOLOGY — Family → Open-Monosyllable Yield

Grounded in WALS Ch.12 (only ~61/492 ≈ **12.5%** of sampled languages are "simple"/CV-only, where open monosyllables concentrate; ~56.5% moderately complex, ~30.9% complex) and the bimoraic word-minimality constraint (bans open LIGHT CV monosyllables, permits open BIMORAIC CVV). Open = vowel/diphthong nucleus, no coda.

**RICH (high-value targets — coda-less, mostly tonal, monomoraic OK):**
- **Hmong-Mien** — TOP. Most varieties allow NO coda (or nasal only), obligatorily monosyllabic, richly tonal. Purest CV+tone space.
- **Yoruboid / Volta-Niger** — strict CV, no codas, register tone. Structurally the richest African tonal family after Bantu, BUT thin CLDF coverage → sourcing gap / new adapter (see §7).
- **Bantu** — canonical open CV, codas rare/nasal-only; augment/bimoraic minimality favours open CVV. (Licence-split: bantubvd/tls clean, grollemundbantu NC.)
- **Austronesian / Oceanic / Polynesian** — dominantly open CV/CVV, best-covered family. Polynesian bimoraic minimality bans light CV but permits CVV → yield is CVV-heavy, not CV-light. **Record minimality as a per-language variable.**
- **Sinitic** — monosyllabic, tonal, codas limited to nasals (+ some -ʔ/-p/-t/-k in Min/Yue) → large open-CV(V)+tone subset.

**MEDIUM (monosyllabic + tonal, favourable, BUT coda-bearing → open subset is a fraction):**
- **Tai-Kadai / Kra-Dai** — heavy -p/-t/-k/-m/-n/-ŋ codas (castrosui already ingested).
- **Vietic / Austroasiatic** — split: Vietic coda-rich, Bahnaric/Katuic sesquisyllabic, Munda agglutinating.
- **Sino-Tibetan / Tibeto-Burman (non-Sinitic)** — heterogeneous: Loloish/Burmese lean open+tonal (higher), Kuki-Chin/Bodo-Garo/Kho-Bwa carry codas (lower). halenepal, bodtkhobwa already ingested.
- **Japonic** — near-pure CV but bimoraic minimality pushes content words to CVV/CVN.
- **Dravidian, Chadic, Koreanic, Tukanoan, Arawakan, Tupían** — moderate CV core with productive codas.

**POOR (deprioritise):**
- **Pama-Nyungan** — instructive false positive: simple CV(C) syllables BUT disyllabic word-minimality bans monosyllables outright → near-zero yield. Use as a minimality control case.
- **Quechuan, Cariban** — CV(C) with productive codas, no monosyllabic bias.
- **Salishan, NW Caucasian, Athabaskan/Dene** — extreme clusters, huge consonant inventories; WALS "complex"; near-zero yield.
- **Germanic / heavy-coda IE** — archetype of closed-syllable; open monosyllables are a small function-word set. Contrast baseline only.

**Caveat on all yield figures:** these are structural priors (syllable-type + minimality), NOT measured counts. Confirm per-language by running the pipeline's openness classifier on each ingested set.

---

## 7. COVERAGE GAPS — Honest Limits After Clean Ingestion

Even after ingesting every licence-clean CLDF set plus the mined/generated tiers, these remain thin:

1. **Bantu-scale Africa** — NC-gated. The 424-language grollemundbantu is the gap; bantubvd (10) + tls + polyglottaafricana (~100, noisy 1854) are partial. The single biggest mission casualty.
2. **West-African Niger-Congo / Yoruboid / Volta-Niger** — high-yield tonal-CV, but only ASJP (non-IPA) coverage in the clean pool. Needs a new adapter (Wiktextract/Kaikki Yoruba, or dedicated elicitation) or a licence-clean IPA source. **Highest-value roadmap item currently un-ingestible in CLDF form.**
3. **Papuan** — transnewguineaorg + zgraggenmadang (CC-BY) give coverage but not IPA-quality transcription; the phonetic-quality papuanvoices is NC-blocked.
4. **Amazonian** — thin but improving: chaconcolumbian (Tukanoan), chaconbaniwa (Arawakan), galuciotupi/TuLeD (Tupían), sabor cover fragments under CC-BY. Quechuan/Cariban are low-yield anyway.
5. **Australian (Pama-Nyungan)** — bowernpny is CC-BY and huge, but structurally yields near-zero (bimoraic minimality). A structural absence, not a data gap.
6. **Khoisan** — largely absent from CLDF and typologically poor-yield (clicks + complex onsets). A double gap; low priority.

Use ASJP (6,126 Glottocodes) purely as a GAP-audit instrument to mechanically list which mission-priority languages lack any licence-clean IPA attestation.

---

## 8. Recommended Sequence

Ingest the proven-adapter high-yield core first: `abvd` (largest single win, adapter already validated on the Polynesian sibling), then the coda-less RICH families where yield is purest — the Hmong-Mien pair (`chenhmongmien`, `wanghmongmien`), the Loloish/Ngwi cluster (`castroyi`, then `yanglalo`/`lamanisoic`/`yangyi`), Sinitic (`liusinitic`), and the licence-clean Bantu foothold (`bantubvd` + `tls`); add the Pacific Oceanic breadth (`mcd`, `tryonsolomon`) and Japonic (`leejaponic`), then the mixed-yield-but-mission-critical Papuan (`transnewguineaorg`, `zgraggenmadang`) and Amazonian (`chaconbaniwa`, `chaconcolumbian`) sets. Before each ingest, read `cldf-metadata.json dc:license` for any NOASSERTION/null repo (never trust the GitHub API) — this is where NC/ND masks. In parallel, scope the WikiPron adapter (moderate effort, biggest yield lever, unlocks Yoruboid and the tonal long-tail) as the first non-CLDF workstream, and file the upstream re-licensing ask on grollemundbantu. Defer Transphone-approximated G2P, ASJP-as-source (keep it as a gap checklist only), and the POOR-tier families (Pama-Nyungan, Salishan, NW-Caucasian) to contrast/validation roles.
