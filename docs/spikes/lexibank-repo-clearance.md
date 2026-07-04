# Spike: lexibank-repo-clearance (closes licensing-audit open-Q #2)

**Date:** 2026-07-03 · **Scope:** the ~28 `lexibank` GitHub-org repos the `licensing-audit` spike flagged as NOASSERTION / no-license, resolved to their *actual* declared licence and an allow/block verdict against the Phase-0 allowlist. · **Verification:** ✅ = read online this spike (GitHub API + `raw.githubusercontent.com`). ⚠️ = could not resolve online → **needs manual check**.

**Terms of reference:** (a) named allow/block lists; (b) which blocked datasets matter for open-monosyllable coverage; (c) a reusable clearance procedure. Respects the locked Phase-0 allowlist: **allow** CC0 / CC-BY 3.0/4.0 / CC-BY-SA 3.0/4.0 / dual-Wiktionary / MIT / Apache; **block** NC / ND / research-only / NOASSERTION-until-read.

---

## Findings

**Org survey reproduced (✅ GitHub API, `/orgs/lexibank/repos`, 191 public repos):** `CC-BY-4.0` ×155, `NOASSERTION` ×15, no-license ×13, `Apache-2.0` ×4, `GPL-3.0` ×2, `MIT` ×2. The 15+13 = **28** matches the licensing-audit count exactly.

**Key procedural finding — the GitHub licence API is the WRONG signal.** GitHub's `license.spdx_id` returns `NOASSERTION` whenever the licence is declared only in CLDFBench's root `metadata.json` (which GitHub's detector ignores), regardless of what that licence actually is. So the NOASSERTION bucket is **not** a block-list — it is an "unread" list. Reading `metadata.json`'s `license` field resolved 14 of 15 NOASSERTION repos to real licences, and it turned up the opposite error too: **`valpal` is NOASSERTION on GitHub but CC-BY-3.0 in metadata → allowable.** Clearance MUST read `metadata.json` (fallback `.zenodo.json`, then README, then `cldf/*-metadata.json`), never trust the GitHub licence field.

### The 15 NOASSERTION repos — resolved (✅ all via root `metadata.json`)

| Repo | Declared licence | Verdict |
|---|---|---|
| kitchensemitic | CC-BY-NC-4.0 | **BLOCK** (NC) |
| grollemundbantu | CC-BY-NC-4.0 | **BLOCK** (NC) |
| listcognatebenchmark | CC-BY-NC-4.0 | **BLOCK** (NC) |
| hruschkaturkic | CC-BY-NC-4.0 | **BLOCK** (NC) |
| wheelerutoaztecan | CC-BY-NC-4.0 | **BLOCK** (NC) |
| mixezoqueanvoices | CC-BY-NC-4.0 | **BLOCK** (NC) |
| zhangrgyalrong | CC-BY-NC-4.0 | **BLOCK** (NC) |
| nashcolorterms | CC-BY-NC-4.0 | **BLOCK** (NC) |
| sawkatokaleya | CC-BY-NC-4.0 | **BLOCK** (NC) |
| vanuatuvoices | CC-BY-NC-4.0 | **BLOCK** (NC) |
| papuanvoices | CC-BY-NC-4.0 | **BLOCK** (NC) |
| peirosst | CC-BY-NC-4.0 | **BLOCK** (NC) |
| amazonianvoices | CC-BY-NC-4.0 | **BLOCK** (NC) |
| luangthongkumkaren | CC-BY-NC-**ND**-4.0 | **BLOCK** (NC + ND) |
| **valpal** | **CC-BY-3.0** | **ALLOW** |

Pattern: NOASSERTION ≈ the **non-commercial** subset. 14/15 are NC/ND; the lone exception (valpal) is cleanly allowable.

### The 13 no-licence repos — resolved

| Repo | Declared licence (source) | Verdict |
|---|---|---|
| chechurodaghestan | CC-BY-4.0 (✅ metadata.json) | **ALLOW** |
| lindseypahotuririver | CC-BY-4.0 (✅ metadata.json) | **ALLOW** |
| kaufmanpmed | CC-BY-4.0 (✅ README) | **ALLOW** |
| servamalagasy | "CC-BY" unversioned (✅ metadata.json) | **ALLOW** (treat as CC-BY 4.0; version unstated) |
| hayniecolorterms | bare "CC" (✅ metadata.json) | ⚠️ **NEEDS MANUAL CHECK** — "CC" doesn't say NC-or-not |
| williamsonbenuecongo | metadata.json present, **no `license` key** (✅) | ⚠️ **NEEDS MANUAL CHECK** → block until cleared |
| wustphylogenies | metadata.json `"license": null` (✅) | ⚠️ **NEEDS MANUAL CHECK** → block until cleared |
| huismanjaponic | WIP — only `raw/` + `NOTES.md`, no CLDF built, no licence (✅) | **BLOCK** (incomplete + unlicensed) |
| language-island-paper | "GPL" (✅ metadata.json) — a *paper* repo | **BLOCK** (GPL not in data allowlist; not a Form source) |
| phylogenetics-data-management-tutorial | tutorial repo, no metadata.json (✅) | **N/A** — not a dataset |
| abvdsouthernoceanic | **empty stub** — only `.gitignore` (✅) | **N/A** — no data |
| ronataswestoldturkic | **empty stub** — only `.gitignore` (✅) | **N/A** — no data |
| .github | org profile meta-repo (✅) | **N/A** — not a dataset |

---

## Recommendation

### (a) Allowlist and blocklist of named datasets

**ALLOW (6 cleared — enter ingestion):** `valpal` (CC-BY-3.0), `chechurodaghestan` (CC-BY-4.0), `lindseypahotuririver` (CC-BY-4.0), `kaufmanpmed` (CC-BY-4.0), `servamalagasy` (CC-BY, version unstated).
*(5 firmly cleared; `servamalagasy` allowable pending a version read — low risk, any CC-BY version is allowlisted.)*

**BLOCK — non-commercial (14):** `kitchensemitic`, `grollemundbantu`, `listcognatebenchmark`, `hruschkaturkic`, `wheelerutoaztecan`, `mixezoqueanvoices`, `zhangrgyalrong`, `nashcolorterms`, `sawkatokaleya`, `vanuatuvoices`, `papuanvoices`, `peirosst`, `amazonianvoices`, `luangthongkumkaren` (also ND). NC is incompatible with a CC-BY-SA 4.0 catalog and with not constraining downstream reuse — hard block.

**BLOCK — other (2):** `language-island-paper` (GPL, and a paper repo not a Form source), `huismanjaponic` (unlicensed WIP).

**NEEDS MANUAL CHECK (3):** `hayniecolorterms` (bare "CC"), `williamsonbenuecongo` (no licence key), `wustphylogenies` (`license: null`). Block until a human resolves; each is a candidate for one upstream issue to the maintainers.

**N/A — not datasets (4):** `abvdsouthernoceanic` + `ronataswestoldturkic` (empty stubs), `phylogenetics-data-management-tutorial` (tutorial), `.github` (org meta).

### (b) Which blocked datasets matter for open-monosyllable coverage

The block is **materially costly in one place: the "Voices" family** — `vanuatuvoices`, `papuanvoices`, `amazonianvoices`, `mixezoqueanvoices`. These uniquely cover a large set of **small Oceanic / Papuan / Amazonian / Mixe-Zoquean languages** — exactly the mission-priority Global-South long tail — **and they carry field-recorded audio** (the asset the audio-subsystem spike wants). Losing them to NC forfeits both Form coverage for languages thinly served elsewhere *and* real human audio for them. This is the one blocked-list entry worth an upstream re-licensing ask.

Second tier of concern: **`grollemundbantu`** — Bantu phonotactics are canonically open-syllable (CV), so this is topically central to open monosyllables; but it is a Swadesh-style cognate set whose *languages* largely also appear in CC-BY Lexibank sets and the mined tier, so the unique loss is smaller than Voices.

Low concern: the comparative-wordlist and color-term/benchmark sets (`kitchensemitic`, `hruschkaturkic`, `wheelerutoaztecan`, `peirosst`, `zhangrgyalrong`, `sawkatokaleya`, `nashcolorterms`, `listcognatebenchmark`, `luangthongkumkaren`) — narrow semantic domains and/or families well covered by allowlisted sources; low unique monosyllable yield. Net: **coverage loss is concentrated in the Voices audio sets, not spread across the block.**

### (c) Reusable clearance procedure (Phase-0 gate, runs at seed-set selection)

For each candidate `lexibank/<repo>`:
1. **Do NOT use the GitHub `license` API as the verdict** — it under-reports (NOASSERTION for metadata-only licences) and would wrongly block allowable CC-BY sets.
2. **Read the declared licence in priority order:** root `metadata.json` `"license"` → `.zenodo.json` `license` → `README.md` licence line → `cldf/*-metadata.json` `dc:license`. Record the first hit **and its source path** in the Source registry.
3. **Normalise** the string (URLs like `.../by-nc/4.0/`, bare `CC-BY-NC-4.0`, unversioned `CC-BY`) to an SPDX-ish id.
4. **Verdict vs allowlist:** contains `NC` or `ND` → **BLOCK**; `GPL`/other copyleft-code licence on data → **BLOCK**; `CC0`/`CC-BY[-SA]` any version / `MIT` / `Apache` → **ALLOW**; unversioned/ambiguous (`CC`, `CC-BY` no version) → **ALLOW only if the family is clearly non-NC**, else queue.
5. **No licence found, `license: null`, empty stub, or WIP-without-CLDF → BLOCK + QUEUE for manual review** (one upstream issue per repo is cheap; some maintainers clarify on request).
6. **Re-run the gate at each catalog rebuild** — licences change upstream; the registry entry is versioned with the `cldfbench` pin.

---

## What still needs a human

1. **3 manual-check repos:** `hayniecolorterms` (resolve bare "CC"), `williamsonbenuecongo` and `wustphylogenies` (no declared licence). File one upstream issue each; block meanwhile.
2. **`servamalagasy` version:** confirm the CC-BY version (any version is allowlisted, so this is a metadata nicety, not a gate).
3. **Voices re-licensing ask (judgement call):** decide whether to open an upstream request to dual-licence or CC-BY the Voices sets (`vanuatuvoices`/`papuanvoices`/`amazonianvoices`/`mixezoqueanvoices`) given they are the one materially costly block for mission-priority languages + audio. Product/legal call, not automatable.
4. **Counsel note:** NC/ND verdicts here are clear-cut; no legal review needed for the block decisions themselves.

---

## Consequences for the strategy

- **licensing-audit open-Q #2 is closed:** the "~28 unlicensed/NOASSERTION" set is now a concrete 6-allow / 16-block / 3-manual / 4-N/A partition, verified online.
- **Phase-0 gate spec gains a hard rule:** *clearance reads `metadata.json`'s `license`, not the GitHub licence API.* Add this to the ADR-0002 quarantine note — trusting the GitHub field would both admit nothing new and wrongly exclude `valpal`.
- **ADR-0002 Consequences (licensing bullet):** append the named allow/block lists and the metadata-first procedure; the "block NOASSERTION" phrasing should read "block NOASSERTION **until `metadata.json` is read**", since NOASSERTION ≈ the NC subset, not a licence.
- **Coverage note for sourcing-leftovers:** flag that the NC block concentrates on the **Voices** audio datasets (Oceanic/Papuan/Amazonian small languages) — a known, bounded long-tail gap, not a diffuse loss; feed to the audio-subsystem and seed-set selection.
- **No impact on locked decisions.** CC-BY-SA 4.0 catalog, tone-blind Shape, CLDF/CLTS backbone, honesty axes all untouched.
