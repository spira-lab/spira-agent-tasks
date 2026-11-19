#!/usr/bin/env python3
"""Repurpose builder (Super Nova, shared designer skill): up to twenty organic
repurposes of one finished video. --count sets how many (default 20).

  python3 repurpose.py --source <root>/renders/<name>.mp4 [--count N]
        [--editable <root>/editable/<name>.html] [--timings <path>] [--cm <designers' shared folder>]
        [--out <folder>] [--preview-only] [--preview-at S] [--quip "..." ...] [--only 4,11]
        [--caption-band Y0,Y1] [--no-mirror] [--jobs 3] [--keep-temp]

Every variant stays a native, full-bleed post. What changes is what a duplicate
matcher compares: the video layers are mirrored in place (layout, text and
motion untouched), the persona zoomed, the frame punched in, tilted,
bordered or inset, the timing cut, the audio sped and pitched. Grade and
texture ride on top. Measured per source: the caption rows, the source's cuts,
and the top of the moving subject in each scene. The duplicate gate keeps the
twenty that sit far from the original and from each other.

--preview-only renders a 2-second clip of each kept variant, a contact sheet
and a grid video, for review before the full render.
"""
import argparse, base64, concurrent.futures as cf, datetime, json, math, os, re, secrets, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import diff_gate as G  # noqa: E402

W, H = 1080, 1920
TW, TH = 108, 192
NEED = 20
ORIG_MIN, PAIR_MIN = 16, 12   # the usual near-duplicate line is 10 bits; both sit above it
SEL_MARGIN = 2   # a still estimates a rendered file to within about 2 bits: a replacement keeps that much in hand
PREVIEW_S = 2.0
SEL_FPS = 5          # frame rate of the base renders measured during selection
TOP_SHARE = 0.25   # of what a zoom or tilt removes vertically, the share taken off the top
GRADES = {
 "modern": "curves=r='0/0.02 0.25/0.225 0.75/0.795 1/1':g='0/0.018 0.5/0.5 1/1':b='0/0.05 0.5/0.487 1/0.98',eq=contrast=1.07:saturation=1.05",
 "warm":   "curves=r='0/0.055 0.5/0.52 1/0.97':g='0/0.050 0.5/0.50 1/0.95':b='0/0.070 0.5/0.48 1/0.90',eq=contrast=0.94:saturation=0.88:gamma=1.02",
 "mono":   "hue=s=0,curves=all='0/0 0.25/0.155 0.75/0.865 1/1',eq=contrast=1.10",
 "cool":   "colorbalance=rs=-0.06:bs=0.08:rm=-0.04:bm=0.05,eq=saturation=0.92:contrast=1.04",
 "faded":  "curves=all='0/0.08 0.5/0.52 1/0.93',eq=saturation=0.82",
}
SHX, SHY = "+7*sin(2*PI*t*1.3)+4*sin(2*PI*t*2.7+1)", "+6*sin(2*PI*t*1.1+2)+3*sin(2*PI*t*3.1)"

# Injected into a copy of the editable for mirrored bases: every <video> and <canvas> on the
# stage is flipped about its own centre and nothing else is. The layout, the text, the cards and
# every animation keep their direction: a layer that slides left still slides left, only the
# picture inside it is mirrored. The individual `scale` property composes with any transform the
# element or its parents animate, and a persona zoom already set on the video is kept.
FLIP_JS = r"""<script id="rep-flip">(function(){
var st=document.getElementById('stage'); if(!st) return;
st.querySelectorAll('video,canvas').forEach(function(el){var cs=getComputedStyle(el).scale;
  if(cs&&cs!=='none'){var p=cs.split(' '),x=parseFloat(p[0]),y=p.length>1?parseFloat(p[1]):x;el.style.scale=(-x)+' '+y;}
  else el.style.scale='-1 1';});
})();</script>
"""


CAPFONT_JS = r"""<script id="rep-capfont">(function(){
var st=document.getElementById('stage'); if(!st) return;
var sr=st.getBoundingClientRect(), B0=%d, B1=%d, K=%.3f;
document.fonts.load("700 100px RepCap");
function hasText(el){var w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null),n;
  while((n=w.nextNode())){if(n.nodeValue.replace(/\s+/g,'').length) return true;} return false;}
function hasMedia(el){return el.matches('video,canvas,iframe')||!!el.querySelector('video,canvas,iframe');}
var blocks=[], targets=[];
(function walk(el){for(var i=0;i<el.children.length;i++){var c=el.children[i],t=c.tagName;
  if(t==='AUDIO'||t==='SCRIPT'||t==='STYLE'||c.classList.contains('guide')) continue;
  if(hasMedia(c)){walk(c);continue;} if(hasText(c)){blocks.push(c);continue;} walk(c);}})(st);
function consider(el){var r=el.getBoundingClientRect(),t=(r.top-sr.top)/sr.height*1920,b=(r.bottom-sr.top)/sr.height*1920;
  if(b-t>2&&b-t<=700&&Math.min(b,B1)-Math.max(t,B0)>0){targets.push(el);return;}
  for(var i=0;i<el.children.length;i++){if(hasText(el.children[i])) consider(el.children[i]);}}
blocks.forEach(consider);
function tree(el){return [el].concat([].slice.call(el.querySelectorAll('*')));}
// the widest caption line, by layout: transforms and opacity are ignored, so the answer is the
// same on every frame and in every render worker
function widest(el){var lines={},w=0;
  tree(el).forEach(function(e){
    var own=[].some.call(e.childNodes,function(n){return n.nodeType===3&&n.nodeValue.trim();});
    if(!own||!e.offsetWidth) return;
    var key=[].indexOf.call(document.all,e.offsetParent)+':'+e.offsetTop;
    var l=lines[key]||(lines[key]=[1e9,-1e9]); l[0]=Math.min(l[0],e.offsetLeft); l[1]=Math.max(l[1],e.offsetLeft+e.offsetWidth);});
  for(var k in lines) w=Math.max(w,lines[k][1]-lines[k][0]); return w;}
// once every face has loaded: note how wide the original captions are, switch the face, and
// shrink any block that came out wider. The source's captions were made to fit, whatever its
// animation does to them, so a new face never runs wider than the original did.
function run(){var before=targets.map(widest);
  targets.forEach(function(el){var all=tree(el),fs=all.map(function(e){return parseFloat(getComputedStyle(e).fontSize);});
    all.forEach(function(e,i){e.style.fontFamily="'RepCap',sans-serif";e.style.fontSize=(fs[i]*K)+'px';
      e.style.fontVariationSettings='normal';e.style.letterSpacing='-0.01em';});});
  targets.forEach(function(el,i){var now=widest(el);
    if(before[i]>0&&now>before[i]) tree(el).forEach(function(e){e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)*before[i]/now)+'px';});});}
window.addEventListener('load',function(){st.offsetHeight;document.fonts.ready.then(run);});
})();</script>
"""
CAPFONTS = {"sans": ("DejaVuSans-Bold.ttf", 0.86), "serif": ("DejaVuSerif-Bold.ttf", 0.88), "mono": ("DejaVuSansMono-Bold.ttf", 0.80)}


def say(*a): print(*a, flush=True)
def even(v): v = int(round(v)); return v - (v % 2)


def probe(path):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_packets", "-show_entries",
        "stream=codec_type,width,height,nb_read_packets,sample_rate:format=duration", "-of", "json", path]))
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    return int(v["width"]), int(v["height"]), int(v["nb_read_packets"]), float(j["format"]["duration"]), int(a["sample_rate"]) if a else 48000


def grab(ctx, t):
    t = min(max(t, 0.0), ctx.dur - 0.05)
    return subprocess.check_output(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", ctx.source, "-frames:v", "1",
        "-vf", "scale=%d:%d,format=gray" % (TW, TH), "-f", "rawvideo", "-"])[:TW * TH]


# ------------------------------------------------------------------ analysis
def detect_band(ctx):
    """Rows of the baked captions: change across a word start minus change over an equal
    span inside the word. Captions change at word starts; motion changes all the time."""
    ws = ctx.words; cand = []
    for i in range(1, len(ws) - 1):
        s = ws[i]["s"]
        if ws[i + 1]["s"] - s >= 0.56 and s - ws[i - 1]["s"] >= 0.18 and s > 0.12 and s + 0.52 < ctx.dur: cand.append(s)
    if len(cand) < 5: return None
    cand = cand[::max(1, len(cand) // 28)][:28]; acc = [0.0] * TH; x0, x1 = TW // 6, TW - TW // 6
    for s in cand:
        a, b, c, d = (grab(ctx, t) for t in (s - 0.12, s + 0.18, s + 0.22, s + 0.52)); prof = []
        for y in range(TH):
            o = y * TW
            prof.append(max(0.0, sum(abs(a[o + x] - b[o + x]) for x in range(x0, x1)) - sum(abs(c[o + x] - d[o + x]) for x in range(x0, x1))))
        m = sum(prof) / TH + 1.0
        for y in range(TH): acc[y] += prof[y] / m
    peak = max(acc)
    if peak / (sum(acc) / TH + 1e-6) < 3.0: return None
    py = acc.index(peak); y0 = y1 = py
    while y0 > 0 and acc[y0 - 1] >= 0.30 * peak: y0 -= 1
    while y1 < TH - 1 and acc[y1 + 1] >= 0.30 * peak: y1 += 1
    k = ctx.H0 / TH
    return (max(0, int(y0 * k) - 50), min(ctx.H0, int((y1 + 1) * k) + 50))


def detect_scenes(ctx):
    """The source's own cuts, from ffmpeg's scene scores with a threshold set by this video."""
    p = subprocess.run(["ffmpeg", "-v", "info", "-i", ctx.source, "-vf",
        "scale=%d:%d,select='gte(scene,0)',metadata=print:key=lavfi.scene_score" % (TW, TH), "-an", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    txt = p.stderr.decode()
    ts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", txt)]
    sc = [float(x) for x in re.findall(r"lavfi\.scene_score=([0-9.]+)", txt)]
    n = min(len(ts), len(sc))
    if n < 10: return [(0.0, ctx.dur)]
    ts, sc = ts[:n], sc[:n]; m = sum(sc) / n; sd = (sum((s - m) ** 2 for s in sc) / n) ** 0.5
    th = max(0.03, m + 5 * sd)
    cuts = [t for t, s in zip(ts, sc) if s > th and 0.5 < t < ctx.dur - 0.5]
    bounds = [0.0] + cuts + [ctx.dur]; out = []
    for a, b in zip(bounds, bounds[1:]):
        if out and b - a < 0.8: out[-1] = (out[-1][0], b)
        else: out.append((a, b))
    if len(out) > 1 and out[0][1] - out[0][0] < 0.8: out[1] = (0.0, out[1][1]); out.pop(0)
    return out


def scene_top(ctx, a, b):
    """Top row (source px) of the moving subject in one scene, captions excluded."""
    k = max(2, min(5, int((b - a) / 0.6)))
    fr = [grab(ctx, a + 0.1 + (b - a - 0.2) * i / (k - 1)) for i in range(k)]
    N = TW * TH; n = len(fr)
    mean = [sum(f[i] for f in fr) / n for i in range(N)]
    mot = [(sum((f[i] - mean[i]) ** 2 for f in fr) / n) ** 0.5 for i in range(N)]
    if sorted(mot)[int(N * 0.99)] < 6.0:   # a still scene: use detail instead of motion
        f = fr[0]; mot = [0.0] * N
        for y in range(1, TH - 1):
            for x in range(1, TW - 1):
                i = y * TW + x; mot[i] = abs(f[i + 1] - f[i - 1]) + abs(f[i + TW] - f[i - TW])
    band = (int(ctx.band[0] / ctx.k), int(ctx.band[1] / ctx.k) + 1) if ctx.band else None
    prof = [0.0 if band and band[0] <= y < band[1] else sum(mot[y * TW:(y + 1) * TW]) for y in range(TH)]
    prof = [(prof[max(0, y - 1)] + prof[y] + prof[min(TH - 1, y + 1)]) / 3 for y in range(TH)]
    pk = max(prof) or 1.0
    top = next((y for y in range(TH) if prof[y] >= 0.25 * pk), 0)
    bot = next((y for y in range(TH - 1, -1, -1) if prof[y] >= 0.25 * pk), TH - 1)
    return top * ctx.k, (bot + 1) * ctx.k


def punch_offsets(ctx, s, mode=None):
    """Per-scene vertical crop offset (source px) for a punch-in of scale s. The top of a
    talking head edited frame holds the cards and graphics; the space below the captions is
    mostly empty. So the image is pushed down: the crop comes off the bottom, as far as the
    captions (or, without captions, the content) allow, and the top survives."""
    vh = ctx.H0 / s; span = ctx.H0 - vh
    return [int(min(max(TOP_SHARE * span, b + 60 - vh, 0.0), span)) for b in ctx.bottoms]


def tilt_filter(deg, ctx):
    """A tilt that keeps the top: scale just enough to fill, rotate, then take the highest
    window that still lies wholly inside the rotated picture, so the crop falls off the
    bottom rather than the top. Captions stay in frame."""
    a = math.radians(deg); ca, sa = math.cos(abs(a)), math.sin(abs(a))
    f = ca + (H / W) * sa + 0.035
    Ws, Hs = even(W * f), even(H * f)
    bw, bh = even(Ws * ca + Hs * sa + 2), even(Ws * sa + Hs * ca + 2)
    cx, cy = bw / 2, bh / 2
    def inside(x, y):
        u = (x - cx) * math.cos(a) + (y - cy) * math.sin(a); v = -(x - cx) * math.sin(a) + (y - cy) * math.cos(a)
        return abs(u) <= Ws / 2 - 1 and abs(v) <= Hs / 2 - 1
    x0 = (bw - W) / 2; yt = None
    for y in range(0, bh - H + 1):
        if all(inside(x, yy) for x in (x0, x0 + W) for yy in (y, y + H)): yt = y; break
    if yt is None: yt = (bh - H) // 2
    else: yt = int(yt + TOP_SHARE * 2 * ((bh - H) / 2 - yt))   # a quarter of the removal off the top
    if ctx.band:   # the caption band, scaled about the centre, must end above the window's bottom
        bb = cy + (ctx.band[1] - H / 2) * f + 40
        while bb > yt + H and yt < (bh - H) // 2: yt += 1
    return "scale=%d:%d:flags=lanczos,rotate=%.5f:ow=%d:oh=%d:c=black,crop=%d:%d:%d:%d" % (Ws, Hs, a, bw, bh, W, H, int(x0), yt)


def piece(vals, starts, off):
    e = "%d" % vals[-1]
    for i in range(len(vals) - 2, -1, -1):
        e = "if(lt(t+%.3f,%.3f),%d,%s)" % (off, starts[i + 1], vals[i], e)
    return e


def remix_segments(ctx):
    """Jump cuts: the longest pauses between words shortened to a beat, never in the hook."""
    if not ctx.words: return None
    ws = ctx.words; gaps = []
    for i in range(len(ws) - 1):
        a, b = ws[i]["e"] + 0.10, ws[i + 1]["s"] - 0.10
        if b - a >= 0.20 and ws[i]["e"] > 2.5 and b < ctx.dur - 1.0: gaps.append((b - a, a, b))
    cuts = sorted(sorted(gaps, reverse=True)[:8], key=lambda g: g[1])
    if not cuts: return None
    segs, t = [], 0.0
    for _, a, b in cuts: segs.append((t, a)); t = b
    segs.append((t, ctx.dur))
    return segs


# ------------------------------------------------------------------ editable bases
def base_html(ctx, cfg, dur_ms=None):
    s = open(ctx.editable).read()
    css = ["<style id=\"rep-css\">"]
    if cfg.get("zoom"): css.append("#stage video { scale: %.3f; transform-origin: 50%% %d%%; }" % (cfg["zoom"], ctx.zoom_origin))
    if cfg.get("capfont") and ctx.band:
        fn = CAPFONTS[cfg["capfont"]][0]
        b64 = base64.b64encode(open(os.path.join(PKG, "fonts", fn), "rb").read()).decode()
        css.append("@font-face { font-family: 'RepCap'; src: url(data:font/ttf;base64,%s) format('truetype'); }" % b64)
    css.append("</style>\n")
    i = s.find("</head>"); s = s[:i] + "\n".join(css) + s[i:]
    inject = (FLIP_JS if cfg.get("mirror") else "")
    if cfg.get("capfont") and ctx.band: inject += CAPFONT_JS % (ctx.band[0], ctx.band[1], CAPFONTS[cfg["capfont"]][1])
    if inject:
        st = s.find('id="stage"'); j = s.find("<script", st)
        if j < 0: j = s.find("</body>")
        s = s[:j] + inject + s[j:]
    if dur_ms: s = re.sub(r'data-duration="\d+"', 'data-duration="%d"' % dur_ms, s, count=1)
    return s


def base_page(ctx, cfg, dur_ms=None):
    """Writes a repurpose editable beside the source editable, once per base. Every page of a
    run is built before any of them renders, and all are kept until the run ends."""
    tag = cfg["id"] + ("-%dms" % dur_ms if dur_ms else "")
    path = os.path.join(os.path.dirname(ctx.editable), "%s-repbase-%s.html" % (ctx.name, tag))
    if path not in ctx.pages:
        open(path, "w").write(base_html(ctx, cfg, dur_ms)); ctx.pages.append(path)
    return path


def render_base(ctx, cfg, out, dur_ms=None, fps=30):
    """Renders one repurpose editable. Called one at a time: rendering is GPU-heavy.
    On an error, its editable and its failed output are deleted, a new editable is built,
    and it renders once more. Only once: a second error skips that base."""
    err = ""
    for attempt in (1, 2):
        path = base_page(ctx, cfg, dur_ms)
        p = subprocess.run(["node", ctx.renderer, path, out, str(fps)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode == 0 and os.path.exists(out): return True, ""
        err = p.stderr.decode()[-600:] or "render failed"
        if os.path.exists(out): os.remove(out)
        if os.path.exists(path): os.remove(path)
        if path in ctx.pages: ctx.pages.remove(path)
        if attempt == 1: say("  base %s failed; deleted its editable and output, rebuilding and rendering once more" % cfg["id"])
    return False, err


def retire_pages(ctx):
    """When rendering is done (or the run stops), moves every repurpose editable of this run to
    the video's materials deletable/ folder. Never deletes them."""
    pages = [p for p in getattr(ctx, "pages", []) if os.path.exists(p)]
    if not pages: return
    dl = os.path.join(os.path.dirname(ctx.editable), "materials", ctx.name, "deletable"); os.makedirs(dl, exist_ok=True)
    for p in pages:
        stem, ext = os.path.splitext(os.path.basename(p)); dest = os.path.join(dl, stem + ext); k = 2
        while os.path.exists(dest): dest = os.path.join(dl, "%s_%d%s" % (stem, k, ext)); k += 1
        shutil.move(p, dest)
    say("repurpose editables moved to %s (%d)" % (dl, len(pages)))


# ------------------------------------------------------------------ post pass
def post(r, ctx, base, seek=None, clip=None, still=False):
    """ffmpeg arguments for one variant from its base. seek/still: a single frame at source
    time `seek` for the gate. clip: the first N seconds, for review."""
    ins = (["-ss", "%.3f" % seek] if seek is not None else []) + ["-i", base]
    f = []; off = seek or 0.0; lab = [0]
    def L(): lab[0] += 1; return "[p%d]" % lab[0]
    cur = "[0:v]"; parts = []
    chain = []; graded = [False]
    def picture_done():
        nonlocal cur, chain
        if graded[0]: return
        graded[0] = True
        if r.get("grade"): chain.append(GRADES[r["grade"]])
        if chain: o = L(); parts.append(cur + ",".join(chain) + o); cur = o; chain = []
        if r.get("halation"):
            a, b, hg, hb, o = L(), L(), L(), L(), L()
            parts.extend(["%ssplit=2%s%s" % (cur, a, b),
                          "%scurves=all='0/0 0.68/0 1/1',gblur=sigma=26,colorbalance=rh=0.12:bh=-0.08,format=gbrp%s" % (b, hg),
                          "%sformat=gbrp%s" % (a, hb), "%s%sblend=all_mode=screen:all_opacity=0.30,format=yuv420p%s" % (hb, hg, o)])
            cur = o
    for op in r["ops"]:
        if op[0] == "punch":
            _, s, mode, shake = op[:4]
            xa = op[4] if len(op) > 4 else 0.5   # where across the spare width the frame sits: 0.5 centred
            ys = punch_offsets(ctx, s, mode)
            sw, sh = even(W * s), even(H * s)
            yexp = piece([int(y * s) for y in ys], ctx.starts, off)
            chain.append("scale=%d:%d:flags=lanczos,crop=%d:%d:x='clip((iw-ow)*%.3f%s,0,iw-ow)':y='clip(%s%s,0,ih-oh)',unsharp=5:5:0.25"
                         % (sw, sh, W, H, xa, SHX if shake else "", yexp, SHY if shake else ""))
        elif op[0] == "tilt":
            chain.append(tilt_filter(op[1], ctx))
        elif op[0] == "border":
            picture_done()
            k = op[1]; iw_, ih_ = even(W * k), even(H * k)
            side = (W - iw_) // 2; place = op[3] if len(op) > 3 else ""
            py = side if place == "high" else H - ih_ - side if place == "low" else (H - ih_) // 2
            chain.append("scale=%d:%d:flags=lanczos,pad=%d:%d:%d:%d:color=black" % (iw_, ih_, W, H, (W - iw_) // 2, py))
            o = L(); parts.append(cur + ",".join(chain) + o); cur = o; chain = []
            ins += ["-i", r["_wash_png"]]; wi = len([x for x in ins if x == "-i"]) - 1; o2 = L()
            parts.append("%s[%d:v]overlay=0:0:format=auto%s" % (cur, wi, o2)); cur = o2
        elif op[0] == "post":
            picture_done()
            if chain: o = L(); parts.append(cur + ",".join(chain) + o); cur = o; chain = []
            ins += ["-i", r["_post_png"]]; pi = len([x for x in ins if x == "-i"]) - 1; b, o = L(), L()
            parts.append("%sscale=842:1498:flags=lanczos,pad=%d:%d:119:420%s" % (cur, W, H, b))
            parts.append("%s[%d:v]overlay=0:0:format=auto%s" % (b, pi, o)); cur = o
        elif op[0] == "blurframe":
            picture_done()
            k = op[1]; iw_, ih_ = even(W * k), even(H * k)
            place = op[2] if len(op) > 2 else ""
            oy = 70 if place == "high" else H - ih_ - 70 if place == "low" else (H - ih_) // 2
            if chain: cur_ = L(); parts.append(cur + ",".join(chain) + cur_); cur = cur_; chain = []
            a, b, bg, fg, o = L(), L(), L(), L(), L()
            parts.append("%ssplit=2%s%s" % (cur, a, b))
            parts.append("%sscale=54:96,boxblur=4:2,scale=1188:2112,crop=%d:%d%s" % (a, W, H, bg))
            parts.append("%sscale=%d:%d:flags=lanczos%s" % (b, iw_, ih_, fg))
            parts.append("%s%soverlay=%d:%d%s" % (bg, fg, (W - iw_) // 2, oy, o)); cur = o
    picture_done()
    if chain: o = L(); parts.append(cur + ",".join(chain) + o); cur = o
    if r.get("plate"):
        name, op_ = r["plate"]; ins += ["-stream_loop", "-1", "-i", os.path.join(PKG, "filter", name + ".mp4")]
        pi = len([x for x in ins if x == "-i"]) - 1; pb, pl, o = L(), L(), L()
        parts += ["%sformat=gbrp%s" % (cur, pb),
                  "[%d:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=30,format=gbrp%s" % (pi, W, H, W, H, pl),
                  "%s%sblend=all_mode=screen:all_opacity=%.2f:shortest=1,format=yuv420p%s" % (pb, pl, op_, o)]
        cur = o
    if r.get("vignette"): o = L(); parts.append("%svignette=PI/5%s" % (cur, o)); cur = o
    if r.get("_head_png"):
        ins += ["-i", r["_head_png"]]; hi = len([x for x in ins if x == "-i"]) - 1; o = L()
        parts.append("%s[%d:v]overlay=0:0:format=auto%s" % (cur, hi, o)); cur = o
    if still:
        o = L(); parts.append("%sscale=270:480%s" % (cur, o))
        return ins, ";".join(parts), o, None
    acur = "[0:a]"
    if base != ctx.source:   # the sound is the source's own: a rendered base's audio format never reaches a variant
        ins += (["-ss", "%.3f" % seek] if seek is not None else []) + ["-i", ctx.source]
        acur = "[%d:a]" % (len([x for x in ins if x == "-i"]) - 1)
    segs = ctx.segs if (r.get("remix") and clip is None) else None
    if segs:
        n = len(segs); vs = [L() for _ in range(n)]; as_ = [L() for _ in range(n)]
        parts.append("%ssplit=%d%s" % (cur, n, "".join(vs))); parts.append("%sasplit=%d%s" % (acur, n, "".join(as_)))
        cat = ""
        for i, (a, b) in enumerate(segs):
            tv, ta = L(), L()
            parts.append("%strim=%.3f:%.3f,setpts=PTS-STARTPTS%s" % (vs[i], a, b, tv))
            parts.append("%satrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st=%.3f:d=0.015%s" % (as_[i], a, b, max(0, b - a - 0.015), ta))
            cat += tv + ta
        cv, ca = L(), L(); parts.append("%sconcat=n=%d:v=1:a=1%s%s" % (cat, n, cv, ca)); cur, acur = cv, ca
    sp, pt = r.get("speed", 1.0), r.get("pitch", 1.0)
    if sp != 1.0: o = L(); parts.append("%ssetpts=PTS/%.3f%s" % (cur, sp, o)); cur = o
    o = L(); parts.append("%sformat=yuv420p%s" % (cur, o)); cur = o
    af = ["aresample=%d" % ctx.sr]   # a rendered base can carry another rate; pitch assumes the source's
    if pt != 1.0: af += ["asetrate=%d" % round(ctx.sr * pt), "aresample=%d" % ctx.sr]
    if sp / pt != 1.0: af.append("atempo=%.4f" % (sp / pt))
    o = L(); parts.append("%s%s%s" % (acur, ",".join(af), o)); acur = o
    return ins, ";".join(parts), cur, acur


def wrap(d, text, font, width):
    """Greedy lines within `width`, never a single word alone on the last line."""
    lines, cur = [], []
    for w in text.split():
        if d.textlength(" ".join(cur + [w]), font=font) <= width or not cur: cur.append(w)
        else: lines.append(" ".join(cur)); cur = [w]
    if cur: lines.append(" ".join(cur))
    if len(lines) > 1 and len(lines[-1].split()) == 1 and len(lines[-2].split()) > 1:
        pv = lines[-2].split(); lines[-2] = " ".join(pv[:-1]); lines[-1] = pv[-1] + " " + lines[-1]
    return lines


def profile_img(name, pset, height):
    pf = Image.open(os.path.join(PKG, "fropile", pset + "-background", name)).convert("RGBA")
    return pf.resize((round(pf.width * height / pf.height), height), Image.LANCZOS)


def post_frame(ctx, quip, prof, path):
    """The one designed variant: a social post with a profile and a quip.
    Ground counters the source's tone. The video shows through a rounded window."""
    light = ctx.luma < 0.45
    bg, ink, pset = ((242, 242, 242), (17, 17, 17), "light") if light else ((0, 0, 0), (255, 255, 255), "dark")
    im = Image.new("RGBA", (W, H), bg + (255,)); d = ImageDraw.Draw(im)
    im.alpha_composite(profile_img(prof, pset, 120), (119, 180))
    f = ImageFont.truetype(os.path.join(PKG, "fonts", "DejaVuSans.ttf"), 40)
    for i, ln in enumerate(wrap(d, quip, f, 842)[:2]): d.text((119, 310 + i * 46), ln, font=f, fill=ink)
    k = 4; m = Image.new("L", (W * k, H * k), 255)
    ImageDraw.Draw(m).rounded_rectangle((119 * k, 420 * k, (119 + 842) * k, (420 + 1498) * k), radius=24 * k, fill=0)
    im.putalpha(m.resize((W, H), Image.LANCZOS)); im.save(path)


HEAD_TOP = 120   # clear of the platform's own top bar
PROFILE_ROOM = 250   # px above the video a profile-and-quip header needs; less room gets the quip alone


def head_slot(r):
    """Where a low-placed video sits: (left, width, top, kind), or None when it is not low."""
    for op in r["ops"]:
        if op[0] == "blurframe" and len(op) > 2 and op[2] == "low":
            iw_, ih_ = even(W * op[1]), even(H * op[1]); return (W - iw_) // 2, iw_, H - ih_ - 70, "blur"
        if op[0] == "border" and len(op) > 3 and op[3] == "low":
            iw_, ih_ = even(W * op[1]), even(H * op[1]); sd = (W - iw_) // 2; return sd, iw_, H - ih_ - sd, "border"
    return None


def head_frame(ctx, r, quip, prof, path):
    """The space above a low-placed video, filled the way a repost fills it: a profile and the
    quip like a post, or the quip alone, bold and centred, like a caption. Transparent elsewhere.
    Returns the mode it could fit."""
    from PIL import ImageFilter
    x, iw_, vy, kind = head_slot(r)
    dark_ink = kind == "border"   # on a blur frame: white over a soft scrim, readable on any picture
    ink, pset = ((22, 22, 22), "light") if dark_ink else ((255, 255, 255), "dark")
    band = vy - 28 - HEAD_TOP
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    def fit(with_prof):
        face = "DejaVuSans.ttf" if with_prof else "DejaVuSans-Bold.ttf"
        for fs in range(44, 29, -2):
            f = ImageFont.truetype(os.path.join(PKG, "fonts", face), fs)
            lines = wrap(d, quip, f, iw_ if with_prof else iw_ - 40); lh = int(fs * 1.24)
            hp = min(112, int(band * 0.40)) if with_prof else 0
            h = (hp + int(fs * 0.5) if with_prof else 0) + lh * len(lines)
            if len(lines) <= 3 and h <= band and (not with_prof or (hp >= 90 and fs >= 36)): return f, lines, lh, hp, h
        return None
    lay = fit(True) if r["header"] == "profile" and prof else None
    mode = "profile" if lay else "quip"
    lay = lay or fit(False)
    if not lay:   # the quip is too long for the room: keep what fits, smallest size
        f = ImageFont.truetype(os.path.join(PKG, "fonts", "DejaVuSans-Bold.ttf"), 30); lh = 37
        lines = wrap(d, quip, f, iw_ - 40)[:max(1, band // lh)]; lay = (f, lines, lh, 0, lh * len(lines))
    f, lines, lh, hp, h = lay
    y0 = HEAD_TOP + (band - h) // 2
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tx = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dt = ImageDraw.Draw(tx)
    if not dark_ink:   # the darkening a platform lays over the top of a video, fading out above the inset
        col = Image.new("L", (1, H), 0)
        for yy in range(vy): col.putpixel((0, yy), int(255 * 0.55 * (1 - (yy / vy) ** 1.6)))
        sc = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sc.putalpha(col.resize((W, H))); im.alpha_composite(sc)
    if mode == "profile":
        im.alpha_composite(profile_img(prof, pset, hp), (x - int(hp * 0.1), y0)); ty = y0 + hp + int(f.size * 0.5)
        for i, ln in enumerate(lines): dt.text((x, ty + i * lh), ln, font=f, fill=ink)
    else:
        for i, ln in enumerate(lines): dt.text((W // 2, y0 + i * lh), ln, font=f, fill=ink, anchor="ma")
    if not dark_ink:   # white words over a moving blurred picture: a soft shadow keeps them readable
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(tx.getchannel("A").point(lambda v: v * 0.55))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    im.alpha_composite(tx); im.save(path)
    return mode


class Ledger:
    """Quips and profiles already used by other videos in this renders folder, so no two videos
    share one. A re-run of the same video may reuse its own."""
    def __init__(self, ctx):
        self.path = os.path.join(os.path.dirname(ctx.source), ".repurpose-ledger.json"); self.src = ctx.name
        try: self.data = json.load(open(self.path))
        except Exception: self.data = {}
        self.data.setdefault("profiles", {}); self.data.setdefault("quips", {})
    def quip_taken(self, q):
        return self.data["quips"].get(" ".join(q.lower().split()), self.src) != self.src
    def profiles(self):
        """Every profile, least recently used by another video first; stable for this video."""
        names = sorted(f for f in os.listdir(os.path.join(PKG, "fropile", "light-background")) if f.endswith(".png"))
        seed = sum(ord(c) * (i + 1) for i, c in enumerate(self.src))
        def key(n):
            u = self.data["profiles"].get(n)
            return ("" if not u or u["src"] == self.src else u["t"], (names.index(n) * 7 + seed) % len(names))
        return sorted(names, key=key)
    def record(self, quips, profs):
        t = datetime.datetime.now().isoformat(timespec="seconds")
        for q in quips: self.data["quips"][" ".join(q.lower().split())] = self.src
        for p_ in profs: self.data["profiles"][p_] = {"src": self.src, "t": t}
        json.dump(self.data, open(self.path, "w"), indent=1)


def ffrun(ins, fc, outargs):
    p = subprocess.run(["ffmpeg", "-y", "-v", "error"] + ins + ["-filter_complex", fc] + outargs,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stderr.decode()[-700:]


# ------------------------------------------------------------------ the pool
# Border washes: soft two-stop gradients, never solid saturated colour. Pastels for dark
# or mixed sources; dusty deeper tones so a border still separates from a light source.
WASHES = {
 "peach": ("#FDE4D6", "#F6C9B5"), "lilac": ("#EEE6FB", "#D8CBF2"), "mint": ("#DFF4E9", "#C3E7D4"),
 "sky": ("#DFEEFB", "#C4DBF1"), "butter": ("#FBF4D8", "#F1E2AF"), "rose": ("#FBE3E9", "#F1C6D2"),
 "sage": ("#E8EFE1", "#D0DCC4"), "sand": ("#F4EDE3", "#E2D3BF"),
 "dusty-blue": ("#B9C6D8", "#98A8BF"), "dusty-rose": ("#D8B9C1", "#BF9BA6"), "dusty-sage": ("#B9C7B1", "#9CAE92"),
 "taupe": ("#CBBCA9", "#B09F8B"), "slate": ("#A2ACBA", "#838E9D"),
}


def wash_frame(name, k, place, path):
    """A border as a soft gradient frame with a rounded window where the video shows."""
    c1, c2 = (tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in WASHES[name])
    col = Image.new("RGB", (1, 256))
    for y in range(256): t = y / 255; col.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(c1, c2)))
    im = col.resize((W, H), Image.BICUBIC).convert("RGBA")
    iw_, ih_ = even(W * k), even(H * k); x = (W - iw_) // 2
    y = x if place == "high" else H - ih_ - x if place == "low" else (H - ih_) // 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x - 4, y + 6, x + iw_ + 4, y + ih_ + 14), radius=26, fill=(0, 0, 0, 70))
    from PIL import ImageFilter
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    k4 = 4; m = Image.new("L", (W * k4, H * k4), 255)
    ImageDraw.Draw(m).rounded_rectangle((x * k4, y * k4, (x + iw_) * k4, (y + ih_) * k4), radius=22 * k4, fill=0)
    im.putalpha(m.resize((W, H), Image.LANCZOS)); im.save(path)


BASES = {"mirror": dict(id="mirror", mirror=True),
         "mirror-serif": dict(id="mirror-serif", mirror=True, capfont="serif"),
         "mirror-mono": dict(id="mirror-mono", mirror=True, capfont="mono"),
         "sans": dict(id="sans", capfont="sans"), "serif": dict(id="serif", capfont="serif"), "mono": dict(id="mono", capfont="mono"),
         "mirror-zoom": dict(id="mirror-zoom", mirror=True, zoom=1.15), "zoom": dict(id="zoom", zoom=1.20)}


def pool(ctx):
    GEO = [  # name, operations. Colour never counts to a matcher; geometry does. Every zoom and
             # tilt keeps the top of the frame; insets keep the whole frame and move it up or down.
             # A low inset leaves room above it, which a header fills: see head_frame.
     ("plain",        []),
     ("face",         [("punch", 1.22, "top", False)]),
     ("border",       [("punch", 1.10, "top", False), ("border", 0.88, "wash")]),
     ("blur",         [("punch", 1.12, "top", False), ("blurframe", 0.78)]),
     ("border-high",  [("punch", 1.10, "top", False), ("border", 0.86, "wash", "high")]),
     ("blur-low",     [("punch", 1.10, "top", False), ("blurframe", 0.74, "low")]),
     ("handheld",     [("punch", 1.15, "top", True)]),
     ("border-low",   [("punch", 1.10, "top", False), ("border", 0.76, "wash", "low")]),
     ("blur-high",    [("punch", 1.10, "top", False), ("blurframe", 0.80, "high")]),
     ("border-tilt",  [("punch", 1.12, "top", False), ("tilt", 2.0), ("border", 0.88, "wash")]),
     ("small-low",    [("blurframe", 0.70, "low")]),
     ("small-high",   [("blurframe", 0.70, "high")]),
     ("thick-high",   [("punch", 1.12, "top", False), ("border", 0.78, "wash", "high")]),
     ("thick-low",    [("punch", 1.12, "top", False), ("border", 0.70, "wash", "low")]),
     ("tilt",         [("punch", 1.10, "top", False), ("tilt", 2.5)]),
     ("face-tilt",    [("punch", 1.20, "top", False), ("tilt", -2.0)]),
     ("blur-small",   [("blurframe", 0.70)]),
     ("tilt-blur-low",  [("tilt", 2.0), ("blurframe", 0.74, "low")]),
     ("tilt-border-high", [("tilt", -2.0), ("border", 0.84, "wash", "high")]),
     ("tilt-only",    [("tilt", 2.5)]),
     # an off-centre hold: a gentle punch-in sitting left or right. At 1.14 it takes 38 px off one
     # side and 113 off the other, so centred captions up to 850 px wide stay whole
     ("pan-left",     [("punch", 1.14, "top", False, 0.25)]),
     ("pan-right",    [("punch", 1.14, "top", False, 0.75)]),
     ("pan-left-tilt", [("punch", 1.16, "top", False, 0.25), ("tilt", -1.5)]),
     ("pan-right-blur", [("punch", 1.14, "top", False, 0.75), ("blurframe", 0.84)]),
     ("tilt-only-left", [("tilt", -2.5)]),
    ]
    SEASON = [dict(grade="warm", speed=1.03, pitch=1.02), dict(grade="modern", speed=1.02, pitch=0.98),
              dict(grade="cool", speed=1.04), dict(grade="faded", speed=1.02, pitch=1.02, plate=("dust", 0.4)),
              dict(grade="mono", speed=1.03, plate=("grain", 0.35)), dict(speed=1.05, vignette=True),
              dict(grade="warm", halation=True, plate=("old-film", 0.45), speed=1.02, pitch=0.97), dict(grade="modern", speed=1.04, remix=True),
              dict(grade="cool", speed=1.03, pitch=1.02, vignette=True)]
    lum = lambda c: (0.2126 * int(c[1:3], 16) + 0.7152 * int(c[3:5], 16) + 0.0722 * int(c[5:7], 16)) / 255
    span = [e - s0 for s0, e in ctx.scenes]; tot = sum(span) or 1.0
    def score(pair):
        m = (lum(pair[0]) + lum(pair[1])) / 2
        return sum(sp for sp, e in zip(span, ctx.edge_lumas) if abs(m - e) >= 0.18) / tot
    good = [k for k, pr in WASHES.items() if score(pr) >= 0.70 and abs((lum(pr[0]) + lum(pr[1])) / 2 - ctx.edge_lumas[0]) >= 0.18]
    COLOURS = good if len(good) >= 4 else sorted(WASHES, key=lambda k: -score(WASHES[k]))[:4]
    light_w = [c for c in COLOURS if not c.startswith(("dusty", "taupe", "slate"))]
    deep_w = [c for c in COLOURS if c.startswith(("dusty", "taupe", "slate"))]
    if light_w and deep_w:
        COLOURS = [c for pair in zip(light_w * 3, deep_w * 3) for c in pair][:len(COLOURS)]
    P = []; n = 0; nc = [0]
    def paint(ops):
        out = []
        for op in ops:
            if op[0] == "border": op = (op[0], op[1], COLOURS[nc[0] % len(COLOURS)]) + tuple(op[3:]); nc[0] += 1
            out.append(op)
        return out
    if ctx.quips:
        P.append(dict(name="post", base="orig", ops=[("post",)], speed=1.03, pitch=1.02))
    MB, SB = ["mirror", "mirror-serif", "mirror", "mirror-mono"], ["orig", "sans", "orig", "serif"]
    for gi, (gname, ops) in enumerate(GEO):
        for side in ("mirror", "straight"):
            if side == "straight" and gname == "plain": continue
            base = MB[gi % 4] if side == "mirror" else SB[gi % 4]
            P.append(dict(name="%s-%s" % (side, gname), base=base, ops=paint(ops), **SEASON[n % len(SEASON)])); n += 1
    for gname, base, ops in (("persona", "zoom", []), ("persona-border", "zoom", [("border", 0.90, "#E11D48")]),
                             ("persona-blur", "zoom", [("blurframe", 0.82)]), ("mirror-persona", "mirror-zoom", []),
                             ("mirror-persona-tilt", "mirror-zoom", [("tilt", 2.0)])):
        P.append(dict(name=gname, base=base, ops=paint(ops), **SEASON[n % len(SEASON)])); n += 1
    ok = []; hn = 0
    for r in P:
        if head_slot(r):   # a low video leaves room above it: never left empty
            if not ctx.quips: continue
            room = head_slot(r)[2] - 28 - HEAD_TOP
            r["header"] = "profile" if room >= PROFILE_ROOM and hn % 2 == 0 else "quip"; hn += room >= PROFILE_ROOM
        if r["base"] != "orig" and not ctx.editable_ok: r["base"] = "mirror" if r["base"].startswith("mirror") else "orig"
        if r["base"] != "orig" and not ctx.editable_ok: continue
        if BASES.get(r["base"], {}).get("capfont") and not ctx.band and not BASES[r["base"]].get("mirror"): r["base"] = "orig"
        if r["base"].startswith("mirror") and ctx.no_mirror: continue
        if r.get("remix") and not ctx.segs: r["remix"] = False
        if any(op[0] == "punch" and punch_offsets(ctx, op[1], op[2]) is None for op in r["ops"]): continue
        ok.append(r)
    return ok


# ------------------------------------------------------------------ run
class Ctx: pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True); ap.add_argument("--editable"); ap.add_argument("--timings")
    ap.add_argument("--cm"); ap.add_argument("--out"); ap.add_argument("--preview-only", action="store_true")
    ap.add_argument("--count", type=int, default=20, help="how many repurposes to keep, 1 to 20 (default 20)")
    ap.add_argument("--no-mirror", action="store_true"); ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--keep-temp", action="store_true")
    ap.add_argument("--quip", action="append", default=[],
                    help="a quip for the post and the headers above low-placed videos; repeat it, one per quip, "
                         "every one different. Without quips, those variants are skipped")
    ap.add_argument("--preview-at", type=float, default=0.0, help="where the 2-second previews start, in seconds")
    ap.add_argument("--dry-run", action="store_true", help="measure and select only; render nothing")
    ap.add_argument("--caption-band", help="Y0,Y1 rows of the baked captions, when the session knows better than detection")
    ap.add_argument("--repair", action="store_true",
                    help="re-check a rendered set against the gate, replace only the variants that fail, "
                         "and add any missing to reach the full count")
    ap.add_argument("--only", help="comma-separated variant names or numbers to render, e.g. 4,11 or straight-border")
    a = ap.parse_args()
    global NEED
    if not 1 <= a.count <= 20: sys.exit("--count must be 1 to 20")
    NEED = a.count
    ctx = Ctx(); ctx.source = os.path.abspath(a.source); ctx.no_mirror = a.no_mirror; ctx.quips = []; ctx.pages = []
    ctx.W0, ctx.H0, ctx.frames, ctx.dur, ctx.sr = probe(ctx.source)
    if abs(ctx.W0 / ctx.H0 - 9 / 16) > 0.01 or ctx.W0 != W: sys.exit("The source must be a 1080 x 1920 render.")
    ctx.k = ctx.W0 / TW; ctx.name = os.path.splitext(os.path.basename(ctx.source))[0]
    root = os.path.dirname(os.path.dirname(ctx.source))
    tp = a.timings or os.path.join(root, "editable", "materials", ctx.name, "timings.json")
    ctx.words = json.load(open(tp))["words"] if os.path.exists(tp) else None
    ctx.editable = os.path.abspath(a.editable or os.path.join(root, "editable", ctx.name + ".html"))
    # Super Nova: the renderer is in the designers' shared folder, passed with --cm;
    # without it, <super>/Agents/DesignerShared is used.
    cm = a.cm
    if not cm:
        agents = os.path.dirname(os.path.dirname(PKG))   # <super>/Agents/DesignerShared/repurpose
        cm = os.path.join(agents, "DesignerShared")
        if not os.path.exists(os.path.join(cm, "tools", "render", "render.js")): cm = None
    ctx.renderer = os.path.join(cm, "tools", "render", "render.js") if cm else None
    ctx.editable_ok = os.path.exists(ctx.editable) and ctx.renderer and os.path.exists(ctx.renderer)
    edir = os.path.dirname(ctx.editable)   # pages a killed run left behind are never reused
    stale = [f for f in (os.listdir(edir) if os.path.isdir(edir) else []) if f.startswith(ctx.name + "-repbase-") and f.endswith(".html")]
    for f in stale: os.remove(os.path.join(edir, f))
    if stale: say("removed %d repurpose editables left by a stopped run" % len(stale))
    ctx.band = (tuple(int(v) for v in a.caption_band.split(",")) if a.caption_band
                else detect_band(ctx) if ctx.words else None)
    ctx.scenes = detect_scenes(ctx); ctx.starts = [s for s, _ in ctx.scenes]
    tb = [scene_top(ctx, s, e) for s, e in ctx.scenes]
    ctx.tops = [t for t, _ in tb]
    # what must stay in view at the bottom: the captions if there are any, else the content
    ctx.bottoms = [ctx.band[1] if ctx.band else b for _, b in tb]
    ctx.zoom_origin = int(min(60, max(15, 100 * (sorted(ctx.tops)[len(ctx.tops) // 2] + 0.12 * ctx.H0) / ctx.H0)))
    ctx.segs = remix_segments(ctx)
    ctx.luma = sum(sum(grab(ctx, ctx.dur * (i + 0.5) / 8)) for i in range(8)) / (8 * TW * TH * 255.0)
    ctx.ledger = Ledger(ctx)
    for q in a.quip:
        q = " ".join(q.split())
        if not q or q.lower() in [x.lower() for x in ctx.quips]: continue
        if ctx.ledger.quip_taken(q): say("quip      skipped, another video already used it: %s" % q); continue
        ctx.quips.append(q)
    ctx.edge_lumas = []
    for s0, e0 in ctx.scenes:   # the outer tenth of each scene's frame, where a border meets the picture
        f = grab(ctx, (s0 + e0) / 2); bx, by = TW // 10, TH // 10
        px = [f[y * TW + x] for y in range(TH) for x in range(TW) if x < bx or x >= TW - bx or y < by or y >= TH - by]
        ctx.edge_lumas.append(sum(px) / (len(px) * 255.0))
    say("source    %s  %.2fs  %d frames" % (ctx.name, ctx.dur, ctx.frames))
    say("editable  %s" % ("found, mirrored bases available" if ctx.editable_ok else "not available, MP4 variants only"))
    say("captions  %s" % ("rows %d-%d, always kept whole in frame" % ctx.band if ctx.band else "none detected"))
    say("scenes    %d (cuts at %s)" % (len(ctx.scenes), " ".join("%.1f" % s for s in ctx.starts[1:]) or "none"))
    say("subject   top per scene " + " ".join(str(int(t)) for t in ctx.tops) + ", persona zoom origin %d%%" % ctx.zoom_origin)
    say("quips     %d distinct" % len(ctx.quips))
    say("remix     %s" % ("%d jump cuts on pauses" % (len(ctx.segs) - 1) if ctx.segs else "off (no timings)"))
    P = pool(ctx)
    tmp = tempfile.mkdtemp(prefix="repurpose-")
    for i, r in enumerate(P):
        bo = next((o for o in r["ops"] if o[0] == "border"), None)
        if bo:
            r["_wash_png"] = os.path.join(tmp, "wash-%d.png" % i)
            wash_frame(bo[2], bo[1], bo[3] if len(bo) > 3 else "", r["_wash_png"])
            r["_wash"] = bo[2]
    profs = ctx.ledger.profiles()
    if ctx.quips:   # stand-ins for measuring; the real quips and profiles are dealt once the set is chosen
        post_frame(ctx, ctx.quips[0], profs[0], os.path.join(tmp, "post.png"))
        for i, r in enumerate(P):
            if r["name"] == "post": r["_post_png"] = os.path.join(tmp, "post.png")
            if r.get("header"):
                r["_head_png"] = os.path.join(tmp, "head-%d.png" % i); head_frame(ctx, r, ctx.quips[0], profs[0], r["_head_png"])
    try:
        # ---- choose: hash the variants against the original, sampled and matched exactly as the
        # final gate does, so a set chosen here passes there
        fr = G.FRACS; times = [min(f * ctx.dur, ctx.dur - 0.1) for f in fr]
        ref = G.dense(ctx.source)
        # a mirrored or zoomed base changes only the video layers, so how far it moves the hash
        # depends on how much of each frame they fill; render those bases for real at a low
        # frame rate and measure. Caption faces barely move a hash and share their geometry's render.
        geo = lambda b: "mirror" if b in ("mirror-serif", "mirror-mono") else "orig" if b in ("sans", "serif", "mono") else b
        sel = {"orig": ctx.source}
        sel_bases = sorted({geo(r["base"]) for r in P} - {"orig"})
        for b in sel_bases: base_page(ctx, BASES[b])           # all editables first ...
        for b in sel_bases:                                     # ... then render one at a time
            bp = os.path.join(tmp, "sel-%s.mp4" % b)
            say("measuring base %s (%d fps)" % (b, SEL_FPS))
            ok_, err = render_base(ctx, BASES[b], bp, fps=SEL_FPS)
            if ok_: sel[b] = bp
            else: say("  base failed, its variants are skipped: %s" % err)
        P = [r for r in P if geo(r["base"]) in sel]
        def still(job):
            r, i, t = job; out = os.path.join(tmp, "st-%s-%d.png" % (r["name"], i))
            ins, fc, v, _ = post(r, ctx, sel[geo(r["base"])], seek=t, still=True)
            rc, err = ffrun(ins, fc, ["-map", v, "-frames:v", "1", out])
            return r["name"], i, (G.image_hash(out) if rc == 0 else None), err
        hs = {}
        with cf.ThreadPoolExecutor(6) as ex:
            for nm, i, h, err in ex.map(still, [(r, i, t) for r in P for i, t in enumerate(times)]):
                if h is None: say("  still failed: %s %s" % (nm, err)); continue
                hs.setdefault(nm, {})[i] = h
        S = {nm: [(fr[i], d[i]) for i in range(len(fr))] for nm, d in hs.items() if len(d) == len(fr)}
        chosen = []; CAP = {"blur": 8, "border": 7}; used = {}
        hcap = len(ctx.quips) - (1 if any(r["name"] == "post" for r in P) else 0)   # one quip each, never shared
        fam = lambda r: "blur" if any(o[0] == "blurframe" for o in r["ops"]) else "border" if any(o[0] == "border" for o in r["ops"]) else "full"
        say("\ncandidate              base          vs orig  nearest kept")
        for r in P:
            if r["name"] not in S: continue
            do = G.best_match(S[r["name"]], ref)
            near = min([(G.best_match(S[r["name"]], S[c["name"]]), c["name"]) for c in chosen] or [(64, "-")])
            capped = used.get(fam(r), 0) >= CAP.get(fam(r), 99) or (r.get("header") and used.get("header", 0) >= hcap)
            ok = do >= ORIG_MIN and near[0] >= PAIR_MIN and len(chosen) < NEED and not capped
            v = ("KEEP" if ok else "full" if len(chosen) >= NEED else "too close to original" if do < ORIG_MIN
                 else "too close to " + near[1] if near[0] < PAIR_MIN
                 else "no quip left for its header" if r.get("header") and used.get("header", 0) >= hcap else "enough %s variants already" % fam(r))
            if ok: used[fam(r)] = used.get(fam(r), 0) + 1; used["header"] = used.get("header", 0) + bool(r.get("header"))
            say("%-22s %-12s %5d    %3d %-20s %s" % (r["name"], r["base"], do, near[0], near[1], v))
            if ok: chosen.append(r)
        say("\nkept %d of %d" % (len(chosen), len(P)))
        # caption faces don't move the hash, so deal them round-robin across the kept set
        if ctx.band and ctx.editable_ok:
            mi = si = 0
            for r in chosen:
                if r["base"] in ("mirror", "mirror-serif", "mirror-mono"):
                    r["base"] = ["mirror", "mirror-serif", "mirror-mono"][mi % 3]; mi += 1
                elif r["base"] in ("orig", "sans", "serif", "mono") and r["name"] != "post":
                    r["base"] = ["orig", "sans", "mono"][si % 3]; si += 1
        # deal every quip and profile once: none repeats in this set, nor across videos in this folder
        qi = 0; pi_ = 0; used_q, used_p = [], []
        for n_, r in enumerate(chosen, 1):
            if r["name"] == "post":
                r["_quip"], r["_prof"] = ctx.quips[qi], profs[pi_]; qi += 1; pi_ += 1
                r["_post_png"] = os.path.join(tmp, "post-dealt.png"); post_frame(ctx, r["_quip"], r["_prof"], r["_post_png"])
            elif r.get("header"):
                r["_quip"] = ctx.quips[qi]; qi += 1
                r["_head_png"] = os.path.join(tmp, "head-dealt-%d.png" % n_)
                r["header"] = head_frame(ctx, r, r["_quip"], profs[pi_], r["_head_png"])
                if r["header"] == "profile": r["_prof"] = profs[pi_]; pi_ += 1
            if r.get("_quip"): used_q.append(r["_quip"])
            if r.get("_prof"): used_p.append(r["_prof"])
        def recipe(r):
            ops = " + ".join(("%s %s" % (o[0], o[1]) if len(o) > 1 else o[0]) for o in r["ops"]) or "no reframe"
            if r.get("_wash"): ops += " (%s wash)" % r["_wash"]
            if r.get("header"): ops += " + %s header" % ("profile-and-quip" if r["header"] == "profile" else "quip")
            if r.get("_prof"): ops += " [%s]" % os.path.splitext(r["_prof"])[0]
            if r.get("_quip"): ops += ' "%s"' % r["_quip"]
            cap = BASES.get(r["base"], {}).get("capfont")
            bits = [r["base"] if r["base"] != "orig" else "original", ops]
            if cap and ctx.band: bits.append("captions in DejaVu %s" % cap)
            for k in ("grade", "plate"):
                if r.get(k): bits.append("%s %s" % (k, r[k] if k == "grade" else r[k][0]))
            if r.get("halation"): bits.append("halation")
            if r.get("remix") and ctx.segs: bits.append("remix cuts")
            if r.get("speed", 1) != 1: bits.append("speed %.2f" % r["speed"])
            if r.get("pitch", 1) != 1: bits.append("pitch %.2f" % r["pitch"])
            return ", ".join(bits)
        for n, r in enumerate(chosen, 1): say("  Rep%02d %-20s %s" % (n, r["name"], recipe(r)))
        if a.dry_run: return
        if len(chosen) < NEED: say("SHORTFALL: only %d variants are distinct enough for this video." % len(chosen))
        out_dir = os.path.abspath(a.out or os.path.dirname(ctx.source)); os.makedirs(out_dir, exist_ok=True)
        numbered = list(enumerate(chosen, 1))
        if a.only:
            want = {w.strip() for w in a.only.split(",")}
            numbered = [(n, r) for n, r in numbered if r["name"] in want or str(n) in want or "%02d" % n in want]
            chosen = [r for _, r in numbered]
        need_bases = [] if a.repair else sorted({r["base"] for r in chosen} - {"orig"})
        # ---- bases
        bases = {"orig": ctx.source}
        pdur = int((a.preview_at + PREVIEW_S) * 1000 + 200) if a.preview_only else None
        for b in need_bases: base_page(ctx, BASES[b], pdur)    # all editables first ...
        for b in need_bases:                                     # ... then render one at a time
            bp = os.path.join(tmp, "base-%s.mp4" % b)
            say("rendering base %-12s %s" % (b, "(2 s preview)" if a.preview_only else "(full)"))
            ok, err = render_base(ctx, BASES[b], bp, int((a.preview_at + PREVIEW_S) * 1000 + 200) if a.preview_only else None)
            if not ok: say("  base failed: %s" % err); continue
            bases[b] = bp
        chosen = [r for r in chosen if r["base"] in bases]
        if a.preview_only:
            pdir = os.path.join(out_dir, "%s-repurpose-preview" % ctx.name); os.makedirs(pdir, exist_ok=True)
            def clip(job):
                n, r = job; out = os.path.join(pdir, "Rep%02d-%s.mp4" % (n, r["name"]))
                ins, fc, v, al = post(r, ctx, bases[r["base"]], seek=a.preview_at or None, clip=PREVIEW_S)
                oa = ["-map", v] + (["-map", al] if al else ["-map", "0:a"]) + ["-t", "%.2f" % PREVIEW_S, "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", "-b:a", "160k", out]
                rc, err = ffrun(ins, fc, oa); return n, r, out if rc == 0 else None, err
            clips = []
            with cf.ThreadPoolExecutor(a.jobs + 2) as ex:
                for n, r, out, err in ex.map(clip, numbered):
                    if out: clips.append((n, r, out))
                    else: say("  clip failed Rep%02d %s: %s" % (n, r["name"], err))
            clips.sort()
            cols = 5; rows = math.ceil(len(clips) / cols); tw_, th_ = 216, 384
            sheet = Image.new("RGB", (cols * tw_, rows * (th_ + 26)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
            lab = Image.new("RGBA", (cols * tw_, rows * (th_ + 26)), (0, 0, 0, 0)); dl = ImageDraw.Draw(lab)
            fnt = ImageFont.truetype(os.path.join(PKG, "fonts", "DejaVuSans.ttf"), 14)
            for idx, (n, r, out) in enumerate(clips):
                png = os.path.join(tmp, "sheet-%d.png" % n)
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1.0", "-i", out, "-frames:v", "1", "-vf", "scale=%d:%d" % (tw_, th_), png])
                x, y = (idx % cols) * tw_, (idx // cols) * (th_ + 26)
                sheet.paste(Image.open(png).convert("RGB"), (x, y))
                for dd in (d, dl): dd.text((x + 6, y + th_ + 5), "Rep%02d %s" % (n, r["name"]), font=fnt, fill=(235, 235, 235, 255))
            sheet.save(os.path.join(pdir, "contact-sheet.png")); lab.save(os.path.join(tmp, "labels.png"))
            ins = []; fc = []
            for idx, (n, r, out) in enumerate(clips):
                ins += ["-i", out]; fc.append("[%d:v]scale=%d:%d,setsar=1,fps=30,trim=0:%.2f,setpts=PTS-STARTPTS,pad=%d:%d:0:0:color=0x141414[g%d]" % (idx, tw_, th_, PREVIEW_S, tw_, th_ + 26, idx))
            for idx in range(len(clips), rows * cols):
                fc.append("color=c=0x141414:s=%dx%d:d=%.2f:r=30[g%d]" % (tw_, th_ + 26, PREVIEW_S, idx))
            layout = "|".join("%d_%d" % ((i % cols) * tw_, (i // cols) * (th_ + 26)) for i in range(rows * cols))
            fc.append("%sxstack=inputs=%d:layout=%s[grid]" % ("".join("[g%d]" % i for i in range(rows * cols)), rows * cols, layout))
            ins += ["-framerate", "30", "-loop", "1", "-i", os.path.join(tmp, "labels.png")]
            fc.append("[grid][%d:v]overlay=0:0:shortest=0,trim=0:%.2f[gv]" % (len(clips), PREVIEW_S))
            rc, err = ffrun(ins, ";".join(fc), ["-map", "[gv]", "-an", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", os.path.join(pdir, "grid.mp4")])
            if rc: say("grid failed: %s" % err)
            say("\npreview   %s  (%d clips, contact-sheet.png, grid.mp4)" % (pdir, len(clips)))
            return
        # ---- full render
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        def full(job):
            n, r = job; out = os.path.join(out_dir, "%s-Rep%02d.mp4" % (ctx.name, n))
            if os.path.exists(out):
                dl = os.path.join(out_dir, "deletable"); os.makedirs(dl, exist_ok=True)
                shutil.move(out, os.path.join(dl, "%s-Rep%02d_%s.mp4" % (ctx.name, n, stamp)))
            for attempt in (1, 2):
                ins, fc, v, al = post(r, ctx, bases[r["base"]])
                oa = ["-map", v] + (["-map", al, "-c:a", "aac", "-b:a", "192k"] if al else ["-map", "0:a", "-c:a", "copy"])
                oa += ["-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
                rc, err = ffrun(ins, fc, oa)
                if rc == 0:   # checked the moment it lands, so a fault costs one variant, not the whole set
                    dv, da = G.durations(out)
                    want = (sum(e - s0 for s0, e in ctx.segs) if r.get("remix") and ctx.segs else ctx.dur) / r.get("speed", 1.0)
                    if da is None or abs(da - dv) > 0.3 or abs(dv - want) > 0.5:
                        rc, err = 1, "sound %.1fs, picture %.1fs, expected %.1fs" % (da or 0, dv, want)
                if rc == 0: break
                if os.path.exists(out): os.remove(out)   # a failed render never stays in renders/
                if attempt == 1: say("  Rep%02d failed; deleted the output, rendering once more" % n)
            return n, r, (out if rc == 0 else None), err
        man_path = os.path.join(out_dir, "%s-repurpose.json" % ctx.name)
        if a.repair:   # the set on disk, as its manifest records it
            man = json.load(open(man_path)); done = []
            for k, e in sorted(man.items(), key=lambda kv: int(kv[0])):
                pth = os.path.join(out_dir, "%s-Rep%02d.mp4" % (ctx.name, int(k)))
                if os.path.exists(pth): done.append((int(k), dict(name=e["name"], _quip=e.get("quip"), _prof=e.get("prof")), pth))
        else:
            done = []
            with cf.ThreadPoolExecutor(a.jobs) as ex:
                for n, r, out, err in ex.map(full, numbered):
                    say("  Rep%02d %-22s %s" % (n, r["name"], "ok" if out else "FAILED " + err))
                    if out: done.append((n, r, out))
        if not a.only:
            # ---- repair: gate the real files; each variant that fails is replaced by the next
            # candidate that clears every real file with a margin, rendered on its own
            say("\nchecking the rendered set")
            real = {pth: G.sample(pth) for _, _, pth in done}
            keep, drop = [], []
            for n, r, pth in sorted(done, key=lambda x: x[0]):
                bad = G.best_match(real[pth], ref) < ORIG_MIN or any(G.best_match(real[pth], real[q]) < PAIR_MIN for _, _, q in keep)
                (drop if bad else keep).append((n, r, pth))
            taken_q = {r.get("_quip") for _, r, _ in keep} - {None}; taken_p = {r.get("_prof") for _, r, _ in keep} - {None}
            names = {r["name"] for _, r, _ in done}
            have = {n for n, _, _ in keep} | {n for n, _, _ in drop}
            slots = drop + [(n, None, None) for n in range(1, NEED + 1) if n not in have]   # a set short of NEED is filled up
            for n, r, pth in slots:
                if pth:
                    say("  Rep%02d %s fails the gate; replacing it" % (n, r["name"]))
                    dl = os.path.join(out_dir, "deletable"); os.makedirs(dl, exist_ok=True)
                    shutil.move(pth, os.path.join(dl, "%s-Rep%02d_%s.mp4" % (ctx.name, n, stamp)))
                else: say("  Rep%02d missing; adding one" % n)
                cands = [c for c in P if c["name"] not in names and c["name"] in S and c["name"] != "post"
                         and G.best_match(S[c["name"]], ref) >= ORIG_MIN + SEL_MARGIN
                         and all(G.best_match(S[c["name"]], real[q]) >= PAIR_MIN + SEL_MARGIN for _, _, q in keep)]
                cands.sort(key=lambda c: c["base"] not in bases)   # a base already rendered is quickest
                placed = False
                for c in cands:
                    if c.get("header"):
                        fq = [q for q in ctx.quips if q not in taken_q]
                        if not fq: continue
                        c["_quip"] = fq[0]; fp = [x for x in profs if x not in taken_p]
                        c["_head_png"] = os.path.join(tmp, "head-fix-%d.png" % n)
                        c["header"] = head_frame(ctx, c, c["_quip"], fp[0], c["_head_png"])
                        if c["header"] == "profile": c["_prof"] = fp[0]
                    if c["base"] not in bases:
                        bp = os.path.join(tmp, "base-%s.mp4" % c["base"]); say("  rendering base %s" % c["base"])
                        ok_, err = render_base(ctx, BASES[c["base"]], bp)
                        if not ok_: continue
                        bases[c["base"]] = bp
                    _, _, out, err = full((n, c))
                    if not out: continue
                    real[out] = G.sample(out)
                    if G.best_match(real[out], ref) >= ORIG_MIN and all(G.best_match(real[out], real[q]) >= PAIR_MIN for _, _, q in keep):
                        keep.append((n, c, out)); names.add(c["name"]); placed = True
                        if c.get("_quip"): taken_q.add(c["_quip"]); used_q.append(c["_quip"])
                        if c.get("_prof"): taken_p.add(c["_prof"]); used_p.append(c["_prof"])
                        say("  Rep%02d now %-20s %s" % (n, c["name"], recipe(c))); break
                    dl = os.path.join(out_dir, "deletable"); os.makedirs(dl, exist_ok=True)   # never deleted
                    shutil.move(out, os.path.join(dl, "%s-Rep%02d-%s_%s.mp4" % (ctx.name, n, c["name"], stamp)))
                if not placed: say("  Rep%02d: no candidate clears the gate; the set is one short" % n)
            done = sorted(keep, key=lambda x: x[0])
            json.dump({str(n): {"name": r["name"], "quip": r.get("_quip"), "prof": r.get("_prof")} for n, r, _ in done},
                      open(man_path, "w"), indent=1)
            if not a.repair: ctx.ledger.record(used_q, used_p)
            else: ctx.ledger.record([r.get("_quip") for _, r, _ in done if r.get("_quip")], [r.get("_prof") for _, r, _ in done if r.get("_prof")])
        outs = [pth for _, _, pth in done]
        say("\nduplicate gate on the rendered files:")
        sys.exit(subprocess.run([sys.executable, os.path.join(HERE, "diff_gate.py"), ctx.source] + outs).returncode)
    finally:
        retire_pages(ctx)
        if a.keep_temp: say("temp kept at %s" % tmp)
        else: shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
