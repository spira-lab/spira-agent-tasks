"""Light grade from the Design team workflow SOP. Local, no AI model, 0 credits.

Saturation -6%, contrast -5%, and a faint white feathered radial gradient centred off-frame on the
light's side (about 16% white at that edge, about 7% across the middle, almost nothing on the far side).

usage: python -I grade.py <in.png> <out.png> [left|right|top-left|top-right] [strength=1.0]
"""
import sys
import numpy as np
from PIL import Image, ImageEnhance

src, dst = sys.argv[1], sys.argv[2]
side = sys.argv[3] if len(sys.argv) > 3 else "left"
k = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

im = Image.open(src).convert("RGB")
im = ImageEnhance.Color(im).enhance(0.94)
im = ImageEnhance.Contrast(im).enhance(0.95)

w, h = im.size
cx = {"left": -0.25, "right": 1.25, "top-left": -0.2, "top-right": 1.2}[side] * w
cy = {"left": 0.33, "right": 0.33, "top-left": 0.0, "top-right": 0.0}[side] * h
yy, xx = np.mgrid[0:h, 0:w]
d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / np.hypot(w, h)
# 0.16 near the source edge, ~0.07 mid-frame, ~0 on the far side; smooth falloff = feathered
alpha = np.clip(0.16 * np.exp(-((d - 0.2) / 0.45) ** 2), 0, 0.16) * k
alpha[d < 0.2] = 0.16 * k
a = np.asarray(im).astype(np.float32)
out = a + (255.0 - a) * alpha[..., None]
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
print("graded", dst)
