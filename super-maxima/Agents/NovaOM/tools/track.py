#!/usr/bin/env python3
"""The shared task tracker (the owner, 2026-11-19): one Lark Base table that every agent (Nova, Mario,
Mars, ...) writes to, one row per task. Task IDs come from the Base's auto-number, so two agents writing
at the same moment still get different IDs. Brand numbers are worked out from the Task IDs (a task's
brand number = how many tasks of that brand have a Task ID up to its own), so they never clash either.

  python3 track.py new <brand> [count] --type <output type> [--style <s>] [--requester <name>] [--sheet <path>]
      Claims count (default 1) new tasks for this machine's agent (agent.json). Prints one JSON line
      per task: {"task_id", "brand", "brand_number", "record_id"}.
  python3 track.py set <task id> <field>=<value> [...]
      Updates that task's row: Status (claimed, done, uploaded, failed, cancelled, test), Credits,
      Link, Note, Done date (YYYY-MM-DD; "today" works), Requester, Style, Sheet.
  python3 track.py show <task id>
  python3 track.py export
      Every row as one JSON array (for reports: Iris and the output counts).
  python3 track.py count [<brand>] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--agent <name>]
      Counts done and uploaded tasks (by Done date), per brand and per output type, for all agents.

Brands are stored without spaces or special characters ("Glow Lab Co." -> GlowLabCo), like Project/.
The Base's link and IDs are in docs/tracker.json (shared in git). lark-cli runs with this machine's
Lark profile (Lark connect/config.json).
"""
import json, re, subprocess, sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

OM = Path(__file__).resolve().parents[1]
SUPER = OM.parents[1]
TRACKER = json.loads((OM / "docs" / "tracker.json").read_text())
BASE, TABLE = TRACKER["base_token"], TRACKER["table_id"]
STATUSES = ("claimed", "done", "uploaded", "failed", "cancelled", "test")


def tracking_on():
    """The shared Base is used unless this machine's agent.json says "tracking": "local"."""
    try: return json.loads((SUPER / "agent.json").read_text()).get("tracking", "base") != "local"
    except (OSError, ValueError): return True


def agent_name():
    try: return json.loads((SUPER / "agent.json").read_text()).get("name") or "Nova"
    except (OSError, ValueError): return "Nova"


def lark(*args):
    try: c = json.loads((SUPER / "Lark connect" / "config.json").read_text())
    except (OSError, ValueError): c = {}
    exe = ["lark-cli"] + (["--profile", c["lark_profile"]] if c.get("lark_profile") else [])
    r = subprocess.run([*exe, "base", *args, "--as", "bot", "--base-token", BASE, "--table-id", TABLE],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
    out = r.stdout or r.stderr
    try: d = json.loads(out[out.index("{"):])
    except ValueError: sys.exit(f"tracker: lark-cli gave no JSON: {out[:300]}")
    if not d.get("ok"): sys.exit(f"tracker: {json.dumps(d.get('error', d))[:400]}")
    return d["data"]


def clean_brand(b):
    return re.sub(r"[^A-Za-z0-9]", "", b)


def rows():
    """Every row as {field name: value, "_rid": record id}."""
    out, offset = [], 0
    while True:
        d = lark("+record-list", "--format", "json", "--limit", "200", "--offset", str(offset))
        names = d["fields"]
        for rid, vals in zip(d["record_id_list"], d["data"]):
            r = {"_rid": rid}
            for n, v in zip(names, vals):
                r[n] = v[0] if isinstance(v, list) and len(v) == 1 else v
            out.append(r)
        if not d.get("has_more"): return out
        offset += 200


def tid(r):
    return int(re.sub(r"\D", "", str(r.get("Task ID") or "0")) or 0)


def find(task_id):
    for r in rows():
        if tid(r) == int(task_id): return r
    sys.exit(f"tracker: no Task ID {task_id}")


def new(brand, count, typ, style="", requester="", sheet=""):
    b = clean_brand(brand)
    now = datetime.now(ZoneInfo(TRACKER.get("time_zone", "Asia/Manila"))).strftime("%Y-%m-%d %H:%M:%S")   # the Base's zone
    recs = [{"Agent": agent_name(), "Brand": b, "Output type": typ, "Style": style, "Requester": requester,
             "Sheet": sheet, "Status": "claimed", "Created": now} for _ in range(count)]
    ids = lark("+record-batch-create", "--json", json.dumps({"create_records": recs}))["record_id_list"]
    allr = rows()
    mine = {r["_rid"]: r for r in allr if r["_rid"] in ids}
    same = sorted(tid(r) for r in allr if r.get("Brand") == b and r.get("Status") not in ("cancelled", "test"))
    upd = {}
    for rid in ids:
        t = tid(mine[rid]); n = same.index(t) + 1
        upd[rid] = {"Brand number": n}
        print(json.dumps({"task_id": str(t), "brand": b, "brand_number": f"{n:02d}", "record_id": rid}))
    lark("+record-batch-update", "--json", json.dumps({"update_records": upd}))


def set_fields(task_id, pairs):
    r = find(task_id); f = {}
    for p in pairs:
        k, _, v = p.partition("=")
        if k == "Status" and v not in STATUSES: sys.exit(f"tracker: Status must be one of {STATUSES}")
        if k in ("Credits", "Brand number"): v = float(v)
        if k == "Done date": v = (date.today().isoformat() if v == "today" else v) + " 00:00:00"
        f[k] = v
    lark("+record-batch-update", "--json", json.dumps({"update_records": {r["_rid"]: f}}))
    print(json.dumps({"task_id": str(task_id), "updated": list(f)}))


def count(brand=None, frm=None, to=None, agent=None):
    out = {}
    for r in rows():
        if r.get("Status") not in ("done", "uploaded"): continue
        if brand and r.get("Brand") != clean_brand(brand): continue
        if agent and r.get("Agent") != agent: continue
        d = str(r.get("Done date") or "")[:10]
        if frm and d < frm: continue
        if to and d > to: continue
        b = out.setdefault(r.get("Brand"), {})
        t = r.get("Output type") or "unknown"
        b[t] = b.get(t, 0) + 1
    print(json.dumps(out))


def opt(a, name, default=""):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    c = a[0]
    if c == "new" and len(a) >= 2:
        n = int(a[2]) if len(a) > 2 and a[2].isdigit() else 1
        if "--type" not in a: sys.exit("tracker: --type is required")
        new(a[1], n, opt(a, "--type"), opt(a, "--style"), opt(a, "--requester"), opt(a, "--sheet"))
    elif c == "set" and len(a) >= 3: set_fields(a[1], a[2:])
    elif c == "show" and len(a) == 2: print(json.dumps({k: v for k, v in find(a[1]).items()}, ensure_ascii=False))
    elif c == "export": print(json.dumps(rows(), ensure_ascii=False))
    elif c == "count":
        b = a[1] if len(a) > 1 and not a[1].startswith("--") else None
        count(b, opt(a, "--from") or None, opt(a, "--to") or None, opt(a, "--agent") or None)
    else: sys.exit(__doc__)


if __name__ == "__main__":
    main()
