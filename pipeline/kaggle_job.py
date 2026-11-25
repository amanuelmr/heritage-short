"""Run a GPU job on Kaggle from the command line: upload inputs as a private dataset version,
push a script kernel on a T4, wait for it, download its outputs. Used by shots.py and music.py."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from common import ROOT

KAGGLE = ["uvx", "--python", "3.12", "--with", "six", "--from", "kaggle>=1.8", "kaggle"]


def kaggle(*args, check=True) -> str:
    r = subprocess.run([*KAGGLE, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"kaggle {' '.join(args)} failed: {r.stdout[-500:]} {r.stderr[-500:]}")
    return r.stdout


def username() -> str:
    out = kaggle("config", "view", check=False)
    for line in out.splitlines():
        if line.strip().startswith("- username:"):
            return line.split(":", 1)[1].strip()
    return "amanuelmandefrow"


def upload_inputs(slug: str, files: dict[str, Path | str], title: str) -> str:
    """Create or version a private dataset holding this job's inputs. Returns owner/slug."""
    user = username()
    stage = ROOT / "outputs" / ".kaggle" / slug
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    for name, src in files.items():
        dst = stage / name
        if isinstance(src, Path):
            shutil.copy(src, dst)
        else:
            dst.write_text(src)
    (stage / "dataset-metadata.json").write_text(json.dumps(
        {"id": f"{user}/{slug}", "title": title, "licenses": [{"name": "CC0-1.0"}]}))
    exists = subprocess.run([*KAGGLE, "datasets", "status", f"{user}/{slug}"], capture_output=True, text=True)
    if exists.returncode == 0 and "ready" in exists.stdout.lower():
        kaggle("datasets", "version", "-p", str(stage), "-m", time.strftime("inputs %H:%M"), "-r", "zip")
    else:
        kaggle("datasets", "create", "-p", str(stage), "-r", "zip")
    for _ in range(60):  # wait until the new version is processed
        if "ready" in kaggle("datasets", "status", f"{user}/{slug}", check=False).lower():
            break
        time.sleep(5)
    return f"{user}/{slug}"


def run_kernel(slug: str, script: Path, dataset: str, out_dir: Path, timeout_s: int = 3 * 3600) -> float:
    """Push and run the kernel on a T4, poll until done, download outputs. Returns wall seconds."""
    user = username()
    stage = ROOT / "outputs" / ".kaggle" / f"kernel-{slug}"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    shutil.copy(script, stage / script.name)
    (stage / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{slug}", "title": slug, "code_file": script.name, "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [dataset], "competition_sources": [], "kernel_sources": []}))
    t0 = time.monotonic()
    print(kaggle("kernels", "push", "-p", str(stage), "--accelerator", "NvidiaTeslaT4", "-t", str(timeout_s)).strip())
    status = ""
    while time.monotonic() - t0 < timeout_s + 600:
        time.sleep(30)
        status = kaggle("kernels", "status", f"{user}/{slug}", check=False).lower()
        print(f"  [{(time.monotonic() - t0) / 60:5.1f} min] {status.strip()[-80:]}")
        if any(s in status for s in ("complete", "error", "cancel")):
            break
    wall = time.monotonic() - t0
    out_dir.mkdir(parents=True, exist_ok=True)
    kaggle("kernels", "output", f"{user}/{slug}", "-p", str(out_dir), "-o", check=False)
    if "complete" not in status:
        raise RuntimeError(f"kernel {slug} ended with status: {status.strip()} (log saved in {out_dir})")
    return wall
