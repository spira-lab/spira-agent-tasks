#!/usr/bin/env python3
"""Run a render inside one of the machine's render slots, so parallel designers never run more
renders at once than the machine can take (the owner's decision, 2026-11-13: 4 at a time,
"rendering" in Agents/AtlasPM/docs/atlas-limits.json).

  python3 "<shared>/tools/heavy-slot.py" <Task ID> -- <command> [args ...]

Waits for a free slot (checking every 5 seconds, at most 300), runs the command, and exits with
its exit code. With no slot free after 300 seconds it exits 75 without running anything: run the
same line again. Set the Bash timeout to 600000 for it.

A slot is a lock on <super>/.locks/render-slot-<n>.lock, held by this process: it is freed when
the command ends, also when it crashes or the machine restarts, so a slot is never left taken.
<super>/.locks/render-slot-<n>.who says who holds it (atlas-sheet.py slots shows it).
"""
import fcntl, json, os, signal, subprocess, sys, time
from datetime import datetime
from pathlib import Path

# <super>/Agents/DesignerShared/tools/heavy-slot.py -> <super> is three levels up
PROJECT = Path(__file__).resolve().parents[3]
LOCKS = PROJECT / ".locks"
LIMITS = PROJECT / "Agents" / "AtlasPM" / "docs" / "atlas-limits.json"
POLL, MAX_WAIT, BUSY = 5, 300, 75

def render_cap():
    try: return max(1, int(json.loads(LIMITS.read_text()).get("rendering") or 4))
    except (OSError, ValueError): return 10

def take_slot(task):
    LOCKS.mkdir(parents=True, exist_ok=True)
    for i in range(render_cap()):
        f = open(LOCKS / f"render-slot-{i}.lock", "a")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            f.close(); continue
        (LOCKS / f"render-slot-{i}.who").write_text(
            f"Task {task} since {datetime.now().strftime('%Y-%m-%d %H:%M')}\n", encoding="utf-8")
        return f, i
    return None, None

def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[1] != "--": sys.exit(__doc__)
    task, cmd = a[0], a[2:]
    end = time.time() + MAX_WAIT
    while True:
        slot, i = take_slot(task)
        if slot: break
        if time.time() >= end:
            print(f"render slots busy ({render_cap()} renders running); run the same line again", file=sys.stderr)
            sys.exit(BUSY)
        time.sleep(POLL)
    print(f"render slot {i} taken for Task {task}", file=sys.stderr)
    proc = subprocess.Popen(cmd)
    # Pass a stop on to the render rather than leaving it running without its slot.
    for name in ("SIGTERM", "SIGINT", "SIGHUP"):
        if hasattr(signal, name): signal.signal(getattr(signal, name), lambda n, _f: proc.send_signal(n))
    code = proc.wait()
    try: (LOCKS / f"render-slot-{i}.who").unlink()
    except OSError: pass
    sys.exit(code if code >= 0 else 128 - code)

if __name__ == "__main__":
    main()
