#!/usr/bin/env python3
"""Quill's asset tool. Brings a brand's logo and product images into Super Nova:
a local copy in Nova's client assets, a Spira-hosted URL, and the Spira asset ID recorded.
Prints one JSON line. Assets never go into the Lark DNA docs.

  python3 "<quill>/tools/quill-assets.py" logo "<brand>" <file path or URL> [--keep-as-is]
  python3 "<quill>/tools/quill-assets.py" product "<brand>" "<product>" <file or URL> [<file or URL> ...]

For each asset:
  - a local file the user gave is COPIED (the user's original stays where it is);
  - a URL is downloaded;
  - saved to Agents/NovaOM/client-assets/<BrandName>/ as <BrandName>_logo.<ext> or
    <BrandName>_<ProductName>_prdIMG<N>.<ext> (N continues after the images already there);
  - uploaded to Spira (`spira assets upload --json`) unless it already was a Spira URL
    (https://static.viralwell.ai/...), and its asset ID appended to nova-asset-ids.md.
A logo must be a transparent PNG. An SVG is rendered to a transparent PNG. Any other logo
without a transparent background is recreated with GPT Image 2 (Spira CLI, about 4
credits) as the same logo on a transparent background; the original is kept in old/.
--keep-as-is skips that (a brand whose logo must never be redrawn).
Output: {"logo": {"local", "hosted", "transparent", "regenerated"}} or
        {"product_images": [{"local", "hosted"}, ...]}.
"""
import json, re, shutil, subprocess, sys, urllib.request
from PIL import Image
from pathlib import Path
from urllib.parse import urlparse

QUILL = Path(__file__).resolve().parents[1]
SUPER = QUILL.parents[1]
ASSETS = SUPER / "Agents" / "NovaOM" / "client-assets"
ASSET_IDS = SUPER / "Agents" / "NovaOM" / "docs" / "nova-asset-ids.md"
SPIRA_HOST = "https://static.viralwell.ai/"

def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")

def ext_of(src):
    e = Path(urlparse(src).path if "://" in src else src).suffix.lower()
    return e if e in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"} else ".png"

def fetch_url(url, dest):
    """Download with a browser User-Agent: static.viralwell.ai refuses Python's default (HTTP 403)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    with urllib.request.urlopen(req, timeout=120) as r: Path(dest).write_bytes(r.read())

def bring_in(src, dest):
    if "://" in src:
        fetch_url(src, dest)
    else:
        f = Path(src).expanduser().resolve()
        if not f.is_file(): sys.exit(f"no file at {f}")
        shutil.copy2(f, dest)

def transparent(f):
    """True when the image has an alpha channel AND a mostly see-through border (a cut-out logo)."""
    try:
        im = Image.open(f)
    except Exception:
        return False
    if im.mode == "P" and "transparency" in im.info: im = im.convert("RGBA")
    if im.mode not in ("RGBA", "LA"): return False
    a = im.getchannel("A"); w, h = a.size
    if a.getextrema()[0] > 245: return False
    border = [a.getpixel((x, y)) for x in range(0, w, max(1, w // 40)) for y in (0, h - 1)] + \
             [a.getpixel((x, y)) for y in range(0, h, max(1, h // 40)) for x in (0, w - 1)]
    return sum(1 for v in border if v < 20) / len(border) >= 0.6

def spira_json(*args):
    r = subprocess.run(["spira", "--json", *args], capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except json.JSONDecodeError: sys.exit(f"spira {' '.join(args[:3])} failed: {(r.stderr or r.stdout).strip()[:300]}")

def regenerate_logo(dest, src_url):
    """Same logo, transparent background, with GPT Image 2. Returns the result URL (hosted by Spira)."""
    prompt = ("Recreate this exact logo: identical shapes, letters, colours, spacing and proportions, nothing "
              "added, removed, or restyled. On a fully transparent background, PNG with alpha, no backdrop, "
              "no shadow, no frame.")
    d = spira_json("ai", "jobs", "create", "--model-id", "gpt-image-2", "--inputs-json",
                   json.dumps({"prompt": prompt, "referenceImage": [src_url], "size": "auto", "resolution": "1K"}), "--wait")
    urls = d.get("resultUrls") or (d.get("data") or {}).get("resultUrls") or []
    if not urls: sys.exit(f"logo regeneration failed: {str(d)[:300]}")
    fetch_url(urls[0], dest)
    return urls[0]

def host(local, src):
    if src.startswith(SPIRA_HOST): return src                     # already hosted on Spira
    r = subprocess.run(["spira", "assets", "upload", str(local), "--json"], capture_output=True, text=True)
    try: d = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"Spira upload failed for {local.name}: {(r.stderr or r.stdout).strip()[:300]} "
                 "(if it is a sign-in problem: spira auth whoami / spira auth login)")
    data = d.get("data") or {}
    if not data.get("url"): sys.exit(f"Spira upload failed for {local.name}: {d}")
    with open(ASSET_IDS, "a", encoding="utf-8") as f:
        f.write(f"| {local.name} | {data.get('assetId', '')} |\n")
    return data["url"]

def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "logo":
        bk = key(a[1]) or sys.exit("brand name needed")
        keep = "--keep-as-is" in a
        folder = ASSETS / bk; folder.mkdir(parents=True, exist_ok=True); old = folder / "old"
        src = a[2]; ext = ".svg" if src.lower().split("?")[0].endswith(".svg") else ext_of(src)
        for prev in folder.glob(f"{bk}_logo.*"):            # keep the previous logo, never overwrite
            old.mkdir(exist_ok=True); shutil.move(str(prev), str(old / prev.name))
        dest = folder / f"{bk}_logo{ext}"
        bring_in(src, dest)
        if dest.suffix == ".svg":                           # SVG -> transparent PNG
            png = dest.with_suffix(".png")
            r = subprocess.run(["node", str(QUILL / "tools" / "quill-svg.js"), str(dest), str(png)], capture_output=True, text=True)
            if not png.exists(): sys.exit(f"could not render the SVG logo: {r.stdout.strip()[:200]}")
            old.mkdir(exist_ok=True); shutil.move(str(dest), str(old / f"{bk}_logo_original.svg")); dest = png; src = str(png)
        ok, regenerated = transparent(dest), False
        if not ok and not keep:
            original_url = host(dest, src)                  # the model needs the original as a hosted reference
            old.mkdir(exist_ok=True); orig = old / f"{bk}_logo_original{dest.suffix}"; shutil.move(str(dest), str(orig))
            dest = folder / f"{bk}_logo.png"
            hosted = regenerate_logo(dest, original_url); regenerated, ok = True, transparent(dest)
        else:
            hosted = host(dest, src)
        print(json.dumps({"logo": {"local": str(dest.relative_to(SUPER)), "hosted": hosted,
                                   "transparent": ok, "regenerated": regenerated}}))
    elif len(a) >= 4 and a[0] == "product":
        bk, pk = key(a[1]), key(a[2])
        if not bk or not pk: sys.exit("brand and product names needed")
        folder = ASSETS / bk; folder.mkdir(parents=True, exist_ok=True)
        taken = [int(m.group(1)) for p in folder.glob(f"{bk}_{pk}_prdIMG*")
                 if (m := re.search(r"_prdIMG(\d+)\.", p.name))]
        n, out = max(taken, default=0), []
        for src in a[3:]:
            n += 1
            dest = folder / f"{bk}_{pk}_prdIMG{n}{ext_of(src)}"
            bring_in(src, dest)
            out.append({"local": str(dest.relative_to(SUPER)), "hosted": host(dest, src)})
        print(json.dumps({"product_images": out}))
    else:
        sys.exit(__doc__)

if __name__ == "__main__":
    main()
