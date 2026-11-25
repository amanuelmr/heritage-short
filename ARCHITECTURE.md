# Architecture

```
                     storyboard.json  ──validate──▶  schema/storyboard.schema.json
                            │
      ┌──────────────┬──────┴───────┬───────────────┬──────────────┐
      ▼              ▼              ▼               ▼              │
  narration      keyframes   ──▶  shots           music            │
  (Aura/Gemini)  (FLUX.2 klein)   (Wan 2.2,       (ACE-Step 1.5,   │
      │              │             Kaggle T4)      Kaggle T4)      │
      ▼              ▼              ▼               ▼              ▼
  outputs/narration/ outputs/keyframes/ outputs/shots/ outputs/music/
      │  manifest.json   manifest.json    manifest.json   manifest.json
      └──────────────┴──────────────┴──────────┬────┘
                                               ▼
                                   assemble (FFmpeg + Pillow)
                                               ▼
                         outputs/final/not_cleared_{9x16,16x9}.mp4 + .srt
```

## The contract

`storyboard.json` is the only input a person edits. It holds the title, audience and intent; the model ids;
the style block and character description; the voice; 8–12 shots (duration, shot size, **reason**, image
prompt, motion prompt, narration, seed, motion type, Ken Burns move, music cue); the score caption and
seeds; and the end card text.

Every stage starts with `common.load_storyboard()`, which validates the file against the JSON Schema and
checks cross-references (unique shot ids, music cues pointing at real shots). An invalid storyboard stops
the run before any model is called. The schema also enforces a few rules of the brief: 8–12 shots, an end
card text that contains "AI", and Wan sizes that are multiples of 32.

Stages talk to each other only through files. Each stage writes its outputs and a `manifest.json` that maps
shot ids to files. The next stage reads the manifest and never needs to know which provider made the file.
Narration, for example, switched from Aura to Gemini and back without any change to assembly.

## Caching

Every output is named after a hash of everything that affects it (`common.input_hash`):

| Stage | Hash inputs |
|---|---|
| narration | model, voice, style, tempo, pitch target, text (single-take mode: the whole script) |
| keyframes | model, full prompt (style block and character included), seed, hash of the reference image |
| shots | video model, hash of the keyframe file, motion prompt, seed, Wan settings |
| music | model, caption, bpm, key, duration, seed |
| assembly segments | shot id, size, duration, source file hashes, Ken Burns move, crop, `SEGMENT_VERSION` |

If the file exists, the stage prints `cache` and makes no call. Changing one shot's image prompt changes
only that keyframe's hash, then that shot's Wan clip (if any) and its assembly segment; the other shots are
reused. A re-run of narration with nothing changed takes 0.11 s and makes no calls (EXPERIMENTS E2).

The hash must cover code as well as data: after a crop change the assembly reused stale segments until
`SEGMENT_VERSION` was added to the key (FAILURES 10).

## Failure handling

- **Retries:** `common.with_retries` retries any provider call with exponential backoff (3 s, 6 s, 12 s), and
  waits at least 20 s on a 429 or `RESOURCE_EXHAUSTED`. It handled the Cloudflare content-filter false
  positives and Gemini's per-minute limits without stopping the run.
- **Quota exhaustion:** a daily quota is not retried forever; the stage stops with the provider's message, and
  everything already generated stays cached, so the next run continues where this one stopped.
- **Provider fallback by configuration:** the model id decides the provider (`@cf/...` is Cloudflare,
  `gemini-...` is Gemini). Switching voice provider is a one-line storyboard change (FAILURES 4, 9).
- **Voice consistency:** Aura 2 drifts in pitch between calls, so narration can generate several takes and keep
  the one closest to `voice.target_pitch_hz`. Gemini's 10-a-day limit led to `voice.single_take`: one request
  for the script, split per shot by a dynamic-programming search over pauses (EXPERIMENTS E6, E7).
- **GPU jobs:** `kaggle_job.py` uploads the inputs as a private dataset version, pushes a script kernel on a T4,
  polls its status, and downloads the outputs. The Kaggle scripts save each clip or score as soon as it is
  done, with timings, so a timeout keeps the finished work. A clip with black frames is marked
  `black_frames` and not used.
- **Graceful degradation:** a shot without a Wan clip falls back to a Ken Burns move over its keyframe; a film
  without a chosen score uses a quiet placeholder pad. The film can always be assembled.

## Assembly

1. **Timeline:** each shot lasts `max(storyboard duration, spoken narration + 1 s)`, so the voice sets the pace.
2. **Picture:** each shot is rendered to its own cached segment. A Wan clip is cropped to the aspect,
   trimmed by 0.25 s at the start, slowed at most 1.6x, and its last frame held. Otherwise the square
   keyframe is cropped (top-biased for 16:9) and given a slow `zoompan` move. Segments are joined with
   0.5 s dissolves, and the AI end card closes the film.
3. **Text:** subtitles and the "AI-generated" badge are Pillow PNGs composited with `overlay`, because the
   Homebrew ffmpeg build has no `subtitles` or `drawtext` filter (FAILURES 1).
4. **Sound:** narration at -16 LUFS; the score at -24 LUFS, muted for the "silence" cue (shots 7–8), faded,
   and ducked under the voice with `sidechaincompress` (threshold 0.02, ratio 6, attack 300 ms, release 1500 ms);
   a limiter; then two-pass `loudnorm` to -14 LUFS and -1 dBTP (EXPERIMENTS E8).
5. **Export:** H.264, AAC 192 kbps, 24 fps, `+faststart`, in 1080x1920 and 1920x1080.

## Logging

`common.log_call` appends one JSON line per model call to `runs.jsonl`: time, stage, shot, model,
parameters, seed, latency, GPU seconds, cost, status, output path, error, and an `experiment` tag when the
call belongs to an experiment. COSTS.md is computed from it.
