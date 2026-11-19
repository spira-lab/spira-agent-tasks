#!/usr/bin/env bash
# Usage: gen_image.sh <inputs.json|'{json}'> <out.png> [model=gpt-image-2]
# inputs.json example: {"prompt":"...","size":"3:4","resolution":"4K"}
# Every job is kept: its jobId, model, resultUrl and its real cost, read from the job itself
# (`spira --json ai jobs status <jobId>` -> data.credits), never from the account balance.
# The record is appended as one JSON line to $CAROUSEL_JOBS (default: jobs.jsonl beside <out.png>)
# and printed as the last line: JOB {...}. A failed job is recorded too (it may have been billed).
# The Corporate Carousel Designer runs this through `tools/carousel.py gen-image`, which sets CAROUSEL_JOBS
# and copies the record into the carousel's metadata.
set -euo pipefail
IN="$1"; OUT="$2"; MODEL="${3:-gpt-image-2}"
if [ -f "$IN" ]; then JSON=$(cat "$IN"); else JSON="$IN"; fi
mkdir -p "$(dirname "$OUT")"
JOBS="${CAROUSEL_JOBS:-$(dirname "$OUT")/jobs.jsonl}"
RES=$(spira --json ai jobs create --model-id "$MODEL" --wait --wait-timeout 15m --inputs-json "$JSON" 2>&1) || true
python3 - "$RES" "$OUT" "$MODEL" "$JSON" "$JOBS" <<'PY'
import sys, json, re, subprocess, datetime, fcntl, os
res, out, model, inputs, jobs = sys.argv[1:6]

def parse(t):
    try: return json.loads(t)
    except Exception: pass
    m = re.search(r'\{.*\}', t or '', re.S)
    try: return json.loads(m.group(0)) if m else {}
    except Exception: return {}

def data_of(d): return d.get('data') if isinstance(d, dict) and isinstance(d.get('data'), dict) else {}

d = parse(res); dd = data_of(d)
jid = (d.get('ids') or {}).get('jobId') or dd.get('jobId') or dd.get('id') or d.get('id')
if not jid:
    m = re.search(r'"(?:jobId|id)"\s*:\s*"([^"]+)"', res or ''); jid = m.group(1) if m else None
le = dd.get('latestExecution') or {}
urls = le.get('resultUrls') or dd.get('resultUrls') or d.get('resultUrls') or []
if not urls and not d:
    urls = re.findall(r'https://[^"\s]+', res or '')[:1]
url = urls[0] if urls else None

# the job's own charge: spira --json ai jobs status <jobId> -> data.credits
credits, source = (None, 'missing') if jid else (0, 'no job was created')   # no job, no charge
if jid:
    r = subprocess.run(['spira', '--json', 'ai', 'jobs', 'status', jid], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    sd = data_of(parse(r.stdout))
    for k in ('credits', 'creditsCharged', 'chargedCredits', 'cost', 'creditCost'):
        v = sd.get(k)
        if isinstance(v, (int, float)): credits, source = float(v), 'job'; break
    if not url:
        sle = sd.get('latestExecution') or {}
        u2 = sle.get('resultUrls') or sd.get('resultUrls') or []
        url = u2[0] if u2 else None

ok = False
if url:
    r = subprocess.run(['curl', '-sL', url, '-o', out], capture_output=True, text=True)
    ok = r.returncode == 0 and os.path.isfile(out) and os.path.getsize(out) > 0
try: inp = json.loads(inputs)
except Exception: inp = inputs
rec = {'jobId': jid, 'model': model, 'resultUrl': url, 'credits': credits, 'credits_source': source,
       'file': os.path.abspath(out) if ok else None, 'status': 'succeeded' if ok else 'failed',
       'prompt': inp.get('prompt') if isinstance(inp, dict) else None, 'inputs': inp,
       'created': datetime.datetime.now().isoformat(timespec='seconds')}
os.makedirs(os.path.dirname(os.path.abspath(jobs)), exist_ok=True)
with open(jobs, 'a') as f:
    fcntl.flock(f, fcntl.LOCK_EX); f.write(json.dumps(rec, ensure_ascii=False) + '\n')
if not ok:
    print('generation failed:'); print('\n'.join((res or '').splitlines()[-5:]))
    print('JOB ' + json.dumps(rec, ensure_ascii=False)); sys.exit(1)
from PIL import Image
im = Image.open(out); print(out, im.size, im.mode)
print('JOB ' + json.dumps(rec, ensure_ascii=False))
PY
