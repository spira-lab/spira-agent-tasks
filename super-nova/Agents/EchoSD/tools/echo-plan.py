#!/usr/bin/env python3
"""Echo's director tool. Plans a script request, gets the DNA into files, writes each
writer's brief, checks the finished scripts, and delivers them, so Echo directs without
reading DNA or scripts herself. Every command prints a short result.

  init production --sheet <sheet> --tasks <all | 11,12,...> [--duration <s | 11=30,12=45>]
                  [--product "<name>"] [--angle "<podcast angle>"]
      Plans scripts for draft rows of a batch sheet (one brand per request). Each row's
      script file is <echo>/scripts/<BrandName>/echo-<BrandName>-<Brand number>.md; an
      earlier file there is moved to old/ first.
  init adhoc --brand "<brand>" --video-style "<style>" --count <n> --output-type <organic|ad>
             [--duration <s>] [--product "<name>"] [--instructions "<text>"] [--angle "<text>"]
      Every script needs the DNA. Podcast scripts also need --angle: what the conversation is
      about, with the product coming up inside it. One angle per request.
      Brand "Brandless" (a generic video for no client): no product, no DNA; --angle is the
      subject of every script, whatever the style.
      Duration: the row's Duration column first, then --duration. When none is given, the writer
      uses its writing style's own default length.
      Plans a scripts-only request; scripts are written into the request's work folder.
      Both print the plan path and the writing style given to each script by cycling
      (least recently used first, the latest one avoided).
  restyle <plan> <script no.> "<writing style>"   change one script's writing style
  dna <plan> --dna <DNA file path>
      Fetches the DNA (about the product, or about the brand when there is no product) into
      the work folder (dna.md). Prints its size only.
  brief <plan> "<writing style>"
      Prints the brief for that style's writer: hand it to the writer verbatim.
  check <plan>
      Repeat check of every script in the plan, against the brand's earlier scripts and
      each other. Prints only the scripts that are too close (and a count of ok ones).
  rebrief <plan> <script no.> [...]
      Prints a brief for rewriting just those scripts (after a "too close").
  record <plan>      records every script's writing style in the cycling record
  assemble <plan>    ad hoc: builds the table file in <echo>/adhoc/ and prints its path
  fill <plan>        production: puts every script into its row of the sheet

Work folders: <echo>/work/<BrandName>-<YYYYMMDD-HHMMSS>/ (plan.json, DNA, ad hoc scripts).

Carousels (any video style ending in "carousel", e.g. corporate carousel; the old name carousel reads
as corporate carousel; 2026-10-27): a carousel's "script" is its topic angle, one line plus an
optional `Direction:` line, for that style's carousel designer. A carousel style with no writing
style rows of its own in echo-styles.md uses the corporate carousel's. Production files go in
<echo>/scripts/<BrandName>/carousel/echo-<BrandName>-<Brand number>.md; an ad hoc table is
<echo>/adhoc/echo-adhoc-carousel-<BrandName>-<date>.md. Their angles are checked and recorded apart
from the brand's video angles (echo-similar.py --carousel), one record for every carousel style.
Duration does not apply.
"""
import importlib.util, json, re, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

ECHO = Path(__file__).resolve().parents[1]
SUPER = ECHO.parents[1]
SHEET_TOOL = SUPER / "Agents" / "AtlasPM" / "tools" / "atlas-sheet.py"
GUIDE = ECHO / "styles" / "echo-styles.md"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
cycle = load("echo_cycle", ECHO / "tools" / "echo-cycle.py")
similar = load("echo_similar", ECHO / "tools" / "echo-similar.py")

PODCAST = "podcast"
def is_carousel(s): return cycle.is_carousel(s.get("video_style"))   # any style ending in "carousel"
def key(b): return re.sub(r"[^A-Za-z0-9]", "", b or "") or "Brandless"
def norm(s): return " ".join((s or "").lower().split())
def rel(p): return str(Path(p).resolve().relative_to(SUPER))

def opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default

def skill_file(video_style, writing_style):
    for line in GUIDE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Video style"): continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 4 and cycle.vstyle(c[0]) == cycle.writing_key(video_style) and norm(c[1]) == norm(writing_style):
            return c[3].strip("`")
    sys.exit(f"no writing skill for {video_style!r} + {writing_style!r} in echo-styles.md")

def assign_styles(scripts, product=None):
    """Cycle writing styles across the scripts, per video style, without saving the record.
    Echo's working memory narrows the styles for a product that has its own (echo-cycle.py)."""
    rec = json.loads(cycle.RECORD.read_text() or "{}") if cycle.RECORD.exists() else {}
    for s in scripts:
        vs = norm(s["video_style"]); styles = cycle.styles_for(vs, product); rk = cycle.record_key(vs, product)
        if not styles: sys.exit(f"QUESTION no writing style for {vs}")
        recent = rec.get(rk, [])
        rank = {w: (recent.index(w) if w in recent else -1) for w in styles}
        order = sorted(styles, key=lambda w: (rank[w] != -1, -rank[w]))
        if recent and recent[0] in order and len(order) > 1:
            order.remove(recent[0]); order.append(recent[0])
        s["writing_style"] = order[0]
        rec[rk] = ([order[0]] + recent)[:cycle.KEEP]          # in memory only, to keep cycling inside the request

def save(plan_path, plan): plan_path.write_text(json.dumps(plan, indent=1) + "\n")
def read(plan_path):
    p = Path(plan_path).expanduser().resolve()
    if not p.is_relative_to(ECHO / "work") or not p.is_file(): sys.exit(f"no plan in {ECHO / 'work'} at {p}")
    return p, json.loads(p.read_text())

def summary(plan_path, plan):
    groups = {}
    for s in plan["scripts"]: groups.setdefault(s["writing_style"], []).append(s["n"])
    return {"plan": rel(plan_path), "kind": plan["kind"], "brand": plan["brand"], "scripts": len(plan["scripts"]),
            "writing_styles": {w: ns for w, ns in groups.items()}}

def init(args):
    kind = args[0]; now = datetime.now()
    if kind == "production":
        sheet = Path(opt(args, "--sheet", "")).expanduser().resolve()
        if not sheet.is_relative_to(SUPER) or not sheet.is_file(): sys.exit(f"no batch sheet at {sheet}")
        rows, _ = load("atlas_sheet", SHEET_TOOL).load(sheet)
        want = opt(args, "--tasks", "all")
        if want == "all": rows = [r for r in rows if (r.get("Status") or "").lower() == "draft"]
        else:
            ids = [x.strip() for x in want.split(",")]; rows = [r for r in rows if r.get("Task ID") in ids]
            if len(rows) != len(ids): sys.exit("some Task IDs are not in the sheet")
        if not rows: sys.exit("no draft rows to write")
        brands = {key(r.get("Brand")) for r in rows}
        if len(brands) > 1: sys.exit(f"QUESTION one brand per request; these rows have {sorted(brands)}")
        dur = opt(args, "--duration") or ""          # optional: each row's Duration column comes first
        per = dict(x.split("=") for x in dur.split(",")) if "=" in dur else {}
        brand = rows[0].get("Brand") or "Brandless"; bk = key(brand)
        sdir = ECHO / "scripts" / bk; sdir.mkdir(parents=True, exist_ok=True)
        scripts = []
        for n, r in enumerate(rows, 1):
            d = r.get("Duration") or per.get(r["Task ID"]) or (dur if dur and not per else None)   # None: the writing style's default
            car = cycle.is_carousel(r.get("Style"))
            if car: d = None                                  # a carousel angle has no length
            fdir = sdir / "carousel" if car else sdir         # carousel angles live apart from video scripts
            fdir.mkdir(parents=True, exist_ok=True)
            f = fdir / f"echo-{bk}-{r['Brand number']}.md"
            if f.exists():
                (fdir / "old").mkdir(exist_ok=True)
                shutil.move(str(f), str(fdir / "old" / f"{f.stem}_{now:%Y%m%d-%H%M%S}.md"))
            if f.with_suffix(".angle").exists():
                (fdir / "old").mkdir(exist_ok=True)
                shutil.move(str(f.with_suffix(".angle")), str(fdir / "old" / f"{f.stem}_{now:%Y%m%d-%H%M%S}.angle"))
            ins = r.get("Instructions") or ""
            if car:   # the product and website Nova's batch tool added are for the designer, not the writer
                ins = re.sub(r"\s*Product:\s.*?\.\s*(?=Brand website:)", " ", ins)
                ins = re.sub(r"\s*Brand website:\s*\S+", "", ins).strip()
            scripts.append({"n": n, "task_id": r["Task ID"], "video_style": r.get("Style") or "talking head edited",
                            "output_type": "ad" if "ad" in (r.get("Output type") or "") else "organic",
                            "duration": int(d) if d else None, "instructions": ins, "file": rel(f)})
        plan = {"kind": "production", "sheet": rel(sheet), "brand": brand}
    elif kind == "adhoc":
        brand = opt(args, "--brand") or sys.exit("QUESTION brand missing"); bk = key(brand)
        count = int(opt(args, "--count") or sys.exit("QUESTION count missing"))
        dur = opt(args, "--duration")                     # None: the writing style's default
        vs = opt(args, "--video-style") or sys.exit("QUESTION video style missing")
        ot = opt(args, "--output-type") or ("organic" if norm(vs) == PODCAST else None) or sys.exit("QUESTION organic or ad missing")
        plan = {"kind": "adhoc", "brand": brand}
        if cycle.is_carousel(vs): dur = None                # a carousel angle has no length
        scripts = [{"n": n, "task_id": None, "video_style": vs, "output_type": ot, "duration": int(dur) if dur else None,
                    "instructions": opt(args, "--instructions", ""), "file": None} for n in range(1, count + 1)]
    else:
        sys.exit(__doc__)
    pods = any(norm(s["video_style"]) == PODCAST for s in scripts)
    angle = opt(args, "--angle") or None
    brandless = key(plan["brand"]).lower() == "brandless"
    if brandless and not angle: sys.exit("QUESTION angle missing: a brandless script is written from its angle")
    if pods and not angle: sys.exit("QUESTION podcast angle missing")
    if angle and not pods and not brandless: sys.exit("QUESTION an angle is only for podcast or brandless scripts")
    work = ECHO / "work" / f"{key(plan['brand'])}-{now:%Y%m%d-%H%M%S}"; k = 2
    while work.exists(): work = ECHO / "work" / f"{key(plan['brand'])}-{now:%Y%m%d-%H%M%S}-{k}"; k += 1
    work.mkdir(parents=True)
    for s in scripts:
        if s["file"] is None: s["file"] = rel(work / f"script-{s['n']:02d}.md")
    product = None if brandless else (opt(args, "--product") or None)
    assign_styles(scripts, product)
    plan.update(created=now.isoformat(timespec="minutes"), product=product,
                angle=angle, brandless=brandless, dna={}, scripts=scripts)
    save(work / "plan.json", plan)
    print(json.dumps(summary(work / "plan.json", plan)))

def dna(p, plan, args):
    if plan.get("brandless"): sys.exit("a brandless request has no DNA: go straight to `brief`")
    for kind in ("dna",):
        url = opt(args, "--dna")
        if not url or url.lower() == "none": continue
        src = Path(url).expanduser(); src = src if src.is_absolute() else SUPER / src
        try: content = src.read_text(encoding="utf-8")
        except OSError as e:
            sys.exit(f"FAILED cannot read DNA {url}: {e}")
        f = p.parent / "dna.md"; f.write_text(content, encoding="utf-8")
        plan["dna"][kind] = rel(f)
    if "dna" not in plan["dna"]: sys.exit("QUESTION DNA missing")
    save(p, plan)
    print(json.dumps({k: f"{(SUPER / v).stat().st_size} bytes" for k, v in plan["dna"].items()}))

def brief_text(plan, scripts, rewrite=False):
    ws = scripts[0]["writing_style"]; vs = scripts[0]["video_style"]
    skill = skill_file(vs, ws); d = plan["dna"]
    if plan.get("brandless"):
        source = "2. The subject (nothing to read):"; holds = "the angle"
        subject = (f"- The angle: {plan['angle']}\n"
                   "   This is a generic video for no brand: no product, no company, no DNA. The angle is the subject of every script.\n"
                   "   What is stated as fact must be true: no invented statistics, studies, quotes, or claims about real people or companies.\n"
                   "   Where your skill speaks of the product or the brand, read it as the angle.")
    elif "dna" not in d: sys.exit("run `dna` first")
    else: source = "2. Read the DNA (Markdown files):"; holds = "the product" if plan.get("product") else "the brand"
    if plan.get("brandless"): pass
    elif norm(vs) == PODCAST:
        thing = f"the product, {plan['product']}," if plan.get("product") else "the brand"
        subject = (f"- {d['dna']}: the DNA (description, key highlights, RTB).\n"
                   f"   The podcast's angle: {plan['angle']}\n"
                   f"   The conversation is about the angle; {thing} comes up inside it, the way things come up between two people.\n"
                   "   Never invent claims the DNA does not support, and anything else they state as fact must be true:\n"
                   "   no invented statistics, studies, quotes, or claims about real people or companies.")
        holds = "the angle"
    else:
        subject = (f"- {d['dna']}: the DNA (description, key highlights, RTB). The product, {plan['product']}, "
               f"is the subject of every script.") if plan.get("product") else \
              f"- {d['dna']}: the DNA (description, key highlights, RTB). There is no product: the brand is the subject."
        subject += "\n   Never invent claims the DNA does not support."
    car = cycle.is_carousel(vs)
    lines = "\n".join(f"   - `{s['file']}`: {s['output_type']}, "
                      + ("a carousel topic angle (no duration)" if car else
                         f"{s['duration']} seconds" if s['duration'] else "duration not given (use your skill's default length)")
                      + (f", instructions: {s['instructions']}" if s['instructions'] else "") for s in scripts)
    redo = ("These scripts were too close to earlier ones for this brand: the same angle, or near-identical "
            "phrasing. Rewrite each from scratch with a new angle and your own phrasing.\n\n") if rewrite else ""
    return f"""You are one of Echo's scriptwriters in Super Nova ({SUPER}). {redo}Work only inside that folder. Do not start other agents and do not message anyone.
Never read any video designer skill or file (Agents/DesignerShared/, Agents/*VideoDesigner/): they are for making the video, not the script, and would change how you write. Your writing skill is your only guide.

1. Read your writing skill in full and follow it exactly. It is the only writing style you use: {SUPER / skill}
{source}
{subject}
3. Read the {'carousel angles' if car else 'angles'} already used for this brand{' (carousel angles are kept apart from video angles)' if car else ''}. Every script must take a NEW angle, not on that list and different from your other scripts:
   python3 "{ECHO / 'tools' / 'echo-similar.py'}" angles "{plan['brand']}"{(' --product "' + plan['product'] + '"') if plan.get('product') else ''}{' --carousel' if car else ''}
   It tells you what the angle is for this brand, which angles you may not use, and, when the brand has one, the list you must pick from (use the list's wording exactly). The angle is the script's one core subject in 2 to 5 words: for a persona-led script, the person's job or role (e.g. "hotel housekeeper"); otherwise the topic (e.g. "platelet counts after CAR-T"). A new detail on a used angle (the same job, another situation) is still the same angle.
   Never deliver phrasing identical to an earlier script. The product's own feature lines and call to action may recur.
4. Write {len(scripts)} {'carousel topic angle' if car else 'script'}{'s' if len(scripts) > 1 else ''} ({('organic or ad is given for each' if len(scripts) > 1 else 'organic or ad is given') if car else ('organic or ad and the duration are given for each' if len(scripts) > 1 else 'organic or ad and the duration are given')}):
{lines}
   Where a script has instructions, they come first: follow them even where your skill's defaults say otherwise (e.g. a named speaker in the first person). A named speaker only changes who is talking: {holds} stays the subject, never the speaker.
   Fit each script to {'its format' if car else 'its duration'} and to organic or ad exactly as your skill says. Every script must be clearly different from the others (your skill's rules for several options apply across them).
5. Save each script to its file path (relative to {SUPER}) with the Write tool, exactly in your skill's output format ({'the topic angle line, and the Direction line only when your skill calls for one' if car else 'spoken words only; speaker labels only when your skill uses them'}). Nothing else in the file.
   Beside each script, save its angle (one line, 2 to 5 words, nothing else) to the same path with `.angle` in place of `.md`.

Your final reply is exactly one line: DONE {len(scripts)} files, or FAILED <short reason>."""

def check(p, plan):
    files = [SUPER / s["file"] for s in plan["scripts"]]
    missing = [s["n"] for s, f in zip(plan["scripts"], files) if not f.is_file() or not f.read_text().strip()]
    if missing: print(json.dumps({"missing": missing})); return
    own = [SUPER / plan["adhoc_file"]] if plan.get("adhoc_file") else []   # never against its own assembled table
    res = []   # against earlier scripts and each other; carousel angles only against carousel angles
    for car in (False, True):
        group = [f for s, f in zip(plan["scripts"], files) if is_carousel(s) == car]
        if group: res += similar.check(key(plan["brand"]), group, also_exclude=own, product=plan.get("product"), carousel=car)
    by_name = {Path(s["file"]).name: s["n"] for s in plan["scripts"]}
    bad = []
    for r in res:
        if r["verdict"] == "ok": continue
        n, other = by_name.get(r["script"]), by_name.get(r["closest"])
        if other is not None and other > n: continue      # two new scripts clash: only the later one is rewritten
        bad.append(dict(r, n=n))
    for b in bad: print(json.dumps(b))
    print(json.dumps({"ok": len(res) - len(bad), "too_close": [b["n"] for b in bad]}))

def assemble(p, plan):
    bk = key(plan["brand"]); day = plan["created"][:10]
    s0 = plan["scripts"][0]
    pre = "echo-adhoc-carousel-" if is_carousel(s0) else "echo-adhoc-"   # carousel angles kept apart
    out = ECHO / "adhoc" / f"{pre}{bk}-{day}.md"; k = 2
    while out.exists(): out = ECHO / "adhoc" / f"{pre}{bk}-{day}-{k}.md"; k += 1
    rows = []
    for s in plan["scripts"]:
        text = " ".join((SUPER / s["file"]).read_text(encoding="utf-8").split()).replace("|", "\\|")
        rows.append(f"| {s['n']} | {s['writing_style']} | {text} |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"# {plan['brand']} — {s0['video_style']} scripts — {day}\n\n"
                   f"Product: {plan['product'] or 'none'} · Output type: {s0['output_type']} · Duration: {str(s0['duration']) + ' s' if s0['duration'] else 'style default'}\n\n"
                   "| # | Writing style | Script |\n|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    plan["adhoc_file"] = rel(out); save(p, plan)
    print(json.dumps({"adhoc_file": rel(out), "scripts": len(rows)}))

def fill(p, plan):
    for s in plan["scripts"]:
        r = subprocess.run([sys.executable, str(SHEET_TOOL), str(SUPER / plan["sheet"]), "set", s["task_id"],
                            f"Script=@{SUPER / s['file']}"], capture_output=True, text=True)
        if r.returncode != 0: sys.exit(f"FAILED fill Task {s['task_id']}: {(r.stderr or r.stdout).strip()}")
    print(json.dumps({"filled": [s["task_id"] for s in plan["scripts"]]}))

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "init" and len(a) > 1: return init(a[1:])
    if len(a) < 2: sys.exit(__doc__)
    p, plan = read(a[1])
    if a[0] == "restyle" and len(a) == 4:
        s = next((x for x in plan["scripts"] if x["n"] == int(a[2])), None) or sys.exit("no such script")
        ws = norm(a[3])
        if ws not in cycle.styles_for(s["video_style"], plan.get("product")):
            sys.exit(f"{ws!r} is not available for {s['video_style']!r}" + (f" and {plan['product']!r}" if plan.get("product") else ""))
        s["writing_style"] = ws; save(p, plan); print(json.dumps(summary(p, plan)))
    elif a[0] == "dna": dna(p, plan, a[2:])
    elif a[0] == "brief" and len(a) == 3:
        group = [s for s in plan["scripts"] if s["writing_style"] == norm(a[2])] or sys.exit("no scripts in that style")
        print(brief_text(plan, group))
    elif a[0] == "rebrief" and len(a) >= 3:
        ns = {int(x) for x in a[2:]}; group = [s for s in plan["scripts"] if s["n"] in ns]
        styles = {s["writing_style"] for s in group}
        if len(styles) != 1: sys.exit("rebrief one writing style at a time")
        for s in group:
            (SUPER / s["file"]).unlink(missing_ok=True); (SUPER / s["file"]).with_suffix(".angle").unlink(missing_ok=True)
        print(brief_text(plan, group, rewrite=True))
    elif a[0] == "check": check(p, plan)
    elif a[0] == "record":
        for s in plan["scripts"]: cycle_used(s, plan.get("product"))
        items = []
        for s in plan["scripts"]:   # the brand's angle record, so later scripts never take the same angle
            af = (SUPER / s["file"]).with_suffix(".angle")
            label = Path(s["file"]).name if plan["kind"] == "production" else f"{Path(plan.get('adhoc_file') or s['file']).name}#{s['n']}"
            items.append((label, af.read_text(encoding="utf-8").strip() if af.is_file() else "", is_carousel(s)))
        for car in (False, True):   # carousel angles go to their own record
            group = [(l, x) for l, x, c in items if c == car]
            if group: similar.record(key(plan["brand"]), group, carousel=car)
        print(json.dumps({"recorded": len(plan["scripts"]), "angles": sum(1 for _, x, _ in items if x)}))
    elif a[0] == "assemble" and plan["kind"] == "adhoc": assemble(p, plan)
    elif a[0] == "fill" and plan["kind"] == "production": fill(p, plan)
    else: sys.exit(__doc__)

def cycle_used(s, product=None):
    r = subprocess.run([sys.executable, str(ECHO / "tools" / "echo-cycle.py"), "used", s["video_style"], s["writing_style"],
                        *(["--product", product] if product else [])], capture_output=True, text=True)
    if r.returncode != 0: sys.exit(r.stderr.strip())

if __name__ == "__main__":
    main()
