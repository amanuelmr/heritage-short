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
