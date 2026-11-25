"""Timeline and subtitles shared by the radio cut and the final assembly.
Each shot lasts max(storyboard duration, spoken length + padding), so the voice sets the pace."""
import textwrap

LEAD_IN, TAIL = 0.4, 0.6


def build_timeline(sb, nar):
    t, out = 0.0, []
    for s in sb["shots"]:
        spoken = nar.get(s["id"], {}).get("duration_s", 0)
        dur = max(s["duration_s"], spoken + LEAD_IN + TAIL)
        out.append({"id": s["id"], "start": t, "end": t + dur, "voice_start": t + LEAD_IN,
                    "voice_end": t + LEAD_IN + spoken, "text": s["narration"], "duration": dur})
        t += dur
    return out


def _ts(x):
    h, rem = divmod(x, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def _chunks(text, width=40):
    """Split into subtitle cards of at most two lines of ~40 characters."""
    lines = textwrap.wrap(text, width)
    return ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]


def write_srt(timeline, path):
    n, rows = 1, []
    for t in timeline:
        if not t["text"]:
            continue
        cards = _chunks(t["text"])
        span = (t["voice_end"] - t["voice_start"]) or 1
        weights = [len(c) for c in cards]
        start = t["voice_start"]
        for c, w in zip(cards, weights):
            end = start + span * w / sum(weights)
            rows.append(f"{n}\n{_ts(start)} --> {_ts(end + 0.2)}\n{c}\n")
            start, n = end, n + 1
    path.write_text("\n".join(rows))


# --- Burned-in subtitles without libass -------------------------------------
# Homebrew's default ffmpeg has neither the `subtitles` nor the `drawtext` filter,
# so we render each subtitle card to a transparent PNG and overlay it. This works
# with any ffmpeg build, which keeps the pipeline reproducible from a clean clone.
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def font(size):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)


def cards(timeline):
    """(text, start, end) for every subtitle card, same timing as the SRT."""
    out = []
    for t in timeline:
        if not t["text"]:
            continue
        chunks = _chunks(t["text"])
        span = (t["voice_end"] - t["voice_start"]) or 1
        total = sum(len(c) for c in chunks)
        start = t["voice_start"]
        for c in chunks:
            end = start + span * len(c) / total
            out.append((c, round(start, 2), round(end + 0.2, 2)))
            start = end
    return out


def render_text_png(text, w, h, path, *, size, y_frac, box=True):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(size)
    bbox = d.multiline_textbbox((0, 0), text, font=f, align="center", spacing=size // 4)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = (w - tw) / 2, h * y_frac - th / 2
    if box:
        pad = size // 2
        d.rounded_rectangle((x - pad, y - pad, x + tw + pad, y + th + pad), radius=pad, fill=(0, 0, 0, 150))
    d.multiline_text((x, y - bbox[1]), text, font=f, fill="white", align="center", spacing=size // 4,
                     stroke_width=max(1, size // 18), stroke_fill="black")
    img.save(path)


def subtitle_overlays(timeline, w, h, outdir, first_input):
    """Write subtitle PNGs; return (extra ffmpeg -i args, filter chain from [base] to [subbed])."""
    outdir.mkdir(parents=True, exist_ok=True)
    vertical = h > w
    size = round(w * (0.05 if vertical else 0.032))
    y = 0.72 if vertical else 0.86          # vertical: above the platform UI safe area
    args, chain, last = [], [], "base"
    for i, (text, a, b) in enumerate(cards(timeline)):
        p = outdir / f"sub_{w}x{h}_{i:02d}.png"
        render_text_png(text, w, h, p, size=size, y_frac=y)
        args += ["-i", str(p)]
        nxt = f"s{i}"
        chain.append(f"[{last}][{first_input + i}:v]overlay=0:0:enable='between(t,{a},{b})'[{nxt}]")
        last = nxt
    chain.append(f"[{last}]null[subbed]")
    return args, ";".join(chain)
