#!/usr/bin/env python3
"""Split one generated collage of full-screen shots into separate frames.
Usage: python3 tools/split-collage.py <collage.png> <out-dir> [--cols 2] [--rows 2] [--size 1080x1920]

The generator does not place its seams exactly on the grid lines; they can
sit a few pixels off. So each seam is found where it really is (the
sharpest line near where it should be), every shot is cut along its own
seams, a few pixels are trimmed inside each cut, and the shot is scaled to
fill --size exactly. Saves shot-1.png onward in reading order (left to
right, then top to bottom) and prints each one with where it was cut.
"""
import sys, os, argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("collage"); ap.add_argument("out")
ap.add_argument("--cols", type=int, default=2); ap.add_argument("--rows", type=int, default=2)
ap.add_argument("--size", default="1080x1920")
a = ap.parse_args()
TW, TH = (int(v) for v in a.size.lower().split("x"))
im = Image.open(a.collage).convert("RGB"); W, H = im.size
px = np.asarray(im).astype(np.int16)
colstep = np.abs(np.diff(px, axis=1)).mean(axis=(0, 2))   # change between each column and the next
rowstep = np.abs(np.diff(px, axis=0)).mean(axis=(1, 2))

def seams(step, n, length):
    cuts = [0]
    for k in range(1, n):
        c = round(k * length / n); w = max(4, length // (n * 12))
        lo, hi = max(1, c - w), min(length - 1, c + w)
        cuts.append(int(np.argmax(step[lo:hi])) + lo + 1)
    return cuts + [length]

xs, ys = seams(colstep, a.cols, W), seams(rowstep, a.rows, H)
os.makedirs(a.out, exist_ok=True)
TRIM = 3   # pixels trimmed inside every cut, so no line of the neighbour survives
i = 0
for r in range(a.rows):
    for c in range(a.cols):
        i += 1
        box = (xs[c] + (TRIM if c else 0), ys[r] + (TRIM if r else 0),
               xs[c + 1] - (TRIM if c < a.cols - 1 else 0), ys[r + 1] - (TRIM if r < a.rows - 1 else 0))
        shot = im.crop(box); sw, sh = shot.size
        s = max(TW / sw, TH / sh)                              # fill the target, then centre-crop the excess
        shot = shot.resize((round(sw * s), round(sh * s)), Image.Resampling.LANCZOS)
        l, t = (shot.width - TW) // 2, (shot.height - TH) // 2
        shot = shot.crop((l, t, l + TW, t + TH))
        f = os.path.join(a.out, f"shot-{i}.png"); shot.save(f)
        print(f"{f}  {TW}x{TH}  cut from x={box[0]}..{box[2]} y={box[1]}..{box[3]}")
