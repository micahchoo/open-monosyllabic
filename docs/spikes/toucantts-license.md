# Spike: IMS ToucanTTS Weights License (toucantts-license)

**Status:** complete · 2026-07-03 · time-boxed licence-fact spike
**Terms of reference:** close the one open confirmation flagged by the audio spike
([audio-subsystem.md](audio-subsystem.md) §Decision 1) — the toolkit is permissive, but the
released massive-multilingual **checkpoint/weights** licence was UNCONFIRMED. Verify online whether
we can generate audio clips with ToucanTTS weights and redistribute them under the catalog's
**CC-BY-SA 4.0**. Respects locked decisions (static-baked hybrid, recorded-vs-synthesized honesty
axis, CC-BY-SA 4.0 catalog).

---

## Findings

### (a) Toolkit code licence — CONFIRMED **Apache-2.0** (correction to prior spike)

GitHub's license endpoint for `DigitalPhonetics/IMS-Toucan` resolves the repository LICENSE to:

```json
{ "key": "apache-2.0", "name": "Apache License 2.0", "spdx_id": "Apache-2.0" }
```

The raw `LICENSE` file base64-decodes to the verbatim **Apache License, Version 2.0, January 2004**
text. Default branch at verification time: `MassiveScaleToucan`.

- Source (GitHub license API): https://api.github.com/repos/DigitalPhonetics/IMS-Toucan/license
- Source (raw LICENSE): https://raw.githubusercontent.com/DigitalPhonetics/IMS-Toucan/MassiveScaleToucan/LICENSE

**This corrects the audio spike**, which recorded the toolkit as "MIT" (that label came from a
secondary MarkTechPost 2024 headline, not the repo). The current, authoritative repo licence is
**Apache-2.0** — still fully permissive, and if anything *cleaner* for us (explicit patent grant,
explicit "no restriction on output").

### (b) Pretrained CHECKPOINT / model-weights licence — CONFIRMED covered by the same Apache-2.0

The pretrained artifacts (massively-multilingual ToucanTTS checkpoint, self-contained aligner,
embedding function, vocoder, embedding GAN) are distributed **inside this same repository's Releases
section** and pulled by `run_model_downloader.py` from that release page
([README](https://github.com/DigitalPhonetics/IMS-Toucan/blob/ToucanTTS/README.md),
[Releases](https://github.com/DigitalPhonetics/IMS-Toucan/releases)).

- There is **no separate LICENSE, NOTICE, or "research-only/non-commercial" clause** attached to the
  weights — not in the README licensing discussion, not on the release assets, not in a weights
  sidecar. The repository-level Apache-2.0 is the governing grant for everything the repo distributes,
  weights included.
- Apache-2.0 grants use, reproduction, modification, **and redistribution, including commercial use**,
  with only attribution/NOTICE preservation as a condition. Crucially, Apache-2.0 places **no
  restriction on the *output* of running the software** — generated audio is not a derivative work of
  the licensed code/weights in a way that propagates the licence.

This is the decisive difference from the disqualified engines in the audio spike: MMS-TTS weights are
CC-BY-NC 4.0, and XTTS weights are CPML non-commercial. ToucanTTS weights are **not** encumbered that
way.

### (c) Training-data constraint on output redistribution — LOW, non-blocking

The 7000-language checkpoint was meta-trained on ~18,000 hrs after cleaning, dominated by
permissively-licensed speech corpora
([paper 2406.06403](https://arxiv.org/abs/2406.06403)):

| Corpus | Hours | Typical licence |
|---|---|---|
| Multilingual LibriSpeech | 16,298 | CC-BY-4.0 (LibriVox public-domain derived) |
| Bible-MMS (371 langs) | 1,230 | Mixed — some Bible recordings carry NC/attribution terms upstream |
| Fleurs (90) | 377 | CC-BY-4.0 |
| Snow Mountain (15) | 269 | CC-BY-4.0 |
| CSS10, African Voices, Indian TTS, Zambezi Voice, Living Audio | small | mostly CC-BY / CC-BY-SA |

Two reasons this does **not** block redistribution:

1. **The model outputs synthetic voices.** Speaker identity comes from an embedding GAN
   ("ThisSpeakerDoesNotExist"), so clips are not utterances of any real corpus speaker — no
   voice-likeness/personality-rights exposure, and each clip is a fresh generation, not a redistributed
   training sample.
2. **We rely on the distributor's grant, not on re-deriving upstream provenance.** IMS published the
   weights under Apache-2.0; that is their affirmative licence. The only residual is the standard,
   *theoretical* open-weights risk that an upstream corpus owner (e.g. a Bible-recording rights holder)
   disputes the training. That risk is identical in kind for every open-weights model and is negligible
   for short, single-syllable, synthetic-speaker segmental clips.

---

## Recommendation

**GO (conditional).** We can generate audio clips with the ToucanTTS pretrained checkpoint and
redistribute them under the catalog's **CC-BY-SA 4.0**. The weights are **Apache-2.0**, which permits
commercial redistribution and imposes no licence on model output, so our generated clips are ours to
license as CC-BY-SA 4.0.

**Two lightweight conditions** (Apache-2.0 hygiene + honesty axis, not blockers):

1. **Ship an Apache-2.0 attribution/NOTICE** for the build-time tool: credit "IMS Toucan
   (DigitalPhonetics, University of Stuttgart), Apache-2.0" and cite paper 2406.06403 in the catalog's
   THIRD-PARTY / build-provenance notice. This is for the *tooling* used to bake clips; it does not
   encumber the CC-BY-SA 4.0 clips themselves.
2. **Stamp the honesty metadata already required by the audio spike** — synthesized badge, "synthesized
   from IPA — tone not rendered," and the canonicalization-version stamp on the clip filename. No new
   obligation; just confirming the licence verdict doesn't relax it.

**Runner-up / fallback (unchanged):** if the project ever wants zero upstream-provenance risk or wants
to avoid a GPU bake step, **espeak-ng remains the confirmed licence-clean baseline** — GPL-3.0 CLI
invoked at build time does not encumber the emitted audio (audio spike §Decision 1). ToucanTTS is the
quality upgrade; espeak-ng is the always-safe floor. The two can coexist (Toucan where it renders well,
espeak-ng fallback for out-of-distribution long-tail segments).

---

## What still needs a human

- **Sign-off on accepting the standard open-weights training-data residual** (the theoretical
  Bible-MMS-style upstream dispute risk). This is a risk-acceptance call, not a fact question — the fact
  (Apache-2.0 grant, no NC clause) is verified. A one-line owner acknowledgement closes it.
- **Confirm the NOTICE placement** (a THIRD-PARTY-NOTICES file vs. an About-page credit) once the
  delivery skeleton exists.
- **Per-release re-check at bake time:** verify the *specific* release asset used still carries no
  asset-level licence override (none exists today, but assets are versioned; re-run the license API
  check against the pinned release tag when the bake is pinned).

## Consequences for the strategy

- **Correct the record:** ToucanTTS toolkit is **Apache-2.0, not MIT** — amend the audio spike table
  and any IMPLEMENTATION-STRATEGY §11 line that inherited the MIT label.
- **Audio subsystem §11 open item can close:** the "checkpoint licence needs one confirmation pass"
  caveat is resolved GO. ToucanTTS is promotable from "candidate pending licence" to "ratified primary
  synthesis engine," with espeak-ng as the named licence-clean fallback.
- **No change to the CC-BY-SA 4.0 catalog licence** and no change to the honesty axis — the verdict
  confirms compatibility rather than forcing a redesign.
- **Add a build-provenance obligation:** the bake pipeline must emit an Apache-2.0 NOTICE for the
  synthesis tool and pin the release tag it downloaded (feeds the ADR-0002 version-stamping discipline).
