"""Stage: music. ACE-Step 1.5 score candidates, one per seed in storyboard music.seeds, made either on the
official ACE-Step Space (ZeroGPU, `music.backend: hf_space`) or on our own Kaggle T4 kernel (`kaggle`).
Cached by hash of (model, caption, bpm, key, duration, seed). music.chosen names the candidate the edit uses."""
import json
import shutil
import subprocess
import time

from common import OUT, ROOT, load_storyboard, log_call, rel, input_hash
from kaggle_job import run_kernel, upload_inputs

sb = load_storyboard()
m = sb["music"]
d = OUT / "music"
d.mkdir(parents=True, exist_ok=True)
want = {seed: d / f"score_{seed}_{input_hash(sb['models']['music'], m['caption'], m.get('bpm'), m.get('key'), m['duration_s'], seed)}.wav"
        for seed in m.get("seeds", [42])}
missing = [s for s, p in want.items() if not p.exists()]

def space_generate(seed):
    """One instrumental candidate from ACE-Step/Ace-Step-v1.5 via gradio_client. Returns (path, seconds)."""
    from gradio_client import Client
    from common import env
    c = Client("ACE-Step/Ace-Step-v1.5", token=env("HF_TOKEN"), verbose=False)
    ep = c.view_api(return_format="dict", print_info=False)["named_endpoints"]["/generation_wrapper"]
    args = {p["parameter_name"]: p.get("parameter_default") for p in ep["parameters"]}
    args = {k: int(v) if isinstance(v, float) and v.is_integer() else v for k, v in args.items()}  # API wants ints
    args.update(selected_model="acestep-v15-xl-turbo", generation_mode="custom", param_4=m["caption"],
                param_5="[Instrumental]", param_6=int(m["bpm"]), param_7=m.get("key", ""), param_8="4",
                param_12=False, param_13=str(seed), param_15=int(m["duration_s"]), param_16=1, param_30="flac",
                param_43=False, param_44=False)
    t = time.monotonic()
    r = c.predict(api_name="/generation_wrapper", **args)
    if not r[0]:
        raise RuntimeError(f"space returned no audio: {r[10]}")
    return r[0], time.monotonic() - t


if missing and m.get("backend") == "hf_space":
    for seed in missing:
        try:
            src, dt = space_generate(seed)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "48000", str(want[seed])], check=True)
            log_call("music", sb["models"]["music"], params={"caption": m["caption"], "bpm": m.get("bpm"), "key": m.get("key"),
                     "duration": m["duration_s"], "backend": "hf_space ACE-Step/Ace-Step-v1.5 (ZeroGPU)"},
                     seed=seed, latency_s=dt, output=rel(want[seed]))
            print(f"seed {seed}: {dt:.0f}s")
        except Exception as e:
            log_call("music", sb["models"]["music"], params={"backend": "hf_space"}, seed=seed, latency_s=0,
                     status="error", error=str(e)[:300])
            print(f"seed {seed}: ERROR {str(e)[:200]}")
    missing = [s for s, p in want.items() if not p.exists()]

if missing and m.get("backend", "kaggle") == "kaggle":
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
