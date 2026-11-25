"""Stage: assembly. Builds the film in both aspect ratios from the storyboard and the other stages' outputs.

Picture: each shot is a Wan clip if one exists (outputs/shots/manifest.json), otherwise a slow Ken Burns
move over its keyframe. Shots are cross-dissolved, subtitles are burned in from PNG overlays, and an
AI end card closes the film.
Sound: narration placed per shot (the voice sets the pace), the chosen ACE-Step score (or a quiet
placeholder pad) pre-levelled, silenced for the "silence" cue, ducked under the voice with
sidechaincompress, then loudness-normalised to -14 LUFS / -1 dBTP.

Per-shot segments are cached by a hash of their inputs, so changing one shot re-renders one segment."""
import hashlib
import json
import subprocess
import sys
import time

from PIL import Image, ImageDraw

from common import OUT, ROOT, load_storyboard, log_call, rel, input_hash
from subtitles import build_timeline, font, subtitle_overlays, write_srt

FPS, XFADE = 24, 0.5
SEGMENT_VERSION = 2  # bump when the segment filters change, so cached segments re-render
CROP_Y = 0.25  # landscape crop of a square keyframe: keep more of the top, where faces are
SIZES = {"9x16": (1080, 1920), "16x9": (1920, 1080)}
sb = load_storyboard()
nar = json.loads((OUT / "narration/manifest.json").read_text())
kf = json.loads((OUT / "keyframes/manifest.json").read_text())["shots"]
clips_manifest = OUT / "shots/manifest.json"
clips = json.loads(clips_manifest.read_text()) if clips_manifest.exists() else {}
timeline = build_timeline(sb, nar)
shots = {s["id"]: s for s in sb["shots"]}
END = sb["end_card"]["duration_s"]
TOTAL = round(timeline[-1]["end"] + END, 3)
aspects = [a for a in sys.argv[1:] if a in SIZES] or list(SIZES)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def file_hash(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:12]


def kenburns_filter(shot, w, h, dur):
    """Crop the square keyframe to the target aspect, upscale 2x for smooth sub-pixel motion, then zoompan."""
    n = round(dur * FPS)
    kb = shot.get("kenburns", {})
    z0, z1 = kb.get("zoom_from", 1.04), kb.get("zoom_to", 1.16)
    if kb.get("zoom") == "out":
        z0, z1 = max(z0, z1), min(z0, z1)
    z = f"{z0}+({z1 - z0})*on/{{n}}"
    px = {"right": "on/{n}", "left": "1-on/{n}"}.get(kb.get("pan"), "0.5")
    py = str(kb["anchor_y"]) if "anchor_y" in kb else {"down": "on/{n}", "up": "1-on/{n}"}.get(kb.get("pan"), "0.5")
    crop = "crop='min(iw,ih*{a})':'min(ih,iw/{a})':'(iw-ow)/2':'(ih-oh)*{y}'".format(a=w / h, y=CROP_Y)
    return (f"{crop},scale={w * 2}:{h * 2}:flags=lanczos,"
            f"zoompan=z='{z.format(n=n)}':x='({px.format(n=n)})*(iw-iw/zoom)':y='({py.format(n=n)})*(ih-ih/zoom)'"
            f":d={n}:s={w}x{h}:fps={FPS},format=yuv420p")


def clip_filter(w, h, clip_len, dur):
    """Crop the Wan clip to the aspect, trim the weak first 0.25 s, slow it at most 1.6x, hold the last frame."""
    usable = clip_len - 0.25
    slow = min(1.6, max(1.0, dur / usable))
    hold = max(0.0, dur - usable * slow)
    crop = "crop='min(iw,ih*{a})':'min(ih,iw/{a})':'(iw-ow)/2':'(ih-oh)*{y}'".format(a=w / h, y=CROP_Y)
    return (f"trim=start=0.25,setpts=(PTS-STARTPTS)*{slow:.4f},fps={FPS},{crop},scale={w}:{h}:flags=lanczos,"
            f"tpad=stop_mode=clone:stop_duration={hold:.3f},trim=duration={dur:.3f},format=yuv420p")


def segment(shot_id, w, h, dur, outdir):
    """Render one shot to its own cached MP4 of exactly `dur` seconds."""
    shot = shots[shot_id]
    src = clips.get(shot_id) if shot["motion"] == "wan" else None
    key = input_hash(shot_id, w, h, round(dur, 3), src and file_hash(src), file_hash(kf[shot_id]),
                     shot.get("kenburns"), FPS, CROP_Y, SEGMENT_VERSION)
    out = outdir / f"{shot_id}_{key}.mp4"
    if out.exists():
        return out, "cache"
    if src:
        clip_len = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                         ROOT / src], capture_output=True, text=True).stdout)
        ffmpeg("-i", ROOT / src, "-vf", clip_filter(w, h, clip_len, dur), "-an", "-c:v", "libx264", "-crf", "18",
               "-preset", "fast", out)
        return out, "wan"
    ffmpeg("-i", ROOT / kf[shot_id], "-vf", kenburns_filter(shot, w, h, dur), "-t", f"{dur:.3f}", "-c:v", "libx264",
           "-crf", "18", "-preset", "fast", out)
    return out, "kenburns"


def credits():
    """Name the models this cut really used, read from the storyboard and the stage manifests."""
    m = sb["models"]
    voice = "Deepgram Aura 2" if m["tts"].startswith("@cf/deepgram") else "Gemini TTS"
    parts = [f"Voice: {voice}", "Images: FLUX.2 klein"]
    if clips:
        parts.append("Motion: Wan 2.2")
    if music_source()[1].startswith("ace-step"):
        parts.append("Music: ACE-Step 1.5")
    return "  ·  ".join(parts)


def end_card(w, h, outdir):
    img = Image.new("RGB", (w, h), (12, 18, 32))
    d = ImageDraw.Draw(img)
    lines = sb["end_card"]["text"].split("\n") + [credits()]
    base = min(w, h)
    rows = [(line, font(round(base * (0.085 if i == 0 else 0.032)))) for i, line in enumerate(lines)]
    heights = [d.textbbox((0, 0), t, font=f)[3] for t, f in rows]
    gap = base * 0.035
    y = (h - sum(heights) - gap * (len(rows) - 1)) / 2
    for i, ((line, f), lh) in enumerate(zip(rows, heights)):
        d.text(((w - d.textlength(line, font=f)) / 2, y), line, font=f, fill=(235, 225, 205) if i == 0 else (170, 180, 195))
        y += lh + gap
    png = outdir / f"endcard_{w}x{h}.png"
    img.save(png)
    out = outdir / f"endcard_{w}x{h}_{input_hash(sb['end_card'], credits())}.mp4"
    if not out.exists():
        ffmpeg("-loop", "1", "-i", png, "-t", END, "-r", FPS, "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "18", out)
    return out


def ai_badge(w, h, outdir):
    """Small 'AI-generated' label shown for the whole film (not only the end card), top-left,
    inside the safe area that platform buttons do not cover."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(round(min(w, h) * (0.034 if h > w else 0.024)))
    text = "AI-generated"
    tw = d.textlength(text, font=f)
    th = d.textbbox((0, 0), text, font=f)[3]
    x, y = round(w * 0.05), round(h * (0.08 if h > w else 0.06))
    pad = th * 0.45
    d.rounded_rectangle((x - pad, y - pad, x + tw + pad, y + th + pad), radius=pad, fill=(0, 0, 0, 110))
    d.text((x, y), text, font=f, fill=(255, 255, 255, 215))
    p = outdir / f"ai_badge_{w}x{h}.png"
    img.save(p)
    return p


def music_source():
    mf = OUT / "music/manifest.json"
    if mf.exists():
        m = json.loads(mf.read_text())
        chosen = m.get("chosen") or sb["music"].get("chosen")
        if chosen and str(chosen) in m["candidates"]:
            return ["-i", ROOT / m["candidates"][str(chosen)]], f"ace-step seed {chosen}"
    pad = (f"sine=f=146.83:d={TOTAL},volume=0.5[p1];sine=f=220:d={TOTAL},volume=0.3[p2];"
           f"[p1][p2]amix=inputs=2")
    return ["-f", "lavfi", "-i", f"aevalsrc=0:d={TOTAL}"], pad  # placeholder pad built in the graph


def silence_windows():
    """Times where the storyboard music cue is 'silence' (the music drops out for the twist)."""
    by = {t["id"]: t for t in timeline}
    return [(by[c["from_shot"]]["start"], by[c["to_shot"]]["end"]) for c in sb["music"]["cues"] if c["id"] == "silence"]


def music_gain_expr():
    expr = "1"
    for a, b in silence_windows():
        expr = (f"if(lt(t,{a - 1:.2f}),{expr},if(lt(t,{a:.2f}),({a:.2f}-t),if(lt(t,{b:.2f}),0,"
                f"if(lt(t,{b + 2:.2f}),(t-{b:.2f})/2,{expr}))))")
    return expr


def master(src, out):
    """Two-pass EBU R128 loudness: measure, then normalise linearly to -14 LUFS, -1 dBTP."""
    target = "I=-14:TP=-1:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    meas = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"loudnorm={target}:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:measured_LRA={meas['input_lra']}"
          f":measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true,aresample=48000")
    ffmpeg("-i", src, "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    src.unlink()


def build(aspect):
    w, h = SIZES[aspect]
    segdir = OUT / "assembly" / aspect
    segdir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    segs, kinds = [], {}
    for i, t in enumerate(timeline):
        p, kind = segment(t["id"], w, h, t["duration"] + XFADE, segdir)
        segs.append(p)
        kinds[t["id"]] = kind
    segs.append(end_card(w, h, segdir))

    # picture: cross-dissolve chain, offsets are the storyboard start times
    chain = [f"[{i}:v]settb=AVTB,fps={FPS},setsar=1[v{i}]" for i in range(len(segs))]
    last = "v0"
    for i, t in enumerate(timeline[1:] + [{"start": timeline[-1]["end"]}], start=1):
        chain.append(f"[{last}][v{i}]xfade=transition=fade:duration={XFADE}:offset={t['start']:.3f}[x{i}]")
        last = f"x{i}"
    badge = ai_badge(w, h, segdir)
    chain.append(f"[{last}]fade=t=in:d=0.8,fade=t=out:st={TOTAL - 0.8:.3f}:d=0.8[faded]")
    chain.append(f"[faded][{len(segs)}:v]overlay=0:0:enable='lt(t,{timeline[-1]['end']:.3f})'[base]")
    segs.append(badge)
    inputs = sum([["-i", p] for p in segs], [])
    n_vid = len(segs)

    # subtitles
    sub_args, sub_chain = subtitle_overlays(timeline, w, h, segdir / "subs", n_vid)
    n_sub = len(sub_args) // 2

    # narration
    nar_inputs, delays = [], []
    for j, t in enumerate(timeline):
        idx = n_vid + n_sub + j
        nar_inputs += ["-i", ROOT / nar[t["id"]]["file"]]
        ms = int(t["voice_start"] * 1000)
        delays.append(f"[{idx}:a]aresample=48000,adelay={ms}|{ms}[n{j}]")
    voice = ";".join(delays) + ";" + "".join(f"[n{j}]" for j in range(len(timeline))) + \
        f"amix=inputs={len(timeline)}:normalize=0,apad=whole_dur={TOTAL},loudnorm=I=-16:TP=-2,aresample=48000,asplit=2[voice][sc]"

    # music: level it low, apply the silence cue, fade, then duck under the voice
    m_args, label = music_source()
    m_idx = n_vid + n_sub + len(timeline)
    if label.startswith("sine"):
        m_src = f"{label},volume=0.08[mraw]"
    else:
        m_src = f"[{m_idx}:a]aresample=48000,aloop=loop=-1:size=2147483647,atrim=duration={TOTAL},loudnorm=I=-24:TP=-6,aresample=48000[mraw]"
    music = (f"{m_src};[mraw]volume='{music_gain_expr()}':eval=frame,afade=t=in:d=2,"
             f"afade=t=out:st={TOTAL - 3:.2f}:d=3[mlev];"
             f"[mlev][sc]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[mduck];"
             f"[voice][mduck]amix=inputs=2:normalize=0,alimiter=limit=0.5:attack=5:release=80:level=false,"
             f"atrim=duration={TOTAL}[aout]")  # tame voice peaks so the linear loudness gain has headroom

    graph = ";".join(chain) + ";" + sub_chain + ";" + voice + ";" + music
    final = OUT / "final"
    final.mkdir(exist_ok=True)
    out = final / f"not_cleared_{aspect}.mp4"
    pre = segdir / "premaster.mp4"
    ffmpeg(*inputs, *sub_args, *nar_inputs, *m_args, "-filter_complex", graph, "-map", "[subbed]", "-map", "[aout]",
           "-r", FPS, "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-c:a", "pcm_s16le", "-ar", "48000", "-t", TOTAL, pre.with_suffix(".mov"))
    master(pre.with_suffix(".mov"), out)
    dt = time.monotonic() - t0
    log_call("assemble", "ffmpeg", params={"aspect": aspect, "size": f"{w}x{h}", "music": label if not label.startswith("sine") else "placeholder pad",
             "segments": kinds, "duration_s": TOTAL}, latency_s=dt, output=rel(out))
    print(f"{aspect}: {rel(out)} {TOTAL:.1f}s in {dt:.0f}s  ({sum(v == 'cache' for v in kinds.values())} cached segments)")


(OUT / "final").mkdir(exist_ok=True)
write_srt(timeline, OUT / "final" / "not_cleared.en.srt")
for a in aspects:
    build(a)
