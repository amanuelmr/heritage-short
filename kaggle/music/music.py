"""Kaggle T4 job: ACE-Step 1.5 (turbo) score candidates, one per seed in jobs.json.
Installs ACE-Step with its own lockfile (uv sync), then runs the generation inside that env."""
import glob, json, os, subprocess, sys, textwrap

inp = os.path.dirname(glob.glob("/kaggle/input/**/jobs.json", recursive=True)[0])
ace = "/kaggle/working/ace"
sh = lambda c: subprocess.run(c, shell=True, check=True)
sh(f"git clone -q --depth 1 https://github.com/ACE-Step/ACE-Step-1.5 {ace}")
sh(f"{sys.executable} -m pip install -q uv")
sh(f"cd {ace} && uv sync -q && uv run python -m acestep.model_downloader")

gen = textwrap.dedent(f'''
import json, os, time, torch, glob, shutil
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music
job = json.load(open("{inp}/jobs.json"))
out = "/kaggle/working/music"; os.makedirs(out, exist_ok=True)
t0 = time.time()
dit, llm = AceStepHandler(), LLMHandler()
print(dit.initialize_service(project_root="{ace}", config_path="acestep-v15-turbo", device="cuda"), flush=True)
lm_ok = False
for lm in ("acestep-5Hz-lm-1.7B", "acestep-5Hz-lm-0.6B"):
    if os.path.isdir(f"{ace}/checkpoints/" + lm):
        try:
            print(llm.initialize(checkpoint_dir="{ace}/checkpoints", lm_model_path=lm, backend="pt", device="cuda"), flush=True)
            lm_ok = True; break
        except Exception as e:
            print("LM init failed", lm, e, flush=True)
load_s = time.time() - t0
log = []
for seed in job["seeds"]:
    t = time.time()
    params = GenerationParams(caption=job["caption"], lyrics="[Instrumental]", instrumental=True, bpm=job["bpm"],
                              keyscale=job["key"], duration=job["duration"], seed=seed, inference_steps=8,
                              thinking=lm_ok)
    config = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[seed], audio_format="wav")
    res = generate_music(dit, llm, params, config, save_dir=out + f"/raw_{{seed}}")
    entry = {{"seed": seed, "gpu_s": round(time.time() - t, 1), "ok": bool(res.success), "lm": lm_ok}}
    if res.success:
        shutil.copy(res.audios[0]["path"], f"{{out}}/score_{{seed}}.wav")
        entry["key"] = res.audios[0].get("key")
    else:
        entry["error"] = str(res.error)[:500]
    log.append(entry); print(entry, flush=True)
    json.dump({{"load_s": round(load_s, 1), "gpu": torch.cuda.get_device_name(0), "candidates": log}},
              open(out + "/timings.json", "w"), indent=2)
''')
open(f"{ace}/gen_job.py", "w").write(gen)
sh(f"cd {ace} && uv run python gen_job.py")
sh(f"rm -rf {ace}")  # keep only /kaggle/working/music in the output
