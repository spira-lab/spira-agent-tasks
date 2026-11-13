"""Timing slots: at most "timing" local Whisper runs at once across the employee (the owner's
decision, 2026-11-13: one per 2 cores, at least 2, "cpus_per_timing" in
Agents/AtlasPM/docs/atlas-limits.json), each on
WHISPER_THREADS threads. Separate from the render slots of heavy-slot.py.

  with timing_slot("<what is transcribed>"):
      ... run Whisper with WHISPER_THREADS threads ...

Waits for a free slot (checking every 5 seconds, at most 300). With no slot free after 300 seconds
it exits 75 without running anything: run the same line again.

A slot is a lock on <super>/.locks/timing-slot-<n>.lock held by this process, freed when it ends,
also on a crash or a restart. <super>/.locks/timing-slot-<n>.who says who holds it
(atlas-sheet.py slots shows it)."""
import fcntl, json, os, sys, time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

# <super>/Agents/DesignerShared/tools/timing_slot.py -> <super> is three levels up
PROJECT = Path(__file__).resolve().parents[3]
LOCKS = PROJECT / ".locks"
LIMITS = PROJECT / "Agents" / "AtlasPM" / "docs" / "atlas-limits.json"
POLL, MAX_WAIT, BUSY = 5, 300, 75
WHISPER_THREADS = 8


def cpu_count():
    try: return len(os.sched_getaffinity(0))
    except AttributeError: return os.cpu_count() or 1


def timing_cap():
    try: per = int(json.loads(LIMITS.read_text()).get("cpus_per_timing") or 2)
    except (OSError, ValueError): per = 2
    return max(2, cpu_count() // max(1, per))


def _take(label):
    LOCKS.mkdir(parents=True, exist_ok=True)
    for i in range(timing_cap()):
        f = open(LOCKS / f"timing-slot-{i}.lock", "a")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            f.close(); continue
        (LOCKS / f"timing-slot-{i}.who").write_text(
            f"{label} since {datetime.now().strftime('%Y-%m-%d %H:%M')}\n", encoding="utf-8")
        return f, i
    return None, None


@contextmanager
def timing_slot(label):
    end = time.time() + MAX_WAIT
    waited = False
    while True:
        f, i = _take(label)
        if f: break
        if time.time() >= end:
            print(f"timing slots busy ({timing_cap()} running); run the same line again", file=sys.stderr)
            sys.exit(BUSY)
        if not waited:
            print("waiting for a timing slot", file=sys.stderr); waited = True
        time.sleep(POLL)
    try:
        yield i
    finally:
        try: (LOCKS / f"timing-slot-{i}.who").unlink()
        except OSError: pass
        f.close()
