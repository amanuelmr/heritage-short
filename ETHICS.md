# Ethics: consent, labelling, licences

## Consent
The film is about me. I am the only real person whose story is told.

- **Subject:** myself (Amanuel). I consent to an AI-generated illustrated character representing me,
  and to the narration text in `storyboard.json`, which I wrote and approved.
- **Voice:** the narration uses a stock Gemini TTS voice (`voice.name` in `storyboard.json`), not a clone of any real person's voice.
- **Other people:** no other real person is shown, named or voiced. The examiner and doctor are not depicted.
- **Airline:** referred to only as "the national airline"; no logos, livery or brand marks are generated.

Signed: ______________________  Date: 25 Nov 2026

## Labelling
- The film ends with an end card that says "Made with AI" and names the models (`end_card` in `storyboard.json`).
- When posting I will switch on the platform's AI-content disclosure (YouTube "altered or synthetic content" / TikTok "AI-generated" label).
- Watermarks and provenance metadata are left intact.

## Private data
Only the story above is sent to hosted APIs. No names of other people, addresses or medical details beyond "my eyes" are sent.

## Licences
| Model / tool | Used for | Licence / terms | Output use |
|---|---|---|---|
| Gemini (text, TTS) | storyboard drafting, narration | Gemini API terms (free tier may use inputs to improve products) | allowed |
| FLUX.1 schnell | keyframes | Apache 2.0 | allowed |
| FLUX.2 klein 4B | reference-conditioned keyframes | Apache 2.0 (the 9B is non-commercial; not used) | allowed |
| Wan 2.2 TI2V-5B | moving shots | Apache 2.0 | allowed |
| ACE-Step 1.5 | score | MIT; outputs usable commercially | allowed |
| FFmpeg, Pillow | assembly | LGPL/GPL, HPND | n/a |
