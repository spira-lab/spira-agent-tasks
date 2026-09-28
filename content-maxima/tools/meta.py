#!/usr/bin/env python3
"""Keeps metadata/<name>.json. Every write to it goes through here; never edit it by hand.

  python3 tools/meta.py asset   <file> --tool <model or process> --prompt <text> [--url <url>] [--job <id>] [--source <file>]
  python3 tools/meta.py move    <file> [--by <file that replaces it>]    # into deletable/, entry updated
  python3 tools/meta.py render  <render.mp4> --fps 30 --duration-ms 29140
  python3 tools/meta.py publish <render.mp4> --tag <name> --asset-id <id> --url <url>
  python3 tools/meta.py check   <editable.html | render | any file of the video>

The video a file belongs to is read from its path: editable/materials/<name>/...,
editable/<name>.html, renders/<name>.mp4 or metadata/<name>.json, under the root.
Writes are locked, so parallel generations can record at the same time.
"""
import argparse, datetime, fcntl, json, os, pathlib, re, shutil, sys


def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")


def locate(file):
    """(root, name) for any file of a video."""
    p = pathlib.Path(file).resolve()
    parts = p.parts
    for i, part in enumerate(parts):
        if part == "editable" and i + 2 < len(parts) and parts[i + 1] == "materials":
            return pathlib.Path(*parts[:i]), parts[i + 2]
        if part == "editable" and i + 1 == len(parts) - 1:
            return pathlib.Path(*parts[:i]), re.sub(r"\.html?$", "", p.name)
        if part in ("renders", "metadata") and i + 1 <= len(parts) - 1:
            stem = p.stem.split("_")[0] if part == "renders" else p.stem
            return pathlib.Path(*parts[:i]), re.sub(r"\.cover$", "", stem)
    sys.exit(f"meta: cannot tell which video {file} belongs to")


class Meta:
    """Open metadata/<name>.json under an exclusive lock; saved on exit."""

    def __init__(self, file):
        self.root, self.name = locate(file)
        self.path = self.root / "metadata" / f"{self.name}.json"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = open(str(self.path) + ".lock", "w")
        fcntl.flock(self.lock, fcntl.LOCK_EX)
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            mat = self.root / "editable" / "materials" / self.name
            script = mat / "script.txt"
            self.data = {
                "root": str(self.root), "name": self.name,
                "created": datetime.date.today().isoformat(),
                "editable": str(self.root / "editable" / f"{self.name}.html"),
                "script": {"file": str(script), "text": script.read_text().strip() if script.exists() else None},
                "assets": [], "renders": [],
            }
        return self.data

    def __exit__(self, *exc):
        if exc[0] is None:
            script = pathlib.Path(self.data["script"]["file"])
            if not self.data["script"].get("text") and script.exists():
                self.data["script"]["text"] = script.read_text().strip()
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n")
            os.replace(tmp, self.path)
        fcntl.flock(self.lock, fcntl.LOCK_UN)
        self.lock.close()


def record_asset(file, tool, prompt, url=None, job=None, source=None):
    file = str(pathlib.Path(file).resolve())
    with Meta(file) as m:
        m["assets"] = [a for a in m["assets"] if a["file"] != file]
        m["assets"].append({"file": file, "status": "in-use", "tool": tool, "prompt": prompt,
                            "source": source, "url": url, "job": job, "generated": now(), "replaced_by": None})


def free_name(folder, name):
    target = folder / name
    n = 2
    while target.exists():
        target = folder / f"{pathlib.Path(name).stem}_{n}{pathlib.Path(name).suffix}"
        n += 1
    return target


def move_to_deletable(file, by=None):
    src = pathlib.Path(file).resolve()
    if not src.exists():
        sys.exit(f"meta: {src} does not exist")
    root, name = locate(src)
    if src.parent.name == "renders":
        stamp = datetime.datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y%m%d-%H%M")
        folder = src.parent / "deletable"
        target = free_name(folder, f"{src.stem}_{stamp}{src.suffix}")
    else:
        folder = root / "editable" / "materials" / name / "deletable"
        target = free_name(folder, src.name)
    folder.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(target))
    with Meta(src) as m:
        for entry in m["assets"] + m["renders"]:
            if entry["file"] == str(src):
                entry["file"] = str(target)
                entry["status"] = "deletable"
                if by:
                    entry["replaced_by"] = str(pathlib.Path(by).resolve())
    return target


def record_render(file, fps, duration_ms):
    file = str(pathlib.Path(file).resolve())
    with Meta(file) as m:
        m["renders"] = [r for r in m["renders"] if r["file"] != file]
        m["renders"].append({"file": file, "rendered": now(), "status": "current", "fps": fps,
                             "duration_ms": duration_ms, "published": None})


def record_publish(file, tag, asset_id, url):
    file = str(pathlib.Path(file).resolve())
    with Meta(file) as m:
        for r in m["renders"]:
            if r["file"] == file:
                r["published"] = {"tag": tag, "asset_id": asset_id, "url": url, "uploaded": now()}
                return
        sys.exit(f"meta: no render entry for {file}; render it with tools/render/render.js first")


def check(file):
    """Hand-over checklist: every referenced file exists outside deletable, every entry's file exists."""
    root, name = locate(file)
    problems = []
    html = root / "editable" / f"{name}.html"
    if html.exists():
        for ref in sorted(set(re.findall(r'(?:src|href)="(materials/[^"]+)"', html.read_text()))):
            if "/deletable/" in ref:
                problems.append(f"html references a deletable file: {ref}")
            elif not (html.parent / ref).exists():
                problems.append(f"html references a missing file: {ref}")
    meta = root / "metadata" / f"{name}.json"
    if meta.exists():
        data = json.loads(meta.read_text())
        for e in data["assets"] + data["renders"]:
            if not pathlib.Path(e["file"]).exists():
                problems.append(f"metadata points at a missing file: {e['file']}")
        current = [r for r in data["renders"] if r["status"] == "current"]
        if current and not current[-1].get("published"):
            problems.append(f"current render not published: {current[-1]['file']}")
    else:
        problems.append(f"no metadata file: {meta}")
    print("\n".join(problems) if problems else "check ok")
    return 1 if problems else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("asset"); a.add_argument("file"); a.add_argument("--tool", required=True)
    a.add_argument("--prompt", required=True); a.add_argument("--url"); a.add_argument("--job"); a.add_argument("--source")
    mv = sub.add_parser("move"); mv.add_argument("file"); mv.add_argument("--by")
    r = sub.add_parser("render"); r.add_argument("file"); r.add_argument("--fps", type=int, required=True)
    r.add_argument("--duration-ms", type=int, required=True)
    p = sub.add_parser("publish"); p.add_argument("file"); p.add_argument("--tag", required=True)
    p.add_argument("--asset-id", required=True); p.add_argument("--url", required=True)
    c = sub.add_parser("check"); c.add_argument("file")
    args = ap.parse_args()
    if args.cmd == "asset":
        record_asset(args.file, args.tool, args.prompt, args.url, args.job, args.source)
    elif args.cmd == "move":
        print(move_to_deletable(args.file, args.by))
    elif args.cmd == "render":
        record_render(args.file, args.fps, args.duration_ms)
    elif args.cmd == "publish":
        record_publish(args.file, args.tag, args.asset_id, args.url)
    elif args.cmd == "check":
        sys.exit(check(args.file))


if __name__ == "__main__":
    main()
