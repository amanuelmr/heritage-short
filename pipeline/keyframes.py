"""Stage: keyframes. Reference sheet first, then one image per shot conditioned on the
style block and character description (and the reference image if the model supports it).
Cached by hash of (model, prompt, seed, reference)."""
import json
import sys

from common import OUT, ROOT, load_storyboard, log_call, rel, with_retries, input_hash
from providers import cloudflare_image

sb = load_storyboard()
style, char = sb["style"]["style_block"], sb["style"]["character"]
use_ref = "--ref" in sys.argv
only = {a for a in sys.argv[1:] if not a.startswith("--")}
model = sb["models"]["image_ref"] if use_ref else sb["models"]["image"]
d = OUT / "keyframes"
d.mkdir(parents=True, exist_ok=True)


def generate(key, prompt, seed, ref=None):
    h = input_hash(model, prompt, seed, input_hash(ref) if ref else None)
    path = d / f"{key}_{h}.png"
    if path.exists() and key not in only:
        print(f"cache {key}")
        return path
    img, dt = with_retries(lambda: cloudflare_image(model, prompt, seed=seed, reference_png=ref), label=f"img {key}")
    path.write_bytes(img)
    log_call("keyframes", model, params={"prompt": prompt, "steps": 4, "ref": bool(ref)}, seed=seed,
             latency_s=dt, shot=key, output=rel(path))
    print(f"gen   {key} {dt:.1f}s")
    return path


ref_prompt = f"{char.get('reference_prompt', '')}, {char['description']}, {style}"
ref_path = generate("ref_" + char["id"], ref_prompt, char.get("reference_seed", 1))
ref_bytes = ref_path.read_bytes() if use_ref else None

manifest = {"reference": rel(ref_path), "model": model, "shots": {}}
for shot in sb["shots"]:
    who = f"{char['description']}, " if shot.get("show_character", True) else ""
    prompt = f"{shot['image_prompt']}, {who}{style}"
    p = generate(shot["id"], prompt, shot["seed"], ref_bytes if shot.get("show_character", True) else None)
    manifest["shots"][shot["id"]] = rel(p)
(d / "manifest.json").write_text(json.dumps(manifest, indent=2))
