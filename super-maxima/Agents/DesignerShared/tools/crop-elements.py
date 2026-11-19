#!/usr/bin/env python3
"""Cut every separate element out of one transparent image.
Usage: python3 tools/crop-elements.py <sheet.png> <out-dir> --grid <cols>x<rows>
       python3 tools/crop-elements.py <sheet.png> <out-dir> [--gap 24] [--min 2000]

With --grid, the image is a grid of equal sections with one element in each:
every section is cut out and trimmed to its element, and saved as
element-01.png onward, left to right, then top to bottom. Empty sections
are skipped. This is the normal way.

Without --grid, elements are found wherever they sit:
Elements are found by the transparent space between them: any opaque pixels
closer than --gap pixels count as one element, so a label and its icon stay
together. Pieces smaller than --min opaque pixels are dropped as specks.
Each element is saved trimmed to its own edges, with its alpha kept, as
element-01.png, element-02.png, ... in reading order (top to bottom, then
left to right). Prints one line per element: file, size, and where it sat.
"""
import sys, os, argparse
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("sheet"); ap.add_argument("out")
ap.add_argument("--gap", type=int, default=24); ap.add_argument("--min", type=int, default=2000)
ap.add_argument("--grid", help="cols x rows, for example 3x2")
a = ap.parse_args()
im = Image.open(a.sheet).convert("RGBA")
if im.getextrema()[3][0] == 255:
    sys.exit("the image has no transparent pixels: it was not generated on a transparent background")
W, H = im.size
if a.grid:
    cols, rows = (int(v) for v in a.grid.lower().split("x"))
    os.makedirs(a.out, exist_ok=True); i = 0
    for r in range(rows):
        for c in range(cols):
            box = (round(c * W / cols), round(r * H / rows), round((c + 1) * W / cols), round((r + 1) * H / rows))
            cell = im.crop(box)
            bb = cell.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
            if not bb or sum(cell.crop(bb).getchannel("A").histogram()[25:]) < a.min: continue
            i += 1; piece = cell.crop(bb); f = os.path.join(a.out, f"element-{i:02d}.png"); piece.save(f)
            print(f"{f}  {piece.width}x{piece.height}  section row {r + 1}, column {c + 1}")
    if not i: sys.exit("no elements found")
    sys.exit(0)
S = max(1, a.gap // 3)                      # work on a reduced mask for speed
w, h = (W + S - 1) // S, (H + S - 1) // S
alpha = im.getchannel("A").point(lambda v: 255 if v > 24 else 0)
small = alpha.resize((w, h), Image.Resampling.BOX).point(lambda v: 255 if v > 0 else 0)
m = small.load(); seen = bytearray(w * h); r = max(1, a.gap // S)
boxes = []
for y0 in range(h):
    for x0 in range(w):
        if not m[x0, y0] or seen[y0 * w + x0]: continue
        stack = [(x0, y0)]; seen[y0 * w + x0] = 1
        x1 = x2 = x0; y1 = y2 = y0
        while stack:
            x, y = stack.pop()
            x1, x2, y1, y2 = min(x1, x), max(x2, x), min(y1, y), max(y2, y)
            for yy in range(max(0, y - r), min(h, y + r + 1)):
                row = yy * w
                for xx in range(max(0, x - r), min(w, x + r + 1)):
                    if m[xx, yy] and not seen[row + xx]:
                        seen[row + xx] = 1; stack.append((xx, yy))
        boxes.append((x1 * S, y1 * S, min(W, (x2 + 1) * S), min(H, (y2 + 1) * S)))
os.makedirs(a.out, exist_ok=True)
kept = []
for b in boxes:
    piece = im.crop(b); bb = piece.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if not bb: continue
    piece = piece.crop(bb); ox, oy = b[0] + bb[0], b[1] + bb[1]
    if sum(piece.getchannel("A").histogram()[25:]) < a.min: continue
    kept.append((oy, ox, piece))
row_h = max(1, H // 12)
kept.sort(key=lambda k: (k[0] // row_h, k[1]))
for i, (oy, ox, piece) in enumerate(kept, 1):
    f = os.path.join(a.out, f"element-{i:02d}.png"); piece.save(f)
    print(f"{f}  {piece.width}x{piece.height}  at x={ox} y={oy}")
if not kept: sys.exit("no elements found")
