# HANDOFF — Open Monosyllabic web Explorer

Rolling checkpoint. Work is in `web/app.js` + `web/index.html` (static, served from
project root: `python3 -m http.server`, open `/web/`). Data: `data/scaled/oms-canon-v1/`
(chunked; **1458 languages · 9387 shapes** — scaled up from the old 63-lang seed).

## Done this session

1. **Heatmap cell blowout fixed** (`renderHeatmap`/`cellStats`). Cells were rendering
   `TIER_GLYPH.repeat(count)` → up to 480 glyphs wide → blew out the table. Now
   `cellStats` dedupes composition to *languages* at their best tier (sums to
   `langCount`), and cells render compact `47● 2◐`, clipped by `.comp` CSS
   (`max-width:2.2rem;overflow:hidden`). Structurally width-bounded.

2. **Map "not working" fixed** (`drawMap` + new `buildBasemap`). It was drawing only
   `<circle>` dots on white — no basemap. Added an Equal-Earth boundary + 30° graticule
   (pure projection math, offline, memoized in `MAP_BASE`). Fixed extent constants
   (`MAP_MINX..`) so frame + dots share one coordinate system. Coordinate-less languages
   are now excluded (were plotted at (0,0)) and reported in the map note as "listed but
   unmapped". **Coastlines DONE (2026-07-04):** network came back; vendored
   `web/land-110m.json` (world-atlas 2.0.2 / Natural Earth, 55 KB). `decodeLand()` in
   app.js inlines the TopoJSON arc decode (no topojson-client dep); `splitAntimeridian()`
   cuts rings crossing lon ±180 (Chukotka, Fiji) that otherwise draw a chord across the
   map. Land renders as ONE evenodd path (lake holes punch through), layered
   ocean → graticule → land → dots. Verified by rasterizing the real `buildBasemap()`
   output (rsvg-convert) and inspecting the PNG — continents correct, no artifacts.
   `boot()` fetches the asset with try/catch: if it's missing, map degrades to the
   graticule-only frame.

3. **Languages view** (new route `languages`). Searchable list (left) + detail (right):
   a language's open-monosyllable shapes with tier badges, structural notes
   (doc_status/prosodic_type/coords), "see in Sounds →" cross-link + click-to-open form
   sheet. Backed by memoized `langIndex()` (inverts postings → per-language shapes).

4. **Regions view** (new route `regions`). Macroarea list + detail: languages in a region
   (sorted by shape count) with aggregate distinct-shape count + tier composition; click a
   language → jumps to Languages view. Backed by memoized `regionIndex()`.
   Regions in data: Papunesia 864, Africa 258, Eurasia 111, Unlisted 57, S.America 6,
   N.America 4, Australia 3.

5. **Look-alikes view** (new route `convergence`, nav "Look-alikes"). Pick a meaning →
   the sound-shapes that ≥2 languages independently use for it, ranked by language count,
   led by a **honesty banner** (`CONV_BANNER`). HONESTY BOUNDARY: surfaces raw
   co-occurrences only — NO similarity/relatedness score (respects ux-design.md "Why no
   similarity score"). Banner deliberately takes no side (coincidence *or* shared history)
   — an earlier draft wrongly asserted "not cognates", corrected since /rua/='Two'×120 etc.
   are real Austronesian cognates. Per-concept (one chunk), so it scales. A *global*
   cross-meaning leaderboard would need a build-time index in `oms/bake.py` (1417 concept
   chunks — too many to load client-side); flagged as follow-up, not built.

The new views mirror the existing Meanings view pattern (`.crow`/`.cshape` CSS, search +
list + detail, `#x=` deep links). `ROUTES` + nav buttons + `state.language`/`state.region`
+ boot wiring (`renderLanguages`/`renderRegions`, `langSearch` oninput, `#l=`/`#r=` deep
links) all added.

## Verification done / not done

- Verified: `node --check` passes; `langIndex`/`regionIndex`/`selectLanguage` template
  logic executed against real `core.json` (sane output, caps fire, tier comp bounded);
  all new `getElementById` ids exist in HTML; 9387 shapes == 9387 posting keys (no
  cross-link dead-ends).
- NOT done: no real-browser click-through. Snap chromium won't launch in this sandbox
  (mount-namespace conflict); can't write to `/tmp` (confined). The USER has a live
  browser and has been screenshotting — rely on them for pixel confirmation.

## Open next steps (from the scale-audit, earlier in session)

- **Observed-vs-expected heatmap intensity** — `app.js:116` still uses raw
  `langCount/maxL`; doc requires denominator = languages that *could* have the cell
  (PHOIBLE-inventory × prosodic-type). Highest-value unbuilt honesty piece.
- **Virtualize long lists** — language list & `renderLangs` cap/slice at 300–400 but
  don't windowed-render; fine for now, revisit if DOM node count bites.
- ~~Real coastlines~~ — done 2026-07-04 (see #2). Possible polish: credit Natural
  Earth / world-atlas on the Sources page alongside the data sources.

---

## Data & pipeline work (assistant, 2026-07-04 — parallel to the frontend above)

The **data grew from 1,458 → 2,053 languages** (14,322 shapes, ~50,750 Forms). The frontend
reads `core.json` dynamically, so the new counts flow through automatically (your regionIndex
etc. now show Papunesia 986 / Africa 404 / Eurasia 353 / N.America 138 / S.America 96 / Australia 3).

**Ingested (all real, via `git clone` into `sources/`, then `python3 -m oms.scaleout`):**
- Quick-win CLDF sets: abvd (Austronesian), grollemundbantu (Bantu, NC), + India-focused
  (marrisonnaga, suntb, dyenindoeuropean/Indo-Aryan, sohartmannchin, zhangrgyalrong, dravlex,
  nagarajakhasian), Amazonia (galuciotupi, mattercariban, chaconarawakan, constenlachibchan),
  Mesoamerica (utoaztecan, mixtecansubgrouping, wichmannmixezoquean), Chadic (kraftchadic),
  Voices (vanuatuvoices 236, papuanvoices, amazonianvoices — NC, now allowed).
- **NEW mined tier — `oms/ingest_wikipron.py`** reads WikiPron TSVs (`sources/wikipron/tsv/*.tsv`
  + `langmap.json`). Got **Yoruba (215), Hausa, Hindi, Tamil, Telugu, Malayalam** — the West-Africa
  Yoruboid gap closed. Forms-only (no gloss).

**Two correctness fixes real data forced:**
1. **Tone diacritics** — `canon.py` now siphons combining tone marks (à/á/ā), not just tone letters,
   so Yoruba `/ba/` groups tone-blind (was fragmenting into bà/bá/bā). Nasal tilde preserved.
2. Earlier: the **one-syllable rule** (rejected disyllables) and **3+ vowel = contested**.

**Licence widened (user "any CC is fine"):** gate accepts CC-BY-NC; catalog → **CC-BY-NC-SA 4.0**;
ND still blocked. `williamsonbenuecongo` (Benue-Congo, unlicensed) blocked → Yoruboid via WikiPron.

**SEAM — chunk tripwire:** at 14,322 (the tone fix pulled it back under 15k). The next big dataset
crosses it → `bake` must shard/pack (§10). Tripwire already warns.

**Gaps still open:** Igbo/Wolof (absent from WikiPron), Khoisan, Nilo-Saharan (no CLDF), Australia
(structural). `docs/ingestion-study.md` has the full roadmap.

---

## Catalog correctness audit (assistant, 2026-07-04)

**Structural audit of `data/scaled/oms-canon-v1` — PASSED (exhaustive, not sampled):**
tests 20 pass; shapes↔postings 1:1 (14,316); all 50,729 postings valid, no dup lang-per-shape;
Σform_count == postings; all shape chunks match postings & glottocodes; all 2,117 concept chunks'
summaries match entries; every shape re-passes `classify_openness` (open), `canonicalize` (fixpoint —
tone fix fully applied), `is_clean_ipa`; nucleus_type agrees with classifier; no ND licences;
current.json → scaled build, web resolves it.

**3 findings (none corrupting):**
1. **1,500 orphan shape chunks** — shape/ has 15,816 files vs 14,316 live (stale pre-tone-fix slugs).
   `write_build` (oms/bake.py:153) never sweeps outdir. On-disk count silently exceeds the 15k
   tripwire which only sees the in-memory count. Fix seam: sweep stale `u*.json` in write_build.
2. **173 languages with form_count=0** (bell1243, emab1235, tsat1238, …) — in core.languages
   (counted in the 2,053 headline) but invisible in postings-derived views. Decide: negative
   evidence (surface in UI) or drop at bake.
3. Stale HANDOFF numbers: actual = 14,316 shapes / 50,729 postings (was written 14,322/50,750).

**DATA-CONTENT audit — DONE (workflow wf_0263828f-9e8 + inline verification).** Audit ran against the
CURRENT post-hygiene-fix build (**15,099 shapes / 56,203 postings / 2,122 concepts / 164 zero-form
langs / 2,018 orphan chunks**). Structural battery re-run CLEAN on it. Rebuild-determinism: shipped ==
fresh rebuild from current code+sources (agent-verified byte-identical). All 30 per-source fidelity
auditors ran; forward traces (catalog→raw row) pass overwhelmingly; all 33 licences verified (no ND;
williamsonbenuecongo fully blocked). Monthly spend limit killed most adversarial verifiers + 5
auditors (metadata, absurdity, 3 linguistic lenses) — key claims re-verified INLINE instead. Full
findings JSON: `/tmp/claude-1000/-mnt-Ghar-2TA-DevStuff-open-monosyllabic/7a746962-7a80-4976-8763-22b57192716a/tasks/whrfiomz3.output`.

**CONFIRMED systematic defects (each re-verified against raw data/code inline, current build):**
1. **Slash annotation-gate false positive** — `_ANNOTATION = set("/~<>[]{}()")` (ingest_cldf.py)
   matches CLTS `grapheme/BIPA` + tone `₁/¹³` notation → **castrosui 9459/9459 rows silently dropped
   yet still listed in core.sources**; kraftchadic loses 72%, grollemundbantu 34%, sohartmannchin 48%;
   ~10,349 valid open monosyllables lost overall + ALL tone data for those sources.
2. **Morpheme-join minting** — loaders strip `+` boundaries/spaces then join: fake "monosyllables"
   from polymorphemic words (marrisonnaga 40 — confirmed by 3 refuters; wold 59, satterthwaitetb 99
   space-joins, suntb ~440 fake VV "diphthongs", nagarajakhasian, papuanvoices, mixtecan…).
3. **Orthography shipped as IPA** — dyenindoeuropean is 100% romanized spelling (`boyau`, `cle`,
   `krow` ship as shapes); abvd `'y' in _VOWELS` → orthographic glide = vowel → ~1,201 disyllables
   pass as open monos; satterthwaitetb pinyin/Lahu ~217 forms.
4. **65 proto-languages ship as attested** (Proto-Polynesian 27 forms, Proto-Lakkja 68, Middle
   Chinese 11, Old Chinese 9, Proto-Keresan 2; ~50 more as zero-form entries) — the new `*` hygiene
   gate checks the FORM, but loaders prefer SEGMENTS where `*` is already stripped → bypassed.
5. **Tamil glottocode typo** in wikipron langmap.json: `tami1289` shipped; real code `taml1289`.
6. **Duplicate gloss_set entries: 3,728/56,203 forms (6.6%)** — pipeline never dedups per-row glosses.
7. **WikiPron letter-page noise** — `_is_noise_word` ASCII-only; 370 one-char Wiktionary letter
   entries in the TSVs, ~274 shippable as fake words (Indic scripts; grows with ben.tsv).
8. **Seed fixture invents attributions** — seed.json cites "wikipron" for viet1252/finn1318/stan1290/
   hawa1245 (7 forms, incl. glosses wikipron can't provide — it's forms-only).
9. **Bound morphemes as free words** — halenepal 40 (refuter-confirmed), zgraggenmadang 42% of its
   forms, mattercariban 14, dravlex hyphen-stems (hyphen lost in Segments).
Minor confirmed: doculect merges under one glottocode with first-name-wins labels (many sources);
zgraggenmadang ships lowercase machine IDs as language names; 2,018 stale orphan chunks (bake never
sweeps); catalog declares NO release licence despite NC/SA source obligations.

**NOT audited** (spend limit): metadata bounding-box sweep, full absurdity scan, Pacific/Africa/
SouthAsia linguistic spot-checks (Tamil typo, letter-noise, castrosui done inline; rest open).
**Suggested fix order:** slash gate (#1) → morpheme-boundary reject (#2) → Segments-vs-Form hygiene
(#4, also fixes #3-adjacent reconstruction leak) → small fixes (#5–#9) → re-bake → re-run audit
(workflow script is resumable: `workflows/scripts/data-content-audit-wf_0263828f-9e8.js`).

**SLASH GATE FIXED + RE-BAKED (assistant, 2026-07-04 ~11am).** `ingest_cldf._ipa` now resolves CLTS
`grapheme/BIPA` tokens per-token to the BIPA (right) side instead of dropping the whole row; `x/`
(empty BIPA) still drops; `~<>[]{}()` row-gate + Form-fallback unchanged. Superscript Chao tones
(castrosui `₁/¹³` → `¹³`) were already siphoned by `canon._TONE_SUPERS` — no canon change. Tests: NEW
`tests/test_ingest_cldf.py` (6 cases incl. castrosui tone token e2e) — **28 pass**.
**New build (verified):** 2,053 langs · **16,396 shapes · 61,620 postings** · 2,270 concepts.
castrosui **0 → 733 forms (733/733 with tones)**; kraftchadic 867→1,636; grollemundbantu 1,775→3,484;
sohartmannchin 228→459; marrisonnaga 2,534→2,915; chaconarawakan 36→63. Zero-form langs 164→103.
Structural battery CLEAN (postings valid, Σform_count==postings, all shapes re-pass
openness/canon/is_clean_ipa, 0 missing chunks, concept summaries match). **Tripwire FIRED:
16,396 chunks > 15k → sharding decision now due** (touches `app.js` slugOf/ensureShape).

**ALL FIXES DONE + RE-BAKED + VERIFIED (2026-07-04). Final build: 1,925 langs · 13,945 shapes ·
53,501 postings · 2,192 concepts · 86 zero-form langs · 0 orphan chunks · tripwires: NONE (honesty
fixes brought it back under 15k — sharding no longer urgent).** Verified: dyen gone from sources
(no 'boyau'-type shapes), 0 proto-languages, castrosui 729 (all-tones), kraftchadic 1,636,
wikipron 906 (letter pages gone), gloss-dups 0/53,501, structural battery clean, 32 tests pass.
Tamil = tami1289 only, 82 forms (wikipron 76 + dravlex 6 merged). Implementation notes: seed.json
also dropped its fabricated 'wikipron' sources entry; scaleout prints EXCLUDE twice for dyen
(cosmetic); bake sweeps shape/ + concept/ dirs ("swept N stale chunk files").
**Still open from audit:** sesquisyllabic/apical-vowel policy calls (suntb/sohartmannchin), abvd
orthographic-but-kept caveat (document on Sources page), doculect-merge naming, no catalog-level
licence declared (CC-BY-NC-SA per licence-widening decision — add to core.meta + web Sources page),
re-run the killed auditors (metadata/absurdity/linguistic) when spend limit resets.
1. ✅ slash gate (above).
2. **Morpheme-join reject** (`ingest_cldf._ipa`): Segments containing boundary tokens `+ _ #` →
   DROP row (polymorphemic ≠ monosyllabic word); Form-fallback values containing a space → DROP
   (multi-word phrase, satterthwaitetb/wold space-joins); Form/Value with leading/trailing `-` →
   DROP even when Segments used (bound morpheme; halenepal/zgraggenmadang/mattercariban). UPDATE
   test_ingest_cldf.py: the `+`-join test must now expect "" (drop). castrosui will fall <733
   (compounds out — honest).
3. **Reconstruction/proto leak**: raw Form/Value starting with `*` → DROP row (walworth/utoaztecan/
   zhangrgyalrong Baxter-Sagart); language Name matching `^[Pp]roto[- ]` → skip language + forms
   (65 proto-langs incl. poly1242 27 forms, lakk1238 68). Leave Old/Middle Chinese lang entries
   (attested doculects) — their `*`-forms die via the Form check.
4. ~~Tamil typo~~ **AUDITOR FINDING WAS FALSE** — verified live on glottolog.org: `tami1289` IS
   Tamil (ISO tam). The auditor claim (`taml1289`) was a hallucination whose adversarial refuters
   died on the spend limit. langmap REVERTED to tami1289 + re-baked (bg `bsnni33n3`). Lesson
   recorded: never act on an unrefuted-only critical without independent re-derivation.
5. **Gloss dedup**: pipeline.py where gloss_set/words build — dedup identical
   (gloss, concepticon_id, source_id) entries (3,728 forms affected pre-fix, likely more now).
6. **Letter-page noise**: ingest_wikipron `_is_noise_word` — add: len(w)==1 and U+0900≤ord<U+0E00
   (Brahmic block) → noise (Indic letter pages; keeps Yoruba 1-char pronouns like ó).
7. **Seed fabricated attributions**: seed/seed.json cites "wikipron" for viet1252/finn1318/
   stan1290/hawa1245 (7 forms + glosses wikipron can't have) → DELETE those seed entries (fixture
   fabrication; unknowable real source).
8. **dyenindoeuropean = pure orthography** → EXCLUDE source in scaleout (skip-list w/ comment;
   1,702 spelling-shapes like `boyau`). abvd stays (orthographic but near-phonemic; caveat doc'd).
   NOTE `'y' in _VOWELS` stays — y IS valid IPA (front rounded V); abvd's y-as-glide is a source
   caveat, not classifier bug.
9. **Orphan sweep in bake**: write_build removes stale `u*.json` in shape/ (and stale concept
   chunks) not in current build — kills the 2,018 orphans permanently.
10. Re-bake (`python3 -m oms.scaleout` bg) → structural battery + per-source recount → update
    numbers here. NOT DOING: chunk sharding (frontend coordination needed — flag only).
Tests after each step; suite must stay green (28 now).

---

## Hygiene fix + ToucanTTS (assistant, 2026-07-04)

**Shape hygiene (`canon.py`):** added `is_clean_ipa()` (pipeline excludes it) — rejects
reconstruction `*`, ASCII cover symbols `A-Z` (V/N/tone-class labels), infix `<>`, boundaries
`+ | = / \`, uncertain `? !`. Also **siphon ASCII tone digits** (`tsa33`→`tsa`, tone `33`).
Result: noisy shapes 28→**0**; and a *correctness gain* — Sino-Tibetan/Kra-Dai tonal monosyllables
that were wrongly excluded (digits misparsed as codas) now included → shapes 14,316 → **15,099**,
postings **56,203**. Tests 20 pass (added hygiene cases in test_canon.py).
→ This puts the build **over the 15k chunk tripwire** (compounds orphan-chunk finding #1 above —
`write_build` should sweep stale `u*.json` AND the next step is real chunk sharding, which changes
the frontend fetch path in `app.js` `slugOf`/`ensureShape` — coordinate before deploying to a
file-count-limited static host).

**ToucanTTS seam (`oms/audio.py` + NEW `oms/toucan_infer.py`):** engine-ordered — Toucan batch
(model loaded ONCE) → espeak-ng fallback per shape; per-clip `engine` in manifest. Toucan runs as a
subprocess (PyTorch never enters the pipeline). **Not runnable in-sandbox (no GPU/model)** → espeak
stays live; seam verified (selftest reports unavailable, fallback works).
**ACTIVATION:** clone github.com/DigitalPhonetics/IMS-Toucan → `pip install -r requirements.txt` →
`python run_model_downloader.py` → `export IMS_TOUCAN_HOME=/path` → `python3 -m oms.toucan_infer
--selftest` (expect "toucan ok") → `python3 -m oms.audio`. One line may need version-alignment:
`_synthesize()`'s `read_to_file(..., input_is_phones=True)` (IMS-Toucan phone-input API varies).

**LIVE Toucan provisioning IN PROGRESS (this box IS the Ryzen AI Max 395 / Strix Halo gfx1151;
ROCm 7.2.2 installed, 15T free):**
- venv: `.venv-toucan/` (Python 3.11.15 — 3.14 is too new for torch wheels). Installing
  `torch 2.9.1+rocm6.4` (4.5 GB wheel, bg task blkqkfr9f).
- IMS-Toucan cloned to `.venv-toucan-src/` (has `InferenceInterfaces/ToucanTTSInterface.py`,
  `run_model_downloader.py?`, `requirements.txt`).
- NEXT STEPS: (1) `.venv-toucan/bin/python -c "import torch;print(torch.cuda.is_available(),
  torch.cuda.get_device_name(0))"` — expect True + Radeon 8060S; if gfx1151 kernel missing, set
  `HSA_OVERRIDE_GFX_VERSION=11.5.1` (or nightly torch). (2) install IMS-Toucan requirements into the
  venv + download the checkpoint. (3) `export IMS_TOUCAN_HOME=$PWD/.venv-toucan-src`. (4) **RUN
  oms.audio FROM THE VENV** — `.venv-toucan/bin/python -m oms.audio` — because `_toucan_ready`
  subprocesses `sys.executable -m oms.toucan_infer`, which needs torch (venv), and `oms` is pure
  stdlib so the venv python runs it fine.
- **BLOCKER FOUND (2026-07-04): stable `torch 2.9.1+rocm6.4` has NO gfx1151 kernels.** arch list =
  gfx900/906/908/90a/942/1030/1100/1101/1102/1200/1201 — no gfx1151. Torch *detects* the Radeon 8060S
  (`cuda.is_available()`=True) but any GPU op → HIP "no kernel image" / "invalid device function".
  Overrides don't fix it (gfx1100 spoof fails — RDNA3.5≠RDNA3 ISA). **FIX = a gfx1151-native build:**
  AMD ROCm-7 "TheRock" nightly wheels (repo.radeon.com / github ROCm/TheRock releases target gfx1151),
  or pytorch nightly, or build from source. **OR just run CPU torch** (`pip install torch` plain) —
  guaranteed, one-time batch, fine overnight. Model download (`run_model_downloader.py`) not yet done.
  Env is otherwise perfect (ROCm 7.2.2, 15T disk, IMS-Toucan cloned, oms seam ready).
- **DECISION: running on CPU** (ROCm wheel runs CPU kernels; `HIP_VISIBLE_DEVICES=-1` →
  `cuda.is_available()`=False → verified CPU matmul works). No torch reinstall needed.
- **IN PROGRESS (bg task b6l7q2ne3):** installing IMS-Toucan deps with **RELAXED pins** into
  `.venv-toucan` (its requirements pin numpy 1.23 / librosa 0.9.2 → conflict on py3.11, so pins
  stripped via `sed -E 's/[~=<>!].*//'`, torch/torchaudio excluded to keep 2.9.1), then
  `run_model_downloader.py` (multi-GB checkpoint). Log: `/tmp/toucan_setup.log` (markers DEPS_OK /
  MODEL_OK).
- **REMAINING RISKS to verify after download:** (a) torch 2.9 vs Toucan's 2.4 pin → possible API
  drift in ToucanTTSInterface/speechbrain 0.5.13; (b) `_synthesize()` phone-input API
  (`read_to_file(..., input_is_phones=True)`) may need version-alignment; (c) soundfile/phonemizer
  system libs (espeak-ng present; libsndfile?). **TO RENDER:** `IMS_TOUCAN_HOME=$PWD/.venv-toucan-src
  HIP_VISIBLE_DEVICES=-1 .venv-toucan/bin/python -m oms.toucan_infer --selftest`, then a small
  `--batch` (incl. a click like ǃa) before the full `-m oms.audio`. Likely best finished in a fresh
  session (multi-GB downloads + possible dep patching).
- **UPDATE:** deps install **SUCCEEDED** with relaxed pins → but pulled MODERN versions
  (speechbrain **1.1.0** vs Toucan's pinned 0.5.13, numpy 2.4, torch 2.9 vs Toucan's 2.4). No
  `run_model_downloader.py` exists — model auto-downloads when `ToucanTTSInterface` is constructed.
  Selftest running (bg `bd4iycba9`, log `/tmp/toucan_selftest.log`) — it downloads the checkpoint +
  reveals API breaks. **LIKELY next fix:** constrained reinstall pinning `speechbrain==0.5.13` +
  a Toucan-compatible torch (their req is `torch~=2.4`); best done fresh. venv is otherwise fully
  provisioned — only version reconciliation + the model download remain.
- **SYSTEM-LIB BLOCKER FIXED:** selftest failed on `PortAudio library not found` (IMS-Toucan imports
  `sounddevice` at module load). Fixed WITHOUT sudo: `brew install portaudio` →
  `/home/linuxbrew/.linuxbrew/opt/portaudio/lib/libportaudio.so.2`. **MUST export
  `LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/opt/portaudio/lib:$LD_LIBRARY_PATH`** whenever running
  `oms.toucan_infer` / `oms.audio` (subprocess inherits it). NOTE: speechbrain 1.1 did NOT break the
  import — portaudio was the real wall. Selftest re-running with the lib path (bg brtrfu2v4,
  `/tmp/toucan_selftest2.log`) — downloading the multilingual checkpoint now.
- **RESUME (venv fully provisioned + portaudio installed):**
  `LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/opt/portaudio/lib IMS_TOUCAN_HOME=$PWD/.venv-toucan-src
  HIP_VISIBLE_DEVICES=-1 .venv-toucan/bin/python -m oms.toucan_infer --selftest` → then `--batch
  /tmp/tjobs.json` (has /ma/ + click ǃa + ejective kʼa) → then `-m oms.audio`. Only the model
  download + a possible `_synthesize` phone-API tweak remain.
- **MODEL SOURCE FOUND — HuggingFace `Flux9665/ToucanTTS`** (via `hf_hub_download`; NOT auto-fetched
  by the interface — must be pre-placed). Interface with `tts_model_path="Meta"` looks for
  `Models/ToucanTTS_Meta/best.pt`. **Downloading now (bg b8f36q9dy, `/tmp/toucan_model_dl.log`):**
  `ToucanTTS.pt` (→ copied to `Models/ToucanTTS_Meta/best.pt`), `16kHz_encodec.pt` (vocoder),
  `embedding_gan.pt`, `aligner.pt`, iso JSONs, cached in `.venv-toucan-src/Models/_hf`.
- **AFTER DOWNLOAD:** rerun selftest (RESUME cmd above). If it still errors on a missing
  Models/ path, read `InferenceInterfaces/ToucanTTSInterface.py` for the exact expected layout
  (vocoder/aligner/embedding sub-paths) and place the downloaded files accordingly — that + the
  `_synthesize` phone-input keyword are the ONLY things between here and a working render.
  **ALL environmental blockers (GPU→CPU, py3.11 deps, PortAudio) are cleared.**
- **RENDER WORKS + PHONE-FORMAT BUG RESOLVED (2026-07-04):** selftest passes, model at
  `.venv-toucan-src/Models/ToucanTTS_Meta/best.pt`, `forward(text, input_is_phones=True)` returns
  `(wave, sr)`. **Root cause of the mispronunciation** (`/ma/` → "emae", then "pembaabey" after a
  bad `~` guess): `TextFrontend.string_to_tensor(text, input_phonemes=True)` uses the string AS-IS
  and **skips `postprocess_phoneme_string`** — so raw phone input never gets the trailing silence
  `~` + **EOS `#`** (TextFrontend L1015-1018) the model needs to terminate, nor the phone
  normalization (g→ɡ, unsupported-mark stripping). Without the EOS the model garbles short
  syllables. Two wrong guesses first (repeat-padding `ma ma ma`; appending only `~`, the PAUSE
  symbol not the EOS). **FIX (`oms/toucan_infer.py` `_synthesize`):** normalize via Toucan's own
  `tts.text2phone.postprocess_phoneme_string(clean, for_feature_extraction=True,
  include_eos_symbol=True, for_plot_labels=False)` before `forward(..., input_is_phones=True)` —
  feeds the model byte-for-byte what its working grapheme path feeds it; the appended `~#` also
  clears the aligner's 3-phone floor, so the artifact-inducing repeat-padding is gone. Compiles;
  **needs one listen-test to confirm by ear** (I cannot hear output). VERIFY:
  `LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/opt/portaudio/lib IMS_TOUCAN_HOME=$PWD/.venv-toucan-src
  IMS_TOUCAN_MODEL=Meta HIP_VISIBLE_DEVICES=-1 .venv-toucan/bin/python -m oms.toucan_infer --batch
  /tmp/tjobs.json` → play `/tmp/t_ma.wav` (should say "ma"). If `/tmp/tjobs.json` is gone, it's
  `{"ma": "/tmp/t_ma.wav", "kʼa": "/tmp/t_ka.wav"}`. Then full render: `... -m oms.audio`.
- **ROOT CAUSE FULLY DIAGNOSED + FIXED (2026-07-04, ground-truth experiments — no more guessing).**
  Postprocess fix alone was NOT enough ("still not pronouncing ma correctly"). Ran diagnostics on
  this box (scratchpad `diag_toucan.py` / `diag_toucan2.py`, logs `/tmp/diag_toucan*.log`):
  (1) phone-path mechanics SOUND — g2p-internal string via `input_is_phones=True` ≈ grapheme render;
  (2) EOS `#` requirement REAL — `'ma~'` without it smears to 1.68 s (model overwrites last two
  positions from index [-3] and hardwires element 0 as leading silence:
  `Modules/ToucanTTS/InferenceToucanTTS.py:229-231,244-245`; `#` = silence+EOS features, `~` =
  silence: `Preprocessing/articulatory_features.py:27-28`); (3) REMAINING BUG = vowel REDUCTION:
  working eng path says "ma" as `'~mˈɑː~#'` — citation STRESS BEFORE THE VOWEL (ˈ applies to the
  FOLLOWING phone: `mˈa`, NOT `ˈma`) — while ours was unstressed short cardinal /a/ under the
  default ENGLISH accent embedding → reduced to mush. Spanish g2p ground truth: "ma" → `'~mˈa~#'`
  (SAME cardinal a as our shapes!). NOTE: **no code in the whole IMS-Toucan repo ever passes
  `input_is_phones=True`** — we are its first users; nothing guarded this path.
  **FIX (both in `oms/toucan_infer.py`):** (a) `_synthesize` inserts `ˈ` before the first vowel
  (nucleus) using `oms.openness._VOWELS` — prosodic citation form, segmental identity unchanged;
  (b) `_load_tts` sets `tts.set_accent_language(os.environ.get("IMS_TOUCAN_ACCENT", "spa"))` —
  Romance accent = full unreduced cardinal vowels (env-overridable). Stress insertion verified on
  ma/a/wai/puː/kʼa/ǃa/tie. LISTEN-COMPARE files: `/tmp/diag2_A_spa_grapheme.wav` (ground truth),
  `B_spa_stress` (= production recipe), `C_spa_plain`, `D_eng_stress`, `E_eng_stress_long`.
  Production-path verify (bg): `--batch /tmp/tjobs.json` → `/tmp/t_ma.wav` should now say "ma".
  If eng accent preferred by ear: `export IMS_TOUCAN_ACCENT=eng`. Then full render: `-m oms.audio`.
- **TAIL-GASP FIX + HINDI/MALAYALAM A/B SAMPLE SET (2026-07-04).** User: production `t_ma.wav` had a
  "shivering gasp at the end". Cause: clip ends on a rendered silence phone `~`, and `forward()`'s
  loudness normalization (-29 dB over a mostly-silent clip) amplifies vocoder breath in the tail.
  Fix in `_synthesize`: energy-based tail trim (keep ≤80 ms past the last sample above 2% of peak) —
  trims by SIGNAL, unlike the rejected proportional slice. — For "was Toucan worth it": A/B set of
  12 real catalog shapes (Hindi dʒɑː kjɑː d̪oː bʱiː keː d̪ũː; Malayalam puː t̪iː n̪iː maː ʃriː kɐi̯)
  in `/tmp/oms-samples/` as `{lang}_{slug}_espeak.wav` vs `..._toucan.wav` (script: scratchpad
  `hindi_mal_samples.py`; espeak side = production `to_kirshenbaum`). espeak: 2/12 UNRENDERABLE
  (bʱiː, kɐi̯), 4 lossy. Toucan render incl. re-verify of `/tmp/t_ma.wav` ran via
  `--batch /tmp/oms-samples/jobs.json`.
- **TOUCAN VERDICT: NO-GO (user, by ear, 2026-07-04, after the A/B sample set).** No pipeline code
  change needed: `oms/audio.py` only tries Toucan when `IMS_TOUCAN_HOME` is set — unset, espeak-ng
  is the sole engine. The `toucan_infer.py` work (EOS wrap, citation stress, accent embedding, tail
  trim) stays dormant + documented in case neural audio is revisited. CONSEQUENCE ACCEPTED: the
  espeak-unrenderable long tail (clicks, ejectives, breathy voice — e.g. Hindi bʱiː) ships with NO
  clip (honest absence, already the pipeline's behavior). — **mespeak evaluated and REJECTED**
  (user asked re: github.com/itinerarium/phoneme-synthesis): meSpeak.js = speak.js = Emscripten
  port of the ORIGINAL eSpeak (2011-2020, pre-espeak-ng), ~30 voices vs espeak-ng's 100+; same
  formant synth, older/frozen → cannot beat our espeak-ng. Its IPA→espeak table (106 regex rules)
  covers LESS than `to_kirshenbaum` (no breathy/dental/ejective/click/implosive, no ɐ, no stress) —
  nothing to adopt.
- **ESPEAK COVERAGE AUDIT (2026-07-04, post-Toucan-no-go; user asked "were any samples ungenable").**
  Sample set: 2/12 no-clip (Hindi bʱiː, Malayalam kɐi̯), 4/12 lossy (dentals→alveolar). CATALOG-WIDE
  (13,945 shapes): 52% clean / 16% lossy / **31% NO CLIP (4,389 shapes)**. KEY FINDING: most of the
  gap is `to_kirshenbaum`'s seed-era _MAP being narrow, NOT espeak inability. Evidence: top blockers
  ʰ(399) ɯ(378) ɕ(360) ɨ(252) c(232) '(229) ʂ ɣ ʐ q ˞ ɐ ʌ ʑ — nearly all have standard
  Kirshenbaum equivalents (ʌ→V, ɯ→u-, ɨ→i", ɣ→Q, ʂ→s., ʈ→t., ɖ→d., ɻ→r., ɾ→*, β→B, ð→D, œ→W,
  ɒ→A.) or honest lossy drops (ʰ ʱ ˀ ʼ). The leading apostrophe = GLOTTAL STOP in
  vanuatuvoices/papuanvoices transcriptions — it alone zeroes out whole languages (Teun/Serua/
  Perai/Nila/Iliun/Aputai 100% no-audio; positional rule: initial '→ʔ→Kirshenbaum ?, post-consonant
  '→lossy drop). Telugu 65% no-audio (retroflexes). SIMULATED RECOVERY with ~20 map entries:
  31%→10% no-clip (and that's an UNDERESTIMATE — ð β œ ɒ ɜ ɰ in the "hopeless" residue are also
  Kirshenbaum-mappable). PROPOSED (not yet done): widen _MAP + apostrophe rule in oms/audio.py,
  re-render. SEPARATE HYGIENE FLAG: shapes carrying ̍ U+030D (syllabicity) suggest syllabic
  consonants leaked past ADR-0001 — check canon/openness, different lane than audio.
- **KIRSHENBAUM MAP REWRITE DONE (2026-07-04, "do it" + user heard silent y).** Empirical probe of
  EVERY code ([[<code> a]] context test; identical-to-baseline = silently skipped) exposed TWO bugs
  beyond narrowness: (1) the SEED map shipped codes espeak-en doesn't know — A(ɑ) &(æ) y Y(ø) 7(ɤ)
  and nasal '~' — and (2) one unknown mnemonic in a CONCATENATED string ABORTS the whole render →
  those clips were SILENT but marked clean (user's "y does not get pronounced": y is not in the en
  phoneme table; any y-shape rendered silence). FIX in `oms/audio.py to_kirshenbaum`: verified
  _MAP (retroflexes t. s. z. n. l. r. *., taps *, ɹ→r\, ʋ→v#, ʎ→l^, palatals c J C S; Z;, uvular q R,
  fric B D T Q, vowels A: o- 0 @. V V" u- i" 3), _LOSSY_APPROX for en-absent bases (æ→a y→i ø→e œ→E
  ɖ→d ɢ→g ħ→h χ→x + implosives; _IMPLOSIVE_APPROX aliased for back-compat), nasal ̃ now LOSSY DROP
  (espeak-en has no nasal vowels — old '~' emit was an abort), positional _GLOTTAL_MARKS rule
  (initial '→? real glottal stop; post-consonant = ejective → lossy), SPACE-JOINED output (caps any
  future gap at one skipped segment, never a silent clip). Tests 22 pass. COVERAGE: 31%→5% no-clip
  (719 shapes, mostly clicks — honest gaps); clean 55% lossy 40%. Probes verified BY RMS: py mɑ mã
  'ma ʈa kʂa d̪ũː bʱiː kɐi̯ all SOUND. Full re-render bg → web/audio (log /tmp/audio_rebuild.log).
  TODO after render: sweep orphan webms not in manifest (old silent clips for changed slugs).
- **MALAYALAM "no meanings" ROOT CAUSE (user question, 2026-07-04):** mala1464 = 6 glossed forms
  (dravlex, curated) + 60 gloss-less (WikiPron, mined). WikiPron is a pronunciation dictionary
  (word→IPA only, NO glosses by design) — mined-tier forms ship as Forms without Words, the domain
  model's graceful degradation. Not a bug. Upgrade path if wanted: wiktextract (Wiktionary senses,
  CC-BY-SA) could attach glosses to WikiPron-mined forms; new ingestion source, not a quick fix.
- **AUDIO RE-RENDER LANDED (2026-07-04): 13,226 clips (5,622 lossy) → web/audio, all espeak-ng with
  the verified map.** Orphan-webm sweep still TODO (old slugs from pre-fix renders linger on disk).
- **IN FLIGHT — WIKTEXTRACT GLOSSES + MARATHI ("do it" + "why is marathi not represented"):**
  (1) Marathi WAS just an omission — langmap.json only had my hand-picked set (hin ben tam tel mal
  yor hau + ibo/wol which WikiPron lacks). FIXED: fetched mar_deva_broad.tsv (4,872 pairs) →
  sources/wikipron/tsv/mar.tsv, added mara1378 to langmap; ingest verified (4,820 entries pre-filter).
  (2) NEW `oms/fetch_glosses.py`: downloads kaikki.org wiktextract JSONL per mined language
  (hin ben tam tel mal mar yor hau), emits sources/wikipron/gloss/{iso}.json = {headword: [≤3 short
  glosses]}, skips form_of/alt_of senses, CC-BY-SA (same gate as WikiPron). Idempotent (skips
  existing). (3) `ingest_wikipron.load` now joins gloss/{iso}.json on the TSV headword; multiple
  glosses become multiple entries that merge into one Word's gloss_set. Tests 22 OK.
  NEXT once fetch (bg, /tmp/gloss_fetch.log) finishes: `python3 -m oms.scaleout` (WATCH the 15k
  chunk tripwire — was 14,322, Marathi may cross it; bake warns but builds), spot-check glossed
  Malayalam/Marathi forms, then `python3 -m oms.audio` again for NEW shapes only (full re-render is
  fine too). Frontend picks up core.json automatically.
- **GLOSSES + MARATHI LANDED (2026-07-04).** kaikki fetch: all 8 langs (hin 20,342 / ben 8,639 /
  tam 9,453 / tel 15,150 / mal 10,088 / mar 4,621 / yor 4,207 / hau 1,867 glossed headwords →
  sources/wikipron/gloss/). TWO SEAMS the join forced: (1) `bake.build_concepts` gloss-ckeys now
  HASHED (`g-`+sha1[:16]) — per-char slug of sentence-length wiktextract glosses blew the 255-byte
  filename limit (OSError). ckey opaque to frontend; old g- deep links die (acceptable). (2)
  `ingest_wikipron` cuts glosses at first comma/semicolon — prose senses would mint near-duplicate
  concepts; raw gloss/*.json keeps full text. REBUILD: **1,926 languages / 13,960 shapes / 53,547
  postings** — languages DROPPED from 2,053 because the dyenindoeuropean exclusion (audit) had
  never been re-baked: 2,053 − ~128 orthographic doculects + Marathi = 1,926, first fully-hygienic
  count ("swept 300 stale chunk files" = dyen garbage leaving). RESULTS: Marathi 46 shapes / 43
  glossed (ka → "why"); Malayalam 55/66 glossed (was 6); Hindi 188/309. Chunks: 13,960 shape +
  3,325 concept, under 15k-per-kind tripwire. FIXED test pollution: test_scaleout baked into repo
  root `data-scaled/` → now tempdir; stray dir removed. `oms/audio.py build()` now sweeps orphan
  webms (old TODO). Final espeak render running bg (log /tmp/audio_rebuild2.log) — after it:
  verify in browser; frontend reads new core.json automatically.
- **FINAL RENDER LANDED (2026-07-04): 13,238 clips (5,627 lossy) → web/audio; new orphan sweep
  removed 923 stale clips (dyen garbage + pre-map-fix slugs). Tests OK. The Marathi+gloss+audio
  chain is COMPLETE — catalog: 1,926 langs / 13,960 shapes / 53,547 postings, mined-tier meanings
  attached (mal 55/66, hin 188/309, mar 43/46), espeak coverage 95% (5% honest no-clip long tail).
  Everything verified except in-browser click-through — user has the live browser.**
- **SYLLABIC-CONSONANT + LIGATURE HYGIENE (2026-07-04, user report: /n̪d̪ʱɐ/ "not a word").** THREE
  fixes: (1) `openness.classify_openness` — the syllabicity mark (̩ U+0329 / ̍ U+030D) folded into
  its consonant token so syllabic nuclei masqueraded as onset consonants (kr̩ba/r̩kʂi shipped as
  "open monophthongs"); now any C/G token carrying a syllabic mark → excluded (ADR-0001: consonant
  nucleus, or a second syllable). Voiceless ring U+0325 (l̥i) unaffected — tested. (2)
  `ingest_wikipron._is_noise_word` — Wiktionary CONJUNCT/LIGATURE pages (ന്ധ "ligature of na+dha",
  pron = letter name with epenthetic ɐ) now dropped: all-Brahmic + contains VIRAMA + NO vowel char
  (independent or sign). Real words kept: कल (inherent vowel, no virama), क्या/हिन्दी (vowel signs) —
  tested (new tests/test_ingest_wikipron.py). (3) `canon._NON_IPA` += ◌ U+25CC (dotted-circle
  placeholder leaked into "◌jɐ"). Suite: 27 tests OK. REBUILD: 13,819 shapes / 53,346 postings
  (-141 junk shapes, 206 stale chunks swept); all 9 reported junk shapes verified GONE; Malayalam
  66→41 shapes, list now reads as real lexicon (puː t̪iː n̪iː ʃriː + genuine loanwords skruː bɭuː).
  Audio re-render bg (/tmp/audio_rebuild3.log) — orphan sweep will clear removed shapes' clips.
- **HYGIENE RENDER LANDED (2026-07-04): 13,107 clips (5,510 lossy), 131 stale clips swept (the
  removed junk shapes' audio). Chain complete — catalog 1,926 langs / 13,819 shapes, tests 27 OK.**
