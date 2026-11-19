#!/usr/bin/env python3
"""Hermes's upload tool. Uploads finished videos (and carousels) from a batch sheet into Spira's
Social Post Assets library, tagged from Hermes's working memory. Uploading and tagging only: it
never creates posts, drafts, or schedules, and never creates tags.

  python3 "<hermes>/tools/hermes-upload.py" --sheet <batch sheet> --tasks <11,12,... | done>
          --brand "<brand>" [--product "<product name>"] [--tag <tag id>] [--dry-run]

For each Task ID (or every done row with "done"):
  - the row must be done; its render path comes from the row's Result (DONE <render path> ...)
  - a carousel row (Result DONE <carousel folder> ..., any carousel style, 2026-10-27): the slide JPEGs in the
    folder's out/ (slide-01.jpg, slide-02.jpg, ...) go up together as ONE album asset, in slide order, with the
    carousel tag (Spira CLI 0.0.31, 2026-10-30), and the carousel is recorded once in the upload log; the
    contact sheet and notes are never uploaded
  - the tag comes from docs/hermes-working-memory.md, per kind (2026-10-29): video rows use the
    tag For "videos", carousel rows the tag For "carousels", either falling back to a row For both
    (For empty); a row for the kind wins, then the product's row over the brand's. Each tag the
    batch needs is checked against Spira's tag list before anything is uploaded
  - a Spiraverse row (its Instructions start with "[Spiraverse: <Name> ...", 2026-11-12) goes up under that
    persona's own tag in Spira Character, from Nova's persona index, whatever the brand's tag is
  - an Emochi persona row (its Instructions start with "[Emochi persona: <Name> ...", 2026-11-19) goes up under
    that persona's own tag in the Emochi category, from client-assets/Emochi/emochi-personas.json
  - --tag <tag id>: a one-off tag for this run only (named by the owner or Jekylle for this
    batch), used for every row instead of the working memory; checked against Spira the same way
  - a video or carousel already uploaded (same file or folder, same size, same tag) is skipped; docs/hermes-upload-log.json
    records every upload with what Spira returned; an upload Spira gives no asset ID counts as
    failed and is not recorded, so a rerun tries it again
  - post copy (the owner's rule, 2026-11-12): when the designer saved Project/<Brand>/metadata/<name>.post.json
    (DesignerShared/tools/post-copy.py), its title goes up as --title and its caption plus hashtags as
    --description, so Spira posts that copy as written; without the file the upload goes up as before
--dry-run checks everything and prints what would be uploaded, uploading nothing.

Prints one JSON line per video, then one summary line.
"""
import fcntl, importlib.util, json, re, shutil, subprocess, sys, tempfile
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

def spira(*args):
    r = subprocess.run(["spira", "--json", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        d = None
    if r.returncode != 0 or d is None or str(d.get("status", "")).lower() == "error":
        raise RuntimeError((r.stderr or r.stdout).strip()[-400:] or f"spira {' '.join(args[:3])} failed")
    return d

def asset_id(d):
    """The asset ID Spira gave the upload, or None; an upload without one did not land."""
    return ((d.get("data") or {}).get("asset") or {}).get("assetId")

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

SPIRAVERSE = SUPER / "Agents" / "NovaOM" / "client-assets" / "Spira" / "spiraverse" / "spiraverse.json"

EMOCHI = SUPER / "Agents" / "NovaOM" / "client-assets" / "Emochi" / "emochi-personas.json"

def persona_tag(row):
    """A Spiraverse row (Instructions start with "[Spiraverse: <Name> ...", 2026-11-12) goes up under its own
    persona's tag in Spira Character, never the brand's: returns ("Spira Character / <Name>", tag id), or None.
    An Emochi persona row ("[Emochi persona: <Name> ...", 2026-11-19) goes up under its persona's tag in Emochi."""
    e = re.match(r"\[Emochi persona:\s*([^\s(]+)", row.get("Instructions") or "")
    if e:
        try: idx = json.loads(EMOCHI.read_text(encoding="utf-8"))["personas"]
        except (OSError, json.JSONDecodeError, KeyError): idx = []
        p = next((p for p in idx if p["name"].lower() == e.group(1).lower()), None)
        return ("Emochi / " + e.group(1), p.get("tag_id") if p else None)
    m = re.match(r"\[Spiraverse:\s*([^\s(]+)", row.get("Instructions") or "")
    if not m: return None
    try:
        idx = json.loads(SPIRAVERSE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ("Spira Character / " + m.group(1), None)
    acc = next((a for g in idx["groups"] for a in g["accounts"] if a["name"].lower() == m.group(1).lower()), None)
    return ("Spira Character / " + m.group(1), acc.get("tag_id") if acc else None)

def post_copy(item):
    """The designer's post copy for a render or carousel folder (the owner's rule, 2026-11-12):
    Project/<Brand>/metadata/<name>.post.json, written by DesignerShared/tools/post-copy.py.
    Returns the upload args (--title, --description) and a short label, or ([], None) when there is none."""
    name = item.stem if item.suffix else item.name
    f = item.parent.parent / "metadata" / f"{name}.post.json"
    if not f.is_file(): return [], None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], None
    caption = (d.get("caption") or "").strip()
    tags = " ".join(h for h in (d.get("hashtags") or []) if isinstance(h, str) and h.startswith("#"))
    desc = (caption + ("\n\n" + tags if tags else "")).strip()[:2200]
    if not desc: return [], None
    args = ["--description", desc]
    title = (d.get("title") or "").strip()[:90]
    if title: args = ["--title", title] + args   # the CLI takes a title only with a description
    return args, title or caption[:40]

def slides_of(folder):
    """The slide JPEGs in order: out/slide-01.jpg, slide-02.jpg, ..."""
    return sorted((folder / "out").glob("slide-*.jpg"), key=lambda f: int(re.sub(r"\D", "", f.stem) or 0))

def main():
    a = sys.argv[1:]
    sheet, tasks, brand = opt(a, "--sheet"), opt(a, "--tasks"), opt(a, "--brand")
    product, dry = opt(a, "--product"), "--dry-run" in a
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

    # the tag for each kind of row in this batch: videos and carousels can have different tags
    personas = {r["Task ID"]: persona_tag(r) for r in picked if persona_tag(r)}
    lost = [f"{tid} ({lt[0]})" for tid, lt in personas.items() if not lt[1]]
    if lost: sys.exit(f"QUESTION no Spira tag recorded for the persona of: {', '.join(lost)}")
    kinds = {"carousels" if (not render_of(r) and carousel_of(r)) else "videos"
             for r in picked if norm(r.get("Status")) == "done" and r["Task ID"] not in personas}
    if not kinds and not personas: kinds = {"videos"}
    tag = {}
    for kind in sorted(kinds, reverse=True):
        lt = (one_off, one_off) if one_off else tag_for(brand, product, kind)
        if not lt[1]:
            sys.exit(f"QUESTION no upload tag for {kind} in Hermes's working memory for {brand}" + (f" / {product}" if product else ""))
        tag[kind] = lt
    try:
        tags = spira("social", "assets", "tags")
    except RuntimeError as e:
        sys.exit(f"FAILED cannot read Spira's tags: {e}")
    def text(v):  # names come as plain text or {"en": ..., "zh": ...}
        if isinstance(v, dict): v = v.get("en") or v.get("name") or next(iter(v.values()), "")
        return v if isinstance(v, str) else ""
    for kind, (label, tag_id) in tag.items():
        match = next((t for t in (tags.get("data") or {}).get("items", []) if t.get("id") == tag_id), None)
        if not match:
            sys.exit(f"QUESTION the tag {label} ({tag_id}) is " + ("not in Spira" if one_off else "no longer in Spira"))
        if one_off:
            cat = text(match.get("category") or match.get("categoryName"))
            name = text(match.get("name")) or tag_id
            tag[kind] = (f"{cat} / {name}" if cat else name, tag_id)

    spira_ids = {t.get("id") for t in (tags.get("data") or {}).get("items", [])}
    gone = [f"{tid} ({lt[0]})" for tid, lt in personas.items() if lt[1] not in spira_ids]
    if gone: sys.exit(f"QUESTION the persona tag is no longer in Spira for: {', '.join(gone)}")
    for tid, lt in personas.items():
        for kind in ("videos", "carousels"): tag.setdefault(kind, lt)   # placeholder so the label lines below never fail
    LOG.parent.mkdir(parents=True, exist_ok=True); LOG.touch(exist_ok=True)
    done = skipped = 0; problems = []; carousels = slides_up = 0
    with open(LOG, "r+") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        raw = lf.read().strip(); log = json.loads(raw) if raw else {}
        for r in picked:
            tid = r["Task ID"]
            if norm(r.get("Status")) != "done":
                problems.append(f"{tid} not done ({r.get('Status') or 'pending'})"); continue
            folder = None if render_of(r) else carousel_of(r)
            if folder:
                # a carousel: every slide JPEG, in order, as one image each with the carousel tag
                if not folder.is_dir():
                    problems.append(f"{tid} carousel folder not found"); continue
                if not folder.resolve().is_relative_to(PROJECT):
                    problems.append(f"{tid} carousel outside Project/"); continue
                slides = slides_of(folder)
                if not slides:
                    problems.append(f"{tid} carousel has no slides in out/"); continue
                label, tag_id = personas.get(tid) or tag["carousels"]
                key = str(folder); size = sum(s.stat().st_size for s in slides)
                prev = log.get(key)
                if prev and prev.get("size") == size and prev.get("tag_id") == tag_id:
                    skipped += 1
                    print(json.dumps({"task_id": tid, "carousel": folder.name, "skipped": "already uploaded"})); continue
                if dry:
                    print(json.dumps({"task_id": tid, "carousel": folder.name, "slides": len(slides), "tag": label, "post_copy": post_copy(folder)[1], "dry_run": True}))
                    carousels += 1; slides_up += len(slides); continue
                # one album per carousel (Spira CLI 0.0.31, 2026-10-30): the CLI posts a folder's images in
                # filename order, so only the slides are staged; out/ also holds the contact sheet
                with tempfile.TemporaryDirectory() as tmp:
                    album = Path(tmp) / folder.name; album.mkdir()
                    for s in slides: shutil.copy2(s, album / s.name)
                    try:
                        pargs, plabel = post_copy(folder)
                        d = spira("social", "assets", "upload", str(album), "--tag", tag_id, *pargs)
                    except RuntimeError as e:
                        problems.append(f"{tid} carousel upload failed: {e}"); continue
                if not asset_id(d):   # not logged, so a rerun tries it again
                    problems.append(f"{tid} carousel upload failed: Spira returned no asset ID"); continue
                log[key] = {"task_id": tid, "brand": brand, "product": product, "tag": label, "tag_id": tag_id,
                            "size": size, "carousel": str(folder), "slides": len(slides), "post_copy": plabel,
                            "uploaded": datetime.now().isoformat(timespec="minutes"), "spira": d.get("data") or {}}
                lf.seek(0); lf.truncate(); lf.write(json.dumps(log, indent=1, ensure_ascii=False) + "\n"); lf.flush()
                carousels += 1; slides_up += len(slides)
                print(json.dumps({"task_id": tid, "carousel": folder.name, "slides": len(slides), "tag": label, "post_copy": plabel}))
                track = Path(__file__).resolve().parents[2] / "NovaOM" / "tools" / "track.py"   # the shared tracker (2026-11-19)
                if track.is_file():
                    subprocess.run([sys.executable, str(track), "set", str(tid).lstrip("0"), "Status=uploaded"],
                                   capture_output=True, text=True)
                continue
            render = render_of(r)
            label, tag_id = personas.get(tid) or tag["videos"]
            if not render or not render.is_file():
                problems.append(f"{tid} render not found"); continue
            if not render.resolve().is_relative_to(PROJECT):
                problems.append(f"{tid} render outside Project/"); continue
            key = str(render)
            prev = log.get(key)
            if prev and prev.get("size") == render.stat().st_size and prev.get("tag_id") == tag_id:
                skipped += 1
                print(json.dumps({"task_id": tid, "video": render.name, "skipped": "already uploaded"})); continue
            if dry:
                print(json.dumps({"task_id": tid, "video": render.name, "tag": label, "post_copy": post_copy(render)[1], "dry_run": True}))
                done += 1; continue
            pargs, plabel = post_copy(render)
            args = ["social", "assets", "upload", str(render), "--tag", tag_id, *pargs]
            try:
                d = spira(*args)
            except RuntimeError as e:
                problems.append(f"{tid} upload failed: {e}"); continue
            if not asset_id(d):   # not logged, so a rerun tries it again
                problems.append(f"{tid} upload failed: Spira returned no asset ID"); continue
            data = d.get("data") or {}
            log[key] = {"task_id": tid, "brand": brand, "product": product, "tag": label, "tag_id": tag_id,
                        "size": render.stat().st_size, "post_copy": plabel,
                        "uploaded": datetime.now().isoformat(timespec="minutes"), "spira": data}
            lf.seek(0); lf.truncate(); lf.write(json.dumps(log, indent=1, ensure_ascii=False) + "\n"); lf.flush()
            done += 1
            print(json.dumps({"task_id": tid, "video": render.name, "tag": label, "post_copy": plabel}))
            track = Path(__file__).resolve().parents[2] / "NovaOM" / "tools" / "track.py"   # the shared tracker (2026-11-19)
            if track.is_file():
                subprocess.run([sys.executable, str(track), "set", str(tid).lstrip("0"), "Status=uploaded"],
                               capture_output=True, text=True)
    verb = "WOULD UPLOAD" if dry else "UPLOADED"
    vids = f"{done} videos" if done or not carousels else ""
    cars = f"{carousels} carousel{'s' if carousels != 1 else ''} ({slides_up} slides)" if carousels else ""
    vlabel = tag.get("videos", (None,))[0]; clabel = tag.get("carousels", (None,))[0]
    if personas:   # Spiraverse rows each went under their own persona's tag
        used = sorted({lt[0] for lt in personas.values()} | ({vlabel} if kinds & {"videos"} else set()) | ({clabel} if kinds & {"carousels"} else set()))
        vlabel = clabel = ", ".join(x for x in used if x)
    if vids and cars and vlabel != clabel:
        line = f"{verb} {vids} tag {vlabel} and {cars} tag {clabel}"
    else:
        line = f"{verb} {' and '.join(x for x in (vids, cars) if x)} tag {vlabel or clabel}"
    if skipped: line += f"; {skipped} already uploaded"
    if problems: line += f"; problems: {'; '.join(problems)}"
    print(line)
    sys.exit(1 if problems and not done and not slides_up and not skipped else 0)

if __name__ == "__main__":
    main()
