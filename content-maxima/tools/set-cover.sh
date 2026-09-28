#!/usr/bin/env bash
# Embed a frame of the render as its cover (attached picture), without re-encoding
# the video, so the first frame keeps its motion.
#   tools/set-cover.sh <root>/renders/<name>.mp4 <second>
# The still is kept as materials/<name>/deletable/cover.png.
set -euo pipefail
render="$1"; sec="$2"
[ -f "$render" ] || { echo "no render at $render" >&2; exit 1; }
name="$(basename "$render" .mp4)"
root="$(cd "$(dirname "$render")/.." && pwd)"
still="$root/editable/materials/$name/deletable/cover.png"
mkdir -p "$(dirname "$still")"
ffmpeg -v error -y -ss "$sec" -i "$render" -frames:v 1 "$still"
tmp="${render%.mp4}.cover.mp4"
ffmpeg -v error -y -i "$render" -i "$still" -map 0:v:0 -map 0:a? -map 1 -c copy -c:v:1 png -disposition:v:1 attached_pic "$tmp"
mv "$tmp" "$render"
echo "cover set from ${sec}s: $still"
