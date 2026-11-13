#!/usr/bin/env python3
"""Turn a long generated track into a cut that fits a video.

usage: <MUSIC_PYTHON> music_cut.py <in.mp3> <out.wav> --length 14 --cuts 4.8,6.6,9.5,12.5
                    [--target-bpm 99.4] [--reverb 0.3] [--no-vocal-start]

1. measures the take's tempo
2. if --target-bpm is set: changes speed and pitch together to that tempo, the way slowed edits are made
3. adds a long reverb (--reverb = wet mix, 0 to turn off)
4. picks the best window of --length seconds: high energy, ideally starting where a sung phrase starts
5. nudges the start (+-0.6 s) so the music's accents land on the video's cuts
Prints what it did.

Run it with the Python that prereq_check.py prints as MUSIC_PYTHON (one with librosa, scipy and
soundfile); plain python3 works once those are installed into it. Also needs ffmpeg, and the
`whisper` command only for the vocal-start check (skipped with --no-vocal-start, or when whisper
is missing); that check runs in a timing slot (DesignerShared/tools/timing_slot.py), exit 75 =
slots busy, run the same line again. Paths may be absolute, relative to the current folder, or relative to the Super Vega
folder. The output goes only inside Super Vega/Project/ (or the system temp folder); only folders
inside Project/ are ever created.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "DesignerShared" / "tools"))
import profile as scratch_profile  # noqa: E402,F401  (redirects tempfile to the scratch root)
from timing_slot import WHISPER_THREADS, timing_slot  # noqa: E402
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


ap = argparse.ArgumentParser(description="Cut a generated music take to a video's length and cuts.")
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--length", type=float, required=True)
ap.add_argument("--cuts", default="")
ap.add_argument("--target-bpm", type=float, default=0)
ap.add_argument("--reverb", type=float, default=0.3)
ap.add_argument("--no-vocal-start", action="store_true")
a = ap.parse_args()
src, out = resolve_in(a.src), resolve_out(a.out)
if not src.is_file():
    sys.exit(f"no such file: {src}")

try:
    import numpy as np, librosa, soundfile as sf
    from scipy.signal import fftconvolve, butter, sosfilt
except ImportError as e:
    sys.exit(f"{e}: run this with the MUSIC_PYTHON that prereq_check.py prints (librosa, scipy, soundfile). "
             "Without one, extend or trim the take with Agents/DesignerShared/tools/bgm-extend.py instead.")

SR = 44100
cuts = [float(c) for c in a.cuts.split(",") if c]

y, _ = librosa.load(str(src), sr=SR, mono=False)
y = np.atleast_2d(y)
mono = y.mean(0)
onset = librosa.onset.onset_strength(y=librosa.effects.percussive(mono), sr=SR)
tempo = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=onset, sr=SR))[0])
print(f"take tempo: {tempo:.1f} BPM")

# 2. slowed-edit style: change speed and pitch together (resample, then play at the original rate)
if a.target_bpm:
    f = a.target_bpm / tempo
    if abs(1 - f) > 0.02:
        y = np.stack([librosa.resample(ch, orig_sr=SR, target_sr=int(SR / f)) for ch in y])
        print(f"speed x{f:.3f} (pitch moves with it) -> {a.target_bpm:.1f} BPM")

# 3. reverb: decaying filtered noise as the room
if a.reverb > 0:
    n = int(2.6 * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    ir = rng.standard_normal((2, n)) * np.exp(-t / 0.55)
    ir = sosfilt(butter(2, 5000, "low", fs=SR, output="sos"), ir)
    ir[:, :int(0.012 * SR)] = 0
    ir /= np.abs(ir).sum(1, keepdims=True) ** 0.5 * 30
    wet = np.stack([fftconvolve(y[i % len(y)], ir[i], mode="full")[:y.shape[1]] for i in range(2)])
    dry = np.stack([y[i % len(y)] for i in range(2)])
    wet *= np.sqrt((dry ** 2).mean() / max((wet ** 2).mean(), 1e-12))
    y = (1 - a.reverb) * dry + a.reverb * wet

mono = y.mean(0); L = int(a.length * SR); dur = y.shape[1] / SR
if dur < a.length:
    sys.exit(f"the take is {dur:.1f} s, shorter than --length {a.length}: extend it with bgm-extend.py first")
rms = librosa.feature.rms(y=mono, frame_length=4096, hop_length=1024)[0]
rt = librosa.frames_to_time(np.arange(len(rms)), sr=SR, hop_length=1024)

# 4. candidate starts: where sung phrases start (whisper lyrics mode), else every beat
starts = []
if not a.no_vocal_start and shutil.which("whisper"):
    with tempfile.TemporaryDirectory(prefix="music-cut-") as td:
        w = os.path.join(td, "v.wav"); sf.write(w, mono, SR)
        with timing_slot(f"music_cut {src}"):
            subprocess.run(["whisper", w, "--model", "small", "--language", "en", "--initial_prompt", "Song lyrics:",
                            "--no_speech_threshold", "0.9", "--condition_on_previous_text", "False",
                            "--threads", str(WHISPER_THREADS),
                            "--output_format", "json", "--output_dir", td], capture_output=True)
        try:
            segs = json.load(open(os.path.join(td, "v.json")))["segments"]
            starts = [s["start"] - 0.15 for s in segs if s["text"].strip()]
            print("sung phrases start at:", [round(s, 1) for s in starts[:12]])
        except Exception:
            pass
elif not a.no_vocal_start:
    print("whisper not found: choosing the window on beats only")
beat_t = librosa.frames_to_time(librosa.beat.beat_track(y=mono, sr=SR)[1], sr=SR)
pool = [s for s in starts if 0 <= s <= dur - a.length] or [b for b in beat_t if b <= dur - a.length] or [0.0]


def energy(s):
    m = (rt >= s) & (rt < s + a.length)
    return float(rms[m].mean()) if m.any() else 0


best = max(pool, key=energy)
# 5. nudge so accents land on the cuts
on = librosa.onset.onset_strength(y=mono, sr=SR, hop_length=512)
ot = librosa.frames_to_time(np.arange(len(on)), sr=SR, hop_length=512)


def hit(s):
    return sum(on[np.argmin(abs(ot - (s + c)))] for c in cuts) if cuts else 0


cand = [best + d for d in np.arange(-0.6, 0.61, 0.01) if 0 <= best + d <= dur - a.length]
start = max(cand, key=hit) if (cuts and cand) else best
print(f"window: {start:.2f}-{start + a.length:.2f} s of {dur:.1f} s (energy {energy(start):.4f})")

clip = y[:, int(start * SR): int(start * SR) + L].copy()
fi, fo = int(0.03 * SR), int(0.5 * SR)
clip[:, :fi] *= np.linspace(0, 1, fi); clip[:, -fo:] *= np.linspace(1, 0, fo)
clip /= max(np.abs(clip).max() / 0.95, 1)
sf.write(str(out), clip.T, SR)
print("wrote", out)
