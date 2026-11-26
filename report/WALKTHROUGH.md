# Walkthrough script (5 minutes max)

A screen recording with my voice. Speak in your own words; these are cues, not lines to read.

## Before recording (5 minutes)

1. Open VS Code on `~/Projects/heritage-short` with these tabs: `storyboard.json`, `ARCHITECTURE.md`,
   `EXPERIMENTS.md`, `runs.jsonl`. Open a terminal inside VS Code (`` Ctrl+` ``).
2. Run once so everything is cached: `make narration assemble`. Every line should say `cache`.
3. Open `outputs/final/not_cleared_9x16.mp4` in QuickTime, paused at the start.
4. Make the editor font bigger (Cmd + `+` two or three times) so the text is readable in the video.
5. Close Slack, Telegram and other notifications, and any window showing `.env` or keys.
6. Press **Cmd + Shift + 5**, choose **Record Entire Screen**, then **Options → Microphone → MacBook Microphone**.
   Click **Record**. To stop, click the stop button in the menu bar. The file lands on the Desktop.

## 0:00–0:30 · The film and the idea
- Play the first 10 seconds of the film (the rooftop and the plane).
- Say what it is: a 76-second film about passing every stage of Ethiopian Airlines' trainee pilot program except the eye test.
- "I did not edit it by hand. One file, storyboard.json, drives a pipeline that makes the whole film."

## 0:30–1:45 · How it works
- In `storyboard.json`, scroll to one shot and point at: `reason` (why the shot exists), `image_prompt`,
  `narration`, `seed`, `motion`.
- "Before any stage runs, the storyboard is checked against a JSON Schema, so a mistake stops the run before any model is called."
- Show the diagram at the top of `ARCHITECTURE.md` and name the stages:
  narration (Gemini TTS), keyframes (FLUX.2 klein on Cloudflare), moving shots and music (Wan 2.2 and ACE-Step on a free Kaggle GPU), assembly (FFmpeg).
- "Every file is named by a hash of its inputs. If nothing changed, the stage prints cache and calls nothing."
- Show a few lines of `runs.jsonl`: "one line per model call: model, settings, seed, how long it took."

## 1:45–3:00 · One hard decision: the voice
- "In the first test cut the narrator sounded like two different people."
- "I measured the pitch of every line. The same Aura voice went from 101 to 163 Hz between calls."
- Show E6 in `EXPERIMENTS.md`. "So I compared voices, and in the end the whole script is voiced in one
  request, then cut into one clip per shot using Whisper word timestamps (E7, E13)."
- One sentence on why: free quotas (10 voice requests a day), so one request for the whole film.

## 3:00–4:30 · Live: change one narration line
1. In `storyboard.json`, find shot **s10** and change the last sentence, for example
   `So I kept learning, and I built this.` → `So I kept learning, and I made this film.`
   Save. Use your own wording; any change works.
2. In the terminal run:
   ```
   make narration assemble
   ```
3. Point at the output: `cache s01 … cache s09`, **`gen s10`**, `cache s11`, then
   `11 cached segments` for the pictures. "Only the line I changed was voiced again: one request."
4. Show the last lines of `runs.jsonl`: one narration call with `"shot": "s10"`.
5. Play shot s10 in the new film (about 0:57) so the new line and subtitle are heard and seen.
6. Optional, honest point: "A line voiced on its own comes out a bit higher than in the full take (E15),
   so before the final version I re-voice the whole script in one take."

It takes about 1 minute (3 s for the voice, about 25 s per aspect ratio). You can pause the recording while it runs.

## 4:30–5:00 · Close
- "Everything is in the repo: experiments, failures, costs. The film is labelled AI-generated on every shot and on the end card."

## After recording
- Put the line back (Cmd+Z in `storyboard.json`, save) and run `make narration assemble` again: all `cache`, no calls.
  This restores the submitted film.
- Upload the recording to YouTube (Unlisted) or Google Drive ("Anyone with the link"), and test the link in a private window.

## If the Cloudflare image quota is back
You can change an image prompt instead (for example add "a single red pen on the desk" to **s05**), then run
`make keyframes assemble`: you should see `gen s05` and `10 cached segments`. Check first with one run before recording.
