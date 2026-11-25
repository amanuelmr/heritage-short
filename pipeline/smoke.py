"""Call each hosted provider once, log latency to runs.jsonl, and list the real model ids.
Model names change often; this tells us which ids actually exist today."""
import time

from common import OUT, load_storyboard, log_call, with_retries
from providers import cloudflare_image, gemini_list_models, gemini_text, gemini_tts

sb = load_storyboard()
m = sb["models"]
(OUT / "smoke").mkdir(parents=True, exist_ok=True)

print("== Gemini models available to this key ==")
names = gemini_list_models()
for n in names:
    if "flash" in n or "tts" in n:
        print("  ", n)
for want in (m["text"], m["tts"]):
    if want not in names:
        print(f"!! {want} not found: pick the closest id above and update storyboard.json models")

def run(label, stage, model, fn, path, params, seed=None):
    try:
        data, dt = with_retries(fn, attempts=2, label=label)
        path.write_bytes(data if isinstance(data, bytes) else data.encode())
        log_call(stage, model, params=params, seed=seed, latency_s=dt, output=str(path.name), experiment="smoke")
        print(f"OK  {label:10s} {dt:6.2f}s -> outputs/smoke/{path.name}")
    except Exception as e:
        log_call(stage, model, params=params, seed=seed, latency_s=0, status="error", error=str(e)[:300], experiment="smoke")
        print(f"ERR {label:10s} {str(e)[:200]}")

run("text", "smoke", m["text"], lambda: gemini_text(m["text"], "Reply with exactly: pipeline ready"),
    OUT / "smoke/text.txt", {"prompt": "ping"})
run("tts", "smoke", m["tts"], lambda: gemini_tts(m["tts"], "Every morning, planes drew white lines across the sky.", sb["voice"]["name"]),
    OUT / "smoke/tts.wav", {"voice": sb["voice"]["name"]})
run("image", "smoke", m["image"], lambda: cloudflare_image(m["image"], "a small airliner over hills at dawn, painted", seed=1),
    OUT / "smoke/image.jpg", {"steps": 4}, seed=1)
if m.get("image_ref"):
    run("image_ref", "smoke", m["image_ref"], lambda: cloudflare_image(m["image_ref"], "a small airliner over hills at dawn, painted", seed=1),
        OUT / "smoke/image_ref.png", {"steps": 4}, seed=1)
