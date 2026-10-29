#!/usr/bin/env python3
"""The podcast designer's tool: every mechanical step of a podcast video, so the session never
writes shell loops (the approved tool list refuses them). Prints short lines; exit 1 on a problem.

  python3 <podcast>/tools/podcast.py <command> <materials folder> [...]

<materials> is the video's materials folder, <root>/editable/materials/<name>/. It holds
script.txt and cast.json (both written by you), and everything the tool writes:

  lines      Read script.txt + cast.json -> lines.json (one entry per line, in script order).
  split <two-shot image>
             Cut the 16:9 two-shot in half -> persona/left.png, persona/right.png, and pad each
             to a square with black on its left and right (no crop) -> persona/left-sq.png, right-sq.png.
  join       Join the lines in order with a 0.35 s pause between turns -> vo.mp3, and note every
             line's start and end (lines.json).
  mark prelap <n> [...] | mark listen <n> [...] | mark clear
             Plan the shots. prelap <n>: the cut to line n lands before line n-1 ends.
             listen <n>: line n is a listening shot (split screen with line n-1's speaker).
  pad        Pad each line's audio for its plan -> lines/NN_TAG-pad.mp3, and set each clip's
             start on the timeline (lines.json clip_start).
  check      Every clip's length matches its padded audio, and the pre-lap and listening
             silences are still in the clip.
  align      Scribe (Whisper as fallback; shared make-timings.py) on vo.mp3, then the words aligned to the script:
             the script's spelling with Whisper's timing, each word with its speaker and line
             -> timings.json.
  captions   Caption groups: at most 3 words, broken at punctuation, quoted phrases kept
             together, never across speakers -> captions.json.
  music      Measure vo.mp3 and bgm.mp3 and print the bgm tag's data-volume (music about 16 dB
             under the voices) and data-under.
  black <render.mp4>
             Look for black in the finished video: whole black frames and black bands at the
             edges or on the split-screen seam. Prints the times; none means clean.

This tool makes no generation and no upload: the voices (lines/NN_TAG.mp3) and the talking clips
(clips/NN_TAG.mp4) are generated with submit_ai_job / wait_ai_job, and the padded halves and
padded lines are hosted with host_file, all by you (see the skill). Every generation is recorded
in the video's metadata file (assets, with its credits), written by hand.
"""
import json, re, subprocess, sys
from difflib import SequenceMatcher
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parents[1] / "DesignerShared"
PAUSE = 0.35          # seconds between turns
PRELAP = 1.0          # silence added to the start of a pre-lap clip
MIN_PRELAP_LINE = 1.5 # never pre-lap out of a line shorter than this

# ---------- helpers ----------
def die(msg): print(msg); sys.exit(1)
def load(p, default=None):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else default
def save(p, d): Path(p).write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
def run(cmd, timeout=3600):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0: raise RuntimeError((r.stderr or r.stdout).strip()[-400:])
    return r.stdout
def dur(f):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]).strip())
def now(): return datetime.now().strftime("%Y-%m-%dT%H:%M")

def lines_of(m):
    L = load(m / "lines.json")
    if not L: die("no lines.json: run `lines` first")
    return L

def meta_add(m, entry):
    """Append an asset entry to <root>/metadata/<name>.json, if it exists."""
    root = m.parents[2]; mf = root / "metadata" / f"{m.name}.json"
    d = load(mf)
    if d is None: return
    d.setdefault("assets", []).append(dict({"status": "in-use", "source": None, "generated": now(), "replaced_by": None}, **entry))
    save(mf, d)

def retire(m, f):
    """A file about to be replaced moves to the materials deletable/ folder (never deleted), and its
    metadata entry follows it."""
    f = Path(f)
    if not f.exists(): return
    dd = m / "deletable"; dd.mkdir(exist_ok=True)
    new = dd / f.name; k = 2
    while new.exists(): new = dd / f"{f.stem}_{k}{f.suffix}"; k += 1
    f.rename(new)
    mf = m.parents[2] / "metadata" / f"{m.name}.json"; d = load(mf)
    if d:
        for e in d.get("assets", []):
            if e.get("file") == str(f) and e.get("status") == "in-use":
                e.update(status="deletable", file=str(new), replaced_by=str(f))
        save(mf, d)

def pick(L, only):
    if not only: return L
    want = {int(x) for x in only.split(",") if x.strip()}
    return [l for l in L if l["n"] in want]

def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default

# ---------- lines ----------
LABEL = re.compile(r"(?:^|(?<=[\s.!?\"”'’)\]]))([A-Z][\w'’.-]*(?: [A-Z][\w'’.-]*)?):\s")

def cmd_lines(m, a):
    script = (m / "script.txt").read_text(encoding="utf-8").strip()
    cast = load(m / "cast.json") or die("no cast.json: write it first (see the skill)")
    speakers = cast.get("speakers") or die("cast.json has no speakers")
    if len(speakers) != 2: die(f"cast.json must have exactly 2 speakers, has {len(speakers)}")
    voices = [s.get("voice") for s in speakers.values()]
    if len(set(voices)) != 2 or not all(voices): die("the two speakers must have two different voices")
    if {s.get("side") for s in speakers.values()} != {"left", "right"}: die("one speaker is side left, the other side right")
    tags = [s.get("tag") for s in speakers.values()]
    if len(set(tags)) != 2 or not all(tags): die("the two speakers need two different tags (M/F, M1/M2, or F1/F2)")
    names = sorted(speakers, key=len, reverse=True)
    pat = re.compile(r"(?:^|(?<=[\s\"”'’)\]]))(" + "|".join(re.escape(n) for n in names) + r"):\s*")
    parts = pat.split(script)
    if parts[0].strip(): die(f"text before the first speaker label: {parts[0].strip()[:80]!r}")
    L = []
    for i in range(1, len(parts), 2):
        text = " ".join(parts[i + 1].split())
        if not text: continue
        sp = parts[i]; s = speakers[sp]; n = len(L) + 1
        L.append({"n": n, "speaker": sp, "tag": s["tag"], "side": s["side"], "voice": s["voice"],
                  "file": f"{n:02d}_{s['tag']}", "text": text, "say": text})
    if not L: die("no lines found: every turn starts with a speaker label from cast.json and a colon")
    unknown = set(LABEL.findall(script)) - set(speakers)
    old = {l["n"]: l for l in (load(m / "lines.json") or [])}
    for l in L:   # keep a reword already written into `say` when the text is unchanged
        o = old.get(l["n"])
        if o and o.get("text") == l["text"]: l["say"] = o.get("say", l["text"])
    save(m / "lines.json", L)
    for l in L: print(f"{l['file']}  {l['text'][:90]}")
    if unknown: print(f"note: label-like words not in cast.json, left inside the text: {sorted(unknown)}")
    print(f"{len(L)} lines -> lines.json")

# ---------- split ----------
def cmd_split(m, a):
    from PIL import Image
    src = Path(a[0]) if a else die("split <two-shot image>")
    im = Image.open(src).convert("RGB"); W, H = im.size
    out = m / "persona"; out.mkdir(exist_ok=True)
    half = W // 2
    for side, box in (("left", (0, 0, half, H)), ("right", (W - half, 0, W, H))):
        h = im.crop(box); h.save(out / f"{side}.png")
        side_len = max(h.size)
        sq = Image.new("RGB", (side_len, side_len), "black")
        sq.paste(h, ((side_len - h.size[0]) // 2, (side_len - h.size[1]) // 2))
        sq.save(out / f"{side}-sq.png")
        print(f"persona/{side}.png {h.size[0]}x{h.size[1]} -> persona/{side}-sq.png {side_len}x{side_len} "
              f"(picture {h.size[0]} wide in the middle, {(side_len - h.size[0]) // 2} px black each side)")

# ---------- join ----------
def cmd_join(m, a):
    L = lines_of(m); t = 0.0; inputs = []; fc = []
    sil = m / "lines" / "_pause.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(PAUSE), str(sil)])
    k = 0
    for i, l in enumerate(L):
        f = m / "lines" / f"{l['file']}.mp3"
        if not f.exists(): die(f"missing {f.name}: generate the line voices first")
        d = dur(f); l["dur"] = round(d, 3); l["start"] = round(t, 3); l["end"] = round(t + d, 3); t += d
        inputs += ["-i", str(f)]; fc.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=mono[a{k}]"); k += 1
        if i < len(L) - 1:
            inputs += ["-i", str(sil)]; fc.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=mono[a{k}]"); k += 1; t += PAUSE
    fc.append("".join(f"[a{j}]" for j in range(k)) + f"concat=n={k}:v=0:a=1[out]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2", str(m / "vo.mp3")])
    sil.unlink(missing_ok=True)
    save(m / "lines.json", L)
    for l in L: print(f"{l['file']}  {l['start']:7.2f} - {l['end']:7.2f}  ({l['dur']:.2f}s)")
    print(f"vo.mp3 {dur(m / 'vo.mp3'):.2f}s")

# ---------- mark ----------
def cmd_mark(m, a):
    L = lines_of(m); by = {l["n"]: l for l in L}
    if not a: die("mark prelap <n> ... | mark listen <n> ... | mark clear")
    if a[0] == "clear":
        for l in L: l["prelap"] = False; l["listen"] = False
        save(m / "lines.json", L); print("plan cleared"); return
    kind = a[0]
    if kind not in ("prelap", "listen"): die("mark prelap | listen | clear")
    if any("dur" not in l for l in L): die("run `join` first: the plan needs every line's length")
    for x in a[1:]:
        n = int(x); l = by.get(n) or die(f"no line {n}")
        prev = by.get(n - 1)
        if not prev or prev["speaker"] == l["speaker"]:
            die(f"line {n}: the line before it must be the other person's")
        if kind == "prelap" and prev["dur"] < MIN_PRELAP_LINE:
            die(f"line {n}: line {n - 1} is {prev['dur']:.2f}s, shorter than {MIN_PRELAP_LINE}s: no pre-lap out of it")
        l[kind] = True
    save(m / "lines.json", L)
    print("pre-lap: " + (", ".join(str(l["n"]) for l in L if l.get("prelap")) or "none"))
    print("listening: " + (", ".join(str(l["n"]) for l in L if l.get("listen")) or "none"))

# ---------- pad ----------
def cmd_pad(m, a):
    L = lines_of(m); by = {l["n"]: l for l in L}
    if any("dur" not in l for l in L): die("run `join` first")
    for l in L: l["pad_start"] = PRELAP if l.get("prelap") else 0.0; l["pad_end"] = 0.0
    for l in L:
        if l.get("listen"): by[l["n"] - 1]["pad_end"] = round(PAUSE + l["dur"] + PAUSE, 3)
    for l in L:
        src = m / "lines" / f"{l['file']}.mp3"; dst = m / "lines" / f"{l['file']}-pad.mp3"
        ms = int(round(l["pad_start"] * 1000))
        af = f"adelay={ms}:all=1," if ms else ""
        af += f"apad=pad_dur={l['pad_end']}" if l["pad_end"] else "anull"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", af, "-c:a", "libmp3lame", "-q:a", "2", str(dst)])
        l["pad_dur"] = round(dur(dst), 3); l["clip_start"] = round(l["start"] - l["pad_start"], 3)
        print(f"{dst.name}  +{l['pad_start']:.2f}s start, +{l['pad_end']:.2f}s end -> {l['pad_dur']:.2f}s, clip starts at {l['clip_start']:.2f}s")
    save(m / "lines.json", L)

# ---------- check ----------
def silent_spans(f):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", str(f), "-af", "silencedetect=noise=-40dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    total = dur(f)
    return [(s, en[i] if i < len(en) else total) for i, s in enumerate(st)]

def cmd_check(m, a):
    L = lines_of(m); bad = []
    for l in L:
        c = m / "clips" / f"{l['file']}.mp4"
        if not c.exists(): bad.append(f"{l['file']}: no clip"); continue
        d = dur(c); p = []
        if abs(d - l["pad_dur"]) > 0.2: p.append(f"length {d:.2f}s, audio {l['pad_dur']:.2f}s")
        sp = silent_spans(c) if (l.get("pad_start") or l.get("pad_end")) else []
        if l.get("pad_start") and not any(s <= 0.1 and e >= l["pad_start"] - 0.25 for s, e in sp):
            p.append("pre-lap silence missing at the start")
        if l.get("pad_end") and not any(e >= d - 0.15 and s <= d - l["pad_end"] + 0.4 for s, e in sp):
            p.append("listening silence missing at the end")
        print(f"{l['file']}  {d:.2f}s  " + ("ok" if not p else "PROBLEM: " + "; ".join(p)))
        if p: bad.append(f"{l['file']}: " + "; ".join(p))
    if bad: die(f"{len(bad)} clip(s) need a fix")
    print("all clips ok")

# ---------- align ----------
def norm(w): return re.sub(r"[^\w]", "", w.lower().replace("’", "'"))

def cmd_align(m, a):
    L = lines_of(m)
    run(["python3", str(SHARED / "tools" / "make-timings.py"), str(m / "vo.mp3")])
    T = load(m / "timings.json"); hw = T["words"]
    sw = [(w, l) for l in L for w in l["text"].split()]
    A = [norm(w["w"]) for w in hw]; B = [norm(w) for w, _ in sw]
    times = [None] * len(sw)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(j2 - j1): times[j1 + k] = (hw[i1 + k]["s"], hw[i1 + k]["e"])
        elif tag == "replace":   # different word counts: spread Whisper's span over the script words
            s0, e0 = hw[i1]["s"], hw[i2 - 1]["e"]; n = j2 - j1
            for k in range(n): times[j1 + k] = (s0 + (e0 - s0) * k / n, s0 + (e0 - s0) * (k + 1) / n)
    for j, t in enumerate(times):   # words Whisper missed: fill inside their line, between neighbours
        if t is None:
            l = sw[j][1]; prev = next((times[k][1] for k in range(j - 1, -1, -1) if times[k] and sw[k][1] is l), l["start"])
            nxt = next((times[k][0] for k in range(j + 1, len(sw)) if times[k] and sw[k][1] is l), l["end"])
            times[j] = (prev, max(prev, nxt))
    for j, (w, l) in enumerate(sw):   # every word stays inside its own line
        s, e = times[j]; s = min(max(s, l["start"]), l["end"]); e = min(max(e, s), l["end"]); times[j] = (s, e)
    words = [{"w": w, "s": round(times[j][0], 2), "e": round(times[j][1], 2), "sp": l["speaker"], "line": l["n"]} for j, (w, l) in enumerate(sw)]
    missed = sum(1 for t in SequenceMatcher(None, A, B, autojunk=False).get_opcodes() if t[0] in ("insert", "delete"))
    T["words"] = words; T["duration"] = words[-1]["e"]; T["aligned_to_script"] = True
    save(m / "timings.json", T)
    print(f"{len(words)} script words timed ({len(hw)} heard by Whisper, {missed} gap(s) filled) -> timings.json; last word ends {words[-1]['e']:.2f}s")

# ---------- captions ----------
def cmd_captions(m, a):
    T = load(m / "timings.json") or die("run `align` first")
    if not T.get("aligned_to_script"): die("timings.json is not aligned to the script: run `align`")
    W = T["words"]; groups = []; cur = []; quote = False
    def flush():
        nonlocal cur
        if cur: groups.append({"s": cur[0]["s"], "e": cur[-1]["e"], "sp": cur[0]["sp"], "line": cur[0]["line"],
                               "words": [{"w": x["w"], "s": x["s"], "e": x["e"]} for x in cur]})
        cur = []
    for i, w in enumerate(W):
        if cur and (w["line"] != cur[-1]["line"]): flush(); quote = False
        opens = bool(re.match(r"^[\"“‘']", w["w"])); closes = bool(re.search(r"[\"”’']\W*$", w["w"])) and not (opens and len(w["w"]) < 2)
        if opens and not closes and cur and not quote:
            # a quoted phrase starts: give it its own caption when it fits in 3 words
            j = i; k = 0
            while j < len(W) and W[j]["line"] == w["line"] and k < 4:
                if re.search(r"[\"”’']\W*$", W[j]["w"]) and j != i: break
                j += 1; k += 1
            if k < 3: flush()
        if opens and not closes: quote = True
        cur.append(w)
        if closes:
            quote = False; flush(); continue   # a quoted phrase ends its caption
        end_punct = bool(re.search(r"[.,!?;:—–…]\W*$", w["w"]))
        if (len(cur) >= 3 and not quote) or (end_punct and not quote): flush()
        elif quote and len(cur) >= 3:
            flush()
    flush()
    save(m / "captions.json", groups)
    print(f"{len(groups)} captions -> captions.json")
    for g in groups[:6]: print(f"  {g['s']:6.2f}-{g['e']:6.2f} {g['sp']}: {' '.join(x['w'] for x in g['words'])}")

# ---------- music ----------
def lufs(f):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(f), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    v = re.findall(r"I:\s+(-?[0-9.]+) LUFS", out)
    if not v: die(f"could not measure {f.name}")
    return float(v[-1])

def cmd_music(m, a):
    vo, bgm = m / "vo.mp3", m / "bgm.mp3"
    if not bgm.exists(): die("no bgm.mp3")
    vi, bi = lufs(vo), lufs(bgm)
    vol = min(1.0, 10 ** (((vi - 16) - bi) / 20))
    print(f"voices {vi:.1f} LUFS, music {bi:.1f} LUFS -> music 16 dB under the voices")
    print(f'set on the bgm tag: data-volume="{vol:.3f}" data-under="16"')

# ---------- black ----------
def cmd_black(m, a):
    from PIL import Image, ImageStat
    import tempfile
    v = Path(m)
    with tempfile.TemporaryDirectory(prefix="podcast-black-") as td:
        run(["ffmpeg", "-v", "error", "-i", str(v), "-vf", "fps=10,scale=270:480", str(Path(td) / "f%05d.png")])
        frames = sorted(Path(td).glob("f*.png")); hits = []
        for i, f in enumerate(frames):
            im = Image.open(f).convert("L"); w, h = im.size
            def dark(box):
                return ImageStat.Stat(im.crop(box)).mean[0] < 10
            why = []
            if dark((0, 0, w, h)): why.append("whole frame")
            else:
                if dark((0, 0, 4, h)): why.append("left edge")
                if dark((w - 4, 0, w, h)): why.append("right edge")
                if dark((0, 0, w, 3)): why.append("top edge")
                if dark((0, h - 3, w, h)): why.append("bottom edge")
                if dark((0, h // 2 - 2, w, h // 2 + 2)): why.append("seam")
            if why: hits.append((i / 10, ", ".join(why)))
    if not hits: print("no black found"); return
    spans = []
    for t, why in hits:
        if spans and spans[-1][2] == why and t - spans[-1][1] <= 0.15: spans[-1][1] = t
        else: spans.append([t, t, why])
    for s, e, why in spans: print(f"BLACK {s:.1f}s-{e + 0.1:.1f}s: {why}")
    die(f"{len(spans)} black span(s)")

CMDS = {"lines": cmd_lines, "split": cmd_split, "join": cmd_join, "mark": cmd_mark, "pad": cmd_pad,
        "check": cmd_check, "align": cmd_align, "captions": cmd_captions,
        "music": cmd_music, "black": cmd_black}

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in CMDS: sys.exit(__doc__)
    target = Path(a[1]).expanduser().resolve()
    if a[0] != "black" and not target.is_dir(): die(f"no materials folder at {target}")
    CMDS[a[0]](target, a[2:])
