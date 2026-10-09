#!/usr/bin/env python3
"""Fetch a hosted package file (music, sound effects) listed in resources.json.

The package does not ship its audio; resources.json maps each package path to a
hosted URL and its sha256. This fetches one file to where the video needs it.

Usage: python3 tools/fetch-resource.py <package path> <destination> [--write-level <editable.html>]
  python3 tools/fetch-resource.py music/DD01.mp3 editable/materials/<name>/bgm.mp3 \
      --write-level editable/<name>.html
  python3 tools/fetch-resource.py sfx/03_whoosh.mp3 editable/materials/<name>/sfx/03_whoosh.mp3

The package path is the `path` of an entry in music/Music metadata.json or
sfx/SFX metadata.json. The download goes through curl (the CDN turns away
urllib's default client) and is checked against its sha256 before it lands; a
destination that already holds the right file is left alone.

A music track also carries `lufs_i`, its measured integrated loudness. `--write-level`
puts the gain that places it at BED_LUFS into the editable's `#bgm` tag as
`data-level-db`, which is what the renderer applies and the preview reads. That is
the only place a music level is set: a session never works it out or edits it.
The files themselves are never re-encoded, so their sha256 still matches and the
renderer still counts them as library tracks.
"""
import hashlib, json, os, re, subprocess, sys, tempfile

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Where a music bed belongs in the mix, in LUFS under the voice's -16. Kept in step
# with render.js's BED_LUFS: the two must agree, and the renderer is the one that
# applies it, so a change here is a change there too.
BED_LUFS = -26


def lufs_of(rel):
    """A track's measured integrated loudness, from the metadata rather than
    resources.json (which carries only what the download needs)."""
    entries = json.load(open(os.path.join(PKG, "music", "Music metadata.json"), encoding="utf-8"))
    for e in entries:
        if e["path"] == rel:
            return e.get("lufs_i")
    return None


def level_db(rel):
    """The gain that puts this track at BED_LUFS, never positive: a track already
    quieter than the target is left where its author put it (the WC tracks are
    deliberately low and their mix_note says to play them as they are)."""
    lufs = lufs_of(rel)
    if lufs is None:
        print(f"warning: {rel} has no measured lufs_i: laying it with no gain", file=sys.stderr)
        return 0.0
    return min(0.0, BED_LUFS - float(lufs))


def write_level(editable, db):
    """Put data-level-db on the editable's #bgm tag, in place, keeping the file's
    line endings and its attribute order."""
    # newline="" both ways: the editable is CRLF, and without it the read turns
    # every \r\n into \n and the write would hand back a file of a different shape.
    html = open(editable, encoding="utf-8", newline="").read()
    tag = re.search(r"<audio\b[^>]*\bid=\"bgm\"[^>]*>", html)
    if not tag:
        sys.exit(f"no #bgm tag in {editable}: lay the bed in the editable first")
    value = f'data-level-db="{db:.1f}"'
    old = tag.group(0)
    new = re.sub(r'\s+data-level-db="[^"]*"', "", old)
    new = new[:-1].rstrip() + f" {value}>"
    open(editable, "w", encoding="utf-8", newline="").write(html[:tag.start()] + new + html[tag.end():])
    print(f"  #bgm {value} ({db:+.1f} dB, target {BED_LUFS} LUFS)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    argv = sys.argv[1:]
    editable = None
    if "--write-level" in argv:
        k = argv.index("--write-level")
        if k + 1 >= len(argv):
            sys.exit("--write-level needs an editable html")
        editable = argv[k + 1]
        argv = argv[:k] + argv[k + 2:]
    if len(argv) != 2:
        sys.exit(__doc__.split("\n\n")[2])
    rel, dest = argv[0].lstrip("./"), argv[1]
    files = json.load(open(os.path.join(PKG, "resources.json")))["files"]
    entry = files.get(rel)
    if entry is None:
        near = [k for k in files if os.path.basename(k).split("_")[0] == os.path.basename(rel).split("_")[0]][:3]
        sys.exit(f"not in resources.json: {rel}" + (f" (did you mean {', '.join(near)}?)" if near else ""))
    # Before the download, so a bad editable is reported without transferring 6 MB,
    # and before the early return below, so re-running the same fetch still lands the
    # level: a bed fetched in an earlier session may never have had one.
    if editable:
        if not rel.startswith("music/"):
            sys.exit(f"--write-level is for a music bed; {rel} is not one")
        write_level(editable, level_db(rel))
    if os.path.isfile(dest) and sha256(dest) == entry["sha256"]:
        print(f"already there: {dest}")
        return
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(dest)), suffix=".part"); os.close(fd)
    try:
        if subprocess.run(["curl", "-sSfL", "--retry", "3", "-o", tmp, entry["url"]]).returncode != 0:
            sys.exit(f"download failed: {entry['url']}")
        if sha256(tmp) != entry["sha256"]:
            sys.exit(f"checksum mismatch for {rel}: the hosted file is not the one resources.json lists")
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f"fetched {rel} -> {dest} ({entry['bytes'] / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
