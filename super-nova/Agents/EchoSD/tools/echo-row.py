#!/usr/bin/env python3
"""Echo's row reader. Prints one batch-sheet row's brief as one JSON line, so Echo never
loads the whole sheet. Read-only: scripts are written into the sheet with Atlas's
`atlas-sheet.py set`, never here.

  python3 "<echo>/tools/echo-row.py" <sheet.md> <task id>
      Prints {"task_id", "brand", "brand_number", "output_type", "video_style",
              "instructions", "music", "status", "has_script"}.
  python3 "<echo>/tools/echo-row.py" <sheet.md> drafts
      Prints the Task IDs of every row still waiting for its script, one per line.
"""
import importlib.util, json, sys
from pathlib import Path

SUPER = Path(__file__).resolve().parents[3]
SHEET_TOOL = SUPER / "Agents" / "AtlasPM" / "tools" / "atlas-sheet.py"

def atlas_sheet():
    spec = importlib.util.spec_from_file_location("atlas_sheet", SHEET_TOOL)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def main():
    if len(sys.argv) != 3: sys.exit(__doc__)
    path = Path(sys.argv[1]).expanduser().resolve()
    if not path.is_relative_to(SUPER) or not path.is_file():
        sys.exit(f"no batch sheet inside {SUPER} at {path}")
    rows, _ = atlas_sheet().load(path)
    if sys.argv[2] == "drafts":
        for r in rows:
            if (r.get("Status") or "").lower() == "draft": print(r.get("Task ID"))
        return
    for r in rows:
        if r.get("Task ID") == sys.argv[2]:
            print(json.dumps({
                "task_id": r.get("Task ID"), "brand": r.get("Brand"), "brand_number": r.get("Brand number"),
                "output_type": r.get("Output type"), "video_style": r.get("Style"),
                "instructions": r.get("Instructions"), "music": r.get("Music"),
                "status": r.get("Status"), "has_script": bool(r.get("Script")),
            })); return
    sys.exit(f"no row with Task ID {sys.argv[2]}")

if __name__ == "__main__":
    main()
