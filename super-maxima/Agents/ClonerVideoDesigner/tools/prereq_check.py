#!/usr/bin/env python3
"""Pre-requisite check for the Cloner video designer. Run before starting any clone:

  python3 "<super>/Agents/ClonerVideoDesigner/tools/prereq_check.py"

Prints PASS / WARN / FAIL per item with the fix, and the Python to run music_cut.py with
(MUSIC_PYTHON). Exit code 1 if anything FAILs. Read only: it installs nothing, creates no folder
and writes no file. It never reads the credit balance to measure spend (the account is shared);
the balance is shown only so you know there is enough to work with.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLONER = HERE.parent
SUPER = HERE.parents[2]
AGENTS = SUPER / "Agents"
SHARED = AGENTS / "DesignerShared"
PROJECT = SUPER / "Project"
CLIENT_ASSETS = AGENTS / "NovaOM" / "client-assets"

MODELS = ["ai-influencer-image", "gpt-image-2", "wan-3.0", "kling-3.0-motion-control",
          "gemini-omni-flash-1.1", "seedance-1.5-pro", "suno-music",
          "pixelcut-video-background-removal", "elevenlabs-text-to-speech", "elevenlabs-sound-effects"]

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


def spira_json(*args):
    code, out = run("spira", "--json", *args)
    try:
        start = out.index("{")
        return code, json.loads(out[start:], strict=False)
    except ValueError:
        return code, {}


print("== Spira")
if shutil.which("spira"):
    ok(f"Spira CLI {run('spira', '--version')[1].strip()}")
    code, d = spira_json("credits", "balance")
    data = d.get("data") or {}
    bal = data.get("availableCredits", data.get("balance"))
    if code == 0 and bal is not None:
        ok(f"signed in, {bal} credits available on the shared account (not a measure of this run's spend)")
    else:
        fail("Spira not signed in (or the sign-in expired)", "the user runs: spira auth login")
    for m in MODELS:
        if run("spira", "--json", "ai", "models", "get", m)[0] == 0:
            ok(f"model {m}")
        else:
            fail(f"model {m} not available", "check 'spira --json ai models list' for a renamed id and tell Nova")
    if run("spira", "workflows", "--help")[0] == 0:
        ok("spira workflows (understand_source.py creates one workflow per run, named with the Task ID)")
    else:
        fail("spira workflows command missing", "update the Spira CLI: npm install -g @spira-lab/cli")
else:
    fail("Spira CLI not installed", "npm install -g @spira-lab/cli")

print("== Media tools")
for t in ("yt-dlp", "ffmpeg", "ffprobe"):
    if shutil.which(t):
        ok(t)
    else:
        fail(f"{t} not installed", f"brew install {'ffmpeg' if t == 'ffprobe' else t}")
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
    ok(f"python3 {sys.version.split()[0]} (prereq_check, understand_source, lyrics_check, shared tools)")
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
               (render / "node_modules" / "playwright-core", "npm install in Agents/DesignerShared/tools/render (ask Nova)"),
               (SHARED / "tools" / "bgm-extend.py", "restore it one folder above the renderer")):
    (ok if f.exists() else (lambda m: fail(m, fix)))(f"{f.relative_to(SUPER)}")
chrome = os.environ.get("CHROME_PATH")
if chrome and os.access(chrome, os.X_OK):
    ok("Chrome at CHROME_PATH")
elif Path("/Applications/Google Chrome.app").exists():
    ok("Google Chrome installed (renderer and capture_site.js)")
else:
    fail("Google Chrome not found", "install Google Chrome, or set CHROME_PATH to a Chrome binary")

print("== Shared designer files")
for rel in ("stage/stage-9x16.html", "tools/chunker.py", "tools/make-timings.py", "tools/spira-jobs.py",
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
            "references/source-understanding-workflow.json", "tools/understand_source.py",
            "tools/music_cut.py", "tools/lyrics_check.py", "tools/capture_site.js"):
    f = CLONER / rel
    (ok if f.exists() else (lambda m: fail(m, "restore it; tell Nova")))(f"ClonerVideoDesigner/{rel}")

print("== Folders")
if PROJECT.is_dir() and os.access(PROJECT, os.W_OK):
    ok(f"Project folder writable: {PROJECT}")
else:
    fail(f"can't write to {PROJECT}", "Nova checks the build folder (this check creates nothing)")
if CLIENT_ASSETS.is_dir():
    ok(f"client assets: {CLIENT_ASSETS.relative_to(SUPER)} (anchor sheets and persona records in <BrandName>/personas/; persona images stay in the project)")
else:
    fail(f"{CLIENT_ASSETS} missing", "tell Nova")

print()
print(f"MUSIC_PYTHON={music_py or 'none'}")
print(f"result: {fails} fail(s), {warns} warning(s)")
sys.exit(1 if fails else 0)
