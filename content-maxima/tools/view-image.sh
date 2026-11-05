#!/usr/bin/env bash
# The copy of an image to look at, so a Read puts as few pixels in context as it can.
#   tools/view-image.sh <image> <materials>/<name>/deletable [--max <px>] [--crop x,y,w,h]
# Prints the path to Read. The image is scaled so its long edge is at most --max px
# (default 1024); an image already at or under that is printed as it is.
# --crop cuts a region of the source first (source pixels), then applies --max: the
# way to see small type or an edge at full resolution.
# A position or size seen on the copy is in the copy's pixels; recover the source
# value by multiplying by the `scale` the tool prints. Never measure the video's
# layout on a copy -- measure on the stage with `audit.js --at` (stage skill section 7).
# The copy is for looking only. Everything the video uses (the editable, cut-sheet.py,
# an upload, a job's referenceImage) takes the original, never a file from view/.
set -euo pipefail
max=1024
src=""; dir=""; crop=""
args=("$@")
i=0
while [ $i -lt ${#args[@]} ]; do
  case "${args[$i]}" in
    --max)  max="${args[$((i+1))]:?--max needs a pixel value}"; i=$((i+2));;
    --crop) crop="${args[$((i+1))]:?--crop needs x,y,w,h}"; i=$((i+2));;
    *)      if [ -z "$src" ]; then src="${args[$i]}"; elif [ -z "$dir" ]; then dir="${args[$i]}"; else
              echo "unknown argument: ${args[$i]}" >&2; exit 1
            fi; i=$((i+1));;
  esac
done
[ -n "$src" ] && [ -n "$dir" ] || { echo "usage: tools/view-image.sh <image> <materials>/<name>/deletable [--max <px>] [--crop x,y,w,h]" >&2; exit 1; }
[ -f "$src" ] || { echo "no such image: $src" >&2; exit 1; }
[[ "$max" =~ ^[0-9]+$ ]] || { echo "--max is a whole number of pixels" >&2; exit 1; }

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
if [ "$long" -le "$max" ] && [ -z "$crop" ]; then
  echo "$src (${w}x${h}) - small enough, Read it as it is (scale 1)"
  exit 0
fi
if [ "$long" -gt "$max" ]; then
  if [ "$cw" -ge "$ch" ]; then size="$max:-2"; else size="-2:$max"; fi
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
rel=$(awk -v o="$ow" -v oh="$oh" -v c="$cw" -v ch="$ch" 'BEGIN { printf "%.4f", ((c/o) + (ch/oh)) / 2 }')
echo "$dest (${ow}x${oh}; source ${w}x${h}${crop:+, crop $crop}; scale $rel, multiply a copy measurement by it to get source px) - look only, use $src"
