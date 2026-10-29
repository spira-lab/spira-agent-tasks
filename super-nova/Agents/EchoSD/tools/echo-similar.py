#!/usr/bin/env python3
"""Echo's repeat check. Keeps a brand's scripts from repeating what was already written for
that brand, in two ways (the owner's rule, 2026-10-22):
  1. Angle: no two scripts for a brand share the same angle (the one core subject: for a
     persona-led script, the person's job or role; otherwise the topic).
  2. Phrasing: no script is delivered with phrasing identical, or nearly identical, to an
     earlier one. Shared product and feature lines are fine; only near-copies are caught.
Echo never has to read old scripts in full.

  python3 "<echo>/tools/echo-similar.py" angles "<brand>" [--product "<name>"]
      Prints the brand's angle rule, the angles writers must not use (newest first), and,
      when the brand has a list to pick from, the choices still open. Writers read it before
      writing.
  python3 "<echo>/tools/echo-similar.py" check "<brand>" [--product "<name>"] <file> [<file> ...]
      Checks new script files (or each script in an ad hoc table file) against every earlier
      script for the brand, and against each other. Each script file has its angle beside it
      in <file stem>.angle (one line). Prints one JSON line per script: "ok", or "too close"
      with the reason ("angle", "phrasing", or "no angle") and the closest earlier script.
  python3 "<echo>/tools/echo-similar.py" record "<brand>" <label>=<angle file> [...]
      Adds delivered scripts' angles to the brand's angle record (Echo's director tool calls it).
  --carousel (with any of the three): carousel topic angles (every carousel style, e.g. corporate
      carousel, 2026-10-27). They are kept in one record per brand, shared by every carousel style
      and separate from the brand's video angles, and checked only
      against earlier carousel angles: a carousel angle never repeats, and a video angle never
      blocks a carousel angle (nor the other way round).

Earlier scripts: <echo>/scripts/<BrandName>/*.md and the brand's ad hoc tables in
<echo>/adhoc/. Angle record: <echo>/scripts/<BrandName>/angles.json.
Carousels: <echo>/scripts/<BrandName>/carousel/*.md and <echo>/adhoc/echo-adhoc-carousel-<BrandName>-*.md;
angle record <echo>/scripts/<BrandName>/carousel-angles.json. The Angle rules table does not apply to
carousels: no carousel angle repeats within the brand's last 75 recorded carousels.
Per-brand angle rules (what the angle is, how many recent scripts it may not repeat, and a
list to pick from): the "Angle rules" table in <echo>/docs/echo-working-memory.md. A brand
with no row never repeats any recorded angle.
<brand> is matched without spaces or special characters.
"""
import json, re, sys
from datetime import date
from pathlib import Path

ECHO = Path(__file__).resolve().parents[1]
PHRASING_LIMIT = 0.50  # share of 3-word phrases in common: at or above it, the phrasing is a near-copy
ANGLE_LIMIT = 0.50     # share of an angle's main words in common: at or above it, the same angle
STOP = set("a an the of for and or to in on at with by from about is are your you their his her its as "
           "who that this these those how why what when after before during into over vs".split())

def key(b): return re.sub(r"[^A-Za-z0-9]", "", b or "") or "Brandless"
LABELS = re.compile(r"\bPodcaster [12]:\s*")   # podcast speaker labels are not words anyone says
def spoken(t): return LABELS.sub(" ", t or "")
def words(t): return re.findall(r"[a-z0-9']+", spoken(t).lower())
def grams(t, n=3):
    w = words(t); return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}
def jacc(a, b): return len(a & b) / len(a | b) if a and b else 0.0
def stem(w): return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
def angle_words(a): return {stem(w) for w in re.findall(r"[a-z0-9]+", (a or "").lower()) if w not in STOP}
def angle_file(f): return Path(f).with_suffix(".angle")

def table_scripts(path):
    """Scripts from an ad hoc table: the last cell of each data row."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not line.startswith("|---") and not line.startswith("| #"):
            cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
            if len(cells) >= 3: out.append(cells[-1].strip().replace("\\|", "|"))
    return out

def scripts_in(path):
    if path.name.startswith("echo-adhoc-"): return table_scripts(path)
    t = path.read_text(encoding="utf-8").strip()
    return [t] if t else []

def earlier(brand, exclude=(), carousel=False):
    files = []
    d = ECHO / "scripts" / brand / ("carousel" if carousel else "")
    if d.is_dir(): files += [p for p in d.glob("*.md")]
    files += list((ECHO / "adhoc").glob(f"echo-adhoc-{'carousel-' if carousel else ''}{brand}-*.md"))
    skip = {Path(x).resolve() for x in exclude}
    files = [p for p in files if p.resolve() not in skip]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in files:
        for i, s in enumerate(scripts_in(p), 1):
            out.append((f"{p.name}#{i}" if p.name.startswith("echo-adhoc-") else p.name, s))
    return out

MEMORY = ECHO / "docs" / "echo-working-memory.md"
CAROUSEL_WINDOW = 75   # a carousel angle may come back after the brand's last 75 carousels (the owner, 2026-10-27)

def rule(brand, product=None, carousel=False):
    """The brand's angle rule: {what, window (None = all), choices (list or None)}.
    Carousels have one rule for every brand: no carousel angle repeats within the brand's last
    CAROUSEL_WINDOW recorded carousels (the owner's rule, 2026-10-27: 75)."""
    out = {"what": "the script's one core subject", "window": None, "choices": None, "list_file": None}
    if carousel:
        out["what"] = "the carousel's one core topic"
        out["window"] = CAROUSEL_WINDOW
        return out
    try: text = MEMORY.read_text(encoding="utf-8")
    except FileNotFoundError: return out
    sec = text.split("## Angle rules", 1)
    if len(sec) < 2: return out
    best = None
    for line in sec[1].splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Brand"): continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 5 or key(c[0]) != brand: continue
        prod = c[1].lower()
        if prod in ("", "-", "any", "all"): best = best or c
        elif product and prod == product.strip().lower(): best = c
    if not best: return out
    out["what"] = best[2]
    out["window"] = int(best[3]) if best[3].isdigit() else None
    if best[4] not in ("", "-"):
        f = ECHO / best[4]; out["list_file"] = best[4]
        out["choices"] = [l[2:].strip() for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("- ")] if f.is_file() else []
    return out

def blocked(brand, product=None, exclude=(), carousel=False):
    """Recorded angles a new script may not take, newest first: [(script, angle)]."""
    r = rule(brand, product, carousel)
    rec = [(x["script"], x["angle"]) for x in used_angles(brand, carousel) if x["script"] not in exclude]
    return rec[:r["window"]] if r["window"] else rec

def record_path(brand, carousel=False):
    return ECHO / "scripts" / brand / ("carousel-angles.json" if carousel else "angles.json")
def used_angles(brand, carousel=False):
    """[{script, angle, date}], newest first."""
    try: return json.loads(record_path(brand, carousel).read_text())
    except (FileNotFoundError, json.JSONDecodeError): return []

def record(brand, items, carousel=False):
    """items: [(label, angle)]. A label already recorded gets its new angle (a rewritten script)."""
    rec = [r for r in used_angles(brand, carousel) if r["script"] not in {l for l, _ in items}]
    today = date.today().isoformat()
    rec = [{"script": l, "angle": a, "date": today} for l, a in items if a] + rec
    p = record_path(brand, carousel); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    return len(items)

def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in {"angles", "check", "record"}: sys.exit(__doc__)
    brand = key(a[1])
    product = None
    if "--product" in a:
        i = a.index("--product"); product = a[i + 1]; del a[i:i + 2]
    carousel = "--carousel" in a
    if carousel: a.remove("--carousel")
    if a[0] == "angles":
        r = rule(brand, product, carousel); bl = blocked(brand, product, carousel=carousel)
        print(f"The angle is: {r['what']}.")
        what = "carousel" if carousel else "script"
        print(f"Never use these ({'the brand' + chr(39) + 's last ' + str(r['window']) + ' recorded ' + what + 's' if r['window'] else 'every recorded ' + what + ' of the brand'}):")
        for _, x in bl: print(f"  - {x}")
        if not bl: print("  (none recorded yet)")
        if r["choices"] is not None:
            used = [angle_words(x) for _, x in bl]
            open_ = [c for c in r["choices"] if not any(jacc(angle_words(c), u) >= ANGLE_LIMIT for u in used)]
            print(f"Pick only from this list ({r['list_file']}); still open ({len(open_)}):")
            for c in open_: print(f"  - {c}")
        return
    if a[0] == "record":
        items = []
        for x in a[2:]:
            label, f = x.split("=", 1)
            items.append((label, Path(f).read_text(encoding="utf-8").strip() if Path(f).is_file() else ""))
        print(json.dumps({"recorded": record(brand, items, carousel)})); return
    if len(a) < 3: sys.exit(__doc__)
    files = [Path(x).expanduser().resolve() for x in a[2:]]
    for f in files:
        if not f.is_relative_to(ECHO) or not f.is_file(): sys.exit(f"no script file inside {ECHO} at {f}")
    for line in check(brand, files, product=product, carousel=carousel): print(json.dumps(line))

def check(brand, files, also_exclude=(), product=None, carousel=False):
    """One verdict per new script, against the brand's earlier scripts and each other.
    carousel=True: carousel angles, against the brand's earlier carousels only."""
    new = []
    for f in files:
        parts = scripts_in(f)
        af = angle_file(f)
        ang = af.read_text(encoding="utf-8").strip() if af.is_file() else ""
        for k, t in enumerate(parts, 1):
            new.append((f"{f.name}#{k}" if len(parts) > 1 else f.name, t, ang))
    prev = earlier(brand, exclude=list(files) + list(also_exclude), carousel=carousel)
    labels = {n for n, _, _ in new}
    r = rule(brand, product, carousel)
    prev_angles = blocked(brand, product, exclude=labels, carousel=carousel)   # the brand's window of recent angles
    out = []
    for i, (label, s, ang) in enumerate(new):
        if not ang:
            out.append({"script": label, "verdict": "too close", "reason": "no angle",
                        "closest": None, "note": f"missing {angle_file(label).name}"}); continue
        # 1. angle: from the brand's list (when it has one), and not one of its recent angles or the other new scripts
        aw, best_a = angle_words(ang), None
        if r["choices"] is not None and not any(angle_words(c) == aw for c in r["choices"]):
            out.append({"script": label, "verdict": "too close", "reason": "not on the brand's list", "angle": ang,
                        "closest": None, "list": r["list_file"]}); continue
        for name, other in prev_angles + [(n, o) for j, (n, _, o) in enumerate(new) if j != i and o]:
            sc = jacc(aw, angle_words(other))
            if best_a is None or sc > best_a[0]: best_a = (sc, name, other)
        if best_a and best_a[0] >= ANGLE_LIMIT:
            out.append({"script": label, "verdict": "too close", "reason": "angle", "angle": ang,
                        "closest": best_a[1], "closest_angle": best_a[2]}); continue
        # 2. phrasing: a near-copy of any earlier or other new script
        best_p = None
        for name, t in prev + [(n, t) for j, (n, t, _) in enumerate(new) if j != i]:
            sc = jacc(grams(s), grams(t))
            if best_p is None or sc > best_p[0]: best_p = (sc, name)
        if best_p and best_p[0] >= PHRASING_LIMIT:
            out.append({"script": label, "verdict": "too close", "reason": "phrasing",
                        "closest": best_p[1], "phrasing_overlap": round(best_p[0], 2)}); continue
        out.append({"script": label, "verdict": "ok", "angle": ang})
    return out

if __name__ == "__main__":
    main()
