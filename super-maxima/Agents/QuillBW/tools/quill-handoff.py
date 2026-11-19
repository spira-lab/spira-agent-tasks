#!/usr/bin/env python3
"""Quill's handoff tool. After the user APPROVES the brief, leaves it in Nova's inbox as one
small file. Nova records it into her Client Ledger and working memory with her own tool.
Without --product the brief is about the brand (its brand row); with --product it is about
that product (its own row). --dna is that row's DNA doc.
Prints one JSON line with the handoff file.

  python3 "<quill>/tools/quill-handoff.py" "<brand>" [--product "<product>"]
      [--dna <Lark URL>] [--website <the site researched>] [--colors "#1E40AF, #F5F5F5"]
      [--logo '<{"local":..,"hosted":..} from quill-assets.py>']
      [--product-images '<[{"local":..,"hosted":..}, ...] from quill-assets.py>']
      [--pref "production: talking head edited only"] [--pref "after: upload every video to Spira"]
      [--pref "other: ..."] [--renamed-from "<old product name>"]

--renamed-from renames that product's existing ledger row to --product (same row, not a new
product); the user's approval of the new name is required as for any brief.

--pref sections: production (how batch rows are filled: style, music, duration,
instructions, avatar), after (follow-ups once a video is done), other.
"""
import json, re, sys
from datetime import datetime
from pathlib import Path

QUILL = Path(__file__).resolve().parents[1]
INBOX = QUILL.parents[1] / "Agents" / "NovaOM" / "docs" / "nova-inbox"
SECTIONS = {"production", "after", "other"}

def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")

def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("--"): sys.exit(__doc__)
    brand = a[0]; h = {"brand": brand, "product": None, "dna": None,
                       "colors": [], "logo": None, "product_images": [], "preferences": []}
    i = 1
    while i < len(a):
        flag, val = a[i], (a[i + 1] if i + 1 < len(a) else sys.exit(f"{a[i]} needs a value"))
        if flag == "--product": h["product"] = val
        elif flag == "--dna": h["dna"] = val
        elif flag == "--website": h["website"] = val
        elif flag == "--renamed-from": h["renamed_from"] = val
        elif flag == "--colors":
            h["colors"] = [c.strip() for c in val.split(",") if c.strip()]
            bad = [c for c in h["colors"] if not re.fullmatch(r"#[0-9A-Fa-f]{6}", c)]
            if bad: sys.exit(f"colors must be hex codes like #1E40AF: {bad}")
        elif flag == "--logo": h["logo"] = json.loads(val)
        elif flag == "--product-images": h["product_images"] = json.loads(val)
        elif flag == "--pref":
            sec, _, text = val.partition(":")
            if sec.strip().lower() not in SECTIONS or not text.strip():
                sys.exit("--pref must be 'production: ...', 'after: ...', or 'other: ...'")
            h["preferences"].append({"section": sec.strip().lower(), "text": text.strip()})
        else: sys.exit(f"unknown option {flag}")
        i += 2
    if h.get("renamed_from") and not h["product"]: sys.exit("--renamed-from needs --product (the new name)")
    if not (h.get("renamed_from") or h["dna"] or h.get("website") or h["colors"] or h["logo"] or h["product_images"] or h["preferences"]):
        sys.exit("nothing to hand over")
    h["from"] = "Quill"; h["approved_by_user"] = True; h["created"] = datetime.now().isoformat(timespec="seconds")
    INBOX.mkdir(parents=True, exist_ok=True)
    f = INBOX / f"nova-handoff-{key(brand) or 'Brandless'}-{datetime.now():%Y%m%d-%H%M%S}.json"
    f.write_text(json.dumps(h, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"handoff": str(f.relative_to(QUILL.parents[1])), "brand": brand}))

if __name__ == "__main__":
    main()
