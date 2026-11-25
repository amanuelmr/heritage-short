"""Thin clients for each provider. Every function returns raw bytes or text; logging is done by callers."""
from __future__ import annotations

import base64
import io
import wave

import requests

from common import check_http, env

GEMINI = "https://generativelanguage.googleapis.com/v1beta"


def gemini_list_models() -> list[str]:
    r = requests.get(f"{GEMINI}/models", params={"key": env("GEMINI_API_KEY"), "pageSize": 200}, timeout=30)
    check_http(r)
    return [m["name"].removeprefix("models/") for m in r.json().get("models", [])]


def gemini_text(model: str, prompt: str, *, json_mode: bool = False, temperature: float = 0.7) -> str:
    cfg: dict = {"temperature": temperature}
    if json_mode:
        cfg["responseMimeType"] = "application/json"
    r = requests.post(
        f"{GEMINI}/models/{model}:generateContent",
        params={"key": env("GEMINI_API_KEY")},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": cfg},
        timeout=120,
    )
    check_http(r)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def gemini_tts(model: str, text: str, voice: str, style: str | None = None) -> bytes:
    """Returns a WAV file (Gemini returns raw 24 kHz 16-bit mono PCM)."""
    prompt = f"{style}:\n{text}" if style else text
    r = requests.post(
        f"{GEMINI}/models/{model}:generateContent",
        params={"key": env("GEMINI_API_KEY")},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        },
        timeout=180,
    )
    check_http(r)
    part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
    pcm = base64.b64decode(part["data"])
    rate = 24000
    mime = part.get("mimeType", "")
    if "rate=" in mime:
        rate = int(mime.split("rate=")[1].split(";")[0])
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def cloudflare_image(model: str, prompt: str, *, seed: int, steps: int = 4,
                     reference_png: bytes | None = None, width: int = 1024, height: int = 1024) -> bytes:
    """Text-to-image (FLUX.1 schnell, JSON API) or reference-conditioned (FLUX.2, multipart API)."""
    url = f"https://api.cloudflare.com/client/v4/accounts/{env('CLOUDFLARE_ACCOUNT_ID')}/ai/run/{model}"
    headers = {"Authorization": f"Bearer {env('CLOUDFLARE_API_TOKEN')}"}
    if "flux-2" in model:
        form: dict = {"prompt": (None, prompt), "steps": (None, str(steps)), "seed": (None, str(seed)),
                "width": (None, str(width)), "height": (None, str(height))}
        if reference_png:
            form["input_image_0"] = ("ref.png", reference_png, "image/png")
        r = requests.post(url, headers=headers, files=form, timeout=180)
    else:
        r = requests.post(url, headers=headers, json={"prompt": prompt, "steps": steps}  # schnell on Workers AI rejects `seed`, timeout=180)
    check_http(r)
    if r.headers.get("content-type", "").startswith("image/"):
        return r.content
    return base64.b64decode(r.json()["result"]["image"])
