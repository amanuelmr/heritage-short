# Experiments

Format: hypothesis → change (one thing, seed fixed) → result (with numbers from `runs.jsonl`) → decision.

## E1. Which hosted TTS to use when Gemini is blocked
- **Hypothesis:** Cloudflare's Deepgram Aura voices are good enough for a reflective English narrator, and fast.
- **Change:** the same 20-word line (shot 1) through `@cf/deepgram/aura-2-en` and `@cf/deepgram/aura-1`, speaker `orion`; MeloTTS also tried.
- **Result:** Aura 2 took 5.2 s for 6.05 s of audio (3.3 words/s); Aura 1 took 1.1 s for 4.88 s of audio (4.1 words/s, rushed). MeloTTS returned `410 deprecated on 2026-11-20`.
- **Decision:** Aura 2. Over all 11 lines it measured **2.37 words/s, 60.4 s of speech** (median 4.8 s latency per line), inside the 2–2.5 words/s range the brief suggests, so no tempo change was needed (`voice.tempo = 1.0`).

## E2. Does the cache really skip unchanged work?
- **Hypothesis:** naming outputs by a hash of their inputs means a re-run makes no model calls.
- **Change:** ran `pipeline/narration.py` a second time with nothing changed.
- **Result:** 0.11 s wall time, 0 new lines in `runs.jsonl` (11 narration calls before and after).
- **Decision:** keep hash-named outputs for every stage.

## E3. A generic character description vs an explicit Habesha one
- **Hypothesis:** "young Ethiopian man" is not specific enough for FLUX.2 klein.
- **Change:** same seeds (1001–1003), description changed to "Ethiopian Habesha man from Addis Ababa, deep brown skin, short tightly curled black hair, East African facial features".
- **Result:** run 1 (`experiment: E-ref-candidates`) produced three faces that read as South Asian. Run 2 (`E-ref-ethnicity`) produced three faces that read as Habesha.
- **Decision:** keep the explicit description. The model's default for "Ethiopian" drifts toward other groups unless told the features.

## E4. Two-view character sheet vs single portrait as the reference image
- **Hypothesis:** a front plus three-quarter sheet gives klein more identity information.
- **Change:** conditioned all character shots on (a) a two-view sheet, then (b) a single head-and-shoulders portrait (seed 1004).
- **Result:** (a) klein copied **both** figures into every shot, so 7 of 8 character shots showed two identical men. (b) one man in every shot, same face in all of them.
- **Decision:** single portrait. For an image-edit model, the reference is treated as content to keep, not as a description of a person.

## E5. Reference conditioning on every shot vs only on medium shots
- **Hypothesis:** the reference fixes identity but also fixes composition, which hurts wide shots and extreme close-ups.
- **Change:** `use_reference: false` for s03, s08, s09, s11 (wide or extreme close-up); same seeds and prompts.
- **Result:** with the reference, all four came out as a front-facing chest-up portrait with the shot's background behind it (the rooftop, the night, the dawn). Without it, they followed the prompt: sitting on a ledge, tears in close-up, head down at night, looking up at a plane. Identity stayed close enough (beard, curly hair, navy jacket) because the text description is identical in every prompt.
- **Decision:** reference on for medium and close shots (s02, s04, s06, s10), off for wide and extreme close-up. A per-shot `use_reference` field was added to the schema.

## E6. Which voice stays the same person across lines
- **Hypothesis:** one speaker id is not enough; some TTS voices vary pitch between calls.
- **Change:** the same three lines (s01, s08, s10) through four voices, median pitch measured per line (`outputs/voice_samples/`, `experiment: E-voice-samples`).
- **Result:** pitch spread was Aura 2 orion 27 Hz (46 Hz in an earlier run), Aura 2 arcas 17 Hz, Aura 1 arcas 3 Hz, Gemini Charon 8 Hz.
- **Decision:** I preferred the sound of Aura 2 orion, so `narration.py` now keeps the take closest to a target pitch (135 Hz). Until the Cloudflare quota resets, the film uses Gemini Charon (see E7).

## E7. One request for the whole script vs one request per line
- **Hypothesis:** with a 10-requests-per-day Gemini TTS limit, narrating all 11 lines in one take and splitting it saves quota and keeps the voice consistent.
- **Change:** `voice.single_take: true`; the script is sent as 11 paragraphs to `gemini-3.8-flash-lite-tts` and split at pauses.
- **Result:** 1 request instead of 11; pitch range 90–125 Hz across lines. Splitting at the 10 longest pauses failed (7 of 11 lines got an impossible speaking rate, because the longest pauses were inside staccato lines like "Passed. Interview. Passed."). Choosing pauses near where each line is expected to end (dynamic programming over pauses, expected time from word count) got 9 of 11 right. Counting each sentence break as two words of time got all 11 to plausible rates (1.3–3.9 words/s), with no extra API calls.
- **Decision:** single take for Gemini. The trade-off: changing one line regenerates the whole take, so for the "change one shot" demo the per-line Aura mode is better.

## E8. One-pass vs two-pass loudness normalisation
- **Hypothesis:** a single `loudnorm` pass in the filter graph lands close enough to the -14 LUFS platform target.
- **Change:** (a) single pass `loudnorm=I=-14:TP=-1` on the mix; (b) render a premaster, measure it, then apply the measured values with `linear=true`; (c) as (b) with `alimiter=limit=0.5` on the mix first.
- **Result (ffmpeg `ebur128`):** (a) -15.7 LUFS; (b) -15.3 LUFS, because linear gain would have pushed the voice peaks past -1 dBTP, so loudnorm fell back; (c) **-14.4 LUFS, peak -0.8 dBFS**, the same for both aspect ratios.
- **Decision:** (c). Balance the layers, limit the peaks, then set the loudness, the order the brief's tips describe.

## E9. Centre crop vs top-biased crop for 16:9 from square keyframes
- **Hypothesis:** square keyframes keep faces in the upper half, so a centre crop to 16:9 cuts foreheads.
- **Change:** crop y offset from 0.5 to 0.25 of the spare height (`CROP_Y`); 9:16 is unaffected (it crops the sides).
- **Result:** in the first 16:9 render, the top of the head was cut off in s02 and s10. With 0.25 the full head is in frame with headroom (checked on frames at 12 s and 62 s).
- **Decision:** keep 0.25. Composing keyframes square with the subject centred, as the brief suggests, is what lets one image serve both aspect ratios.

## E10. How hard to duck the score under the voice
- **Hypothesis:** the brief's starting point (`sidechaincompress` threshold 0.02, ratio 6, attack 300 ms, release 1500 ms) ducks enough; a higher threshold would leave more music under the voice.
- **Change:** only the threshold, at 0.02, 0.05 and 0.1, with the real narration track as the sidechain and a steady pink-noise bed standing in for music, so the measurement shows the ducking and not the music's own dynamics. Music level measured under speech and in the pauses after the release (`experiment: E10-ducking` in `runs.jsonl`).
- **Result:** ducking depth **15.9 dB** at 0.02, 9.5 dB at 0.05, 4.8 dB at 0.1. The level in pauses is the same in all three (about 50 dB on the same scale), so only the depth under speech changes.
- **Decision:** keep 0.02. 10–15 dB under speech is the usual target for music under dialogue, and the music still rises in the pauses, which matters at "For weeks, I couldn't look up."

## E11. Fixed-width subtitle wrapping vs sentence-aware cards
- **Hypothesis:** wrapping every line at 40 characters, two lines per card, splits sentences across cards and leaves stray words; my rough-cut review saw a card ending on "I".
- **Change:** `_chunks` in `pipeline/subtitles.py` now packs whole sentences into a card when they fit in two lines and only wraps a sentence that is too long by itself.
- **Result:** over the 11 narration lines, fixed wrap made 17 cards, **5 ending mid-sentence** and 4 ending on a one-word line. Sentence-aware made 18 cards, **0 ending mid-sentence** and 2 ending on a one-word line (both are the second line of a sentence that ends naturally, e.g. "... the sky / closed.").
- **Decision:** sentence-aware. One extra card is a small price for subtitles that read as sentences.

## E12. Three score candidates, one choice
- **Hypothesis:** with ACE-Step, the seed changes the piece more than the caption does, so it is worth generating several and choosing by ear, the way the brief describes a composer's sketchbook.
- **Change:** one caption ("instrumental cinematic ambient score, warm analog synth pads, soft felt piano, gentle strings, hopeful and reflective, slow build, airy texture, no vocals"), 72 BPM, D major, 85 s, three seeds (7, 42, 2026), ACE-Step 1.5 turbo with the LM planner, on a Kaggle T4 (about 67 s of GPU time per candidate, model load excluded).
- **Result:** the three differ most in dynamics (ffmpeg `ebur128` on the raw tracks): seed 7 at -19.8 LUFS with an 18.3 LU loudness range (quiet start, large build); seed 42 at -15.7 LUFS, 8.3 LU (full throughout); seed 2026 at -18.0 LUFS, 5.7 LU (an even bed). I listened to each under the narration, ducked as in the film (`outputs/music/previews/`).
- **Decision:** seed 7, my choice by ear. Its wide range suits the film's shape: quiet under the opening, a build through the "Passed" shots, and space for the silence at "Not cleared". After ducking and mastering, the film measures -14.8 LUFS, peak -0.9 dBFS.
