# Walkthrough script (5 minutes max)

Screen: VS Code or a terminal with the repo open, and the GitHub page. Speak in your own words; these are cues.

## 0:00–0:30 · The film and the idea
- Play 10 seconds of `outputs/final/not_cleared_9x16.mp4` (the opening rooftop shot).
- "This is Not Cleared, a 76-second film about passing every stage of Ethiopian Airlines' trainee pilot program except the eye test. I did not edit it by hand. One file, storyboard.json, drives a pipeline that makes it."

## 0:30–1:45 · Architecture
- Open `storyboard.json` and scroll to one shot: point at `reason`, `image_prompt`, `narration`, `seed`, `motion`.
- Open `schema/storyboard.schema.json`: "every stage validates the storyboard against this schema first."
- Show the diagram in `ARCHITECTURE.md`: narration (Cloudflare Aura or Gemini), keyframes (FLUX.2 klein), moving shots and music (Wan 2.2 and ACE-Step, run on a Kaggle T4 from the command line), assembly (FFmpeg).
- "Each output is named by a hash of its inputs, so a re-run only regenerates what changed."
- Show 3 lines of `runs.jsonl`: "one line per model call: model, parameters, seed, latency."

## 1:45–3:00 · One hard decision
Pick one:
- **The voice:** "The radio cut sounded like two narrators. I measured pitch per line: Aura 2 ranged from 101 to 163 Hz with the same speaker. So the pipeline keeps the take closest to a target pitch." Show E6 in EXPERIMENTS.md.
- **The reference image:** show the two-men contact sheet vs the final one (E4, E5): "the suggested character sheet put two copies of me in every frame, so I switched to a single portrait and turned it off for wide shots."

## 3:00–4:40 · Live: change one shot
1. In `storyboard.json`, change **shot s05's `image_prompt`** (e.g. add "a single red pen" to the desk).
   (Use an image prompt, not a narration line: narration runs as one Gemini take, so a narration change regenerates every line.)
2. Run:
   ```
   make keyframes assemble
   ```
3. Point at the output: `cache s01 … cache s04`, **`gen s05`**, `cache s06 …`, and in assembly "10 cached segments".
4. Show the new last line of `runs.jsonl`: one keyframes call, `"shot": "s05"`.
5. You may pause the recording while it runs (about 10 s for the image and about 30 s per aspect ratio).

Before recording, make sure the Cloudflare daily quota is not used up (it resets at 03:00 EAT), and run
`make keyframes` once so everything else is cached.

## 4:40–5:00 · Close
- "Everything is in the repo: experiments, failures, costs. The film is labelled AI-generated on every shot."
