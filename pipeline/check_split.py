"""Verify the narration split: transcribe every per-shot WAV in one Gemini request and compare with the
storyboard text. Exits non-zero if any shot's transcript is far from its narration line."""
import base64
import difflib
import json
import re
import sys
import time

import requests

from common import OUT, ROOT, env, load_storyboard, log_call, with_retries, check_http

MODEL = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--model=")), "gemini-2.5-flash")
sb = load_storyboard()
nar = json.loads((OUT / "narration/manifest.json").read_text())
shots = [s for s in sb["shots"] if s["id"] in nar]
# Without labels, the model treated the clips as one recording and re-split it by sentence (run 1),
# so each clip gets its own label and the reply is keyed by label.
parts = [{"text": f"There are {len(shots)} separate audio clips, each preceded by its label. Transcribe each clip on its "
                  f"own, exactly, without moving words between clips. Reply with only a JSON object mapping each label "
                  f"to its transcript."}]
for s in shots:
    parts.append({"text": f"Clip {s['id']}:"})
    parts.append({"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode((ROOT / nar[s["id"]]["file"]).read_bytes()).decode()}})


def call():
    key = env("GEMINI_API_KEY_2") if "--key2" in sys.argv else env("GEMINI_API_KEY")
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                      headers={"x-goog-api-key": key},
                      json={"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0}},
                      timeout=180)
    check_http(r)
    return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])


heard, dt = with_retries(call, label="transcribe")
norm = lambda t: re.sub(r"[^a-z' ]", "", t.lower()).split()
bad = 0
for s in shots:
    h = heard.get(s["id"]) or heard.get(f"Clip {s['id']}") or ""
    ratio = difflib.SequenceMatcher(None, norm(s["narration"]), norm(h)).ratio()
    flag = "" if ratio >= 0.85 else "   <-- MISMATCH"
    bad += ratio < 0.85
    print(f"{s['id']} {ratio:.2f}  heard: {h}{flag}")
log_call("narration-check", MODEL, params={"clips": len(shots), "mismatches": bad}, latency_s=dt, experiment="E13-split-check")
sys.exit(1 if bad else 0)
