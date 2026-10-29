#!/usr/bin/env python3
"""Split an edge-to-edge collage into panels. Usage: split_collage.py collage.png outdir cols rows [names...]"""
import sys, os
from PIL import Image
src, out, cols, rows = sys.argv[1], sys.argv[2].rstrip('/'), int(sys.argv[3]), int(sys.argv[4]); names = sys.argv[5:]
im = Image.open(src).convert('RGB'); w, h = im.width // cols, im.height // rows; os.makedirs(out, exist_ok=True)
k = 0
for r in range(rows):
    for c in range(cols):
        nm = names[k] if k < len(names) else f'panel_{k}'
        im.crop((c * w, r * h, (c + 1) * w, (r + 1) * h)).save(f'{out}/{nm}.jpg', quality=92); print(nm, (w, h)); k += 1
