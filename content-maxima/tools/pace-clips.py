#!/usr/bin/env python3
"""Speed up Seedance talking-head clips whose chunk is too short for its slot.

  python3 tools/pace-clips.py <materials>/<name> th-01.mp4=26 th-02.mp4=27 th-03.mp4=9

Each argument is a clip in the materials folder and the number of words in its
chunk, in stage order. Seedance clips are exactly 4, 8 or 12 seconds, and a chunk
with fewer words than its slot holds (13, 26 or 38) is spoken slowly to fill it.
A chunk 1 or 2 words short is left alone. A chunk 3 or more words short is sped
up, picture and voice together (the voice keeps its pitch), to the length its
words take at 3.3 words a second. The clip is replaced in place; the original is
kept as deletable/<clip>.unpaced.mp4.

Prints every clip's length and its data-start on the stage (the clips back to
back), and which clips were sped up: host those again and give Bria the new URL.
Run it before the cut-outs and before make-timings.py --from.
"""
import json, pathlib, shutil, subprocess, sys

WPS = 3.3
SLOT_WORDS = {4: 13, 8: 26, 12: 38}  # the fewest words each Seedance slot holds (toolkit 3e)
MIN_SHORTFALL = 3


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,r_frame_rate",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    video = next(s for s in d["streams"] if s["codec_type"] == "video")
    num, den = video["r_frame_rate"].split("/")
    return float(d["format"]["duration"]), round(int(num) / int(den), 3), any(s["codec_type"] == "audio" for s in d["streams"])


def atempo(factor):
    # One atempo stage per factor of 2 keeps every stage inside the filter's best range.
    stages = []
    while factor > 2.0:
        stages.append(2.0); factor /= 2.0
    stages.append(factor)
    return ",".join(f"atempo={s:.6f}" for s in stages)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mat = pathlib.Path(sys.argv[1]).resolve()
    start_ms, rows, paced = 0, [], []
    for arg in sys.argv[2:]:
        name, _, words = arg.partition("=")
        if not words.isdigit():
            sys.exit(f"pace-clips: give each clip as <clip>=<words>, got {arg!r}")
        clip, words = mat / name, int(words)
        if not clip.exists():
            sys.exit(f"pace-clips: clip not found: {clip}")
        dur, fps, has_audio = probe(clip)
        slot = min(SLOT_WORDS, key=lambda s: abs(s - dur))
        short = SLOT_WORDS[slot] - words
        if short >= MIN_SHORTFALL:
            target = words / WPS
            factor = dur / target
            keep = mat / "deletable" / f"{clip.stem}.unpaced.mp4"
            keep.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(clip), keep)
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(keep), "-filter:v", f"setpts=PTS/{factor:.6f}", "-r", str(fps)]
            # apad + -shortest: the voice runs exactly as long as the picture, so clips joined by
            # make-timings.py --from never drift from their data-start.
            cmd += ["-filter:a", atempo(factor) + ",apad", "-shortest", "-c:a", "aac", "-b:a", "192k"] if has_audio else ["-an"]
            cmd += ["-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(clip)]
            subprocess.run(cmd, check=True)
            dur = probe(clip)[0]
            paced.append(name)
            action = f"sped up x{factor:.2f}"
        else:
            action = "kept" if short > 0 else "kept (fills its slot)"
        rows.append((name, words, slot, max(short, 0), action, dur, start_ms))
        start_ms += round(dur * 1000)
    print(f"{'clip':<12}{'words':>6}{'slot':>6}{'short':>7}  {'action':<22}{'length':>8}{'data-start':>12}")
    for name, words, slot, short, action, dur, at in rows:
        print(f"{name:<12}{words:>6}{slot:>5}s{short:>7}  {action:<22}{dur:>7.2f}s{at:>10} ms")
    print(f"total {start_ms / 1000:.2f}s")
    if paced:
        print("sped up: " + " ".join(paced) + " — host each again (spira assets upload) and give Bria that URL")


if __name__ == "__main__":
    main()
