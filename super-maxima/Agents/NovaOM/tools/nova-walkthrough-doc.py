"""Build a visual step-by-step Lark doc from a steps JSON (IN / OUT pictures per step).
Usage: nova-walkthrough-doc.py <steps.json> "<title>" <final video> [<detail doc url>]
A cell is {"label", "image"} | {"label", "video", "t"} | {"label", "note": true}; label starts with a unique "N.k" key."""
import html, json, re, shutil, subprocess, sys, time
from pathlib import Path
from PIL import Image
ROOT = Path("/Users/jefframirez/Super Nova"); V = ROOT / "_wt_vis"
spec, title, final = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
detail = sys.argv[4] if len(sys.argv) > 4 else None

def lark(*a):
    for i in range(6):
        r = subprocess.run(["lark-cli", "--profile", "super-nova", "docs", *a, "--as", "bot"], capture_output=True, text=True, cwd=ROOT)
        for src in (r.stdout, r.stderr):
            if "{" in src:
                try:
                    d = json.JSONDecoder().raw_decode(src[src.index("{"):])[0]
                    if d.get("ok"): return d
                except Exception: pass
        time.sleep(3 * (i + 1))
    raise SystemExit(f"failed: {a[:3]} {(r.stderr or r.stdout)[-400:]}")

def picture(cell, n, per_row):
    """A JPEG under _wt_vis/ for the cell, sized for its column; None for a note."""
    out = V / f"p{n:03d}.jpg"; maxw = {1: 1800, 2: 1400}.get(per_row, 900)
    if cell.get("video"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cell["t"]), "-i", cell["video"], "-frames:v", "1",
                        "-vf", f"scale='min({maxw},iw)':-2", str(out)], check=True)
    elif cell.get("image"):
        im = Image.open(cell["image"])
        if im.mode in ("RGBA", "LA", "P"):   # transparent logos and tiles go on white, not black
            im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.getchannel("A")); im = bg
        im = im.convert("RGB")
        if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
        im.save(out, quality=85)
    else: return None
    return out.relative_to(ROOT)

V.mkdir(exist_ok=True)
e = html.escape
intro = "Each step shows what went in (IN), the tool used, and what came out (OUT), in the order the designer worked."
if detail: intro += f' Exact prompts and commands are in the <a href="{e(detail)}">full written report</a>.'
xml = [f"<title>{e(title)}</title>", f"<p>{intro} The finished video is at the end.</p>"]
jobs, n = [], 0
for st in spec:
    xml.append(f"<h2>{e(st['heading'])}</h2>")
    xml += [f"<p>{e(l)}</p>" for l in st.get("lines", [])]
    for row in st.get("rows", []):
        w = 1 / len(row); cols = []
        for cell in row:
            n += 1; p = picture(cell, n, len(row))
            if p: jobs.append((cell["label"].split(" ")[0], p))
            cols.append(f'<column width-ratio="{w:.4f}"><p>{e(cell["label"])}</p></column>')
        xml.append("<grid>" + "".join(cols) + "</grid>")
keys = [k for k, _ in jobs]; assert len(keys) == len(set(keys)), "label keys must be unique"
(ROOT / "_wt_doc.xml").write_text("".join(xml))
d = lark("+create", "--content", "@_wt_doc.xml"); (ROOT / "_wt_doc.xml").unlink()
doc = d["data"]["document"]["document_id"]; url = d["data"]["document"]["url"]; print("doc", doc, url, flush=True)
full = lark("+fetch", "--doc", doc, "--detail", "with-ids")["data"]["document"]["content"]
missed = []
for key, p in jobs:
    mm = re.search(r'<p[^>]*\bid="([^"]+)"[^>]*>' + re.escape(key) + r' ', full)
    m = lark("+media-insert", "--doc", doc, "--file", str(p), "--type", "image")
    blk = (m.get("data") or {}).get("block_id")
    if mm and blk: lark("+update", "--doc", doc, "--command", "block_move_after", "--block-id", mm.group(1), "--src-block-ids", blk)
    else: missed.append(key)
lark("+media-insert", "--doc", doc, "--file", str(Path(final).resolve().relative_to(ROOT)), "--type", "file", "--file-view", "preview")
c = lark("+fetch", "--doc", doc, "--detail", "full")["data"]["document"]["content"]
cols = re.findall(r"<column[^>]*>(.*?)</column>", c, re.S)
print("pictures", len(jobs), "| in columns", sum(x.count("<img") for x in cols), "| outside", c.count("<img") - sum(x.count("<img") for x in cols),
      "| videos", re.findall(r'view-type="(\w+)"', c), "| missed", missed)
shutil.rmtree(V); print("done", doc, url)
