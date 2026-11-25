# Failures

## 1. Homebrew ffmpeg has no subtitle or text filters
- **What broke:** burning subtitles into the radio cut failed with `No such filter: 'subtitles'`. The `drawtext` filter is also missing: the default Homebrew ffmpeg 8.1.2 is built without libass and libfreetype.
- **Tried:** escaping the `force_style` argument first (the first error was a parse error), which only revealed the real problem.
- **Fix:** render each subtitle card as a transparent PNG with Pillow and composite it with ffmpeg's `overlay` filter, using `enable='between(t,a,b)'` (`pipeline/subtitles.py`). This works with any ffmpeg build, so a stranger's clean clone does not need a special ffmpeg.

## 2. Gemini key returns HTTP 402 "prepayment credits are depleted"
- **What broke:** the smoke test listed models fine (`gemini-3.8-flash`, `gemini-3.8-flash-tts` both exist), but every `generateContent` call returned `402 Your prepayment credits are depleted`.
- **Why:** the key belongs to an AI Studio project with prepaid billing attached and no credit left. A billed project does not fall back to the free tier.
- **Fix:** *(in progress)* create a key in a project with no billing attached, so it uses the free tier.

## 3. FLUX.1 schnell on Workers AI rejects a seed
- **What broke:** `400 AiError: Additional or unevaluated properties '/seed' ... not allowed`.
- **Why:** the Workers AI schema for `@cf/black-forest-labs/flux-1-schnell` accepts only `prompt` and `steps`. Without a seed, a schnell image cannot be reproduced, which breaks the "same inputs, same output" rule the cache depends on.
- **Fix:** made `@cf/black-forest-labs/flux-2-klein-4b` the main image model. It accepts a seed and a reference image, and the smoke call took 8.2 s. schnell is kept as `image_alt` for a comparison experiment only, with the seed dropped from its payload.
- **Also noticed:** the klein smoke image invented an airline logo on the tail. The style block's "no logos, no letters" is needed, and every keyframe gets a quick check for marks.

## 4. The second Gemini key also returned 402
- **What broke:** a new key (`AQ.` format) gave `402 prepayment credits are depleted` on every model, from `gemini-2.5-flash` to `gemini-3.8-flash`.
- **Why:** the new key appears to sit under the same prepaid-billing setup, so the free tier never applies.
- **Workaround:** moved narration to Deepgram Aura 2 on Cloudflare Workers AI, which uses the token that already works (see E1). `narration.py` picks the provider from the model id (`@cf/...` or `gemini-...`), and Gemini TTS stays as `models.tts_alt`, so switching back is a one-line storyboard change.
- **Side note:** while debugging I used `curl .../$m:generateContent` in zsh. zsh read `:g` as a history modifier, so every URL was mangled into a 404. Writing `${m}` fixed it.

## 5. Reference sheet duplicated the character, and reference overrode composition
- See E4 and E5. Two separate failures: two men in every frame, then a front-facing portrait pasted over every wide shot. Fixed with a single-portrait reference and a per-shot `use_reference` flag.

## 6. Content filter false positive on a portrait
- **What broke:** `400 Your output has been flagged` on the plain portrait prompt, twice, for seed 1001 (no unsafe content in the prompt).
- **Fix:** the retry with backoff in `common.with_retries` got through on attempt 2 or 3. Logged as errors in `runs.jsonl`.

## 7. s07 generated an unrelated woman and readable text
- **What broke:** "close-up of an eye examination room" gave a woman's portrait and an eye chart with letter-like text, even though the shot has `show_character: false`.
- **Fix:** rewrote the prompt as "an empty eye examination room with no people, an eye chart far away ... so out of focus that no letters can be read".

## 8. Aura 2 voice drifts between lines, then the Cloudflare daily quota ran out
- **What broke:** listening to the radio cut, I heard what sounded like two different narrators. Measuring median pitch per line showed Aura 2 `orion` ranging from 101 to 163 Hz with the same speaker setting (experiment `E-voice-stability` in `runs.jsonl`).
- **Tried:** compared four voices on the same three lines (`outputs/voice_samples/`): pitch spread was Aura 2 orion 27–46 Hz, Aura 2 arcas 15–17 Hz, Aura 1 arcas 3–8 Hz, Gemini Charon 8 Hz. I still preferred the sound of orion.
- **Fix:** `narration.py` now generates up to `max_takes` takes per line and keeps the one closest to `target_pitch_hz` (135 Hz, the line I liked).
- **New blocker:** while regenerating, Cloudflare returned `429 you have used up your daily free allocation of 10,000 neurons` after 8 takes. The same allowance pays for keyframes, so the ~50 images and ~40 TTS calls of the day used it up. It resets at 00:00 UTC (03:00 EAT).
