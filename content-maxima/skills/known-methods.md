---
name: known-methods
description: Methods proven to work and methods proven to fail in this package, each with the reason and a pointer to where the working way is written. Read before building; never re-pay for a failure recorded here.
---

# Known Methods

Each entry is a failure that has already cost time or credits, and the
method that replaced it. The instruction itself lives in the skill or
tool the entry points to; this file holds the why. An entry is removed
once its lesson is fully absorbed and no longer needs explaining.

## Talking head on the stage

- **Works:** the alpha WebM cut-out placed as a `<video>` inside `#stage`
  with `data-start`. The harness and the renderer drive it; the builder
  writes no sync script and extracts nothing. A build done this way
  was several times faster than the alternative.
- **Fails:** extracting the clip to a frame sequence and stepping it
  with CSS. A short video became 775 frames, minutes of conversion, and
  a hand-written converter that hung for ten minutes on a
  multiprocessing bug before anything was placed.
- **Where:** stage-canvas-html, rule 11.

## Writing the editable

- **Works:** skeleton first, then one scene per edit. Progress is on
  disk as it happens.
- **Fails:** the whole editable in a single write. An 80 KB file takes
  minutes to produce with nothing visible, and an interruption during
  it loses everything.
- **Where:** stage-canvas-html, section 2.

## Building the editable

- **Works:** editing the html directly. Read the timings, write the
  scene, move on.
- **Fails:** writing a helper script that generates the html from the
  timings. A session judged writing by hand impractical, built a
  generator instead, and paid three times: writing it, running it, and
  fixing it, with a stall possible at each. The judgement was a human
  reflex applied to an LLM, for which direct editing is the cheap path.
- **Where:** stage-canvas-html, section 2.

## Publishing a finished render

- **Works:** `spira social assets tags` first, then
  `spira social assets upload <file> --tag <id>` with a tag that already
  exists. IF none fits the video, the user creates it and the upload
  waits for that.
- **Fails:** calling upload with a tag name of your own invention,
  expecting it to be created. The CLI has no command that creates a tag;
  it rejects the name with `VALIDATION_FAILED`, and the whole hand-over
  stalls on a round trip to the user that listing the tags first would
  have avoided.
- **Where:** file-management, section 6.
