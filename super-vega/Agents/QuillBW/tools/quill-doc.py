#!/usr/bin/env python3
"""Quill's DNA tool. Keeps a brand's or product's DNA as a local Markdown file. Local only:
no network, no subprocess. Prints one JSON line.

  python3 "<quill>/tools/quill-doc.py" create "<brand>" ["<product>"] <draft.md>
      Copies the draft to Agents/VegaOM/client-assets/<Brand>/dna/<Brand>[-<Product>]-DNA.md
      -> {"path": <DNA path, relative to the Super Vega folder>, "title": ...}
  python3 "<quill>/tools/quill-doc.py" update <DNA path> <draft.md>
      Replaces the DNA file's whole content with the revised draft (the user's changes).
  python3 "<quill>/tools/quill-doc.py" fetch <DNA path> <out.md>
      Copies a DNA file to <out.md> (to revise an existing DNA).
  python3 "<quill>/tools/quill-doc.py" list "<brand>"
      The DNA references of one brand's rows in Vega's Client Ledger (read only):
      {"brand": ref, "products": {name: ref}}. A ref is whatever the ledger holds (a path or an old URL).

Title: "<Brand> — <Product> — DNA", or "<Brand> — DNA" when there is no product.
Drafts and DNA files must be inside the Super Vega folder.
"""
import json, re, shutil, sys
from pathlib import Path

QUILL = Path(__file__).resolve().parents[1]
SUPER = QUILL.parents[1]
CLIENTS = SUPER / "Agents" / "VegaOM" / "client-assets"
LEDGER = SUPER / "Agents" / "VegaOM" / "docs" / "vega-client-ledger.md"

def inside(p, must_exist=True):
    f = Path(p).expanduser(); f = (f if f.is_absolute() else SUPER / f).resolve()
    if not f.is_relative_to(SUPER): sys.exit(f"must be inside {SUPER}: {f}")
    if must_exist and not f.is_file(): sys.exit(f"no file at {f}")
    return f

def safe(name):
    """A name as a file-name part: letters and digits kept, other runs become one hyphen."""
    return re.sub(r"[^\w]+", "-", name or "", flags=re.UNICODE).strip("-") or "Brand"

def ledger_dna(brand):
    key = lambda n: re.sub(r"[^A-Za-z0-9]", "", n or "")
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    hi = next(i for i, l in enumerate(lines) if l.startswith("| Brand name"))
    head = [c.strip() for c in lines[hi].strip().strip("|").split("|")]
    col = next((h for h in head if h.startswith("DNA")), "DNA")
    out = {"brand": None, "products": {}}
    for l in lines[hi + 2:]:
        if not l.startswith("|"): break
        r = dict(zip(head, [c.strip() for c in l.strip().strip("|").split("|")]))
        if key(r.get("Brand name")) != key(brand): continue
        if key(r.get("Product name")): out["products"][r["Product name"]] = r.get(col) or None
        else: out["brand"] = r.get(col) or None
    return out

def main():
    a = sys.argv[1:]
    if a[:1] == ["create"] and len(a) in (3, 4):
        brand, product, src = a[1], (a[2] if len(a) == 4 else ""), inside(a[-1])
        title = f"{brand} — {product} — DNA" if product.strip() else f"{brand} — DNA"
        name = f"{safe(brand)}-{safe(product)}-DNA.md" if product.strip() else f"{safe(brand)}-DNA.md"
        dest = CLIENTS / safe(brand) / "dna" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        print(json.dumps({"path": str(dest.relative_to(SUPER)).replace("\\", "/"), "title": title}, ensure_ascii=False))
    elif len(a) == 3 and a[0] == "update":
        dest, src = inside(a[1]), inside(a[2])
        shutil.copyfile(src, dest)
        print(json.dumps({"path": str(dest.relative_to(SUPER)).replace("\\", "/"), "updated": True}))
    elif len(a) == 3 and a[0] == "fetch":
        src, out = inside(a[1]), inside(a[2], must_exist=False)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, out)
        print(json.dumps({"saved": str(out.relative_to(SUPER)).replace("\\", "/"), "chars": len(out.read_text(encoding="utf-8"))}))
    elif len(a) == 2 and a[0] == "list":
        print(json.dumps(ledger_dna(a[1]), ensure_ascii=False))
    else:
        sys.exit(__doc__)

if __name__ == "__main__":
    main()
