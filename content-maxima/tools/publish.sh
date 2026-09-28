#!/usr/bin/env bash
# Publish the current render to the Social Post Assets library and record it in metadata.
#   tools/publish.sh <root>/renders/<name>.mp4 <tag name or id>
# The tag must already exist (the CLI cannot create one); run with no tag to list them.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [ $# -lt 2 ]; then spira social assets tags; exit 2; fi
render="$1"; tag="$2"
UPLOAD="$(spira --json social assets upload "$render" --tag "$tag" || true)" \
python3 - "$render" "$tag" "$here/meta.py" <<'PY'
import json, os, subprocess, sys
render, tag, meta = sys.argv[1:4]
raw = os.environ["UPLOAD"]
try:
    d = json.loads(raw[raw.find("{"):])
except ValueError:
    sys.exit(f"upload failed: {raw[-800:]}")
if d.get("status") != "success":
    sys.exit(f"upload failed: {json.dumps(d.get('error') or d)[:800]}")
asset = (d.get("data") or {}).get("asset") or {}
# tagName may come back as a per-locale object; the tag as given is what the operator knows
subprocess.run(["python3", meta, "publish", render, "--tag", tag,
                "--asset-id", asset["assetId"], "--url", asset["url"]], check=True)
print(f"published {os.path.basename(render)} under {tag}: {asset['assetId']} {asset['url']}")
PY
