#!/usr/bin/env python3
"""Jani's backup tool. Copies Super Nova's Project folder to the backup drive, checks every
copied file against the original, writes the ledgers (on the drive, in Jani's docs, and in Nova's
data), and only then clears what was backed up from Project/ and from the designers' scratch.

Each backed-up video's designer sessions (the designers' full conversation logs, kept in Claude's
own data folder) are backed up with it, under "Designer sessions/<Brand>/<video>/", then cleared.

A carousel (any carousel designer, e.g. the Corporate Carousel Designer, 2026-10-27) is one set like a video: its folder
Project/<Brand>/carousels/<name>/ (slides, contact sheet, notes, slides.html, research, gen) and its
metadata Project/<Brand>/metadata/<name>.json, with its designer sessions, are backed up, checked and
cleared together. It is counted as a carousel, not a video.

Work made today is never touched: a video whose project was created today, and any other file or
folder changed today, is neither backed up nor cleared (it may be unfinished or get feedback).

  python3 "<jani>/tools/jani-backup.py" plan
      Looks, changes nothing. Prints one JSON line: the plan id, what would be backed up and
      cleared (videos per brand, other items, size), what is kept because it is from today, the
      drive's free space, and any blocker. The plan is saved for `run`.
  python3 "<jani>/tools/jani-backup.py" run --plan <plan id>
      Runs that plan, and only if nothing changed since it was made (same day, same files, same
      sizes): copy to "<drive>/<backup root>/Project <YYYY-MM-DD>/", check every file (size and
      SHA-256), write the ledgers, record the videos in Nova's data, then clear them from Project/
      and clear their designers' scratch. A file whose copy does not match is not cleared.
  python3 "<jani>/tools/jani-backup.py" status
      The drive, and the last runs.

Prints one JSON line per command.
"""
import hashlib, json, os, re, shutil, sys, time, uuid
from datetime import datetime, date
from pathlib import Path

JANI = Path(__file__).resolve().parents[1]
SUPER = JANI.parents[1]
PROJECT = SUPER / "Project"
AGENTS = SUPER / "Agents"
CONFIG = JANI / "docs" / "jani-config.json"
PLANS = JANI / "docs" / "plans"
RUNS = JANI / "docs" / "jani-runs.json"
MAX_RECORD = AGENTS / "NovaOM" / "docs" / "nova-backups.md"
BATCHES = AGENTS / "AtlasPM" / "batches"
SCRATCH_ROOT = Path("/tmp") / f"claude-{os.getuid()}" / re.sub(r"[^A-Za-z0-9]", "-", str(PROJECT))
SESSIONS_ROOT = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(PROJECT))
SKIP_NAMES = {".DS_Store"}
SETS = {"video", "carousel"}   # whole sets: backed up, checked and cleared together
EXFAT_BAD = re.compile(r'[:"*?<>|\\]')
CHUNK = 8 * 1024 * 1024


def out(d, code=0):
    print(json.dumps(d, ensure_ascii=False)); sys.exit(code)


def cfg():
    return json.loads(CONFIG.read_text())


def drive_mount(volume):
    """Where the backup drive is mounted on this Linux host. A directory that is not a mount point
    does not count, so nothing is ever written to the root disk by mistake; when the drive is not
    mounted the returned path does not exist."""
    user = Path.home().name
    for base in (Path("/mnt"), Path("/media"), Path("/media") / user, Path("/run/media") / user):
        p = base / volume
        if os.path.ismount(p):
            return p
    return Path("/mnt/.not-mounted") / volume


def drive_paths(c):
    vol = drive_mount(c["volume"])
    return vol, vol / c["backup_root"]


def today():
    return date.today()


def is_today(ts):
    return datetime.fromtimestamp(ts).date() == today()


def newest_mtime(p):
    if p.is_file():
        return p.stat().st_mtime
    m = p.stat().st_mtime
    for root, dirs, files in os.walk(p):
        for n in files:
            try: m = max(m, (Path(root) / n).stat().st_mtime)
            except OSError: pass
    return m


def size_of(p):
    if p.is_file():
        return p.stat().st_size
    return sum((Path(r) / n).stat().st_size for r, _, fs in os.walk(p) for n in fs if n not in SKIP_NAMES)


def files_in(p):
    if p.is_file():
        return [p]
    return sorted(Path(r) / n for r, _, fs in os.walk(p) for n in fs if n not in SKIP_NAMES)


# ---------------------------------------------------------------- what is in Project/
def videos_of(brand_dir):
    """Every video project (and carousel) in a brand folder: name -> {created, task_id, brand_number, kind}."""
    vids = {}
    md = brand_dir / "metadata"
    cd = brand_dir / "carousels"
    for f in sorted(md.glob("*.json")) if md.is_dir() else []:
        try: d = json.loads(f.read_text())
        except (OSError, ValueError): d = {}
        name = d.get("name") or f.stem
        kind = "carousel" if d.get("output_type") == "carousel" or (cd / name).is_dir() else "video"
        vids[name] = {"created": d.get("created"), "task_id": str(d.get("task_id") or ""),
                      "brand_number": str(d.get("brand_number") or ""), "kind": kind}
    for c in sorted(cd.iterdir()) if cd.is_dir() else []:
        if c.is_dir() and c.name not in vids:   # a carousel folder with no metadata: its creation time decides
            vids[c.name] = {"created": datetime.fromtimestamp(c.stat().st_birthtime).strftime("%Y-%m-%d"),
                            "task_id": "", "brand_number": "", "kind": "carousel"}
    ed = brand_dir / "editable"
    for h in sorted(ed.glob("*.html")) if ed.is_dir() else []:
        if h.stem not in vids:   # an editable with no metadata: its creation time decides
            vids[h.stem] = {"created": datetime.fromtimestamp(h.stat().st_birthtime).strftime("%Y-%m-%d"),
                            "task_id": "", "brand_number": "", "kind": "video"}
    for name, v in vids.items():
        if not v["created"]:
            h = ed / f"{name}.html"
            v["created"] = datetime.fromtimestamp(h.stat().st_birthtime).strftime("%Y-%m-%d") if h.exists() else None
    return vids


def owner_of(rel_parts, names):
    """Which video a path inside a brand folder belongs to (by its file or folder name)."""
    leaf = rel_parts[-1]
    for n in sorted(names, key=len, reverse=True):
        if leaf == n or leaf.startswith(n + ".") or leaf.startswith(n + "-") or leaf.startswith(n + "_"):
            return n
        if len(rel_parts) >= 3 and rel_parts[0] == "editable" and rel_parts[1] == "materials" and rel_parts[2] == n:
            return n
    return None


def sessions_for(task_id):
    """The designer session logs of a task (every designer that worked on it, redos included)."""
    if not task_id: return []
    files = []
    for a in sorted(agent_ids({task_id.lstrip("0")})):
        files += sorted(SESSIONS_ROOT.glob(f"*/subagents/agent-{a}.*"))
    return [f for f in files if f.is_file()]


def survey():
    """Top-level units to handle: whole video sets and other items, each kept or backed up."""
    units, kept = [], []
    for brand_dir in sorted(p for p in PROJECT.iterdir() if p.is_dir()):
        brand = brand_dir.name
        vids = videos_of(brand_dir)
        sets = {n: [] for n in vids}
        others = []
        # walk two levels deep: editable/, editable/materials/, renders/, renders/deletable/, metadata/, archive/,
        # carousels/ (each carousels/<name>/ belongs to its carousel's set, by its name)
        for top in sorted(brand_dir.iterdir()):
            if top.name in SKIP_NAMES: continue
            if top.is_file():
                others.append(top); continue
            for child in sorted(top.iterdir()):
                if child.name in SKIP_NAMES: continue
                if child.is_dir() and child.name in {"materials", "deletable"}:
                    for g in sorted(child.iterdir()):
                        if g.name in SKIP_NAMES: continue
                        o = owner_of(g.relative_to(brand_dir).parts, vids)
                        (sets[o] if o else others).append(g)
                    continue
                o = owner_of(child.relative_to(brand_dir).parts, vids)
                (sets[o] if o else others).append(child)
        for n, items in sets.items():
            if not items: continue
            v = vids[n]
            ses = sessions_for(v["task_id"])
            if any(is_today(f.stat().st_mtime) for f in ses): ses = []   # a designer worked on it today: its logs wait
            u = {"kind": v.get("kind", "video"), "brand": brand, "video": n, "created": v["created"], "task_id": v["task_id"],
                 "brand_number": v["brand_number"], "paths": [str(p.relative_to(PROJECT)) for p in items],
                 "sessions": [str(f) for f in ses],
                 "size": sum(size_of(p) for p in items) + sum(f.stat().st_size for f in ses)}
            (kept if v["created"] == today().isoformat() else units).append(u)
        for p in others:
            u = {"kind": "other", "brand": brand, "video": None, "paths": [str(p.relative_to(PROJECT))], "size": size_of(p)}
            (kept if is_today(newest_mtime(p)) else units).append(u)
    return units, kept


def fingerprint(units):
    """What the plan covers, to refuse a run when Project/ changed since the plan."""
    fp = []
    for u in units:
        for rel in u["paths"]:
            for f in files_in(PROJECT / rel):
                st = f.stat(); fp.append([str(f.relative_to(PROJECT)), st.st_size, int(st.st_mtime)])
        for sf in u.get("sessions", []):
            st = Path(sf).stat(); fp.append([sf, st.st_size, int(st.st_mtime)])
    return sorted(fp)


def blockers(c, need):
    b = []
    vol, root = drive_paths(c)
    if not vol.is_dir():
        b.append(f"backup drive '{c['volume']}' is not connected")
    else:
        free = shutil.disk_usage(vol).free
        if free < need * 1.05:
            b.append(f"not enough space on the drive: {free / 1e9:.1f} GB free, {need / 1e9:.1f} GB needed")
    return b


# ---------------------------------------------------------------- copy and check
def copy_checked(src, dst):
    """Copy one file, hashing it on the way; then read the copy back and compare. Returns sha256."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        while True:
            b = fi.read(CHUNK)
            if not b: break
            h.update(b); fo.write(b)
        fo.flush(); os.fsync(fo.fileno())
    os.utime(dst, (src.stat().st_atime, src.stat().st_mtime))   # keep the original's dates
    h2 = hashlib.sha256()
    with open(dst, "rb") as fo:
        while True:
            b = fo.read(CHUNK)
            if not b: break
            h2.update(b)
    if h.hexdigest() != h2.hexdigest() or dst.stat().st_size != src.stat().st_size:
        raise IOError("copy does not match the original")
    return h.hexdigest()


def backup_folder(root):
    base = root / f"Project {today().isoformat()}"
    k, d = 2, base
    while d.exists():
        d = root / f"Project {today().isoformat()} ({k})"; k += 1
    return d


# ---------------------------------------------------------------- ledgers
def write_ledgers(dest, units, results, plan_id, started):
    ok_units = [u for u in units if all(results.get(p, {}).get("ok") for p in u["paths"] + u.get("sessions", []))]
    total = sum(u["size"] for u in ok_units)
    ledger = {"plan": plan_id, "started": started, "finished": datetime.now().isoformat(timespec="seconds"),
              "source": str(PROJECT), "backup": str(dest), "size": total, "units": []}
    for u in units:
        ledger["units"].append(dict(u, files=[r for p in u["paths"] + u.get("sessions", [])
                                               for r in results.get(p, {}).get("files", [])],
                                    backed_up=u in ok_units))
    (dest / "jani-ledger.json").write_text(json.dumps(ledger, indent=1, ensure_ascii=False))
    lines = [f"# Backup {dest.name}", "",
             f"- Backed up: {ledger['finished']} by Jani (plan {plan_id})",
             f"- From: {PROJECT}",
             f"- Size: {total / 1e9:.2f} GB, {sum(len(x['files']) for x in ledger['units'] if x['backed_up'])} files",
             "- Every file was checked against the original (size and SHA-256); the checksums are in jani-ledger.json.",
             "- To restore a video: copy its paths below back into the Super Nova Project folder.",
             "- Designer sessions: each video's designer conversation logs, in `Designer sessions/<Brand>/<video>/`.", ""]
    for brand in sorted({u["brand"] for u in units}):
        bu = [u for u in ledger["units"] if u["brand"] == brand]
        lines += [f"## {brand}", "", "| Task ID | Brand no. | Video | Created | Files | Designer sessions | Size | Backed up |",
                  "|---|---|---|---|---|---|---|---|"]
        for u in [x for x in bu if x["kind"] in SETS]:
            ns = sum(1 for f in u.get("sessions", []) if f.endswith(".jsonl"))
            lines.append(f"| {u['task_id']} | {u['brand_number']} | {u['video']}{' (carousel)' if u['kind'] == 'carousel' else ''} | {u['created']} | {len(u['files'])} "
                         f"| {ns} | {u['size'] / 1e6:.0f} MB | {'yes' if u['backed_up'] else 'NO, copy failed'} |")
        oth = [x for x in bu if x["kind"] == "other"]
        if oth:
            lines += ["", "Other items:", ""] + [f"- `{x['paths'][0]}` ({x['size'] / 1e6:.1f} MB)"
                                                 + ("" if x["backed_up"] else " NOT backed up") for x in oth]
        lines.append("")
    (dest / "jani-ledger.md").write_text("\n".join(lines))
    return ok_units, total


def record_runs(dest, ok_units, total, plan_id):
    runs = json.loads(RUNS.read_text()) if RUNS.exists() else []
    runs.append({"date": datetime.now().isoformat(timespec="minutes"), "plan": plan_id, "backup": str(dest),
                 "videos": sum(1 for u in ok_units if u["kind"] == "video"),
                 "carousels": sum(1 for u in ok_units if u["kind"] == "carousel"), "size": total})
    RUNS.write_text(json.dumps(runs, indent=1))
    # the drive's own index of every backup
    idx = dest.parent / "jani-backups.md"
    if not idx.exists():
        idx.write_text("# Super Nova backups\n\n| Date | Folder | Videos | Size |\n|---|---|---|---|\n")
    with open(idx, "a") as f:
        f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | {dest.name} | {sum(1 for u in ok_units if u['kind'] == 'video')} "
                f"| {total / 1e9:.2f} GB |\n")


def record_max(dest, ok_units):
    """Nova's data: which videos are backed up, and where."""
    if not MAX_RECORD.exists():
        MAX_RECORD.write_text(
            "# Nova — Backups\n\nVideos backed up by Jani and cleared from Project/. Written only by Jani's tool.\n"
            "Their numbers stay used: a backed-up video's Task ID and Brand number are never issued again.\n\n"
            "| Backed up | Brand | Task ID | Brand no. | Video | Backup folder |\n|---|---|---|---|---|---|\n")
    with open(MAX_RECORD, "a") as f:
        for u in ok_units:
            if u["kind"] in SETS:
                f.write(f"| {datetime.now():%Y-%m-%d} | {u['brand']} | {u['task_id']} | {u['brand_number']} "
                        f"| {u['video']} | `{dest}` |\n")


# ---------------------------------------------------------------- clearing
def clear_units(ok_units, results):
    freed = 0
    for u in ok_units:
        for rel in u["paths"]:
            p = PROJECT / rel
            rec = {r["path"]: r for r in results[rel]["files"]}
            # never clear anything that changed after it was copied
            if any((PROJECT / r).stat().st_size != rec[r]["size"] or int((PROJECT / r).stat().st_mtime) != rec[r]["mtime"]
                   for r in rec if (PROJECT / r).exists()):
                continue
            freed += size_of(p)
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        for sf in u.get("sessions", []):      # the designer session logs, once their copy checked out
            f = Path(sf); rec = {r["path"]: r for r in results[sf]["files"]}
            if f.is_file() and f.stat().st_size == rec[sf]["size"] and int(f.stat().st_mtime) == rec[sf]["mtime"]:
                freed += f.stat().st_size; f.unlink()
    for brand_dir in PROJECT.iterdir():   # empty materials folders left behind
        mat = brand_dir / "editable" / "materials"
        if mat.is_dir():
            for d in mat.iterdir():
                if d.is_dir() and not any(d.iterdir()): d.rmdir()
    return freed


def agent_ids(task_ids):
    ids = set()
    for f in BATCHES.glob("*.agents.json"):
        try: d = json.loads(f.read_text())
        except (OSError, ValueError): continue
        for t, a in d.items():
            if t.lstrip("0") in task_ids and a: ids.add(a)
    return ids


def clear_scratch(ok_units):
    """The designers' scratch for the backed-up tasks: their session logs, and scratchpad files
    not changed today (scratch only holds throwaway intermediates of finished work)."""
    freed = 0
    if not SCRATCH_ROOT.is_dir(): return 0
    tids = {u["task_id"].lstrip("0") for u in ok_units if u["kind"] in SETS and u["task_id"]}
    ids = agent_ids(tids)
    for sess in SCRATCH_ROOT.iterdir():
        if not sess.is_dir(): continue
        for a in ids:
            f = sess / "tasks" / f"{a}.output"
            if f.is_symlink() or f.is_file():   # often only a link to the session log: count the link itself
                freed += f.lstat().st_size; f.unlink()
        sp = sess / "scratchpad"
        if sp.is_dir():
            for p in sp.iterdir():
                if not is_today(newest_mtime(p)):
                    freed += size_of(p); shutil.rmtree(p) if p.is_dir() else p.unlink()
    return freed


# ---------------------------------------------------------------- commands
def plan():
    c = cfg()
    units, kept = survey()
    need = sum(u["size"] for u in units)
    bad = [p for u in units for p in u["paths"] if EXFAT_BAD.search(p)]
    b = blockers(c, need) + ([f"names the drive cannot hold: {bad[:5]}"] if bad else [])
    pid = f"{datetime.now():%Y%m%d-%H%M}-{uuid.uuid4().hex[:4]}"
    PLANS.mkdir(parents=True, exist_ok=True)
    (PLANS / f"{pid}.json").write_text(json.dumps({"id": pid, "day": today().isoformat(), "units": units,
                                                   "kept": kept, "fingerprint": fingerprint(units)}, ensure_ascii=False))
    per_brand, car_brand = {}, {}
    for u in units:
        if u["kind"] == "video": per_brand[u["brand"]] = per_brand.get(u["brand"], 0) + 1
        if u["kind"] == "carousel": car_brand[u["brand"]] = car_brand.get(u["brand"], 0) + 1
    vol, _ = drive_paths(c)
    out({"plan": pid, "backup_and_clear": {"videos": sum(per_brand.values()), "per_brand": per_brand,
         "carousels": sum(car_brand.values()), "carousels_per_brand": car_brand,
         "other_items": sum(1 for u in units if u["kind"] == "other"),
         "designer_sessions": sum(1 for u in units for f in u.get("sessions", []) if f.endswith(".jsonl")),
         "size_gb": round(need / 1e9, 2)},
         "kept_today": {"videos": sum(1 for u in kept if u["kind"] == "video"),
                        "carousels": sum(1 for u in kept if u["kind"] == "carousel"),
                        "other_items": sum(1 for u in kept if u["kind"] == "other")},
         "drive": c["volume"], "drive_free_gb": round(shutil.disk_usage(vol).free / 1e9, 1) if vol.is_dir() else None,
         "blockers": b})


def run(pid):
    c = cfg()
    pf = PLANS / f"{pid}.json"
    if not pf.is_file(): out({"result": "FAILED", "reason": f"no plan {pid}: run plan first"}, 1)
    p = json.loads(pf.read_text())
    if p["day"] != today().isoformat():
        out({"result": "FAILED", "reason": "the plan is from another day: run plan again"}, 1)
    units, _ = survey()
    if [u["paths"] for u in units] != [u["paths"] for u in p["units"]] or fingerprint(units) != p["fingerprint"]:
        out({"result": "FAILED", "reason": "Project/ changed since the plan: run plan again"}, 1)
    b = blockers(c, sum(u["size"] for u in units))
    if b: out({"result": "FAILED", "reason": "; ".join(b)}, 1)
    _, root = drive_paths(c)
    dest = backup_folder(root); dest.mkdir(parents=True)
    started = datetime.now().isoformat(timespec="seconds")
    results = {}
    for u in units:
        for rel in u["paths"]:
            src = PROJECT / rel; files = []; ok = True
            for f in files_in(src):
                r = str(f.relative_to(PROJECT)); st = f.stat()
                try:
                    files.append({"path": r, "size": st.st_size, "mtime": int(st.st_mtime),
                                  "sha256": copy_checked(f, dest / r)})
                except (OSError, IOError) as e:
                    ok = False; files.append({"path": r, "error": str(e)[:200]})
            results[rel] = {"ok": ok, "files": files}
        for sf in u.get("sessions", []):
            f = Path(sf); st = f.stat()
            target = dest / "Designer sessions" / u["brand"] / u["video"] / f.name
            try:
                results[sf] = {"ok": True, "files": [{"path": sf, "backup": str(target.relative_to(dest)), "size": st.st_size,
                                                      "mtime": int(st.st_mtime), "sha256": copy_checked(f, target)}]}
            except (OSError, IOError) as e:
                results[sf] = {"ok": False, "files": [{"path": sf, "error": str(e)[:200]}]}
    ok_units, total = write_ledgers(dest, units, results, pid, started)
    record_runs(dest, ok_units, total, pid)
    record_max(dest, ok_units)
    freed = clear_units(ok_units, results)
    freed_scratch = clear_scratch(ok_units)
    pf.rename(pf.with_suffix(".done.json"))
    failed = len(units) - len(ok_units)
    out({"result": "BACKED UP", "backup": str(dest), "videos": sum(1 for u in ok_units if u["kind"] == "video"),
         "carousels": sum(1 for u in ok_units if u["kind"] == "carousel"),
         "other_items": sum(1 for u in ok_units if u["kind"] == "other"), "size_gb": round(total / 1e9, 2),
         "designer_sessions": sum(1 for u in ok_units for f in u.get("sessions", []) if f.endswith(".jsonl")),
         "cleared_project_and_sessions_gb": round(freed / 1e9, 2), "cleared_scratch_gb": round(freed_scratch / 1e9, 2),
         "not_backed_up": failed, "ledger": str(dest / "jani-ledger.md")}, 1 if failed else 0)


def status():
    c = cfg(); vol, root = drive_paths(c)
    runs = json.loads(RUNS.read_text()) if RUNS.exists() else []
    out({"drive": c["volume"], "connected": vol.is_dir(),
         "drive_free_gb": round(shutil.disk_usage(vol).free / 1e9, 1) if vol.is_dir() else None,
         "backup_root": str(root), "last_runs": runs[-3:]})


def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "plan": plan()
    elif a[0] == "run" and "--plan" in a and a.index("--plan") + 1 < len(a): run(a[a.index("--plan") + 1])
    elif a[0] == "status": status()
    else: sys.exit(__doc__)


if __name__ == "__main__":
    main()
