"""Audio subsystem (IMPLEMENTATION-STRATEGY Phase 4; audio-subsystem spike).

Pre-renders ONE clip per Shape (tone-blind, so shared across languages) to a
static asset seam: web/audio/{shape-slug}.webm. v1 engine = espeak-ng phoneme
mode (build-side only, GPLv3 — never linked into shipped app code); the ADR names
ToucanTTS as the ratified upgrade behind the same seam.

Provenance axis (recorded vs synthesized): every seed clip is `synthesized` and
badged as such — never passed off as a recording (the seed has no Wiktextract
`sounds` audio). Shapes whose segments espeak can't render get no clip (honest
gap), and the deaf-user path is free: the visible IPA already carries the signal.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unicodedata
from pathlib import Path

from oms.canon import SCHEME_VERSION

# IPA -> espeak-ng phoneme map. EVERY code here passed an empirical context probe
# ([[<code> a]] must render the trailing 'a'; identical-to-baseline = silently
# skipped = unsupported) against THIS espeak-ng's default table — 2026-07-04 audit:
# the old seed map shipped codes the en table doesn't have (A & y Y 7, nasal ~),
# and a single unknown mnemonic in a concatenated string ABORTS the whole render,
# producing silent clips falsely marked clean. Unmapped bases still make a shape
# unrenderable (recorded honestly, not faked).
_MAP = {
    # vowels
    "a": "a", "ɑ": "A:", "e": "e", "ɛ": "E", "i": "i", "ɪ": "I",
    "o": "o", "ɔ": "O", "u": "u", "ʊ": "U", "ə": "@",
    "ɤ": "o-", "ɒ": "0", "ɵ": "@.", "ʌ": "V", "ɐ": 'V"',
    "ɯ": "u-", "ɨ": 'i"', "ɜ": "3",
    # stops / affricate bases
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "g": "g", "ɡ": "g",
    "ʔ": "?", "c": "c", "ɟ": "J", "q": "q", "ʈ": "t.",
    # nasals
    "m": "m", "n": "n", "ŋ": "N", "ɲ": "n^", "ɳ": "n.",
    # fricatives
    "f": "f", "v": "v", "s": "s", "z": "z", "ʃ": "S", "ʒ": "Z",
    "x": "x", "h": "h", "β": "B", "ð": "D", "θ": "T", "ɣ": "Q",
    "ç": "C", "ɕ": "S;", "ʑ": "Z;", "ʂ": "s.", "ʐ": "z.", "ʁ": "R",
    # liquids / glides / taps
    "l": "l", "r": "r", "w": "w", "j": "j", "ɹ": "r\\", "ɻ": "r.",
    "ɭ": "l.", "ʎ": "l^", "ɾ": "*", "ɽ": "*.", "ʋ": "v#",
    "ː": ":",
}
# Bases the en table lacks entirely -> nearest supported segment, clip flagged
# lossy (front-rounded vowels unround; uvular/dental stops fall to velar/alveolar).
_LOSSY_APPROX = {
    "æ": "a", "y": "i", "ø": "e", "œ": "E", "ɘ": "@", "ɶ": "a",
    "ɖ": "d", "ɢ": "g", "ħ": "h", "χ": "x",
    "ɓ": "b", "ɗ": "d", "ʄ": "J", "ɠ": "g",   # implosives approx to plain stop
}
_IMPLOSIVE_APPROX = _LOSSY_APPROX  # back-compat alias (implosives folded in)
# Modifiers approximated (dropped) -> clip is lossy. Nasalization is here too:
# espeak-en has no nasal-vowel phonemes ('~' probes identical to plain vowel).
_LOSSY_DROP = {"ʰ", "ʱ", "ʲ", "ʷ", "ˠ", "ˤ", "ⁿ", "ˡ", "˞"}
# Ejective/glottalization marks: shape-INITIAL they transcribe a glottal stop
# (vanuatuvoices/papuanvoices write 'ma for ʔma); after a consonant they mark an
# ejective, which espeak can't voice -> approximated to the plain consonant.
_GLOTTAL_MARKS = {"'", "ʼ", "ˀ"}


def slug(shape: str) -> str:
    """Filesystem-safe, canonicalization-version-stamped clip name."""
    return "u" + "-".join(f"{ord(c):04x}" for c in shape)


def to_kirshenbaum(shape: str) -> tuple[str | None, bool]:
    """Return (espeak phoneme string, lossy?) or (None, _) if unrenderable.
    Phonemes are SPACE-joined: espeak skips an unknown space-delimited mnemonic but
    ABORTS on an unknown character mid-token — spacing is what caps the blast radius
    of any future map gap at one segment instead of a silent clip."""
    out, lossy = [], False
    for ch in unicodedata.normalize("NFD", shape):
        if ch in _GLOTTAL_MARKS:
            if not out:
                out.append("?")     # initial mark = glottal stop, a real segment
            else:
                lossy = True        # post-consonant = ejective; plain consonant stands
            continue
        if ch in _LOSSY_APPROX:
            out.append(_LOSSY_APPROX[ch]); lossy = True; continue
        if unicodedata.combining(ch):
            lossy = True; continue  # combining marks (incl. nasal ̃) dropped
        if ch in _LOSSY_DROP:
            lossy = True; continue
        if ch in _MAP:
            out.append(_MAP[ch]); continue
        return None, lossy          # a base segment we cannot voice -> no clip
    return " ".join(out) or None, lossy


def _to_webm(wav: Path, webm: Path) -> bool:
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(wav), "-c:a", "libopus", "-b:a", "24k", str(webm)],
                       check=True, capture_output=True, timeout=30)
        wav.unlink(missing_ok=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


# --- ToucanTTS engine (the ratified best-in-class upgrade, Apache-2.0) -----------
# IMS-Toucan is a large neural model (multi-GB checkpoint, PyTorch); it renders
# ARBITRARY segmental IPA by articulatory features, so it voices the marked long-tail
# (clicks/ejectives/implosives/rare vowels) espeak drops. It runs via the wrapper in
# `oms/toucan_infer.py`, enabled by pointing IMS_TOUCAN_HOME at a set-up IMS-Toucan
# checkout + downloaded checkpoint. When unavailable, render() falls back to espeak.
_TOUCAN_READY: bool | None = None


def _toucan_ready() -> bool:
    """Memoized: is a runnable IMS-Toucan present? Checked once, not per shape."""
    global _TOUCAN_READY
    if _TOUCAN_READY is None:
        import os
        home = os.environ.get("IMS_TOUCAN_HOME")
        try:
            _TOUCAN_READY = bool(home) and subprocess.run(
                [sys.executable, "-m", "oms.toucan_infer", "--selftest"],
                capture_output=True, timeout=600).returncode == 0
        except (subprocess.SubprocessError, OSError):
            _TOUCAN_READY = False
    return _TOUCAN_READY


def _toucan_batch(shapes: list[str], out_dir: Path) -> dict:
    """Render a whole shape list through ToucanTTS in ONE process (model loaded
    once — a neural checkpoint mustn't reload per shape). Returns {shape: clip} for
    the ones Toucan produced; {} when Toucan isn't provisioned. Fallback fills the rest."""
    if not _toucan_ready():
        return {}
    jobs = {sh: str((out_dir / slug(sh)).with_suffix(".wav")) for sh in shapes}
    spec = out_dir / "_toucan_jobs.json"
    spec.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    try:
        subprocess.run([sys.executable, "-m", "oms.toucan_infer", "--batch", str(spec)],
                       check=True, timeout=6 * 3600)
    except (subprocess.SubprocessError, OSError):
        return {}
    finally:
        spec.unlink(missing_ok=True)
    out = {}
    for sh, wavp in jobs.items():
        wav = Path(wavp)
        webm = wav.with_suffix(".webm")
        if wav.exists() and _to_webm(wav, webm):
            # ToucanTTS voices arbitrary IPA by construction — no segment is "lossy".
            out[sh] = {"file": webm.name, "provenance": "synthesized",
                       "engine": "toucantts", "lossy": False, "tone_rendered": False}
    return out


def render(shape: str, out_dir: Path) -> dict | None:
    """espeak-ng fallback for a single shape (Kirshenbaum phoneme synthesis)."""
    phon, lossy = to_kirshenbaum(shape)
    if not phon:
        return None
    stem = out_dir / slug(shape)
    wav, webm = stem.with_suffix(".wav"), stem.with_suffix(".webm")
    try:
        subprocess.run(["espeak-ng", f"[[{phon}]]", "-w", str(wav)], check=True,
                       capture_output=True, timeout=20)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if not _to_webm(wav, webm):
        return None
    return {"file": webm.name, "provenance": "synthesized", "engine": "espeak-ng",
            "lossy": lossy, "tone_rendered": False}


def build(core_path: str | Path, out_dir: str | Path) -> dict:
    core = json.loads(Path(core_path).read_text(encoding="utf-8"))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shapes = [s["shape"] for s in core["shapes"]]
    # best engine first, in one model-load pass (empty dict if Toucan isn't provisioned)…
    manifest = _toucan_batch(shapes, out_dir)
    # …then espeak-ng fills every shape Toucan didn't produce.
    for sh in shapes:
        if sh in manifest:
            continue
        clip = render(sh, out_dir)
        if clip:
            manifest[sh] = clip
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    # sweep clips this build no longer emits (renamed/removed shapes, old engine
    # runs) — same orphan lesson as bake._sweep_stale: stale files serve forever
    live = {m["file"] for m in manifest.values()}
    stale = [p for p in out_dir.glob("*.webm") if p.name not in live]
    for p in stale:
        p.unlink()
    if stale:
        print(f"swept {len(stale)} stale clips from {out_dir}")
    return manifest


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    cur = json.loads((root / "data" / "current.json").read_text(encoding="utf-8"))
    core = root / "data" / cur.get("dir", SCHEME_VERSION) / "core.json"
    manifest = build(core, root / "web" / "audio")
    from collections import Counter
    engines = Counter(m["engine"] for m in manifest.values())
    lossy = sum(1 for m in manifest.values() if m["lossy"])
    print(f"rendered {len(manifest)} synthesized clips by engine {dict(engines)} ({lossy} lossy) "
          f"→ web/audio/  (unrenderable shapes get no clip — honest gap; deaf-user path is the visible IPA)")
