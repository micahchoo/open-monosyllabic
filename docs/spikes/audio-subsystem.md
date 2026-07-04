# Spike: Audio Subsystem (gaps 2.1 + 2.2)

**Status:** complete · 2026-07-03 · time-boxed spike
**Terms of reference:** [implementation-gaps.md](../implementation-gaps.md) §2.1 (no IPA-to-speech engine) + §2.2 (no source of real recordings). Honors the locked decisions: recorded-vs-synthesized honesty axis ([ux-design.md](../ux-design.md) §Audio), generated-never-hidden, deaf-user alternative, CLDF/CLTS backbone ([ADR-0002](../adr/0002-data-sourcing-and-ingestion-pipeline.md)).

---

## Findings

### A. IPA-to-speech: the engine landscape

The catalog's synthesis need is unusually **favorable**: inputs are short (1 syllable), segmental, tone-blind, and drawn from a *finite* inventory of CLTS BroadIPA canonical strings. We do not need general TTS — we need "render this one canonical IPA syllable." That reframes the problem from "hard, niche capability" (the gap report's framing) to "bounded batch job."

Surveyed engines, verified online 2026-07:

| Engine | IPA/phoneme input? | Arbitrary segmental IPA? | Coverage | Quality | License (engine / voices) |
|---|---|---|---|---|---|
| **espeak-ng** | Yes — `[[...]]` phoneme mode in **Kirshenbaum ASCII-IPA**, not Unicode IPA; documented IPA↔Kirshenbaum mapping tables exist ([docs](https://github.com/espeak-ng/espeak-ng/blob/master/docs/phonemes/kirshenbaum.md), [phonemes.md](https://github.com/espeak-ng/espeak-ng/blob/master/docs/phonemes.md)) | Partial — phonemes are interpreted against the **current voice's** inventory; out-of-inventory segments (clicks, ejectives, rare vowels) are approximated or dropped ([issue #227](https://github.com/espeak-ng/espeak-ng/issues/227)) | 100+ languages/accents (127 in dev) ([repo](https://github.com/espeak-ng/espeak-ng)) | Robotic formant synthesis; intelligible, clearly artificial | GPL-3.0+ (CLI invocation at build time does not encumber the emitted audio) |
| **IMS ToucanTTS** | **Yes — IPA-native.** Articulatory-feature phoneme representation; "all phonemes in the IPA standard are supported" ([repo](https://github.com/DigitalPhonetics/IMS-Toucan), [README](https://github.com/DigitalPhonetics/IMS-Toucan/blob/ToucanTTS/README.md)) | **Yes, by construction** — segments map to articulatory feature vectors, so unseen segments still render | Meta-checkpoint trained/adapted for **7,000+ languages** ([paper](https://arxiv.org/html/2406.06403v1), [MarkTechPost](https://www.marktechpost.com/2024/06/23/toucan-tts-an-mit-licensed-text-to-speech-advanced-toolbox-with-speech-synthesis-in-more-than-7000-languages/)) | Neural (FastSpeech2-lineage); markedly more natural than espeak-ng; long-tail zero-shot quality varies | **MIT** (toolkit); massive-multilingual checkpoint license needs one confirmation pass |
| **MBROLA** | Yes — diphone synthesis driven by phoneme+duration+pitch input (espeak-ng can front-end it, `mb-*` voices) ([docs](https://github.com/espeak-ng/espeak-ng/blob/master/docs/mbrola.md)) | No — per-voice diphone databases only | ~35 languages of voice DBs | Dated diphone quality | Engine AGPL-3.0; **voices non-commercial-only, not open source** ([Wikipedia](https://en.wikipedia.org/wiki/MBROLA)) — disqualifying for a redistributed catalog |
| **Piper (OHF piper1-gpl)** | Indirect — text → espeak-ng phonemization → VITS; no supported arbitrary-IPA surface | No (bound to per-language voice models) | 30+ languages, 100+ voices ([repo](https://github.com/OHF-Voice/piper1-gpl)) | Good neural quality | GPL-3.0 |
| **Coqui TTS / XTTS (VITS family)** | Phoneme input exists for VITS training via espeak/gruut; XTTS is grapheme-in | No practical arbitrary-IPA path | ~20 languages (XTTS 17) | Good–excellent | Code MPL-2.0; **XTTS weights CPML non-commercial, company shut down Jan 2024, no license for sale** ([issue #3490](https://github.com/coqui-ai/TTS/issues/3490)) |
| **Kokoro-82M + misaki** | Yes — "the model receives phoneme sequences; raw text never reaches the network"; misaki is the G2P frontend ([HF card](https://huggingface.co/hexgrad/Kokoro-82M)) | Risky — trained on ~9 languages' phoneme distributions; arbitrary cross-linguistic IPA is out-of-distribution | 9 languages | Excellent for covered languages | Apache-2.0 |
| **Meta MMS-TTS** | No — grapheme input (uroman), per-language VITS models | No | **1,107 languages** ([fairseq](https://github.com/facebookresearch/fairseq/blob/main/examples/mms/README.md)) | Decent neural | **CC-BY-NC 4.0** (weights) — non-commercial restriction propagates to generated audio posture; also grapheme-input mismatches our IPA-keyed need |
| **Amazon Polly (cloud)** | Yes — SSML `<phoneme alphabet="ipa">` ([docs](https://docs.aws.amazon.com/polly/latest/dg/phoneme-tag.html)) | **No** — each voice accepts only its language's phoneme table; arbitrary cross-linguistic IPA is rejected/approximated | ~30 voice languages | High | Proprietary cloud; per-request cost; output usable but engine unownable |

**Key structural facts:**

1. **Only ToucanTTS is genuinely IPA-first** across the whole IPA space. Everything else either restricts input to a per-voice phoneme inventory (espeak-ng, Polly, MBROLA) or doesn't expose IPA at all (Piper, MMS, XTTS).
2. **espeak-ng is the universal pragmatic baseline** — installable everywhere, deterministic, scriptable, and its Kirshenbaum notation is mechanically derivable from our canonical BroadIPA strings (a small mapping over the finite CLTS segment set — Cognition-light because our strings are single CV(V) syllables). Its two costs: robotic timbre, and lossy approximation of segments outside the chosen voice's inventory.
3. **Pre-render dominates on-the-fly.** The distinct-Shape count is plausibly 10³–10⁴ strings (gap §3.2 estimates Forms at 10⁵–10⁶, but Shapes collapse heavily — Vietnamese alone has ~6.5k *syllables*, but open CV shapes across languages overlap massively). At ~0.5 s/clip, Opus/WebM at ~10 kB/clip → **tens of MB total, a build artifact**. Pre-rendering: works with the static-leaning delivery model (gap §3.1), removes GPU/engine from the serving path, lets audio be QA'd and licensed once, and lets the canonicalization-scheme version stamp the audio filename exactly as ADR-0002 already stamps Form keys (closes the gap-4.2 interaction: reprocessing can't silently orphan clips).
4. **Tone-blindness is a feature here, with one honesty duty.** The Shape string is tone-blind, so one clip per Shape serves every language sharing it — but a Word row displays a tone the clip does not render. The synthesized badge copy must therefore say "synthesized from IPA — tone not rendered," or the audio axis quietly overclaims.

### B. Real recordings: what archives actually offer

| Source | Per-word audio keyed to forms/languages? | License | Verdict |
|---|---|---|---|
| **Wiktextract/Kaikki `sounds` field** | **Yes — already in our ratified mined-tier source.** Each entry's `sounds` array carries `audio` filename, `ogg_url`/`mp3_url` (Wikimedia Commons), the associated IPA, and dialect tags ([wiktextract](https://github.com/tatuylonen/wiktextract), [kaikki rawdata](https://kaikki.org/dictionary/rawdata.html) — bulk audio downloads offered) | Per-file Commons licensing (CC0 recommended for pronunciation files; in practice CC0/CC-BY/CC-BY-SA mix) — capture license metadata per file ([Wiktionary:Audio](https://en.wiktionary.org/wiki/Wiktionary:Audio)) | **v1: yes.** Zero new pipeline surface — it rides stage 1 (WRAP) of ADR-0002's existing Wiktextract ingestion |
| **Wikimedia Commons pronunciation categories** | Yes — hundreds of thousands of per-word pronunciation files, conventional naming `xx-region-word.ogg` ([Commons WikiProject](https://commons.wikimedia.org/wiki/Commons:WikiProject_Pronunciation)) | Free licenses by policy (CC0 recommended) | Superset/substrate of the above; reach it *through* Wiktextract rather than scraping categories |
| **Lingua Libre** | Yes — Wikimédia France's recording studio; contributors in **310+ languages** ([Wikipedia](https://en.wikipedia.org/wiki/Lingua_Libre)); ~730k recordings already by Nov 2021 ([CommonsDownloadTool](https://github.com/lingua-libre/CommonsDownloadTool)); per-language zip datasets ([Help:Download datasets](https://lingualibre.org/wiki/Help:Download_datasets)) | Free licenses (uploaded to Commons; CC-BY/CC-BY-SA mix) | **v1.x fast-follow.** Keyed by *orthographic* word + language, not IPA — needs a join through curated/mined orthographic forms. Highest upside for the mission (its point is under-recorded languages) |
| **Forvo** | Yes (4M+ pronunciations, 340+ languages) — but **API forbids caching audio**; post-2019 ad-hoc license is non-commercial and severely restricts copy/redistribution ([license](https://forvo.com/license/), [API docs](https://api.forvo.com/documentation/general-information/), [Wikipedia](https://en.wikipedia.org/wiki/Forvo)) | Non-redistributable | **Excluded.** Incompatible with a pre-baked, redistributed catalog |
| **ELAR / Pangloss** | Corpus/utterance-level fieldwork archives, not word-keyed; ELAR access-controlled. *(Unverified this session — from training knowledge, cutoff Jan 2026)* | Varies; Pangloss largely CC | **Not v1.** Candidate for the Phase-5 mission-weighted human pass (hand-extracting words for priority languages), not automation |

**Structural fact:** the "recorded" badge is **attainable in v1 essentially for free**, because recordings arrive inside Wiktextract, which ADR-0002 already ingests. The honesty axis does not collapse to a constant (gap 2.2's fear). The catch is distributional: Commons/Wiktionary audio skews Global-North, so recorded-tier audio will be sparsest exactly for the priority languages — same tension as gap §6.1, and the same posture applies: show it honestly, never fake it.

---

## Options considered

### Decision 1 — synthesis engine

1. **espeak-ng phoneme mode, pre-rendered** — universal, trivial to operate, deterministic; robotic voice, lossy outside per-voice inventories (worst exactly on typologically interesting segments). GPL-3 engine, unencumbered output.
2. **ToucanTTS, pre-rendered** *(chosen)* — the only true arbitrary-IPA engine; MIT; neural quality; 7,000-language meta-model aligns with the long tail. Costs: research-toolkit operability (PyTorch, checkpoint download, GPU-preferred batch), and long-tail naturalness is unproven until we listen.
3. **Kokoro/MMS/Piper/XTTS** — each fails a hard constraint (language coverage, non-commercial weights, or no arbitrary-IPA input). Rejected.
4. **Cloud (Polly SSML IPA)** — per-voice phoneme tables reject arbitrary cross-linguistic IPA; recurring cost; unownable. Rejected.
5. **MBROLA** — non-commercial voice licenses disqualify redistribution. Rejected.

### Decision 2 — pre-render vs on-the-fly

1. **Build-time pre-render per Shape** *(chosen)* — 10³–10⁴ clips ≈ tens of MB static assets; QA-able; version-stamped filenames; zero serving infrastructure; static-delivery-compatible.
2. **On-the-fly synthesis** — requires a GPU/CPU synthesis service (contradicts the static-leaning fork §3.1) or in-browser espeak-ng WASM (robotic + inventory-lossy, and duplicates honesty QA at runtime). Rejected for v1; WASM espeak-ng noted as a conceivable offline-PWA fallback later.

### Decision 3 — recorded badge in v1

1. **v1-attainable via Wiktextract `sounds`** *(chosen)* — pipeline already ingests the JSON; add audio-URL + per-file-license capture at stage 1 and an AUDIO attach at stage 8.
2. **Synthesis-only v1, badge aspirational** — simpler, but discards recordings the ratified source already hands us and collapses a stated honesty pillar for no saving. Rejected.
3. **Forvo licensing deal** — non-redistributable terms; rejected.

---

## Recommendation

**v1 audio posture — "pre-rendered, two-provenance, honest by construction":**

1. **Engine: IMS ToucanTTS (MIT), batch pre-render, one clip per canonical Shape string** (not per Form), filenames stamped with the canonicalization-scheme version per ADR-0002. **Runner-up: espeak-ng phoneme mode** — and it is also the *bootstrap*: wire the Phase-3 placeholder → real-audio seam with espeak-ng clips first (hours of work), then regenerate the corpus with Toucan once its checkpoint is validated by ear on the seed languages. The seam (a directory of `{shape-key}.webm`) is engine-agnostic, so swapping engines is a re-render, not a rewire.
2. **Recorded audio: ingest Wiktextract's `sounds` audio in v1.** Stage 1 captures `ogg_url`/`mp3_url` + Commons license metadata per file; stage 8 (ATTACH) links Audio to Word/Form with provenance `recorded` and the file's license for the Data-sources page. **Lingua Libre is the named fast-follow** (per-language datasets, 310+ languages, mission-aligned), joined via orthographic word — not v1 because it needs a new orthographic join the pipeline doesn't have yet.
3. **The recorded badge is real in v1, not aspirational** — sparse and Global-North-skewed, which the UI states rather than hides (consistent with generated-never-hidden). Synthesized badge copy must disclose tone-blindness: *"synthesized from IPA — tone not rendered."*
4. **Deaf-user alternative: the IPA is the content.** Every clip is generated *from* the displayed canonical IPA string, so the visible IPA + the already-locked plain keyword ("as in bed") + per-Word tone glyph together carry 100% of the synthesized signal — no information may exist only in audio. Play buttons get ARIA labels speaking the keyword (per the locked IPA-as-hero accessibility decision); recorded clips additionally carry the source word's orthography. This satisfies the requirement with zero new surface.
5. **Forvo, MBROLA voices, XTTS, MMS: excluded on licensing; Polly: excluded on arbitrary-IPA failure.**

---

## Consequences for the strategy

- **Phase 4 stays additive and shrinks in risk.** The "largest unknown" is now two bounded jobs: (a) a batch pre-render script over the distinct-Shape list; (b) an audio-URL/license capture in the existing Wiktextract wrap. Neither re-edits Phase-3 write-targets — the inert placeholders bind to static `{shape-key}` asset URLs.
- **A slice of Phase 4 moves into Phase 1's seed pipeline:** capturing `sounds` (audio URLs + license) at WRAP time costs near-zero there and avoids re-wrapping later. Flag this as an amendment to the Phase-1 scope.
- **New pipeline touchpoints:** stage 1 (capture recordings), stage 8 (attach Audio + provenance + per-file license), and a post-stage-9 **RENDER** batch step (Shape list → clips). Suggest recording this as the audio annex to ADR-0002 or a new ADR-0003.
- **Data-sources page** gains per-file Commons attribution (CC-BY/CC-BY-SA files require it); CC0 files don't but list anyway. This folds into the existing licensing gate (Phase 0).
- **Storage math:** audio adds tens of MB of static assets — does not flip the static-vs-backend fork (§3.1); if anything it strengthens static.
- **Compare view:** per-column play of the *same* Shape across languages will play the *same synthesized clip* unless a recorded clip exists for that language — this is correct (the Shape is the same string) but should be stated in the methodology page to preempt "why do they sound identical."

## Open questions

1. **ToucanTTS massive-multilingual checkpoint license** — toolkit is MIT (verified); the released meta-checkpoint's own license needs one confirmation before corpus generation (fallback: espeak-ng corpus ships v1 regardless).
2. **Zero-shot quality floor** — how bad is Toucan on typologically distant seed languages? Decide a reject-threshold by ear on the seed set; below it, fall back to espeak-ng for that Shape or omit synthesis (badge: "no audio yet").
3. **Voice/language conditioning policy** — Toucan conditions on a language embedding; do we render each Shape once neutrally, or per-language for Forms? v1 says once (Shape-keyed); revisit if listeners find a "neutral" voice misleading for specific languages.
4. **Commons license long-tail** — a minority of pronunciation files may carry GFDL-only or other awkward licenses; the stage-1 capture must be able to *exclude* files failing the licensing gate.
5. **Lingua Libre join design** (fast-follow): orthographic-word matching across sources needs the same care as the gloss join (gap §1.6) — not designed here.

---

*Verification note: all engine/archive capability and license claims above were checked via web search 2026-07-03; the sole exception is the ELAR/Pangloss row, marked unverified (training knowledge, cutoff Jan 2026).*
