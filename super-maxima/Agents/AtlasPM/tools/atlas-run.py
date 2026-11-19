#!/usr/bin/env python3
"""LEGACY Atlas runner: no Task ID column, so the designer will stop and ask for one.
Use atlas-sheet.py with the Atlas skill instead.

Run a sheet of video requests, one Claude Code session per row, one after another.

Usage:
  python3 "<atlas>/tools/atlas-run.py" <sheet.xlsx|sheet.csv> [--dry-run | --check] [--permission-mode auto]
                             [--model <model>] [--hours 3]

  --dry-run  print the request each row would send; launches nothing.
  --check    launch a real session per row with the same flags and folders, but a
             health-check prompt instead of the request: it reads the skills, runs the
             Spira preflight, and writes a test file in the root. No video, no credits,
             about a minute a row. The sheet is not changed. Covers example rows too.

Each row whose status is blank or "pending" becomes the request below, run headless
in that row's root folder. The runner waits for it to finish, writes the outcome back
into the row, saves the sheet, then starts the next row. Rows marked done, failed,
running, or example are skipped; set a row back to pending to run it again.

Close the sheet in Excel or Numbers before starting: the runner saves into it.
"""
import argparse, csv, json, os, subprocess, sys, time, uuid
from datetime import datetime
from pathlib import Path

# <super>/Agents/AtlasPM/tools/atlas-run.py -> <super> (Super Nova) is three levels up
PROJECT = Path(__file__).resolve().parents[3]
PACKAGE = PROJECT / "Agents" / "TalkingHeadEditedVideoDesigner"
SKILL = PACKAGE / "skills" / "talking-head-edited-video-designer.md"
INPUT_COLS = ["label", "root_folder", "style_ref", "instructions", "script", "after_video_skill"]
OUTPUT_COLS = ["status", "started", "minutes", "session_id", "result"]
COLUMNS = INPUT_COLS + OUTPUT_COLS
RUNNABLE = {"", "pending"}

def build_prompt(r):
    lines = [f"Read this skill {SKILL}"]
    if r["style_ref"]:
        lines.append(f"This is the style: {r['style_ref']}")
    if r["instructions"]:
        lines.append(f"Instructions: {r['instructions']}")
    lines.append("Here is the script:")
    lines.append(r["script"])
    if r["after_video_skill"]:
        lines.append(f"Read and use {r['after_video_skill']} once done with the video. "
                     "Only when done with the original video.")
    return "\n".join(lines)

def check_prompt(r):
    steps = [
        "Run pwd.",
        f"Read the first 5 lines of {SKILL}.",
    ]
    if r["after_video_skill"]:
        steps.append(f"Read the first 5 lines of {r['after_video_skill']}.")
    steps += [
        "Run: spira auth whoami",
        "Run: spira credits balance",
        "Create a file named .batch-check in the current folder, then delete it.",
    ]
    body = "\n".join(f"{i}. {t}" for i, t in enumerate(steps, 1))
    return ("This is a health check only. Do not produce a video, generate anything, or read "
            "any other file. Do these steps and nothing else:\n" + body +
            "\nReply with one line per step: its number, OK or FAILED, and the error if it failed. "
            "Nothing else.")

# ---------- sheet io: xlsx or csv ----------
def load(path):
    if path.suffix.lower() == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path); ws = wb.active
        head = [str(c.value or "").strip() for c in ws[1]]
        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            d = {h: ("" if v is None else str(v).strip()) for h, v in zip(head, row)}
            if any(d.get(c) for c in INPUT_COLS): rows.append(d)
        return rows, (wb, ws, head)
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    return [r for r in rows if any(r.get(c) for c in INPUT_COLS)], None

def save(path, rows, handle):
    for r in rows:
        for c in COLUMNS: r.setdefault(c, "")
    if handle:
        wb, ws, head = handle
        for c in COLUMNS:
            if c not in head: head.append(c); ws.cell(row=1, column=len(head), value=c)
        for i, r in enumerate(rows, start=2):
            for j, h in enumerate(head, start=1):
                if h in r: ws.cell(row=i, column=j, value=r[h])
        tmp = path.with_name(path.stem + ".saving" + path.suffix); wb.save(tmp); os.replace(tmp, path)
        return
    tmp = path.with_name(path.stem + ".saving" + path.suffix)
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)

# ---------- one run ----------
def extra_dirs(r):
    dirs = {str(PACKAGE), str(PROJECT / "Agents" / "DesignerShared")}
    if r["after_video_skill"]:
        p = Path(r["after_video_skill"]).expanduser().resolve()
        if not p.is_relative_to(PROJECT):   # skills are read only from inside the Super Nova folder
            sys.exit(f"after_video_skill must be inside {PROJECT}, not {p}")
        dirs.add(str(p.parent.parent if p.parent.name == "skills" else p.parent))
    if r["style_ref"] and not r["style_ref"].lower().startswith("http"):
        dirs.add(str(Path(r["style_ref"]).expanduser().parent))
    return sorted(dirs)

def command(r, sid, args, prompt=None):
    cmd = ["claude", "-p", prompt or build_prompt(r), "--output-format", "json",
           "--permission-mode", args.permission_mode, "--session-id", sid,
           "--name", r["label"] or f"batch {sid[:8]}"]
    for d in extra_dirs(r): cmd += ["--add-dir", d]
    if args.model: cmd += ["--model", args.model]
    return cmd

def run_row(r, args):
    root = Path(r["root_folder"]).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    sid = str(uuid.uuid4())
    r.update(status="running", started=datetime.now().strftime("%Y-%m-%d %H:%M"), session_id=sid, result="")
    t0 = time.time()
    try:
        p = subprocess.run(command(r, sid, args), cwd=root, capture_output=True, text=True,
                           timeout=args.hours * 3600)
        out = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
        ok = p.returncode == 0 and not out.get("is_error")
        text = out.get("result") or p.stderr.strip() or p.stdout.strip()
    except subprocess.TimeoutExpired:
        ok, text = False, f"stopped after {args.hours} h"
    r.update(status="done" if ok else "failed", minutes=str(round((time.time() - t0) / 60)),
             result=" ".join(text.split())[:1500])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--permission-mode", default="auto"); ap.add_argument("--model")
    ap.add_argument("--hours", type=float, default=3.0)
    args = ap.parse_args()
    path = Path(args.sheet).expanduser().resolve()
    if not path.is_file():
        sys.exit(f"No sheet at {path}\nGive the path of a filled copy of atlas-videos-template.xlsx.")
    rows, handle = load(path)
    runnable = RUNNABLE | {"example"} if args.check else RUNNABLE   # a check spends nothing, so it covers the example too
    todo = [r for r in rows if r.get("status", "").lower() in runnable]
    bad = [r.get("label") or "(no label)" for r in todo if not r.get("root_folder") or not r.get("script")]
    if bad: sys.exit(f"rows missing root_folder or script: {', '.join(bad)}")
    proj = PROJECT / "Project"
    outside = [r.get("label") or r["root_folder"] for r in todo
               if not Path(r["root_folder"]).expanduser().resolve().is_relative_to(proj)]
    if outside: sys.exit(f"root_folder must be inside {proj}: {', '.join(outside)}")
    print(f"{len(todo)} row(s) to run, {len(rows) - len(todo)} skipped")
    if args.dry_run:
        for r in todo:
            print(f"\n--- {r.get('label') or '(no label)'}  in  {r['root_folder']}\n{build_prompt(r)}")
            print("add-dir:", ", ".join(extra_dirs(r)))
        return
    if args.check:
        for r in todo:
            label = r.get("label") or r["root_folder"]
            root = Path(r["root_folder"]).expanduser(); root.mkdir(parents=True, exist_ok=True)
            print(f"\n--- check: {label}  in  {root}", flush=True)
            t0 = time.time()
            try:
                p = subprocess.run(command(r, str(uuid.uuid4()), args, check_prompt(r)), cwd=root,
                                   capture_output=True, text=True, timeout=600)
                out = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
                text = out.get("result") or p.stderr.strip() or p.stdout.strip()
                bad = p.returncode != 0 or out.get("is_error") or "FAILED" in text
            except subprocess.TimeoutExpired:
                text, bad = "no answer within 10 minutes", True
            print(text.strip())
            print(f"=> {'PROBLEM' if bad else 'READY'} ({round(time.time() - t0)} s)")
        return
    if sys.platform == "darwin":   # keep the Mac awake for exactly as long as this runner lives
        subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    for n, r in enumerate(todo, 1):
        print(f"[{n}/{len(todo)}] {r.get('label') or r['root_folder']} ...", flush=True)
        r["status"] = "running"; save(path, rows, handle)
        run_row(r, args); save(path, rows, handle)
        print(f"   {r['status']} in {r['minutes']} min", flush=True)
    print("all rows finished")

if __name__ == "__main__":
    main()
