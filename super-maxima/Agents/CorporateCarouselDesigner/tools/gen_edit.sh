#!/usr/bin/env bash
# Product-referenced generation (GPT Image 2 image-to-image via Spira CLI).
# Usage: gen_edit.sh "<prompt>" <reference_image_url> <out.png> [size=1:1] [resolution=2K]
# reference_image_url must be a PUBLIC url (use the one from research/images.txt). Local files are not accepted by Spira.
# A local file is never sent to generation: use it in the layout as it is. The job is recorded by gen_image.sh.
set -euo pipefail
PROMPT="$1"; REF="$2"; OUT="$3"; SIZE="${4:-1:1}"; RES="${5:-2K}"
case "$REF" in http://*|https://*) ;; *) echo "reference must be a public http(s) URL"; exit 2;; esac
JSON=$(python3 -c 'import json,sys;print(json.dumps({"prompt":sys.argv[1],"size":sys.argv[2],"resolution":sys.argv[3],"referenceImage":[sys.argv[4]]}))' "$PROMPT" "$SIZE" "$RES" "$REF")
exec bash "$(dirname "$0")/gen_image.sh" "$JSON" "$OUT"
