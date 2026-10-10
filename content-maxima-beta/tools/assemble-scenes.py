#!/usr/bin/env python3
"""Assemble scene fragments written in parallel into the editable.

  python3 tools/assemble-scenes.py <root>/editable/<name>.html [s1 s3 ...]

The skeleton (stage skill section 3b) holds one marker pair per scene: inside
the scene's container `<!-- scene:sN -->` ... `<!-- /scene:sN -->`, and in the
video CSS `/* scene:sN */` ... `/* /scene:sN */`. Each subagent writes its scenes
to materials/<name>/scenes/sN.html (the container's inner markup) and
scenes/sN.css (rules scoped to #sN). This tool checks every fragment, then puts
each one between its markers, replacing whatever was there. Without scene ids
it takes every scene that has a fragment.

Checks, one line each, and nothing is written while any fails:
  * a scene with a fragment but no marker pair in the editable
  * <script> or <style> in a fragment (video JS belongs to the session; CSS to sN.css)
  * a CSS rule not scoped to #sN, or an @keyframes not named sN-...; @font-face,
    @import and @media (the fonts are declared in the skeleton; rule 1, rule 8)
  * transition, animation-play-state, animation: none, vw/vh units (rules 1, 5, 9)
  * a materials/ file that does not exist or sits in deletable/ or jobs/
  * an id used twice, across the fragments and the editable
A scene with markers but no fragment is reported and left as it is.

Assembly is one-shot: on success scenes/ moves to deletable/scenes/ and the
editable is the only source from then on; audit fixes go into the editable.
"""
import pathlib, re, shutil, sys

HTML_MARK = ("<!-- scene:{s} -->", "<!-- /scene:{s} -->")
CSS_MARK = ("/* scene:{s} */", "/* /scene:{s} */")


def block_re(start, end):
    return re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.S)


def css_rules(css):
    """(selector-or-at-rule, body) for each top-level block, comments stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, depth, start = [], 0, 0
    for i, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                head = css[start:i].strip()
                body_start = i + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append((head, css[body_start:i]))
                start = i + 1
    return out


def check_css(scene, css, problems):
    for head, body in css_rules(css):
        if head.startswith("@keyframes"):
            name = head.split(None, 1)[1].strip() if " " in head else ""
            if not name.startswith(f"{scene}-"):
                problems.append(f"{scene}.css: @keyframes {name or '?'} must be named {scene}-<something>, so no two scenes define the same animation")
        elif head.startswith("@"):
            problems.append(f"{scene}.css: {head.split()[0]} is not allowed in a fragment (fonts are declared in the skeleton; no media queries, no imports)")
        else:
            for sel in head.split(","):
                sel = sel.strip()
                if not re.match(rf"#{re.escape(scene)}(?![\w-])", sel):
                    problems.append(f"{scene}.css: selector `{sel}` is not scoped to #{scene}; write `#{scene} {sel}`")
        if re.search(r"\btransition\s*:", body):
            problems.append(f"{scene}.css: `transition` in `{head}`; timed motion is @keyframes + animation (rule 5)")
        if re.search(r"animation-play-state", body) or re.search(r"\banimation\s*:\s*none\b", body):
            problems.append(f"{scene}.css: `{head}` sets animation-play-state or animation: none; the harness owns those (rule 9)")
        if re.search(r"\d(vw|vh)\b", head + body):
            problems.append(f"{scene}.css: `{head}` uses vw/vh; layout is absolute px on the 1080 x 1920 canvas (rule 1)")


def refs(text):
    return [m[1] or m[2] for m in re.finditer(r"""(?:src|href)=["'](materials/[^"']+)|url\(\s*["']?(materials/[^"')]+)""", text)]


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: assemble-scenes.py <root>/editable/<name>.html [s1 s3 ...]")
    ed = pathlib.Path(args[0]).resolve()
    only = set(args[1:])
    name = ed.stem
    mat = ed.parent / "materials" / name
    scenes_dir = mat / "scenes"
    if not scenes_dir.is_dir():
        sys.exit(f"assemble-scenes: no {scenes_dir.relative_to(ed.parent)}/; the subagents write their fragments there")

    frags = sorted(scenes_dir.glob("s*.html"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    scenes = [p.stem for p in frags if not only or p.stem in only]
    if not scenes:
        sys.exit("assemble-scenes: no fragments to assemble")

    text = ed.read_text(encoding="utf-8")
    problems, html_frag, css_frag = [], {}, {}
    # Ids already in the editable, minus what sits between the markers being
    # replaced, so a fragment can be assembled again over its own earlier version.
    kept = text
    for s in scenes:
        hs, he = (x.format(s=s) for x in HTML_MARK)
        kept = block_re(hs, he).sub(lambda _: "", kept, count=1)
    seen_ids = {}
    for m in re.finditer(r'\bid="([^"]+)"', kept):
        seen_ids.setdefault(m.group(1), "the editable")

    for s in scenes:
        hp, cp = scenes_dir / f"{s}.html", scenes_dir / f"{s}.css"
        h = hp.read_text(encoding="utf-8")
        c = cp.read_text(encoding="utf-8") if cp.exists() else ""
        if not cp.exists():
            problems.append(f"{s}: scenes/{s}.css is missing (write an empty file if the scene needs no CSS of its own)")
        hs, he = (x.format(s=s) for x in HTML_MARK)
        cs, ce = (x.format(s=s) for x in CSS_MARK)
        if not block_re(hs, he).search(text):
            problems.append(f"{s}: the editable has no `{hs}` ... `{he}` inside #{s}; add the marker pair to the skeleton")
        if not block_re(cs, ce).search(text):
            problems.append(f"{s}: the editable has no `{cs}` ... `{ce}` in the video CSS; add the marker pair to the skeleton")
        if re.search(r"<\s*(script|style)\b", h, re.I):
            problems.append(f"{s}.html: contains <script> or <style>; a fragment is markup only, its CSS goes in {s}.css")
        if "<!-- scene:" in h or "/* scene:" in c:
            problems.append(f"{s}: a fragment must not contain scene markers of its own")
        for m in re.finditer(r'\bid="([^"]+)"', h):
            i = m.group(1)
            if i in seen_ids:
                problems.append(f"{s}.html: id `{i}` is already used in {seen_ids[i]}")
            else:
                seen_ids[i] = f"{s}.html"
        for ref in refs(h) + refs(c):
            if re.search(r"/(deletable|jobs)/", ref):
                problems.append(f"{s}: references {ref}, which is in deletable/ or jobs/")
            elif not (ed.parent / ref).exists():
                problems.append(f"{s}: references {ref}, which does not exist")
        check_css(s, c, problems)
        html_frag[s], css_frag[s] = h, c

    pending = [m.group(1) for m in re.finditer(r"<!-- scene:(s\d+) -->", text) if m.group(1) not in html_frag]

    if problems:
        print("\n".join(problems))
        print(f"assemble-scenes: {len(problems)} problem(s); nothing written")
        sys.exit(1)

    for s in scenes:
        hs, he = (x.format(s=s) for x in HTML_MARK)
        cs, ce = (x.format(s=s) for x in CSS_MARK)
        text = block_re(hs, he).sub(lambda _: f"{hs}\n{html_frag[s].strip()}\n{he}", text, count=1)
        text = block_re(cs, ce).sub(lambda _: f"{cs}\n{css_frag[s].strip()}\n{ce}", text, count=1)
        print(f"{s}: {len(html_frag[s])} bytes markup, {len(css_frag[s])} bytes CSS")
    ed.write_text(text, encoding="utf-8")

    deletable = mat / "deletable"
    deletable.mkdir(exist_ok=True)
    dest = deletable / "scenes"
    n = 2
    while dest.exists():
        dest = deletable / f"scenes_{n}"
        n += 1
    shutil.move(str(scenes_dir), str(dest))
    print(f"assembled {len(scenes)} scene(s) into {ed.name}; fragments moved to {dest.relative_to(mat).as_posix()}/")
    if pending:
        print(f"no fragment yet for: {', '.join(pending)} (their markers are left as they are)")


if __name__ == "__main__":
    main()
