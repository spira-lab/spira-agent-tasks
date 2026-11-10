#!/usr/bin/env python3
"""Vega's source-length check (the owner's rule, 2026-11-03). Measures each clone / re-skit
source before its batch is built, and flags the long ones with a credit estimate, so the
requester can OK the cost or send a shorter cut.

    python3 "<max>/tools/vega-source-length.py" <link> [<link> ...]

Downloads a low-quality copy of each link to a temporary folder (yt-dlp, about 4 s each),
reads its length with ffprobe, deletes it, and prints ONE JSON line:
  {"limit_s": 30, "sources": [{"link", "seconds", "long", "estimate": "<lo>-<hi>"}], "any_long": bool}
`long` is true over 30 s. The estimate is seconds x 10-13 credits (Task 94: 61 s, 735;
Task 103: 50 s, 669). A link that can't be measured has "seconds": null and an "error".
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "DesignerShared" / "tools"))
import profile as scratch_profile  # noqa: E402,F401  (redirects tempfile to the scratch root)

LIMIT = 30
PER_S = (10, 13)

def measure(link):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(["yt-dlp", "-q", "--no-warnings", "--no-playlist", "-f", "worst[ext=mp4]/worst",
                            "-o", str(Path(d) / "s.%(ext)s"), link], capture_output=True, text=True, timeout=180)
        files = list(Path(d).glob("s.*"))
        if not files:
            return {"link": link, "seconds": None, "error": (r.stderr or "download failed").strip()[-200:]}
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(files[0])],
                           capture_output=True, text=True)
        s = round(float(p.stdout.strip()), 1)
        out = {"link": link, "seconds": s, "long": s > LIMIT}
        if s > LIMIT: out["estimate"] = f"{round(s * PER_S[0])}-{round(s * PER_S[1])}"
        return out

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    res = [measure(l) for l in sys.argv[1:]]
    print(json.dumps({"limit_s": LIMIT, "sources": res, "any_long": any(x.get("long") for x in res)}))
