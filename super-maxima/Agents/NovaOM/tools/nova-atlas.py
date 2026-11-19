#!/usr/bin/env python3
"""Nova's Atlas launcher. Runs Atlas (the project manager) in the background as a
Claude Code session, with no window and nothing for the user to open, and hands Nova
back one line.

  python3 "<max>/tools/nova-atlas.py" run <batch sheet path> [--model <model>]
      Resumes the current Atlas session when it is under 80% context, or starts a
      fresh one, and tells it: "Run this batch: <sheet>". Waits for Atlas to finish
      the whole batch (run it in the background; it can take hours). Prints one JSON
      line: {"atlas": "new"|"reused", "context_pct", "is_error", "report"}.
      --note "<text>" adds a one-off instruction from the user to Atlas's message (e.g. a
      decision on interrupted rows); it changes nothing else. A note given while the sheet
      is queued is kept and used when that sheet runs.
      --notify "<Nova's session name>" tells Atlas where his designers send each video's
      VIDEO DONE message, so Nova gets finished videos before the whole batch ends.
      The line also carries "unfinished": rows still designing, ready, or rendering after
      Atlas stopped (his designers were shut down with him; tell the user).
      When a batch is already running, the sheet is added to the batch queue instead and
      it prints {"busy": true, "queued": <position>}. When a batch finishes, the line also
      carries "sheets" (every sheet Atlas ran, including any he took from the queue in a tail
      handoff) and "next_in_queue": the sheet to run next (Nova runs it; nothing starts on its own).
  python3 "<max>/tools/nova-atlas.py" queue
      Prints the batch queue, in order (first in, first out).
  python3 "<max>/tools/nova-atlas.py" take-next
      For the running Atlas only (the tail handoff, the owner's rule, 2026-10-22): when his
      current sheet has no rows left to start, he takes the FIRST queued sheet, if its rows are
      all ready (no draft rows waiting for scripts), and runs it in his free slots. Prints
      {"sheet": <path>, "note": <its queued note or null>}, or {"sheet": null, "why": ...}.
      Any number of queued sheets per run (the owner, 2026-10-26).
  python3 "<max>/tools/nova-atlas.py" status
      Prints the current Atlas session, its last context %, and whether a batch runs.
  python3 "<max>/tools/nova-atlas.py" reset
      Forgets the current Atlas session; the next run starts a fresh one.

Atlas runs in <super>/Project, may read <super>/Agents, and may use only the approved
tool list in Agents/AtlasPM/docs/atlas-allowed-tools.txt. The Mac is kept awake for the
whole run (caffeinate). The full raw output of each run is kept in docs/atlas-runs/ for
debugging; Nova never needs to open it.
"""
import fcntl, json, os, subprocess, sys, uuid
from datetime import datetime
from pathlib import Path

MAX = Path(__file__).resolve().parents[1]
SUPER = MAX.parents[1]
PROJECT = SUPER / "Project"
AGENTS = SUPER / "Agents"
ATLAS_SKILL = AGENTS / "AtlasPM" / "atlas-project-manager.md"
ALLOWED = AGENTS / "AtlasPM" / "docs" / "atlas-allowed-tools.txt"
GUARD = AGENTS / "AtlasPM" / "docs" / "atlas-guard-settings.json"   # blocks that hold in every mode, bypass included
IDENTITY = SUPER / "agent.json"   # this machine's agent; atlas_permission_mode picks Atlas's mode (2026-11-19)
STATE = MAX / "docs" / "nova-atlas-session.json"
LOCK = MAX / "docs" / ".nova-atlas.lock"
RUNS = MAX / "docs" / "atlas-runs"
QUEUE = MAX / "docs" / "nova-batch-queue.json"
QUEUE_NOTES = MAX / "docs" / "nova-batch-queue-notes.json"   # --note given while queued, used when it runs
ATLAS_NAME = "Atlas PM"   # fixed session name, so Nova can message the running Atlas
FRESH_AT = 80          # % context at which Atlas is replaced by a fresh session
MAX_TAKEN = 1000       # no practical limit (the owner lifted the 2-sheets-per-run rule, 2026-10-26); the launcher still starts a fresh Atlas over 80% context

def load_queue():
    try: return json.loads(QUEUE.read_text())
    except (OSError, json.JSONDecodeError): return []

def save_queue(q):
    tmp = QUEUE.with_suffix(".saving"); tmp.write_text(json.dumps(q, indent=1) + "\n"); os.replace(tmp, QUEUE)

def load_state():
    try: return json.loads(STATE.read_text())
    except (OSError, json.JSONDecodeError): return {}

def save_state(st):
    tmp = STATE.with_suffix(".saving"); tmp.write_text(json.dumps(st, indent=1) + "\n"); os.replace(tmp, STATE)

def atlas_mode():
    """Atlas runs in the same permission mode as this machine's main agent (agent.json), so their
    messages are never held for approval. Empty: the allowed-tools list, with no special mode."""
    try: return (json.loads(IDENTITY.read_text()).get("atlas_permission_mode") or "").strip()
    except (OSError, ValueError): return ""

def allowed_tools():
    return ",".join(l.strip() for l in ALLOWED.read_text().splitlines() if l.strip() and not l.strip().startswith("#"))

def context_pct(d):
    u = d.get("usage") or {}
    its = u.get("iterations") or []
    last = its[-1] if its else u          # the top-level figures add up every step; the last step is the real size
    used = last.get("input_tokens", 0) + last.get("cache_read_input_tokens", 0) + last.get("cache_creation_input_tokens", 0)
    windows = [m.get("contextWindow", 0) for m in (d.get("modelUsage") or {}).values()]
    window = max(windows) if windows and max(windows) else 200_000
    return round(100 * used / window, 1)

def unfinished(sheet):
    r = subprocess.run([sys.executable, str(AGENTS / "AtlasPM" / "tools" / "atlas-sheet.py"), str(sheet), "summary"],
                       capture_output=True, text=True)
    return [l.strip() for l in r.stdout.splitlines()[1:]
            if l.strip().split(": ")[-1] in {"designing", "ready", "rendering"}]

def queue_note(sheet, note=None, take=False):
    try: notes = json.loads(QUEUE_NOTES.read_text())
    except (OSError, json.JSONDecodeError): notes = {}
    if take:
        n = notes.pop(str(sheet), None)
    else:
        n = note; notes[str(sheet)] = note
    tmp = QUEUE_NOTES.with_suffix(".saving"); tmp.write_text(json.dumps(notes, indent=1) + "\n"); os.replace(tmp, QUEUE_NOTES)
    return n

def run(sheet, model, note=None, notify=None):
    sheet = Path(sheet).expanduser()
    sheet = (sheet if sheet.is_absolute() else SUPER / sheet).resolve()
    if not sheet.is_relative_to(AGENTS / "AtlasPM" / "batches") or not sheet.is_file():
        sys.exit(f"the batch sheet must be an existing file in {AGENTS / 'AtlasPM' / 'batches'}: {sheet}")
    LOCK.touch(exist_ok=True)
    lock = open(LOCK, "r+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)        # one batch at a time
    except BlockingIOError:
        q = load_queue()
        if str(sheet) not in q: q.append(str(sheet)); save_queue(q)
        if note: queue_note(sheet, note)          # kept for when the sheet runs
        print(json.dumps({"busy": True, "running": load_state().get("running"),
                          "queued": q.index(str(sheet)) + 1})); return
    q = load_queue()
    if str(sheet) in q: q.remove(str(sheet)); save_queue(q)      # it starts now: off the queue
    saved = queue_note(sheet, take=True)
    if saved and not note: note = saved

    st = load_state()
    reuse = bool(st.get("session_id")) and st.get("context_pct", 100) < FRESH_AT
    if reuse:
        msg = f"Run this batch: {sheet}"
        cmd_id = ["--resume", st["session_id"]]
    else:
        msg = (f"Read and follow {ATLAS_SKILL}. You are Atlas, running in the background through "
               f"Nova's launcher: nobody can answer questions mid-run, the build folder {PROJECT} is "
               f"confirmed, and the Mac is kept awake for you. Run this batch: {sheet}")
        cmd_id = ["--session-id", str(uuid.uuid4())]
    if notify: msg += f"\nNova's session for video-done messages: {notify}"
    if note: msg += f"\nNova's note from the user for this run: {note}"
    cmd = ["caffeinate", "-i", "claude", "-p", msg, "--name", ATLAS_NAME, "--output-format", "json",
           "--allowedTools", allowed_tools(), "--add-dir", str(AGENTS), "--settings", str(GUARD), *cmd_id]
    if atlas_mode(): cmd += ["--permission-mode", atlas_mode()]
    if model: cmd += ["--model", model]

    st["running"] = str(sheet); st["taken"] = []; save_state(st)
    started = datetime.now()
    r = subprocess.run(cmd, cwd=PROJECT, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / f"{started:%Y%m%d-%H%M%S}.json").write_text(r.stdout or r.stderr)

    try:
        d = json.loads(r.stdout)
        if isinstance(d, list):          # newer CLI prints every message; the last "result" one is the summary
            d = next((x for x in reversed(d) if isinstance(x, dict) and x.get("type") == "result"), {})
    except json.JSONDecodeError:
        st.pop("running", None); save_state(st)
        print(json.dumps({"atlas": "reused" if reuse else "new", "is_error": True,
                          "report": f"launcher could not read Atlas's output: {(r.stderr or r.stdout).strip()[:300]}"}))
        return
    pct = context_pct(d)
    st = dict(load_state(), **{k: v for k, v in st.items() if k != "taken"})   # keep what take-next recorded
    sheets = [str(sheet)] + st.get("taken", [])
    st.update(session_id=d.get("session_id") or st.get("session_id"), context_pct=pct,
              batches=(st.get("batches", 0) + 1) if reuse else 1, last_sheet=str(sheet),
              last_run=started.isoformat(timespec="minutes"))
    st.pop("running", None); st.pop("taken", None); save_state(st)
    nxt = (load_queue() or [None])[0]
    print(json.dumps({"atlas": "reused" if reuse else "new", "context_pct": pct,
                      "is_error": bool(d.get("is_error")), "report": d.get("result"),
                      "sheets": sheets, "unfinished": [u for s in sheets for u in unfinished(s)],
                      "next_in_queue": nxt}))

def take_next():
    st = load_state()
    if not st.get("running"):
        print(json.dumps({"sheet": None, "why": "no batch is running"})); return
    if len(st.get("taken", [])) >= MAX_TAKEN:
        print(json.dumps({"sheet": None, "why": f"already took {MAX_TAKEN} sheets this run"})); return
    q = load_queue()
    if not q:
        print(json.dumps({"sheet": None, "why": "queue empty"})); return
    s = q[0]                                              # first in, first out: never skip ahead
    r = subprocess.run([sys.executable, str(AGENTS / "AtlasPM" / "tools" / "atlas-sheet.py"), s, "summary"],
                       capture_output=True, text=True)
    first = r.stdout.splitlines()[0] if r.stdout.strip() else ""
    if r.returncode != 0 or not first or "draft" in first:
        print(json.dumps({"sheet": None, "why": "the next queued sheet is not ready (rows still waiting for scripts)"})); return
    q.pop(0); save_queue(q)
    note = queue_note(s, take=True)
    st.setdefault("taken", []).append(s); save_state(st)
    print(json.dumps({"sheet": s, "note": note}))

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "run" and len(a) >= 2:
        model = a[a.index("--model") + 1] if "--model" in a else os.environ.get("MAX_ATLAS_MODEL")
        note = a[a.index("--note") + 1] if "--note" in a else None
        notify = a[a.index("--notify") + 1] if "--notify" in a else None
        run(a[1], model, note, notify)
    elif a[0] == "status":
        st = load_state(); LOCK.touch(exist_ok=True)
        with open(LOCK, "r+") as lk:
            try: fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB); busy = False
            except BlockingIOError: busy = True
        print(json.dumps({"session_id": st.get("session_id"), "context_pct": st.get("context_pct"),
                          "batches": st.get("batches"), "running": st.get("running") if busy else None}))
    elif a[0] == "take-next":
        take_next()
    elif a[0] == "queue":
        print(json.dumps({"queue": load_queue()}))
    elif a[0] == "reset":
        st = load_state(); st.pop("session_id", None); st.pop("context_pct", None); save_state(st)
        print(json.dumps({"reset": True}))
    else:
        sys.exit(__doc__)

if __name__ == "__main__":
    main()
