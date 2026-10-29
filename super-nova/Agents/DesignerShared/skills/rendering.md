---
name: rendering
description: Render a finished editable into the final MP4 in one command, with its sound effects, cover, and output check. Use when the video is designed and has passed the stage skill's checks.
---

# Rendering

Rendering is one command. It does every step of the render itself and
checks its own output, so there is nothing to do around it: no extra
checks before, no frame pulls or probes after, no splitting it into
steps. Each extra step costs thinking time without making the video
better. Run it, read its one result line, move on.

## When

WHEN the editable is built and has passed the stage skill's first-frame
audit (3a) and its checks before hand-over (4), it is ready to render.
Only one render runs on the machine at a time; never start a second one
alongside.

## Before you run it

Settle the cover moment, from what you already know about the video.
It needs no file opened and no frame looked at.

- **The cover moment.** The cover is the still a player shows before the
  video plays. It is embedded in the MP4 as its own image, so the first
  frame stays as designed and the hook keeps its motion. Pick the
  clearest poster moment from your own timeline: a time where the key
  element is fully built, sharp, and readable, nothing mid-transition,
  mid-fade, or half built. Never 0, never the first frame.

## Sound effects in the editable

Each sound effect is one tag in the editable, with its file copied into
the video's materials folder:

```html
<audio class="sfx" data-at="<seconds>" src="materials/<name>/<file>.mp3"></audio>
```

`data-at` is the moment, in seconds on the stage timeline, the sound
starts. The renderer mixes every such tag into the final audio. Do not
mix effects into the voice file yourself.

## The command

```bash
node <shared>/tools/render/render-fast.js <root>/editable/<name>.html <root>/renders/<name>.mp4 --cover <seconds>
```

`<shared>` is the designers' shared folder, `Super Nova/Agents/DesignerShared`; `<root>` and `<name>` are
as the file-management skill gives them.

What it does, in order:

1. Moves an existing render of this video to `renders/deletable/`, with
   its time as a suffix.
2. Decodes every video clip in the editable once, into still frames.
3. Draws each frame in headless Chrome (software rendering), showing each clip's
   pre-decoded frame for that moment.
4. Encodes with libx264.
5. Mixes the audio: voice at -16 LUFS, music 20 LU under it (or as
   many LU as the bgm tag's `data-under` says) with a one-second fade in
   and 1.5 out, and every sound effect tag at its moment.
6. Embeds the frame at `--cover` as the cover.
7. Checks the file: frame count, length, stereo audio, cover.

Expect about one second of wall time per second of video; a 40-second
video takes about 45 seconds.

## The result

The command prints one line of JSON.

- **`"ok": true`** means the render passed its own checks. The video is
  done. Record the render in the metadata file as the file-management
  skill says, and continue. Do not re-open it, pull frames from it, or
  probe it again.
- **`"ok": false`** lists what failed in `problems`. Fix that cause and
  run the command once more. IF it fails a second time, stop and report
  the problems; do not keep retrying.

## What the machine needs

Node, ffmpeg, and Chromium at `/usr/bin/chromium` (or `CHROME_PATH` set to
another Chromium), with `npm install` run once in the shared folder's `tools/render`.
The render always encodes in software.

`tools/render/render.js`, the older renderer, stays in the shared folder
because other tools still call it. Productions use `render-fast.js`.
