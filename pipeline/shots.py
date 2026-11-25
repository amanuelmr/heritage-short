"""Stage: moving shots. Wan 2.2 TI2V-5B on a Kaggle T4 for shots with motion "wan".
Each clip is cached by hash of (keyframe, motion prompt, seed, settings); only missing clips are
sent to Kaggle. Shots with motion "kenburns", or whose clip fails, are animated in assemble.py."""
import hashlib
import json
import shutil
import sys

from common import OUT, ROOT, load_storyboard, log_call, rel, input_hash
from kaggle_job import run_kernel, upload_inputs

sb = load_storyboard()
v = sb.get("video", {})
settings = {k: v.get(k, d) for k, d in
            {"width": 640, "height": 640, "frames": 49, "steps": 30, "guidance": 5.0}.items()}
negative = v.get("negative", "")
kf = json.loads((OUT / "keyframes/manifest.json").read_text())["shots"]
d = OUT / "shots"
d.mkdir(parents=True, exist_ok=True)
force = set(sys.argv[1:])

jobs, files, manifest = [], {}, {}
for s in sb["shots"]:
    if s["motion"] != "wan":
        continue
    img = ROOT / kf[s["id"]]
    h = input_hash(sb["models"]["video"], hashlib.sha256(img.read_bytes()).hexdigest(), s["motion_prompt"],
                   s["seed"], settings, negative)
    path = d / f"{s['id']}_{h}.mp4"
    manifest[s["id"]] = rel(path)
    if path.exists() and s["id"] not in force:
        print(f"cache {s['id']}")
        continue
    files[f"{s['id']}.png"] = img
    jobs.append({"shot": s["id"], "image": f"{s['id']}.png", "out": path.name, "seed": s["seed"],
                 "prompt": f"{s['motion_prompt']}, hand-painted illustration, gentle slow motion",
                 "negative": negative, **settings})

if jobs:
    print(f"sending {len(jobs)} shot(s) to Kaggle: {[j['shot'] for j in jobs]}")
    files["jobs.json"] = json.dumps({"shots": jobs}, indent=2)
    ds = upload_inputs("heritage-short-wan-inputs", files, "heritage-short wan inputs")
    raw = OUT / ".kaggle" / "wan-output"
    shutil.rmtree(raw, ignore_errors=True)
    wall = run_kernel("heritage-short-wan", ROOT / "kaggle/wan/wan.py", ds, raw)
    timings = json.loads(next(raw.rglob("timings.json")).read_text())
    for c in timings["clips"]:
        src = next(raw.rglob(c["out"]), None)
        if c["status"] == "ok" and src:
            shutil.move(src, d / c["out"])
        log_call("shots", sb["models"]["video"], params={k: c[k] for k in settings} | {"prompt": c["prompt"],
                 "gpu": timings["gpu"], "load_s": timings["load_s"], "kernel_wall_s": round(wall)},
                 seed=c["seed"], latency_s=c["gpu_s"], gpu_s=c["gpu_s"], shot=c["shot"],
                 status=c["status"], error=c.get("error"), output=rel(d / c["out"]))
        print(f"{c['shot']}: {c['status']} in {c['gpu_s']}s GPU")

done = {k: p for k, p in manifest.items() if (ROOT / p).exists()}
(d / "manifest.json").write_text(json.dumps(done, indent=2))
print(f"clips ready: {sorted(done)}; Ken Burns for the rest")
