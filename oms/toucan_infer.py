"""ToucanTTS inference wrapper (the ratified best-in-class IPA synthesizer).

Runs as a SUBPROCESS so PyTorch / IMS-Toucan never load into the main pipeline, and
so the model is loaded exactly once per batch. ToucanTTS (Apache-2.0) voices arbitrary
segmental IPA by articulatory features, so it renders the marked long-tail (clicks,
ejectives, implosives, rare/nasal vowels) that the espeak-ng fallback cannot.

ENABLE (until then, `oms.audio` transparently falls back to espeak-ng):
  1. git clone https://github.com/DigitalPhonetics/IMS-Toucan
  2. install its requirements (PyTorch, …) and download the multilingual checkpoint
  3. export IMS_TOUCAN_HOME=/path/to/IMS-Toucan   (optionally IMS_TOUCAN_MODEL=Meta)

USAGE:
  python -m oms.toucan_infer --selftest        # exit 0 iff Toucan is runnable
  python -m oms.toucan_infer --batch jobs.json  # jobs = {ipa_shape: out_wav_path}
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _load_tts():
    """Construct the ToucanTTS interface from an IMS_TOUCAN_HOME checkout. Raises
    if unavailable (caught by the caller → espeak fallback)."""
    home = os.environ.get("IMS_TOUCAN_HOME")
    if not home or not Path(home).is_dir():
        raise RuntimeError("IMS_TOUCAN_HOME not set or not a directory")
    sys.path.insert(0, home)
    os.chdir(home)   # IMS-Toucan resolves Models/… relative to its own dir
    import torch  # noqa: heavy, only inside the subprocess
    from InferenceInterfaces.ToucanTTSInterface import ToucanTTSInterface
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # "Meta" = the massively-multilingual ToucanTTS checkpoint (Apache-2.0).
    tts = ToucanTTSInterface(device=device, tts_model_path=os.environ.get("IMS_TOUCAN_MODEL", "Meta"))
    # Accent embedding (lang_id) conditions vowel realization. The default "eng"
    # REDUCES unstressed short cardinal vowels (diagnosed 2026-07-04: '~ma~#' under
    # eng garbled; Spanish g2p ground truth for "ma" is '~mˈa~#' and renders clean).
    # A five-vowel Romance accent gives full citation-form cardinal vowels, which is
    # what a language-neutral IPA catalog wants. Override with IMS_TOUCAN_ACCENT.
    tts.set_accent_language(os.environ.get("IMS_TOUCAN_ACCENT", "spa"))
    return tts


def _synthesize(tts, ipa: str, wav_path: str) -> None:
    """Render one IPA shape to a wav, feeding phones directly (bypassing grapheme G2P).
    IMS-Toucan's articulatory frontend accepts phone strings; the exact keyword differs
    across checkpoint versions — align this one call to your build if needed."""
    import io
    import contextlib
    import soundfile as sf
    # (1) Drop diacritics Toucan's phone table lacks — the ejective / glottalization
    # marks ʼ ' ˀ that spam "unknown phoneme". The feature is approximated away (same
    # result as before, just clean); the glottal STOP ʔ is a real segment and kept.
    clean = "".join(c for c in ipa if c not in {"ʼ", "'", "ˀ"})
    if not clean.strip():
        raise ValueError("empty after removing unvoiceable marks")
    # (1b) Citation stress on the nucleus. Toucan's ˈ applies to the FOLLOWING phone,
    # and its g2p always emits it (Spanish "ma" → '~mˈa~#'); an UNSTRESSED short vowel
    # gets prosodically reduced into un-syllable-like mush. Stress is prosody, not
    # segmental identity, so the catalog shape is unchanged.
    from oms.openness import _VOWELS
    if "ˈ" not in clean:
        for i, ch in enumerate(clean):
            if ch in _VOWELS:
                clean = clean[:i] + "ˈ" + clean[i:]
                break
    # (2) Normalize the phones exactly as Toucan's grapheme path does. With
    # input_is_phones=True the frontend (TextFrontend.string_to_tensor) uses the string
    # AS-IS and skips postprocess_phoneme_string — so a raw phone input loses BOTH the
    # phone normalization (g→ɡ, unsupported-mark stripping) AND the trailing silence "~"
    # plus EOS "#" that the model needs to terminate. Missing the EOS, the model never
    # resolves the syllable and garbles it ("ma" → "emae"/"pembaabey"). Reusing Toucan's
    # own postprocessing feeds the model byte-for-byte what its working grapheme path
    # feeds it — and the appended "~#" lifts even a 1-phone input past the aligner's
    # 3-phone floor, so the old repeat-padding (which smeared boundary artifacts) is gone.
    text = tts.text2phone.postprocess_phoneme_string(
        clean, for_feature_extraction=True, include_eos_symbol=True, for_plot_labels=False)
    if not text.strip("~# "):
        raise ValueError("empty after phone normalization")
    # (3) Silence Toucan's frontend print spam during synthesis.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        wave, sr = tts.forward(text=text, input_is_phones=True)   # → (wave, sample_rate)
    try:
        wave = wave.detach().cpu().numpy()
    except AttributeError:
        pass
    # (4) Trim the synthetic tail. The clip ends on a rendered silence phone "~", and
    # forward()'s loudness normalization (-29 dB over a mostly-silent clip) cranks the
    # gain until low-level vocoder breath in that tail becomes an audible shivering
    # gasp. Energy-based: keep up to 80 ms after the last sample above 2% of peak.
    # (NOT the earlier proportional slice — this trims by signal, not by phone count.)
    import numpy as np
    env = np.abs(wave)
    if env.max() > 0:
        above = np.flatnonzero(env > 0.02 * env.max())
        wave = wave[: min(len(wave), int(above[-1]) + int(0.08 * sr))]
    sf.write(str(wav_path), wave, sr)


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        try:
            _load_tts()
            print("toucan ok")
            return 0
        except Exception as e:  # noqa: broad — any failure means "unavailable"
            print(f"toucan unavailable: {e}", file=sys.stderr)
            return 1
    if argv and argv[0] == "--batch":
        jobs = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        try:
            tts = _load_tts()   # loaded ONCE for the whole batch
        except Exception as e:
            print(f"toucan load failed: {e}", file=sys.stderr)
            return 1
        ok = 0
        for ipa, wav in jobs.items():
            try:
                _synthesize(tts, ipa, wav)
                ok += 1
            except Exception as e:  # a segment Toucan can't voice → espeak fills it later
                print(f"skip {ipa!r}: {e}", file=sys.stderr)
        print(f"toucan rendered {ok}/{len(jobs)}")
        return 0
    print("usage: python -m oms.toucan_infer (--selftest | --batch jobs.json)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
