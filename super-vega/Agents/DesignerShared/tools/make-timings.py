#!/usr/bin/env python3
"""Transcribe a VO (or a clip) with word timestamps and write timings.json next to it.
Usage: python3 tools/make-timings.py <path to vo.mp3> [more files] [--language <code>] [--prompt "<words>"]
       python3 tools/make-timings.py <clip.mp4> [more files] --txt <out dir> [--language <code>] [--prompt "<words>"]

Engine: local Whisper (needs no hosting and no Spira call). On Linux, faster-whisper is used when
installed (same model, int8 on CPU, loaded once for all files), else the whisper CLI. The line
printed at the end says which engine ran; timings.json records it as "engine".

Runs inside a timing slot (timing_slot.py): at most 4 transcriptions at once across the employee,
8 threads each. Exit 75 means every timing slot stayed busy for 5 minutes: run the same line again.

--language  ISO 639 code of the speech (default en), e.g. vi, ms, th, id, zh.
--prompt    names to spell right (brand, product, people), e.g. "Cookiy Earn, Davin".
            Whisper uses it; check names against the script.
--txt <dir> writes only the plain transcript to <dir>/<file stem>.txt (the clip
            cut-off check) instead of timings.json.
Needs openai-whisper (pip install openai-whisper) and ffmpeg."""
import json, re, shutil, subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import profile as scratch_profile  # noqa: E402,F401  (redirects tempfile to the scratch root)
from timing_slot import WHISPER_THREADS, timing_slot  # noqa: E402

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
srcs = [pathlib.Path(x).resolve() for x in args]
model_name = WHISPER_MODEL_EN if lang == "en" else WHISPER_MODEL
_fw_model = []   # loaded once, shared by every input file
_fw_failed = []


def faster_whisper(src):
    """Same output as whisper() from the faster-whisper engine, or None when it is not usable."""
    if _fw_failed:
        return None
    try:
        if not _fw_model:
            from faster_whisper import WhisperModel
            _fw_model.append(WhisperModel(model_name, device="cpu", compute_type="int8",
                                          cpu_threads=WHISPER_THREADS))
        it, _ = _fw_model[0].transcribe(str(src), language=lang, initial_prompt=prompt or None, word_timestamps=True)
        words, segs = [], []
        for s in it:
            segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
            for w in s.words or []:
                words.append((w.word.strip(), w.start, w.end))
        return words, segs, " ".join(s["text"] for s in segs)
    except Exception as e:
        print(f"faster-whisper unavailable ({type(e).__name__}: {e}); using the whisper CLI", file=sys.stderr)
        _fw_failed.append(True)
        return None


def whisper(src, out_dir):
    """Words [(text, start, end)], segments and full text from local Whisper, or exit."""
    exe = shutil.which("whisper")
    cmd = [exe] if exe else [sys.executable, "-m", "whisper"]
    try:
        subprocess.run(cmd + [str(src), "--model", model_name, "--language", lang,
                              *(["--initial_prompt", prompt] if prompt else []),
                              "--word_timestamps", "True", "--threads", str(WHISPER_THREADS),
                              "--output_format", "json",
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


def process(src):
    out_dir = src.parent
    got = faster_whisper(src)
    engine = "faster-whisper" if got else "whisper"
    words, segs, text = got or whisper(src, out_dir)
    credits = None

    if txt_dir:
        d = pathlib.Path(txt_dir); d.mkdir(parents=True, exist_ok=True)
        (d / (src.stem + ".txt")).write_text(text + "\n")
        print(f"[{engine}] {len(words)} words -> {d / (src.stem + '.txt')}")
        print(text)
        return

    out = [{"w": w, "s": round(s, 2), "e": round(e, 2)} for w, s, e in words]
    json.dump({"source": src.name, "engine": engine, "duration": out[-1]["e"], "segments": segs, "words": out},
              open(out_dir / "timings.json", "w"), indent=1, ensure_ascii=False)
    print(f"[{engine}{f', {credits} credits' if credits is not None else ''}] {len(out)} words, {len(segs)} segments -> {out_dir / 'timings.json'}")
    for s in segs: print(f"  {s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")


with timing_slot(", ".join(str(s) for s in srcs)):
    for _src in srcs:
        process(_src)
