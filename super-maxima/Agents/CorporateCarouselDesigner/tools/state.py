#!/usr/bin/env python3
"""Run memory for the Corporate Carousel Designer (Agents/CorporateCarouselDesigner).
  state.py next-theme [--run ID] -> prints "dark" or "light"; claim is per run (ID defaults to cwd), repeat calls return the same theme
  state.py history [N]           -> prints the last N (default 30) runs, newest first, one per line
  state.py check --subject S --angle A --headline H
                                 -> exit 0 if novel, exit 3 if it repeats one of the last 30 runs
  state.py record --url U --theme T --subject S --angle A --headline H --story TEXT --slides N [--notes TEXT] [--run ID]
                                 -> appends to history (kept at 30) and writes last-run.json
State lives in Agents/CorporateCarouselDesigner/state/: history.json and last-run.json. Never edit by hand.
Up to 8 designers run at once: next-theme and record both hold the lock on state/.lock, so two
runs never claim the same theme or overwrite each other's record. Always pass --run <carousel folder>:
every designer in a batch works from the same folder (Project/), so the default would be shared."""
import sys, json, os, argparse, datetime, re, fcntl
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.normpath(os.path.join(HERE, '..', 'state'))   # Agents/CorporateCarouselDesigner/state
HIST = os.path.join(STATE, 'history.json'); LAST = os.path.join(STATE, 'last-run.json')
KEEP = 30
def load():
    os.makedirs(STATE, exist_ok=True)
    try: return json.load(open(HIST))
    except Exception: return []
def save(path, data, **kw):
    # write whole, then swap in, so a reader never sees half a file
    tmp = path + '.saving'
    with open(tmp, 'w') as f: json.dump(data, f, **kw)
    os.replace(tmp, path)
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()
def same(a, b):
    return norm(a['subject']) == norm(b['subject']) and norm(a['angle']) == norm(b['angle']) \
        or norm(a['headline']) == norm(b['headline'])
cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'
PEND = os.path.join(STATE, 'pending-themes.json')
if cmd == 'next-theme':
    # Claim a theme for THIS run (identified by --run, default: cwd). Repeated calls from the same run return the same theme.
    # Different concurrent runs alternate. A record for the run clears its claim.
    run = os.getcwd()
    if '--run' in sys.argv: run = sys.argv[sys.argv.index('--run') + 1]
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, '.lock'), 'w') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try: pend = json.load(open(PEND))
        except Exception: pend = []
        mine = [c for c in pend if c.get('run') == run]
        if mine: theme = mine[-1]['theme']
        else:
            try: last = json.load(open(LAST)).get('theme')
            except Exception: last = None
            if pend: last = pend[-1]['theme']
            theme = 'light' if last == 'dark' else 'dark'
            pend.append({'run': run, 'theme': theme}); save(PEND, pend[-16:])
    print(theme)
elif cmd == 'history':
    n = int(sys.argv[2]) if len(sys.argv) > 2 else KEEP
    h = load()[-n:][::-1]
    if not h: print('(no previous runs)')
    for r in h: print(f"{r['date']} | {r['theme']} | {r['subject']} | {r['angle']} | \"{r['headline']}\" | {r.get('slides','?')} slides | {r.get('story','')[:90]}")
elif cmd in ('check', 'record'):
    p = argparse.ArgumentParser(); p.add_argument('cmd')
    for k in ('url', 'theme', 'subject', 'angle', 'headline', 'story', 'notes', 'run'): p.add_argument('--' + k, default='')
    p.add_argument('--slides', default='')
    a = vars(p.parse_args())
    h = load(); cand = {'subject': a['subject'], 'angle': a['angle'], 'headline': a['headline']}
    dup = [r for r in h[-KEEP:] if same(cand, r)]
    if cmd == 'check':
        if dup:
            print('REPEAT of:', json.dumps(dup[-1], ensure_ascii=False)); sys.exit(3)
        print('novel'); sys.exit(0)
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, '.lock'), 'w') as lk:
        # the same lock as next-theme: concurrent designers record one at a time, each on the latest history
        fcntl.flock(lk, fcntl.LOCK_EX)
        h = load(); dup = [r for r in h[-KEEP:] if same(cand, r)]
        if dup: print('refusing to record a repeat; change subject/angle/headline first'); sys.exit(3)
        rec = {'date': datetime.date.today().isoformat(), **{k: a[k] for k in ('url', 'theme', 'subject', 'angle', 'headline', 'story', 'slides', 'notes')}}
        h.append(rec); h = h[-KEEP:]
        save(HIST, h, indent=1, ensure_ascii=False); save(LAST, rec, indent=1, ensure_ascii=False)
        try:
            run = os.getcwd()
            if '--run' in sys.argv: run = sys.argv[sys.argv.index('--run') + 1]
            pend = [c for c in json.load(open(PEND)) if c.get('run') != run]
            save(PEND, pend)
        except Exception: pass
    print('recorded; next theme will be', 'light' if a['theme'] == 'dark' else 'dark')
else:
    print(__doc__)
