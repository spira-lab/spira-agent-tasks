#!/usr/bin/env bash
# Usage: scrape.sh <url> <outdir>   -> page.txt meta.json links.txt style.json
set -euo pipefail
URL="$1"; OUT="${2:-research}"; mkdir -p "$OUT"
CHROME="${CHROME_PATH:-/usr/bin/chromium}"
TMP="$OUT/dom.html"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
"$CHROME" --headless=new --disable-gpu --user-agent="$UA" --virtual-time-budget=10000 --dump-dom "$URL" > "$TMP" 2>/dev/null || true
if [ "$(wc -c < "$TMP")" -lt 20000 ]; then curl -sL -A "$UA" -H "Accept-Language: en-US,en;q=0.9" "$URL" -o "$TMP.curl" || true; [ "$(wc -c < "$TMP.curl" 2>/dev/null || echo 0)" -gt "$(wc -c < "$TMP")" ] && mv "$TMP.curl" "$TMP"; rm -f "$TMP.curl"; fi
python3 - "$TMP" "$OUT" "$URL" <<'PY'
import sys,re,json,html
from html.parser import HTMLParser
src,out,url=sys.argv[1],sys.argv[2],sys.argv[3]
raw=open(src,encoding='utf-8',errors='ignore').read()
meta={}
for m in re.finditer(r'<meta[^>]+>',raw,re.I):
    tag=m.group(0); n=re.search(r'(?:name|property)=["\']([^"\']+)',tag,re.I); c=re.search(r'content=["\']([^"\']*)',tag,re.I)
    if n and c: meta[n.group(1)]=html.unescape(c.group(1))
t=re.search(r'<title[^>]*>(.*?)</title>',raw,re.I|re.S); meta['title']=html.unescape(t.group(1).strip()) if t else ''
json.dump(meta,open(f'{out}/meta.json','w'),indent=1)
links=sorted(set(re.findall(r'href=["\'](https?://[^"\'#]+)',raw)))
open(f'{out}/links.txt','w').write('\n'.join(links))
class P(HTMLParser):
    skip=0; buf=[]
    def handle_starttag(self,t,a):
        if t in('script','style','noscript','svg'): self.skip+=1
        if t in('p','h1','h2','h3','h4','li','br','div','section','tr'): self.buf.append('\n')
    def handle_endtag(self,t):
        if t in('script','style','noscript','svg'): self.skip=max(0,self.skip-1)
    def handle_data(self,d):
        if not self.skip: self.buf.append(d)
p=P(); p.feed(raw); txt=''.join(p.buf); txt=re.sub(r'[ \t]+',' ',txt); txt=re.sub(r'\n\s*\n+','\n',txt).strip()
open(f'{out}/page.txt','w').write(txt)
# --- product image candidates ---
from urllib.parse import urljoin
cands=[]
for k in ('og:image','twitter:image','og:image:secure_url'):
    if meta.get(k): cands.append(meta[k])
for m in re.finditer(r'<img[^>]+>',raw,re.I):
    tag=m.group(0); src=re.search(r'(?:data-src|src|srcset)=["\']([^"\' ,]+)',tag,re.I)
    if not src: continue
    u=src.group(1); alt=(re.search(r'alt=["\']([^"\']*)',tag,re.I) or [None,''])[1]
    w=re.search(r'width=["\']?(\d+)',tag); h=re.search(r'height=["\']?(\d+)',tag)
    big=(w and int(w.group(1))>=400) or (h and int(h.group(1))>=400)
    hint=re.search(r'product|hero|device|app|screen|pack|bottle|box|shot|render|mockup',(u+' '+alt).lower())
    u=re.sub(r'\{width\}x?','1600x',u); u=re.sub(r'_\{width\}','_1600',u)
    if big or hint: cands.append(urljoin(url,u))
seen=[]; [seen.append(c) for c in cands if c not in seen and c.startswith('http') and not re.search(r'\.svg($|\?)|logo|icon|favicon|avatar|flag|sprite|pixel',c,re.I)]
def hint(u):
    ns=[int(n) for n in re.findall(r'(?<![\d.])(\d{3,4})(?:w|px|x\d{3,4})?(?![\d.])',u.split('?')[0])]; return max([n for n in ns if 200<=n<=6000] or [0])
og=[c for c in seen if c in cands[:3]]; rest=sorted([c for c in seen if c not in og],key=hint,reverse=True); seen=og+rest
open(f'{out}/images.txt','w').write('\n'.join(seen))
import urllib.request, os
os.makedirs(f'{out}/img',exist_ok=True); got=0
for i,u in enumerate(seen[:8]):
    try:
        ext=os.path.splitext(u.split('?')[0])[1] or '.jpg'
        req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36','Referer':url}); data=urllib.request.urlopen(req,timeout=20).read()
        if len(data)<2000: continue
        open(f'{out}/img/{i:02d}{ext}','wb').write(data); got+=1
    except Exception: pass
print(f'product image candidates: {len(seen)} listed, {got} downloaded to {out}/img/ (URLs in images.txt)')
colors=re.findall(r'#(?:[0-9a-fA-F]{6})\b',raw)
fonts=sorted(set(f.strip() for f in re.findall(r'font-family:\s*["\']?([^;"\',}]+)',raw,re.I) if not f.strip().startswith('var(')))[:20]
faces=sorted(set(re.findall(r'@font-face\s*\{[^}]*?font-family:\s*["\']?([^;"\'}]+)',raw,re.I|re.S)))
gfonts=sorted(set(re.findall(r'fonts\.googleapis\.com/css2?\?[^"\']*?family=([^&"\']+)',raw,re.I)))
# also pull external stylesheets (first 6) to find fonts declared there
css_links=re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)',raw,re.I)[:6]
import urllib.request
for href in css_links:
    try:
        cu=urljoin(url,href); req=urllib.request.Request(cu,headers={'User-Agent':'Mozilla/5.0'}); css=urllib.request.urlopen(req,timeout=15).read().decode('utf-8','ignore')
        fonts+= [f.strip() for f in re.findall(r'font-family:\s*["\']?([^;"\',}]+)',css,re.I) if not f.strip().startswith('var(')]
        faces+= re.findall(r'@font-face\s*\{[^}]*?font-family:\s*["\']?([^;"\'}]+)',css,re.I|re.S)
        colors+= re.findall(r'#(?:[0-9a-fA-F]{6})\b',css)
    except Exception: pass
fonts=sorted(set(fonts))[:30]; faces=sorted(set(f.strip() for f in faces))
from collections import Counter
top=[c for c,_ in Counter(x.lower() for x in colors).most_common(12)]
json.dump({'font_families':fonts,'font_faces':faces,'google_fonts':[g.replace('+',' ') for g in gfonts],'colors':top,'theme_color':meta.get('theme-color')},open(f'{out}/style.json','w'),indent=1)
print(f"{out}/page.txt {len(txt)} chars; {len(links)} links; theme {meta.get('theme-color')}")
PY
