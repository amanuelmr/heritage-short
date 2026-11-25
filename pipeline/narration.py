"""Stage: narration. One WAV per shot, cached by hash of (model, voice settings, text).
Supports Cloudflare Deepgram Aura (`@cf/...`) and Gemini TTS (`gemini-...`).

Aura 2 changes pitch from call to call, so the same speaker can sound like two people.
If `voice.target_pitch_hz` is set, we generate up to `max_takes` takes per line and keep
the one whose median pitch is closest to the target (stopping early inside the tolerance)."""
import json
import subprocess
import sys
import wave

import numpy as np

from common import OUT, load_storyboard, log_call, rel, with_retries, input_hash
from providers import cloudflare_tts, gemini_tts

sb = load_storyboard()
model, voice = sb["models"]["tts"], sb["voice"]
tempo = voice.get("tempo", 1.0)
target, tol, max_takes = voice.get("target_pitch_hz"), voice.get("pitch_tolerance_hz", 8), voice.get("max_takes", 1)
d = OUT / "narration"
d.mkdir(parents=True, exist_ok=True)
manifest = {}
only = set(sys.argv[1:])


def synth(text):
    if model.startswith("@cf/"):
        return cloudflare_tts(model, text, voice["name"])
    return gemini_tts(model, text, voice["name"], voice.get("style_instruction"))


def to_wav(raw, path):
    """Normalise every provider to 48 kHz mono WAV, applying the tempo change."""
    af = f"atempo={tempo}," if tempo != 1.0 else ""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "-", "-af", f"{af}aresample=48000", "-ac", "1", str(path)],
                   input=raw, check=True)


def median_pitch(path):
    """Median fundamental frequency of voiced frames, by autocorrelation."""
    with wave.open(str(path)) as w:
        sr, x = w.getframerate(), np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
    f0, n = [], 4096
    for i in range(0, len(x) - n, n // 2):
        fr = x[i:i + n]
        if np.sqrt((fr ** 2).mean()) < 800:
            continue
        fr = fr - fr.mean()
        ac = np.correlate(fr, fr, "full")[n - 1:]
        lo, hi = sr // 400, sr // 60
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] > 0.3 * ac[0]:
            f0.append(sr / lag)
    return float(np.median(f0)) if f0 else 0.0


for shot in sb["shots"]:
    text = shot["narration"].strip()
    if not text:
        continue
    style = None if model.startswith("@cf/") else voice.get("style_instruction")
    h = input_hash(model, voice["name"], style, tempo, target, tol, max_takes, text)
    path = d / f"{shot['id']}_{h}.wav"
    if path.exists() and shot["id"] not in only:
        print(f"cache {shot['id']}")
    else:
        best = None
        for take in range(1, (max_takes if target else 1) + 1):
            raw, dt = with_retries(lambda: synth(text), label=f"tts {shot['id']}")
            tmp = d / f"{shot['id']}_{h}.take{take}.wav"
            to_wav(raw, tmp)
            pitch = median_pitch(tmp)
            err = abs(pitch - target) if target else 0
            log_call("narration", model, params={"voice": voice["name"], "style": style, "tempo": tempo, "chars": len(text),
                                                 "take": take, "pitch_hz": round(pitch), "target_hz": target},
                     latency_s=dt, shot=shot["id"], output=rel(tmp))
            if best is None or err < best[0]:
                best = (err, tmp, pitch, take)
            if err <= tol:
                break
        best[1].rename(path)
        for t in d.glob(f"{shot['id']}_{h}.take*.wav"):
            t.unlink()
        print(f"gen   {shot['id']} take {best[3]} pitch {best[2]:.0f} Hz")
    with wave.open(str(path)) as w:
        dur = w.getnframes() / w.getframerate()
    manifest[shot["id"]] = {"file": rel(path), "duration_s": round(dur, 2), "words": len(text.split()),
                            "pitch_hz": round(median_pitch(path))}

(d / "manifest.json").write_text(json.dumps(manifest, indent=2))
tot = sum(v["duration_s"] for v in manifest.values())
wps = sum(v["words"] for v in manifest.values()) / tot
ps = [v["pitch_hz"] for v in manifest.values()]
print(f"narration: {tot:.1f}s spoken, {wps:.2f} words/s, pitch {min(ps)}-{max(ps)} Hz")
