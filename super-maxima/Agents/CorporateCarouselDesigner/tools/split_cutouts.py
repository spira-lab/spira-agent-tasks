#!/usr/bin/env python3
"""Split a transparent cutout sheet into element PNGs via connected components.
Usage: split_cutouts.py sheet.png outdir [name1 name2 ...]  (names in reading order)"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
sheet, out = sys.argv[1], sys.argv[2].rstrip('/')
names = sys.argv[3:]
im = Image.open(sheet).convert('RGBA')
arr = np.array(im); arr[..., 3] = np.where(arr[..., 3] < 24, 0, arr[..., 3]); im = Image.fromarray(arr)  # drop low-alpha speckle
a = arr[..., 3] > 8
assert a.any() and (~a).any(), 'sheet has no alpha; regenerate with "fully transparent background"'
lab, n = ndimage.label(ndimage.binary_dilation(a, iterations=6))
comps = []; labels = []
for i, sl in enumerate(ndimage.find_objects(lab)):
    ys, xs = sl; area = (lab[sl] == i + 1).sum()
    if area > 3000: comps.append((xs.start, ys.start, xs.stop, ys.stop)); labels.append(i + 1)
order = sorted(range(len(comps)), key=lambda j: (int(((comps[j][1] + comps[j][3]) / 2) // (im.height / max(1, round(len(comps) ** 0.5)))), (comps[j][0] + comps[j][2]) / 2))
comps = [comps[j] for j in order]; k_lab = [labels[j] for j in order]
import os; os.makedirs(out, exist_ok=True)
for k, c in enumerate(comps):
    nm = names[k] if k < len(names) else f'cut_{k}'
    crop = im.crop(c)
    # keep only this component's pixels (erase neighbours' specks inside the bbox)
    sub = (lab[c[1]:c[3], c[0]:c[2]] == k_lab[k]); ca = np.array(crop); ca[..., 3] = np.where(sub, ca[..., 3], 0); crop = Image.fromarray(ca)
    crop.save(f'{out}/{nm}.png'); print(nm, crop.size)
print(f'{len(comps)} elements')
