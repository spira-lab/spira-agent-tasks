#!/usr/bin/env python3
"""The Lifestyle Story Carousel Designer's tool (installed 2026-11-03). One entry point for every step of a
lifestyle story carousel row, so the designer only ever runs `python3` (Atlas's approved commands have no
`bash`, no `cd` and no `$(...)`). Rey's scripts (scripts/) run from here, under the carousel's own Python
(~/.venvs/lifestyle-carousel: Playwright, Pillow, NumPy, OpenCV); without it, under this python3.

  python3 "<lsc>/tools/lsc.py" new "<Brand>" <Task ID> --brand-number <n> [--product "<name>"] [--website <url>]
          [--format feed|story] [--cap <credits>]
      Makes Project/<BrandName>/carousels/<TaskID>-<brandname>-<MM-DD>/ (gen/ work/ slides/ out/ deletable/)
      and its metadata Project/<BrandName>/metadata/<same name>.json, with the start time and the credit cap
      (150 unless --cap). On a resumed session it prints the existing ones (same Task ID).
  python3 "<lsc>/tools/lsc.py" client "<Brand>" ["<Product>"]
      The client in clients/CLIENTS.md for this brand / product (the product first, by name or alias).
      None: adds a row (brief status draft) and clients/<client>/used-ideas.md, prints "new": true.
  python3 "<lsc>/tools/lsc.py" ideas <client>
      The client's open bank ideas (count and IDs) and its last 5 used or reserved carousels.
  python3 "<lsc>/tools/lsc.py" reserve "<folder>" --client <c> --idea <ID> --kind <KIND> --pain "<pain type>"
          --persona "<group>" --setting "<specific place>" --hook "<filled hook>" [--round <n>]
      Reserves the idea for this build, under a lock (designers of one batch run at the same time). Refuses
      (exit 3) an idea already in the client's log for that round, a kind or pain type of the last 5
      carousels, a persona or place of the last 3. Updates the bank's status and CLIENTS.md's counts.
  python3 "<lsc>/tools/lsc.py" mark "<folder>" --client <c> --idea <ID> used|dropped [--why "<reason>"]
  python3 "<lsc>/tools/lsc.py" append angles|ledger|bank:<client>|sources:<client> "| cell | cell | ... |"
      Adds one table row under a lock: angles-log.md, references/ideas-ledger.md (the next G-ID is put in
      front), clients/<client>/ideas.md (the next <client>-NNN is put in front), clients/<client>/screens/sources.md.
  python3 "<lsc>/tools/lsc.py" job "<folder>" <model-id> <name> '<inputs-json>' [listed credits]
      One Spira job through Rey's scripts/job.py (submit once, poll the same ID) into <folder>/gen/<name>.<ext>.
      Then the job's real charge (`spira --json ai jobs status <jobId>` -> data.credits) goes into the
      metadata's "jobs" (listed price only when the job gives none: credits_source "price"). Refused (exit 4)
      when the credits already spent plus this job's listed price would pass the carousel's cap.
  python3 "<lsc>/tools/lsc.py" fetch "<folder>" <name>
      Picks up a job that job.py gave up polling (its gen/<name>.job.json), never a second paid job.
  python3 "<lsc>/tools/lsc.py" cap "<folder>" <credits>
      Raises the cap after Nova's ANSWER allows it (at most 500).
  python3 "<lsc>/tools/lsc.py" run "<folder>" grade|render_text|statusbar|screen_fit|screen_composite <args...>
      Runs that script of Rey's (0 credits). Every path argument must be inside the build folder or <lsc>/clients/.
  python3 "<lsc>/tools/lsc.py" py "<folder>" "<folder>/work/<script>.py" [args...]
      Runs a script you wrote in the build folder's work/ (a Playwright capture), under the carousel's Python.
  python3 "<lsc>/tools/lsc.py" export "<folder>" [--format feed|story]
      The newest version of each named slide PNG in slides/ -> out/slide-01.jpg ... (feed 1080x1350, story
      1080x1920) and out/contact.png. Older versions stay in slides/; nothing is deleted.
  python3 "<lsc>/tools/lsc.py" check "<folder>"
      Confirms the finished carousel, changes nothing. Prints {"ok", "slides", "total_credits", "problems"}.
  python3 "<lsc>/tools/lsc.py" finish "<folder>" [--title "<title>"]
      Writes the slides, totals and minutes since the start into the metadata.

<folder> is the build folder (absolute, or relative to the Super Nova folder), inside Project/<BrandName>/carousels/.
"""
import fcntl, json, os, re, subprocess, sys, time
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
LSC = TOOLS.parent
SCRIPTS = LSC / "scripts"
CLIENTS = LSC / "clients"
LEDGER_MD = CLIENTS / "CLIENTS.md"
ANGLES = LSC / "angles-log.md"
IDEAS_LEDGER = LSC / "references" / "ideas-ledger.md"
STATE_LOCK = LSC / "clients" / ".lsc.lock"          # one lock for every shared log of this designer
SUPER = LSC.parents[1]
PROJECT = SUPER / "Project"
VENV_PY = Path.home() / ".venvs" / "lifestyle-carousel" / "bin" / "python"
DEFAULT_CAP, MAX_CAP = 150, 500                   # the owner's rules, 2026-11-03
SIZES = {"feed": (1080, 1350), "story": (1080, 1920)}
RUNNABLE = {"grade", "render_text", "statusbar", "screen_fit", "screen_composite"}

# Run under the carousel's own Python when it is there (Playwright and OpenCV live in it).
if VENV_PY.is_file() and not os.environ.get("LSC_IN_VENV"):
    os.execve(str(VENV_PY), [str(VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]], {**os.environ, "LSC_IN_VENV": "1"})
PY = sys.executable


def key(b): return re.sub(r"[^A-Za-z0-9]", "", b or "")


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def say(d, code=0):
    print(json.dumps(d, ensure_ascii=False)); sys.exit(code)


def folder_of(arg):
    p = Path(arg).expanduser()
    p = (p if p.is_absolute() else SUPER / p).resolve()
    if not (p.is_relative_to(PROJECT) and p.parent.name == "carousels"):
        sys.exit(f"not a carousel build folder (Project/<BrandName>/carousels/<name>/): {p}")
    if not p.is_dir(): sys.exit(f"no build folder at {p}: run `new` first")
    return p


def meta_path(folder): return folder.parents[1] / "metadata" / f"{folder.name}.json"


class Locked:
    """An exclusive lock held while a shared file is read and written."""
    def __init__(self, path): self.path = path
    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.path, "a"); fcntl.flock(self.f, fcntl.LOCK_EX); return self
    def __exit__(self, *exc): fcntl.flock(self.f, fcntl.LOCK_UN); self.f.close()


class Meta:
    """The metadata file, read and written under a lock (two jobs may finish at once)."""
    def __init__(self, folder):
        self.path = meta_path(folder); self.lock = Locked(folder / ".metadata.lock")
    def __enter__(self):
        self.lock.__enter__()
        self.d = json.loads(self.path.read_text()) if self.path.is_file() else {}
        return self.d
    def __exit__(self, *exc):
        if exc[0] is None:
            tmp = self.path.with_name(self.path.stem + ".saving.json")
            tmp.write_text(json.dumps(self.d, indent=1, ensure_ascii=False) + "\n"); os.replace(tmp, self.path)
        self.lock.__exit__()


def total(jobs): return round(sum(j.get("credits") or 0 for j in jobs), 2)


def write_atomic(path, text):
    tmp = path.with_name("." + path.name + ".saving"); tmp.write_text(text, encoding="utf-8"); os.replace(tmp, path)


# ---------- markdown tables ----------
def cells(line): return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def table(path, first_col=None):
    """(header, rows as dicts, line index of each row) of the first table whose header starts with first_col."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    for i, l in enumerate(lines):
        if l.startswith("|") and (first_col is None or cells(l)[0].lower().startswith(first_col.lower())):
            hdr = cells(l); rows = []
            for j in range(i + 2, len(lines)):
                if not lines[j].startswith("|"): break
                c = cells(lines[j]); rows.append((dict(zip(hdr, c + [""] * (len(hdr) - len(c)))), j))
            return hdr, rows, lines
    return [], [], lines


def insert_row(path, row):
    """Put a row after the last table line of the file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    last = max((i for i, l in enumerate(lines) if l.startswith("|")), default=None)
    if last is None: sys.exit(f"no table in {path}")
    lines.insert(last + 1, row)
    write_atomic(path, "\n".join(lines) + "\n")


def norm_row(row, n_cols=None):
    row = row.strip()
    if not (row.startswith("|") and row.endswith("|")): sys.exit("a row is written as | cell | cell | ... |")
    if n_cols and len(cells(row)) != n_cols: sys.exit(f"the row has {len(cells(row))} cells; the table has {n_cols}")
    return row


# ---------- the carousel ----------
def new(a):
    if len(a) < 3 or "--brand-number" not in a: sys.exit(__doc__)
    brand, task = a[1], a[2].strip()
    if not task.isdigit(): sys.exit("the Task ID must be a number")
    fmt = (opt(a, "--format") or "feed").lower()
    if fmt not in SIZES: sys.exit("--format is feed or story")
    cap = int(opt(a, "--cap") or DEFAULT_CAP)
    if not 0 < cap <= MAX_CAP: sys.exit(f"the cap is 1 to {MAX_CAP} credits")
    bk = key(brand) or "Brandless"; root = PROJECT / bk
    for m in sorted((root / "metadata").glob(f"{task}-*.json")) if (root / "metadata").is_dir() else []:
        try: d = json.loads(m.read_text())
        except (OSError, ValueError): continue
        if d.get("output_type") == "carousel" and str(d.get("task_id")) == task and Path(d.get("folder", "")).is_dir():
            say({"folder": d["folder"], "metadata": str(m), "name": d["name"], "started": d.get("started"),
                 "format": d.get("format"), "credit_cap": d.get("credit_cap"), "resumed": True})
    now = datetime.now(); name = f"{task}-{bk.lower()}-{now:%m-%d}"
    folder = root / "carousels" / name
    for sub in ("gen", "work", "slides", "out", "deletable"): (folder / sub).mkdir(parents=True, exist_ok=True)
    (root / "metadata").mkdir(parents=True, exist_ok=True)
    with Meta(folder) as d:
        d.update({"root": str(root), "task_id": task, "brand_number": opt(a, "--brand-number"), "name": name,
                  "brand": bk, "output_type": "carousel", "style": "lifestyle story carousel",
                  "product": opt(a, "--product") or None, "website": opt(a, "--website") or None,
                  "format": fmt, "credit_cap": cap, "client": None, "idea": None,
                  "created": now.strftime("%Y-%m-%d"), "started": now.isoformat(timespec="seconds"),
                  "folder": str(folder), "out": [], "contact": str(folder / "out" / "contact.png"),
                  "notes": str(folder / "out" / "notes.md"), "report": str(folder / "report.md"),
                  "jobs": [], "total_credits": 0})
    say({"folder": str(folder), "metadata": str(meta_path(folder)), "name": name,
         "started": now.isoformat(timespec="seconds"), "format": fmt, "credit_cap": cap})


def client_cmd(a):
    if len(a) < 2: sys.exit(__doc__)
    brand, product = a[1], (a[2] if len(a) > 2 else "")
    with Locked(STATE_LOCK):
        hdr, rows, _ = table(LEDGER_MD, "Client")
        def names(r):
            out = {key(r.get("Client")).lower()}
            out |= {key(x).lower() for x in re.split(r",", r.get("Aliases") or "") if key(x)}
            return out
        for want in [w for w in (product, brand) if key(w)]:
            for r, _ in rows:
                if key(want).lower() in names(r):
                    slug = re.search(r"\]\(([^/)]+)/", r.get("Brief") or "")
                    slug = slug.group(1) if slug else key(r["Client"]).lower()
                    cdir = CLIENTS / slug
                    say({"client": slug, "name": r["Client"], "dir": str(cdir), "new": False,
                         "brief": str(cdir / "BRIEF.md") if (cdir / "BRIEF.md").is_file() else None,
                         "brief_status": r.get("Brief status"), "matched": want})
        # not in the ledger: a row, a folder and an empty used-log; the designer drafts the brief
        label = product or brand; slug = key(label).lower()
        if not slug: sys.exit("no brand or product name")
        cdir = CLIENTS / slug; cdir.mkdir(parents=True, exist_ok=True)
        if not (cdir / "used-ideas.md").is_file():
            (cdir / "used-ideas.md").write_text(USED_TEMPLATE.format(client=label), encoding="utf-8")
        # a product's client never takes the bare brand name as an alias: the brand's other products are other clients
        both = f"{brand} {product}".lower() if product and not product.lower().startswith(brand.lower()) else ""
        aliases = ", ".join(dict.fromkeys(x for x in (label.lower(), both) if x))
        insert_row(LEDGER_MD, f"| {label} | {aliases} | _to be researched_ | _to be researched_ | _to be researched_ | "
                              f"[BRIEF]({slug}/BRIEF.md) | draft | 0 | 0 / 100 |")
        say({"client": slug, "name": label, "dir": str(cdir), "new": True, "brief": None, "brief_status": "draft"})


USED_TEMPLATE = """# {client}: ideas used
| Idea ID (bank or ledger) | Round | Status | Kind | Pain type | Persona | Setting | Filled hook | Build | Date |
|---|---|---|---|---|---|---|---|---|---|
"""
BANK_TEMPLATE = """# {client}: idea bank
| ID | Status | Kind | Hook | Persona group | Pain (their words) | Source | Feature that answers it | Place seed | Format | Added |
|---|---|---|---|---|---|---|---|---|---|---|
"""
SOURCES_TEMPLATE = """# {client} screens: sources

| file | URL | date captured | device and size | what it shows | signed out? |
|---|---|---|---|---|---|
"""


def client_dir(c):
    d = CLIENTS / c.strip().lower()
    if not c.strip() or not d.is_dir() or d.parent != CLIENTS: sys.exit(f"no client folder clients/{c}/ (run `client` first)")
    return d


def used_rows(cdir):
    p = cdir / "used-ideas.md"
    if not p.is_file(): p.write_text(USED_TEMPLATE.format(client=cdir.name), encoding="utf-8")
    hdr, rows, _ = table(p, None)
    return p, hdr, [r for r, _ in rows]


def col(r, *names):
    for n in names:
        for k, v in r.items():
            if k.lower().startswith(n.lower()): return v
    return ""


def ideas_cmd(a):
    if len(a) < 2: sys.exit(__doc__)
    cdir = client_dir(a[1])
    _, hdr, used = used_rows(cdir)
    _, bank, _ = table(cdir / "ideas.md", "ID")
    open_ids = [r.get("ID") for r, _ in bank if (r.get("Status") or "").lower() == "open"]
    live = [r for r in used if (col(r, "Status") or "").lower() in ("used", "reserved")]
    say({"client": cdir.name, "bank_open": len(open_ids), "bank_open_ids": open_ids, "bank_total": len(bank),
         "last_5": [{"idea": col(r, "Idea ID", "Ledger ID"), "status": col(r, "Status"), "kind": col(r, "Kind"),
                     "pain": col(r, "Pain type"), "persona": col(r, "Persona"), "setting": col(r, "Setting"),
                     "hook": col(r, "Filled hook")} for r in live[-5:]],
         "logged_ids": sorted({col(r, "Idea ID", "Ledger ID") for r in used})})


def words(s): return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def persona_clash(new, old):
    """The broad group: 'engineer' clashes with 'young engineer, olive overshirt'."""
    n, o = words(new), words(old)
    return bool(n) and (n <= o or (bool(o) and o <= n))


def set_bank_status(cdir, idea, status):
    p = cdir / "ideas.md"
    if not p.is_file(): return False
    hdr, rows, lines = table(p, "ID")
    for r, j in rows:
        if r.get("ID", "").lower() == idea.lower():
            c = cells(lines[j]); c[hdr.index("Status")] = status
            lines[j] = "| " + " | ".join(c) + " |"; write_atomic(p, "\n".join(lines) + "\n"); return True
    return False


def refresh_counts(cdir):
    """CLIENTS.md's 'Carousels made' and 'Ideas used (round)' for this client, from its used-log."""
    _, _, used = used_rows(cdir)
    st = [(col(r, "Status") or "").lower() for r in used]
    made, res = st.count("used"), st.count("reserved")
    rnd = max([int(x) for x in (col(r, "Round") for r in used) if str(x).isdigit()] or [1])
    hdr, rows, lines = table(LEDGER_MD, "Client")
    for r, j in rows:
        if re.search(rf"\]\({re.escape(cdir.name)}/", r.get("Brief") or "") or key(r.get("Client")).lower() == cdir.name:
            c = cells(lines[j]) + [""] * len(hdr)
            c[hdr.index("Carousels made")] = f"{made}" + (f" + {res} reserved" if res else "")
            c[hdr.index("Ideas used (round)")] = f"{made} / 100 (" + (f"{res} reserved, " if res else "") + f"round {rnd})"
            lines[j] = "| " + " | ".join(c[:len(hdr)]) + " |"
            write_atomic(LEDGER_MD, "\n".join(lines) + "\n"); return


def reserve(folder, a):
    need = ["--client", "--idea", "--kind", "--pain", "--persona", "--setting", "--hook"]
    miss = [n for n in need if not opt(a, n)]
    if miss: sys.exit("reserve needs " + ", ".join(miss))
    cdir = client_dir(opt(a, "--client")); idea = opt(a, "--idea").strip(); rnd = str(opt(a, "--round") or 1)
    kind, pain = opt(a, "--kind").strip().upper(), opt(a, "--pain").strip().lower()
    persona, setting = opt(a, "--persona").strip(), opt(a, "--setting").strip()
    with Locked(STATE_LOCK):
        p, hdr, used = used_rows(cdir)
        mine = [r for r in used if col(r, "Build") == folder.name and (col(r, "Status") or "").lower() == "reserved"]
        if mine: say({"reserved": False, "why": f"this build already reserved {col(mine[0], 'Idea ID', 'Ledger ID')}"}, 3)
        why = []
        if any(col(r, "Idea ID", "Ledger ID").lower() == idea.lower() and (col(r, "Round") or "1") == rnd for r in used):
            why.append(f"{idea} is already in the log for round {rnd}")
        live = [r for r in used if (col(r, "Status") or "").lower() in ("used", "reserved")]
        for r in live[-5:]:
            if col(r, "Kind").upper() == kind: why.append(f"kind {kind} is in the last 5 ({col(r, 'Idea ID', 'Ledger ID')})")
            if col(r, "Pain type").lower() == pain: why.append(f"pain type {pain!r} is in the last 5 ({col(r, 'Idea ID', 'Ledger ID')})")
        for r in live[-3:]:
            if persona_clash(persona, col(r, "Persona")): why.append(f"persona {persona!r} is in the last 3 ({col(r, 'Persona')})")
            if words(setting) and words(setting) == words(col(r, "Setting")): why.append(f"place {setting!r} is in the last 3")
        if why: say({"reserved": False, "why": why}, 3)
        cellv = lambda s: (s or "").replace("|", "/").strip()
        row = [idea, rnd, "reserved", kind, pain, persona, setting, opt(a, "--hook"), folder.name, datetime.now().strftime("%Y-%m-%d")]
        insert_row(p, "| " + " | ".join(cellv(x) for x in row[:len(hdr)]) + " |")
        set_bank_status(cdir, idea, "reserved"); refresh_counts(cdir)
    with Meta(folder) as d:
        d["client"] = cdir.name; d["idea"] = {"id": idea, "round": int(rnd), "kind": kind, "pain_type": pain,
                                              "persona": persona, "setting": setting, "hook": opt(a, "--hook")}
    say({"reserved": True, "client": cdir.name, "idea": idea, "round": int(rnd)})


def mark(folder, a):
    status = next((x for x in a if x in ("used", "dropped")), None)
    if not status or not opt(a, "--client") or not opt(a, "--idea"): sys.exit(__doc__)
    cdir = client_dir(opt(a, "--client")); idea = opt(a, "--idea").strip()
    with Locked(STATE_LOCK):
        p = cdir / "used-ideas.md"
        hdr, rows, lines = table(p, None)
        hit = [(r, j) for r, j in rows if col(r, "Idea ID", "Ledger ID").lower() == idea.lower() and col(r, "Build") == folder.name]
        if not hit: sys.exit(f"{idea} is not reserved by {folder.name} in {p}")
        r, j = hit[-1]; c = cells(lines[j]) + [""] * len(hdr)
        si = next(i for i, h in enumerate(hdr) if h.lower().startswith("status"))
        c[si] = status if status == "used" else f"dropped ({(opt(a, '--why') or 'no reason given').replace('|', '/')})"
        lines[j] = "| " + " | ".join(c[:len(hdr)]) + " |"; write_atomic(p, "\n".join(lines) + "\n")
        set_bank_status(cdir, idea, status); refresh_counts(cdir)
    say({"client": cdir.name, "idea": idea, "status": status})


def append(a):
    if len(a) < 3: sys.exit(__doc__)
    target, row = a[1], a[2]
    with Locked(STATE_LOCK):
        if target == "angles":
            hdr, _, _ = table(ANGLES, "Carousel"); insert_row(ANGLES, norm_row(row, len(hdr))); say({"added": "angles-log.md"})
        if target == "ledger":
            hdr, rows, _ = table(IDEAS_LEDGER, "ID")
            n = max([int(m.group(1)) for r, _ in rows for m in [re.match(r"G(\d+)$", r.get("ID", ""))] if m] or [100]) + 1
            gid = f"G{n:03d}"
            insert_row(IDEAS_LEDGER, norm_row(f"| {gid} " + norm_row(row, len(hdr) - 1), len(hdr))); say({"added": gid})
        kind, _, c = target.partition(":")
        if kind == "bank" and c:
            cdir = client_dir(c); p = cdir / "ideas.md"
            if not p.is_file(): p.write_text(BANK_TEMPLATE.format(client=cdir.name), encoding="utf-8")
            hdr, rows, _ = table(p, "ID")
            n = max([int(m.group(1)) for r, _ in rows for m in [re.search(r"-(\d+)$", r.get("ID", ""))] if m] or [0]) + 1
            bid = f"{cdir.name}-{n:03d}"
            insert_row(p, norm_row(f"| {bid} " + norm_row(row, len(hdr) - 1), len(hdr))); say({"added": bid})
        if kind == "sources" and c:
            cdir = client_dir(c); p = cdir / "screens" / "sources.md"; p.parent.mkdir(exist_ok=True)
            if not p.is_file(): p.write_text(SOURCES_TEMPLATE.format(client=cdir.name), encoding="utf-8")
            insert_row(p, norm_row(row)); say({"added": str(p)})
    sys.exit(__doc__)


# ---------- Spira jobs ----------
def spira_json(*args):
    r = subprocess.run(["spira", "--json", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try: return json.loads(r.stdout)
    except ValueError:
        m = re.search(r"\{.*\}", r.stdout or "", re.S)
        try: return json.loads(m.group(0)) if m else {}
        except ValueError: return {}


def job_credits(job_id):
    for attempt in range(2):
        d = (spira_json("ai", "jobs", "status", job_id).get("data") or {})
        for k in ("credits", "creditsCharged", "chargedCredits", "cost", "creditCost"):
            if isinstance(d.get(k), (int, float)): return float(d[k]), "job"
        if attempt == 0: time.sleep(5)
    return None, "missing"


def record(folder, name, listed, ok, out_file=None, note=None):
    side = folder / "gen" / f"{name}.job.json"
    info = json.loads(side.read_text()) if side.is_file() else {}
    jid = info.get("jobId")
    credits, source = job_credits(jid) if jid else (0, "no job was created")
    if credits is None and listed is not None: credits, source = float(listed), "price"
    res = folder / "gen" / f"{name}.json"
    url = json.loads(res.read_text()).get("source_url") if res.is_file() else None
    rec = {"name": name, "jobId": jid, "model": info.get("model"), "resultUrl": url, "credits": credits,
           "credits_source": source, "listed_credits": listed, "file": str(out_file) if out_file else None,
           "status": "succeeded" if ok else "failed", "prompt": (info.get("inputs") or {}).get("prompt"),
           "inputs": info.get("inputs"), "created": datetime.now().isoformat(timespec="seconds")}
    if note: rec["note"] = note
    with open(folder / "jobs.jsonl", "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with Meta(folder) as d:
        jobs = d.setdefault("jobs", [])
        jobs[:] = [j for j in jobs if not (j.get("jobId") and j.get("jobId") == jid)] + [rec]
        d["total_credits"] = total(jobs); tc = d["total_credits"]
    return rec, tc


def job(folder, a):
    if len(a) < 5: sys.exit(__doc__)
    model, name, inputs = a[2], a[3], a[4]
    listed = float(a[5]) if len(a) > 5 and re.fullmatch(r"\d+(\.\d+)?", a[5]) else None
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name): sys.exit("the name is letters, digits, dot, dash, underscore (no folder)")
    try: json.loads(inputs)
    except ValueError as e: sys.exit(f"the inputs are not JSON: {e}")
    if (folder / "gen" / f"{name}.job.json").exists():
        sys.exit(f"gen/{name} already has a job: use `fetch` to pick it up, or another name for a re-roll")
    d = json.loads(meta_path(folder).read_text())
    cap, spent = d.get("credit_cap") or DEFAULT_CAP, total(d.get("jobs", []))
    if spent + (listed or 0) > cap:
        say({"refused": True, "why": f"{spent} credits spent + {listed} listed would pass the cap of {cap}",
             "total_credits": spent, "credit_cap": cap}, 4)
    out = folder / "gen" / name
    r = subprocess.run([PY, str(SCRIPTS / "job.py"), model, str(out), inputs] + ([a[5]] if listed is not None else []),
                       text=True, capture_output=True, cwd=str(SCRIPTS), stdin=subprocess.DEVNULL)
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr)
    files = sorted(p for p in (folder / "gen").glob(f"{name}.*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
    still = "still running" in (r.stderr or "")
    rec, tc = record(folder, name, listed, r.returncode == 0 and bool(files), files[0] if files else None,
                     note="polling gave up: run `fetch`" if still else None)
    print(json.dumps({"job": rec["jobId"], "status": rec["status"], "file": rec["file"], "url": rec["resultUrl"],
                      "credits": rec["credits"], "total_credits": tc}))
    sys.exit(r.returncode)


def fetch(folder, a):
    if len(a) < 3: sys.exit(__doc__)
    name = a[2]; side = folder / "gen" / f"{name}.job.json"
    if not side.is_file(): sys.exit(f"no gen/{name}.job.json")
    info = json.loads(side.read_text()); jid = info["jobId"]; start = time.time()
    prev = json.loads(meta_path(folder).read_text()).get("jobs", [])
    listed = next((j.get("listed_credits") for j in prev if j.get("jobId") == jid), None)
    while True:
        d = spira_json("ai", "jobs", "status", jid).get("data") or {}
        st = str(d.get("status") or "").upper()
        if st in ("SUCCEEDED", "COMPLETED", "SUCCESS", "DONE"): break
        if st in ("FAILED", "CANCELLED", "CANCELED"):
            rec, tc = record(folder, name, listed, False); say({"job": jid, "status": "failed", "total_credits": tc}, 1)
        if time.time() - start > 3600: say({"job": jid, "status": "still running after 60 min"}, 1)
        time.sleep(10)
    text = json.dumps(d)
    urls = [u for u in re.findall(r'https://[^"\s]+?\.(?:png|jpg|jpeg|webp)(?:\?[^"\s]*)?', text) if "/uploads/" not in u]
    if not urls: sys.exit("the job succeeded but has no result URL")
    ext = urls[0].split("?")[0].rsplit(".", 1)[-1]
    import urllib.request
    req = urllib.request.Request(urls[0], headers={"User-Agent": "Mozilla/5.0"})   # the CDN 403s without it
    out = folder / "gen" / f"{name}.{ext}"; out.write_bytes(urllib.request.urlopen(req).read())
    (folder / "gen" / f"{name}.json").write_text(json.dumps({"model": info.get("model"), "provider": "spira-cli", "jobId": jid,
        "inputs": info.get("inputs"), "source_url": urls[0], "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=1))
    rec, tc = record(folder, name, listed, True, out)
    say({"job": jid, "status": "succeeded", "file": str(out), "url": urls[0], "credits": rec["credits"], "total_credits": tc})


def cap_cmd(folder, a):
    if len(a) < 3 or not a[2].isdigit(): sys.exit(__doc__)
    n = int(a[2])
    if not 0 < n <= MAX_CAP: sys.exit(f"the cap is at most {MAX_CAP} credits: over that, always QUESTION")
    with Meta(folder) as d: d["credit_cap"] = n
    say({"credit_cap": n})


# ---------- local scripts (0 credits) ----------
def run(folder, a):
    if len(a) < 3 or a[2] not in RUNNABLE: sys.exit(f"run takes one of: {', '.join(sorted(RUNNABLE))}")
    for x in a[3:]:
        if "/" in x:
            p = Path(x).expanduser().resolve()
            if not (p.is_relative_to(folder) or p.is_relative_to(CLIENTS) or p.is_relative_to(LSC / "references")):
                sys.exit(f"{p} is outside the build folder and {CLIENTS}")
    r = subprocess.run([PY, "-I", str(SCRIPTS / f"{a[2]}.py"), *a[3:]], cwd=str(folder), stdin=subprocess.DEVNULL)
    sys.exit(r.returncode)


def py(folder, a):
    if len(a) < 3: sys.exit(__doc__)
    s = Path(a[2]).expanduser().resolve()
    if not (s.is_relative_to(folder / "work") and s.suffix == ".py" and s.is_file()):
        sys.exit(f"the script must be a .py file in {folder / 'work'}")
    r = subprocess.run([PY, "-I", str(s), *a[3:]], cwd=str(folder / "work"), stdin=subprocess.DEVNULL)
    sys.exit(r.returncode)


# ---------- out/ ----------
def named_slides(folder):
    """{slide number: newest version's PNG} from slides/ (render_text.py's '... - Slide NN - <Maker> - vN.png')."""
    best = {}
    for p in (folder / "slides").glob("*.png"):
        m = re.search(r"Slide (\d+)\b.*?v(\d+)\.png$", p.name)
        if not m: continue
        n, v = int(m.group(1)), int(m.group(2))
        if n not in best or v > best[n][0] or (v == best[n][0] and p.stat().st_mtime > best[n][1].stat().st_mtime):
            best[n] = (v, p)
    return {n: p for n, (v, p) in sorted(best.items())}


def fit(im, size):
    from PIL import Image
    W, H = size; w, h = im.size; s = max(W / w, H / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS); w, h = im.size
    return im.crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))


def export(folder, a):
    from PIL import Image
    fmt = (opt(a, "--format") or "").lower()
    with Meta(folder) as d:
        if fmt:
            if fmt not in SIZES: sys.exit("--format is feed or story")
            d["format"] = fmt
        fmt = d.get("format") or "feed"
    size = SIZES[fmt]; sl = named_slides(folder)
    if not sl: sys.exit("no named slide PNGs in slides/ (render_text.py writes them)")
    if list(sl) != list(range(1, len(sl) + 1)): sys.exit(f"slides are not numbered 01..{len(sl):02d}: {list(sl)}")
    out = folder / "out"; out.mkdir(exist_ok=True)
    for old in out.glob("slide-*.jpg"):
        if int(re.sub(r"\D", "", old.stem) or 0) > len(sl):     # a slide dropped since the last export
            (folder / "deletable").mkdir(exist_ok=True); os.replace(old, folder / "deletable" / f"{datetime.now():%H%M%S}-{old.name}")
    files = []
    for n, p in sl.items():
        im = Image.open(p).convert("RGB")
        if im.size != size: im = fit(im, size)
        f = out / f"slide-{n:02d}.jpg"; im.save(f, quality=92, subsampling=0); files.append(f)
    tw = 540 if fmt == "feed" else 405; th = round(tw * size[1] / size[0])
    cols = len(files) if len(files) <= 4 else (4 if len(files) <= 8 else 5); rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 10) + 10, rows * (th + 10) + 10), "#888")
    for i, f in enumerate(files):
        sheet.paste(Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS), (10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 10)))
    sheet.save(out / "contact.png")
    say({"format": fmt, "size": f"{size[0]}x{size[1]}", "slides": len(files), "out": str(out), "contact": str(out / "contact.png"),
         "from": [p.name for p in sl.values()]})


def slides_in(folder): return sorted((folder / "out").glob("slide-*.jpg"), key=lambda f: int(re.sub(r"\D", "", f.stem) or 0))


def check(folder):
    from PIL import Image
    problems = []
    mp = meta_path(folder); d = json.loads(mp.read_text()) if mp.is_file() else {}
    if not d: problems.append("no metadata")
    size = SIZES.get(d.get("format") or "feed", SIZES["feed"])
    sl = slides_in(folder)
    if not 5 <= len(sl) <= 10: problems.append(f"{len(sl)} slides (5 to 10 expected)")
    nums = [int(re.sub(r"\D", "", s.stem)) for s in sl]
    if nums != list(range(1, len(sl) + 1)): problems.append(f"slides not numbered 01..{len(sl):02d}: {[s.name for s in sl]}")
    for s in sl:
        try:
            with Image.open(s) as im:
                if im.size != size: problems.append(f"{s.name} is {im.size[0]}x{im.size[1]}, not {size[0]}x{size[1]}")
        except OSError as e: problems.append(f"{s.name} unreadable: {e}")
    if not (folder / "out" / "contact.png").is_file(): problems.append("no out/contact.png")
    notes = folder / "out" / "notes.md"
    if not notes.is_file(): problems.append("no out/notes.md")
    else:
        t = notes.read_text(encoding="utf-8"); m = re.search(r"^## Captions\s*\n(.*?)(?=^## |\Z)", t, re.S | re.M)
        if not m or len(m.group(1).strip()) < 40: problems.append("out/notes.md has no ## Captions section with the captions")
        elif not re.search(r"linkedin", m.group(1), re.I): problems.append("out/notes.md's captions have no LinkedIn caption")
    for f in ("research.md", "copy.md", "prompts.md", "report.md"):
        if not (folder / f).is_file(): problems.append(f"no {f}")
    if d and not d.get("idea"): problems.append("no idea reserved in the metadata (lsc.py reserve)")
    if d and any(j.get("credits") is None for j in d.get("jobs", [])): problems.append("a job has no credits recorded")
    tc = total(d.get("jobs", []))
    res = {"ok": not problems, "folder": str(folder), "format": d.get("format"), "slides": len(sl), "total_credits": tc,
           "credit_cap": d.get("credit_cap"), "problems": problems}
    if d.get("credit_cap") and tc > d["credit_cap"]: res["note"] = f"spent {tc}, over the cap of {d['credit_cap']}: say why in report.md"
    return res


def finish(folder, a):
    with Meta(folder) as d:
        d["out"] = [str(s) for s in slides_in(folder)]; d["slides"] = len(d["out"])
        d["total_credits"] = total(d.get("jobs", []))
        if opt(a, "--title"): d["title"] = opt(a, "--title")
        now = datetime.now(); d["finished"] = now.isoformat(timespec="seconds")
        try: d["minutes"] = round((now - datetime.fromisoformat(d["started"])).total_seconds() / 60)
        except (KeyError, ValueError): d["minutes"] = None
        res = {"folder": str(folder), "slides": d["slides"], "total_credits": d["total_credits"], "minutes": d["minutes"]}
    say(res)


def report(folder, a):
    # The Write tool refuses report files from subagents (Task 184, 2026-11-03), so the report goes in through here:
    # lsc.py report <folder> <<'EOF' ... EOF  (or --file <path> to copy a draft written under another name)
    src = opt(a, "--file")
    text = Path(src).read_text(encoding="utf-8") if src else sys.stdin.read()
    if len(text.strip()) < 40: say({"ok": False, "error": "report text is empty or too short"}, 1)
    write_atomic(folder / "report.md", text if text.endswith("\n") else text + "\n")
    say({"ok": True, "report": str(folder / "report.md"), "chars": len(text)})


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"): print(__doc__); sys.exit(0 if a else 2)
    cmd = a[0]
    if cmd == "new": return new(a)
    if cmd == "client": return client_cmd(a)
    if cmd == "ideas": return ideas_cmd(a)
    if cmd == "append": return append(a)
    if len(a) < 2: sys.exit(__doc__)
    folder = folder_of(a[1])
    cmds = {"reserve": reserve, "mark": mark, "job": job, "fetch": fetch, "cap": cap_cmd, "run": run, "py": py,
            "export": export, "finish": finish, "report": report}
    if cmd in cmds: return cmds[cmd](folder, a)
    if cmd == "check":
        res = check(folder); say(res, 0 if res["ok"] else 1)
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
