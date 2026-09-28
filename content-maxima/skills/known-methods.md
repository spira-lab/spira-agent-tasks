---
name: known-methods
description: Methods proven to work and methods proven to fail in this package, each with the reason and a pointer to where the working way is written. Read before building; never re-pay for a failure recorded here.
---

# Known Methods

Each entry is a failure that has already cost time or credits, and the
method that replaced it. The instruction itself lives in the skill or
tool the entry points to; this file holds the why.

## Talking head on the stage

- **Works:** the alpha WebM cut-out placed as a `<video>` inside `#stage`
  with `data-start`. The harness drives it, and the renderer swaps in an
  all-keyframe copy so each frame costs one decode.
- **Fails:** extracting the clip to a frame sequence and stepping it
  with CSS: 775 frames, minutes of conversion, and a hand-written
  converter that hung for ten minutes. Also slow: the renderer seeking
  the original clip, which decodes from the last keyframe on every
  frame and took 120 s for a 29 s video against 48 s now.
- **Where:** stage-canvas-html, rule 11; `tools/render/render.js`.

## Writing the editable

- **Works:** skeleton first, then one scene per edit, written by hand
  from `timings.json`.
- **Fails:** the whole editable in one write (an 80 KB file takes minutes
  with nothing visible, and an interruption loses everything), and a
  generator script that emits the html (paid for three times: writing,
  running, fixing).
- **Where:** stage-canvas-html, section 3.

## Sound effects and the number of renders

- **Works:** `<audio class="sfx" data-at>` tags placed before the first
  render; the renderer mixes them. One render per video.
- **Fails:** rendering first, then mixing effects with a hand-written
  ffmpeg command and rendering again: two or three renders per video,
  two to four minutes each.
- **Where:** stage-canvas-html, section 5.

## Checking the stage

- **Works:** `tools/render/audit.js` after each scene; it prints every
  leak and text problem and writes a sheet of frames.
- **Fails:** writing a Playwright screenshot or leak script in every
  session, which costs the time to write and debug it each time.
- **Where:** stage-canvas-html, section 6.

## Music style

- **Works:** a `style` of genre, mood, tempo, and instruments only.
- **Fails:** a style naming the subject ("motorsport"): Suno rejects it
  as a producer tag, the CLI shows only `provider_error`, and blind
  retries fail the same way, minutes each.
- **Where:** toolkit, section 3g.

## Publishing a finished render

- **Works:** `tools/publish.sh` with no tag lists the tags; then publish
  under one that exists. IF none fits, leave the render unpublished and
  say so.
- **Fails:** uploading under a tag name of your own: the CLI cannot
  create tags and rejects it with `VALIDATION_FAILED`.
- **Where:** file-management, section 6.
