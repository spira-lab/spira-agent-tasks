#!/usr/bin/env python3
"""Spiraverse persona production (the owner's design, 2026-11-12). 10 persona groups, each one original
account and three regen accounts (new name, face and voice, same content). Every video is its own task:
an original is made first; once it is approved, each of its 3 regens becomes its own row and Task ID, made
by a new designer session that copies the original's project and swaps only the persona.

  python3 nova-spiraverse.py index
      Rebuild the persona index (client-assets/Spira/spiraverse/spiraverse.json) from the persona docs.
      Tag IDs already recorded are kept.
  python3 nova-spiraverse.py tags [--create]
      Check each of the 40 accounts has its own tag under the Spira category "Spira Character";
      with --create, make the missing ones (named after the persona) and record their IDs.
  python3 nova-spiraverse.py new "<original persona or group number>" <count> [--with "<partner persona>"]
          [--instructions "<text>"] [any other nova-batch.py new option: --type, --style, --source, --music, ...]
      Original videos for that persona (brand Spiraverse, one row each). --with makes it a couple video.
  python3 nova-spiraverse.py approve <original Task ID> [<Task ID> ...]
      The original is approved: makes its 3 regen rows (one per regen account) on one new sheet.
  python3 nova-spiraverse.py regen <original Task ID> "<regen persona>" [--note "<text>"]
      One regen made again as a NEW task by a new designer (the old one moved to test); the map points to the new one.
  python3 nova-spiraverse.py show [<Task ID>]
      The map: each original, its approval and its regens.
  python3 nova-spiraverse.py group <Task ID>
      Is that original's group (original + 3 regens) complete? Announce it when it is (the owner, 2026-11-12).
  python3 nova-spiraverse.py tag-of "<persona>"
      The persona's tag ID (Hermes uses this).

The map is Agents/NovaOM/docs/spiraverse-map.json. Prints one JSON line per command.
"""
import importlib.util, json, re, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

MAX = Path(__file__).resolve().parents[1]
SUPER = MAX.parents[1]
PERSONAS = MAX / "client-assets" / "Spira" / "spiraverse"
INDEX = PERSONAS / "spiraverse.json"
MAP = MAX / "docs" / "spiraverse-map.json"
BATCH = MAX / "tools" / "nova-batch.py"
CATEGORY = "Spira Character"
MARK = re.compile(r"^\[Spiraverse:.*?\]\s*", re.S)
# What every account of a group keeps from the original, whatever the regen's face (the owner's rules)
KEEP = {"02": "eyeglasses in every shot, like Mike (the owner, 2026-11-12)"}

spec = importlib.util.spec_from_file_location("atlas_sheet", SUPER / "Agents" / "AtlasPM" / "tools" / "atlas-sheet.py")
sheet = importlib.util.module_from_spec(spec); spec.loader.exec_module(sheet)

def out(d): print(json.dumps(d, ensure_ascii=False))
def load(p, default): return json.loads(p.read_text()) if p.is_file() else default
def save(p, d): p.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
def opt(a, name):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else None
def drop(a, name):
    if name in a:
        i = a.index(name); del a[i:i + 2]

# ---------- the persona index ----------
def build_index():
    old = {acc["name"].lower(): acc.get("tag_id") for g in load(INDEX, {"groups": []})["groups"] for acc in g["accounts"]}
    groups = []
    for f in sorted(PERSONAS.glob("[0-9][0-9]-*.md")):
        t = f.read_text(encoding="utf-8")
        gnum = f.name[:2]
        profile = (re.search(r"## Shared profile\s+(.+)", t) or [None, ""])[1].strip()
        accounts = []
        for m in re.finditer(r"^### (Original|Regen (\d)) · ([^(\n]+?)\s*(?:\((.*?)\))?\s*$(.*?)(?=^### |^## |\Z)", t, re.M | re.S):
            body = m.group(5)
            sheet_url = (re.search(r"Character sheet URL: \[(https?://[^\]]+)\]", body) or [None, None])[1]
            partner = re.search(r"\*\*Couple partner:\*\* ([^(]+?) \(", body)
            trait = re.search(r"\*\*(?:Comic traits|Features) to (?:retain|exaggerate)[^*]*:\*\* ([^\n]+)", body)
            region = re.search(r"\*\*Appearance:\*\* ((?:[A-Z][a-z]+-)?[A-Z][a-z]+(?:-American| American))", body)
            name = m.group(3).strip()
            accounts.append({"role": "original" if m.group(1) == "Original" else f"regen {m.group(2)}",
                             "name": name, "handle": (m.group(4) or "").strip() if "@" in (m.group(4) or "") else None,
                             "sheet": sheet_url, "photo": str((PERSONAS / "profile-photos" / f"{name}.jpg").relative_to(SUPER)),
                             "partner": partner.group(1).strip() if partner else None,
                             "traits": trait.group(1).strip().rstrip(".") if trait else None,
                             "region": region.group(1) if region else None,
                             "tag_id": old.get(name.lower())})
        bio = re.search(r"\*\*Who (?:she|he) is:\*\*[^\n]*?\b((?:[A-Z][a-z]+-)?[A-Z][a-z]+-American)", t)
        if bio and accounts and not accounts[0]["region"]: accounts[0]["region"] = bio.group(1)   # the original's heritage is in the bio
        groups.append({"group": gnum, "doc": str(f.relative_to(SUPER)), "profile": profile,
                       "gender": "male" if profile.lower().startswith("male") else "female", "accounts": accounts})
    by_name = {acc["name"].lower(): acc for g in groups for acc in g["accounts"]}
    for g in groups:   # couples are mutual: if Savanna lists Mike, Mike gets Savanna (2026-11-12)
        for acc in g["accounts"]:
            p = by_name.get((acc["partner"] or "").lower())
            if p and not p["partner"]: p["partner"] = acc["name"]
    save(INDEX, {"_about": "Spiraverse personas, built from the persona docs by nova-spiraverse.py index", "groups": groups})
    return groups

def groups(): return load(INDEX, None)["groups"] if INDEX.is_file() else build_index()

def find(who):
    """A persona by name (any account) or a group by number ("01", "group 1")."""
    w = who.strip().lower()
    num = re.fullmatch(r"(?:group\s*)?(\d{1,2})", w)
    for g in groups():
        if num and int(num.group(1)) == int(g["group"]): return g, g["accounts"][0]
        for acc in g["accounts"]:
            if acc["name"].lower() == w or (acc["handle"] or "").lower().lstrip("@") == w.lstrip("@"): return g, acc
    sys.exit(f"REFUSED no Spiraverse persona or group {who!r}")

def regen_account(g, n): return next(a for a in g["accounts"] if a["role"] == f"regen {n}")

PET_DIR = SUPER / "Agents/NovaOM/client-assets/Spiraverse/personas"

def pet_of(name):
    """The persona's saved dog (personas/<Name>/dog.md: '- Dog: ...' and '- Reference URL: https://...'), or None."""
    f = PET_DIR / name / "dog.md"
    if not f.is_file(): return None
    t = f.read_text(encoding="utf-8")
    dog = re.search(r"^- Dog: (.+)$", t, re.M); url = re.search(r"^- Reference URL: (https://\S+)", t, re.M)
    return {"dog": dog.group(1).strip(), "url": url.group(1)} if dog and url else None

def block(g, acc, partner=None):
    """The persona block at the start of a row's Instructions (Hermes reads the name from it)."""
    b = (f"[Spiraverse: {acc['name']} ({acc['handle'] or 'no handle yet'}), group {g['group']} {acc['role']}. "
         f"Character sheet (the face and look): {acc['sheet']}. Persona doc (who they are, voice, wardrobe, pillars, "
         f"audience): {SUPER / g['doc']} (use the section for {acc['name']}). Pick a voice that fits {acc['name']} "
         f"from the shared voice list. Never mention or show the other accounts of this group. "
         + (f"KEEP FROM THE CHARACTER SHEET: retain {acc['name']}'s defining features in every shot: {acc['traits']}. " if acc.get("traits") else "") +
         f"Spiraverse rule (the owner, "
         f"2026-11-12, it overrides the persona doc): never mention or show any brand, Spira included (no names, logos, "
         f"websites, apps or product UI, in the video or its post copy) and no ad-like lines (no sales pitch, promo-speak or "
         f"hard sell), unless these instructions ask for them. Organic creator CTAs ('comment X', 'link in bio', 'follow "
         f"for more') and text overlays are fine.")
    pet = pet_of(acc["name"])
    if pet:   # the owner, 2026-11-12: a persona's dog stays the same dog in every video
        b += (f" {acc['name']}'s dog: {pet['dog']}, reference image {pet['url']}. ONLY when the source video has a dog in "
              f"it, that dog becomes exactly this dog from the reference (same breed, coat colour and markings, never "
              f"another dog). When the source has no dog, never add one.")
    if partner:
        pg, pa = partner
        b += f" Couple video with {pa['name']} ({pa['handle'] or 'no handle yet'}), character sheet {pa['sheet']}."
        if pg["group"] in KEEP: b += f" {pa['name']} must keep {KEEP[pg['group']]}."
    elif acc.get("partner"):   # the persona's couple partner (2026-11-12: Mike's skit had a woman who should be Savanna)
        pg, pa = find(acc["partner"])
        b += (f" {acc['name']}'s partner is {pa['name']} ({pa['handle'] or 'no handle yet'}), character sheet {pa['sheet']}: "
              f"if the video has a second main person (a partner, girlfriend or boyfriend, a co-star), cast them as {pa['name']} "
              f"from that sheet, unless the instructions say otherwise.")
        if pg["group"] in KEEP: b += f" {pa['name']} must keep {KEEP[pg['group']]}."
    return b + "] "

# ---------- tags ----------
def spira(*args):
    r = subprocess.run(["spira", "--json", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try: d = json.loads(r.stdout)
    except json.JSONDecodeError: d = None
    if r.returncode or not d or str(d.get("status", "")).lower() == "error":
        raise RuntimeError((r.stderr or r.stdout).strip()[-300:])
    return d

def tags(create):
    gs = groups()
    items = spira("social", "assets", "tags")["data"]["items"]
    def en(v): return (v or {}).get("en") if isinstance(v, dict) else v
    have = {en(i["name"]).lower(): i["id"] for i in items if en(i.get("category")) == CATEGORY and en(i.get("name"))}
    made, missing = [], []
    for g in gs:
        for acc in g["accounts"]:
            tid = have.get(acc["name"].lower())
            if not tid and create:
                d = spira("social", "assets", "tags", "create", "--en", acc["name"], "--category", CATEGORY)
                tid = (d.get("ids") or {}).get("tagId") or next((i["id"] for i in (d.get("data") or {}).get("items", [])), None)
                if not tid:
                    items = spira("social", "assets", "tags")["data"]["items"]
                    tid = next((i["id"] for i in items if en(i.get("category")) == CATEGORY and (en(i["name"]) or "").lower() == acc["name"].lower()), None)
                made.append(acc["name"])
            acc["tag_id"] = tid
            if not tid: missing.append(acc["name"])
    save(INDEX, {"_about": "Spiraverse personas, built from the persona docs by nova-spiraverse.py index", "groups": gs})
    out({"tags": sum(1 for g in gs for a in g["accounts"] if a["tag_id"]), "created": made, "missing": missing})

# ---------- originals and regens ----------
def ids_of(s):
    a, _, b = s.partition("-")
    return [str(i).zfill(len(a)) for i in range(int(a), int(b or a) + 1)]

def new(a):
    who, count = a[0], a[1]
    g, acc = find(who)
    if acc["role"] != "original": sys.exit(f"REFUSED {acc['name']} is a regen account: make the original ({g['accounts'][0]['name']}) and approve it")
    partner = find(opt(a, "--with")) if opt(a, "--with") else None
    rest = a[2:]; note = opt(rest, "--instructions") or ""; drop(rest, "--instructions"); drop(rest, "--with")
    if "--label" not in rest: rest += ["--label", f"spiraverse-{acc['name'].lower()}"]
    if "--type" not in rest: rest += ["--type", "organic-video"]
    if "--avatar-image" not in rest and "carousel" not in " ".join(rest): rest += ["--avatar-image", acc["sheet"]]
    r = subprocess.run([sys.executable, str(BATCH), "new", "Spiraverse", count, *rest, "--instructions", block(g, acc, partner) + note],
                       capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr or r.stdout)
    line = json.loads(r.stdout.strip().splitlines()[-1])
    m = load(MAP, {})
    for tid in ids_of(line["task_ids"]):
        m[tid] = {"persona": acc["name"], "group": g["group"], "role": "original", "sheet": line["sheet"],
                  "with": partner[1]["name"] if partner else None, "created": datetime.now().isoformat(timespec="minutes"),
                  "approved": None, "regens": {}}
    save(MAP, m)
    out({**line, "spiraverse": {"persona": acc["name"], "group": g["group"], "with": partner[1]["name"] if partner else None}})

def row_of(sheet_path, tid):
    rows, _ = sheet.load(SUPER / sheet_path)
    return next((r for r in rows if r["Task ID"].lstrip("0") == tid.lstrip("0")), None)

def approve(tids, only=None, extra=""):
    m = load(MAP, {}); made = []; sheet_out = None
    for tid in tids:
        e = m.get(tid) or m.get(tid.zfill(2))
        if not e or e["role"] != "original": sys.exit(f"REFUSED Task {tid} is not a Spiraverse original")
        if e["regens"] and not only: sys.exit(f"REFUSED Task {tid} already has regens: {e['regens']}")
        r = row_of(e["sheet"], tid)
        if not r or (r.get("Status") or "").lower() != "done": sys.exit(f"REFUSED Task {tid} is not done yet")
        res = r.get("Result") or ""
        mv = re.match(r"DONE\s+(.+?\.mp4)\b", res); mc = re.match(r"DONE\s+(.+?/carousels/[^/\s]+)", res)
        item = Path(mv.group(1) if mv else mc.group(1))
        root, name = item.parent.parent, (item.stem if mv else item.name)
        g, orig = find(e["persona"])
        pg = find(e["with"])[0] if e.get("with") else None
        brief = MARK.sub("", r.get("Instructions") or "").strip()
        style = sheet.style_name(r.get("Style")) or "talking head edited"
        otype = (r.get("Output type") or "organic-video").strip()
        new_here = []
        for n in (1, 2, 3):
            acc = regen_account(g, n)
            if only and acc["name"].lower() != only.lower(): continue
            partner = (pg, regen_account(pg, n)) if pg else None
            keep = f"{acc['name']} must keep {KEEP[g['group']]}. " if g["group"] in KEEP else ""
            reg = acc.get("region") or "US (no region in the doc)"
            local = (f"Region and language (the owner, 2026-11-12): {acc['name']} is {reg}; {orig['name']} is "
                     f"{orig.get('region') or 'not set'}. If the original's on-screen text, speech or post copy names a heritage or "
                     f"region, or mixes English with another language, adapt it to {acc['name']}'s own (e.g. 'a Mexican mom' -> "
                     f"her own heritage; Spanish words -> her own language). If the region is not set, the persona is plain US: US English only, "
                     f"no heritage reference and no words from another language (the owner, 2026-11-12). The SPEECH follows the same rule: "
                     f"if the original's speech uses a language other than English, re-voice those lines in the persona's own language "
                     f"(a US persona: English), unless the request asks for English only. ")
            regen = (f"REGEN {n} of Task {tid} ({orig['name']} -> {acc['name']}). {keep}{local}Copy the original's project into your own "
                     f"project for this Task ID and change ONLY the persona: the face (this character sheet), the voice (a voice "
                     f"that fits {acc['name']}, not the original's), any on-screen name, and the background. Keep the script, "
                     f"structure, hook, timing, overlays and edit the same. Original project: root {root}, name {name} "
                     f"(metadata {root}/metadata/{name}.json, output {item}). Never edit the original's files. Post copy: rewrite "
                     f"the original's ({root}/metadata/{name}.post.json) in fresh words for {acc['name']}: the same idea, never "
                     f"word for word, never mentioning any other account. ")
            args = [sys.executable, str(BATCH), "new", "Spiraverse", "1", "--type", otype, "--style", style,
                    "--instructions", block(g, acc, partner) + regen + extra + (f" Original brief: {brief}" if brief else "")]
            if "carousel" not in style: args += ["--avatar-image", acc["sheet"]]
            for col, flag in (("Source video", "--source"), ("Music", "--music"), ("Duration", "--duration")):
                if (r.get(col) or "").strip(): args += [flag, r[col].strip()]
            args += ["--sheet", sheet_out] if sheet_out else ["--label", "spiraverse-regens"]
            p = subprocess.run(args, capture_output=True, text=True)
            if p.returncode: sys.exit(f"FAILED making regen {n} of Task {tid}: {(p.stderr or p.stdout)[-300:]}")
            line = json.loads(p.stdout.strip().splitlines()[-1]); sheet_out = line["sheet"]; rid = line["task_ids"]
            if (r.get("Script") or "").strip():   # same script as the original: the regen is never rewritten
                with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f: f.write(r["Script"])
                subprocess.run([sys.executable, str(SUPER / "Agents/AtlasPM/tools/atlas-sheet.py"), str(SUPER / sheet_out), "set", rid, f"Script=@{f.name}"],
                               capture_output=True, text=True, check=True)
            e["regens"][acc["name"]] = rid; new_here.append(rid)
            m[rid] = {"persona": acc["name"], "group": g["group"], "role": f"regen {n}", "of": tid, "sheet": sheet_out,
                      "with": partner[1]["name"] if partner else None, "created": datetime.now().isoformat(timespec="minutes")}
            made.append(rid)
        rids = list(e["regens"].values())
        for rid in new_here:   # each regen's copy must differ from its siblings' too (the owner, 2026-11-12)
            others = [x for x in rids if x != rid]
            row = row_of(sheet_out, rid)
            note = (f" Sibling regens of Task {tid}: Tasks {', '.join(others)}. Before saving your post copy, read theirs if saved "
                    f"({root}/metadata/<Task ID>-*.post.json) and the original's, and make yours clearly different from all of them "
                    f"(different hook and opening words).")
            subprocess.run([sys.executable, str(SUPER / "Agents/AtlasPM/tools/atlas-sheet.py"), str(SUPER / sheet_out), "set", rid,
                            f"Instructions={row['Instructions']}{note}"], capture_output=True, text=True, check=True)
        e["approved"] = e.get("approved") or datetime.now().isoformat(timespec="minutes")
        save(MAP, m)
    out({"sheet": sheet_out, "regens": made, "status": "pending: run the sheet with nova-atlas.py"})

def show(a):
    m = load(MAP, {})
    if a: out({a[0]: m.get(a[0])}); return
    out({tid: {"persona": e["persona"], "approved": e["approved"], "regens": e["regens"]} for tid, e in m.items() if e["role"] == "original"})

def group_status(tid):
    """Is the group of this original or regen complete (original done + all 3 regens done)? (the owner, 2026-11-12)"""
    m = load(MAP, {}); e = m.get(tid)
    if not e: sys.exit(f"REFUSED Task {tid} is not on the Spiraverse map")
    otid = e.get("of") or tid; o = m[otid]
    tasks = [otid] + list(o["regens"].values())
    def done(t):
        r = row_of(m[t]["sheet"], t)
        return bool(r) and (r.get("Status") or "").strip().lower() == "done" and "TEST" not in (r.get("Result") or "")
    state = {t: done(t) for t in tasks}
    complete = len(o["regens"]) == 3 and all(state.values())
    out({"original": otid, "persona": o["persona"], "tasks": {t: m[t]["persona"] for t in tasks},
         "done": [t for t, v in state.items() if v], "complete": complete})

def tag_of(who):
    g, acc = find(who); out({"persona": acc["name"], "tag_id": acc.get("tag_id"), "tag": f"{CATEGORY} / {acc['name']}"})

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    c = a.pop(0)
    if c == "index": gs = build_index(); out({"groups": len(gs), "accounts": sum(len(g["accounts"]) for g in gs)})
    elif c == "tags": tags("--create" in a)
    elif c == "new" and len(a) >= 2: new(a)
    elif c == "approve" and a: approve(a)
    elif c == "regen" and len(a) >= 2:   # one regen again, as a NEW task with a new designer (the old one moved to test)
        note = opt(a, "--note") or ""
        approve([a[0]], only=a[1], extra=(" " + note + " ") if note else " ")
    elif c == "show": show(a)
    elif c == "tag-of" and a: tag_of(a[0])
    elif c == "group" and a: group_status(a[0])
    else: sys.exit(__doc__)

if __name__ == "__main__":
    main()
