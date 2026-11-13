"""Platform profile shared by the Python tools. Decisions come from the platform and the machine,
never from new environment variables.

Importing this module redirects `tempfile` to the scratch root, so import it before any tempfile use."""
import os, shutil, sys, tempfile, time
from pathlib import Path

MIN_FREE_BYTES = 4 * 2 ** 30
STALE_SECONDS = 4 * 3600


def cpu_count():
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count() or 1


def sweep_stale(d):
    now = time.time()
    for p in Path(d).iterdir():
        try:
            if now - p.stat().st_mtime > STALE_SECONDS:
                shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink()
        except OSError:
            pass


def _pick_root():
    shm = Path("/dev/shm")
    try:
        if os.access(shm, os.W_OK) and shutil.disk_usage(shm).free >= MIN_FREE_BYTES:
            d = shm / f"supervega-{os.getuid()}"
            d.mkdir(mode=0o700, exist_ok=True)
            sweep_stale(d)
            return str(d)
    except OSError:
        pass
    return tempfile.gettempdir()


OS_TEMP = tempfile.gettempdir()
SCRATCH_ROOT = _pick_root()
tempfile.tempdir = SCRATCH_ROOT


def preset(kind):
    """kind: 'intermediate' (reference cuts, composites, share copy) or 'final' (the delivered picture)."""
    return "faster" if kind == "final" else "veryfast"
