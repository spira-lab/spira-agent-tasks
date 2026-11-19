"""Put carousel text on the slide photos and export final PNGs.

usage: python -I render_text.py <text.json>

text.json:
{
  "out_dir": "/Users/.../Super Nova/Project/<Brand>/carousels/<build>/slides",   # (Rey: D:/.../builds/<run>/slides)
  "name": "NO.<batch> - <Client> - <NN> <Title>",     # file name prefix
  "maker": "Rey", "version": 1,
  "width": 1080, "height": 1350,
  "style": "box" | "outline",                            # story captions | feed overlay text
  "slides": [
    {"id": "01", "image": "/Users/.../carousels/<build>/work/s01-graded.png",
     "main": "line one", "sub": "optional smaller line",
     "x": 50, "y": 12,            # anchor point in % of the frame
     "align": "center" | "left" | "right",
     "width": 80,                 # text box width in % of the frame
     "cta": true,                 # optional: main + sub in a rounded block of the brand color
     "pill": "1998",              # optional: a small brand-colour pill before the main line (then-vs-now years)
     "size": 46,                  # optional: main line font size in px (split slides use ~46 to stay on one line)
     "title": true}               # optional: main line in a dark rounded pill (then-vs-now slide 1)
    # A slide may instead hold "blocks": [ {main, sub, x, y, width, align, cta, pill, title}, ... ]
    # for split slides with one caption per half.
  "brand": "#22808D"                                     # the client's brand color (BRIEF.md Brand look), for "cta"
  ]
}
"""
import base64, html, json, os, sys
from playwright.sync_api import sync_playwright

spec = json.load(open(sys.argv[1], encoding="utf-8"))
W, H = spec["width"], spec["height"]
os.makedirs(spec["out_dir"], exist_ok=True)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@600;700;800&display=block');
html,body{margin:0;width:%(W)spx;height:%(H)spx;overflow:hidden;background:#000}
.bg{position:absolute;inset:0;width:100%%;height:100%%;object-fit:cover}
.t{position:absolute;font-family:'Inter Tight',Arial,sans-serif;color:#fff}
.outline .main{font-weight:800;font-size:64px;line-height:1.12;letter-spacing:-0.5px;
  -webkit-text-stroke:5px #000;paint-order:stroke fill;text-shadow:0 0 22px rgba(0,0,0,.55),0 3px 6px rgba(0,0,0,.5)}
.outline .sub{font-weight:700;font-size:42px;line-height:1.2;margin-top:12px;
  -webkit-text-stroke:3.5px #000;paint-order:stroke fill;text-shadow:0 0 18px rgba(0,0,0,.55),0 2px 5px rgba(0,0,0,.5)}
.box .main,.box .sub{display:inline;background:#000;color:#fff;font-weight:600;font-size:46px;
  line-height:1.42;padding:4px 14px;border-radius:12px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.box .sub{font-size:34px}
.box .gap{height:10px}
.cta{background:%(BRAND)s;border-radius:28px;padding:34px 40px;box-shadow:0 10px 40px rgba(0,0,0,.35)}
.cta .main{font-weight:800;font-size:60px;line-height:1.1;letter-spacing:-0.5px;color:#fff;-webkit-text-stroke:0;text-shadow:none}
.cta .sub{font-weight:600;font-size:38px;line-height:1.25;margin-top:14px;color:#fff;opacity:.95;-webkit-text-stroke:0;text-shadow:none}
.pill{display:inline-block;background:%(BRAND)s;color:#fff;font-weight:800;font-size:36px;line-height:1;
  padding:10px 18px;border-radius:999px;margin-right:14px;vertical-align:8px;-webkit-text-stroke:0;text-shadow:0 2px 8px rgba(0,0,0,.35)}
.title .main{display:inline-block;background:rgba(16,24,40,.88);border-radius:22px;padding:16px 28px;-webkit-text-stroke:0;text-shadow:none}
""" % {"W": W, "H": H, "BRAND": spec.get("brand", "#111")}

with sync_playwright() as p:
    try:
        b = p.chromium.launch(channel="msedge")   # Rey's Windows default; on the Mac it falls back to Playwright's Chromium
    except Exception:
        b = p.chromium.launch()  # needs: python -m playwright install chromium
    pg = b.new_page(viewport={"width": W, "height": H})
    def block(s):
        x, y, w, al = s.get("x", 50), s.get("y", 12), s.get("width", 80), s.get("align", "center")
        left = {"center": x - w / 2, "left": x, "right": x - w}[al]
        sub = f'<div class="gap"></div><span class="sub">{html.escape(s["sub"])}</span>' if (
            s.get("sub") and spec["style"] == "box") else (
            f'<div class="sub">{html.escape(s["sub"])}</div>' if s.get("sub") else "")
        pill = f'<span class="pill">{html.escape(s["pill"])}</span>' if s.get("pill") else ""
        main = (f'<span class="main">{html.escape(s["main"])}</span>' if spec["style"] == "box"
                else f'<div class="main"{" style=font-size:%dpx" % s["size"] if s.get("size") else ""}>{pill}{html.escape(s["main"])}</div>')
        cls = "t" + (" cta" if s.get("cta") else "") + (" title" if s.get("title") else "")
        return f"<div class='{cls}' style='left:{left}%;top:{y}%;width:{w}%;text-align:{al}'>{main}{sub}</div>"

    for s in spec["slides"]:
        doc = (f"<html><head><style>{CSS}</style></head><body class='{spec['style']}'>"
               f"<img class='bg' src='data:image/png;base64,{base64.b64encode(open(s['image'],'rb').read()).decode()}'>"
               + "".join(block(t) for t in (s.get("blocks") or [s])) +
               "</body></html>")
        pg.set_content(doc)
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        fn = (f"{spec['out_dir']}/{spec['name']} - Slide {s['id']} - "
              f"{spec.get('maker', 'Rey')} - v{spec.get('version', 1)}.png")
        pg.screenshot(path=fn)
        print("exported", fn, flush=True)
    b.close()
