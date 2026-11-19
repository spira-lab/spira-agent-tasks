"""Puts a finished video into a Lark doc right after its source line, as Nova's bot (2026-11-12):
    python3 nova-doc-output.py <doc url> <source block id> <Task ID> <render path> [--video] [--label "<extra label, e.g. Carousel 1 slide 3>"]
Uploads the render to Spira for a public link, then inserts after the block:
a line "✅ Output · Task <id>: <link>"; with --video also the video as a playable preview.
--video embeds the playable file too (the doc media upload scope was added 2026-11-12): use it by default. Inserts once, never retried: a retry
after a partial insert duplicated the link line (2026-11-12)."""
import html, json, re, subprocess, sys, time
from pathlib import Path
doc, bid, task, render = sys.argv[1:5]
render = Path(render).resolve()
u = subprocess.run(["spira", "--json", "assets", "upload", str(render)], capture_output=True, text=True)
m = re.search(r'"url":\s*"(https://[^"]+)"', u.stdout)
url = m.group(1) if m else None
if not url:
    sys.exit("spira upload failed: " + (u.stderr or u.stdout)[-300:])
e = html.escape(url, quote=True)
extra = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
name = f"Task {task} · {html.escape(extra)}" if extra else f"Task {task}"
xml = f'<p><b>✅ Output · {name}</b>: <a href="{e}">{e}</a></p>'
if "--video" in sys.argv:
    xml += f'<figure view-type="Preview"><source path="@./{render.name}" name="{render.name}"/></figure>'
for i in range(5):   # retry only a call that wrote nothing (e.g. 429 rate limit)
    r = subprocess.run(["lark-cli", "--profile", "super-nova", "docs", "+update", "--doc", doc, "--command", "block_insert_after",
                        "--block-id", bid, "--content", xml, "--as", "bot"], capture_output=True, text=True, cwd=render.parent)
    out = r.stdout + r.stderr
    d = json.loads(out[out.index("{"):]) if "{" in out else {}
    data = d.get("data") or {}
    if (data.get("document") or {}).get("new_blocks") or data.get("result") == "success":
        fails = data.get("local_resource_failures") or []
        print(json.dumps({"ok": not fails, "task": task, "link": url, "video_failed": [f.get("error") for f in fails]})); break
    time.sleep(8 * (i + 1))
else:
    sys.exit("doc insert failed: " + out[-400:])
