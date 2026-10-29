#!/usr/bin/env bash
# Usage: render.sh slides.html outdir count ["1 3 5"]  -> outdir/slide-0N.jpg + outdir/contact.png
set -euo pipefail
HTML="$1"; OUT="$2"; N="$3"; ONLY="${4:-}"
CHROME="${CHROME_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
mkdir -p "$OUT"; ABS="$(cd "$(dirname "$HTML")" && pwd)/$(basename "$HTML")"
IDS=${ONLY:-$(seq 1 "$N")}
TMP="$(dirname "$ABS")/.render-tmp.html"
for i in $IDS; do
  # Isolate slide #s$i by convention (class="slide", id="sN"); the author's HTML needs no script or template.
  python3 - "$ABS" "$TMP" "$i" <<'PY'
import sys; src,dst,i=sys.argv[1],sys.argv[2],sys.argv[3]
h=open(src,encoding='utf-8').read()
inject=('<style id="__render">html,body{margin:0!important;padding:0!important;overflow:hidden!important;background:#000}'
        f'.slide:not(#s{i}){{display:none!important}} #s{i}{{position:fixed!important;left:0!important;top:0!important;margin:0!important;transform:none!important}}</style>')
h = h.replace('</head>', inject+'</head>',1) if '</head>' in h else inject+h
open(dst,'w',encoding='utf-8').write(h)
PY
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --window-size=1080,1350 --virtual-time-budget=8000 \
    --screenshot="$OUT/slide-$(printf %02d "$i").png" "file://$TMP" >/dev/null 2>&1
done
rm -f "$TMP"
python3 - "$OUT" "$N" <<'PY'
import sys, glob
from PIL import Image
out, n = sys.argv[1], int(sys.argv[2])
for f in sorted(glob.glob(f'{out}/slide-*.png')):
    Image.open(f).convert('RGB').save(f[:-4] + '.jpg', quality=92, subsampling=0)
    import os; os.remove(f)
fs = [f'{out}/slide-{i:02d}.jpg' for i in range(1, n + 1)]
W, H = 540, 675; cols = 4 if n > 4 else n; rows = (n + cols - 1) // cols
sheet = Image.new('RGB', (cols * (W + 10) + 10, rows * (H + 10) + 10), '#888')
for i, f in enumerate(fs):
    try: im = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
    except FileNotFoundError: continue
    sheet.paste(im, (10 + (i % cols) * (W + 10), 10 + (i // cols) * (H + 10)))
sheet.save(f'{out}/contact.png'); print('rendered', len(fs), 'slides ->', out)
PY
