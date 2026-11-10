#!/usr/bin/env python3
"""Vega's inbox. Quill leaves each user-approved brand brief here as one small file; Vega
records it with one call and never opens the ledger or the file herself.

  python3 "<max>/tools/vega-inbox.py" list
      One JSON line: the briefs waiting ({"waiting": [{"file", "brand", "product", "from"}]}).
  python3 "<max>/tools/vega-inbox.py" apply <handoff file>
      Records the brief: adds or updates the brand row (brief about the brand) or the product
      row (brief about a product) of the Client Ledger: its DNA link and product images; brand
      colors and logo go to the brand row. Only fields the brief carries are changed. Adds
      its preferences to the brand's working memory (created from the template if new),
      and moves the file to vega-inbox/done/. One JSON line back. A brief with "renamed_from"
      first renames that product's row to the brief's product name (same row, not a new one).
"""
import json, re, shutil, sys
from pathlib import Path

MAX = Path(__file__).resolve().parents[1]
SUPER = MAX.parents[1]
INBOX = MAX / "docs" / "vega-inbox"
LEDGER = MAX / "docs" / "vega-client-ledger.md"
MEMORY = MAX / "docs" / "working-memory"
COLS = ["Brand name", "Product name", "DNA (Lark URL)", "Brand colors (hex)", "Brand logo (hosted URL)",
        "Brand logo (local path)", "Product images (hosted URL)", "Product images (local path)", "Website"]
SECTION_HEAD = {"production": "## Production", "after": "## After a video is done", "other": "## Other"}

def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")

def cells(line):
    s = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]

def esc(v): return " ".join(str(v).split()).replace("|", "\\|")

def update_ledger(h):
    """A brief about the brand updates the brand row (Product name empty); a brief about a
    product updates that product's row. Brand colors and logo always go to the brand row."""
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    hi = next(i for i, l in enumerate(lines) if l.startswith("| Brand name"))
    end = hi + 2
    while end < len(lines) and lines[end].startswith("|"): end += 1
    rows = [dict(zip(COLS, cells(l) + [""] * len(COLS))) for l in lines[hi + 2:end]]
    rows = [r for r in rows if any(r.values())]
    bk, pk = key(h["brand"]), key(h.get("product"))

    def row_for(product_key, product_name):
        r = next((r for r in rows if key(r["Brand name"]) == bk and key(r["Product name"]) == product_key), None)
        if r is None:
            r = {c: "" for c in COLS}; r["Brand name"] = h["brand"]; r["Product name"] = product_name or ""
            rows.append(r); r["_new"] = True
        return r

    old = key(h.get("renamed_from"))
    if old and pk and not any(key(r["Brand name"]) == bk and key(r["Product name"]) == pk for r in rows):
        r = next((r for r in rows if key(r["Brand name"]) == bk and key(r["Product name"]) == old), None)
        if r is None: sys.exit(f"no ledger row for {h['brand']} / {h['renamed_from']} to rename")
        r["Product name"] = h["product"]
    logo, imgs = h.get("logo") or {}, h.get("product_images") or []
    dna = h.get("dna") or (h.get("product_dna") if pk else h.get("brand_dna")) or ""
    target = row_for(pk, h.get("product"))
    action = "added" if target.get("_new") else ("renamed" if old else "updated")
    if dna: target["DNA (Lark URL)"] = dna
    if h.get("website"): target["Website"] = h["website"]
    if imgs and pk:
        target["Product images (hosted URL)"] = "<br>".join(i["hosted"] for i in imgs if i.get("hosted"))
        target["Product images (local path)"] = "<br>".join(f"`{i['local']}`" for i in imgs if i.get("local"))
    if h.get("colors") or logo:                       # brand-wide: kept on the brand row
        brand_row = row_for("", "")
        if h.get("colors"): brand_row["Brand colors (hex)"] = "<br>".join(h["colors"])
        if logo.get("hosted"): brand_row["Brand logo (hosted URL)"] = logo["hosted"]
        if logo.get("local"): brand_row["Brand logo (local path)"] = f"`{logo['local']}`"
    rows.sort(key=lambda r: (key(r["Brand name"]).lower(), key(r["Product name"]) != "", key(r["Product name"]).lower()))
    table = [lines[hi], lines[hi + 1]] + ["| " + " | ".join(esc(r[c]) for c in COLS) + " |" for r in rows]
    LEDGER.write_text("\n".join(lines[:hi] + table + lines[end:]) + "\n", encoding="utf-8")
    return action

def update_memory(h):
    prefs = h.get("preferences") or []
    if not prefs: return 0
    bk = key(h["brand"]) or "Brandless"
    f = MEMORY / f"vega-memory-{bk}.md"
    if not f.exists():
        t = (MEMORY / "vega-memory-template.md").read_text(encoding="utf-8").replace("[Brand name]", h["brand"])
        t = "\n".join(l for l in t.splitlines()
                      if not l.startswith("Copy this file") and not l.startswith("time the user asks")
                      and "<e.g." not in l and "<library" not in l and "<anything else" not in l)
        f.write_text(re.sub(r"\n{3,}", "\n\n", t) + "\n", encoding="utf-8")
    lines = f.read_text(encoding="utf-8").splitlines()
    for p in prefs:
        head = SECTION_HEAD[p["section"]]
        i = next((k for k, l in enumerate(lines) if l.strip() == head), None)
        if i is None: lines += ["", head, ""]; i = len(lines) - 2
        j = i + 1
        while j < len(lines) and not lines[j].startswith("## "): j += 1
        while j > i + 1 and not lines[j - 1].strip(): j -= 1      # after the section's last line
        if not lines[j - 1].startswith("- "):
            lines.insert(j, ""); j += 1                         # blank line after the section's description
        lines.insert(j, f"- {p['text']} (from Quill's approved brief)")
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(prefs)

def main():
    a = sys.argv[1:]
    if a[:1] == ["list"]:
        out = []
        for f in sorted(INBOX.glob("vega-handoff-*.json")):
            h = json.loads(f.read_text())
            out.append({"file": str(f.relative_to(SUPER)), "brand": h.get("brand"), "product": h.get("product"), "from": h.get("from")})
        print(json.dumps({"waiting": out}, ensure_ascii=False)); return
    if len(a) == 2 and a[0] == "apply":
        f = Path(a[1]); f = (f if f.is_absolute() else SUPER / f).resolve()
        if not f.is_file() or f.parent != INBOX.resolve(): sys.exit(f"not a waiting handoff in {INBOX}: {f}")
        h = json.loads(f.read_text())
        if not h.get("approved_by_user"): sys.exit("this brief was not approved by the user; not recorded")
        action = update_ledger(h); n = update_memory(h)
        done = INBOX / "done"; done.mkdir(exist_ok=True); shutil.move(str(f), str(done / f.name))
        print(json.dumps({"recorded": h["brand"], "product": h.get("product"), "ledger": action,
                          "preferences_added": n, "dna": h.get("dna")}, ensure_ascii=False)); return
    sys.exit(__doc__)

if __name__ == "__main__":
    main()
