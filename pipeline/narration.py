"""Stage: narration. One WAV per shot, cached by hash of (model, voice, style, tempo, text).
Supports Cloudflare Deepgram Aura (`@cf/...`) and Gemini TTS (`gemini-...`)."""
import json
import subprocess
import sys
import tempfile
import wave

from common import OUT, load_storyboard, log_call, rel, with_retries, input_hash
from providers import cloudflare_tts, gemini_tts

sb = load_storyboard()
model, voice = sb["models"]["tts"], sb["voice"]
tempo = voice.get("tempo", 1.0)
d = OUT / "narration"
d.mkdir(parents=True, exist_ok=True)
manifest = {}
only = set(sys.argv[1:])


def synth(text):
    if model.startswith("@cf/"):
        return cloudflare_tts(model, text, voice["name"]), "mp3"
    return gemini_tts(model, text, voice["name"], voice.get("style_instruction")), "wav"


def to_wav(raw, ext, path):
    """Normalise every provider to 48 kHz mono WAV, applying the tempo change."""
    with tempfile.NamedTemporaryFile(suffix=f".{ext}") as tmp:
        tmp.write(raw)
        tmp.flush()
        af = f"atempo={tempo}," if tempo != 1.0 else ""
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-af", f"{af}aresample=48000",
                        "-ac", "1", str(path)], check=True)


for shot in sb["shots"]:
    text = shot["narration"].strip()
    if not text:
        continue
    style = voice.get("style_instruction") if not model.startswith("@cf/") else None
    h = input_hash(model, voice["name"], style, tempo, text)
    path = d / f"{shot['id']}_{h}.wav"
    if path.exists() and shot["id"] not in only:
        print(f"cache {shot['id']}")
    else:
        (raw, ext), dt = with_retries(lambda: synth(text), label=f"tts {shot['id']}")
        to_wav(raw, ext, path)
        log_call("narration", model, params={"voice": voice["name"], "style": style, "tempo": tempo, "chars": len(text)},
                 latency_s=dt, shot=shot["id"], output=rel(path))
        print(f"gen   {shot['id']} {dt:.1f}s")
    with wave.open(str(path)) as w:
        dur = w.getnframes() / w.getframerate()
    manifest[shot["id"]] = {"file": rel(path), "duration_s": round(dur, 2), "words": len(text.split())}

(d / "manifest.json").write_text(json.dumps(manifest, indent=2))
tot = sum(v["duration_s"] for v in manifest.values())
wps = sum(v["words"] for v in manifest.values()) / tot
print(f"narration: {tot:.1f}s spoken, {wps:.2f} words/s")
