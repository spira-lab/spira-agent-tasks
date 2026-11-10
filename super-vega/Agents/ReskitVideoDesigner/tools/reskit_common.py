"""Shared helpers for the Re-skit designer's tools: where things are, a video's names, the
metadata file, the editable page. Imported by reskit.py and build_edit.py
(all in this folder); never run on its own.

Layout (the shared file-management skill, exactly):
  Project/<BrandName>/editable/NN-name-MM-DD.html            the editable (a page that lists the build)
  Project/<BrandName>/editable/materials/NN-name-MM-DD/      everything the build uses
  Project/<BrandName>/renders/NN-name-MM-DD.mp4              the final video
  Project/<BrandName>/metadata/NN-name-MM-DD.json            every job, prompt, credit, lesson
Brand-level files that must survive backups:
  Agents/VegaOM/client-assets/<BrandName>/personas/<Name>/ and .../brand/
"""
import fcntl, hashlib, html, json, re, shutil, subprocess, sys, tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent                  # <super>/Agents/ReskitVideoDesigner/tools
RESKIT = TOOLS.parent
AGENTS = RESKIT.parent
SUPER = AGENTS.parent
PROJECT = SUPER / "Project"
SHARED = AGENTS / "DesignerShared"
CLIENT_ASSETS = AGENTS / "VegaOM" / "client-assets"
PLAYWRIGHT = SHARED / "tools" / "render" / "node_modules" / "playwright-core"
sys.path.insert(0, str(SHARED / "tools"))
import profile as scratch_profile   # redirects tempfile to the scratch root
MAKE_TIMINGS = SHARED / "tools" / "make-timings.py"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"   # the asset CDN refuses Python's default agent

MATERIAL_DIRS = ["source", "assets", "gen/ref", "gen/out", "music", "deletable"]


def brand_key(brand):
    """'Glow Lab Co.' -> 'GlowLabCo' (spaces and special characters removed, case kept)."""
    k = re.sub(r"[^A-Za-z0-9]", "", brand or "")
    return k or "Brandless"


def slug(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (text or "").lower())).strip("-")


def video_name(brand, task_id, date=None, topic=None):
    nn = str(int(str(task_id).strip())).zfill(2)
    key = brand_key(brand)
    word = slug(topic) if key == "Brandless" else key.lower()
    if not word:
        raise SystemExit("a Brandless video needs --topic (two to four words)")
    return f"{nn}-{word}-{date or datetime.now().strftime('%m-%d')}"


class Video:
    """A video's paths, found from its materials folder, its edit.json, or its editable."""

    def __init__(self, any_path):
        p = Path(any_path).expanduser().resolve()
        if p.is_file():
            if p.suffix == ".html" and p.parent.name == "editable":
                p = p.parent / "materials" / p.stem
            else:
                p = p.parent
        # walk up to <root>/editable/materials/<name>
        while p.parent.name != "materials" or p.parent.parent.name != "editable":
            if p == p.parent:
                raise SystemExit(f"{any_path} is not inside a video's materials folder (<root>/editable/materials/<name>/)")
            p = p.parent
        self.materials = p
        self.name = p.name
        self.root = p.parent.parent.parent
        self.brand = self.root.name
        self.editable = self.root / "editable" / f"{self.name}.html"
        self.metadata = self.root / "metadata" / f"{self.name}.json"
        self.render = self.root / "renders" / f"{self.name}.mp4"
        self.render_deletable = self.root / "renders" / "deletable"
        self.edit_json = p / "edit.json"
        self.plan = p / "plan.md"


# ---------------------------------------------------------------- metadata
@contextmanager
def locked(path):
    """An exclusive lock for one file, kept in the system temp folder (never beside the file,
    so no lock files land in the brand folder)."""
    key = hashlib.sha1(str(Path(path).resolve()).encode()).hexdigest()[:16]
    with open(Path(scratch_profile.OS_TEMP) / f"reskit-{key}.lock", "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        yield


def read_meta(v):
    try:
        return json.loads(v.metadata.read_text())
    except (OSError, ValueError):
        return {}


def update_meta(v, fn):
    """Read-modify-write the metadata file under a lock (the build writes it, and the agent edits it by hand while jobs land)."""
    with locked(v.metadata):
        d = read_meta(v)
        fn(d)
        v.metadata.parent.mkdir(parents=True, exist_ok=True)
        tmp = v.metadata.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
        tmp.replace(v.metadata)
        return d


def to_deletable(path, folder):
    """Move a file into a deletable/ folder, keeping its name (_2, _3 on a collision)."""
    path, folder = Path(path), Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / path.name
    k = 2
    while dest.exists():
        dest = folder / f"{path.stem}_{k}{path.suffix}"; k += 1
    shutil.move(str(path), str(dest))
    return dest


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


# ---------------------------------------------------------------- media helpers
def ffprobe_json(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate:stream_disposition=attached_pic",
                        "-of", "json", str(path)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {}


def duration(path):
    try:
        return float(ffprobe_json(path)["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        return 0.0


def loudness(path):
    """Integrated loudness (LUFS) and true peak (dBTP) of a file's audio, with ffmpeg ebur128."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[0-9.]+|-inf) LUFS", r.stderr)
    tp = re.findall(r"Peak:\s+(-?[0-9.]+|-inf) dBFS", r.stderr)
    f = lambda s: float("-inf") if s == "-inf" else float(s)
    return (f(i[-1]) if i else None), (f(tp[-1]) if tp else None)


def scene_changes(path, threshold=0.3):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "info", "-i", str(path), "-an", "-vf",
                        f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"], capture_output=True, text=True)
    return [round(float(t), 3) for t in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


# ---------------------------------------------------------------- the editable page
def write_editable(v, edit=None, note=""):
    """The editable is a small HTML page: what the build is, where its build file is, and the
    command that rebuilds it. It embeds the build file so the page alone shows every decision.
    It is rewritten by every build; never edit it by hand (edit edit.json instead)."""
    edit = edit if edit is not None else (json.loads(v.edit_json.read_text()) if v.edit_json.exists() else {})
    meta = read_meta(v)
    rows = []
    for i, s in enumerate(edit.get("segments", []), 1):
        if "insert" in s:
            rows.append(f"<tr><td>{i}</td><td>insert</td><td>{html.escape(str(s['insert']))}</td><td>{s.get('dur', '')} s</td></tr>")
        else:
            rows.append(f"<tr><td>{i}</td><td>clip {html.escape(str(s.get('clip')))}</td>"
                        f"<td>source {s.get('from')}–{s.get('to')} s</td><td>{'zoom' if s.get('zoom') else ''}</td></tr>")
    ovs = "".join(f"<tr><td>{html.escape(str(o.get('png')))}</td><td>{html.escape(str(o.get('in')))}</td>"
                  f"<td>{html.escape(str(o.get('out')))}</td><td>{html.escape(str(o.get('kind', 'full')))}</td></tr>"
                  for o in edit.get("overlays", []))
    build = f'python3 "{TOOLS / "build_edit.py"}" "{v.edit_json}"'
    embedded = json.dumps(edit, ensure_ascii=False).replace("</", "<\\/")
    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="reskit-video-designer">
<title>{html.escape(v.name)}</title>
<style>
 body {{ font: 14px/1.45 Arial, sans-serif; margin: 24px; color: #111; background: #fff; max-width: 960px; }}
 code {{ background: #f2f2f2; padding: 2px 5px; border-radius: 4px; }}
 table {{ border-collapse: collapse; margin: 8px 0 20px; }} td, th {{ border: 1px solid #ddd; padding: 4px 8px; text-align: left; }}
 .note {{ color: #555; }}
</style></head>
<body>
<h1>{html.escape(v.name)}</h1>
<p class="note">Re-skit editable. This page is not a stage and is not rendered with render-fast.js.
The video is built from its build file by the Re-skit build tool; this page is rewritten on every build.</p>
<p><b>Brand:</b> {html.escape(v.brand)} &nbsp; <b>Task ID:</b> {html.escape(str(meta.get('task_id', '')))} &nbsp;
<b>Source:</b> {html.escape(str((meta.get('source') or {}).get('link', '')))}</p>
<p><b>Story:</b> {html.escape(str(meta.get('story', '')))}</p>
<p><b>Build file:</b> <code>materials/{html.escape(v.name)}/edit.json</code><br>
<b>Plan:</b> <code>materials/{html.escape(v.name)}/plan.md</code><br>
<b>Rebuild a draft:</b> <code>{html.escape(build)} draft</code><br>
<b>Final render:</b> <code>{html.escape(build)} final</code></p>
<h2>Segments</h2><table><tr><th>#</th><th>kind</th><th>what</th><th></th></tr>{''.join(rows)}</table>
<h2>Overlays</h2><table><tr><th>png</th><th>in</th><th>out</th><th>kind</th></tr>{ovs}</table>
<p class="note">{html.escape(note)}</p>
<script type="application/json" id="reskit-edit">{embedded}</script>
</body></html>
"""
    v.editable.parent.mkdir(parents=True, exist_ok=True)
    v.editable.write_text(page, encoding="utf-8")
    return v.editable
