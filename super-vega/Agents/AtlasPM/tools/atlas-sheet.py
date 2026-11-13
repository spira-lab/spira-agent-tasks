#!/usr/bin/env python3
"""Atlas sheet helper for batch production. Every read and write of the batch sheet goes
through here, so the orchestrating session never loads the sheet into its context.
The sheet is a Markdown table (.md); an .xlsx sheet also works.

  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> next
      Takes the first row whose Status is blank or pending, marks it designing,
      and prints {"task_id": ..., "request": ...}. Prints NONE when no row is left.
      Prints "FULL <n>/<cap>" and the rows counted (and claims nothing) when <cap> rows are
      already designing across every sheet in <atlas>/batches/ (docs/atlas-limits.json, 20).
      An avatar row's request carries only the avatar description; a carousel row's (any style
      ending in "carousel", e.g. corporate carousel; Output type carousel) only the brand, its
      numbers, the instructions (with the product and the brand website) and Echo's topic angle
      from the Script column; a scriptless carousel style's (lifestyle story carousel, 2026-11-03)
      the same without an angle (its designer picks its own idea). An old style name (e.g. "carousel") reads as its current one
      (the _aliases in atlas-designers.json).
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> request <task id>
      Prints a row's request again, as `next` did, whatever its status (to brief a new
      designer for a row after a restart). Changes nothing.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> list <status>
      Prints the Task IDs whose Status is <status>, one per line, in sheet order.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> agent <task id> [<agent id>]
      Records, or with no agent id prints, the subagent session that owns a row.
      Kept in <sheet>.agents.json beside the sheet, not in the sheet itself.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> mark <task id> <status> [--if <current status>] <result text>
      Writes the status and outcome into that row, with the minutes since it started.
      With --if, it changes the row only while its status is still <current status>
      (prints "<id>: unchanged (<status>)" otherwise), so a late reply never moves a row back.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> wait [seconds] [--also <sheet2.md> ...]
      Blocks until any row's status changes (a designer marking its row) or the seconds run
      out (default 110, at most 540), then prints {"changed": [...], "timeout": bool}.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> slots
      Prints {"designing", "cap", "rendering", "render_cap", "renders", "timing", "timing_cap",
      "timings", "free"} across every batch sheet; "renders" names who holds each busy render
      slot (heavy-slot.py), "timings" each busy Whisper timing slot (timing_slot.py).
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> recover
      After a restart: one JSON line per designing or question row in every batch sheet, with
      its agent id, its metadata and chain.json files, and the jobs submitted there that have
      no result yet ("jobs_in_flight": wait for those, never submit them again).
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> summary
      Counts rows by status and lists every row that is not done.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> create
      Makes a new, empty batch sheet at <sheet.md> from the blank template.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> add "Column=value" ...
      Appends one row: pending when it has a Script, draft (waiting for its script) when not. A value starting with @ is read from that file
      (e.g. "Script=@<path>"), so a script never has to pass through anyone's context.
      Files must be inside the Super Vega folder.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> set <task id> "Column=value" ...
      Changes a draft or pending row (Echo, the script director, fills "Script=@<file>" this way).
      A draft row becomes pending once it has a script.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> tally
      Counts finished (done) rows by brand and Output type, for Vega's output log.
      Output types: organic-video, ad-video, avatar-image, carousel.
  python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> remove <task id>
      Data Cleaner only, for a CANCELLED task: deletes the row and its session record.

Do not edit the sheet while a batch runs: this saves into it. Atlas and his designers may
write at the same time, so every command holds a lock on <sheet>.lock while it reads and saves.
"""
import fcntl, json, os, re, sys, time
from datetime import datetime
from pathlib import Path

# <super>/Agents/AtlasPM/tools/atlas-sheet.py -> <super> (Super Vega) is three levels up
PROJECT = Path(__file__).resolve().parents[3]
AGENTS = PROJECT / "Agents"
DEFAULT_SKILL = AGENTS / "TalkingHeadEditedVideoDesigner" / "skills" / "talking-head-edited-video-designer.md"
COLS = ["Task ID", "Brand", "Brand number", "Output type", "Duration", "Style", "Read the skill", "Style ref", "Source video", "Product", "Brand logo", "Brand color", "Avatar image", "Avatar voice",
        "Instructions", "Script", "Music", "After video skill", "Status", "Started", "Minutes", "Result"]
# Retired columns: an older sheet that has one keeps it in its old place (before the column
# named here) when saved; new sheets never get it, and nothing reads it. Repurpose: 2026-10-24.
RETIRED = {"Repurpose": "Status"}
INPUTS = COLS[:COLS.index("Status")]
OUTPUT_TYPES = {"organic-video", "ad-video", "avatar-image", "carousel"}
DESIGNERS = Path(__file__).resolve().parents[1] / "docs" / "atlas-designers.json"
RUNNABLE = {"", "pending"}
# Parallel production (the owner's decision, 2026-11-13): at most 20 rows designing across every
# batch sheet of this employee, at most 10 renders at once (the render slots of heavy-slot.py) and
# at most 10 Whisper transcriptions at once (the timing slots of timing_slot.py).
LIMITS = Path(__file__).resolve().parents[1] / "docs" / "atlas-limits.json"
BATCHES = Path(__file__).resolve().parents[1] / "batches"
LOCKS = PROJECT / ".locks"
IN_FLIGHT = {"submitted", "queued", "running", "processing", "pending"}

# ---------- markdown table ----------
def md_cells(line):
    s = line.strip()
    if s.startswith("|"): s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"): s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]

def md_load(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip().startswith("|")), None)
    if start is None: sys.exit(f"no table found in {path}")
    end = start
    while end < len(lines) and lines[end].strip().startswith("|"): end += 1
    head = md_cells(lines[start])
    body = [md_cells(l) for l in lines[start + 2:end]]
    rows = [{h: (c[i] if i < len(c) else "") for i, h in enumerate(head)} for c in body]
    return rows, (lines[:start], head, lines[end:])

def md_save(path, rows, handle):
    before, head, after = handle
    known = list(COLS)
    for c, at in RETIRED.items():
        if c in head: known.insert(known.index(at), c)   # an old sheet keeps its retired column in place
    extra = [h for h in head if h not in known]
    for r in rows:
        extra += [k for k in r if k not in known and k not in extra]
    head = known + extra   # known columns in their fixed order, extra ones (like Topic) after them
    esc = lambda v: " ".join(str(v).split()).replace("|", "\\|")
    table = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    table += ["| " + " | ".join(esc(r.get(h, "")) for h in head) + " |" for r in rows]
    tmp = path.with_name(path.stem + ".saving" + path.suffix)
    tmp.write_text("\n".join(before + table + after) + "\n", encoding="utf-8"); os.replace(tmp, path)

# ---------- xlsx ----------
def xl_load(path):
    import openpyxl
    wb = openpyxl.load_workbook(path); ws = wb.active
    head = [str(c.value or "").strip() for c in ws[1]]
    rows = [{h: ("" if v is None else str(v).strip()) for h, v in zip(head, r)}
            for r in ws.iter_rows(min_row=2, values_only=True)]
    return rows, (wb, ws, head)

def xl_save(path, rows, handle):
    wb, ws, head = handle
    for c in COLS:
        if c not in head: head.append(c); ws.cell(row=1, column=len(head), value=c)
    for i, r in enumerate(rows, start=2):
        for j, h in enumerate(head, start=1): ws.cell(row=i, column=j, value=r.get(h, ""))
    tmp = path.with_name(path.stem + ".saving" + path.suffix); wb.save(tmp); os.replace(tmp, path)

def load(path):  return md_load(path) if path.suffix.lower() == ".md" else xl_load(path)
def save(path, rows, handle):
    (md_save if path.suffix.lower() == ".md" else xl_save)(path, rows, handle)

def filled(r): return any(r.get(c, "") for c in INPUTS)

def music_line(v):
    v = v.strip()
    if not v: return None                                   # blank: the skill generates music
    if v.lower() in {"none", "no", "no music", "no bgm"}: return "Music: no music."
    if v.lower() in {"library", "lib", "music library"}: return "Music: use music from the library."
    return f"Music: {v}"

def inside_skill(value, what, task):
    """Skills are read only from inside the Super Vega folder; outside copies may be outdated."""
    p = Path(value).expanduser()
    p = (p if p.is_absolute() else PROJECT / p).resolve()
    if not p.is_relative_to(PROJECT):
        sys.exit(f"row {task}: {what} must be inside {PROJECT}, not {p}")
    if not p.is_file():
        sys.exit(f"row {task}: {what} not found at {p}")
    return str(p)

def style_name(value):
    """A style's current name: lower case, single spaces, and an old name mapped to its new one
    through _aliases in Atlas's designer list ("carousel" -> "corporate carousel", 2026-10-27)."""
    s = " ".join((value or "").lower().split())
    try: aliases = json.loads(DESIGNERS.read_text()).get("_aliases") or {}
    except (OSError, ValueError): aliases = {}
    return aliases.get(s, s)

def is_carousel(value):
    """A carousel style: any style whose name ends in "carousel" (corporate carousel, and the
    carousel designers to come). They share output type carousel and the carousel path."""
    return style_name(value).endswith("carousel")

def style_entry(style_value):
    """(designer skill path, needs a script) for a style, from Atlas's designer list."""
    d = json.loads(DESIGNERS.read_text())
    style = style_name(style_value) or style_name(d["default"])
    e = d.get(style) if not style.startswith("_") and style != "default" else None
    if e is None: return None, True
    if isinstance(e, str): return e, True
    return e["skill"], (e.get("script", "required") != "none")

def needs_script(r):
    return style_entry(r.get("Style"))[1]

def designer_for(r):
    """Read the skill wins; otherwise the row's Style, looked up in Atlas's designer list."""
    if r.get("Read the skill"): return r["Read the skill"]
    skill, _ = style_entry(r.get("Style"))
    if skill is None:
        sys.exit(f"row {r['Task ID']}: no designer for style {style_name(r.get('Style'))!r} in {DESIGNERS.name}")
    return str(PROJECT / skill)

def check_duration(r):
    d = (r.get("Duration") or "").strip()
    if not d:
        return                        # no duration given: the writing style's own default applies

    if not d.isdigit() or int(d) < 1:
        sys.exit(f"Duration must be a whole number of seconds, not {d!r}")

def check_style(value):
    d = json.loads(DESIGNERS.read_text())
    style = style_name(value)
    if style and (style not in d or style.startswith("_") or style == "default"):
        known = ", ".join(k for k in d if not k.startswith("_") and k != "default")
        sys.exit(f"no designer for style {style!r}; available: {known}")

def full_path(v):
    """Designers work from inside Project/, so a file path written relative to the Super Vega
    folder (e.g. Agents/VegaOM/client-assets/...) is passed on as a full path. URLs pass as they are."""
    v = (v or "").strip()
    if not v or "://" in v or Path(v).is_absolute(): return v
    p = (PROJECT / v).resolve()
    return str(p) if p.exists() and p.is_relative_to(PROJECT) else v

AVATAR_STYLE = "avatar"

def build_request(r):
    r = dict(r)
    style = style_name(r.get("Style"))
    if is_carousel(style):
        # A carousel row (the owner's decisions, 2026-10-27): 4:5 slides made by that style's carousel
        # designer (corporate carousel: the Corporate Carousel Designer).
        # Its inputs are only Echo's topic angle (the Script column) and the website; Vega's batch tool
        # puts "Product: <name>." and "Brand website: <url>" in Instructions. No video-only fields:
        # no duration, music, style reference, source video, logo, color, avatar or after-video skill.
        skill = inside_skill(designer_for(r), "Designer skill", r['Task ID'])
        lines = [f"Task ID: {r['Task ID']}", f"Read this skill first: {skill}"]
        if r.get("Brand"): lines.append(f"Brand: {r['Brand']}")
        if not needs_script(r):
            # A scriptless carousel style (lifestyle story carousel, 2026-11-03): no topic angle from Echo;
            # the designer picks and researches its own idea. A story (9:16) only when the instructions ask.
            lines += [f"Brand number: {r['Brand number']}",
                      "This is a carousel task: slides as JPEGs, 4:5 (1080x1350) unless the instructions ask for a 9:16 story, no video and no music."]
            if r.get("Instructions"): lines.append(f"These are the instructions: {r['Instructions']}")
            lines.append("This is a scriptless carousel: there is no topic angle. Pick and research your own idea as your skill says, and work from the instructions above.")
            return "\n".join(lines)
        lines += [f"Brand number: {r['Brand number']}",
                  "This is a carousel task: 4:5 slides (1080x1350 JPEGs), no video and no music."]
        if r.get("Instructions"): lines.append(f"These are the instructions: {r['Instructions']}")
        lines += ["Here is the topic angle:", r.get("Script") or ""]
        return "\n".join(lines)
    if style == AVATAR_STYLE:
        # An avatar row: the designer gets only what the avatar looks like (the owner's rule,
        # 2026-10-22), never a script, logo, color, product, music or style reference.
        skill = inside_skill(designer_for(r), "Designer skill", r['Task ID'])
        desc = (r.get("Instructions") or "").strip() or "No description given: decide the avatar yourself, with no question."
        return "\n".join([f"Task ID: {r['Task ID']}", f"Read this skill first: {skill}", f"Brand: {r.get('Brand') or 'Avatar'}",
                          f"Brand number: {r['Brand number']}", "This is an avatar image task: no script and no video.",
                          f"These are the instructions: {desc}"])
    for c in ("Style ref", "Source video", "Product", "Brand logo", "Avatar image"): r[c] = full_path(r.get(c))
    skill = inside_skill(designer_for(r), "Designer skill", r['Task ID'])
    lines = [f"Task ID: {r['Task ID']}", f"Read this skill first: {skill}"]
    if r.get("Brand"): lines.append(f"Brand: {r['Brand']}")
    # Duration is never passed on: it is only for Echo, who writes the script to it.
    # The designer takes the video's length from the script itself.
    lines.append(f"Brand number: {r['Brand number']}")
    if r.get("Style ref"): lines.append(f"This is the style: {r['Style ref']}")
    if r.get("Source video"): lines.append(f"This is the source video: {r['Source video']}")
    if r.get("Product"): lines.append(f"This is the product image: {r['Product']}")
    if r.get("Brand logo"): lines.append(f"Use this brand logo: {r['Brand logo']}")
    if r.get("Brand color"): lines.append(f"Use this brand color: {r['Brand color']}")
    if r.get("Avatar image"): lines.append(f"Use this avatar image: {r['Avatar image']}")
    if r.get("Avatar voice"): lines.append(f"Use this avatar voice: {r['Avatar voice']}")
    m = music_line(r.get("Music", ""))
    if m: lines.append(m)
    if r.get("Instructions"): lines.append(f"These are the instructions: {r['Instructions']}")
    if r.get("Script"):
        lines += ["Here is the script:", r["Script"]]
    else:
        lines.append("This is a scriptless video: there is no script. Work from the instructions above.")
    if r.get("After video skill"):
        after = inside_skill(r['After video skill'], "After video skill", r['Task ID'])
        lines.append(f"Read this skill right after you complete the video and continue: {after}")
    return "\n".join(lines)

TEMPLATE = Path(__file__).resolve().parents[1] / "docs" / "atlas-batch-template.md"

def create(path):
    if path.exists(): sys.exit(f"{path} already exists")
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    out, in_table, seen = [], False, 0
    for l in lines:
        if l.strip().startswith("|"):
            seen += 1
            if seen > 2: continue          # keep header + separator, drop example rows
        out.append(l)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"created {path}")

def field_value(v):
    if not v.startswith("@"): return v
    f = Path(v[1:]).expanduser().resolve()
    if not f.is_relative_to(PROJECT): sys.exit(f"{f} is outside {PROJECT}")
    if not f.is_file(): sys.exit(f"no file at {f}")
    return " ".join(f.read_text(encoding="utf-8").split())

def statuses(path):
    with open(path.with_name(path.name + ".lock"), "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_SH)
        rows, _ = load(path)
    return {r.get("Task ID", ""): (r.get("Status") or "pending").lower() for r in rows if filled(r)}

def limits():
    try: d = json.loads(LIMITS.read_text())
    except (OSError, ValueError): d = {}
    return int(d.get("designing") or 20), int(d.get("rendering") or 10), int(d.get("timing") or 10)

def batch_sheets(extra=None):
    sheets = {p.resolve() for p in BATCHES.glob("*.md") if ".saving" not in p.name} if BATCHES.is_dir() else set()
    if extra is not None: sheets.add(extra)
    return sorted(sheets)

def designing_elsewhere(own):
    """(sheet, Task ID) of every designing row in the other batch sheets. Never reads `own`:
    the caller holds its lock, and a second lock on it from this process would wait forever."""
    out = []
    for p in batch_sheets():
        if p == own: continue
        try: st = statuses(p)
        except (SystemExit, OSError, ValueError): continue
        out += [(p, t) for t, s in st.items() if s == "designing"]
    return out

def held_slots(kind="render"):
    """Who holds each busy render (heavy-slot.py) or timing (timing_slot.py) slot, from the .who
    file written beside it."""
    busy = []
    for f in sorted(LOCKS.glob(f"{kind}-slot-*.lock")) if LOCKS.is_dir() else []:
        with open(f, "a") as lk:
            try: fcntl.flock(lk, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                who = f.with_suffix(".who")
                busy.append(who.read_text(encoding="utf-8").strip() if who.exists() else f.stem)
    return busy

def jobs_in_flight(node, out):
    """Every job entry with a job_id still waiting for its result (chain.json, metadata jobs/assets)."""
    if isinstance(node, dict):
        if node.get("job_id") and str(node.get("status") or "").lower() in IN_FLIGHT:
            out.append({k: node.get(k) for k in ("job_id", "status", "file", "kind", "model", "id") if node.get(k) is not None})
        for v in node.values(): jobs_in_flight(v, out)
    elif isinstance(node, list):
        for v in node: jobs_in_flight(v, out)
    return out

def recover(extra=None):
    """One JSON line per designing or question row, with what a restart needs to pick it up."""
    for p in batch_sheets(extra):
        try:
            with open(p.with_name(p.name + ".lock"), "a") as lk:
                fcntl.flock(lk, fcntl.LOCK_SH)
                rows, _ = load(p)
        except (SystemExit, OSError, ValueError): continue
        side = p.with_name(p.name + ".agents.json")
        try: agents = json.loads(side.read_text()) if side.exists() else {}
        except ValueError: agents = {}
        for r in rows:
            task, status = r.get("Task ID", ""), (r.get("Status") or "pending").lower()
            if status not in {"designing", "question"} or not task or not filled(r): continue
            nn = task.zfill(2)
            files = sorted(str(f) for f in (PROJECT / "Project").glob(f"*/metadata/{nn}-*.json"))
            files += sorted(str(f) for f in (PROJECT / "Project").glob(f"*/editable/materials/{nn}-*/chain.json"))
            jobs = []
            for f in files:
                try: jobs_in_flight(json.loads(Path(f).read_text(encoding="utf-8")), jobs)
                except (OSError, ValueError): pass
            print(json.dumps({"sheet": str(p), "task_id": task, "status": status, "started": r.get("Started", ""),
                              "agent": agents.get(task), "files": files, "jobs_in_flight": jobs}))

def wait(path, secs, also=()):
    """Block until a row's status changes, so Atlas never has to end his turn to be woken.
    --also <sheet> watches more sheets at the same time (a tail handoff runs two)."""
    secs = max(5, min(int(secs), 540))
    paths = [path] + [Path(x).expanduser().resolve() for x in also]
    def all_statuses():
        return {(p.name if len(paths) > 1 else "", t): s for p in paths for t, s in statuses(p).items()}
    before, end = all_statuses(), time.time() + secs
    while time.time() < end:
        time.sleep(3)
        now = all_statuses()
        changed = [f"{(n + ' ') if n else ''}{t}: {s}" for (n, t), s in now.items() if before.get((n, t)) != s]
        if changed:
            print(json.dumps({"changed": changed, "timeout": False})); return
    print(json.dumps({"changed": [], "timeout": True}))

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    path = Path(sys.argv[1]).expanduser().resolve(); cmd = sys.argv[2]
    if cmd == "create": return create(path)
    if cmd == "slots":
        cap, render_cap, timing_cap = limits()
        designing = 0
        for p in batch_sheets(path if path.is_file() else None):
            try: designing += sum(1 for s in statuses(p).values() if s == "designing")
            except (SystemExit, OSError, ValueError): pass
        busy, timings = held_slots("render"), held_slots("timing")
        print(json.dumps({"designing": designing, "cap": cap, "rendering": len(busy), "render_cap": render_cap,
                          "renders": busy, "timing": len(timings), "timing_cap": timing_cap,
                          "timings": timings, "free": max(0, cap - designing)})); return
    if cmd == "recover":
        return recover(path if path.is_file() else None)
    if not path.is_file(): sys.exit(f"No sheet at {path}")
    if cmd == "wait":
        a = sys.argv[3:]; also = []
        while "--also" in a:
            i = a.index("--also"); also.append(a[i + 1]); del a[i:i + 2]
        return wait(path, a[0] if a else 110, also)
    if cmd == "next":
        # Taken before the sheet's own lock, by every `next` alike, so two batches never both
        # claim the last free slot and never wait on each other's sheets.
        BATCHES.mkdir(parents=True, exist_ok=True)
        slots_lock = open(BATCHES / ".slots.lock", "a")
        fcntl.flock(slots_lock, fcntl.LOCK_EX)
    lock = open(path.with_name(path.name + ".lock"), "a")
    fcntl.flock(lock, fcntl.LOCK_EX)          # released when the process exits
    rows, handle = load(path)
    for r in rows:
        for c in COLS: r.setdefault(c, "")
    if cmd == "next":
        cap = limits()[0]
        for r in rows:
            if filled(r) and r["Status"].lower() in RUNNABLE:
                if not r["Task ID"] or not r["Brand number"] or (needs_script(r) and not r["Script"]):
                    sys.exit("a pending row is missing its Task ID, Brand number, or Script")
                mine = [x["Task ID"] for x in rows if filled(x) and x["Status"].lower() == "designing"]
                others = designing_elsewhere(path)
                if len(mine) + len(others) >= cap:
                    print(f"FULL {len(mine) + len(others)}/{cap}")
                    print("designing: " + ", ".join(mine + [f"{p.name} {t}" for p, t in others])); return
                request = build_request(r)   # validate before marking, so a rejected row stays pending
                r["Status"] = "designing"; r["Started"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save(path, rows, handle)
                print(json.dumps({"task_id": r["Task ID"], "request": request})); return
        print("NONE"); return
    if cmd == "mark":
        if len(sys.argv) < 5: sys.exit(__doc__)
        task, status, rest = sys.argv[3], sys.argv[4].lower(), sys.argv[5:]
        only_if = None
        if rest[:1] == ["--if"]:
            if len(rest) < 2: sys.exit("--if needs a status")
            only_if, rest = rest[1].lower(), rest[2:]
        result = " ".join(rest)
        for r in rows:
            if r["Task ID"] == task:
                if only_if is not None and (r["Status"].lower() or "pending") != only_if:
                    print(f"{task}: unchanged ({r['Status'] or 'pending'})"); return
                if r["Started"]:
                    r["Minutes"] = str(round((datetime.now() - datetime.strptime(r["Started"], "%Y-%m-%d %H:%M")).total_seconds() / 60))
                r["Status"] = status; r["Result"] = " ".join(result.split())[:1500]
                save(path, rows, handle); print(f"{task}: {status}"); return
        sys.exit(f"no row with Task ID {task}")
    if cmd == "request":
        for r in rows:
            if r["Task ID"] == sys.argv[3]:
                print(json.dumps({"task_id": r["Task ID"], "request": build_request(r)})); return
        sys.exit(f"no row with Task ID {sys.argv[3]}")
    if cmd == "list":
        want = sys.argv[3].lower()
        for r in rows:
            if filled(r) and (r["Status"].lower() or "pending") == want: print(r["Task ID"])
        return
    if cmd == "agent":
        side = path.with_name(path.name + ".agents.json")
        agents = json.loads(side.read_text()) if side.exists() else {}
        task = sys.argv[3]
        if len(sys.argv) > 4:
            agents[task] = sys.argv[4]
            tmp = side.with_name(side.name + ".saving"); tmp.write_text(json.dumps(agents, indent=1)); os.replace(tmp, side)
            print(f"{task}: recorded")
        else:
            if task not in agents: sys.exit(f"no session recorded for Task ID {task}")
            print(agents[task])
        return
    if cmd == "add":
        row = {c: "" for c in COLS}
        for pair in sys.argv[3:]:
            if "=" not in pair: sys.exit(f"expected Column=value, got {pair!r}")
            k, v = pair.split("=", 1); k = k.strip()
            if k not in INPUTS and k != "Topic": sys.exit(f"unknown column {k!r}")
            row[k] = field_value(v.strip())
        check_style(row["Style"])
        if not row["Task ID"] or not row["Brand number"]:
            sys.exit("a row needs Task ID and Brand number")
        if row["Output type"] not in OUTPUT_TYPES:
            sys.exit(f"Output type must be one of: {', '.join(sorted(OUTPUT_TYPES))}")
        check_duration(row)
        if any(r["Task ID"] == row["Task ID"] for r in rows): sys.exit(f"Task ID {row['Task ID']} already in this sheet")
        # draft: waiting for its script. A scriptless style has none to wait for.
        row["Status"] = "pending" if (row["Script"] or not needs_script(row)) else "draft"
        rows.append(row); save(path, rows, handle); print(f"{row['Task ID']}: added"); return
    if cmd == "set":
        task = sys.argv[3]
        for r in rows:
            if r["Task ID"] == task:
                if r["Status"].lower() not in {"", "draft", "pending"}:
                    sys.exit(f"{task} is {r['Status']}; only draft or pending rows can be changed")
                for pair in sys.argv[4:]:
                    if "=" not in pair: sys.exit(f"expected Column=value, got {pair!r}")
                    k, v = pair.split("=", 1); k = k.strip()
                    if k not in INPUTS and k != "Topic": sys.exit(f"unknown column {k!r}")
                    if k in {"Task ID", "Brand number"}: sys.exit(f"{k} comes from Vega's numbers tool and is never changed here")
                    r[k] = field_value(v.strip())
                check_style(r["Style"])
                if r["Output type"] not in OUTPUT_TYPES:
                    sys.exit(f"Output type must be one of: {', '.join(sorted(OUTPUT_TYPES))}")
                check_duration(r)
                if (r["Script"] or not needs_script(r)) and r["Status"].lower() in {"", "draft"}: r["Status"] = "pending"
                save(path, rows, handle); print(f"{task}: {r['Status']}"); return
        sys.exit(f"no row with Task ID {task}")
    if cmd == "remove":
        task = sys.argv[3]
        keep = [r for r in rows if r["Task ID"] != task]
        if len(keep) == len(rows): sys.exit(f"no row with Task ID {task}")
        save(path, keep, handle)
        side = path.with_name(path.name + ".agents.json")
        if side.exists():
            agents = json.loads(side.read_text()); agents.pop(task, None)
            tmp = side.with_name(side.name + ".saving"); tmp.write_text(json.dumps(agents, indent=1)); os.replace(tmp, side)
        print(f"{task}: removed"); return
    if cmd == "tally":
        # Vega's bookkeeping: finished rows counted by brand and output type, one JSON line
        out = {}
        for r in rows:
            if (r["Status"] or "").lower() == "done":
                b = out.setdefault(r.get("Brand") or "Brandless", {})
                t = r.get("Output type") or "unknown"
                b[t] = b.get(t, 0) + 1
        print(json.dumps(out)); return
    if cmd == "summary":
        counts, open_rows = {}, []
        for r in rows:
            if not filled(r): continue
            s = r["Status"].lower() or "pending"
            counts[s] = counts.get(s, 0) + 1
            if s != "done": open_rows.append(f"{r['Task ID']}: {s}")
        print(json.dumps(counts)); print("\n".join(open_rows)); return
    sys.exit(__doc__)

if __name__ == "__main__":
    main()
