#!/usr/bin/env python3
"""The Re-skit designer's tool: every mechanical step that is not a generation or the build, so
the session never writes shell loops or temp-file juggling (the approved tool list refuses them).
Prints short lines; exits non-zero on a problem.

  python3 <reskit>/tools/reskit.py <command> ...

  new "<Brand>" <Task ID> --brand-number <n> [--topic "<two to four words>"] [--date MM-DD]
        Create the video's files exactly as the shared file-management skill lays them out:
        <root>/editable/NN-name-MM-DD.html (the editable page), its materials folder with
        source/ assets/ gen/ref/ gen/out/ music/ deletable/, plan.md, edit.json (empty build),
        metadata/NN-name-MM-DD.json, renders/deletable/. NN is the Task ID. Never overwrites:
        on a resumed session it prints the existing paths. --topic only for Brandless.
  fetch <materials> "<link or local path>"
        Get the source video into source/source.mp4 (yt-dlp for a link, ffmpeg as the
        fallback for a direct video URL; a local file is copied). Saves the link's info as source/info.json and
        records the source in the metadata.
  probe <video> [--scene 0.3]
        Length, size, fps, audio, and every scene change (each camera setup becomes one clip).
  frames <video> <out dir> [--every 0.5] [--width 270] [--from S] [--to S]
        Frames every N seconds as JPGs plus one contact sheet (contact.jpg, 6 across, in time
        order; the times are printed). Read the sheet to describe every shot and gesture.
  still <video> <seconds> <out.png>
        One full-resolution frame (for a plate or a check).
  dna <materials> "<DNA file path>"
        Copy the brand's DNA file into source/dna.md. Prints its size.
  mask <video> <out.png> <x0> <x1> <y0> <y1> [--th 228] [--dilate 14] [--times t1,t2,...]
        A mask of the burned-in caption for ffmpeg removelogo: darken-blend frames from across
        the video so the moving person drops out, keep the bright text inside the box, and
        dilate generously (a thin mask leaves ghost letters). Default 8 evenly spaced times.
  cutref <video> <start> <usable_len> <whole_seconds> <out.mp4> [--mask mask.png]
        One person-replacement reference clip: one camera setup, whole seconds, no audio,
        30 fps, caption masked, last frame held when the usable part is shorter. Trims on the
        INPUT side so the hold really happens, then reports any scene change inside (there
        must be none: end it a few frames before the next shot).
  strip <source.mp4> <clip.mp4> <out.jpg> --offset <clip start in source> [--times a,b,c]
        Source frames (top row) above the generated clip's frames (bottom row) at the same
        moments, to check identity, outfit, room, props, hands, leftover text and motion.
  safe <image.png> <out.png>
        Draw the social-platform safe area over a 1080x1920 frame (red = covered by the app).
  audio-probe <file> [--drop] [--from S] [--to S]
        Tempo candidates (may read double or half time), brightness, bass share, energy by
        eighths, and with --drop the biggest quiet-to-loud jump. Needs numpy.
  loudness <file>
        Integrated loudness (LUFS) and true peak, with ffmpeg ebur128.
  lesson <materials> "<lesson>"
        Propose a lesson: appended to the metadata's "lessons" list (Vega decides; this tool
        never writes to the skill or its references).
"""
import json, math, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reskit_common import (PROJECT, SHARED, UA, MATERIAL_DIRS, Video, brand_key, video_name, update_meta,
                           read_meta, write_editable, ffprobe_json, duration, loudness, scene_changes, now, to_deletable, scratch_profile)


def opt(a, flag, default=None):
    if flag in a:
        i = a.index(flag); v = a[i + 1]; del a[i:i + 2]; return v
    return default


def flag(a, name):
    if name in a:
        a.remove(name); return True
    return False


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"{Path(str(cmd[0])).name} failed: {(r.stderr or r.stdout).strip()[-600:]}")
    return r


# ---------------------------------------------------------------- new
def cmd_new(a):
    topic = opt(a, "--topic"); date = opt(a, "--date"); bno = opt(a, "--brand-number", "")
    if len(a) < 2: sys.exit("usage: new \"<Brand>\" <Task ID> --brand-number <n> [--topic ...] [--date MM-DD]")
    brand, task = a[0], a[1]
    if not str(task).strip().isdigit(): sys.exit(f"Task ID must be a number, not {task!r}")
    root = PROJECT / brand_key(brand)
    # A resumed session: reuse the video already made for this Task ID, whatever its date.
    nn = str(int(task)).zfill(2)
    existing = sorted((root / "metadata").glob(f"{nn}-*.json")) if (root / "metadata").is_dir() else []
    existing = [f for f in existing if str(json.loads(f.read_text() or "{}").get("task_id", "")).lstrip("0") == str(int(task))]
    if existing:
        v = Video(root / "editable" / "materials" / existing[0].stem / "x")
        print(json.dumps({"exists": True, "name": v.name, "root": str(v.root), "editable": str(v.editable),
                          "materials": str(v.materials), "metadata": str(v.metadata)}, indent=1))
        return
    name = video_name(brand, task, date, topic)
    mat = root / "editable" / "materials" / name
    for d in MATERIAL_DIRS: (mat / d).mkdir(parents=True, exist_ok=True)
    (root / "renders" / "deletable").mkdir(parents=True, exist_ok=True)
    (root / "metadata").mkdir(parents=True, exist_ok=True)
    v = Video(mat / "x")
    if not v.plan.exists():
        v.plan.write_text(f"# {name}\n\n## Source\n\n## Story\n\n## Keep / cut / rewrite\n\n| # | Source time | Source line or beat | Decision | New meaning / overlay | Truth row |\n|---|---|---|---|---|---|\n\n"
                          "## Persona and outfit\n\n## Generation plan\n\n| Label | Model | Settings | Expected credits |\n|---|---|---|---|\n\n"
                          "## Job log\n\n| Label | Job ID | Model | Settings | Credits | Render time |\n|---|---|---|---|---|---|\n")
    if not v.edit_json.exists():
        v.edit_json.write_text(json.dumps({"source": "source/source.mp4", "mask": "", "caption": "", "clips": {},
                                           "segments": [], "end_hold": 0, "overlays": [], "pop_cy": 1290,
                                           "audio": "source", "pitch_semitones": 0.6, "music": None,
                                           "music_under_lu": 20, "roomtone": None,
                                           "zoom": "crop=982:1745:49:118,scale=1080:1920", "cover": None}, indent=1) + "\n")
    created = now()[:10]
    update_meta(v, lambda d: d.update({
        "root": str(v.root), "task_id": str(task), "brand_number": str(bno or d.get("brand_number", "")), "name": name,
        "brand": v.brand, "style": "re-skit", "created": created, "editable": str(v.editable),
        "build": str(v.edit_json), "plan": str(v.plan), "source": d.get("source", {}), "story": d.get("story", ""),
        "persona": d.get("persona", {}), "music": d.get("music", {}), "jobs": d.get("jobs", []), "assets": d.get("assets", []),
        "renders": d.get("renders", []), "credits_total": d.get("credits_total", 0), "lessons": d.get("lessons", []),
        "risks": d.get("risks", []), "unverified": d.get("unverified", [])}))
    write_editable(v, note="Created; nothing built yet.")
    print(json.dumps({"exists": False, "name": name, "root": str(v.root), "editable": str(v.editable),
                      "materials": str(v.materials), "metadata": str(v.metadata)}, indent=1))


# ---------------------------------------------------------------- fetch
def cmd_fetch(a):
    if len(a) < 2: sys.exit("usage: fetch <materials> <link or path>")
    v = Video(a[0]); src = a[1]; out = v.materials / "source" / "source.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    info = {}
    local = Path(src).expanduser()
    if local.exists():
        raw = local
    else:
        tmpl = str(v.materials / "source" / "download.%(ext)s")
        r = subprocess.run(["yt-dlp", "--no-playlist", "--no-progress", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
                            "--write-info-json", "-o", tmpl, src], capture_output=True, text=True)
        got = sorted((v.materials / "source").glob("download.*"))
        vids = [g for g in got if g.suffix in (".mp4", ".mkv", ".webm", ".mov")]
        if r.returncode != 0 or not vids:
            print(f"yt-dlp failed ({(r.stderr or '').strip()[-200:]}); trying ffmpeg on the link as a direct video URL", file=sys.stderr)
            raw = v.materials / "source" / "download.mp4"
            f = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c", "copy", str(raw)], capture_output=True, text=True)
            if f.returncode != 0 or not raw.exists():
                sys.exit(f"could not download {src}: {(f.stderr or r.stderr or '').strip()[-300:]}. "
                         "Save the video to source/download.mp4 with the ai tool's download action and run fetch again with that path.")
        else:
            raw = vids[0]
            js = sorted((v.materials / "source").glob("download*.info.json"))
            if js:
                full = json.loads(js[0].read_text())
                info = {k: full.get(k) for k in ("id", "title", "uploader", "uploader_id", "webpage_url", "duration",
                                                 "width", "height", "fps", "description", "upload_date", "track", "artist")}
                to_deletable(js[0], v.materials / "deletable")
    p = ffprobe_json(raw)
    vs = next((s for s in p.get("streams", []) if s.get("codec_type") == "video"), {})
    if raw.suffix == ".mp4" and vs.get("codec_name") == "h264":
        shutil.copy2(raw, out) if raw.resolve() != out.resolve() else None
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-c:v", "libx264", "-crf", "16", "-preset", scratch_profile.preset("intermediate"),
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    for g in sorted((v.materials / "source").glob("download*")):   # raw downloads: kept, out of the way
        if g.resolve() != out.resolve(): to_deletable(g, v.materials / "deletable")
    (v.materials / "source" / "info.json").write_text(json.dumps({"link": src, **info}, indent=1, ensure_ascii=False) + "\n")
    update_meta(v, lambda d: d.update({"source": {"link": src, "file": str(out), "title": info.get("title"),
                                                  "uploader": info.get("uploader"), "fetched": now()}, "stage": "fetched"}))
    cmd_probe([str(out)])


# ---------------------------------------------------------------- probe / frames / still
def cmd_probe(a):
    th = float(opt(a, "--scene", "0.3"))
    f = Path(a[0]); p = ffprobe_json(f)
    vs = next((s for s in p.get("streams", []) if s.get("codec_type") == "video"), {})
    au = [s for s in p.get("streams", []) if s.get("codec_type") == "audio"]
    num, den = (vs.get("r_frame_rate") or "0/1").split("/")
    fps = round(float(num) / float(den or 1), 3) if float(den or 1) else 0
    cuts = scene_changes(f, th)
    print(json.dumps({"file": str(f), "seconds": round(duration(f), 3), "size": f"{vs.get('width')}x{vs.get('height')}",
                      "fps": fps, "audio": [f"{s.get('codec_name')} {s.get('channels')}ch {s.get('sample_rate')}Hz" for s in au] or "none",
                      "scene_changes": cuts, "setups": len(cuts) + 1}, indent=1))


def cmd_frames(a):
    every = float(opt(a, "--every", "0.5")); width = int(opt(a, "--width", "270"))
    t0 = float(opt(a, "--from", "0")); t1 = opt(a, "--to")
    src, out = Path(a[0]), Path(a[1]); out.mkdir(parents=True, exist_ok=True)
    keep = "--keep-frames" in a
    end = float(t1) if t1 else duration(src)
    work = Path(tempfile.mkdtemp(prefix="reskit-frames-"))
    try:
        run(["ffmpeg", "-v", "error", "-y", "-ss", t0, "-t", max(0.1, end - t0), "-i", src, "-vf",
             f"fps=1/{every},scale={width}:-2", "-q:v", "4", work / "f%04d.jpg"])
        frames = sorted(work.glob("f*.jpg"))
        times = [round(t0 + i * every, 2) for i in range(len(frames))]
        for f, t in zip(frames, times):
            f.rename(work / f"t{t:07.2f}.jpg")
        cols = 6; rows = max(1, math.ceil(len(frames) / cols))
        run(["ffmpeg", "-v", "error", "-y", "-ss", t0, "-t", max(0.1, end - t0), "-i", src, "-vf",
             f"fps=1/{every},scale={width}:-2,tile={cols}x{rows}:padding=4:color=white", "-frames:v", "1", "-q:v", "3",
             work / "contact.jpg"])
        shutil.copy2(work / "contact.jpg", out / "contact.jpg")
        if keep:
            for f in work.glob("t*.jpg"): shutil.copy2(f, out / f.name)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(f"{len(frames)} frames; contact sheet {out / 'contact.jpg'} ({cols} across, left to right, top to bottom)"
          + (f"; frames in {out}" if keep else "; single frames: use `still` or add --keep-frames"))
    print("times:", " ".join(f"{t:.2f}" for t in times))


def cmd_still(a):
    src, t, out = a[0], a[1], a[2]
    run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", src, "-frames:v", "1", out])
    print(out)


# ---------------------------------------------------------------- dna
def cmd_dna(a):
    v = Video(a[0]); url = a[1]
    try:
        content = Path(url).expanduser().read_text(encoding="utf-8")
    except OSError as e:
        sys.exit(f"cannot read the DNA {url}: {e}")
    f = v.materials / "source" / "dna.md"; f.write_text(content, encoding="utf-8")
    print(f"{f} {f.stat().st_size} bytes")


# ---------------------------------------------------------------- mask / cutref
def cmd_mask(a):
    th = int(opt(a, "--th", "228")); dil = int(opt(a, "--dilate", "14")); times = opt(a, "--times")
    if len(a) < 6: sys.exit("usage: mask <video> <out.png> <x0> <x1> <y0> <y1> [--th 228] [--dilate 14] [--times a,b]")
    src, out, x0, x1, y0, y1 = a[0], a[1], *map(int, a[2:6])
    if times:
        ts = [float(t) for t in times.split(",")]
    else:
        d = duration(src); ts = [d * (i - 0.5) / 8.0 for i in range(1, 9)]
    if len(ts) < 2: sys.exit("give at least two sample times")
    args = []
    for t in ts: args += ["-ss", f"{t:.3f}", "-i", src]
    fc = "[0:v][1:v]blend=all_mode=darken[d1]"
    for i in range(2, len(ts)):
        fc += f";[d{i - 1}][{i}:v]blend=all_mode=darken[d{i}]"
    last = f"d{len(ts) - 1}"
    dils = ",".join(["dilation"] * dil)
    fc += (f";[{last}]format=gray,geq=lum='if(gt(lum(X\\,Y)\\,{th})*between(X\\,{x0}\\,{x1})*between(Y\\,{y0}\\,{y1})\\,255\\,0)'"
           + (f",{dils}" if dils else "") + "[m]")
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fc, "-map", "[m]", "-frames:v", "1", out])
    print(f"mask -> {out} (check: crop the caption area of a frame and of the mask side by side)")


def cmd_cutref(a):
    mask = opt(a, "--mask")
    if len(a) < 5: sys.exit("usage: cutref <video> <start> <usable_len> <whole_seconds> <out.mp4> [--mask m.png]")
    src, s, length, dur, out = a[0], float(a[1]), float(a[2]), a[3], Path(a[4])
    if not str(dur).isdigit(): sys.exit(f"the clip length must be whole seconds, not {dur}")
    dur = int(dur); pad = dur - length
    if pad < -0.001: sys.exit(f"usable length {length} is longer than the clip length {dur}: cut it shorter")
    if dur > 15: sys.exit("wan-3.0 takes at most 15 s of reference video")
    vf = "fps=30"
    if mask: vf += f",removelogo=filename='{Path(mask).resolve()}'"
    if pad > 0.001: vf += f",tpad=stop_mode=clone:stop_duration={pad:.3f}"
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-t", f"{length:.3f}", "-i", src, "-an", "-map_metadata", "-1",
         "-vf", vf, "-t", dur, "-c:v", "libx264", "-crf", "16", "-preset", scratch_profile.preset("intermediate"), "-pix_fmt", "yuv420p", out])
    cuts = scene_changes(out, 0.3)
    print(f"{out} {duration(out):.2f}s  scene changes inside: {' '.join(map(str, cuts)) or 'none'}")
    if cuts: sys.exit("a scene change is inside the reference clip: end it a few frames before the cut")


# ---------------------------------------------------------------- strip / safe
def cmd_strip(a):
    off = float(opt(a, "--offset", "0")); times = opt(a, "--times")
    src, clip, out = a[0], a[1], a[2]
    d = duration(clip)
    ts = [float(t) for t in times.split(",")] if times else [d * (i + 0.5) / 6 for i in range(6)]
    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for row, (f, base) in enumerate(((src, off), (clip, 0.0))):
            for i, t in enumerate(ts):
                p = Path(tmp) / f"{row}_{i}.png"
                run(["ffmpeg", "-v", "error", "-y", "-ss", f"{base + t:.3f}", "-i", f, "-frames:v", "1",
                     "-vf", "scale=240:-2,pad=240:428:(ow-iw)/2:(oh-ih)/2", p])
                tiles.append(p)
        args = []
        for p in tiles: args += ["-i", p]
        n = len(ts)
        fc = "".join(f"[{i}:v]" for i in range(n)) + f"hstack=inputs={n}[top];" + \
             "".join(f"[{n + i}:v]" for i in range(n)) + f"hstack=inputs={n}[bot];[top][bot]vstack=inputs=2[o]"
        run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fc, "-map", "[o]", "-frames:v", "1", "-q:v", "3", out])
    print(f"{out}: top = source at {', '.join(f'{off + t:.2f}' for t in ts)} s; bottom = clip at {', '.join(f'{t:.2f}' for t in ts)} s")


def cmd_safe(a):
    src, out = a[0], a[1]
    vf = ("scale=1080:1920,drawbox=x=0:y=1536:w=1080:h=384:color=red@0.35:t=fill,"
          "drawbox=x=940:y=900:w=140:h=700:color=red@0.35:t=fill,drawbox=x=0:y=0:w=1080:h=150:color=red@0.35:t=fill")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-frames:v", "1", "-vf", vf, out])
    print(f"{out}: red = bottom 20% (caption, name, music), right column (buttons), top 150 px (tabs)")


# ---------------------------------------------------------------- audio
def cmd_audio_probe(a):
    import numpy as np
    drop = flag(a, "--drop"); fr_ = opt(a, "--from"); to = opt(a, "--to")
    path = a[0]; sr = 22050
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    s0 = float(fr_) if fr_ else 0.0
    if fr_: x = x[int(s0 * sr):]
    if to: x = x[:int((float(to) - s0) * sr)]
    n, hop = 2048, 512
    if len(x) < n * 4: sys.exit("too short to measure")
    fr = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    S = np.abs(np.fft.rfft(fr, axis=1)); f = np.fft.rfftfreq(n, 1 / sr)
    flux = np.maximum(np.diff(np.log1p(S), axis=0), 0).sum(1); flux -= flux.mean(); fps = sr / hop
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]; lags = np.arange(len(ac)); bpm = 60 * fps / np.maximum(lags, 1)
    ok = (bpm > 60) & (bpm < 200)
    cands = [round(float(60 * fps / l), 1) for _, l in sorted(zip(ac[ok], lags[ok]), reverse=True)[:5]]
    cent = (S * f).sum(1) / (S.sum(1) + 1e-9); low = S[:, f < 150].sum(1) / (S.sum(1) + 1e-9)
    rms = np.sqrt((fr ** 2).mean(1))
    print(f"duration {len(x) / sr:.2f}s  tempo candidates {cands}")
    print(f"brightness (centroid) {np.median(cent):.0f} Hz  bass share (<150 Hz) {np.median(low):.2f}")
    print("energy by eighth (dB):", " ".join(f"{20 * np.log10(s.mean() + 1e-9):.1f}" for s in np.array_split(rms, 8)))
    if drop:
        win = int(sr * 0.25); m = len(x) // win
        db = 20 * np.log10(np.sqrt((x[:m * win].reshape(m, win) ** 2).mean(1)) + 1e-9)
        best = max(((db[i:i + 12].mean() - db[i - 16:i].mean(), i) for i in range(16, m - 40)), default=None)
        print(f"biggest drop at {s0 + best[1] * 0.25:.2f}s (+{best[0]:.1f} dB)" if best else "too short to search for a drop (needs > 14 s)")
    print("note: speech recognition hearing nothing under a beat is NOT proof of no vocals")


def cmd_loudness(a):
    i, tp = loudness(a[0])
    print(json.dumps({"file": a[0], "integrated_lufs": i, "true_peak_dbtp": tp}))


def cmd_lesson(a):
    v = Video(a[0]); text = " ".join(a[1:]).strip()
    if not text: sys.exit("give the lesson text")
    d = update_meta(v, lambda d: d.setdefault("lessons", []).append({"date": now()[:10], "lesson": text}))
    print(f"{len(d['lessons'])} lessons proposed in {v.metadata}")


def cmd_stage(a):
    v = Video(a[0])
    if len(a) < 2:
        print(read_meta(v).get("stage", "none")); return
    update_meta(v, lambda d: d.update({"stage": a[1]}))
    print(f"stage = {a[1]}")


COMMANDS = {"stage": cmd_stage, "new": cmd_new, "fetch": cmd_fetch, "probe": cmd_probe, "frames": cmd_frames, "still": cmd_still,
            "dna": cmd_dna, "mask": cmd_mask, "cutref": cmd_cutref, "strip": cmd_strip, "safe": cmd_safe,
            "audio-probe": cmd_audio_probe, "loudness": cmd_loudness, "lesson": cmd_lesson}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS: sys.exit(__doc__)
    COMMANDS[sys.argv[1]](sys.argv[2:])
