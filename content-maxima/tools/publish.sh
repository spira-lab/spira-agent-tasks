#!/usr/bin/env bash
# Publish the current render to the Social Post Assets library.
#   tools/publish.sh <root>/renders/<name>.mp4 <tag name or id>
# The tag must already exist (the CLI cannot create one); run with no tag to list them.
# Prints the published asset's id and URL.
set -euo pipefail
if [ $# -lt 2 ]; then spira social assets tags; exit 2; fi
render="$1"; tag="$2"
UPLOAD="$(spira --json social assets upload "$render" --tag "$tag" || true)" \
python3 - "$render" "$tag" <<'PY'
import json, os, sys
render, tag = sys.argv[1:3]
raw = os.environ["UPLOAD"]
try:
    d = json.loads(raw[raw.find("{"):])
except ValueError:
    sys.exit(f"upload failed: {raw[-800:]}")
if d.get("status") != "success":
    sys.exit(f"upload failed: {json.dumps(d.get('error') or d)[:800]}")
asset = (d.get("data") or {}).get("asset") or {}
print(f"published {os.path.basename(render)} under {tag}\nasset: {asset['assetId']}\nurl: {asset['url']}")
PY
