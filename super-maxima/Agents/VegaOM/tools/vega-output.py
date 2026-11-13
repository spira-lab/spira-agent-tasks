#!/usr/bin/env python3
"""Vega's output bookkeeping. Logs completed outputs and answers count questions,
printing one short line, so Vega never opens his monthly files or data sheet.

  python3 "<max>/tools/vega-output.py" log <brand> <type> [count] [--date YYYY-MM-DD]
      Logs completed outputs (never rejected, failed, or cancelled ones). Creates the
      brand's monthly file from the template when it is missing (new client or new
      month), then refreshes that month's totals and the brand's all-time row in the
      Client Data Sheet.
  python3 "<max>/tools/vega-output.py" count <brand> [all | month YYYY-MM | week YYYY-MM-DD]
      Prints the totals: all time (default), one month, or the Monday-Sunday week
      holding that date (reads both months when the week spans two).
  python3 "<max>/tools/vega-output.py" move <brand> <to brand> <type> <count> --date YYYY-MM-DD
      Moves already-logged outputs of that type and date from one brand to another (e.g.
      to "Test" when the user says they were test runs, not official content), so they
      stop counting for the first brand. Refreshes both brands' months and all-time rows.

  python3 "<max>/tools/vega-output.py" redate <brand> <type> <count> --from YYYY-MM-DD --to YYYY-MM-DD
      Moves already-logged outputs to another day for the same brand (e.g. when the owner says
      videos made on a closed week count toward the current one).

<type>: organic-video, ad-video, organic-post, ad-post, carousel.
<brand> is stored without spaces or special characters ("Glow Lab Co." -> GlowLabCo).
"""
import fcntl, json, re, sys
from datetime import date, timedelta
from pathlib import Path

MAX = Path(__file__).resolve().parents[1]
DOCS = MAX / "docs"
MONTHLY = DOCS / "client-monthly"
TEMPLATE = MONTHLY / "vega-monthly-template.md"
DATA_SHEET = DOCS / "vega-client-data.md"
LOCK = DOCS / ".vega-output.lock"

TYPES = {"organic-video": "Organic video", "ad-video": "Ad video",
         "organic-post": "Organic post", "ad-post": "Ad post", "carousel": "Carousel"}
COLS = ["Projects completed", "Original videos", "Organic videos", "Ad videos",
        "Image posts", "Organic posts", "Ad posts", "Carousels"]
# Retired (2026-10-24): repurpose videos are no longer made or logged. Older files and the data
# sheet may still have the column; it keeps showing what was logged before, never anything new.
RETIRED = {"Repurpose videos": "Repurpose video"}

def brand_key(name):
    return re.sub(r"[^A-Za-z0-9]", "", name or "") or "Brandless"

def month_file(brand, ym):
    return MONTHLY / brand / f"vega-{brand}-{ym}.md"

def read_log(path):
    """[(date, type)] from a monthly file's output log."""
    if not path.exists(): return []
    out, in_log = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Output log"): in_log = True; continue
        if in_log and line.startswith("|") and not line.startswith("| Date") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0]): out.append((cells[0], cells[1]))
    return out

def totals(entries):
    c = {t: 0 for t in TYPES.values()}
    for _, t in entries:
        if t in c: c[t] += 1
    orig = c["Organic video"] + c["Ad video"]
    img = c["Organic post"] + c["Ad post"] + c["Carousel"]
    return dict(zip(COLS, [orig + img, orig, c["Organic video"], c["Ad video"],
                           img, c["Organic post"], c["Ad post"], c["Carousel"]]))

def cells_for(header, entries):
    """The values for a totals table, in the order of its own header (a file made before a column
    was retired still has it)."""
    t = totals(entries)
    for col, ty in RETIRED.items(): t[col] = sum(1 for _, x in entries if x == ty)
    return [str(t.get(h, 0)) for h in header]

def header_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

def write_month(path, brand, ym, entries):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        text = TEMPLATE.read_text(encoding="utf-8").replace("[Brand name]", brand).replace("[YYYY-MM]", ym)
        text = "\n".join(l for l in text.splitlines() if not l.startswith("Copy this template")) + "\n"
        text = re.sub(r"\n{3,}", "\n\n", text)
    else:
        text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # month totals: the row right after the totals separator
    for i, l in enumerate(lines):
        if l.startswith("| Projects completed"):
            lines[i + 2] = "| " + " | ".join(cells_for(header_cells(l), entries)) + " |"; break
    # output log: rebuild rows after its separator
    j = next(i for i, l in enumerate(lines) if l.startswith("| Date"))
    lines = lines[: j + 2] + [f"| {d} | {ty} |" for d, ty in sorted(entries)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def all_entries(brand):
    out = []
    for f in sorted((MONTHLY / brand).glob(f"vega-{brand}-*.md")) if (MONTHLY / brand).is_dir() else []:
        out += read_log(f)
    return out

def write_data_sheet(brand):
    lines = DATA_SHEET.read_text(encoding="utf-8").splitlines()
    j = next(i for i, l in enumerate(lines) if l.startswith("| Brand name"))
    row = f"| {brand} | " + " | ".join(cells_for(header_cells(lines[j])[1:], all_entries(brand))) + " |"
    body = [l for l in lines[j + 2:] if l.startswith("|") and l.strip("| ").strip()]
    body = [l for l in body if l.split("|")[1].strip() != brand] + [row]
    rest = [l for l in lines[j + 2:] if not l.startswith("|")]
    lines = lines[: j + 2] + sorted(body, key=lambda l: l.split("|")[1].strip().lower()) + rest
    DATA_SHEET.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    cmd, brand = sys.argv[1], brand_key(sys.argv[2])
    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        if cmd == "log":
            if len(sys.argv) < 4 or sys.argv[3] not in TYPES:
                sys.exit(f"type must be one of: {', '.join(TYPES)}")
            args = sys.argv[4:]
            day = date.today().isoformat()
            if "--date" in args:
                k = args.index("--date"); day = args[k + 1]; args = args[:k] + args[k + 2:]
                date.fromisoformat(day)
            n = int(args[0]) if args else 1
            if n < 1: sys.exit("count must be 1 or more")
            ym = day[:7]; path = month_file(brand, ym)
            entries = read_log(path) + [(day, TYPES[sys.argv[3]])] * n
            write_month(path, brand, ym, entries)
            write_data_sheet(brand)
            print(json.dumps({"logged": n, "type": TYPES[sys.argv[3]], "brand": brand, "date": day}))
        elif cmd == "move":
            if len(sys.argv) < 8 or sys.argv[4] not in TYPES or sys.argv[6] != "--date":
                sys.exit(__doc__)
            to, ty, n, day = brand_key(sys.argv[3]), TYPES[sys.argv[4]], int(sys.argv[5]), sys.argv[7]
            date.fromisoformat(day)
            ym = day[:7]; src = read_log(month_file(brand, ym))
            have = sum(1 for e in src if e == (day, ty))
            if n < 1 or n > have: sys.exit(f"{brand} has {have} {ty} logged on {day}; cannot move {n}")
            left, moved = [], 0
            for e in src:
                if e == (day, ty) and moved < n: moved += 1
                else: left.append(e)
            write_month(month_file(brand, ym), brand, ym, left)
            write_month(month_file(to, ym), to, ym, read_log(month_file(to, ym)) + [(day, ty)] * n)
            write_data_sheet(brand); write_data_sheet(to)
            print(json.dumps({"moved": n, "type": ty, "from": brand, "to": to, "date": day}))
        elif cmd == "redate":
            # redate <brand> <type> <count> --from YYYY-MM-DD --to YYYY-MM-DD: the same outputs, counted on another day
            a = sys.argv[3:]
            if len(a) < 6 or a[0] not in TYPES or "--from" not in a or "--to" not in a: sys.exit(__doc__)
            ty, n = TYPES[a[0]], int(a[1]); d0, d1 = a[a.index("--from") + 1], a[a.index("--to") + 1]
            date.fromisoformat(d0); date.fromisoformat(d1)
            src = read_log(month_file(brand, d0[:7]))
            have = sum(1 for e in src if e == (d0, ty))
            if n < 1 or n > have: sys.exit(f"{brand} has {have} {ty} logged on {d0}; cannot redate {n}")
            left, moved = [], 0
            for e in src:
                if e == (d0, ty) and moved < n: moved += 1
                else: left.append(e)
            if d0[:7] == d1[:7]:
                write_month(month_file(brand, d0[:7]), brand, d0[:7], left + [(d1, ty)] * n)
            else:
                write_month(month_file(brand, d0[:7]), brand, d0[:7], left)
                write_month(month_file(brand, d1[:7]), brand, d1[:7], read_log(month_file(brand, d1[:7])) + [(d1, ty)] * n)
            write_data_sheet(brand)
            print(json.dumps({"redated": n, "type": ty, "brand": brand, "from": d0, "to": d1}))
        elif cmd == "count":
            scope = sys.argv[3] if len(sys.argv) > 3 else "all"
            if scope == "all":
                entries, label = all_entries(brand), "all time"
            elif scope == "month":
                ym = sys.argv[4]; entries, label = read_log(month_file(brand, ym)), ym
            elif scope == "week":
                d = date.fromisoformat(sys.argv[4]); mon = d - timedelta(days=d.weekday()); sun = mon + timedelta(days=6)
                months = {mon.isoformat()[:7], sun.isoformat()[:7]}
                entries = [e for ym in sorted(months) for e in read_log(month_file(brand, ym))
                           if mon.isoformat() <= e[0] <= sun.isoformat()]
                label = f"week {mon.isoformat()} to {sun.isoformat()}"
            else:
                sys.exit(__doc__)
            print(json.dumps({"brand": brand, "scope": label, **totals(entries)}))
        else:
            sys.exit(__doc__)

if __name__ == "__main__":
    main()
