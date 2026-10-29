#!/usr/bin/env python3
"""Iris's track sheet builder. Reads Nova's output logs and targets, works out each brand's month
(made, goal, still needed, pace), week, today, and all time, and writes the track sheet page with
that data in it. Changes nothing of Nova's.

  python3 "<iris>/tools/iris-report.py" [--month YYYY-MM]
      Writes <iris>/report/iris-track-sheet.html (this month, or the month given) and prints one
      JSON line: the file and each brand's made / goal / still needed.

Counts are original videos (organic + ad).
The brand "Test" (test runs, not official content) is left out.
The page also carries the skills used (finished items per style, from the batch sheets) and the
agents in the system (from Nova's roster).
"""
import subprocess, calendar, json, math, os, re, shutil, sys
from datetime import date, datetime, timedelta
from pathlib import Path

IRIS = Path(__file__).resolve().parents[1]
SUPER = IRIS.parents[1]
MAX_DOCS = SUPER / "Agents" / "NovaOM" / "docs"
MONTHLY = MAX_DOCS / "client-monthly"
TARGETS = MAX_DOCS / "nova-targets.md"
LEDGER = MAX_DOCS / "nova-client-ledger.md"
BACKUPS = MAX_DOCS / "nova-backups.md"
JANI = SUPER / "Agents" / "JaniBA"
TEMPLATE = IRIS / "report" / "iris-template.html"
OUT = IRIS / "report" / "iris-track-sheet.html"
LEFT_OUT = {"Test"}
DESIGNERS = SUPER / "Agents" / "AtlasPM" / "docs" / "atlas-designers.json"


def style_aliases():
    """Old style names -> current ones, from Atlas's designer list ("carousel" -> "corporate carousel",
    2026-10-27), so old sheets count under the style's current name."""
    try: return json.loads(DESIGNERS.read_text(encoding="utf-8")).get("_aliases") or {}
    except (OSError, ValueError): return {"carousel": "corporate carousel"}


def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")


def ledger_brands():
    """Every client brand in Nova's Client Ledger: stored key -> display name. A brand gets its own
    section as soon as it is onboarded, before its first video."""
    out, table = {}, False
    for line in LEDGER.read_text(encoding="utf-8").splitlines() if LEDGER.exists() else []:
        if line.startswith("| Brand name"): table = True; continue
        if not table or line.startswith("|---"): continue
        if not line.startswith("|"): table = False; continue
        name = line.strip().strip("|").split("|")[0].strip()
        if name: out.setdefault(key(name), name)
    return out


def read_log(path):
    """[(date, type)] from one of Nova's monthly files (same format her output tool writes)."""
    if not path.exists(): return []
    out, in_log = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Output log"): in_log = True; continue
        if in_log and line.startswith("|") and not line.startswith("| Date") and not line.startswith("|---"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", c[0]): out.append((c[0], c[1]))
    return out


def targets():
    t, table = {}, False
    for line in TARGETS.read_text(encoding="utf-8").splitlines() if TARGETS.exists() else []:
        if line.startswith("| Brand"): table = True; continue
        if not table or line.startswith("|---"): continue
        if not line.startswith("|"): table = False; continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        num = lambda v: int(v) if re.fullmatch(r"\d+", v or "") else None
        if c and c[0]:
            start = c[4] if len(c) > 5 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", c[4] or "") else None
            t[c[0]] = {"monthly": num(c[1]) if len(c) > 1 else None, "weekly": num(c[2]) if len(c) > 2 else None,
                       "daily": num(c[3]) if len(c) > 3 else None, "start": start}
    return t


def originals(entries):
    return sum(1 for _, ty in entries if ty in ("Organic video", "Ad video"))


def brand_data(brand, tg, ym, today, names):
    y, m = map(int, ym.split("-"))
    dim = calendar.monthrange(y, m)[1]
    entries = []
    for f in sorted((MONTHLY / brand).glob(f"nova-{brand}-*.md")): entries += read_log(f)
    t = tg.get(brand, {})
    # counts from: the target's start date when it falls in this month (earlier months count whole)
    first = 1
    if t.get("start") and t["start"][:7] == ym: first = int(t["start"][8:10])
    elif t.get("start") and t["start"][:7] > ym: first = dim + 1
    def workdays(a, b):                                            # Mon-Fri days from day a to day b of this month
        return sum(1 for d in range(a, b + 1) if 1 <= d <= dim and date(y, m, d).weekday() < 5)
    span = workdays(first, dim)                                     # working days the goal covers this month
    month = [e for e in entries if e[0].startswith(ym) and int(e[0][8:10]) >= first]
    if t.get("monthly"): goal, src = t["monthly"], "monthly target"
    elif t.get("daily"): goal, src = t["daily"] * span, f"{t['daily']} a working day"
    elif t.get("weekly"): goal, src = math.ceil(t["weekly"] * span / 5), f"{t['weekly']} a week (Mon-Fri)"
    else: goal, src = None, None
    if goal is not None and first > 1: src += f", counted from {date(y, m, first).strftime('%b %-d')}"
    made = originals(month)
    is_current = today.strftime("%Y-%m") == ym
    day = today.day if is_current else dim
    days_left = workdays(today.day, dim) if is_current else 0      # working days left, today included
    remaining = max(goal - made, 0) if goal else None
    elapsed = workdays(first, day)                                   # working days of the goal's span so far
    expected = round(goal * elapsed / span) if goal and span > 0 else None   # where an even pace would be by now
    # the work week holding today (shown Mon-Fri; any weekend work still counts toward its week)
    wk0 = today - timedelta(days=today.weekday())
    week_days = {(wk0 + timedelta(days=i)).isoformat() for i in range(7)}
    week_made = originals([e for e in entries if e[0] in week_days])
    week_goal = t.get("weekly") or (t["daily"] * 5 if t.get("daily") else None) or \
        (math.ceil(t["monthly"] * 7 / dim) if t.get("monthly") else None)
    day_goal = t.get("daily") or (math.ceil(t["weekly"] / 5) if t.get("weekly") else None) or \
        (math.ceil(t["monthly"] / max(workdays(1, dim), 1)) if t.get("monthly") else None)
    daily = []
    for d in range(1, dim + 1):
        iso = f"{ym}-{d:02d}"
        daily.append(None if is_current and d > today.day else originals([e for e in month if e[0] == iso]))
    return {
        "brand": brand, "name": names.get(brand, brand),
        "month": {"made": made, "made_all": originals([e for e in entries if e[0].startswith(ym)]),
                  "goal": goal, "goal_from": src, "remaining": remaining, "expected": expected,
                  "per_day_needed": math.ceil(remaining / days_left) if remaining and days_left else (0 if goal else None),
                  "days_left": days_left, "organic": sum(1 for _, x in month if x == "Organic video"),
                  "ad": sum(1 for _, x in month if x == "Ad video")},
        "week": {"made": week_made, "goal": week_goal, "start": wk0.isoformat(), "end": (wk0 + timedelta(days=4)).isoformat()},
        "today": {"made": originals([e for e in entries if e[0] == today.isoformat()]), "goal": day_goal},
        "all_time": {"made": originals(entries)},
        "carousels": {"month": sum(1 for e in month if e[1] == "Carousel"),
                      "all_time": sum(1 for e in entries if e[1] == "Carousel")},
        "daily": daily, "daily_goal": day_goal,
    }


def folder_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for n in files:
            try: total += os.lstat(os.path.join(root, n)).st_size
            except OSError: pass
    return total


def storage():
    """The Mac's disk, what Super Nova takes, the backup drive, and what Jani has backed up."""
    gb = lambda b: round(b / 1e9, 1)
    mac = shutil.disk_usage("/")
    out = {"mac": {"total": gb(mac.total), "used": gb(mac.total - mac.free), "free": gb(mac.free)},
           "super_nova": {"size": gb(folder_size(SUPER)), "project": gb(folder_size(SUPER / "Project"))}}
    try: vol = json.loads((JANI / "docs" / "jani-config.json").read_text())["volume"]
    except (OSError, ValueError, KeyError): vol = None
    d = Path("/Volumes") / vol if vol else None
    if d and d.is_dir():
        u = shutil.disk_usage(d)
        out["backup_drive"] = {"name": vol, "connected": True, "total": gb(u.total), "used": gb(u.total - u.free), "free": gb(u.free)}
    else:
        out["backup_drive"] = {"name": vol, "connected": False}
    videos, last = 0, None
    for line in BACKUPS.read_text(encoding="utf-8").splitlines() if BACKUPS.exists() else []:
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", c[0] if c else ""):
            videos += 1; last = max(last or c[0], c[0])
    try: runs = json.loads((JANI / "docs" / "jani-runs.json").read_text())
    except (OSError, ValueError): runs = []
    out["backed_up"] = {"videos": videos, "size": gb(sum(r.get("size", 0) for r in runs)), "runs": len(runs), "last": last}
    return out


BATCHES = SUPER / "Agents" / "AtlasPM" / "batches"
HERMES_DOCS = SUPER / "Agents" / "HermesMU" / "docs"
DEV_NOTES = MAX_DOCS / "nova-dev-notes.md"
DEV_NOTES_SHOWN = 10


def dev_notes():
    """The latest changes to the system, newest first, from Nova's dev notes."""
    try: text = DEV_NOTES.read_text(encoding="utf-8")
    except OSError: return []
    out = []
    for line in text.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(c) == 3 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", c[0]):
            out.append({"date": c[0], "noticed": c[1], "change": c[2]})
    return out[:DEV_NOTES_SHOWN]


def uploads(ym):
    """Original videos uploaded to Spira, per brand: this month and all time. From Hermes's upload
    log (one entry per video), plus the batches Hermes records
    as uploaded outside him (e.g. by hand), counted on the day they were recorded."""
    out = {}
    def add(brand, day, n=1):
        b = out.setdefault(key(brand), {"month": 0, "all_time": 0})
        b["all_time"] += n
        if (day or "").startswith(ym): b["month"] += n
    try: log = json.loads((HERMES_DOCS / "hermes-upload-log.json").read_text())
    except (OSError, ValueError): log = {}
    for e in log.values(): add(e.get("brand"), e.get("uploaded"))
    try: mem = (HERMES_DOCS / "hermes-working-memory.md").read_text(encoding="utf-8")
    except OSError: mem = ""
    sec = mem.split("## Uploaded outside Hermes", 1)
    if len(sec) == 2:
        for line in sec[1].split("\n## ", 1)[0].splitlines():
            m = re.match(r"-\s*([^,]+),\s*(\d+) videos.*?recorded (\d{4}-\d{2}-\d{2})", line)
            if m: add(m.group(1), m.group(3), int(m.group(2)))
    return out


def credits(ym):
    """Spira credits the designer agents spent in the month: the credits on every DONE row of the
    batch sheets dated that month (the designers' own counts, fixes included). Never the Spira
    account's balance or its all-time total, which also hold the owner's own use."""
    total, by_brand, videos = 0.0, {}, 0
    try: reg = json.loads((MAX_DOCS / "nova-task-register.json").read_text()).get("tasks", {})
    except (OSError, ValueError): reg = {}
    for sheet in sorted(BATCHES.glob(f"atlas-batch-{ym}-*.md")):
        lines = [l for l in sheet.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
        if len(lines) < 3: continue
        hdr = [c.strip() for c in lines[0].strip().strip("|").split("|")]
        if "Result" not in hdr or "Brand" not in hdr: continue
        for l in lines[2:]:
            c = [x.strip().replace("\\|", "|") for x in re.split(r"(?<!\\)\|", l.strip().strip("|"))]   # a \| inside a cell is text
            if len(c) != len(hdr): continue
            row = dict(zip(hdr, c))
            m = re.match(r"DONE\s+.+?(?:\.(?:mp4|png)|/carousels/[^\s/]+/?)\s+([\d.]+)", row.get("Result") or "")   # videos, avatar images and carousel folders
            if not m: continue
            v = float(m.group(1)); total += v; videos += 1
            tid = (row.get("Task ID") or "").lstrip("0").zfill(2)
            k = (reg.get(tid) or {}).get("brand") or key(row["Brand"])   # the register wins (e.g. a test made official)
            by_brand[k] = by_brand.get(k, 0.0) + v
    return {"total": round(total), "videos": videos, "usd_per_credit": 0.01,
            "by_brand": {k: round(v) for k, v in by_brand.items()}}


def skills(ym):
    """Finished items per style (the designer skill used): this month, with each brand's count and
    the credits spent, and the all-time count. From the DONE rows of the batch sheets (the month's
    sheets by the date in their name; all time, every sheet). A blank Style is talking head edited; an
    old style name counts under its current one (Style carousel is corporate carousel)."""
    aliases = style_aliases()
    try: reg = json.loads((MAX_DOCS / "nova-task-register.json").read_text()).get("tasks", {})
    except (OSError, ValueError): reg = {}
    cells = lambda l: [x.strip() for x in re.split(r"(?<!\\)\|", l.strip().strip("|"))]   # a \| inside a cell is text
    month, all_time = {}, {}
    for sheet in sorted(BATCHES.glob("atlas-batch-*.md")):
        in_month = sheet.name.startswith(f"atlas-batch-{ym}-")
        lines = [l for l in sheet.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
        if len(lines) < 3: continue
        hdr = cells(lines[0])
        if not {"Result", "Style", "Brand"} <= set(hdr): continue
        for l in lines[2:]:
            c = cells(l)
            if len(c) != len(hdr): continue
            row = dict(zip(hdr, c))
            res = row.get("Result") or ""
            if not res.startswith("DONE"): continue
            style = " ".join((row.get("Style") or "").lower().split()) or "talking head edited"
            style = aliases.get(style, style)
            all_time[style] = all_time.get(style, 0) + 1
            if not in_month: continue
            m = re.match(r"DONE\s+.+?(?:\.(?:mp4|png)|/carousels/[^\s/]+/?)\s+([\d.]+)", res)
            tid = (row.get("Task ID") or "").lstrip("0").zfill(2)
            k = (reg.get(tid) or {}).get("brand") or key(row["Brand"])   # the register wins, as in credits()
            s = month.setdefault(style, {"count": 0, "credits": 0.0, "costed": 0, "by_brand": {}})
            s["count"] += 1
            c = float(m.group(1)) if m else 0.0
            s["credits"] += c
            if c > 0: s["costed"] += 1   # videos made outside the team (0 credits) stay out of the per-video average
            s["by_brand"][k] = s["by_brand"].get(k, 0) + 1
    for s in month.values(): s["credits"] = round(s["credits"])
    order = lambda d, n: dict(sorted(d.items(), key=lambda kv: (-n(kv[1]), kv[0])))
    return {"month": order(month, lambda s: s["count"]), "all_time": order(all_time, lambda n: n)}


def roster():
    """The agents in the system, from Nova's roster."""
    try: return json.loads((MAX_DOCS / "nova-roster.json").read_text(encoding="utf-8")).get("agents", [])
    except (OSError, ValueError): return []


def main():
    a = sys.argv[1:]
    today = date.today()
    ym = a[a.index("--month") + 1] if "--month" in a else today.strftime("%Y-%m")
    tg = targets(); names = ledger_brands()
    found = ({p.name for p in MONTHLY.iterdir() if p.is_dir()} if MONTHLY.is_dir() else set()) | set(tg) | set(names)
    brands = sorted((b for b in found if b not in LEFT_OUT), key=lambda b: names.get(b, b).lower()) + \
             sorted(b for b in found if b in LEFT_OUT)   # test runs: shown last, never in the totals
    y, m = map(int, ym.split("-"))
    data = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "month": ym,
            "month_name": date(y, m, 1).strftime("%B %Y"), "days_in_month": calendar.monthrange(y, m)[1],
            "today": today.isoformat(), "day_of_month": today.day if today.strftime("%Y-%m") == ym else None,
            "workdays_left": sum(1 for d in range(today.day, calendar.monthrange(y, m)[1] + 1) if date(y, m, d).weekday() < 5) if today.strftime("%Y-%m") == ym else 0,
            "brands": [dict(brand_data(b, tg, ym, today, names), test=b in LEFT_OUT) for b in brands], "storage": storage(), "credits": credits(ym)}
    data["dev_notes"] = dev_notes()
    data["skills"] = skills(ym)
    data["roster"] = roster()
    up = uploads(ym)
    for b in data["brands"]:
        u = up.get(b["brand"], {"month": 0, "all_time": 0})
        b["uploads"] = {"month": u["month"], "made_month": b["month"]["made_all"], "all_time": u["all_time"],
                        "made_all_time": b["all_time"]["made"]}
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    if "/*IRIS_DATA*/null" not in html: sys.exit("FAILED the template has no /*IRIS_DATA*/null placeholder")
    OUT.write_text(html.replace("/*IRIS_DATA*/null", payload), encoding="utf-8")
    print(json.dumps({"file": str(OUT), "month": ym, "brands": {b["name"]: {k: b["month"][k] for k in ("made", "goal", "remaining")}
                                                               for b in data["brands"]}}))


if __name__ == "__main__":
    main()
