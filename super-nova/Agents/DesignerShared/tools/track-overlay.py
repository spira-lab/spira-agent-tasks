#!/usr/bin/env python3
"""Track a coloured marker through a video and composite an overlay image on it (a logo or sticker
held in a hand, pinned to a product). Parallel over frames, one x264 pipe, no audio in the result.

Usage: python3 tools/track-overlay.py <video> <overlay.png> <out.mp4>
         --hsv "H0,S0,V0:H1,S1,V1"   marker colour range in OpenCV HSV (H 0-179, S and V 0-255); required
         [--scale 1.0]                overlay width as a fraction of the marker's width (default 1.0)
         [--offset 0,0]               overlay centre offset from the marker centre, in pixels
         [--smooth 7]                 moving-average window over the tracked path, in frames
         [--workers N]                processes (default: the machine's CPU count)
The overlay PNG keeps its alpha. Frames where the marker is not found reuse the nearest found position.
Needs opencv-python-headless and numpy (pip install opencv-python-headless) and ffmpeg."""
import subprocess, sys, os
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profile as scratch_profile  # noqa: E402

try:
    import cv2
    import numpy as np
except ImportError:
    sys.exit("track-overlay.py needs OpenCV. Install with: pip install opencv-python-headless")

CHUNK = 16
args = sys.argv[1:]


def take(flag, default=None):
    if flag in args:
        i = args.index(flag); v = args[i + 1]; del args[i:i + 2]; return v
    return default


hsv = take("--hsv")
scale = float(take("--scale", "1.0"))
offset = [float(x) for x in take("--offset", "0,0").split(",")]
smooth = int(take("--smooth", "7"))
workers = int(take("--workers", str(scratch_profile.cpu_count())))
if len(args) != 3 or not hsv:
    sys.exit(__doc__)
video, overlay_path, out = args
lo, hi = [np.array([int(x) for x in half.split(",")], dtype=np.uint8) for half in hsv.split(":")]
overlay = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
if overlay is None or overlay.ndim < 3 or overlay.shape[2] != 4:
    sys.exit(f"{overlay_path} must be a PNG with an alpha channel")

cap = cv2.VideoCapture(video)
N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); FPS = cap.get(cv2.CAP_PROP_FPS) or 30
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cap.release()
if not N:
    sys.exit(f"cannot read frames from {video}")
chunks = [(s, min(s + CHUNK, N)) for s in range(0, N, CHUNK)]


def read_chunk(a, b):
    c = cv2.VideoCapture(video); c.set(cv2.CAP_PROP_POS_FRAMES, a)
    frames = []
    for _ in range(a, b):
        ok, f = c.read()
        if not ok: break
        frames.append(f)
    c.release()
    return frames


def detect(span):
    kernel = np.ones((5, 5), np.uint8)
    res = []
    for f in read_chunk(*span):
        m = cv2.inRange(cv2.cvtColor(f, cv2.COLOR_BGR2HSV), lo, hi)
        m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cs:
            res.append(None); continue
        x, y, w, h = cv2.boundingRect(max(cs, key=cv2.contourArea))
        res.append((x + w / 2, y + h / 2, w))
    return res


def composite(job):
    span, track = job
    out_frames = []
    for f, (cx, cy, mw) in zip(read_chunk(*span), track):
        ow = max(2, int(mw * scale)); oh = max(2, int(overlay.shape[0] * ow / overlay.shape[1]))
        o = cv2.resize(overlay, (ow, oh), interpolation=cv2.INTER_AREA)
        x0 = int(cx + offset[0] - ow / 2); y0 = int(cy + offset[1] - oh / 2)
        xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + ow, W), min(y0 + oh, H)
        if xb > xa and yb > ya:
            patch = o[ya - y0:yb - y0, xa - x0:xb - x0]
            al = patch[:, :, 3:4].astype(np.float32) / 255
            roi = f[ya:yb, xa:xb].astype(np.float32)
            f[ya:yb, xa:xb] = (patch[:, :, :3] * al + roi * (1 - al)).astype(np.uint8)
        out_frames.append(f.tobytes())
    return b"".join(out_frames)


def fill_and_smooth(raw):
    found = [i for i, r in enumerate(raw) if r]
    if not found:
        sys.exit("the marker colour was not found in any frame; check --hsv")
    arr = np.array([raw[min(found, key=lambda j: abs(j - i))] for i in range(len(raw))], dtype=np.float64)
    if smooth > 1:
        k = np.ones(smooth) / smooth
        pad = smooth // 2
        for c in range(3):
            padded = np.pad(arr[:, c], pad, mode="edge")
            arr[:, c] = np.convolve(padded, k, mode="valid")[:len(arr)]
    return arr


if __name__ == "__main__":
    with Pool(workers) as pool:
        raw = [r for part in pool.map(detect, chunks) for r in part]
        raw += [None] * (N - len(raw))
        track = fill_and_smooth(raw)
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                               "-r", f"{FPS}", "-i", "-", "-an", "-c:v", "libx264", "-preset", scratch_profile.preset("final"),
                               "-crf", "17", "-pix_fmt", "yuv420p", *(["-threads", "2"] if not scratch_profile.IS_MAC else []),
                               "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for data in pool.imap(composite, [((a, b), track[a:b]) for a, b in chunks]):
            ff.stdin.write(data)
        ff.stdin.close()
        if ff.wait() != 0:
            sys.exit("ffmpeg failed")
    print(f"tracked {sum(1 for r in raw if r)}/{N} frames -> {out}")
