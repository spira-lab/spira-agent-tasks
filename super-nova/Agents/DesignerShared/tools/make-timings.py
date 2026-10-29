#!/usr/bin/env python3
"""Transcribe a VO (or a clip) with word timestamps and write timings.json next to it.
Usage: python3 tools/make-timings.py <path to vo.mp3> [--language <code>] [--prompt "<words>"]
       python3 tools/make-timings.py <clip.mp4> --txt <out dir> [--language <code>] [--prompt "<words>"]

Engine: local Whisper (needs no hosting and no Spira call). The line printed at the end
says which engine ran; timings.json records it as "engine".

--language  ISO 639 code of the speech (default en), e.g. vi, ms, th, id, zh.
--prompt    names to spell right (brand, product, people), e.g. "Cookiy Earn, Davin".
            Whisper uses it; check names against the script.
--txt <dir> writes only the plain transcript to <dir>/<file stem>.txt (the clip
            cut-off check) instead of timings.json.
Needs openai-whisper (pip install openai-whisper) and ffmpeg."""
import json, re, shutil, subprocess, sys, pathlib

WHISPER_MODEL_EN = "medium.en"   # was small.en until 2026-10-13: it kept mishearing brand names
WHISPER_MODEL = "medium"         # other languages
END = re.compile(r"[.?!。？！]$")
PAUSE = 0.6                      # seconds of silence that also ends a segment

args = sys.argv[1:]
def take(flag, default=None):
    if flag in args:
        i = args.index(flag); v = args[i + 1]; del args[i:i + 2]; return v
    return default
prompt = take("--prompt")
lang = take("--language", "en")
txt_dir = take("--txt")
src = pathlib.Path(args[0]).resolve(); out_dir = src.parent


def whisper():
    """Words [(text, start, end)], segments and full text from local Whisper, or exit."""
    exe = shutil.which("whisper")
    cmd = [exe] if exe else [sys.executable, "-m", "whisper"]
    model = WHISPER_MODEL_EN if lang == "en" else WHISPER_MODEL
    try:
        subprocess.run(cmd + [str(src), "--model", model, "--language", lang,
                              *(["--initial_prompt", prompt] if prompt else []),
                              "--word_timestamps", "True", "--output_format", "json",
                              "--output_dir", str(out_dir), "--verbose", "False"], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        sys.exit(f"whisper is not available ({e}). Install with: pip install openai-whisper")
    raw = out_dir / (src.stem + ".json")
    d = json.load(open(raw)); raw.unlink()
    words, segs = [], []
    for s in d["segments"]:
        segs.append({"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()})
        for w in s.get("words", []):
            words.append((w["word"].strip(), w["start"], w["end"]))
    return words, segs, " ".join(s["text"] for s in segs)


words, segs, text = whisper()
engine, credits = "whisper", None

if txt_dir:
    d = pathlib.Path(txt_dir); d.mkdir(parents=True, exist_ok=True)
    (d / (src.stem + ".txt")).write_text(text + "\n")
    print(f"[{engine}] {len(words)} words -> {d / (src.stem + '.txt')}")
    print(text)
    sys.exit(0)

if segs is None:   # Scribe has no segments: end one at a sentence end or a pause
    segs, cur = [], []
    for i, (w, s, e) in enumerate(words):
        cur.append((w, s, e))
        nxt = words[i + 1][1] if i + 1 < len(words) else None
        if END.search(w) or nxt is None or nxt - e >= PAUSE:
            segs.append({"start": round(cur[0][1], 2), "end": round(cur[-1][2], 2), "text": " ".join(x[0] for x in cur)})
            cur = []

out = [{"w": w, "s": round(s, 2), "e": round(e, 2)} for w, s, e in words]
json.dump({"source": src.name, "engine": engine, "duration": out[-1]["e"], "segments": segs, "words": out},
          open(out_dir / "timings.json", "w"), indent=1, ensure_ascii=False)
print(f"[{engine}{f', {credits} credits' if credits is not None else ''}] {len(out)} words, {len(segs)} segments -> {out_dir / 'timings.json'}")
for s in segs: print(f"  {s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")
