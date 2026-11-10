#!/usr/bin/env python3
"""Hermes's upload bookkeeping. Hermes hosts each finished video (and carousel slide) with the
host_file tool; this script holds only the local part: which files a batch sheet's rows call for, which
tag they go under, which are already hosted, and the upload log. It never calls Spira and never hosts
anything itself.

  python3 "<hermes>/tools/hermes-upload.py" plan --sheet <batch sheet> --tasks <11,12,... | done>
          --brand "<brand>" [--product "<product name>"] [--tag <tag id>]
  python3 "<hermes>/tools/hermes-upload.py" record --path <file> --url <hosted url>
          --task <Task ID> --brand "<brand>" [--product "<product name>"] --tag "<label>" [--tag-id <id>]
          [--carousel <folder> --slide <i> --of <n>]

plan: for each Task ID (or every done row with "done"):
  - the row must be done; its render path comes from the row's Result (DONE <render path> ...)
  - a carousel row (Result DONE <carousel folder> ..., any carousel style): each slide JPEG in the folder's
    out/ (slide-01.jpg, slide-02.jpg, ...) is listed in order, as an image; the contact sheet and notes
    are never listed
  - the tag comes from docs/hermes-working-memory.md, per kind (2026-10-29): video rows use the
    tag For "videos", carousel rows the tag For "carousels", either falling back to a row For both
    (For empty); a row for the kind wins, then the product's row over the brand's
  - --tag <tag id> is a one-off tag for this run only, used for every row instead of the working memory
  - a file already hosted (same path, same size, same tag) is listed as skipped, with its URL
  Prints one JSON line per file ({"path", "task_id", "action": "host"|"skipped", ...}), then one summary
  line. For every "host" line, call host_file with that path, then record it.
record: appends the file and the URL host_file returned to docs/hermes-upload-log.json.
"""
import fcntl, importlib.util, json, re, sys
from datetime import datetime
from pathlib import Path

HERMES = Path(__file__).resolve().parents[1]
SUPER = HERMES.parents[1]
MEMORY = HERMES / "docs" / "hermes-working-memory.md"
LOG = HERMES / "docs" / "hermes-upload-log.json"
SHEET_TOOL = SUPER / "Agents" / "AtlasPM" / "tools" / "atlas-sheet.py"
PROJECT = SUPER / "Project"

def norm(s): return " ".join((s or "").lower().split())

def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default

def tag_for(brand, product, kind):
    """(label, tag id) from the working memory for kind "videos" or "carousels": a row For that
    kind wins over a row For both (For empty); then the product's row wins over the brand's."""
    rows, head = [], None
    for line in MEMORY.read_text(encoding="utf-8").splitlines():
        if line.startswith("| Brand"):
            head = [norm(x) for x in line.strip().strip("|").split("|")]; continue
        if not head or line.startswith("|---"): continue
        if not line.startswith("|"): head = None; continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) != len(head) or not c[0]: continue
        r = dict(zip(head, c))
        tag = next((v for k, v in r.items() if k.startswith("tag (")), "")
        rows.append((norm(r.get("brand")), norm(r.get("product")), norm(r.get("for")), tag, r.get("tag id", "")))
    b, p = norm(brand), norm(product)
    for want_for in (kind, ""):
        if p:
            for rb, rp, rf, tag, tid in rows:
                if rb == b and rp == p and rf == want_for and tid: return tag, tid
        for rb, rp, rf, tag, tid in rows:
            if rb == b and not rp and rf == want_for and tid: return tag, tid
    return None, None

def load_sheet(path):
    spec = importlib.util.spec_from_file_location("atlas_sheet", SHEET_TOOL)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    rows, _ = m.load(path)
    return rows

def render_of(row):
    m = re.match(r"DONE\s+(.+?\.mp4)\b", row.get("Result") or "")
    return Path(m.group(1)) if m else None

def carousel_of(row):
    """A carousel row's folder (DONE <Project/<Brand>/carousels/<name>> <credits> <minutes>)."""
    m = re.match(r"DONE\s+(.+?/carousels/[^/\s]+)/?(?:\s|$)", row.get("Result") or "")
    return Path(m.group(1)) if m else None

def slides_of(folder):
    """The slide JPEGs in order: out/slide-01.jpg, slide-02.jpg, ..."""
    return sorted((folder / "out").glob("slide-*.jpg"), key=lambda f: int(re.sub(r"\D", "", f.stem) or 0))

def plan(a):
    sheet, tasks, brand = opt(a, "--sheet"), opt(a, "--tasks"), opt(a, "--brand")
    product = opt(a, "--product")
    if not (sheet and tasks and brand): sys.exit(__doc__)
    if norm(product) in {"", "none"}: product = None
    sheet = Path(sheet) if Path(sheet).is_absolute() else SUPER / sheet
    if not sheet.is_file(): sys.exit(f"FAILED no sheet at {sheet}")

    one_off = opt(a, "--tag")

    rows = load_sheet(sheet)
    if norm(tasks) == "done":
        picked = [r for r in rows if norm(r.get("Status")) == "done"]
    else:
        want = [t.strip() for t in tasks.split(",") if t.strip()]
        by_id = {r["Task ID"].lstrip("0"): r for r in rows}
        missing = [t for t in want if t.lstrip("0") not in by_id]
        if missing: sys.exit(f"FAILED no such Task ID on the sheet: {', '.join(missing)}")
        picked = [by_id[t.lstrip("0")] for t in want]

    kinds = {"carousels" if (not render_of(r) and carousel_of(r)) else "videos"
             for r in picked if norm(r.get("Status")) == "done"} or {"videos"}
    tag = {}
    for kind in sorted(kinds, reverse=True):
        lt = (one_off, one_off) if one_off else tag_for(brand, product, kind)
        if not lt[1]:
            sys.exit(f"QUESTION no upload tag for {kind} in Hermes's working memory for {brand}" + (f" / {product}" if product else ""))
        tag[kind] = lt

    log = json.loads(LOG.read_text(encoding="utf-8") or "{}") if LOG.is_file() else {}
    to_host = skipped = 0; problems = []; carousels = 0

    def emit(tid, f, kind, extra=None):
        nonlocal to_host, skipped
        label, tag_id = tag[kind]
        prev = log.get(str(f))
        d = {"task_id": tid, "path": str(f), "tag": label, "tag_id": tag_id, **(extra or {})}
        if prev and prev.get("size") == f.stat().st_size and prev.get("tag_id") == tag_id:
            skipped += 1; d.update(action="skipped", url=prev.get("url"))
        else:
            to_host += 1; d.update(action="host")
        print(json.dumps(d, ensure_ascii=False))

    for r in picked:
        tid = r["Task ID"]
        if norm(r.get("Status")) != "done":
            problems.append(f"{tid} not done ({r.get('Status') or 'pending'})"); continue
        folder = None if render_of(r) else carousel_of(r)
        if folder:
            if not folder.is_dir():
                problems.append(f"{tid} carousel folder not found"); continue
            if not folder.resolve().is_relative_to(PROJECT):
                problems.append(f"{tid} carousel outside Project/"); continue
            slides = slides_of(folder)
            if not slides:
                problems.append(f"{tid} carousel has no slides in out/"); continue
            carousels += 1
            for i, slide in enumerate(slides, 1):
                emit(tid, slide, "carousels", {"carousel": str(folder), "slide": i, "of": len(slides)})
            continue
        render = render_of(r)
        if not render or not render.is_file():
            problems.append(f"{tid} render not found"); continue
        if not render.resolve().is_relative_to(PROJECT):
            problems.append(f"{tid} render outside Project/"); continue
        emit(tid, render, "videos")
    labels = sorted({label for label, _ in tag.values()})
    line = f"PLAN {to_host} files to host under tag {' and '.join(labels)}"
    if carousels: line += f" ({carousels} carousel{'s' if carousels != 1 else ''}, slides in order)"
    if skipped: line += f"; {skipped} already hosted"
    if problems: line += f"; problems: {'; '.join(problems)}"
    print(line)
    sys.exit(1 if problems and not to_host and not skipped else 0)

def record(a):
    path, url, tid, brand, label = opt(a, "--path"), opt(a, "--url"), opt(a, "--task"), opt(a, "--brand"), opt(a, "--tag")
    if not (path and url and tid and brand and label): sys.exit(__doc__)
    if not url.startswith("https://"): sys.exit("--url must be the https URL host_file returned")
    f = Path(path)
    if not f.is_file(): sys.exit(f"FAILED no file at {f}")
    entry = {"task_id": tid, "brand": brand, "product": opt(a, "--product"), "tag": label, "tag_id": opt(a, "--tag-id") or label,
             "size": f.stat().st_size, "url": url, "uploaded": datetime.now().isoformat(timespec="minutes")}
    if opt(a, "--carousel"):
        entry.update(carousel=opt(a, "--carousel"), slide=int(opt(a, "--slide", 0)), of=int(opt(a, "--of", 0)))
    LOG.parent.mkdir(parents=True, exist_ok=True); LOG.touch(exist_ok=True)
    with open(LOG, "r+", encoding="utf-8") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        raw = lf.read().strip(); log = json.loads(raw) if raw else {}
        log[str(f)] = entry
        lf.seek(0); lf.truncate(); lf.write(json.dumps(log, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"recorded": str(f), "url": url}))

def main():
    a = sys.argv[1:]
    if a and a[0] == "plan": return plan(a[1:])
    if a and a[0] == "record": return record(a[1:])
    sys.exit(__doc__)

if __name__ == "__main__":
    main()
