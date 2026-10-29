---
name: known-methods
description: Methods proven to work and methods proven to fail in the designers' shared materials, each with the reason and a pointer to where the working way is written. Read before building; never re-pay for a failure recorded here.
---

# Known Methods

Each entry is a failure that has already cost time or credits, and the
method that replaced it. The instruction itself lives in the skill or
tool the entry points to; this file holds the why. An entry is removed
once its lesson is fully absorbed and no longer needs explaining.

## Recording a corrected approach

WHEN a session takes an approach that turns out to be wrong, spirals on
it, and is only unstuck after the user debugs it, the fix is written into
this file before the session moves on, so the next session does not pay
for the same detour again. The user asks for it by name: "record the
right approach in known-methods.md". The entry is short and has three
parts:

- **Works:** the approach that turned out to be right.
- **Fails:** the approach taken first, and what it cost.
- **Where:** the skill and section that holds the instruction itself.

The why lives here; the instruction lives in the skill it points to. IF
the working way is not written anywhere yet, write it into the right
skill first, then point the entry at it.

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

## Gradient text and tight line-height

- **Works:** `background-clip: text` elements padded on all four sides
  (`padding: .3em .15em .3em; margin: -.3em -.15em -.3em;`) with a
  line-height of at least 1.2, and every letter and accent checked whole
  on a still. The owner noted cuts above the text too, not only below.
- **Fails:** gradient text at line-height 0.85-1.0. The gradient only
  covers the element's box, so descenders are cut flat ("Freezing" lost
  its g in Test 128 at 0:30; "agentic" and "highlight" in Test 49). The
  owner spotted it across many videos (20 editables, 2026-10-19).
- **Where:** stage-canvas-html, rule 12.

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
