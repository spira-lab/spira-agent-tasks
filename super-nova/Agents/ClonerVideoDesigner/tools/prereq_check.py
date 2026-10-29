#!/usr/bin/env python3
"""Pre-requisite check for the Cloner video designer. Run before starting any clone:

  python3 "<super>/Agents/ClonerVideoDesigner/tools/prereq_check.py"

Prints PASS / WARN / FAIL per item with the fix, and the Python to run music_cut.py with
(MUSIC_PYTHON). Exit code 1 if anything FAILs. Read only: it installs nothing, creates no folder
and writes no file. Sign-in and credits are not checked here: the worker preflight covers them.
"""
import os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLONER = HERE.parent
SUPER = HERE.parents[2]
AGENTS = SUPER / "Agents"
SHARED = AGENTS / "DesignerShared"
PROJECT = SUPER / "Project"
CLIENT_ASSETS = AGENTS / "NovaOM" / "client-assets"

fails = warns = 0


def ok(msg): print(f"PASS  {msg}")


def warn(msg, fix):
    global warns; warns += 1
    print(f"WARN  {msg}\n      fix: {fix}")


def fail(msg, fix):
    global fails; fails += 1
    print(f"FAIL  {msg}\n      fix: {fix}")


def run(*cmd, timeout=60):
    try:
        r = subprocess.run(list(cmd), capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


print("== Media tools")
for t in ("ffmpeg", "ffprobe"):
    if shutil.which(t):
        ok(t)
    else:
        fail(f"{t} not installed", "install ffmpeg")
if shutil.which("yt-dlp"):
    ok("yt-dlp")
else:
    warn("yt-dlp not installed (not on the worker by default)",
         "download a source link with the ai tool's download action, or use the file the request supplies")
if shutil.which("ffmpeg") and "libvpx-vp9" in run("ffmpeg", "-hide_banner", "-decoders")[1]:
    ok("ffmpeg can decode VP9 with alpha (libvpx-vp9)")
else:
    warn("ffmpeg has no libvpx-vp9 decoder", "only needed to inspect Pixelcut cut-outs: an ffmpeg built with libvpx")
if shutil.which("whisper"):
    ok("whisper (make-timings fallback, lyrics mode, music_cut vocal starts)")
else:
    warn("whisper not installed", "only the fallback transcriber and lyrics mode need it: pip install openai-whisper")

print("== Python")
if sys.version_info >= (3, 9):
    ok(f"python3 {sys.version.split()[0]} (prereq_check, lyrics_check, shared tools)")
else:
    fail(f"python3 {sys.version.split()[0]} is too old", "Python 3.9 or newer")
music_py = None
cands = [os.environ.get("MUSIC_PYTHON"), os.environ.get("CLONER_PYTHON"),
         str(Path(__file__).resolve().parent.parent / ".music-venv" / "bin" / "python"),   # the Cloner's own, with librosa (2026-10-24)
         sys.executable,
         shutil.which("python3")] + [shutil.which(f"python3.{n}") for n in range(9, 16)]
seen = set()
for p in cands:
    if not p or p in seen:
        continue
    seen.add(p)
    if run(p, "-c", "import librosa, scipy, soundfile")[0] == 0:
        music_py = p
        break
if music_py:
    ok(f"music Python with librosa, scipy, soundfile: {music_py}")
else:
    warn("no Python with librosa, scipy and soundfile (music_cut.py cannot run)",
         "the owner installs them (python3 -m pip install --user librosa scipy soundfile) or sets MUSIC_PYTHON; "
         "until then generated music is fitted with the shared bgm-extend.py")

print("== Renderer (shared)")
if shutil.which("node"):
    ok(f"node {run('node', '--version')[1].strip()}")
else:
    fail("node not installed", "install Node.js")
render = SHARED / "tools" / "render"
for f, fix in ((render / "render-fast.js", "restore the shared renderer"),
               (SHARED / "tools" / "bgm-extend.py", "restore it one folder above the renderer")):
    (ok if f.exists() else (lambda m: fail(m, fix)))(f"{f.relative_to(SUPER)}")
if shutil.which("node") and run("node", "-e", "require('playwright-core')")[0] == 0:
    ok("playwright-core resolves with require('playwright-core')")
else:
    fail("require('playwright-core') does not resolve", "the global playwright-core module is missing on the worker; tell Nova")
chrome = os.environ.get("CHROME_PATH")
if chrome and os.access(chrome, os.X_OK):
    ok(f"Chromium at CHROME_PATH ({chrome})")
elif shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome"):
    ok("Chromium on PATH (renderer and capture_site.js)")
else:
    fail("Chromium not found", "set CHROME_PATH to the chromium binary (/usr/bin/chromium)")

print("== Shared designer files")
for rel in ("stage/stage-9x16.html", "tools/chunker.py", "tools/make-timings.py",
            "skills/file-management.md", "skills/toolkit.md", "skills/prompting.md",
            "skills/stage-canvas-html.md", "skills/rendering.md", "skills/known-methods.md",
            "skills/working-memory.md", "music"):
    f = SHARED / rel
    (ok if f.exists() else (lambda m: fail(m, "restore it; tell Nova")))(f"DesignerShared/{rel}")
f = AGENTS / "AvatarDesigner" / "skills" / "avatar-designer.md"
(ok if f.exists() else (lambda m: fail(m, "restore it; tell Nova")))("AvatarDesigner/skills/avatar-designer.md (persona method)")

print("== This designer")
for rel in ("skills/cloner-video-designer.md", "references/cloningtoolkit.md",
            "references/clonerfilemanagement.md", "references/cloner-lessons.md",
            "references/source-understanding-workflow.json",
            "tools/music_cut.py", "tools/lyrics_check.py", "tools/capture_site.js"):
    f = CLONER / rel
    (ok if f.exists() else (lambda m: fail(m, "restore it; tell Nova")))(f"ClonerVideoDesigner/{rel}")

print("== Folders")
if PROJECT.is_dir() and os.access(PROJECT, os.W_OK):
    ok(f"Project folder writable: {PROJECT}")
else:
    fail(f"can't write to {PROJECT}", "Nova checks the build folder (this check creates nothing)")
if CLIENT_ASSETS.is_dir():
    ok(f"client assets: {CLIENT_ASSETS.relative_to(SUPER)} (personas are saved in <BrandName>/personas/)")
else:
    fail(f"{CLIENT_ASSETS} missing", "tell Nova")

print()
print(f"MUSIC_PYTHON={music_py or 'none'}")
print(f"result: {fails} fail(s), {warns} warning(s)")
sys.exit(1 if fails else 0)
