#!/usr/bin/env python3
"""Transcribe a VO with Whisper (word timestamps) and write timings.json
next to it. Usage: python3 tools/make-timings.py <path to vo.mp3>
Needs openai-whisper installed (pip install openai-whisper) and ffmpeg."""
import json, shutil, subprocess, sys, pathlib

src = pathlib.Path(sys.argv[1]).resolve(); out_dir = src.parent
whisper = shutil.which("whisper")
cmd = [whisper] if whisper else [sys.executable, "-m", "whisper"]
try:
    subprocess.run(cmd + [str(src), "--model", "small.en", "--language", "en",
                          "--word_timestamps", "True", "--output_format", "json",
                          "--output_dir", str(out_dir), "--verbose", "False"], check=True)
except (FileNotFoundError, subprocess.CalledProcessError) as e:
    sys.exit(f"whisper not available ({e}). Install with: pip install openai-whisper")

d = json.load(open(out_dir / (src.stem + ".json")))
words, segs = [], []
for s in d["segments"]:
    segs.append({"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()})
    for w in s.get("words", []):
        words.append({"w": w["word"].strip(), "s": round(w["start"], 2), "e": round(w["end"], 2)})
json.dump({"source": src.name, "duration": round(words[-1]["e"], 2), "segments": segs, "words": words},
          open(out_dir / "timings.json", "w"), indent=1)
(out_dir / (src.stem + ".json")).unlink()
print(f"{len(words)} words, {len(segs)} segments -> {out_dir/'timings.json'}")
for s in segs: print(f"  {s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")
