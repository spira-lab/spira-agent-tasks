#!/usr/bin/env python3
"""Build a re-skit from its build file, as often as you like.

  python3 <reskit>/tools/build_edit.py <materials>/edit.json draft
        A quick cut for review -> <root>/renders/deletable/<name>_draft.mp4. Every segment uses
        its generated clip when gen/out has it, otherwise the source footage of the same moment
        (caption masked) as a stand-in, so the whole edit is built and timed while generation runs.
  python3 <reskit>/tools/build_edit.py <materials>/edit.json final
        The final video -> <root>/renders/<name>.mp4 (an older one moves to renders/deletable/
        with its time as a suffix), with its cover, then the share copy (under 30 MB) ->
        <root>/renders/deletable/<name>_share.mp4, then the checks. A stand-in still in the cut is a problem (ok false).

Both rewrite the editable page (<root>/editable/<name>.html) from the build file, and both print
one JSON line: {"ok", "problems", "out", ...}. The audio is mixed and checked on its own first,
then attached to the picture (a one-pass mix once dropped the vocal). Final loudness is about
-16 LUFS integrated, true peak under -1 dBTP, measured with ffmpeg ebur128, like the shared render.

edit.json (paths relative to the materials folder):
  "source":   "source/source.mp4"
  "mask":     "assets/caption_mask.png" or ""      removelogo mask for the source stand-ins
  "caption":  "assets/caption.png" or ""            full-frame PNG over every footage segment
  "clips":    {"A": {"start": 0.0}, "B": {"start": 11.53, "file": "gen/out/B.mp4"}}
              where each generated clip starts in the source (its reference clip's start);
              file defaults to gen/out/<id>.mp4
  "segments": [{"clip": "A", "from": 0.0, "to": 1.75, "zoom": false},
               {"insert": "assets/broll.mp4", "dur": 2.5}]     an insert is a video or a still
              Times are on the source's clock. A segment of a clip generated longer than its
              reference (a longer delivery) may run past the source's end: "to" up to the clip's
              start + the clip's length. Until that clip lands, the draft holds the source's
              last frame there.
  "end_hold": 0          seconds to hold the last frame (only when the last shot is too short to read)
  "overlays": [{"png": "assets/pop_1.png", "in": "2@4.58", "out": "3@end", "kind": "pop"}]
              times: "<seg>@<source time>", "<seg>@end", "<seg>@+<s from the segment's start>",
              or "t:<timeline seconds>". kind: full (full-frame PNG at 0,0) | pop (sticker centred
              at pop_cy with a three-frame pop-in, 70/95/106/100 %)
  "pop_cy":   1290       keep text above y 1536 and left of x 940 (the safe area)
  "audio":    "source" (the source's own voices, cut with the segments, pitch-adjusted)
              | "clips" (a re-voiced video: each segment's sound is its own generated clip's audio,
                cut at the same points as the picture; a clip still rendering uses the
                pitch-adjusted source audio as a stand-in in the draft)
              | "music" | "none"
  "pitch_semitones": 0.6 source audio is ALWAYS pitch-adjusted (owner's rule): 0.4 to 1.0 up,
              or the same range down; length and lip sync hold (resample + tempo correction)
  "music":    {"file": "music/take_a.mp3", "start": 0, "pitch": false} or null. With audio "music"
              it is the whole soundtrack; with audio "source" or "clips" it is a bed music_under_lu
              under the voices. "pitch": true shifts the bed by pitch_semitones: required when the
              bed is the source's own sound (kept source audio is always pitch-adjusted), e.g.
              {"file": "source/source.mp4", "start": 0, "pitch": true} for a source with no voices.
  "music_under_lu": 20
  "roomtone": [9.30, 2.10]   a truly quiet stretch of the source (start, length) for inserts and holds:
              at least 10 dB below the source and 0.5 s longer than the longest insert or hold, so it
              never loops (checked; the build stops otherwise). When the source has music or voices
              everywhere, set null and carry inserts and the end card on one continuous music bed.
  "zoom":     "crop=982:1745:49:118,scale=1080:1920"   the punch-in used by "zoom": true
  "cover":    3.2        the clearest poster moment on the timeline (final only; never 0)
"""
import json, math, re, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reskit_common import SHARED, Video, update_meta, write_editable, ffprobe_json, duration, loudness, to_deletable, now, scratch_profile

FPS = 30; AF = 0.03; SR = 48000
FIT = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1"
TARGET_LUFS, TP_MAX = -16.0, -1.0
SHARE_MB = 30


class Graph:
    """Filter text with every reused input stream split first (a stream feeds one pad only)."""
    def __init__(self):
        self.parts, self.uses = [], {}

    def use(self, stream):                    # stream like "0:v" or "0:a"
        n = self.uses.get(stream, 0) + 1; self.uses[stream] = n
        return f"[{stream.replace(':', '_')}_{n}]"

    def add(self, s): self.parts.append(s)

    def text(self):
        pre = []
        for st, n in self.uses.items():
            kind = "asplit" if st.endswith(":a") else "split"
            labels = "".join(f"[{st.replace(':', '_')}_{i}]" for i in range(1, n + 1))
            pre.append(f"[{st}]{kind}={n}{labels}" if n > 1 else f"[{st}]{'anull' if kind == 'asplit' else 'null'}{labels}")
        return ";".join(pre + self.parts)


def f3(x): return f"{x:.3f}"


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[1] not in ("draft", "final"): sys.exit(__doc__)
    v = Video(a[0]); mode = a[1]
    E = json.loads(Path(a[0]).read_text())
    M = v.materials
    P = lambda rel: (Path(rel) if Path(rel).is_absolute() else M / rel) if rel else None
    problems, notes = [], []

    src = P(E.get("source") or "source/source.mp4")
    if not src.exists(): sys.exit(f"no source at {src}")
    has_src_audio = any(s.get("codec_type") == "audio" for s in ffprobe_json(src).get("streams", []))
    src_dur = duration(src)
    mask = P(E.get("mask")); caption = P(E.get("caption"))
    for f in (mask, caption):
        if f and not f.exists(): sys.exit(f"missing {f}")
    segs = E.get("segments") or []
    if not segs: sys.exit("the build has no segments yet")
    audio = E.get("audio", "source")
    if audio not in ("source", "clips", "music", "none"): sys.exit(f'audio must be "source", "clips", "music" or "none", not {audio!r}')
    semis = float(E.get("pitch_semitones") or 0)
    music = E.get("music") or None
    bed_from_source = bool(music) and P(music["file"]).resolve() == src.resolve()
    if audio == "source" and not has_src_audio: sys.exit('audio is "source" but the source has no audio')
    if bed_from_source and not music.get("pitch"):
        sys.exit("the music bed is the source's own sound: set \"pitch\": true on it (kept source audio is always pitch-adjusted)")
    if audio in ("source", "clips") or (music and music.get("pitch")):
        if not 0.4 <= abs(semis) <= 1.0:
            sys.exit("kept source audio is always pitch-adjusted (the owner's rule): pitch_semitones must be 0.4 to 1.0 "
                     "(or -0.4 to -1.0); +0.6 is the approved value")
    if audio == "music" and not music: sys.exit('audio is "music" but no music is set')
    if music and not P(music["file"]).exists(): sys.exit(f"missing music {P(music['file'])}")
    rt = E.get("roomtone")

    # ---------------------------------------------------------------- inputs
    inputs = [["-i", src]]; idx = {}
    clips = E.get("clips") or {}
    used, standin = [], []
    for cid, c in clips.items():
        f = P(c.get("file") or f"gen/out/{cid}.mp4")
        if f.exists():
            idx[cid] = len(inputs); inputs.append(["-i", f]); used.append(cid)
    ins = {}
    for s in segs:
        if "insert" in s and s["insert"] not in ins:
            f = P(s["insert"])
            if not f.exists(): sys.exit(f"missing insert {f}")
            ins[s["insert"]] = len(inputs)
            inputs.append(["-loop", "1", "-framerate", str(FPS), "-i", f] if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") else ["-i", f])
    cap_i = None
    if caption: cap_i = len(inputs); inputs.append(["-i", caption])
    ov0 = len(inputs)
    for o in E.get("overlays") or []:
        f = P(o["png"])
        if not f.exists(): sys.exit(f"missing overlay {f}")
        inputs.append(["-i", f])

    # ---------------------------------------------------------------- picture
    g = Graph(); seg_t, seg_s, seg_end = [], [], []
    t = 0.0; nseg = len(segs); vlabels = []
    for n, s in enumerate(segs, 1):
        seg_t.append(t)
        if "insert" in s:
            d = float(s["dur"]); k = ins[s["insert"]]
            g.add(f"{g.use(f'{k}:v')}tpad=stop_mode=clone:stop_duration={f3(d)},trim=duration={f3(d)},setpts=PTS-STARTPTS,"
                  f"fps={FPS},{FIT},format=yuv420p[v{n}]")
            seg_s.append(0.0); t += d
        else:
            cid = s["clip"]; st, en = float(s["from"]), float(s["to"]); d = en - st
            if d <= 0: sys.exit(f"segment {n}: 'to' must be after 'from'")
            hold = float(E.get("end_hold") or 0) if n == nseg else 0.0
            if cid in idx:
                vs = st - float(clips[cid].get("start", 0))
                cd = duration(P(clips[cid].get("file") or f"gen/out/{cid}.mp4"))
                if vs < -0.01 or vs + d > cd + 0.05:
                    problems.append(f"segment {n}: clip {cid} covers {f3(float(clips[cid].get('start', 0)))}+{cd:.2f}s, "
                                    f"not source {st}-{en}")
                chain = f"{g.use(f'{idx[cid]}:v')}trim={f3(max(0, vs))}:{f3(max(0, vs) + d)},setpts=PTS-STARTPTS,fps={FPS},{FIT}"
            else:
                standin.append(cid)
                chain = f"{g.use('0:v')}trim={f3(st)}:{f3(en)},setpts=PTS-STARTPTS" + (f",removelogo=filename='{mask}'" if mask else "") + f",fps={FPS},{FIT}"
                if en > src_dur:   # a segment that runs past the source's end on a longer clip: hold the last frame until it lands
                    chain += f",tpad=stop_mode=clone:stop_duration={f3(en - max(st, src_dur) + 0.1)},trim=duration={f3(d)}"
            if s.get("zoom"): chain += "," + (E.get("zoom") or "crop=982:1745:49:118,scale=1080:1920")
            if hold > 0: chain += f",tpad=stop_mode=clone:stop_duration={f3(hold)}"
            if cap_i is not None:
                g.add(f"{chain}[b{n}]"); g.add(f"[b{n}]{g.use(f'{cap_i}:v')}overlay=0:0,format=yuv420p,setsar=1[v{n}]")
            else:
                g.add(f"{chain},format=yuv420p,setsar=1[v{n}]")
            seg_s.append(st); t += d + hold
        seg_end.append(t); vlabels.append(f"[v{n}]")
    total = t
    g.add("".join(vlabels) + f"concat=n={nseg}:v=1:a=0[vc]")
    end_hold = float(E.get("end_hold") or 0)
    fill_windows = [(seg_t[k], seg_end[k], "insert") for k, s in enumerate(segs) if "insert" in s]
    if end_hold > 0 and "insert" not in segs[-1]: fill_windows.append((seg_end[-1] - end_hold, seg_end[-1], "end hold"))
    if audio == "source": check_roomtone(src, rt, [w[1] - w[0] for w in fill_windows])

    def at(spec):
        spec = str(spec)
        if spec.startswith("t:"): return float(spec[2:])
        m = re.match(r"^(\d+)@(end|\+?-?[0-9.]+)$", spec)
        if not m: sys.exit(f"bad overlay time {spec!r}: use <seg>@<source time>, <seg>@end, <seg>@+<s> or t:<s>")
        k = int(m.group(1)) - 1
        if not 0 <= k < nseg: sys.exit(f"overlay time {spec}: there is no segment {k + 1}")
        x = m.group(2)
        if x == "end": return seg_end[k]
        if x.startswith("+"): return seg_t[k] + float(x[1:])
        if "insert" in segs[k]: sys.exit(f"overlay time {spec}: segment {k + 1} is an insert, use {k + 1}@+<s>")
        return seg_t[k] + float(x) - seg_s[k]

    last = "vc"; f1 = 1.0 / FPS; times = []
    pop_cy = int(E.get("pop_cy") or 1290)
    for p, o in enumerate(E.get("overlays") or []):
        i = ov0 + p; tin, tout = at(o["in"]), at(o["out"])
        times.append(f"{Path(o['png']).name} {tin:.2f}-{tout:.2f}s")
        if o.get("kind", "full") == "full":
            g.add(f"[{last}][{i}:v]overlay=0:0:enable='between(t,{f3(tin)},{f3(tout)})'[o{p}]"); last = f"o{p}"
        else:
            pos = f"x=(W-w)/2:y={pop_cy}-h/2"
            g.add(f"[{i}:v]format=rgba,split=4[p{p}a][p{p}b][p{p}c][p{p}d]")
            g.add(f"[p{p}a]scale=iw*0.70:-1[q{p}a];[p{p}b]scale=iw*0.95:-1[q{p}b];[p{p}c]scale=iw*1.06:-1[q{p}c];[p{p}d]null[q{p}d]")
            steps = [(tin, tin + f1, "a"), (tin + f1, tin + 2 * f1, "b"), (tin + 2 * f1, tin + 3 * f1, "c"), (tin + 3 * f1, tout, "d")]
            for s0, s1, k in steps:
                g.add(f"[{last}][q{p}{k}]overlay={pos}:enable='between(t,{f3(s0)},{f3(s1)})'[o{p}{k}]"); last = f"o{p}{k}"
    g.add(f"[{last}]null[v]")

    # ---------------------------------------------------------------- sound (mixed on its own)
    tmp = Path(tempfile.mkdtemp(prefix="reskit-build-"))
    try:
        mix = tmp / "mix.wav"; voiced = build_audio(E, P, src, segs, seg_end, total, audio, semis, music, rt, tmp, mix, notes, problems)
        i_lufs, tp = loudness(mix)
        if i_lufs is None or i_lufs == float("-inf"): problems.append("the mixed audio is silent")
        elif abs(i_lufs - TARGET_LUFS) > 1.0: problems.append(f"mix loudness {i_lufs} LUFS, not about {TARGET_LUFS}")
        if tp is not None and tp > TP_MAX + 0.3: problems.append(f"mix true peak {tp} dBTP")
        problems += check_fills(mix, fill_windows, (float(rt[1]) - 0.3) if rt and audio == "source" else None)

        # ------------------------------------------------------------ picture render + attach
        pic = tmp / "picture.mp4"
        flat = [x for inp in inputs for x in inp]
        crf, preset = ("23", "veryfast") if mode == "draft" else ("18", scratch_profile.preset("final"))
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, flat), "-filter_complex", g.text(), "-map", "[v]",
                            "-t", f3(total), "-an", "-c:v", "libx264", "-preset", preset, "-crf", crf, "-r", str(FPS),
                            "-pix_fmt", "yuv420p", str(pic)], capture_output=True, text=True)
        if r.returncode != 0: sys.exit("picture render failed: " + r.stderr.strip()[-1500:])
        joined = tmp / "joined.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
             "-b:a", "192k", "-ar", str(SR), "-ac", "2", "-t", f3(total), "-movflags", "+faststart", joined])

        if mode == "draft":
            out = v.render_deletable / f"{v.name}_draft.mp4"; out.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(joined), str(out))
            result = {"ok": not problems, "mode": "draft", "out": str(out), "seconds": round(duration(out), 2),
                      "lufs": i_lufs, "true_peak": tp, "generated_clips": used, "stand_ins": sorted(set(standin)),
                      "voice_from_clips": voiced, "overlays": times, "problems": problems, "notes": notes}
        else:
            if standin: problems.append(f"source stand-ins still in the cut for clip(s) {', '.join(sorted(set(standin)))}")
            cover = E.get("cover")
            if not cover or not 0 < float(cover) < total: sys.exit("final needs \"cover\": the clearest poster moment, after 0 and before the end")
            out = v.render; out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists():
                stamp = datetime.fromtimestamp(out.stat().st_mtime).strftime("%Y%m%d-%H%M")
                old = v.render_deletable / f"{v.name}_{stamp}.mp4"; v.render_deletable.mkdir(parents=True, exist_ok=True)
                shutil.move(str(out), str(old))
                update_meta(v, lambda d: [r_.update({"status": "deletable", "file": str(old)}) for r_ in d.get("renders", [])
                                          if r_.get("file") == str(out)])
            cov = tmp / "cover.png"
            run(["ffmpeg", "-v", "error", "-y", "-ss", f3(float(cover)), "-i", joined, "-frames:v", "1", cov])
            run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-i", cov, "-map", "0", "-map", "1", "-c", "copy", "-c:v:1", "png",
                 "-disposition:v:1", "attached_pic", "-movflags", "+faststart", out])
            share = v.render_deletable / f"{v.name}_share.mp4"
            if share.exists(): share.unlink()            # the share copy is rebuilt from the current render
            for c, scale in (("23", None), ("26", None), ("26", "scale=720:-2")):
                run(["ffmpeg", "-v", "error", "-y", "-i", joined, *(["-vf", scale] if scale else []), "-c:v", "libx264",
                     "-crf", c, "-preset", scratch_profile.preset("intermediate"), "-c:a", "copy", "-movflags", "+faststart", share])
                if share.stat().st_size < SHARE_MB * 1e6: break
            problems += check_final(out, total, share)
            fi, ftp = loudness(out)
            result = {"ok": not problems, "mode": "final", "out": str(out), "share": str(share),
                      "share_mb": round(share.stat().st_size / 1e6, 1), "seconds": round(duration(out), 2),
                      "lufs": fi, "true_peak": ftp, "cover_at": float(cover), "generated_clips": used,
                      "voice_from_clips": voiced, "overlays": times, "problems": problems, "notes": notes}
            update_meta(v, lambda d: d.setdefault("renders", []).append({
                "file": str(out), "rendered": now(), "status": "current", "fps": FPS, "duration_ms": int(round(duration(out) * 1000)),
                "lufs": fi, "true_peak": ftp, "share": str(share), "ok": not problems, "problems": problems}) or d.update({"stage": "rendered"}))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    write_editable(v, E, note=f"Last build: {mode}, {now()}, {'ok' if result['ok'] else 'problems: ' + '; '.join(problems)}")
    print(json.dumps(result))


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode != 0: sys.exit(f"ffmpeg failed: {r.stderr.strip()[-1200:]}")
    return r


def mean_db(src, start=None, length=None):
    """mean_volume (dB) of the source audio, or of one stretch of it."""
    cut = ["-ss", f3(start), "-t", f3(length)] if start is not None else []
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *cut, "-i", str(src), "-vn", "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"mean_volume:\s*(-?[0-9.]+|-inf) dB", r.stderr)
    return float(m.group(1)) if m and m.group(1) != "-inf" else float("-inf")


def check_roomtone(src, rt, fills):
    """A room-tone slice may only be truly quiet and long enough never to repeat (the owner's rule, 2026-10-29:
    a looped slice with the source's music or voices in it sounds like a skipping CD on the end card)."""
    if not rt or not fills: return
    rs, rl = float(rt[0]), float(rt[1])
    need = max(fills) + 0.5
    if rl < need:
        sys.exit(f"roomtone {rl:.2f} s would loop under a {max(fills):.2f} s insert or hold (needs at least {need:.2f} s): "
                 "pick a longer truly quiet stretch, or set roomtone to null and carry inserts and the end card on one "
                 "continuous music bed (music + music_under_lu)")
    slice_db, src_db = mean_db(src, rs, rl), mean_db(src)
    if slice_db != float("-inf") and slice_db > src_db - 10:
        sys.exit(f"roomtone {rs:.2f}+{rl:.2f} s is not quiet ({slice_db:.1f} dB vs the source's {src_db:.1f} dB; it must be "
                 "at least 10 dB below): it holds music or voices. Set roomtone to null and carry inserts and the end card "
                 "on one continuous music bed (music + music_under_lu)")


def check_fills(mix, windows, period=None):
    """Problems in the audio under inserts and holds: a dropout at a cut, and, when room tone fills them, a loop
    (the slice repeating every `period` s). A music bed is never loop-checked: its own beat would read as a loop."""
    sr = 8000
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mix), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout: return []
    import numpy as np
    x = np.frombuffer(r.stdout, dtype=np.float32); problems = []
    fr = int(0.02 * sr)
    def rms_db(a):
        n = len(a) // fr
        if n == 0: return np.array([])
        e = np.sqrt(np.mean(a[:n * fr].reshape(n, fr) ** 2, axis=1)) + 1e-9
        return 20 * np.log10(e)
    for t0, t1, what in windows:
        a = x[int(t0 * sr):int(t1 * sr)]
        if period and len(a) > int(2.2 * period * sr) and np.sqrt(np.mean(a ** 2)) > 1e-4:   # loop check at the slice period
            hop = int(0.01 * sr); n = len(a) // hop
            env = 20 * np.log10(np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
            env = env - env.mean(); best, lag_best = 0.0, 0
            p0 = int(round(period * 100))
            for lag in range(max(5, p0 - 3), min(p0 + 4, n // 2)):
                u, w = env[:-lag], env[lag:]
                den = np.sqrt(np.sum(u * u) * np.sum(w * w))
                c = float(np.sum(u * w) / den) if den > 0 else 0.0
                if c > best: best, lag_best = c, lag
            if best > 0.3:
                problems.append(f"audio loop under the {what} at {t0:.2f}-{t1:.2f}s (repeats every {lag_best / 100:.2f}s, "
                                f"correlation {best:.2f}): use one continuous music bed there, not looped room tone")
        for b in (t0, t1):                                                    # dropout check at the cut
            if b <= 0.2 or b >= len(x) / sr - 0.6: continue           # the video's own start and final fade
            around = rms_db(x[int((b - 0.4) * sr):int((b + 0.4) * sr)])
            if len(around) < 10: continue
            ref = float(np.median(around)); low = around < ref - 6
            run_, worst = 0, 0
            for v_ in low:
                run_ = run_ + 1 if v_ else 0; worst = max(worst, run_)
            if worst * 0.02 >= 0.08 and ref > -45:
                problems.append(f"audio dropout at the {what} cut {b:.2f}s ({worst * 20} ms more than 6 dB down)")
    return problems


def roomtone(g, label, d, rt, notes):
    """d seconds of the source's own room tone, from a quiet stretch looped with crossfades."""
    if not rt:
        notes.append("no roomtone set: inserts and holds are silent")
        g.add(f"anullsrc=r={SR}:cl=stereo,atrim=0:{f3(d)},asetpts=PTS-STARTPTS[{label}]"); return
    rs, rl = float(rt[0]), float(rt[1])
    if rl < 0.8: sys.exit("roomtone length must be at least 0.8 s")
    n = max(1, math.ceil((d + 0.2 - 0.3) / (rl - 0.3)))
    parts = []
    for i in range(n):
        g.add(f"{g.use('0:a')}atrim={f3(rs)}:{f3(rs + rl)},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo[{label}c{i}]")
        parts.append(f"[{label}c{i}]")
    cur = parts[0]
    for i in range(1, n):
        g.add(f"{cur}{parts[i]}acrossfade=d=0.3[{label}x{i}]"); cur = f"[{label}x{i}]"
    fo = max(0.0, d - 0.2)
    g.add(f"{cur}atrim=0:{f3(d)},asetpts=PTS-STARTPTS,afade=t=in:d=0.1,afade=t=out:st={f3(fo)}:d=0.2[{label}]")


def loudnorm_to(src, dst, target=TARGET_LUFS):
    """Two-pass loudnorm (linear) to the target, true peak -1.5 dBTP."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                        f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m: run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11", "-ar", str(SR), dst]); return
    j = json.loads(m[-1])
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
         f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
         f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true", "-ar", str(SR), dst])


def has_audio(f):
    return any(s.get("codec_type") == "audio" for s in ffprobe_json(f).get("streams", []))


def pitch_chain(semis):
    """Pitch shift that keeps length and lip sync (resample + tempo correction)."""
    if not semis: return ""
    r = 2 ** (semis / 12.0)
    return f",asetrate={SR * r:.2f},aresample={SR},atempo={1 / r:.6f}"


def silence(g, label, d):
    g.add(f"anullsrc=r={SR}:cl=stereo,atrim=0:{f3(d)},asetpts=PTS-STARTPTS[{label}]")


def build_audio(E, P, src, segs, seg_end, total, audio, semis, music, rt, tmp, out, notes, problems):
    """Mix the soundtrack on its own. Returns the clips whose own (generated) voice is in the mix."""
    main = tmp / "main.wav"; voiced = []
    if audio == "clips":
        clips = E.get("clips") or {}
        files = [src]; cidx = {}
        for cid, c in clips.items():
            f = P(c.get("file") or f"gen/out/{cid}.mp4")
            if not f.exists(): continue
            if has_audio(f): cidx[cid] = len(files); files.append(f)
            else: problems.append(f"clip {cid} has no sound: a re-voiced clip is generated with \"sound\": true")
        src_audio = has_audio(src); standin = set()
        g = Graph(); labels = []; nseg = len(segs)
        for n, s in enumerate(segs, 1):
            if "insert" in s:
                silence(g, f"a{n}", float(s["dur"])); labels.append(f"[a{n}]"); continue
            cid = s["clip"]; st, en = float(s["from"]), float(s["to"]); d = en - st
            hold = float(E.get("end_hold") or 0) if n == nseg else 0.0
            fade = f"afade=t=in:d={AF},afade=t=out:st={f3(max(0, d - AF))}:d={AF}"
            if cid in cidx:
                vs = max(0.0, st - float(clips[cid].get("start", 0)))
                g.add(f"{g.use(f'{cidx[cid]}:a')}atrim={f3(vs)}:{f3(vs + d)},asetpts=PTS-STARTPTS,aresample={SR},"
                      f"aformat=channel_layouts=stereo,{fade}[sa{n}]")
                if cid not in voiced: voiced.append(cid)
            elif src_audio:
                standin.add(cid)
                g.add(f"{g.use('0:a')}atrim={f3(st)}:{f3(en)},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo"
                      f"{pitch_chain(semis)},apad=whole_dur={f3(d)},atrim=0:{f3(d)},{fade}[sa{n}]")
            else:
                silence(g, f"sa{n}", d)
            if hold > 0:
                silence(g, f"ha{n}", hold); g.add(f"[sa{n}][ha{n}]concat=n=2:v=0:a=1[a{n}]")
            else:
                g.add(f"[sa{n}]anull[a{n}]")
            labels.append(f"[a{n}]")
        g.add("".join(labels) + f"concat=n={nseg}:v=0:a=1,atrim=0:{f3(total)}[a]")
        flat = [x for f in files for x in ("-i", f)]
        run(["ffmpeg", "-v", "error", "-y", *flat, "-filter_complex", g.text(), "-map", "[a]", "-ar", str(SR), "-ac", "2", tmp / "raw.wav"])
        notes.append(f"voices from the generated clips ({', '.join(voiced) or 'none yet'})")
        if standin: notes.append(f"source audio (pitch-adjusted) stands in for clip(s) {', '.join(sorted(standin))} until they land")
        loudnorm_to(tmp / "raw.wav", main)
    elif audio == "source":
        g = Graph(); labels = []
        nseg = len(segs)
        for n, s in enumerate(segs, 1):
            if "insert" in s:
                roomtone(g, f"a{n}", float(s["dur"]), rt, notes); labels.append(f"[a{n}]"); continue
            st, en = float(s["from"]), float(s["to"]); d = en - st
            hold = float(E.get("end_hold") or 0) if n == nseg else 0.0
            ach = (f"{g.use('0:a')}atrim={f3(st)}:{f3(en)},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,"
                   f"afade=t=in:d={AF},afade=t=out:st={f3(max(0, d - AF))}:d={AF}")
            if hold > 0:
                g.add(f"{ach}[sa{n}]"); roomtone(g, f"ha{n}", hold, rt, notes); g.add(f"[sa{n}][ha{n}]concat=n=2:v=0:a=1[a{n}]")
            else:
                g.add(f"{ach}[a{n}]")
            labels.append(f"[a{n}]")
        r = 2 ** (semis / 12.0)
        g.add("".join(labels) + f"concat=n={nseg}:v=0:a=1[ac]")
        g.add(f"[ac]asetrate={SR * r:.2f},aresample={SR},atempo={1 / r:.6f},atrim=0:{f3(total)}[a]")
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", g.text(), "-map", "[a]", "-ar", str(SR), "-ac", "2", tmp / "raw.wav"])
        notes.append(f"source audio pitch-adjusted {semis:+.2f} semitones (tempo-corrected)")
        loudnorm_to(tmp / "raw.wav", main)
    elif audio == "music":
        bed_of(P, music, total, tmp, tmp / "raw.wav", fade_out=0.9)
        loudnorm_to(tmp / "raw.wav", main)
    else:
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=stereo", "-t", f3(total), main])
        notes.append("no audio (audio: none)")
    if audio in ("source", "clips") and music:
        bed = tmp / "bed.wav"; bed_of(P, music, total, tmp, bed, fade_out=1.5, semis=semis if music.get("pitch") else 0)
        bi, _ = loudness(bed); under = float(E.get("music_under_lu") or 20)
        gain = 0 if bi is None or bi == float("-inf") else (TARGET_LUFS - under) - bi
        run(["ffmpeg", "-v", "error", "-y", "-i", main, "-i", bed, "-filter_complex",
             f"[1:a]volume={gain:.2f}dB[b];[0:a][b]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84:level=0[a]",
             "-map", "[a]", "-ar", str(SR), "-ac", "2", out])
        notes.append(f"music bed {under} LU under the {'voices' if audio == 'clips' else 'source'}")
    else:
        shutil.move(str(main), str(out))
    i_lufs, _ = loudness(out)                       # a last small nudge if the mix drifted
    if i_lufs is not None and i_lufs != float("-inf") and 0.3 < abs(TARGET_LUFS - i_lufs) <= 3:
        fixed = tmp / "nudged.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", out, "-af", f"volume={TARGET_LUFS - i_lufs:.2f}dB,alimiter=limit=0.84:level=0", fixed])
        shutil.move(str(fixed), str(out))
    return voiced


def bed_of(P, music, total, tmp, out, fade_out, semis=0):
    f = P(music["file"]); ms = float(music.get("start") or 0)
    if duration(f) - ms < total:
        ext = tmp / "extended.wav"
        run(["python3", SHARED / "tools" / "bgm-extend.py", f, ext, f3(ms + total + 1)]); f = ext
    run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vn", "-af",
         f"atrim={f3(ms)}:{f3(ms + total)},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo"
         f"{pitch_chain(semis)},atrim=0:{f3(total)},"
         f"afade=t=in:d=0.3,afade=t=out:st={f3(max(0, total - fade_out))}:d={f3(fade_out)}", out])


def check_final(out, total, share):
    p = ffprobe_json(out); problems = []
    vids = [s for s in p.get("streams", []) if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic")]
    auds = [s for s in p.get("streams", []) if s.get("codec_type") == "audio"]
    cov = [s for s in p.get("streams", []) if (s.get("disposition") or {}).get("attached_pic")]
    if not vids: problems.append("no video stream")
    elif (vids[0].get("width"), vids[0].get("height")) != (1080, 1920): problems.append(f"size {vids[0].get('width')}x{vids[0].get('height')}")
    if not auds: problems.append("no audio stream")
    elif auds[0].get("channels") != 2: problems.append(f"audio has {auds[0].get('channels')} channels")
    if not cov: problems.append("no cover")
    d = duration(out)
    if abs(d - total) > 0.15: problems.append(f"length {d:.2f}s, expected {total:.2f}s")
    i_lufs, tp = loudness(out)
    if i_lufs is None or abs(i_lufs - TARGET_LUFS) > 1.0: problems.append(f"loudness {i_lufs} LUFS, not about {TARGET_LUFS}")
    if tp is not None and tp > TP_MAX + 0.3: problems.append(f"true peak {tp} dBTP")
    if share.stat().st_size >= SHARE_MB * 1e6: problems.append(f"share copy is {share.stat().st_size / 1e6:.1f} MB")
    return problems


if __name__ == "__main__":
    main()
