"""Shared helpers: storyboard loading and validation, runs.jsonl logging, caching, retries."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
RUNS = ROOT / "runs.jsonl"
STORYBOARD = ROOT / "storyboard.json"
SCHEMA = ROOT / "schema" / "storyboard.schema.json"

load_dotenv(ROOT / ".env")


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return value


def load_storyboard(path: Path = STORYBOARD) -> dict:
    """Load and validate the storyboard. Every stage calls this first."""
    data = json.loads(path.read_text())
    schema = json.loads(SCHEMA.read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    ids = [s["id"] for s in data.get("shots", [])]
    problems = [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors]
    if len(ids) != len(set(ids)):
        problems.append("shots: duplicate shot ids")
    for cue in data.get("music", {}).get("cues", []):
        for key in ("from_shot", "to_shot"):
            if cue[key] not in ids:
                problems.append(f"music.cues.{cue['id']}.{key}: unknown shot {cue[key]}")
    if problems:
        sys.exit("storyboard.json is invalid:\n  " + "\n  ".join(problems))
    return data


def input_hash(*parts) -> str:
    """Stable short hash of a stage's inputs. Output files are named by it, so a
    changed prompt, seed or model produces a new file and an unchanged one is a cache hit."""
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def log_call(stage: str, model: str, *, params: dict, seed=None, latency_s: float,
             status: str = "ok", cost_usd: float = 0.0, gpu_s: float | None = None,
             shot: str | None = None, output: str | None = None, error: str | None = None,
             experiment: str | None = None) -> None:
    """Append one line per model call to runs.jsonl."""
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage": stage, "shot": shot, "model": model, "params": params, "seed": seed,
        "latency_s": round(latency_s, 3), "gpu_s": gpu_s, "cost_usd": cost_usd,
        "status": status, "output": output, "error": error, "experiment": experiment,
    }
    with RUNS.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def with_retries(fn, *, attempts: int = 4, base_delay: float = 3.0, label: str = "call"):
    """Run fn() with exponential backoff. Returns (result, latency_s of the successful try)."""
    last = None
    for i in range(1, attempts + 1):
        t0 = time.monotonic()
        try:
            return fn(), time.monotonic() - t0
        except Exception as exc:  # noqa: BLE001 - we log and retry any provider failure
            last = exc
            if i == attempts:
                break
            delay = base_delay * 2 ** (i - 1)
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                delay = max(delay, 20)
            print(f"  {label} failed ({i}/{attempts}): {msg[:160]} — retrying in {delay:.0f}s")
            time.sleep(delay)
    raise last if last else RuntimeError(label)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def check_http(resp) -> None:
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")
