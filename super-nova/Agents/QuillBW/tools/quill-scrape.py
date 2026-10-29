#!/usr/bin/env python3
"""Quill's product-page scraper. Opens the page in headless Chrome (carousels and lazy images
included), saves what the page says, downloads every candidate image at full size, and lays
the candidates out on numbered contact sheets for Quill to LOOK at and choose from.
Prints one JSON line.

  python3 "<quill>/tools/quill-scrape.py" <page URL> "<brand>" [--work <work folder>]

In the work folder (new one when --work is not given):
  page.md               the page's text + product data (JSON-LD, Open Graph, Shopify) for the brief
  candidates/           candidate product images, c01.jpg ...  (full size, duplicates removed)
  sheet-products.jpg    contact sheet, every candidate numbered (look at THIS, not each file)
  logos/ + sheet-logos.jpg   logo candidates from the page header, numbered L1, L2 ...
  candidates.json       number -> file, source URL, where on the page it was found
Then Quill picks the isolated product shots by number and brings them in with quill-assets.py.
"""
import hashlib, json, re, subprocess, sys, urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from PIL import Image, ImageDraw, ImageFont

QUILL = Path(__file__).resolve().parents[1]
SUPER = QUILL.parents[1]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
SIZE_KEYS = {"width", "w", "height", "h", "size", "crop", "resize", "fit", "quality", "q", "auto", "dpr", "format", "fm", "v"}
MAX_CANDIDATES = 40

def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")

def full_size(u):
    """The largest version of an image URL: no size query, no Shopify/WordPress size suffix."""
    p = urlparse(u)
    q = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in SIZE_KEYS]
    path = re.sub(r"_(\d+x\d*|\d*x\d+|small|medium|large|grande|compact|thumb|pico|icon)(@\dx)?(?=\.\w+$)", "", p.path)
    path = re.sub(r"-\d{2,4}x\d{2,4}(?=\.\w+$)", "", path)
    return urlunparse(p._replace(path=path, query=urlencode(q)))

def fetch(u, dest):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Referer": u})
    with urllib.request.urlopen(req, timeout=25) as r, open(dest, "wb") as f:
        f.write(r.read())

def ahash(im):
    g = im.convert("L").resize((8, 8)); px = list(g.tobytes()); avg = sum(px) / 64
    return "".join("1" if x > avg else "0" for x in px)

def sheet(files, labels, out, cell=260, cols=5):
    rows = (len(files) + cols - 1) // cols
    S = Image.new("RGB", (cols * cell, rows * cell), "white"); d = ImageDraw.Draw(S)
    try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except OSError: font = ImageFont.load_default()
    for i, (f, lab) in enumerate(zip(files, labels)):
        x, y = (i % cols) * cell, (i // cols) * cell
        try:
            im = Image.open(f); im.thumbnail((cell - 10, cell - 10))
            if im.mode in ("RGBA", "LA", "P"):   # show transparency on a checkerboard
                bg = Image.new("RGB", im.size, "white"); cd = ImageDraw.Draw(bg)
                for cx in range(0, im.size[0], 16):
                    for cy in range(0, im.size[1], 16):
                        if (cx // 16 + cy // 16) % 2: cd.rectangle([cx, cy, cx + 15, cy + 15], fill=(225, 225, 225))
                bg.paste(im.convert("RGBA"), (0, 0), im.convert("RGBA")); im = bg
            S.paste(im.convert("RGB"), (x + (cell - im.size[0]) // 2, y + (cell - im.size[1]) // 2))
        except Exception:
            d.text((x + 10, y + 120), "unreadable", fill="red", font=font)
        d.rectangle([x, y, x + 64, y + 38], fill="black"); d.text((x + 8, y + 4), lab, fill="white", font=font)
        d.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(200, 200, 200))
    S.save(out, quality=85)

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    url, brand = a[0], a[1]
    work = Path(a[a.index("--work") + 1]) if "--work" in a else QUILL / "work" / f"{key(brand) or 'Brand'}-{datetime.now():%Y%m%d-%H%M%S}"
    work = (work if work.is_absolute() else SUPER / work).resolve(); work.mkdir(parents=True, exist_ok=True)
    raw = work / "page.json"
    r = subprocess.run(["node", str(QUILL / "tools" / "quill-page.js"), url, str(raw)], capture_output=True, text=True, timeout=240)
    if not raw.exists(): sys.exit(f"could not open the page: {(r.stdout or r.stderr).strip()[:300]}")
    page = json.loads(raw.read_text())

    # ---- what the page says, for the brief ----
    md = [f"# Page: {page.get('title','')}", f"Source: {page.get('url', url)}", ""]
    if page.get("shopify_product"): md += ["## Shopify product data", "```json", json.dumps(page["shopify_product"], indent=1, ensure_ascii=False)[:8000], "```", ""]
    if page.get("ld"): md += ["## Structured data (JSON-LD)", "```json", json.dumps(page["ld"], indent=1, ensure_ascii=False)[:8000], "```", ""]
    if page.get("og"): md += ["## Meta", *(f"- {k}: {v}" for k, v in page["og"].items() if v), ""]
    md += ["## Page text", page.get("text", "")]
    (work / "page.md").write_text("\n".join(md), encoding="utf-8")

    # ---- product image candidates: gallery/carousel first, full size, no duplicates ----
    rank = lambda im: (0 if im["how"] == "shopify-product" else 1 if "in-gallery" in im["ctx"] else 2 if im["how"] == "og:image" else 3)
    seen, ordered = set(), []
    for im in sorted(page.get("imgs", []), key=rank):
        u = im["url"]
        if not u or re.search(r"\.(svg|gif)(\?|$)", u, re.I) or re.search(r"logo|icon|sprite|badge|payment|flag", u, re.I): continue
        k = full_size(u)
        if k in seen: continue
        seen.add(k); ordered.append(dict(im, full=k))
    cand_dir = work / "candidates"; cand_dir.mkdir(exist_ok=True)
    kept, hashes = [], set()
    for im in ordered:
        if len(kept) >= MAX_CANDIDATES: break
        ext = (Path(urlparse(im["full"]).path).suffix.lower() or ".jpg")[:5]
        dest = cand_dir / f"c{len(kept) + 1:02d}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp') else '.jpg'}"
        for src in (im["full"], im["url"]):
            try: fetch(src, dest); break
            except Exception: dest.unlink(missing_ok=True)
        if not dest.exists(): continue
        try:
            with Image.open(dest) as pic:
                w, h = pic.size; hsh = ahash(pic)
        except Exception:
            dest.unlink(missing_ok=True); continue
        if min(w, h) < 300 or w / h > 2.5 or h / w > 2.5 or hsh in hashes:   # tiny, banner-shaped, or a repeat
            dest.unlink(); continue
        hashes.add(hsh)
        kept.append({"n": len(kept) + 1, "file": str(dest.relative_to(SUPER)), "url": im["full"], "found": im["how"],
                     "context": im["ctx"][:120], "alt": im["alt"][:120], "size": f"{w}x{h}"})
    if kept: sheet([SUPER / k["file"] for k in kept], [str(k["n"]) for k in kept], work / "sheet-products.jpg")

    # ---- logo candidates ----
    logo_dir = work / "logos"; logo_dir.mkdir(exist_ok=True); logos = []
    for i, lg in enumerate(page.get("logos", []), 1):
        try:
            if lg.get("svg"):
                f = logo_dir / f"L{i}.svg"; svg = lg["svg"]
                if "xmlns" not in svg: svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
                f.write_text(svg)
            else:
                u = lg["url"]; ext = (Path(urlparse(u).path).suffix.lower() or ".png")[:5]
                f = logo_dir / f"L{i}{ext}"; fetch(u, f)
            logos.append({"n": f"L{i}", "file": str(f.relative_to(SUPER)), "url": lg.get("url"), "alt": lg.get("alt", "")})
        except Exception:
            continue
    raster = [l for l in logos if not l["file"].endswith(".svg")]
    if raster: sheet([SUPER / l["file"] for l in raster], [l["n"] for l in raster], work / "sheet-logos.jpg", cell=320, cols=4)

    (work / "candidates.json").write_text(json.dumps({"products": kept, "logos": logos}, indent=1, ensure_ascii=False))
    print(json.dumps({"work": str(work.relative_to(SUPER)), "page_text": str((work / 'page.md').relative_to(SUPER)),
                      "title": page.get("title", "")[:120], "shopify": bool(page.get("shopify_product")),
                      "product_candidates": len(kept),
                      "product_sheet": str((work / 'sheet-products.jpg').relative_to(SUPER)) if kept else None,
                      "logo_candidates": len(logos),
                      "logo_sheet": str((work / 'sheet-logos.jpg').relative_to(SUPER)) if raster else None,
                      "svg_logos": [l["file"] for l in logos if l["file"].endswith(".svg")]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
