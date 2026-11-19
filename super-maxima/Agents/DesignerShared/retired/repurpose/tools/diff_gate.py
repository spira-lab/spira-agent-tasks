#!/usr/bin/env python3
"""Duplicate gate for the shared designer repurpose skill (Super Nova).

Usage:
  python3 diff_gate.py <original.mp4> <variant.mp4> [<variant.mp4> ...]
                       [--orig-min 16] [--pair-min 12]

Measures how far each variant is from the original, and from every other
variant, the way duplicate matchers compare video: perceptual hashes of
frames (64-bit DCT pHash, luminance only, NOT mirror-invariant). Each
sampled variant frame is matched against the closest original frame within
a few seconds either side, so speed changes and cuts cannot hide a copy.
The score is the median Hamming distance in bits (0 = identical frame,
about 32 = unrelated). Exit status 1 if a variant is closer than --orig-min
to the original or closer than --pair-min to another variant.
"""
import math, os, subprocess, sys

FRACS = [i / 12 for i in range(12)]
N = 32
_COS = [[math.cos(math.pi / N * (n + 0.5) * k) for n in range(N)] for k in range(8)]


def durations(path):
    """(video, audio) stream durations in seconds; audio is None when there is none."""
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
                                   "-of", "csv=p=0", path]).decode().split()
    d = {k: float(v) for k, v in (x.split(",")[:2] for x in out) if v not in ("", "N/A")}
    return d.get("video", 0.0), d.get("audio")


def duration(path):
    return durations(path)[0]


def phash_bytes(raw):
    px = [[raw[y * N + x] for x in range(N)] for y in range(N)]
    rows = [[sum(r[n] * _COS[k][n] for n in range(N)) for k in range(8)] for r in px]
    coef = [[sum(rows[n][u] * _COS[v][n] for n in range(N)) for u in range(8)] for v in range(8)]
    flat = [coef[v][u] for v in range(8) for u in range(8)][1:]
    med = sorted(flat)[len(flat) // 2]
    h = 0
    for c in flat: h = (h << 1) | (c > med)
    return h


def frame_hash(path, t):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", "%.3f" % max(0, t), "-i", path, "-frames:v", "1",
                                   "-vf", "scale=%d:%d:flags=area,format=gray" % (N, N), "-f", "rawvideo", "-"])
    return phash_bytes(raw[:N * N])


def image_hash(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-frames:v", "1",
                                   "-vf", "scale=%d:%d:flags=area,format=gray" % (N, N), "-f", "rawvideo", "-"])
    return phash_bytes(raw[:N * N])


def ham(a, b): return bin(a ^ b).count("1")


def sample(path, fracs=FRACS):
    d = duration(path)
    return [(f, frame_hash(path, min(f * d, d - 0.1))) for f in fracs]


def dense(path, step=0.5):
    d = duration(path); out = []; t = 0.0
    while t < d - 0.05:
        out.append((t / d, frame_hash(path, t))); t += step
    return out


def best_match(samples, ref, window=0.10):
    """Median over samples of the smallest distance to any ref frame near the same point."""
    ds = []
    for f, h in samples:
        near = [rh for rf, rh in ref if abs(rf - f) <= window] or [rh for _, rh in ref]
        ds.append(min(ham(h, rh) for rh in near))
    ds.sort(); return ds[len(ds) // 2]


def main():
    a = sys.argv[1:]; omin, pmin = 16, 12
    if "--orig-min" in a: i = a.index("--orig-min"); omin = int(a[i + 1]); del a[i:i + 2]
    if "--pair-min" in a: i = a.index("--pair-min"); pmin = int(a[i + 1]); del a[i:i + 2]
    if len(a) < 2: sys.exit(__doc__)
    orig, vs = a[0], a[1:]
    name = lambda p: os.path.splitext(os.path.basename(p))[0]
    ref = dense(orig); S = {v: sample(v) for v in vs}
    fails = []
    for v in vs:   # sound and picture must end together
        dv, da = durations(v)
        if da is not None and abs(da - dv) > 0.3: fails.append((name(v), "its own audio (%.1fs vs %.1fs)" % (da, dv), 0))
    print("%-30s %6s   %s" % ("variant", "orig", "nearest variant"))
    for v in vs:
        do = best_match(S[v], ref)
        near = min([(best_match(S[v], S[w]), name(w)) for w in vs if w != v] or [(64, "-")])
        flag = []
        if do < omin: flag.append("TOO CLOSE TO ORIGINAL"); fails.append((name(v), "original", do))
        if near[0] < pmin: flag.append("TOO CLOSE TO " + near[1])
        print("%-30s %6d   %-28s %3d  %s" % (name(v), do, near[1], near[0], "  ".join(flag)))
    for i, v in enumerate(vs):
        for w in vs[i + 1:]:
            d = best_match(S[v], S[w])
            if d < pmin: fails.append((name(v), name(w), d))
    print()
    if fails:
        print("FAIL: %d pair(s) (original needs >= %d bits, variants >= %d)" % (len(fails), omin, pmin))
        for x, y, d in sorted(fails, key=lambda z: z[2]): print("  %-30s ~ %-30s %d" % (x, y, d))
        sys.exit(1)
    print("PASS: no variant hashes close to the original or to another variant")


if __name__ == "__main__":
    main()
