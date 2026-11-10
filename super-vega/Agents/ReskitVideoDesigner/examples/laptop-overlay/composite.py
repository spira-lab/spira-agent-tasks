"""The laptop b-roll of 58-test-10-29: the rebuilt Pexo screens (scr_*.png, from screens.html)
put onto the laptop in the generated plates (plate_l1 / plate_l2, green screen), with a phone-held
camera (slow push, small handheld drift), as one insert from 5.1 s to the end.

  python3 composite.py <frames out dir>      then ffmpeg -framerate 30 -i <dir>/f%04d.jpg ...
Run from anywhere; paths are absolute from this file.
"""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent
W, H, FPS = 1080, 1920, 30
T0, T1 = 5.1, 27.633          # the insert covers this part of the timeline
SW, SH = 2880, 1800           # screen state size

# ------------------------------------------------------------------ plates and their screens
def load_plate(name):
    a = np.asarray(Image.open(ASSETS / f"{name}.png").convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (g > 120) & (g > r + 60) & (g > b + 60)
    ys, xs = np.nonzero(m)
    s, d = xs + ys, xs - ys
    quad = np.array([[xs[s.argmin()], ys[s.argmin()]], [xs[d.argmax()], ys[d.argmax()]],
                     [xs[s.argmax()], ys[s.argmax()]], [xs[d.argmin()], ys[d.argmin()]]], float)
    # take the green spill out of the bezel and keyboard around the screen
    x0, y0 = quad.min(0) - 40; x1, y1 = quad.max(0) + 40
    sub = a[int(y0):int(y1), int(x0):int(x1)]
    mx = np.maximum(sub[..., 0], sub[..., 2])
    over = np.clip(sub[..., 1] - mx, 0, None)
    sub[..., 1] = np.where(over > 18, mx + over * 0.05, sub[..., 1])
    # any leftover green edge pixel just outside the screen becomes bezel black
    edge = (sub[..., 1] > sub[..., 0] + 25) & (sub[..., 1] > sub[..., 2] + 25)
    sub[edge] = (14, 14, 16)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)), quad


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u]); A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.array(A, float))
    Hm = vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]


PLATES = {}
for n in ("plate_l1", "plate_l2"):
    img, quad = load_plate(n)
    pad = 10                                   # the screen image runs a few pixels past the green edge
    rect = np.array([[-pad, -pad], [SW + pad, -pad], [SW + pad, SH + pad], [-pad, SH + pad]], float)
    PLATES[n] = {"img": img, "quad": quad, "P2S": homography(quad, rect), "S2P": homography(rect, quad)}


def screen_to_plate(n, fx, fy):
    p = PLATES[n]["S2P"] @ np.array([fx * SW, fy * SH, 1.0])
    return p[:2] / p[2]

# ------------------------------------------------------------------ the shots
# (start, end, plate, [(state, from)], camera start (fx, fy, plate width), camera end)
SHOTS = [
    (5.100, 6.667, "plate_l1", [("home", 5.1)], (0.50, 0.55, 760), (0.50, 0.53, 700)),
    (6.667, 7.733, "plate_l1", [("type1", 6.667), ("type2", 7.2)], (0.40, 0.60, 520), (0.43, 0.60, 490)),
    (7.733, 9.600, "plate_l1", [("type2", 7.733), ("type3", 8.25)], (0.50, 0.59, 600), (0.52, 0.59, 560)),
    (9.600, 11.667, "plate_l1", [("files1", 9.6), ("files3", 10.25), ("files5", 10.9)], (0.47, 0.67, 600), (0.48, 0.67, 560)),
    (11.667, 12.333, "plate_l1", [("send0", 11.667)], (0.55, 0.66, 600), (0.57, 0.66, 580)),
    (12.333, 12.967, "plate_l1", [("send1", 12.333)], (0.70, 0.68, 470), (0.71, 0.68, 450)),
    (12.967, 15.567, "plate_l1", [("plan1", 12.967), ("plan2", 13.75), ("plan3", 14.55)], (0.42, 0.47, 540), (0.42, 0.50, 490)),
    (15.567, 25.300, "plate_l1", [("ready1", 15.567), ("ready2", 16.9), ("ready3", 18.2), ("ready4", 19.5),
                                  ("comment0", 21.0), ("comment1", 21.8), ("comment2", 22.6), ("comment3", 23.7)],
     (0.47, 0.55, 780), (0.55, 0.50, 600)),
    (25.300, 27.700, "plate_l2", [("end", 25.3)], (0.50, 0.55, 980), (0.50, 0.53, 900)),
]

_cache = {}
def state_img(name):
    if name not in _cache:
        im = Image.open(HERE / f"scr_{name}.png").convert("RGB")
        _cache[name] = im
    return _cache[name]


def ease(x): return 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, x)))


def shake(t, seed):
    r = np.random.default_rng(seed); ph = r.uniform(0, 2 * math.pi, 6)
    dx = 4.0 * math.sin(2 * math.pi * 0.43 * t + ph[0]) + 2.0 * math.sin(2 * math.pi * 1.1 * t + ph[1]) + 0.8 * math.sin(2 * math.pi * 2.3 * t + ph[2])
    dy = 4.0 * math.sin(2 * math.pi * 0.37 * t + ph[3]) + 2.0 * math.sin(2 * math.pi * 0.9 * t + ph[4]) + 0.8 * math.sin(2 * math.pi * 2.1 * t + ph[5])
    rot = 0.35 * math.sin(2 * math.pi * 0.29 * t + ph[0] + ph[3])
    return dx, dy, rot


GRAIN = np.random.default_rng(7).normal(0, 3.2, (8, H, W, 1)).astype(np.float32)
VIG = None


def frame(t, k):
    global VIG
    for si, (a, b, plate, states, c0, c1) in enumerate(SHOTS):
        if a <= t < b or si == len(SHOTS) - 1: break
    P = PLATES[plate]
    st = [s for s, f in states if f <= t + 1e-6][-1]
    e = ease((t - a) / (b - a))
    fx, fy, cw = [c0[i] + (c1[i] - c0[i]) * e for i in range(3)]
    cx, cy = screen_to_plate(plate, fx, fy)
    dx, dy, rot = shake(t, si)
    s = cw / W                                   # plate px per output px
    th = math.radians(rot); co, sn = math.cos(th), math.sin(th)
    # output (u, v) -> plate: p = C + R * s * ((u, v) - centre) + shake
    A = np.array([[s * co, -s * sn, cx + dx * s - s * co * W / 2 + s * sn * H / 2],
                  [s * sn, s * co, cy + dy * s - s * sn * W / 2 - s * co * H / 2],
                  [0, 0, 1]])
    out = P["img"].transform((W, H), Image.AFFINE, data=tuple(A[:2].ravel()), resample=Image.BICUBIC)
    M = P["P2S"] @ A; M = M / M[2, 2]
    scr = state_img(st).transform((W, H), Image.PERSPECTIVE, data=tuple(M.ravel()[:8]), resample=Image.BICUBIC,
                                  fillcolor=(0, 0, 0))
    q = np.ones((SH, SW), np.uint8) * 255
    mask = Image.fromarray(q).transform((W, H), Image.PERSPECTIVE, data=tuple(M.ravel()[:8]), resample=Image.BILINEAR, fillcolor=0)
    scr = scr.filter(ImageFilter.GaussianBlur(0.7))
    o = np.asarray(out).astype(np.float32); sc = np.asarray(scr).astype(np.float32)
    m = (np.asarray(mask).astype(np.float32) / 255.0)[..., None]
    # a screen filmed with a phone: a touch less contrast, a soft hot spot near the middle
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    if VIG is None:
        VIG = 1.0 - 0.18 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
    sc = sc * 0.94 + 10
    comp = o * (1 - m) + sc * m
    comp = comp * VIG[..., None] + GRAIN[k % 8]
    return Image.fromarray(comp.clip(0, 255).astype(np.uint8))


if __name__ == "__main__":
    outdir = Path(sys.argv[1]); outdir.mkdir(parents=True, exist_ok=True)
    only = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
    if only:
        for t in only: frame(t, 0).save(outdir / f"probe_{t:06.2f}.jpg", quality=90)
        sys.exit(0)
    n = round((T1 - T0) * FPS)
    for k in range(n):
        frame(T0 + k / FPS, k).save(outdir / f"f{k:04d}.jpg", quality=92)
    print(n, "frames")
