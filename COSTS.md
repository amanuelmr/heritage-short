# Costs

All numbers below are measured from `runs.jsonl` (25 Nov 2026), except the list prices, which are noted
with their source. The film was made entirely on free tiers: **$0 spent.**

## Free limits we actually hit

| Provider | What the brief or docs suggested | What we measured |
|---|---|---|
| Gemini API, text and TTS | "free tier" | The first two keys returned `402 prepayment credits are depleted` (billed project). On a clean project: **10 requests per day per model** for TTS (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`), plus a per-minute limit. Image models: **0 free** (429 on every key) |
| Cloudflare Workers AI | "roughly 50–170 images a day" | **10,000 neurons per day**, used up after 41 images and about 52 TTS calls (plus 3 smoke images). Resets at 00:00 UTC |
| Kaggle | "about 30 GPU hours a week" | 30 h GPU and 20 h TPU per week shown in Settings; free GPU jobs wait in a queue before starting |

## Latency per stage

| Stage | Model | Calls | Median latency | Total |
|---|---|---|---|---|
| Keyframes | FLUX.2 klein 4B (Workers AI) | 35 (+3 smoke) | 9.8 s per image | 6.2 min |
| Narration | Deepgram Aura 2 (Workers AI) | 41 | 5.2 s per line | 3.5 min |
| Narration | Deepgram Aura 1 (Workers AI) | 11 | 1.3 s per line | 0.2 min |
| Narration | Gemini 3.8 Flash TTS | 14 | 5.9 s per line | 1.4 min |
| Narration | Gemini 3.8 Flash-Lite TTS, whole script in one take | 2 | 9.1 s per script | 0.3 min |
| Assembly | FFmpeg, both aspect ratios | 9 | 32 s per aspect ratio | 5.1 min (local CPU, Apple M4) |
| Moving shots | Wan 2.2 TI2V-5B, Kaggle T4 | *pending* | | |
| Music | ACE-Step 1.5 turbo, Kaggle T4 | *pending* | | |

Wall-clock latency includes network time and, for Cloudflare, occasional cold starts (the first smoke image
took 8.2 s; later images on the same model ranged from 7.3 s to 15 s).

A cached re-run of narration takes 0.11 s; a re-render that reuses all 11 shot segments takes about 26 s
per aspect ratio, against about 42 s from scratch.

## List-price equivalent

| Item | Usage | List price | Equivalent |
|---|---|---|---|
| Cloudflare Workers AI (keyframes and Aura TTS together) | one full day's allowance, 10,000 neurons | $0.011 per 1,000 neurons (Workers AI paid pricing) | **about $0.11** |
| Gemini TTS | 16 requests | free tier only; paid price not verified | not counted |
| Kaggle T4 | *pending* (GPU minutes from `runs.jsonl`, field `gpu_s`) | about $0.35 per T4 GPU-hour on-demand in public clouds (approximate) | *pending* |
| Local assembly | 5 min CPU | own machine | $0 |

The binding constraint was never money. It was daily quotas, which shaped the design: take selection by pitch
for Aura, a single-take mode for Gemini TTS, and reference images only where they help (see FAILURES 8–9 and
EXPERIMENTS E5–E7).

## Frontier comparison

Not run. The frontier image models (Gemini image, "Nano Banana") returned 429 with zero free quota on every
key we had, and no organisation key was provided.
