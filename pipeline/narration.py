"""Stage: narration. One WAV per shot via Gemini TTS, cached by hash of (model, voice, style, text)."""
import json
import sys
import wave

from common import OUT, load_storyboard, log_call, rel, with_retries, input_hash
from providers import gemini_tts

sb = load_storyboard()
model, voice = sb["models"]["tts"], sb["voice"]
d = OUT / "narration"
d.mkdir(parents=True, exist_ok=True)
manifest = {}
only = set(sys.argv[1:])

for shot in sb["shots"]:
    text = shot["narration"].strip()
    if not text:
        continue
    h = input_hash(model, voice["name"], voice.get("style_instruction"), text)
    path = d / f"{shot['id']}_{h}.wav"
    if path.exists() and shot["id"] not in only:
        print(f"cache {shot['id']}")
    else:
        audio, dt = with_retries(lambda: gemini_tts(model, text, voice["name"], voice.get("style_instruction")), label=f"tts {shot['id']}")
        path.write_bytes(audio)
        log_call("narration", model, params={"voice": voice["name"], "style": voice.get("style_instruction"), "chars": len(text)},
                 latency_s=dt, shot=shot["id"], output=rel(path))
        print(f"gen   {shot['id']} {dt:.1f}s")
    with wave.open(str(path)) as w:
        dur = w.getnframes() / w.getframerate()
    manifest[shot["id"]] = {"file": rel(path), "duration_s": round(dur, 2), "words": len(text.split())}

(d / "manifest.json").write_text(json.dumps(manifest, indent=2))
tot = sum(v["duration_s"] for v in manifest.values())
wps = sum(v["words"] for v in manifest.values()) / tot
print(f"narration: {tot:.1f}s spoken, {wps:.2f} words/s")
