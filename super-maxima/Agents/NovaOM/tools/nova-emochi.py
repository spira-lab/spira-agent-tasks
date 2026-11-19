#!/usr/bin/env python3
"""Emochi personas (the owner, 2026-11-19): Emochi's own creator accounts, one persona each. A request that
names Emochi and one of these personas (usually a re-skit) is made with that persona as the on-camera
creator. No regens (unlike Spiraverse). Hermes uploads each video under the persona's own tag in the
Spira category "Emochi".

The personas come from the owner's sheet https://ljpp9tldvzuk.jp.larksuite.com/sheets/GuGUsTDZ2hCAe5tOosajFSngpsc
(each name links to its .md). Ethan and Riley (the backups) are left out, on the owner's word.
Each persona's doc is client-assets/Emochi/personas/<Name>/persona.md; the index is
client-assets/Emochi/emochi-personas.json.

  python3 nova-emochi.py index
      Rebuild the index from the persona docs. Tag IDs already recorded are kept.
  python3 nova-emochi.py tags [--create]
      Check each persona has its own tag under the Spira category "Emochi"; with --create, make the
      missing ones (named after the persona) and record their IDs.
  python3 nova-emochi.py new "<persona>" <count> [--instructions "<text>"]
          [any other nova-batch.py new option: --type, --style, --source, --music, ...]
      Rows for the brand Emochi with that persona (one row each).
  python3 nova-emochi.py list
  python3 nova-emochi.py tag-of "<persona>"
      The persona's tag ID (Hermes uses this).

Prints one JSON line per command.
"""
import json, re, subprocess, sys
from pathlib import Path

OM = Path(__file__).resolve().parents[1]
SUPER = OM.parents[1]
BRAND = OM / "client-assets" / "Emochi"
PERSONAS = BRAND / "personas"
INDEX = BRAND / "emochi-personas.json"
BATCH = OM / "tools" / "nova-batch.py"
CATEGORY = "Emochi"
ABOUT = "Emochi personas (the owner, 2026-11-19), built from personas/<Name>/persona.md by nova-emochi.py index"

def out(d): print(json.dumps(d, ensure_ascii=False))
def load(p, default): return json.loads(p.read_text()) if p.is_file() else default
def save(p, d): p.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
def opt(a, name):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else None
def drop(a, name):
    if name in a:
        i = a.index(name); del a[i:i + 2]

def build_index():
    old = {p["name"].lower(): p.get("tag_id") for p in load(INDEX, {"personas": []})["personas"]}
    ps = []
    for f in sorted(PERSONAS.glob("*/persona.md")):
        t = f.read_text(encoding="utf-8")
        name = (re.search(r"^# (.+)$", t, re.M) or [None, f.parent.name])[1].strip()
        handle = re.search(r"^- Handle: (@\S+)", t, re.M)
        sheet = re.search(r"^- Character sheet: (https://\S+)", t, re.M)
        ps.append({"name": name, "handle": handle.group(1) if handle else None,
                   "profile": t.split("\n")[2].strip() if t.count("\n") > 2 else "",
                   "sheet": sheet.group(1) if sheet else None, "doc": str(f.relative_to(SUPER)),
                   "tag_id": old.get(name.lower())})
    save(INDEX, {"_about": ABOUT, "personas": ps})
    return ps

def personas(): return load(INDEX, None)["personas"] if INDEX.is_file() else build_index()

def find(who):
    w = who.strip().lower().lstrip("@")
    for p in personas():
        if p["name"].lower() == w or (p["handle"] or "").lower().lstrip("@") == w: return p
    sys.exit(f"REFUSED no Emochi persona {who!r} (have: {', '.join(p['name'] for p in personas())})")

def block(p):
    """The persona block at the start of a row's Instructions (Hermes reads the name from it)."""
    return (f"[Emochi persona: {p['name']} ({p['handle'] or 'no handle yet'}), one of Emochi's own creator accounts. "
            f"Cast {p['name']} as the on-camera creator: she takes the place of the source's main person. "
            f"Character sheet (the face and look, the only look reference): {p['sheet']}. Persona doc (who she is, look, "
            f"outfit style, personality and interests): {SUPER / p['doc']}. Pick a voice that fits {p['name']} from the shared "
            f"voice list. Her outfit is chosen per video within her outfit style, never a fixed outfit; record it in "
            f"{BRAND.relative_to(SUPER)}/personas/{p['name']}/outfits.md (the outfit ledger, so outfits don't repeat).] ")

def spira(*args):
    r = subprocess.run(["spira", "--json", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try: d = json.loads(r.stdout)
    except json.JSONDecodeError: d = None
    if r.returncode or not d or str(d.get("status", "")).lower() == "error":
        raise RuntimeError((r.stderr or r.stdout).strip()[-300:])
    return d

def tags(create):
    ps = personas()
    def en(v): return (v or {}).get("en") if isinstance(v, dict) else v
    def have(): return {en(i["name"]).lower(): i["id"] for i in spira("social", "assets", "tags")["data"]["items"]
                        if en(i.get("category")) == CATEGORY and en(i.get("name"))}
    h, made, missing = have(), [], []
    for p in ps:
        tid = h.get(p["name"].lower())
        if not tid and create:
            d = spira("social", "assets", "tags", "create", "--en", p["name"], "--category", CATEGORY)
            tid = (d.get("ids") or {}).get("tagId") or have().get(p["name"].lower())
            made.append(p["name"])
        p["tag_id"] = tid
        if not tid: missing.append(p["name"])
    save(INDEX, {"_about": ABOUT, "personas": ps})
    out({"tags": sum(1 for p in ps if p["tag_id"]), "created": made, "missing": missing})

def new(a):
    p = find(a[0]); count = a[1]
    rest = a[2:]; note = opt(rest, "--instructions") or ""; drop(rest, "--instructions")
    if "--label" not in rest: rest += ["--label", f"emochi-{p['name'].lower()}"]
    if "--type" not in rest: rest += ["--type", "organic-video"]
    if "--avatar-image" not in rest and "carousel" not in " ".join(rest): rest += ["--avatar-image", p["sheet"]]
    r = subprocess.run([sys.executable, str(BATCH), "new", "Emochi", count, *rest, "--instructions", block(p) + note],
                       capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr or r.stdout)
    line = json.loads(r.stdout.strip().splitlines()[-1])
    out({**line, "emochi_persona": p["name"]})

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    c = a.pop(0)
    if c == "index": ps = build_index(); out({"personas": [p["name"] for p in ps]})
    elif c == "tags": tags("--create" in a)
    elif c == "new" and len(a) >= 2: new(a)
    elif c == "list": out({p["name"]: {"handle": p["handle"], "tag_id": p["tag_id"]} for p in personas()})
    elif c == "tag-of" and a:
        p = find(a[0]); out({"persona": p["name"], "tag_id": p.get("tag_id"), "tag": f"{CATEGORY} / {p['name']}"})
    else: sys.exit(__doc__)

if __name__ == "__main__":
    main()
