"""Radio cut: narration over quiet placeholder music on a black screen, timed by the storyboard.
This is the cheap prototype for user test 1."""
import json
import subprocess

from common import OUT, ROOT, load_storyboard
from subtitles import build_timeline, subtitle_overlays, write_srt

sb = load_storyboard()
nar = json.loads((OUT / "narration/manifest.json").read_text())
timeline = build_timeline(sb, nar)
total = round(timeline[-1]["end"] + sb["end_card"]["duration_s"], 2)
srt = OUT / "radio_cut.srt"
write_srt(timeline, srt)

inputs, delays = [], []
for i, t in enumerate(timeline):
    inputs += ["-i", str(ROOT / nar[t["id"]]["file"])]
    ms = int(t["voice_start"] * 1000)
    delays.append(f"[{i}:a]adelay={ms}|{ms},aresample=48000[v{i}]")
n = len(timeline)
mix = ";".join(delays) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0[voice]"
# placeholder pad: a soft D-major drone, very quiet
music = f"sine=f=146.83:d={total},volume=0.04[m1];sine=f=220:d={total},volume=0.025[m2];[m1][m2]amix=inputs=2,afade=t=in:d=2,afade=t=out:st={total-3}:d=3[pad]"
out = OUT / "radio_cut.mp4"
sub_args, sub_chain = subtitle_overlays(timeline, 1280, 720, OUT / "subs", n + 1)
cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
       "-f", "lavfi", "-i", f"color=c=black:s=1280x720:r=24:d={total}", *sub_args,
       "-filter_complex", f"{mix};{music};[voice][pad]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1[a];"
                          f"[{n}:v]null[base];{sub_chain}",
       "-map", "[subbed]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)]
subprocess.run(cmd, check=True, cwd=OUT)
print(f"radio cut: {out.relative_to(ROOT)} ({total:.1f}s)")
