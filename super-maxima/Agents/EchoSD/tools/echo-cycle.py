#!/usr/bin/env python3
"""Echo's writing style cycling. Keeps the last 10 writing styles used for each video
style, so no writing style is worn out by being used again and again.

  python3 "<echo>/tools/echo-cycle.py" candidates "<video style>" [--product "<product>"]
      Prints one JSON line: the available writing styles for that video style in the
      order to prefer them (never used or least recently used first), the latest one
      used (avoid it), and the last-10 record.
  python3 "<echo>/tools/echo-cycle.py" used "<video style>" "<writing style>" [--product "<product>"]
      Records one use. Run it once for every script written, right after writing it.

Available styles come from styles/echo-styles.md (rows marked available), narrowed by Echo's
working memory (docs/echo-working-memory.md): a product listed there cycles only through its
own writing styles, kept in its own record, and those styles are never offered for anything
else. The record is docs/echo-style-cycle.json; never edit it by hand.

Carousel styles (2026-10-27): any video style ending in "carousel" is a carousel style. The old
name "carousel" reads as "corporate carousel". A carousel style with no writing style rows of its
own in echo-styles.md uses the corporate carousel's (the topic angle), so a new carousel designer
needs no Echo row to be planned.
"""
import fcntl, json, re, sys
from pathlib import Path

ECHO = Path(__file__).resolve().parents[1]
GUIDE = ECHO / "styles" / "echo-styles.md"
RECORD = ECHO / "docs" / "echo-style-cycle.json"
MEMORY = ECHO / "docs" / "echo-working-memory.md"
KEEP = 10

def norm(s): return " ".join((s or "").lower().split())

ALIASES = {"carousel": "corporate carousel"}   # old video style names -> current (2026-10-27)
CAROUSEL_DEFAULT = "corporate carousel"         # whose writing styles a carousel style without its own uses

def vstyle(s):
    """A video style's current name (lower case, single spaces, an old name mapped to its new one)."""
    s = norm(s); return ALIASES.get(s, s)

def is_carousel(video_style): return vstyle(video_style).endswith("carousel")

def guide_rows():
    for line in GUIDE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Video style"): continue
        yield [x.strip() for x in line.strip().strip("|").split("|")]

def writing_key(video_style):
    """The video style whose rows in echo-styles.md a video style uses: its own, or for a carousel
    style with none of its own, the corporate carousel's."""
    vs = vstyle(video_style)
    if is_carousel(vs) and not any(len(c) >= 3 and vstyle(c[0]) == vs for c in guide_rows()):
        return CAROUSEL_DEFAULT
    return vs

def available(video_style):
    vs = writing_key(video_style)
    return [norm(c[1]) for c in guide_rows() if len(c) >= 3 and vstyle(c[0]) == vs and norm(c[2]) == "available"]

def product_rules():
    """Echo's working memory: [(product, video style, [writing styles])]."""
    if not MEMORY.exists(): return []
    out, table = [], False
    for line in MEMORY.read_text(encoding="utf-8").splitlines():
        if line.startswith("| Product"): table = True; continue
        if not table or line.startswith("|---"): continue
        if not line.startswith("|"): table = False; continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 3 and c[0]:
            out.append((norm(c[0]), vstyle(c[1]), [norm(w) for w in c[2].split(",") if w.strip()]))
    return out

def styles_for(video_style, product=None):
    """The writing styles a script may get: the product's own when the memory lists it,
    otherwise every available style except those tied to some product."""
    vs, pr = vstyle(video_style), norm(product)
    styles = available(vs)
    rules = [r for r in product_rules() if r[1] == vs]
    own = next((r[2] for r in rules if pr and r[0] == pr), None)
    if own is not None:
        return [w for w in own if w in styles]
    tied = {w for r in rules for w in r[2]}
    return [w for w in styles if w not in tied]

def record_key(video_style, product=None):
    """A product with its own writing styles keeps its own cycling record."""
    vs, pr = vstyle(video_style), norm(product)
    return f"{vs} | {pr}" if pr and any(r[0] == pr and r[1] == vs for r in product_rules()) else vs

def main():
    a = sys.argv[1:]
    product = None
    if "--product" in a:
        i = a.index("--product"); product = a[i + 1] if i + 1 < len(a) else None; del a[i:i + 2]
    if len(a) < 2 or a[0] not in {"candidates", "used"}: sys.exit(__doc__)
    vs = vstyle(a[1]); rk = record_key(vs, product)
    RECORD.parent.mkdir(parents=True, exist_ok=True); RECORD.touch(exist_ok=True)
    with open(RECORD, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        raw = f.read().strip(); rec = json.loads(raw) if raw else {}
        recent = rec.get(rk, [])
        if a[0] == "candidates":
            styles = styles_for(vs, product)
            if not styles:
                print(json.dumps({"video_style": vs, "candidates": [], "note": "no available writing style"})); return
            rank = {s: (recent.index(s) if s in recent else -1) for s in styles}
            # never used first (-1 → treated as oldest), then the least recently used
            order = sorted(styles, key=lambda s: (rank[s] != -1, -rank[s]))
            latest = recent[0] if recent else None
            if latest in order and len(order) > 1:
                order.remove(latest); order.append(latest)          # the latest one goes last
            print(json.dumps({"video_style": vs, "candidates": order, "avoid": latest if len(styles) > 1 else None,
                              "last_10": recent}))
            return
        if len(a) < 3: sys.exit(__doc__)
        ws = norm(a[2])
        if ws not in styles_for(vs, product):
            sys.exit(f"{ws!r} is not an available writing style for {vs!r}" + (f" and {product!r}" if product else ""))
        rec[rk] = ([ws] + recent)[:KEEP]
        f.seek(0); f.truncate(); f.write(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({"video_style": vs, "recorded": ws, "last_10": rec[rk]}))

if __name__ == "__main__":
    main()
