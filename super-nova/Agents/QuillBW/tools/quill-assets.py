#!/usr/bin/env python3
"""Quill's asset tool. Local bookkeeping for a brand's logo and product images in Super Nova.
It never touches the network or Spira: hosting is Quill's own step with the host_file tool, and a
logo that needs redrawing is generated with submit_ai_job / wait_ai_job. Prints one JSON line.
Assets never go into the DNA files.

  python3 "<quill>/tools/quill-assets.py" logo "<brand>" <file path> [--keep-as-is] [--regenerated]
  python3 "<quill>/tools/quill-assets.py" product "<brand>" "<product>" <file path> [<file path> ...]
  python3 "<quill>/tools/quill-assets.py" record --path <local file> --url <hosted url>

logo / product: each file is COPIED (the original stays where it is) into
  Agents/NovaOM/client-assets/<BrandName>/ as <BrandName>_logo.<ext> or
  <BrandName>_<ProductName>_prdIMG<N>.<ext> (N continues after the images already there).
  A remote image is first saved to a file with the ai tool's download action.
  A logo must be a transparent PNG. An SVG is rendered to a transparent PNG (the SVG goes to old/).
  The previous logo is moved to old/, never overwritten. The tool checks transparency and says so;
  it does not redraw: when "transparent" is false and the logo may be redrawn, host the file,
  regenerate it with submit_ai_job (gpt-image-2) + wait_ai_job, save the result to a file and run
  `logo` again with that file and --regenerated. --keep-as-is marks a brand whose logo must never
  be redrawn (it only adds a note to the output).
  Output: {"logo": {"local", "transparent", "regenerated", "keep_as_is"}} or
          {"product_images": [{"local"}, ...]}
record: appends the hosted URL host_file returned for a local asset to docs/nova-asset-ids.md.
  Output: {"recorded": <file name>, "url": <url>}
"""
import json, re, shutil, subprocess, sys
from PIL import Image
from pathlib import Path

QUILL = Path(__file__).resolve().parents[1]
SUPER = QUILL.parents[1]
ASSETS = SUPER / "Agents" / "NovaOM" / "client-assets"
ASSET_IDS = SUPER / "Agents" / "NovaOM" / "docs" / "nova-asset-ids.md"

def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")

def ext_of(src):
    e = Path(src).suffix.lower()
    return e if e in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"} else ".png"

def bring_in(src, dest):
    if "://" in src:
        sys.exit("give a local file: save a remote image first with the ai tool's download action")
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

def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "logo":
        bk = key(a[1]) or sys.exit("brand name needed")
        keep, regen = "--keep-as-is" in a, "--regenerated" in a
        folder = ASSETS / bk; folder.mkdir(parents=True, exist_ok=True); old = folder / "old"
        src = a[2]; ext = ".svg" if src.lower().endswith(".svg") else ext_of(src)
        for prev in folder.glob(f"{bk}_logo.*"):            # keep the previous logo, never overwrite
            old.mkdir(exist_ok=True); shutil.move(str(prev), str(old / prev.name))
        dest = folder / f"{bk}_logo{ext}"
        bring_in(src, dest)
        if dest.suffix == ".svg":                           # SVG -> transparent PNG
            png = dest.with_suffix(".png")
            r = subprocess.run(["node", str(QUILL / "tools" / "quill-svg.js"), str(dest), str(png)], capture_output=True, text=True)
            if not png.exists(): sys.exit(f"could not render the SVG logo: {r.stdout.strip()[:200]}")
            old.mkdir(exist_ok=True); shutil.move(str(dest), str(old / f"{bk}_logo_original.svg")); dest = png
        print(json.dumps({"logo": {"local": str(dest.relative_to(SUPER)), "transparent": transparent(dest),
                                   "regenerated": regen, "keep_as_is": keep}}))
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
            out.append({"local": str(dest.relative_to(SUPER))})
        print(json.dumps({"product_images": out}))
    elif a and a[0] == "record" and "--path" in a and "--url" in a:
        f = Path(a[a.index("--path") + 1]); url = a[a.index("--url") + 1]
        if not url.startswith("https://"): sys.exit("--url must be the https URL host_file returned")
        with open(ASSET_IDS, "a", encoding="utf-8") as fh:
            fh.write(f"| {f.name} | {url} |\n")
        print(json.dumps({"recorded": f.name, "url": url}))
    else:
        sys.exit(__doc__)

if __name__ == "__main__":
    main()
