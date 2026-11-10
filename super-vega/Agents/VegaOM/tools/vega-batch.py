#!/usr/bin/env python3
"""Vega's batch builder. One call issues the task numbers, creates (or extends) the batch
sheet, fills every row from the request and the Client Ledger, and prints ONE line, so a
100-video request costs Vega one call and one line of context.

    python3 "<max>/tools/vega-batch.py" new "<brand | Brandless>" <count> --type <organic-video|ad-video|avatar-image|carousel>
        [--duration <s>] [--style "<video style>"]   (--type carousel: corporate carousel unless --style "<kind> carousel",
                                                      e.g. --style "lifestyle story carousel") [--product "<product name>"]
        [--music <library|none>] [--instructions "<text>"]
        [--style-ref <path or URL>] [--avatar-image <path or URL>] [--avatar-voice "<voice>"]
        [--source "<source video link or path>"]   (styles clone and re-skit: the video to clone or re-skit)
        [--sheet <existing sheet in Agents/AtlasPM/batches/>] [--label <label>]

  --sheet adds the rows to an existing sheet (a second group in the same batch, e.g. the
  ad videos of a mixed request). Without it a new sheet is created:
  Agents/AtlasPM/batches/atlas-batch-<YYYY-MM-DD>-<label or brand>.md

Everything is checked BEFORE any number is issued (style, type, duration), and
all rows are written in one save. If anything fails after the numbers were issued, they
are released again, so there are no gaps.

Brand `Brandless` is a generic video for no client: no ledger lookup, no DNA, no product; its
videos are numbered and saved under Brandless like any brand.

`--type avatar-image` (2026-10-22): avatar images only, one avatar per row, made by the Avatar
Designer (style `avatar`). The brand is always `Avatar`, whatever was given, so avatars never
take a client's video numbers; say who it is for in --instructions. No ledger, no DNA.
--instructions is the avatar's description; leave it out and the designer decides the avatar.

`--type carousel` (2026-10-27): 4:5 carousels (1080x1350 slides), one per row, made by a carousel
designer: style `corporate carousel` (the Corporate Carousel Designer) unless --style names another
carousel style ("<kind> carousel", e.g. "lifestyle story carousel", 2026-11-03). The style must end in
"carousel" and have a designer in Atlas's list; the old name `carousel` means `corporate carousel`.
Every carousel style shares output type `carousel`. The ledger lookup stays (brand, and the product with
--product); the row's only inputs are Echo's topic angle (its Script, so the rows are drafts until
Echo writes them) and the website: the batch tool writes "Product: <name>." and "Brand website: <url>"
into the instructions. A scriptless carousel style (marked script none in Atlas's list: lifestyle story
carousel, whose designer picks its own idea) gets the same instructions but no angle, so its rows are
pending at once, like clone and re-skit rows; the requester's note (a topic, story or feed, a slide
count) goes in --instructions. No duration, music, style ref, source, avatar, logo, color or product image.
A carousel needs the Website column in the Client Ledger (the product's row, else the brand's) and
a brand: not Brandless.

Prints one JSON line: sheet, brand, rows, task_ids, brand_numbers, status counts, what came
from the ledger, the DNA link for Echo's brief, and anything missing.
"""
import importlib.util, io, json, re, subprocess, sys
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

MAX = Path(__file__).resolve().parents[1]
SUPER = MAX.parents[1]
BATCHES = SUPER / "Agents" / "AtlasPM" / "batches"
LEDGER = MAX / "docs" / "vega-client-ledger.md"
TASK_TOOL = MAX / "tools" / "vega-task-id.py"
CAROUSEL_DEFAULT = "corporate carousel"   # the style --type carousel uses without --style (2026-10-27)

spec = importlib.util.spec_from_file_location("atlas_sheet", SUPER / "Agents" / "AtlasPM" / "tools" / "atlas-sheet.py")
sheet = importlib.util.module_from_spec(spec); spec.loader.exec_module(sheet)

def key(name): return re.sub(r"[^A-Za-z0-9]", "", name or "")

def opt(args, name, default=""):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default

def ranges(nums):
    """[1,2,3,7,9,10] -> '1-3, 7, 9-10' (numbers keep their padding)."""
    vals = sorted(int(n) for n in nums); out, i = [], 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[j] + 1: j += 1
        a, b = f"{vals[i]:02d}", f"{vals[j]:02d}"
        out.append(a if i == j else f"{a}-{b}"); i = j + 1
    return ", ".join(out)

def ledger_rows(brand):
    if not LEDGER.is_file(): return []
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    try: start = next(i for i, l in enumerate(lines) if l.startswith("| Brand name"))
    except StopIteration: return []
    head = sheet.md_cells(lines[start]); out = []
    for l in lines[start + 2:]:
        if not l.startswith("|"): break
        c = sheet.md_cells(l); r = {h: (c[i] if i < len(c) else "").strip().strip("`") for i, h in enumerate(head)}
        if key(r.get("Brand name")) and key(r.get("Brand name")) == key(brand): out.append(r)
    return out

def first(cell):
    return (re.split(r"<br\s*/?>|,\s*(?=\S)", cell or "")[0] or "").strip().strip("`")

def pick(local, hosted):
    """Local path first, the hosted URL otherwise."""
    return first(local) or first(hosted)

def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] != "new": sys.exit(__doc__)
    brand, count = a[1], a[2]
    if not count.isdigit() or int(count) < 1: sys.exit("count must be a whole number, 1 or more")
    n = int(count)
    otype = opt(a, "--type")
    style = opt(a, "--style"); product_name = opt(a, "--product")
    avatar = otype == "avatar-image"
    if avatar:
        brand, style = "Avatar", "avatar"
        if product_name: sys.exit("an avatar image has no product")
    carousel = otype == "carousel"
    if carousel:
        # any carousel style ("<kind> carousel"); corporate carousel by default (the owner, 2026-10-27)
        style = sheet.style_name(style) or CAROUSEL_DEFAULT
        if not sheet.is_carousel(style): sys.exit(f"--type carousel needs a carousel style (\"<kind> carousel\"), not {style!r}")
        if sheet.style_entry(style)[0] is None:
            known = [k for k in json.loads(sheet.DESIGNERS.read_text()) if not k.startswith("_") and sheet.is_carousel(k)]
            sys.exit(f"no designer for carousel style {style!r} in Atlas's list; carousel styles: {', '.join(known) or 'none'}")
        for flag in ("--duration", "--music", "--style-ref", "--source", "--avatar-image", "--avatar-voice"):
            if flag in a: sys.exit(f"a carousel has no {flag[2:]}")
        if key(brand).lower() == "brandless": sys.exit("a carousel is made from a brand's website: Brandless has none")
    elif sheet.is_carousel(style):
        sys.exit(f"style {sheet.style_name(style)} needs --type carousel")

    # ---- ledger: DNA, logo, colors, product images (Vega never opens the ledger for this) ----
    # A product video uses the product's row (its DNA + images); a brand video uses the brand
    # row (Product name empty). Logo and colors come from the brand row, else the product row.
    brandless = key(brand).lower() == "brandless"     # a generic video for no client: no ledger, no DNA
    if brandless: brand = "Brandless"
    rows_l = [] if (brandless or avatar) else ledger_rows(brand); missing = []
    brand_row = next((r for r in rows_l if not key(r.get("Product name"))), None)
    prow = None
    if brandless or avatar:
        if product_name: sys.exit("a brandless video has no product")
    elif not rows_l:
        missing.append("brand not in the Client Ledger")
    elif product_name:
        prow = next((r for r in rows_l if key(r.get("Product name")) == key(product_name)), None)
        if prow is None: missing.append(f"product {product_name!r} not in the ledger")
    subject = prow or brand_row or {}
    look = lambda c: (brand_row or {}).get(c) or (prow or {}).get(c) or \
                     next((r.get(c) for r in rows_l if r.get(c)), "")
    logo = pick(look("Brand logo (local path)"), look("Brand logo (hosted URL)"))
    colors = ", ".join(c.strip() for c in re.split(r"<br\s*/?>|,", look("Brand colors (hex)") or "") if c.strip())
    prod_img = pick(prow.get("Product images (local path)"), prow.get("Product images (hosted URL)")) if prow else ""
    dna = subject.get("DNA (Lark URL)") or ""
    site = (prow or {}).get("Website") or (brand_row or {}).get("Website") or next((r.get("Website") for r in rows_l if r.get("Website")), "")
    if rows_l and not product_name and not brand_row:
        missing.append("no brand row in the ledger (a brand video needs the brand's own DNA); products: " +
                       ", ".join(r.get("Product name") or "-" for r in rows_l))
    # a carousel uses no logo or colors from the ledger (its look comes from the site); Echo needs the DNA
    for what, v in ((("DNA", dna),) if carousel else (("logo", logo), ("brand colors", colors), ("DNA", dna))):
        if rows_l and not v: missing.append(f"no {what} in the ledger")
    if carousel and product_name and prow is None:
        sys.exit(f"product {product_name!r} is not in the Client Ledger for {brand}: a carousel needs its row (and Website)")
    if carousel and not site:
        sys.exit(f"no Website for {brand}" + (f" / {product_name}" if product_name else "") +
                 " in the Client Ledger: a carousel is made from the website; add it there first")

    template = {c: "" for c in sheet.COLS}
    template.update({"Brand": brand, "Output type": otype, "Duration": opt(a, "--duration"), "Style": style,
                     "Product": prod_img, "Brand logo": logo, "Brand color": colors,
                     "Style ref": opt(a, "--style-ref"), "Source video": opt(a, "--source"),
                     "Avatar image": opt(a, "--avatar-image"),
                     "Avatar voice": opt(a, "--avatar-voice"), "Music": opt(a, "--music"),
                     "Instructions": opt(a, "--instructions")})

    if carousel:
        # only the angle (Echo, into Script) and the website reach the carousel designer (the owner's
        # decisions, 2026-10-27): no product image, logo or colors from the ledger
        template.update({"Product": "", "Brand logo": "", "Brand color": ""}); logo = colors = prod_img = ""
        if prow: template["Instructions"] = ((template["Instructions"] or "") + f" Product: {prow['Product name']}.").strip()

    # Cloner and Re-skit write their own lines, so they get the brand's DNA in the request
    # (the owner's rule, 2026-10-24: Vega supplies the DNA to every designer that needs it)
    if (style or "").strip().lower() in ("clone", "re-skit"):
        if not template["Source video"]: sys.exit("--source is required for clone and re-skit (the video to work from)")
        if dna: template["Instructions"] = ((template["Instructions"] or "") + f" Brand DNA: {dna}").strip()
    # and the brand's website: for brand info and UI screenshots (Cloner and Re-skit, 2026-10-24),
    # and as the carousel's source (every carousel style, 2026-10-27)
    if (style or "").strip().lower() in ("clone", "re-skit") or carousel:
        if site: template["Instructions"] = ((template["Instructions"] or "") + f" Brand website: {site}").strip()

    # ---- check everything before a single number is issued ----
    if otype not in sheet.OUTPUT_TYPES: sys.exit(f"--type must be one of: {', '.join(sorted(sheet.OUTPUT_TYPES))}")
    if "--repurpose" in a: sys.exit("--repurpose was removed (2026-10-24): no repurpose videos are made")
    sheet.check_style(style); sheet.check_duration(template)

    if opt(a, "--sheet"):
        path = Path(opt(a, "--sheet")); path = (path if path.is_absolute() else SUPER / path).resolve()
        if not path.is_file() or not path.is_relative_to(BATCHES): sys.exit(f"--sheet must be an existing sheet in {BATCHES}")
        new_sheet = False
    else:
        label = key(opt(a, "--label") or brand).lower() or "batch"
        path = BATCHES / f"atlas-batch-{date.today():%Y-%m-%d}-{label}.md"; k = 2
        while path.exists(): path = BATCHES / f"atlas-batch-{date.today():%Y-%m-%d}-{label}-{k}.md"; k += 1
        new_sheet = True

    # ---- numbers ----
    res = subprocess.run([sys.executable, str(TASK_TOOL), "next", brand, str(n)], capture_output=True, text=True)
    if res.returncode != 0: sys.exit(f"numbers tool failed: {(res.stderr or res.stdout).strip()}")
    issued = [json.loads(l) for l in res.stdout.splitlines() if l.strip()]

    def release_all(why):
        for t in issued:
            subprocess.run([sys.executable, str(TASK_TOOL), "release", t["task_id"]], capture_output=True)
        sys.exit(f"{why}; the {len(issued)} numbers were released again")

    # ---- sheet: create if new, add every row, save once ----
    try:
        if new_sheet:
            with redirect_stdout(io.StringIO()): sheet.create(path)
        rows, handle = sheet.load(path)
        for r in rows:
            for c in sheet.COLS: r.setdefault(c, "")
        taken = {r["Task ID"] for r in rows}
        for t in issued:
            if t["task_id"] in taken: release_all(f"Task ID {t['task_id']} is already in the sheet")
            row = dict(template, **{"Task ID": t["task_id"], "Brand number": t["brand_number"]})
            row["Status"] = "pending" if not sheet.needs_script(row) else "draft"
            rows.append(row)
        sheet.save(path, rows, handle)
    except SystemExit:
        raise
    except Exception as e:
        if new_sheet and path.exists(): path.unlink()        # nothing was saved into it
        release_all(f"could not write the sheet ({e})")

    status = "pending (scriptless)" if not sheet.needs_script(template) else "draft (waiting for Echo)"
    line = {
        "sheet": str(path.relative_to(SUPER)), "brand": key(brand) or "Brandless", "rows": n,
        "task_ids": ranges([t["task_id"] for t in issued]),
        "brand_numbers": ranges([t["brand_number"] for t in issued]),
        "status": status,
        "from_ledger": {"logo": bool(logo), "colors": bool(colors), "product_image": bool(prod_img)},
        "product": (prow or {}).get("Product name") or None,
                "dna": dna or None, "brandless": brandless,
        "missing": missing}
    if carousel: line["website"] = site         # what the carousel designer works from
    print(json.dumps(line))

if __name__ == "__main__":
    main()
