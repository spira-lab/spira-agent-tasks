#!/usr/bin/env python3
"""Run a batch of Spira CLI jobs in parallel without shell loops (the approved tool list
refuses loops and variables). Every job is submitted first; only then is any waited on.

  python3 <shared>/tools/spira-jobs.py submit <model-id> <payload.json> [...]
      Submits one job per payload file (its content is the --inputs-json object) and
      writes <payload>.job with the job ID. Submits all before returning.
  python3 <shared>/tools/spira-jobs.py wait <ext> [--timeout 30m] <file.job> [...]
      Waits for each job, writes <file>.url with its first result URL, and downloads
      the result to <file>.<ext> (e.g. th-01.job -> th-01.url + th-01.mp4).
      Each wait gives up after 10m unless --timeout says otherwise: Wan jobs take
      --timeout 30m (the owner's rule, 2026-10-24).
  python3 <shared>/tools/spira-jobs.py cutout <file.url> [...]
      For each talking-head clip URL, writes a Pixelcut cut-out payload <file>-cut.json
      (mode Transparent) and submits it -> <file>-cut.job. Pixelcut returns no audio.
      Then: wait webm *-cut.job -> <file>-cut.webm. ("bria" is an old name for cutout;
      it also uses Pixelcut.)

Prints one line per job: <file> <job id or result>.
"""
import json, subprocess, sys, urllib.request
from pathlib import Path

def spira(*args):
    r = subprocess.run(["spira", "--json", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"spira {' '.join(args[:3])} failed: {(r.stderr or r.stdout).strip()[:400]}")
    return json.loads(r.stdout)

def job_id(d):
    return (d.get("ids") or {}).get("jobId") or d.get("id") or (d.get("data") or {}).get("id")

def submit(model, payloads):
    for p in map(Path, payloads):
        d = spira("ai", "jobs", "create", "--model-id", model, "--inputs-json", p.read_text())
        jid = job_id(d)
        if not jid: sys.exit(f"{p.name}: no job id in response")
        p.with_suffix(".job").write_text(jid + "\n")
        print(f"{p.with_suffix('.job').name} {jid}")

def wait(ext, jobs, timeout="10m"):
    for j in map(Path, jobs):
        d = spira("ai", "jobs", "wait", j.read_text().strip(), "--timeout", timeout)
        urls = d.get("resultUrls") or (d.get("data") or {}).get("resultUrls") or []
        if not urls: sys.exit(f"{j.name}: job finished with no result ({d.get('status')})")
        j.with_suffix(".url").write_text(urls[0] + "\n")
        out = j.with_suffix("." + ext.lstrip("."))
        req = urllib.request.Request(urls[0], headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})   # the CDN refuses Python's default (403)
        with urllib.request.urlopen(req, timeout=300) as r: out.write_bytes(r.read())
        print(f"{out.name} {urls[0]}")

def cutout(urlfiles):
    payloads = []
    for u in map(Path, urlfiles):
        p = u.with_name(u.stem + "-cut.json")
        p.write_text(json.dumps({"referenceVideo": [u.read_text().strip()], "mode": "Transparent"}))
        payloads.append(p)
    submit("pixelcut-video-background-removal", payloads)

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "submit": submit(a[1], a[2:])
    elif len(a) >= 5 and a[0] == "wait" and a[2] == "--timeout": wait(a[1], a[4:], a[3])
    elif len(a) >= 3 and a[0] == "wait": wait(a[1], a[2:])
    elif len(a) >= 2 and a[0] in ("cutout", "bria"): cutout(a[1:])
    else: sys.exit(__doc__)
