#!/usr/bin/env python3
"""Quill's video reader. For a video the user gives as context about a brand or product:
downloads it (a link) or reads it in place (a file), transcribes the speech with Whisper,
and makes a contact sheet of frames so the product can be seen. Prints one JSON line.

  python3 "<quill>/tools/quill-video.py" "<brand>" <video URL or file> [<more> ...] [--work <folder>] [--language <code>]

In the work folder, per video N:
  video-N.<ext>         the downloaded video (links only; a user's file is never moved)
  video-N.txt           the transcript
  video-N-frames.jpg    contact sheet: one frame every few seconds, numbered
English uses the local Whisper model (medium.en); --language <code> (e.g. es, tl) uses the
multilingual one. Whisper runs in a timing slot (DesignerShared/tools/timing_slot.py): exit 75
means every slot stayed busy for 5 minutes, run the same line again.

Read the transcript and look at the frames to UNDERSTAND the brand and product: what it is,
who it is for, what it does, what is claimed. The brief is written from that understanding,
never in the video's tone or as a copy of its script.
"""
import json, re, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

QUILL = Path(__file__).resolve().parents[1]
SUPER = QUILL.parents[1]
sys.path.insert(0, str(QUILL.parent / "DesignerShared" / "tools"))
from timing_slot import WHISPER_THREADS, timing_slot  # noqa: E402

def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")

def run(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0: raise RuntimeError((r.stderr or r.stdout).strip()[-300:])
    return r.stdout

def contact_sheet(files, out, cols=4):
    """Numbered frames in a grid (Python image library; this ffmpeg has no text filter)."""
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(f).convert("RGB") for f in files]; w = max(i.size[0] for i in ims); h = max(i.size[1] for i in ims)
    rows = (len(ims) + cols - 1) // cols; S = Image.new("RGB", (cols * w, rows * h), "black"); d = ImageDraw.Draw(S)
    try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except OSError: font = ImageFont.load_default()
    for k, im in enumerate(ims):
        x, y = (k % cols) * w, (k // cols) * h; S.paste(im, (x, y))
        d.rectangle([x, y, x + 34, y + 28], fill="black"); d.text((x + 6, y + 2), str(k + 1), fill="white", font=font)
    S.save(out, quality=85)

def duration(f):
    try: return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]).strip())
    except Exception: return 0.0

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    brand = a[0]; lang = a[a.index("--language") + 1] if "--language" in a else "en"
    work = Path(a[a.index("--work") + 1]) if "--work" in a else QUILL / "work" / f"{key(brand) or 'Brand'}-{datetime.now():%Y%m%d-%H%M%S}"
    work = (work if work.is_absolute() else SUPER / work).resolve(); work.mkdir(parents=True, exist_ok=True)
    skip = {a.index(f) + 1 for f in ("--work", "--language") if f in a} | {a.index(f) for f in ("--work", "--language") if f in a}
    sources = [x for i, x in enumerate(a[1:], 1) if i not in skip]
    whisper = shutil.which("whisper") or sys.exit("Whisper is not installed (pip install openai-whisper)")
    model = ["--model", "medium.en", "--language", "en"] if lang == "en" else ["--model", "medium", "--language", lang]
    out = []
    for n, src in enumerate(sources, 1):
        item = {"n": n, "source": src}
        try:
            if "://" in src:
                run(["yt-dlp", "-f", "bv*[height<=720]+ba/b[height<=720]/b", "-o", str(work / f"video-{n}.%(ext)s"), src])
                vid = next(work.glob(f"video-{n}.*"))
            else:
                vid = Path(src).expanduser().resolve()
                if not vid.is_file(): raise RuntimeError(f"no file at {vid}")
            # transcript
            audio = work / f"video-{n}.wav"
            run(["ffmpeg", "-y", "-v", "error", "-i", str(vid), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
            with timing_slot(f"Quill {vid}"):
                run([whisper, str(audio), *model, "--threads", str(WHISPER_THREADS),
                     "--output_format", "txt", "--output_dir", str(work), "--fp16", "False"])
            txt = work / f"video-{n}.txt"; audio.unlink(missing_ok=True)
            words = len(txt.read_text().split()) if txt.exists() else 0
            # frames: ~16 evenly spaced, numbered
            dur = duration(vid); step = max(dur / 16, 1.0)
            sheet = work / f"video-{n}-frames.jpg"
            fdir = work / f"video-{n}-frames"; fdir.mkdir(exist_ok=True)
            run(["ffmpeg", "-y", "-v", "error", "-i", str(vid), "-vf", f"fps=1/{step:.2f},scale=320:-1",
                 "-frames:v", "16", str(fdir / "f%02d.jpg")])
            frames = sorted(fdir.glob("f*.jpg"))
            if frames: contact_sheet(frames, sheet)
            shutil.rmtree(fdir, ignore_errors=True)
            item.update(transcript=str(txt.relative_to(SUPER)), words=words, seconds=round(dur),
                        frames=str(sheet.relative_to(SUPER)) if sheet.exists() else None)
        except Exception as e:
            item["error"] = str(e)[:300]
        out.append(item)
    print(json.dumps({"work": str(work.relative_to(SUPER)), "videos": out}, ensure_ascii=False))

if __name__ == "__main__":
    main()
