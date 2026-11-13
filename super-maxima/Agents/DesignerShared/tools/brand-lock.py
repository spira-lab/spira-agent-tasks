#!/usr/bin/env python3
"""Keep parallel designers from writing over each other in the files they share (2026-11-10).

  python3 "<shared>/tools/brand-lock.py" <Brand> -- <command> [args ...]
      Runs the command while holding the brand's lock, and exits with its exit code. For work on
      a brand's shared files that is more than one append: a new voice.md, brand/ui/ screenshots,
      editing brand/truth.md in place. Read the file again inside the lock first; another
      designer may have just made it. Waits up to 540 seconds for the lock (exit 75 after that).
  python3 "<shared>/tools/brand-lock.py" append <file> @<textfile>
      Appends the text in <textfile> to <file> under a lock (the brand's lock for a file in
      client-assets/<Brand>/, the file's own lock otherwise), on a line of its own:
      designer-lessons.md, field-lessons.md, cloner-lessons.md, brand/truth.md, brand/outfits.md.
      Both files must be inside the Super Vega folder.

<Brand> is the brand folder name (letters, digits, - and _). The locks are kept in
<super>/.locks/, released when the process ends, so a crash never leaves one held.
"""
import fcntl, hashlib, re, subprocess, sys, time
from pathlib import Path

# <super>/Agents/DesignerShared/tools/brand-lock.py -> <super> is three levels up
PROJECT = Path(__file__).resolve().parents[3]
LOCKS = PROJECT / ".locks"
POLL, MAX_WAIT, BUSY = 2, 540, 75

def hold(name):
    LOCKS.mkdir(parents=True, exist_ok=True)
    f = open(LOCKS / name, "a")
    end = time.time() + MAX_WAIT
    while True:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); return f
        except BlockingIOError:
            if time.time() >= end:
                print(f"{name} still held by another designer; run the same line again", file=sys.stderr)
                sys.exit(BUSY)
            time.sleep(POLL)

def inside(value):
    p = Path(value).expanduser()
    p = (p if p.is_absolute() else Path.cwd() / p).resolve()
    if not p.is_relative_to(PROJECT): sys.exit(f"{p} is outside {PROJECT}")
    return p

def append(target, source):
    if not source.startswith("@"): sys.exit("the text to append is given as @<textfile>")
    t, s = inside(target), inside(source[1:])
    if not s.is_file(): sys.exit(f"no file at {s}")
    text = s.read_text(encoding="utf-8").strip("\n")
    if not text: sys.exit(f"{s} is empty")
    parts = t.relative_to(PROJECT).parts
    # A brand's own file shares the brand lock, so an append never lands inside an in-place edit.
    brand = parts[parts.index("client-assets") + 1] if "client-assets" in parts[:-2] else None
    _lock = hold(f"brand-{brand}.lock" if brand and re.fullmatch(r"[A-Za-z0-9_-]+", brand)
                 else "append-" + hashlib.sha1(str(t).encode()).hexdigest()[:16] + ".lock")
    t.parent.mkdir(parents=True, exist_ok=True)
    old = t.read_text(encoding="utf-8") if t.exists() else ""
    with open(t, "a", encoding="utf-8") as out:
        out.write(("" if not old or old.endswith("\n") else "\n") + text + "\n")
    print(f"appended to {t}")

def main():
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == "append": return append(a[1], a[2])
    if len(a) < 3 or a[1] != "--": sys.exit(__doc__)
    brand, cmd = a[0], a[2:]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", brand): sys.exit(f"not a brand folder name: {brand!r}")
    _lock = hold(f"brand-{brand}.lock")
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
