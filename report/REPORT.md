# Not Cleared: report

**Amanuel Mandefrow** · B2W0 AI-Content Generation · 26 November 2026  
Repository: https://github.com/amanuelmr/heritage-short

## 1. What I set out to make, and for whom

A 76-second film about the time I passed every stage of Ethiopian Airlines' sponsored trainee pilot program
(age and documents, the written test, the interview, the simulation test, English proficiency) and was not
cleared at the last step, the medical, because of my eyes.

- **Audience:** young Ethiopians who have been told "no" on a dream, plus my family and friends. They watch on a phone, vertical, often with the sound low.
- **Intent:** at the end they should feel that a rejection closes one runway, not the sky.
- **Why this story:** I like aviation and it has always been interesting to me. I watched documentaries and read whatever I could find online, not to study, just to be near it. Getting that far in the program and stopping at the eye test is the most personal thing I could tell, and it fits the film's question: what is left when a door closes?

## 2. What I learned from my audience

I tested twice, and both tests changed the film (DESIGN.md, user testing table).

**My own reviews of each cut.** These changed the most:

| Cut | What I noticed | What changed |
|---|---|---|
| Story draft | The script said documentaries taught me to fly. Not true. It also said "pilot program" instead of "trainee pilot program" | Rewrote shots 2 and 4 |
| Radio cut | It sounded like two different narrators | One voice for the whole film (E6, E7) |
| Rough cut | Subtitles too big on a phone; the AI label only at the end; the documentaries shot looked posed; "the national airline" felt evasive for a true story | Smaller subtitles that break at sentences (E11), an "AI-generated" badge on every shot, shot 2 reframed and rewritten, Ethiopian Airlines named |
| Scored cut | Wrong-looking hands in the simulator shot and the laptop shot; the line "my hands knew what to do before I did" felt exaggerated | Reframed both shots so the hands are out of frame (FAILURES 14); the line became "Simulation test. Passed. English proficiency. Passed." |

**Three viewers from my audience: a friend, my brother and my father.** I shared the cut with them and all three liked it.

What I learned: my own reviews caught the factual and visual problems, because I know the story. The
viewers told me whether the story lands for someone else. Next time I would show the radio cut to people on
the first evening, before any pictures exist. It costs minutes, and their reaction could have changed the
script earlier, when changes are cheap.

## 3. The hardest problem and how I solved it

Free quotas kept running out, and each one broke the voice or the pictures in a different way.

- **Voice.** The radio cut sounded like two people. Measuring the pitch of every line showed why: Deepgram Aura 2 ranged from 101 to 163 Hz between calls with the same speaker setting (FAILURES 8). I compared four voices (E6) and added automatic take selection by pitch. Then the Cloudflare daily allowance ran out. Gemini TTS read my style instruction out loud and allows only 10 requests a day per model (FAILURES 9). So the whole script is narrated in one Gemini request and cut into one clip per shot. Cutting at pauses put words on the wrong shots at 4 of 10 boundaries; local Whisper word timestamps fixed it, and 10 of 11 clips now match their line exactly (E7, E13).
- **Images.** The first faces did not look Ethiopian until I described Habesha features explicitly (E3). The suggested two-view character sheet put two copies of me in every frame (E4). FLUX drew wrong hands in two shots, which I fixed with framing and new prompts (FAILURES 14).
- **GPU.** Kaggle jobs waited 46 minutes in a queue, then Wan 2.2 ran out of memory on a 15 GB T4. Encoding the prompts on the second T4 fixed it (FAILURES 12).

What I would tell someone hitting the same wall: when a quota runs out, it is usually not one problem but
several in a row, so keep everything you already generated cached and keep a second provider configured.
Most of my fixes were one-line storyboard changes because the stages only talk through files.

## 4. Suggested practices, tested honestly

**A practice that beat my instinct: log every call.** When I heard two voices, my first instinct was to
listen again, switch voices and move on. Because every call was in `runs.jsonl`, "two voices" became a
number (pitch per line), a fair comparison between four voices (E6), and a fix I could check (keep the take
closest to the pitch I liked). The same log built the latency table in COSTS.md and showed exactly which
quota ran out and when.

**A practice that did not work as suggested: the character reference sheet.** The brief suggests a sheet
with front and side views before the keyframes. With FLUX.2 klein, which is an image-editing model, the
two-view sheet put **two identical men into 7 of 8 character shots** (E4), and using the reference on wide
shots turned every one into a front-facing portrait (E5). What worked was a single portrait, used only for
medium and close shots, with the same text description in every prompt. The idea (fix the look first) was
right; the form was wrong for this model.

**How I worked with the coding agent.** I used Claude Code to write the stage scripts while I chose the story,
reviewed every cut and decided what to change. The agent was fast at code; the decisions about what the
film should say, and what looked or sounded wrong, came from watching it.

## 5. Beyond the floor

- **Measuring voice consistency:** pitch per line as a metric, a four-voice comparison, and automatic take selection (E6).
- **A model bias, documented:** "young Ethiopian man" gave faces that read as South Asian in all three seeds; an explicit Habesha description fixed it (E3).
- **Quota-aware narration:** one request for the whole script, cut per shot by Whisper word timestamps, checked line by line (E7, E13).
- **GPU jobs from the command line:** `pipeline/kaggle_job.py` uploads inputs, runs a Kaggle T4 kernel, waits and downloads the result, so Wan 2.2 and ACE-Step run from `make film` like any other stage, cached per shot. A second music backend calls the official ACE-Step Space.
- **Measured mixing:** ducking depth per threshold (E10) and two-pass loudness with a limiter (E8).
- **Choosing where GPU time is worth it:** Wan costs about 8.4 GPU minutes per 2 seconds of video, so it is used only on the two rooftop shots where the moving plane carries the meaning (E14).

## 6. What I would build next

An app that helps people understand aviation better: short illustrated explainers made by this same
pipeline. For example, what happens in a pilot medical, how a simulator test works, or why a plane leaves a
contrail. The storyboard format already separates the facts (narration) from the pictures, so a topic
could become a short film in the same way this story did.
