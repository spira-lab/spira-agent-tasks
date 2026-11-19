#!/usr/bin/env python3
"""Delivers one finished video or carousel (the owner's rule, 2026-11-12): every delivery carries its post
copy (title, caption, hashtags), and every re-skit or clone also carries its source link.

  python3 nova-deliver.py --sheet <batch sheet> --task <Task ID> --thread <Lark message_id>
          [--of "<n> of <total>"] [--label "<e.g. Item 3>"] [--note "<extra line>"] [--allow-missing] [--dry-run]
  python3 nova-deliver.py --sheet <batch sheet> --task <Task ID> --here [--of ...] [--label ...]

--thread: replies in that Lark thread with the video (a carousel: its contact sheet), then ONE message:
  ✅ Task <id> (<label>), <style>, done · <length> · <n of total> · ref: <source>   (ref for re-skit and clone)
  Title / Caption / Hashtags from Project/<Brand>/metadata/<name>.post.json
--here: prints that message (for a file caption in the desktop chat) and the file path; sends nothing.
--dry-run: prints what would be sent.
A missing post copy stops the delivery (NO_POST_COPY) unless --allow-missing (outputs made before the rule);
a missing source link is written into the message as a warning. Nothing is ever skipped silently.
"""
import importlib.util, json, re, subprocess, sys
from pathlib import Path

MAX = Path(__file__).resolve().parents[1]
SUPER = MAX.parents[1]
LARK = SUPER / "Lark connect" / "lark-nova.py"
spec = importlib.util.spec_from_file_location("atlas_sheet", SUPER / "Agents" / "AtlasPM" / "tools" / "atlas-sheet.py")
sheet = importlib.util.module_from_spec(spec); spec.loader.exec_module(sheet)
SOURCED = ("re-skit", "clone")

def opt(a, n): return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else None

def source_of(r):
    """The source link: the row's Source video when it is a link, else the link the instructions name
    (a trimmed local source says 'The source is the first 30 s of <link>')."""
    src = (r.get("Source video") or "").strip()
    if src.startswith("http"): return src
    m = re.search(r"(https?://(?:www\.)?(?:instagram\.com|tiktok\.com|youtube\.com|youtu\.be|x\.com|twitter\.com|facebook\.com)\S*)",
                  r.get("Instructions") or "")
    return m.group(1).rstrip(".,;)") if m else None

def main():
    a = sys.argv[1:]
    sh, tid, thread = opt(a, "--sheet"), opt(a, "--task"), opt(a, "--thread")
    here, dry = "--here" in a, "--dry-run" in a
    if not (sh and tid and (thread or here)): sys.exit(__doc__)
    p = Path(sh) if Path(sh).is_absolute() else SUPER / sh
    rows, _ = sheet.load(p)
    r = next((x for x in rows if x["Task ID"].lstrip("0") == tid.lstrip("0")), None)
    if not r: sys.exit(f"FAILED no Task {tid} on {p.name}")
    res = r.get("Result") or ""
    mv = re.match(r"DONE\s+(.+?\.mp4)\b", res); mc = re.match(r"DONE\s+(.+?/carousels/[^/\s]+)", res)
    if not (mv or mc): sys.exit(f"FAILED Task {tid} has no finished output ({(r.get('Status') or '').strip()})")
    item = Path(mv.group(1) if mv else mc.group(1))
    name = item.stem if mv else item.name
    root = item.parent.parent
    send = item if mv else item / "out" / "contact.png"
    if not send.is_file(): sys.exit(f"FAILED file not found: {send}")
    style = sheet.style_name(r.get("Style")) or "talking head edited"
    if mv:
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(item)],
                           capture_output=True, text=True).stdout.strip()
        length = f"{round(float(d))} s" if d else None
    else:
        length = f"{len(list((item / 'out').glob('slide-*.jpg')))} slides"
    label = opt(a, "--label")
    head = f"✅ Task {r['Task ID']}" + (f" ({label})" if label else "") + f", {style}, done"
    bits = [b for b in (length, opt(a, "--of")) if b]
    if any(s in style for s in SOURCED):
        src = source_of(r); bits.append(f"ref: {src}" if src else "ref: ⚠️ source link not found")
    lines = [" · ".join([head] + bits)]
    pc = root / "metadata" / f"{name}.post.json"
    if pc.is_file():
        c = json.loads(pc.read_text(encoding="utf-8"))
        lines += [f"**Title:** {c.get('title', '')}", f"**Caption:** {c.get('caption', '')}",
                  f"**Hashtags:** {' '.join(c.get('hashtags') or [])}"]
    elif "--allow-missing" in a:
        lines.append("⚠️ No post copy: the designer saved no title, caption or hashtags for this one.")
    elif not dry:
        sys.exit(f"NO_POST_COPY Task {r['Task ID']}: {pc} is missing. Have the row's designer write it (post-copy.md) "
                 f"before delivering, or pass --allow-missing for an output made before 2026-11-12.")
    else:
        lines.append("⚠️ NO_POST_COPY: a real delivery would stop here.")
    if opt(a, "--note"): lines.append(opt(a, "--note"))
    msg = "\n".join(lines)
    if here or dry:
        print(json.dumps({"file": str(send), "message": msg, "post_copy": pc.is_file()}, ensure_ascii=False)); return
    for args in (["reply", thread, "--thread", "--file", str(send)], ["reply", thread, "--thread", "--markdown", msg]):
        x = subprocess.run([sys.executable, str(LARK), *args], capture_output=True, text=True)
        if x.returncode: sys.exit(f"FAILED sending to Lark: {(x.stderr or x.stdout)[-300:]}")
    # the shared tracker (2026-11-19): the task is done, with its credits and the day it was delivered
    tracked = None
    track = Path(__file__).resolve().parent / "track.py"
    if track.is_file():
        cr = re.match(r"DONE\s+\S+.*?\s(\d+(?:\.\d+)?)(?:\s|$)", res.replace(str(item), "FILE"))
        args = ["set", r["Task ID"].lstrip("0"), "Status=done", "Done date=today"] + ([f"Credits={cr.group(1)}"] if cr else [])
        t = subprocess.run([sys.executable, str(track), *args], capture_output=True, text=True)
        tracked = t.returncode == 0 or (t.stderr or t.stdout).strip()[:200]
    print(json.dumps({"delivered": r["Task ID"], "thread": thread, "post_copy": pc.is_file(), "tracked": tracked}))

if __name__ == "__main__":
    main()
