#!/usr/bin/env python3
"""Quill's Lark tool. Creates or updates a DNA doc in the Brand Briefs folder in Lark, from a
Markdown draft in Quill's work folder. Prints one JSON line.

  python3 "<quill>/tools/quill-doc.py" create "<brand>" [<"product">] <draft.md>
      -> {"url": <doc URL>, "title": ...}   (no product name when there is no product)
  python3 "<quill>/tools/quill-doc.py" update <doc URL> <draft.md>
      Replaces the doc's whole content with the revised draft (the user's changes).
  python3 "<quill>/tools/quill-doc.py" fetch <doc URL> <out.md>
      Saves a DNA doc's content as Markdown (to revise an existing DNA).
  python3 "<quill>/tools/quill-doc.py" list "<brand>"
      The DNA links of one brand's rows in Nova's Client Ledger (read only): {"brand": url, "products": {name: url}}.
  Add --dry-run to create / update to see the request without touching Lark.

Title: "<Brand> — <Product> — DNA", or "<Brand> — DNA" when there is no product.
The folder comes from docs/quill-config.json. Drafts must be inside the Super Nova folder.
"""
import json, subprocess, sys
from pathlib import Path

QUILL = Path(__file__).resolve().parents[1]
SUPER = QUILL.parents[1]
CFG = json.loads((QUILL / "docs" / "quill-config.json").read_text())

def draft(p):
    f = Path(p).expanduser(); f = (f if f.is_absolute() else SUPER / f).resolve()
    if not f.is_relative_to(SUPER): sys.exit(f"the draft must be inside {SUPER}: {f}")
    if not f.is_file(): sys.exit(f"no draft at {f}")
    return f

def find_url(obj):
    """The doc link in Lark's reply, wherever it sits."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("http") and ("url" in k.lower() or "/docx/" in v): return v
        for v in obj.values():
            u = find_url(v)
            if u: return u
    if isinstance(obj, list):
        for v in obj:
            u = find_url(v)
            if u: return u
    return None

def lark(args, dry):
    cmd = ["lark-cli", "docs", *args, "--as", CFG.get("lark_identity", "user")] + (["--dry-run"] if dry else [])
    r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, cwd=SUPER)  # lark-cli wants file paths relative to its cwd
    try: d = json.loads(r.stdout)
    except json.JSONDecodeError: sys.exit(f"lark-cli: {(r.stderr or r.stdout).strip()[:400]}")
    if not d.get("ok", False):
        e = d.get("error") or {}
        sys.exit(f"lark-cli failed: {e.get('message') or d}"[:500])
    return d

LEDGER = SUPER / "Agents" / "NovaOM" / "docs" / "nova-client-ledger.md"

def ledger_dna(brand):
    import re
    key = lambda n: re.sub(r"[^A-Za-z0-9]", "", n or "")
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    hi = next(i for i, l in enumerate(lines) if l.startswith("| Brand name"))
    head = [c.strip() for c in lines[hi].strip().strip("|").split("|")]
    out = {"brand": None, "products": {}}
    for l in lines[hi + 2:]:
        if not l.startswith("|"): break
        r = dict(zip(head, [c.strip() for c in l.strip().strip("|").split("|")]))
        if key(r.get("Brand name")) != key(brand): continue
        if key(r.get("Product name")): out["products"][r["Product name"]] = r.get("DNA (Lark URL)") or None
        else: out["brand"] = r.get("DNA (Lark URL)") or None
    return out

def main():
    a = [x for x in sys.argv[1:] if x != "--dry-run"]; dry = "--dry-run" in sys.argv
    if a[:1] == ["create"] and len(a) in (3, 4):
        brand, product, f = a[1], (a[2] if len(a) == 4 else ""), draft(a[-1])
        title = f"{brand} — {product} — DNA" if product.strip() else f"{brand} — DNA"
        d = lark(["+create", "--parent-token", CFG["lark_folder_token"], "--doc-format", "markdown",
                  "--title", title, "--content", f"@{f.relative_to(SUPER)}"], dry)
        print(json.dumps({"url": None if dry else find_url(d), "title": title, "dry_run": dry}, ensure_ascii=False))
    elif len(a) == 3 and a[0] == "update":
        url, f = a[1], draft(a[2])
        lark(["+update", "--doc", url, "--command", "overwrite", "--doc-format", "markdown", "--content", f"@{f.relative_to(SUPER)}"], dry)
        print(json.dumps({"url": url, "updated": not dry, "dry_run": dry}))
    elif len(a) == 3 and a[0] == "fetch":
        url = a[1]; out = Path(a[2]).expanduser(); out = (out if out.is_absolute() else SUPER / out).resolve()
        if not out.is_relative_to(SUPER): sys.exit(f"save inside {SUPER}")
        d = lark(["+fetch", "--doc", url, "--doc-format", "markdown"], False)
        content = ((d.get("data") or {}).get("document") or {}).get("content")
        if content is None: sys.exit("could not read the doc's content")
        out.write_text(content, encoding="utf-8"); print(json.dumps({"saved": str(out.relative_to(SUPER)), "chars": len(content)}))
    elif len(a) == 2 and a[0] == "list":
        print(json.dumps(ledger_dna(a[1]), ensure_ascii=False))
    else:
        sys.exit(__doc__)

if __name__ == "__main__":
    main()
