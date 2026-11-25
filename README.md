# Not Cleared

A 76-second AI short film about passing every stage of Ethiopian Airlines' sponsored trainee pilot program
except the eye exam. It comes with the pipeline that makes it: one `storyboard.json` drives keyframes,
moving shots, music, narration and the final edit, in vertical (9:16) and horizontal (16:9).

```
make film
```

That one command validates the storyboard and runs every stage. Each stage regenerates only what changed
since the last run.

## What it does

| Stage | Script | Model | Runs on |
|---|---|---|---|
| Validate | `pipeline/validate.py` | JSON Schema (`schema/storyboard.schema.json`) | local |
| Narration | `pipeline/narration.py` | Deepgram Aura 2 or Gemini 3.8 Flash TTS | Cloudflare Workers AI / Gemini API |
| Keyframes | `pipeline/keyframes.py` | FLUX.2 klein 4B, with a reference portrait | Cloudflare Workers AI |
| Moving shots | `pipeline/shots.py` + `kaggle/wan/wan.py` | Wan 2.2 TI2V-5B | Kaggle T4, driven from the CLI |
| Music | `pipeline/music.py` + `kaggle/music/music.py` | ACE-Step 1.5 turbo | Kaggle T4, driven from the CLI |
| Radio cut | `pipeline/radio_cut.py` | FFmpeg | local |
| Assembly | `pipeline/assemble.py` | FFmpeg + Pillow | local |

The final films land in `outputs/final/` (`not_cleared_9x16.mp4`, `not_cleared_16x9.mp4`, `not_cleared.en.srt`).
Every model call is one line in `runs.jsonl`. See [ARCHITECTURE.md](ARCHITECTURE.md) for how the stages fit together.

## Setup from a clean clone

You need macOS or Linux with `ffmpeg`, [`uv`](https://docs.astral.sh/uv/) and `make`.

```bash
git clone https://github.com/amanuelmr/heritage-short && cd heritage-short
make setup                 # uv sync: requests, jsonschema, pillow, numpy, python-dotenv
cp .env.example .env       # then fill in the keys below
make smoke                 # calls each provider once and lists the model ids your key can use
make film
```

| Key | Where to get it | Free limit we measured |
|---|---|---|
| `GEMINI_API_KEY` | aistudio.google.com → Get API key, in a project **without** billing | 10 TTS requests per model per day |
| `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` | dash.cloudflare.com → Workers AI (account id); My Profile → API Tokens → "Workers AI" template | 10,000 neurons per day (about 50 images and 40 TTS calls) |
| Kaggle | kaggle.com → Settings → phone verification, then API Tokens → Generate; save it to `~/.kaggle/access_token` | 30 GPU hours per week |

Secrets live only in `.env` and `~/.kaggle/`; both are outside git.

## Change one shot

```bash
# edit shots[3].narration or shots[3].image_prompt in storyboard.json, then
make film
```

The other shots print `cache`, and `runs.jsonl` gains only the calls for the changed shot. Run a single stage
with `make narration`, `make keyframes`, `make shots`, `make music` or `make assemble`. To force one shot,
pass its id: `uv run python pipeline/keyframes.py --ref s02`.

## What it costs

$0 on free tiers. At list prices the whole day of work, including every experiment, comes to under a dollar.
See [COSTS.md](COSTS.md) for measured latency per stage.

## Documents

- [DESIGN.md](DESIGN.md): audience, intent, the reason for every shot, and the reviews and what they changed
- [ARCHITECTURE.md](ARCHITECTURE.md): stages, the storyboard contract, caching and failure handling
- [EXPERIMENTS.md](EXPERIMENTS.md): hypothesis, change, result, decision
- [FAILURES.md](FAILURES.md): what broke and what fixed it
- [COSTS.md](COSTS.md): measured latency, GPU minutes and list-price equivalents
- [ETHICS.md](ETHICS.md): consent, licences and labelling

The film is labelled as AI-generated on every shot and on its end card.
