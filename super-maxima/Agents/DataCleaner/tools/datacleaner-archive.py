#!/usr/bin/env python3
"""Data Cleaner's archiver. Moves one failed task's files out of the way, so a redo
can start from scratch under the same numbers, or a cancelled task's numbers can be
issued again without clashing with old files. It only moves files; it never deletes
and never opens their contents.

  python3 "<cleaner>/tools/datacleaner-archive.py" <task id> <redo|cancel>

It looks the task up in Vega's register (never trusts a number it is handed), finds
the video by the metadata file whose task_id matches, and moves everything with that
video's name into:

  Project/<BrandName>/archive/<name>_<redo|cancel>-<YYYYMMDD-HHMM>/
    editable/<name>.html
    editable/materials/<name>/
    renders/<name>.mp4, renders/deletable/<name>_*.mp4
    metadata/<name>.json
    archive.json          what was archived, when, and why

Prints one JSON line: {"task_id", "brand", "brand_number", "archived_to", "moved"}.
"""
import json, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

SUPER = Path(__file__).resolve().parents[3]          # <super>/Agents/DataCleaner/tools/this
MAX_TOOL = SUPER / "Agents" / "VegaOM" / "tools" / "vega-task-id.py"
PROJECT = SUPER / "Project"

def main():
    if len(sys.argv) != 3 or sys.argv[2] not in {"redo", "cancel"}:
        sys.exit(__doc__)
    task, decision = sys.argv[1], sys.argv[2]

    # 1. Vega's register is the source of truth for the task's brand and number.
    res = subprocess.run([sys.executable, str(MAX_TOOL), "show", task], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"Vega's register has no active task {task}: {res.stderr.strip() or res.stdout.strip()}")
    t = json.loads(res.stdout)
    task_id, brand, bno = t["task_id"], t["brand"], t["brand_number"]
    root = PROJECT / brand
    if not root.resolve().is_relative_to(PROJECT.resolve()):
        sys.exit(f"brand folder outside Project/: {root}")

    # 2. Find the video by its metadata task_id, never by guessing from file names.
    names = []
    for m in sorted((root / "metadata").glob("*.json")) if (root / "metadata").is_dir() else []:
        try:
            data = json.loads(m.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("task_id", "")).lstrip("0") == task_id.lstrip("0"):
            names.append(data.get("name") or m.stem)

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    label = names[0] if len(names) == 1 else f"{bno}-task{task_id}"
    dest = root / "archive" / f"{label}_{decision}-{stamp}"
    k = 2
    while dest.exists():                               # never merge into an earlier archive
        dest = root / "archive" / f"{label}_{decision}-{stamp}_{k}"; k += 1
    moved = []

    def move(src, rel):
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(target))
        moved.append(str(Path(rel)))

    for name in names:
        for src, rel in [
            (root / "editable" / f"{name}.html", f"editable/{name}.html"),
            (root / "editable" / "materials" / name, f"editable/materials/{name}"),
            (root / "renders" / f"{name}.mp4", f"renders/{name}.mp4"),
            (root / "metadata" / f"{name}.json", f"metadata/{name}.json"),
        ]:
            if src.exists(): move(src, rel)
        rd = root / "renders" / "deletable"
        if rd.is_dir():
            for f in sorted(rd.glob(f"{name}_*")):
                move(f, f"renders/deletable/{f.name}")

    if moved:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "archive.json").write_text(json.dumps({
            "task_id": task_id, "brand": brand, "brand_number": bno, "decision": decision,
            "archived": datetime.now().isoformat(timespec="minutes"), "names": names, "moved": moved,
        }, indent=1) + "\n")

    print(json.dumps({"task_id": task_id, "brand": brand, "brand_number": bno,
                      "archived_to": str(dest) if moved else None, "moved": len(moved)}))

if __name__ == "__main__":
    main()
