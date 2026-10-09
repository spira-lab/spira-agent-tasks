#!/usr/bin/env bash
# The copy of an image to look at, so a Read puts as few pixels in context as it can.
#   tools/view-image.sh <image> <materials>/<name>/deletable [--crop x,y,w,h]
# Prints the path to Read. An image whose long edge is 1024 px or less is printed as it
# is; a larger one is scaled to half its width and height, never below a 1024 px long
# edge, into <folder>/view/. --crop cuts a region of the source first (source pixels),
# then applies the same rule: the way to see small type or an edge at full resolution.
# The copy is for looking only. Everything the video uses (the editable, cut-sheet.py,
# an upload, a job's referenceImage) takes the original, never a file from view/.
set -euo pipefail
ratio=0.5; min_edge=1024
src="${1:?usage: tools/view-image.sh <image> <materials>/<name>/deletable [--crop x,y,w,h]}"
dir="${2:?usage: tools/view-image.sh <image> <materials>/<name>/deletable [--crop x,y,w,h]}"
crop=""
if [ "${3:-}" = "--crop" ]; then crop="${4:?--crop needs x,y,w,h}"; elif [ -n "${3:-}" ]; then
  echo "unknown argument: $3" >&2; exit 1
fi
[ -f "$src" ] || { echo "no such image: $src" >&2; exit 1; }

probe() { ffprobe -v error -select_streams v:0 -show_entries stream="$2" -of default=nw=1:nk=1 "$1" | tr -d '\r'; }
{ read -r w; read -r h; } < <(probe "$src" width,height)
pix="$(probe "$src" pix_fmt)"

filters=""; cw="$w"; ch="$h"; tag=""
if [ -n "$crop" ]; then
  [[ "$crop" =~ ^([0-9]+),([0-9]+),([0-9]+),([0-9]+)$ ]] || { echo "--crop is x,y,w,h in source pixels" >&2; exit 1; }
  cx="${BASH_REMATCH[1]}"; cy="${BASH_REMATCH[2]}"; cw="${BASH_REMATCH[3]}"; ch="${BASH_REMATCH[4]}"
  if [ "$cw" -eq 0 ] || [ "$ch" -eq 0 ] || [ $((cx + cw)) -gt "$w" ] || [ $((cy + ch)) -gt "$h" ]; then
    echo "--crop $crop is outside the ${w}x${h} image" >&2; exit 1
  fi
  filters="crop=$cw:$ch:$cx:$cy"; tag="_crop-$cx-$cy-$cw-$ch"
fi

long=$(( cw > ch ? cw : ch ))
if [ "$long" -le "$min_edge" ] && [ -z "$crop" ]; then
  echo "$src (${w}x${h}) - small enough, Read it as it is"
  exit 0
fi
if [ "$long" -gt "$min_edge" ]; then
  target=$(awk -v l="$long" -v r="$ratio" -v m="$min_edge" 'BEGIN { t = int(l * r + 0.5); print (t < m ? m : t) }')
  if [ "$cw" -ge "$ch" ]; then size="$target:-2"; else size="-2:$target"; fi
  filters="${filters:+$filters,}scale=$size:flags=lanczos"
fi

# Alpha survives only as PNG; everything else is a lightly compressed JPEG, so small
# type is not smeared by the compression on top of the scaling.
case "$pix" in
  rgba|bgra|argb|abgr|ya8|ya16*|yuva*|gbrap*|rgba64*|bgra64*|pal8) ext=png; quality=() ;;
  *) ext=jpg; quality=(-q:v 3) ;;
esac
stem="$(basename "$src")"; stem="${stem%.*}"
dest="$dir/view/$(basename "$(dirname "$src")")-$stem$tag.$ext"
mkdir -p "$dir/view"
if [ ! "$dest" -nt "$src" ]; then
  ffmpeg -v error -y -i "$src" -vf "$filters" -frames:v 1 "${quality[@]}" "$dest"
fi
{ read -r ow; read -r oh; } < <(probe "$dest" width,height)
echo "$dest (${ow}x${oh}; source ${w}x${h}${crop:+, crop $crop}) - for looking only; use $src"
