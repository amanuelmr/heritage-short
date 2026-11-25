# Design

*Written before any image, clip or music was generated (25 Nov 2026).*

## Audience
Young Ethiopians who have been told "no" on a dream, plus my family and my cohort.
They watch on a phone, vertical, often with the sound low, so the English subtitles are burned in.

## Intent
At the end they should feel that **a rejection closes one runway, not the sky.**

## Story
I have been obsessed with aviation for years. I watched documentaries, not to study,
just to be near it, and read whatever I could find online. I applied to the national airline's
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
- **No airline name or logos on screen:** the narration says "the national airline"; planes are generic. Avoids trademark issues and avoids looking like an official ad.

## User testing
I did not run tests with outside viewers. With the deadline about 30 hours after I started, I chose to spend the time on the pipeline and the film instead.

What I did instead:
- **Self-review against the intent.** After each cut I checked one question: does the ending make "a rejection closes one runway, not the sky" land? Notes on what I changed are below.
- **Story fact-check.** The first draft said I learned aviation from documentaries. That was wrong, since I watched them out of obsession, not to study. I rewrote shots 2 and 4 (and changed "pilot program" to "trainee pilot program") so the narration says only what is true.

| Cut | What I noticed | What I changed in storyboard.json |
|---|---|---|
| Story draft | Narration claimed documentaries taught me; program name wrong | Rewrote s02 and s04 |
| Radio cut | *to fill in* | |
| Near-final cut | *to fill in* | |

If I had more time, the next step would be to play the radio cut to three people who had a dream turned down, and ask what they felt at the end.
