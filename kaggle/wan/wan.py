"""Kaggle T4 job: Wan 2.2 TI2V-5B image-to-video for the shots listed in jobs.json.
Each clip is saved as soon as it is done, with its timing, so a timeout keeps finished work."""
import glob, json, os, subprocess, sys, time

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.35", "transformers", "accelerate",
                "ftfy", "imageio", "imageio-ffmpeg"], check=True)
import torch
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
from diffusers.utils import export_to_video, load_image

inp = os.path.dirname(glob.glob("/kaggle/input/**/jobs.json", recursive=True)[0])
jobs = json.load(open(f"{inp}/jobs.json"))
out = "/kaggle/working/clips"
os.makedirs(out, exist_ok=True)
log = []

t0 = time.time()
mid = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
dtype = torch.float16  # the T4 has no fast bfloat16
vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
pipe = WanImageToVideoPipeline.from_pretrained(mid, vae=vae, torch_dtype=dtype)
pipe.enable_model_cpu_offload()
load_s = time.time() - t0
print(f"loaded in {load_s:.0f}s on {torch.cuda.get_device_name(0)}", flush=True)

for job in jobs["shots"]:
    t = time.time()
    try:
        img = load_image(f"{inp}/{job['image']}").resize((job["width"], job["height"]))
        frames = pipe(image=img, prompt=job["prompt"], negative_prompt=job.get("negative", ""),
                      height=job["height"], width=job["width"], num_frames=job["frames"],
                      num_inference_steps=job["steps"], guidance_scale=job["guidance"],
                      generator=torch.Generator("cuda").manual_seed(job["seed"])).frames[0]
        path = f"{out}/{job['out']}"
        export_to_video(frames, path, fps=24)
        mean = float(sum(f.mean() for f in frames) / len(frames))
        status = "ok" if mean > 0.02 else "black_frames"
        log.append({**job, "status": status, "gpu_s": round(time.time() - t, 1), "mean_pixel": round(mean, 3)})
    except Exception as e:  # keep going so one bad shot does not lose the others
        log.append({**job, "status": "error", "error": str(e)[:500], "gpu_s": round(time.time() - t, 1)})
    print(log[-1], flush=True)
    json.dump({"load_s": round(load_s, 1), "gpu": torch.cuda.get_device_name(0), "clips": log},
              open(f"{out}/timings.json", "w"), indent=2)
