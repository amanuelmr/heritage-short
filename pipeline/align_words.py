"""Word timestamps for a narration take, with Whisper running locally (mlx-whisper, Apple Silicon).
Run in its own throwaway env so the main pipeline stays light:
    uv run --no-project --with mlx-whisper python pipeline/align_words.py take.wav words.json"""
import json
import sys

import mlx_whisper

r = mlx_whisper.transcribe(sys.argv[1], path_or_hf_repo="mlx-community/whisper-base.en-mlx", word_timestamps=True)
words = [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]} for seg in r["segments"] for w in seg["words"]]
json.dump(words, open(sys.argv[2], "w"), indent=1)
