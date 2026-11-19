#!/usr/bin/env python3
"""Saves a finished video's or carousel's post copy (title, caption, hashtags) for Hermes's upload
(the owner's rule, 2026-11-12; the voice is in skills/post-copy.md).

  python3 post-copy.py write "<project root>" "<name>" --title "<title>" --caption "<caption>" --hashtags "#a #b #c"
  python3 post-copy.py show  "<project root>" "<name>"

<project root> is Project/<Brand>; <name> is the metadata name (e.g. 56-partgenie-11-12).
Writes <project root>/metadata/<name>.post.json. Limits: title up to 60 characters (Spira allows 90); caption up to 120 characters (the owner, 2026-11-12: short and witty);
caption plus hashtags up to 2,200; 3 to 8 hashtags, each "#word".
"""
import json, re, sys
from datetime import datetime
from pathlib import Path

def opt(a, name):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else None

def path_of(root, name):
    root = Path(root)
    if not root.is_dir(): sys.exit(f"REFUSED no project root at {root}")
    if not re.fullmatch(r"[\w.-]+", name): sys.exit(f"REFUSED bad name {name!r}")
    return root / "metadata" / f"{name}.post.json"

def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in ("write", "show"): sys.exit(__doc__)
    p = path_of(a[1], a[2])
    if a[0] == "show":
        print(p.read_text() if p.is_file() else f"NONE no post copy at {p}"); return
    title, caption, tags = (opt(a, "--title") or "").strip(), (opt(a, "--caption") or "").strip(), opt(a, "--hashtags") or ""
    hashtags = tags.split()
    errs = []
    if not caption: errs.append("a caption is required")
    if not title: errs.append("a title is required")
    if len(title) > 90: errs.append(f"title is {len(title)} characters (max 90)")
    if not 3 <= len(hashtags) <= 8: errs.append(f"{len(hashtags)} hashtags (need 3 to 8)")
    bad = [h for h in hashtags if not re.fullmatch(r"#[^\s#]+", h)]
    if bad: errs.append(f"not hashtags: {' '.join(bad)}")
    if len(caption) > 120: errs.append(f"caption is {len(caption)} characters (max 120: one short, witty line, the owner's rule 2026-11-12)")
    if len(title) > 60: errs.append(f"title is {len(title)} characters (keep it under 60: a punchy hook)")
    full = caption + "\n\n" + " ".join(hashtags)
    if len(full) > 2200: errs.append(f"caption plus hashtags is {len(full)} characters (max 2,200)")
    if errs: sys.exit("REFUSED " + "; ".join(errs))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"title": title, "caption": caption, "hashtags": hashtags,
                             "written": datetime.now().isoformat(timespec="minutes")}, indent=1, ensure_ascii=False) + "\n")
    print(f"SAVED {p}")

if __name__ == "__main__":
    main()
