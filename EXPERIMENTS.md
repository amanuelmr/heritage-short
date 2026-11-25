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
