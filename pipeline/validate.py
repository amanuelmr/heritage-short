"""Stage 0: validate storyboard.json against schema/storyboard.schema.json."""
from common import load_storyboard

sb = load_storyboard()
total = sum(s["duration_s"] for s in sb["shots"]) + sb["end_card"]["duration_s"]
words = sum(len(s["narration"].split()) for s in sb["shots"])
print(f"storyboard OK: {len(sb['shots'])} shots, {total:.0f}s planned, {words} narration words")
