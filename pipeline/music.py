"""Stage: music. ACE-Step 1.5 score candidates on a Kaggle T4, one per seed in storyboard music.seeds.
Cached by hash of (caption, bpm, key, duration, seed). music.chosen names the candidate the edit uses."""
import json
import shutil

from common import OUT, ROOT, load_storyboard, log_call, rel, input_hash
from kaggle_job import run_kernel, upload_inputs

sb = load_storyboard()
m = sb["music"]
d = OUT / "music"
d.mkdir(parents=True, exist_ok=True)
want = {seed: d / f"score_{seed}_{input_hash(sb['models']['music'], m['caption'], m.get('bpm'), m.get('key'), m['duration_s'], seed)}.wav"
        for seed in m.get("seeds", [42])}
missing = [s for s, p in want.items() if not p.exists()]

if missing:
    print(f"sending {len(missing)} candidate(s) to Kaggle: seeds {missing}")
    job = {"caption": m["caption"], "bpm": m.get("bpm"), "key": m.get("key", ""), "duration": m["duration_s"], "seeds": missing}
    ds = upload_inputs("heritage-short-music-inputs", {"jobs.json": json.dumps(job, indent=2)}, "heritage-short music inputs")
    raw = OUT / ".kaggle" / "music-output"
    shutil.rmtree(raw, ignore_errors=True)
    wall = run_kernel("heritage-short-music", ROOT / "kaggle/music/music.py", ds, raw)
    t = json.loads(next(raw.rglob("timings.json")).read_text())
    for c in t["candidates"]:
        src = next(raw.rglob(f"score_{c['seed']}.wav"), None)
        if c["ok"] and src:
            shutil.move(src, want[c["seed"]])
        log_call("music", sb["models"]["music"], params={"caption": m["caption"], "bpm": m.get("bpm"), "key": m.get("key"),
                 "duration": m["duration_s"], "lm_planner": c.get("lm"), "gpu": t["gpu"], "load_s": t["load_s"],
                 "kernel_wall_s": round(wall)}, seed=c["seed"], latency_s=c["gpu_s"], gpu_s=c["gpu_s"],
                 status="ok" if c["ok"] else "error", error=c.get("error"), output=rel(want[c["seed"]]))
        print(c)

ready = {str(s): rel(p) for s, p in want.items() if p.exists()}
(d / "manifest.json").write_text(json.dumps({"candidates": ready, "chosen": m.get("chosen")}, indent=2))
print("candidates:", ready)
