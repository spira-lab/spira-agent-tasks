---
name: edit-video-super-maxima
description: Edit a super-maxima (Social Maxima 2.0) video according to review comments, in its own editable, under super-maxima's designer rules; check, render on this machine, host, report per comment. Read when edit-video-by-comment routes `super-maxima` here.
---

# Edit a super-maxima Video

The video is a super-maxima **editable** (HTML stage) rendered to MP4 on
this machine. Edit that same editable with super-maxima's own skills and
tools. Nothing is rebuilt and no new video is started; no designer, Atlas
or Nova is involved.

- `<sm>`: the linked task directory ending in `/super-maxima`. IF none is
  listed or it does not exist: `report_error` (package not installed).
- `source.video.path` is `Project/<Brand>/renders/<video>.mp4`, relative
  to `<sm>`. `<root>` is `<sm>/Project/<Brand>`; `<video>` is the file name
  without `.mp4` (`NN-name-MM-DD`).
- `<shared>` is `<sm>/Agents/DesignerShared`.

## 1. Rules of the directory

- Run every command as one call with absolute paths.
- `<sm>/Agents/` is read only.
- Touch only `<root>/editable/<video>.html`,
  `<root>/editable/materials/<video>/`, `<root>/renders/<video>.mp4`,
  `<root>/metadata/<video>.json` and what the renderer moves to
  `<root>/renders/deletable/`. Other videos of the brand may belong to a
  live run: never open or take from them.
- No new editable, materials folder, name, concept, script, style, music
  or persona, unless a comment asks for that change.
- **Jobs and hosting go through the worker tools, never the Spira CLI.**
  super-maxima's toolkit sections 1 and 2 (`spira ai jobs create`,
  `spira assets upload`) do not apply here: submit every generation with
  `submit_ai_job` and wait with `wait_ai_job`, host a local file with
  `host_file`. The toolkit's models, inputs and prompting formats still
  apply.

Read in one turn before the first edit (they win where they apply; this
skill replaces what they say about making a new video):
`<shared>/skills/stage-canvas-html.md`, `<shared>/skills/file-management.md`,
`<shared>/skills/rendering.md`, `<shared>/skills/known-methods.md`,
`<sm>/Agents/TalkingHeadEditedVideoDesigner/skills/talking-head-edited-video-designer.md`
sections 2, 7 and 9; `<shared>/skills/toolkit.md` and `prompting.md` only
WHEN a comment needs new material.

## 2. Find the video

`<root>/renders/<video>.mp4`, `<root>/editable/<video>.html` and
`<root>/editable/materials/<video>/` must exist. IF the path is not
`Project/<Brand>/renders/<video>.mp4` or any is missing: `report_error`
naming what was looked for. Never pick a video by guessing (newest, only,
similar name).

IF `source.videoChanged`: the comments describe an earlier render. Edit
the current editable, but confirm each comment on the first look
(section 4); one whose moment no longer shows what it describes is `not
fixed`, video changed after review. Never restore the old version.

Report `inspect` `started`.

## 3. Map comments onto the stage

Comments were written on the whole render placed from 0 s, so comment
time is stage time.

- Moment: `ms = round(time * 1000)`; never `frame`.
- Span (`endTime` present): the change applies only in `[ms, endMs)`;
  the original shows before `ms` and is restored at `endMs`. Never restyle
  base CSS for a bounded change; use a timed override or a duplicate
  shown only in the span.
- Region and point: `x*W, y*H, width*W, height*H` on `#stage` (1080 x
  1920 unless made at another ratio, stage-canvas-html section 6).
  `regionPx`/`pointPx` only WHEN `canvas` equals the stage.
- Ignore `targets`, `stale`, `madeAgainstVersion`.
- Attachments: each `attachments[].path` is relative to the **edit task**
  directory, not to `<sm>`. Copy it in before referencing it:
  `cp "<edit-task>/comments/media/<run>/<file>" "<root>/editable/materials/<video>/"`.
  Never reference a path under `comments/` from the stage, and never treat
  `path` as a URL.

Check `durationSeconds` against the stage duration and `canvas` against
the aspect of `#stage`; IF they differ, scale times and regions, and say
so in the report. A moment past the end is skipped and reported.

## 4. Look before editing

Copy the current editable to
`<root>/editable/materials/<video>/deletable/pre-edit.html`. Look at every
comment's moment (and each span's boundaries) by opening the editable at
`?render` in the local Chrome and seeking `window.STAGE.seek(ms)`; keep
those frames under `materials/<video>/deletable/`. Find the scene and the
element under each region or point.

Decide every fix first, as one table, then build from it:

| # | ms | scene | element | meaning | change | needs generation |
|---|----|-------|---------|---------|--------|------------------|

Report `inspect` `completed`, `edit` `started`.

## 5. Fix

The kinds of change, `selection`, supplied material, hand-placed regions
and timeline edits follow `skills/edit-video-content-maxima.md` sections
5, 5a, 5b and 6, read with these substitutions:

- `<cm>/<r>` is `<root>/`; content-maxima's `skills/` and `tools/` are
  `<shared>/skills/` and `<shared>/tools/`; the talking-head designer
  skill stands for content-maxima's `creative-video-production.md`.
- Section and rule numbers of `stage-canvas-html` are super-maxima's own.
- `tools/render/audit.js` does not exist here: look as in section 4.
- Timings: `<shared>/tools/make-timings.py`. Captions follow the
  talking-head designer skill section 7; never hand-edit generated
  caption words.
- Sound effects are `<audio class="sfx" data-at="<seconds>" src="…">`
  (rendering skill); levels are set only as the stage and rendering
  skills allow.
- A super-maxima `selection` field the content-maxima section names but
  this stage has no attribute for is made the nearest allowed way and
  reported `partly`.
- Payloads and `.pending` records go in
  `<root>/editable/materials/<video>/jobs/`; `wait_ai_job` saves under
  `work/<video>/`, then `mv` into the materials folder. Record each job's
  `prompt`, `url` and `credits` in `<root>/metadata/<video>.json` as the
  toolkit says.

## 6. Verify and render

1. Diff `pre-edit.html` against the editable: every changed line maps to
   a fix-table row; restore anything else. Look again at every comment's
   moment and span boundaries: the change shows where asked and nothing
   else moved. A supplied file's copy has the same `sha256sum` as its file
   under `comments/media/`.
2. Run stage-canvas-html sections 3a and 4. Report `edit` `completed`,
   `render` `started`.
3. Render once per the rendering skill:
   `node "<shared>/tools/render/render-fast.js" "<root>/editable/<video>.html" "<root>/renders/<video>.mp4" --cover <seconds>`,
   the cover moment from the metadata's render entry unless an edit moved
   it. `"ok": false`: fix the cause and run once more; a second failure is
   `report_error` with its `problems`.
4. Record the render in the metadata file. Host it: `host_file` with
   `path` the absolute `<root>/renders/<video>.mp4`; its `url` is the
   `publicUrl`.

## 7. Deliver

1. `cp "<root>/renders/<video>.mp4" results/<video>.mp4`.
2. `submit_result`: `video` = `results/<video>.mp4`, `publicUrl` = hosted
   URL, `report` = one line per comment in packet order, as
   `edit-video-content-maxima.md` section 8 shows.
3. Report `render` `completed`; end with the same lines and the URL.
