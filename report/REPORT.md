# Not Cleared: report

**Amanuel Mandefrow** · B2W0 AI-Content Generation · 26 November 2026
Repository: https://github.com/amanuelmr/heritage-short

> Lines marked ✍️ are for me to write in my own words. Everything else points at evidence in the repository.

## 1. What I set out to make, and for whom

A 76-second film about the time I passed every stage of Ethiopian Airlines' sponsored trainee pilot program
(age and documents, the written test, the interview, the simulation test, English proficiency) and was not
cleared at the final medical, because of my eyes.

- **Audience:** young Ethiopians who have been told "no" on a dream, plus my family and cohort. They watch on a phone, vertical, often with the sound low.
- **Intent:** at the end they should feel that a rejection closes one runway, not the sky.
- **Why this story:** ✍️ *(two or three sentences: what aviation means to you, and why you wanted this on film)*

## 2. What I learned from my audience

I did not run sessions with outside viewers. With about 30 hours from start to deadline, I chose to spend the
time on the pipeline. I reviewed every cut against the intent myself, and I write that down plainly because
it is a real gap. What the reviews changed (DESIGN.md, user testing table):

| Cut | What I noticed | What changed |
|---|---|---|
| Story draft | It said documentaries taught me to fly. Not true: I watched them out of obsession. It also said "pilot program" instead of "trainee pilot program" | Rewrote shots 2 and 4 |
| Radio cut | It sounded like two different narrators | One voice for the whole film (E6, E7) |
| Rough cut | Subtitles too big on a phone; the AI label only at the end; the documentaries shot looked posed; "the national airline" felt evasive for a true story | Smaller sentence-aware subtitles (E11), an AI badge on every shot, s02 rewritten, Ethiopian Airlines named |
| Near-final cut | ✍️ *(tomorrow)* | |

✍️ *What I would do differently: (for example, send the radio cut to three people on the first evening, because it costs minutes and I only had my own ears.)*

## 3. The hardest problem and how I solved it

**Keeping one narrator's voice while quotas kept running out.** The radio cut sounded like two people. I
measured the median pitch of every line: Deepgram Aura 2 with the same speaker id ranged from 101 to 163 Hz
between calls (FAILURES 8). I compared four voices on the same three lines (E6) and added take selection:
generate up to five takes and keep the one closest to the pitch of the line I liked. Then the Cloudflare
daily allowance ran out (10,000 neurons, used by images and voice tests together). Gemini TTS worked but read
my style instruction aloud, adding about 9 seconds to every line, and allowed only 10 requests a day per model
(FAILURES 9). So I narrated the whole script in one Gemini request and split it per shot. Splitting at the 10
longest pauses failed, because staccato lines ("Passed. Interview. Passed.") have the longest pauses. A small
dynamic program that expects each boundary where the words so far would end, counting each sentence break as
two words, got all 11 lines right with no extra API calls (E7).

✍️ *(one or two sentences: how it felt, or what you would tell someone else hitting the same wall)*

## 4. Suggested practices, tested honestly

**A practice that beat my instinct: log every call.** ✍️ *(Your instinct, e.g. "I would have just listened again and switched voices.")*
Because every narration call went to `runs.jsonl` with its parameters, "two voices" became a number (pitch
per line), a comparison between voices (E6), and a fix I could check (take selection by pitch). The same log
gives COSTS.md its latency table and shows which limits we hit.

**A practice that did not work as suggested: the character reference sheet.** The brief suggests a reference
sheet (front and side) before the keyframes. With FLUX.2 klein, an image-editing model, a two-view sheet put
**two identical men into 7 of 8 character shots** (E4), and conditioning wide shots on the reference turned
every one into a front-facing portrait (E5). What worked was a single head-and-shoulders portrait, used only
for medium and close shots, with the same text description everywhere. The idea (fix the look first) was
right; the form (a multi-view sheet, on every shot) was wrong for this model.

✍️ *(optional: one sentence on what this taught you about following advice vs testing it)*

## 5. Beyond the floor

- **Measuring voice consistency.** Pitch per line as a metric, a four-voice comparison, and automatic take selection (E6, FAILURES 8).
- **A model bias, documented.** "Young Ethiopian man" produced faces that read as South Asian in all three seeds; an explicit Habesha description fixed all three (E3).
- **Quota-aware narration.** Single-take mode plus a pause-alignment algorithm, which cut 11 requests to 1 (E7).
- **GPU jobs from the command line.** `pipeline/kaggle_job.py` uploads inputs as a dataset version, runs a Kaggle T4 kernel, polls it and downloads the result, so Wan 2.2 and ACE-Step run from `make film` like any other stage, cached per shot.
- **Measured mixing.** Ducking depth per threshold (E10) and two-pass loudness with a limiter (E8), instead of tuning by ear alone.

## 6. What I would build next

✍️ *(pick one or two and say why: a small web app where a relative types their story and gets a film; real viewer tests with a blind preference between the Ken Burns and the Wan version of a shot; an Amharic version to test how the TTS models handle it)*
