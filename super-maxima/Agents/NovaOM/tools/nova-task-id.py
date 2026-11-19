#!/usr/bin/env python3
"""Nova's task numbers. Every video task gets two numbers from here:

  Task ID       system-wide; tracks the task across agents, sheets, and logs
  Brand number  per brand, with no gaps; it is the number in the video's file names

Numbers never restart when finished videos are backed up and removed from Project/.
Backing up never frees a number: only `release`, on a cancelled task, does.
A cancelled task's numbers are released and issued again, lowest first, so there are
no gaps. A redo keeps its numbers: it is the same task, built again from scratch.

  python3 "<max>/tools/nova-task-id.py" next <brand> [count]
      Issues the next Task ID + Brand number for that brand (or `count` of them).
      Prints one JSON line per task: {"task_id", "brand", "brand_number"}.
  python3 "<max>/tools/nova-task-id.py" release <task id>
      Cancelled task only (never a redo): frees its Task ID and Brand number.
  python3 "<max>/tools/nova-task-id.py" show <task id>
  python3 "<max>/tools/nova-task-id.py" rebrand <task id> <new brand>
      Moves a task to another brand (e.g. a test the owner makes official): keeps the
      Task ID, frees its old brand number, and gives it the new brand's next number.
      Prints that task's brand and Brand number.
  python3 "<max>/tools/nova-task-id.py" brand <brand>
      Prints the brand's last Brand number and any freed numbers waiting to be reused.

<brand> is the brand as written ("Glow Lab Co."); it is stored without spaces or
special characters ("GlowLabCo"), the same name as the brand's folder in Project/.
The register lives in docs/nova-task-register.json. Never edit it by hand, and
never count files in Project/ to find a number.
"""
import fcntl, json, os, re, sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[1] / "docs" / "nova-task-register.json"
EMPTY = {"last_task_id": 0, "free_task_ids": [], "brands": {}, "tasks": {}}

def brand_key(name):
    key = re.sub(r"[^A-Za-z0-9]", "", name or "")
    return key or "Brandless"

def pad(n): return f"{n:02d}"

def take(free, last):
    """Lowest freed number first; otherwise the next new one."""
    if free:
        free.sort(); return free.pop(0), last
    return last + 1, last + 1

TRACK = Path(__file__).resolve().parent / "track.py"   # the shared Base (2026-11-19)


def shared():
    """True when this machine uses the shared task tracker (agent.json "tracking", default "base")."""
    try: return json.loads((Path(__file__).resolve().parents[3] / "agent.json").read_text()).get("tracking", "base") != "local"
    except (OSError, ValueError): return True


def via_base(a):
    """next / release / show through the shared Base; extra flags (--type, --style, --sheet, --requester) pass through."""
    import subprocess
    if a[0] == "next":
        cmd = ["new", a[1]] + a[2:]
        if "--type" not in cmd: cmd += ["--type", "organic-video"]
    elif a[0] == "release": cmd = ["set", a[1], "Status=cancelled"]
    elif a[0] == "show": cmd = ["show", a[1]]
    else: sys.exit(f"{a[0]} is not used with the shared tracker (set it in the Base by hand if needed)")
    r = subprocess.run([sys.executable, str(TRACK), *cmd], capture_output=True, text=True)
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)


def main():
    if len(sys.argv) > 2 and sys.argv[1] in ("next", "release", "show", "rebrand", "brand") and shared():
        via_base(sys.argv[1:])
    for f in ("--type", "--style", "--sheet", "--requester"):   # only the shared Base uses these
        while f in sys.argv:
            i = sys.argv.index(f); del sys.argv[i:i + 2]
    if len(sys.argv) < 3: sys.exit(__doc__)
    cmd, arg = sys.argv[1], sys.argv[2]
    REGISTER.touch(exist_ok=True)
    with open(REGISTER, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)              # one writer at a time, across sessions
        raw = f.read().strip()
        reg = json.loads(raw) if raw else json.loads(json.dumps(EMPTY))
        out = []

        if cmd == "next":
            key = brand_key(arg)
            n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            if n < 1: sys.exit("count must be 1 or more")
            b = reg["brands"].setdefault(key, {"last": 0, "free": []})
            for _ in range(n):
                tid, reg["last_task_id"] = take(reg["free_task_ids"], reg["last_task_id"])
                bno, b["last"] = take(b["free"], b["last"])
                reg["tasks"][pad(tid)] = {"brand": key, "brand_number": pad(bno)}
                out.append({"task_id": pad(tid), "brand": key, "brand_number": pad(bno)})
        elif cmd == "release":
            tid = pad(int(arg))
            t = reg["tasks"].pop(tid, None)
            if t is None: sys.exit(f"no active task {tid}")
            reg["free_task_ids"].append(int(tid))
            reg["brands"][t["brand"]]["free"].append(int(t["brand_number"]))
            out.append({"released": tid, "brand": t["brand"], "brand_number": t["brand_number"]})
        elif cmd == "rebrand":
            if len(sys.argv) < 4: sys.exit(__doc__)
            tid = pad(int(arg)); key = brand_key(sys.argv[3])
            t = reg["tasks"].get(tid)
            if t is None: sys.exit(f"no active task {tid}")
            if t["brand"] == key: sys.exit(f"task {tid} is already {key}")
            reg["brands"][t["brand"]]["free"].append(int(t["brand_number"]))
            b = reg["brands"].setdefault(key, {"last": 0, "free": []})
            bno, b["last"] = take(b["free"], b["last"])
            out.append({"task_id": tid, "from": t["brand"], "from_number": t["brand_number"], "brand": key, "brand_number": pad(bno)})
            reg["tasks"][tid] = {"brand": key, "brand_number": pad(bno)}
        elif cmd == "show":
            tid = pad(int(arg))
            if tid not in reg["tasks"]: sys.exit(f"no active task {tid}")
            print(json.dumps({"task_id": tid, **reg["tasks"][tid]})); return
        elif cmd == "brand":
            key = brand_key(arg); b = reg["brands"].get(key, {"last": 0, "free": []})
            print(json.dumps({"brand": key, "last_brand_number": pad(b["last"]),
                              "freed": [pad(x) for x in sorted(b["free"])]})); return
        else:
            sys.exit(__doc__)

        f.seek(0); f.truncate(); f.write(json.dumps(reg, indent=1) + "\n"); f.flush(); os.fsync(f.fileno())
    for o in out: print(json.dumps(o))

if __name__ == "__main__":
    main()
