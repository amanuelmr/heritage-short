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


def choose_cuts(runs, shots, n_frames):
    """Pick one pause per line boundary. Boundary k is expected where the words so far would end
    at an even speaking rate; among pauses in order, choose the set that stays close to those
    expected times and prefers longer pauses (dynamic programming)."""
    # a sentence break costs about as long as two words, so staccato lines ("Passed. Interview.") get more time
    words = np.array([len(s["narration"].split()) + 2 * sum(s["narration"].count(p) for p in ".?!") for s in shots], float)
    expected = np.cumsum(words)[:-1] / words.sum() * n_frames
    cand = sorted((a, b) for _, a, b in runs)
    mids = np.array([(a + b) / 2 for a, b in cand])
    lens = np.array([b - a for a, b in cand], float)
    K, C, sigma = len(expected), len(cand), n_frames * 0.04
    cost = np.full((K, C), np.inf)
    back = np.zeros((K, C), int)
    unit = lambda k, c: ((mids[c] - expected[k]) / sigma) ** 2 - np.log(lens[c])
    for c in range(C):
        cost[0, c] = unit(0, c)
    for k in range(1, K):
        best, arg = np.inf, -1
        for c in range(C):
            if c > 0 and cost[k - 1, c - 1] < best:
                best, arg = cost[k - 1, c - 1], c - 1
            if arg >= 0:
                cost[k, c], back[k, c] = best + unit(k, c), arg
    c = int(np.argmin(cost[K - 1]))
    picks = [c]
    for k in range(K - 1, 0, -1):
        c = back[k, c]
        picks.append(int(c))
    return [int(mids[c]) for c in reversed(picks)]


def single_take():
    """One request for the whole script, split into one WAV per shot at the N-1 longest pauses."""
    shots = [s for s in sb["shots"] if s["narration"].strip()]
    script = "\n\n".join(s["narration"].strip() for s in shots)
    style = None  # 3.8 TTS reads inline style aloud; the lite model rejects systemInstruction
    h = input_hash(model, voice["name"], style, tempo, script)
    paths = {s["id"]: d / f"{s['id']}_{h}.wav" for s in shots}
    if all(p.exists() for p in paths.values()) and not only:
        print("cache single take")
        return paths
    full = d / f"full_{h}.wav"
    if not full.exists():
        raw, dt = with_retries(lambda: gemini_tts(model, script, voice["name"], style), label="tts full")
        to_wav(raw, full)
        log_call("narration", model, params={"voice": voice["name"], "style": style, "mode": "single_take",
                                             "chars": len(script)}, latency_s=dt, shot="all", output=rel(full))
    with wave.open(str(full)) as w:
        sr, x = w.getframerate(), np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
    hop = sr // 100                                            # 10 ms frames
    rms = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same")[::hop])
    silent = rms < max(rms) * 10 ** (-40 / 20)                 # 40 dB below the loudest frame
    runs, start = [], None
    for i, sil in enumerate(np.append(silent, False)):
        if sil and start is None:
            start = i
        elif not sil and start is not None:
            if i - start >= 15:                                # at least 150 ms
                runs.append((i - start, start, i))
            start = None
    cuts = choose_cuts(runs, shots, len(x) / hop)
    cuts = [c * hop for c in cuts]
    bounds = [0, *cuts, len(x)]
    for s, a, b in zip(shots, bounds, bounds[1:]):
        seg = x[a:b]
        voiced = np.nonzero(np.abs(seg) > 300)[0]
        pad = int(0.1 * sr)
        seg = seg[max(0, voiced[0] - pad): voiced[-1] + pad] if len(voiced) else seg
        with wave.open(str(paths[s["id"]]), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes(seg.astype(np.int16).tobytes())
        wps = len(s["narration"].split()) / (len(seg) / sr)
        flag = "" if 1.3 <= wps <= 4 else "  <-- check split"
        print(f"split {s['id']} {len(seg) / sr:5.2f}s {wps:.2f} words/s{flag}")
    return paths


single = single_take() if voice.get("single_take") else {}

for shot in sb["shots"]:
    text = shot["narration"].strip()
    if shot["id"] in single:
        path = single[shot["id"]]
        with wave.open(str(path)) as w:
            dur = w.getnframes() / w.getframerate()
        manifest[shot["id"]] = {"file": rel(path), "duration_s": round(dur, 2), "words": len(text.split()),
                                "pitch_hz": round(median_pitch(path))}
        continue
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
