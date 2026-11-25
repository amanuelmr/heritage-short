# Design

*Written before any image, clip or music was generated (25 Nov 2026).*

## Audience
Young Ethiopians who have been told "no" on a dream, plus my family and my cohort.
They watch on a phone, vertical, often with the sound low, so the English subtitles are burned in.

## Intent
At the end they should feel that **a rejection closes one runway, not the sky.**

## Story
I have been obsessed with aviation for years. I watched documentaries, not to study,
just to be near it, and read whatever I could find online. I applied to Ethiopian Airlines'
sponsored trainee pilot program and passed every stage: age and documents, the written test,
the interview, the simulation test and the English proficiency test. I failed the final
medical test because of my eyes.

**Logline:** A young man obsessed with aviation passes every stage of a sponsored trainee pilot
program except the eye exam, and finds he has not stopped looking up.

## Structure and motif
- Motif: looking up at contrails. Shot 1 and shot 11 are the same rooftop at dawn; the meaning changes.
- Rhythm: the repeated "Passed" in shots 5–6 builds momentum that "Not cleared" (shot 8) breaks.
- Music drops to silence for shots 7–8 so the twist lands on the voice alone.
- Every shot's reason is in `storyboard.json` (`shots[].reason`).

## Decisions
- **English narration** with English subtitles: the audience includes my cohort, and English TTS quality is highest.
- **Illustrated style, not photoreal:** keeps one character consistent across 11 shots and avoids a realistic fake of me.
- **Airline named, but no logos on screen:** the narration names Ethiopian Airlines because it is the true story and it matters to the audience; the planes are generic, with no livery or logo, so the film does not look like an official airline ad.

## User testing
I did not run tests with outside viewers. With the deadline about 30 hours after I started, I chose to spend the time on the pipeline and the film instead.

What I did instead:
- **Self-review against the intent.** After each cut I checked one question: does the ending make "a rejection closes one runway, not the sky" land? Notes on what I changed are below.
- **Story fact-check.** The first draft said I learned aviation from documentaries. That was wrong, since I watched them out of obsession, not to study. I rewrote shots 2 and 4 (and changed "pilot program" to "trainee pilot program") so the narration says only what is true.

| Cut | What I noticed | What I changed in storyboard.json |
|---|---|---|
| Story draft | Narration claimed documentaries taught me; program name wrong | Rewrote s02 and s04 |
| Radio cut | Two different-sounding narrators (the Aura 2 voice drifts in pitch between lines) | One voice for the whole film; take selection by pitch, then a single Gemini take (EXPERIMENTS E6, E7) |
| Rough cut, 25 Nov evening | Subtitles too large on a phone; the AI label should be visible during the film, not only at the end; the documentaries shot (s02) looks posed, not absorbed; say "Ethiopian Airlines", since it is my true story | Subtitles ~25% smaller and broken at sentence ends; a small "AI-generated" badge on every shot; s02 rewritten as a side view, absorbed at midnight, without the reference image; s04 narration now names Ethiopian Airlines |
| Scored cut, 25 Nov night | The hands in the simulator shot (s06) look wrong | s06 reframed on the face with no hands in frame (`anchor_y`, zoom range), and its prompt rewritten to keep hands out of frame (FAILURES 14) |
| Near-final cut | *to fill in* | |

If I had more time, the next step would be to play the radio cut to three people who had a dream turned down, and ask what they felt at the end.
