#!/usr/bin/env python3
"""Lyrics tools for the Cloner: check that new lyrics don't copy the source song, and transcribe
sung vocals in Whisper's lyrics mode.

usage:
  python3 lyrics_check.py check <our_lyrics.txt> <source_lyrics.txt> [--n 4] [--title "Song Title"]
      Flags every run of --n or more words found in both, plus any title word (other than common
      words) used in ours. Exit code 1 if anything is flagged. ("check" may be left out.)
  python3 lyrics_check.py transcribe <audio or video> <out.txt> [--language en] [--model small]
      Whisper in lyrics mode (initial prompt "Song lyrics:", high no-speech threshold), which hears
      a sung hook where default mode writes "music". Writes the plain text to <out.txt>.
      Needs the `whisper` command (openai-whisper) and ffmpeg.

Paths may be absolute, relative to the current folder, or relative to the Super Vega folder.
Outputs go only inside Super Vega/Project/ (or the system temp folder); only folders inside
Project/ are ever created. Run with python3.
"""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "DesignerShared" / "tools"))
import profile as scratch_profile  # noqa: E402,F401  (redirects tempfile to the scratch root)
SUPER = HERE.parents[2]
PROJECT = SUPER / "Project"


def resolve_in(p):
    q = Path(p).expanduser()
    if q.is_absolute() or q.exists():
        return q.resolve()
    return (SUPER / q).resolve()


def resolve_out(p):
    q = Path(p).expanduser()
    if not q.is_absolute():
        q = (SUPER / q) if q.parts and q.parts[0] in ("Project", "Agents") else (Path.cwd() / q)
    q = q.resolve()
    temps = {Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()}
    if q.is_relative_to(PROJECT):
        q.parent.mkdir(parents=True, exist_ok=True)
        return q
    if any(q.is_relative_to(t) for t in temps) and q.parent.is_dir():
        return q
    sys.exit(f"output must be inside {PROJECT} or an existing system temp folder, not {q}")


def check(a):
    words = lambda t: re.findall(r"[a-z']+", t.lower())
    strip_tags = lambda t: re.sub(r"\[[^\]]*\]", " ", t)
    ours = words(strip_tags(resolve_in(a.ours).read_text(encoding="utf-8")))
    src = words(resolve_in(a.source).read_text(encoding="utf-8"))
    grams = lambda w, n: {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}
    shared = sorted(grams(ours, a.n) & grams(src, a.n))
    common = set("a an and the i you me my we it is are was be to of in on at for with that this so oh yeah na la no not just".split())
    title = [w for w in words(a.title) if w not in common]
    hook_words = sorted(set(ours) & set(title))
    if shared:
        print(f"COPIED: {len(shared)} phrase(s) of {a.n}+ words also in the source:")
        for g in shared:
            print("  -", g)
    if hook_words:
        print("HOOK WORDS from the source title used in our lyrics:", ", ".join(hook_words))
    if not shared and not hook_words:
        print(f"OK: no shared {a.n}-word phrases and no title hook words.")
    sys.exit(1 if shared or hook_words else 0)


def transcribe(a):
    if not shutil.which("whisper"):
        sys.exit("the whisper command is not installed (pip install openai-whisper)")
    src = resolve_in(a.media)
    if not src.is_file():
        sys.exit(f"no such file: {src}")
    out = resolve_out(a.out)
    with tempfile.TemporaryDirectory(prefix="lyrics-") as td:
        wav = Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
        r = subprocess.run(["whisper", str(wav), "--model", a.model, "--language", a.language,
                            "--initial_prompt", "Song lyrics:", "--no_speech_threshold", "0.9",
                            "--condition_on_previous_text", "False", "--output_format", "json",
                            "--output_dir", td], capture_output=True, text=True)
        j = Path(td) / "a.json"
        if not j.exists():
            sys.exit("whisper failed:\n" + (r.stderr or r.stdout)[-800:])
        segs = json.loads(j.read_text(encoding="utf-8")).get("segments", [])
    lines = [f"[{s['start']:.1f}-{s['end']:.1f}] {s['text'].strip()}" for s in segs if s.get("text", "").strip()]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines) if lines else "(no sung words heard)")
    print("wrote", out)


def main():
    argv = sys.argv[1:]
    if not argv:
        sys.exit(__doc__)
    if argv[0] not in ("check", "transcribe"):
        argv = ["check"] + argv
    ap = argparse.ArgumentParser(description="Cloner lyrics tools")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("ours"); c.add_argument("source")
    c.add_argument("--n", type=int, default=4)
    c.add_argument("--title", default="")
    t = sub.add_parser("transcribe")
    t.add_argument("media"); t.add_argument("out")
    t.add_argument("--language", default="en")
    t.add_argument("--model", default="small")
    a = ap.parse_args(argv)
    check(a) if a.cmd == "check" else transcribe(a)


if __name__ == "__main__":
    main()
