"""Run one Spira image job and save the PNG + a sidecar JSON.

usage: python job.py <model-id> <out-path-without-ext> '<inputs-json>' [credits] [--no-wait-limit]

It submits without --wait, then polls the job. The CLI's own --wait gives up at 10 minutes, and a
retry after that creates a second paid job. Polling the same job ID never double-charges.
"""
import json, re, subprocess, sys, time, urllib.request
from spira_cli import spira_cmd

SPIRA = spira_cmd()
model, out, inputs = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
credits = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else None
LIMIT = 60 * 60  # give up polling after an hour; the job ID is saved so it can be picked up later


def run(args):
    r = subprocess.run(SPIRA + ["--json"] + args, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


rc, out_json = run(["ai", "jobs", "create", "--model-id", model, "--inputs-json", json.dumps(inputs)])
job_id = re.search(r'"(?:jobId|id)":\s*"([0-9a-f-]{36})"', out_json)
if rc != 0 or not job_id:
    sys.exit("submit failed: " + out_json[-400:])
job_id = job_id.group(1)
open(out + ".job.json", "w", encoding="utf-8").write(json.dumps({"jobId": job_id, "model": model, "inputs": inputs}))
print("job", job_id, flush=True)

start = time.time()
while True:
    rc, st = run(["ai", "jobs", "status", job_id])
    try:
        status = json.loads(st)["data"]["status"].upper()
    except Exception:
        status = "UNKNOWN"
    if status in ("SUCCEEDED", "COMPLETED", "SUCCESS", "DONE"):
        break
    if status in ("FAILED", "CANCELLED", "CANCELED"):
        sys.exit("job failed (failed jobs are not charged): " + st[-300:])
    if time.time() - start > LIMIT:
        sys.exit(f"still running after {LIMIT // 60} min. Pick it up later: spira ai jobs wait {job_id}")
    time.sleep(10)

urls = [u for u in re.findall(r'https://[^"\s]+?\.(?:png|jpg|jpeg|webp)(?:\?[^"\s]*)?', st) if "/uploads/" not in u]
ext = urls[0].split("?")[0].rsplit(".", 1)[-1]
req = urllib.request.Request(urls[0], headers={"User-Agent": "Mozilla/5.0"})  # the CDN 403s without it
open(f"{out}.{ext}", "wb").write(urllib.request.urlopen(req).read())
json.dump({"model": model, "provider": "spira-cli", "jobId": job_id, "inputs": inputs,
           "cost_credits_listed": credits, "source_url": urls[0],
           "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
          open(out + ".json", "w", encoding="utf-8"), indent=1)
print(f"{out}.{ext}\n{urls[0]}", flush=True)
