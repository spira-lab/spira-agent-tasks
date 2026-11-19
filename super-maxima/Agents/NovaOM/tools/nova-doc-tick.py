"""Ticks to-do checkbox items in a Lark doc, as Nova's bot: python3 nova-doc-tick.py <doc url> <item number> [...]
An item is the checkbox whose text starts with "<n>. " (e.g. Angelica's Cookiy re-skit checklist)."""
import json, re, subprocess, sys, time
DOC = sys.argv[1]
def lark(*a, tries=3):
    for i in range(tries):
        r = subprocess.run(["lark-cli", "--profile", "super-nova", "docs", *a, "--as", "bot"], capture_output=True, text=True)
        out = r.stdout + r.stderr
        d = json.loads(out[out.index("{"):]) if "{" in out else {"error": out.strip()}
        if d.get("ok") or i == tries - 1:
            return d
        time.sleep(3)
d = lark("+fetch", "--doc", DOC, "--detail", "with-ids")
if not d.get("ok"):
    sys.exit(f"fetch failed: {d.get('error')}")
c = d["data"]["document"]["content"]
for n in sys.argv[2:]:
    m = re.search(r'<checkbox([^>]*)>\s*(%s\.\s.*?)</checkbox>' % re.escape(n), c, re.S)
    if not m: print(n, "not found"); continue
    attrs, inner = m.group(1), m.group(2)
    if 'done="true"' in attrs: print(n, "already ticked"); continue
    bid = re.search(r'id="([^"]+)"', attrs)
    if not bid: print(n, "no block id", attrs); continue
    r = lark("+update", "--doc", DOC, "--command", "block_replace", "--block-id", bid.group(1),
             "--content", '<checkbox done="true">%s</checkbox>' % inner)
    res = (r.get("data") or {})   # Lark can answer ok with result "failed" (e.g. no edit access)
    print(n, "ticked" if r.get("ok") and res.get("result") != "failed" else (res.get("warnings") or r.get("error")))
