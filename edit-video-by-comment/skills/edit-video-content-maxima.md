---
name: edit-video-content-maxima
description: Edit a video made by the content-maxima task according to review comments. Enters the operator's content-maxima directory, maps each comment onto that video's editable, fixes only what the comments ask under content-maxima's own rules, re-audits, renders, hosts, and reports per comment. Read when edit-video-by-comment routes a `content-maxima` review here.
---

# Edit a content-maxima Video

The video was made by the content-maxima task: an HTML stage, the
**editable**, rendered to MP4. It is edited where it was made, in the
same editable, with content-maxima's own tools and rules. Nothing is
rebuilt and no new video is started.

`<cm>` below is the content-maxima task directory. `<video>` is the
video's name, the file name of `source.video.path` without `.mp4`
(content-maxima names it `NN-name-MM-DD`). `<r>` is the part of
`source.video.path` before its `renders/` folder: empty in the standard
layout (`renders/<video>.mp4`), or a folder prefix ending in `/` (for
`7f3c2a91/renders/final.mp4`, `<r>` is `7f3c2a91/`). Every path of this
video in this skill carries `<r>`: `<r>editable/<video>.html`,
`<r>editable/materials/<video>/`, `<r>renders/<video>.mp4`.

## 1. Enter the content-maxima directory

`<cm>` is the linked task directory the file access rules list, the one
ending in `/content-maxima`. IF no such directory is listed or it does
not exist, call `report_error`: the content-maxima package is not
installed for this operator.

Run every content-maxima command from `<cm>`, where its `tools/` are,
with paths relative to it, as one Bash call that starts there:

```bash
cd "<cm>" && node tools/render/audit.js <r>editable/<video>.html --at 4200
```

Write the absolute path every time; never rely on an earlier `cd`, since
the shell's directory may be reset between calls. This is content-maxima's
own "run every command from the root" rule (its `skills/toolkit.md`
section 1), with `<cm>` as the root.

Inside `<cm>`:

- The package folders (`skills/`, `stage/`, `tools/`, `sfx/`, `music/`,
  `styles/`, `fonts/`) are read from, never written to.
- Only this video's files are touched: `<r>editable/<video>.html`,
  `<r>editable/materials/<video>/`, `<r>renders/<video>.mp4` and what the
  renderer moves into `<r>renders/deletable/`. Other editables belong to
  other videos, possibly to a content-maxima run working right now:
  never open, reuse, or take files from them.

Read these content-maxima skills before the first edit, in one turn;
every edit follows them, and where they describe making a new video this
skill replaces them:

- `<cm>/skills/stage-canvas-html.md`: the stage, the animation rules,
  sound effects, captions, the audit, the render;
- `<cm>/skills/file-management.md`: where files go and what happens to a
  replaced one;
- `<cm>/skills/toolkit.md` and `<cm>/skills/prompting.md`: only WHEN a
  comment needs new material;
- `<cm>/skills/known-methods.md`: failures already paid for;
- `<cm>/skills/creative-video-production.md`, for section 1 (the script
  and music rules), section 7 (captions) and section 9 (the hard rules).

What does not happen here: no `tools/new-video.sh`, no new html, no new
materials folder, no new name, no new concept or script, no new style,
music or persona roll. Those were decided when the video was made and
change only where a comment asks.

## 2. Find the video

`source.video.path` is the result video relative to `<cm>`: a
content-maxima render, `<r>renders/<video>.mp4`.

- The render must exist at `<cm>/<r>renders/<video>.mp4`, the editable at
  `<cm>/<r>editable/<video>.html`, and its materials at
  `<cm>/<r>editable/materials/<video>/`. IF the path has no `renders/`
  folder, or any of these does not exist, call `report_error` naming
  what was looked for. Never pick a video by guessing: the newest
  render, the only render, or a similar name is not the video the
  reviewer watched.
- **IF `source.videoChanged` is `true`**, the content-maxima task
  rendered again after the reviewer's draft was built: the comments are
  about an earlier version (`source.reviewedVideoUrl`) and the
  editable may have moved since. Edit the current editable anyway, but
  confirm every comment on the first audit sheet (section 4) before
  changing anything for it: a comment whose moment no longer shows what
  it describes is reported `not fixed`, saying the video changed after
  the review. Never edit to restore the reviewed version.
- Also copy the review JSON from `reviews/` into
  `<cm>/<r>editable/materials/<video>/reviews/<YYYYMMDD-HHMM>.json`, so
  the video keeps the record of what it was edited for. Nothing in that
  folder is referenced by the editable.

Report the `inspect` stage `started`.

## 3. Map each comment onto the stage

The comments were written on the finished render, placed whole from 0 s
in the video editor. So comment time is stage time, and a comment's
region is the same place on the stage.

For every comment:

- **Moment.** `ms = round(time * 1000)`. Use `time`, never `frame`: the
  render is 24 fps and the editor's fps need not be.
- **Region.** `null` means the whole frame. Otherwise, in stage pixels:
  `x * W`, `y * H`, `width * W`, `height * H`, with `W` and `H` the
  `#stage` size (1080 x 1920 unless the video was made at another ratio,
  stage-canvas-html section 9). Use `regionPx` directly only WHEN
  `canvas` equals the stage size.
- **Ignore** `targets`, `stale` and `madeAgainstVersion`: they describe
  the editor draft, not the editable.

Check that the packet is about this render before trusting the mapping:
`durationSeconds` within 0.1 s of the editable's `data-duration` / 1000,
and `canvas` with the same aspect ratio as `#stage`. IF either check
fails, the render was trimmed, padded or resized in the editor: scale
the times by `data-duration / (durationSeconds * 1000)` and the regions
by aspect, confirm each moment on the audit sheet (section 4), and say
in the report that the mapping was scaled. A comment whose moment is
past the end of the video is skipped and reported.

## 4. Look before editing

Before any edit, see what each comment points at, in one run with every
comment's moment:

```bash
cd "<cm>" && node tools/render/audit.js <r>editable/<video>.html --at <ms>,<ms>,...
```

It writes `<r>editable/materials/<video>/deletable/audit-sheet.jpg` with
the stage at exactly those moments, which is what the reviewer saw.
Read that sheet as it is.

Then find, in the editable, what is on screen at each moment:

- **The scene.** Scenes are `#s1`, `#s2`, ... stacked in order, each
  later one above the earlier. A scene's exit time is the delay of its
  exit animation on `#sN` (for example
  `animation: sceneOut 1ms linear 4780ms both` ends `#s2` at 4780 ms).
  The scene on screen at `ms` is the one whose window holds it.
- **The element.** Inside that scene, the element under the region,
  placed by its absolute px position and size (stage-canvas-html
  section 4, rule 1) and timed by its `animation-delay`. A clip's own time at `ms` is
  `ms - data-start`; a sound effect plays from `data-at`.

Decide every fix before the first edit, as one fix table:

| # | ms | scene | element | what the comment means | change | needs generation |
|---|----|-------|---------|------------------------|--------|------------------|

Build from the table without re-deciding each comment as you reach it,
the same discipline as content-maxima's scene table (stage-canvas-html
section 3). Report `inspect` `completed` and `edit` `started`.

## 5. Fix rules

- **Change only what a comment asks.** Everything else in the editable
  stays exactly as it is: no restyling, no new colours, no reordering
  scenes, no new sound effects or music unless a comment names them. A
  comment about one scene is never a reason to "improve" another.
- **Edit the editable by hand** (stage-canvas-html section 3): no script
  that rewrites the html; several small edits, never the whole file in
  one write.
- **Timing** is an element's `animation-delay`, a clip's `data-start`,
  an effect's `data-at`, a scene's exit delay on `#sN`, and
  `data-duration`. Every animation rule of stage-canvas-html section 4
  still holds, rule 10 above all: an exit goes on the scene or a
  wrapper, never beside the entry on one element.
- **The script is spoken word for word** (creative-video-production
  section 1). WHEN a comment asks to change what is said, the speech is
  remade by the route toolkit section 3 names for this video's voice,
  then `tools/make-timings.py` and `tools/captions.py` run again,
  `data-duration` is reset (stage-canvas-html section 2), and every
  scene timed against the changed words is retimed. Say so in the
  report: it is the most expensive kind of fix.
- **Captions** are restyled through `.cc-phrase` CSS after the marker
  block and regenerated with `tools/captions.py`, never edited inside
  the markers (stage-canvas-html section 6). A misspelt caption word is
  fixed in the script's spelling, never by re-recording.
- **The hard rules win over a comment** (creative-video-production
  section 9): the safe zone, the stage grid, nothing over the face, the
  levels. WHEN a comment asks for what a hard rule forbids (text pushed
  outside the safe zone, a card over the eyes), make the nearest change
  the rule allows and report what was done instead.
- **Levels are fixed** (stage-canvas-html section 5). WHEN a sound
  effect is too loud or too soft, choose a different sound; never set a
  volume. The music bed's `data-gain-db` is never changed: a comment
  that the music is too loud is reported as not fixable by level. The
  bed is replaced only WHEN a comment asks for different music, chosen
  as creative-video-production section 1 says, with the new entry's
  `gain_db` on the tag exactly as it reads.
- **New material only when a comment needs it** (a replaced image, a new
  b-roll still, a new element), generated as content-maxima's toolkit
  section 1 says, with the model and prompt format its toolkit and
  prompting skills give, matching the look already in the video. Two
  things differ because this task runs from its own directory:
  - The payload and the `.pending` record go where toolkit section 1
    puts them, in `<cm>/<r>editable/materials/<video>/jobs/`.
  - `wait_ai_job` saves only inside this task's directory, so its
    `saveTo` is `work/<video>/<out-file>`; once saved, `mv` the file to
    `<cm>/<r>editable/materials/<video>/<out-file>`, then delete the
    `.pending`. IF this task was interrupted, read those `.pending`
    records and wait on the ids they hold before submitting anything.
  - The file a new one replaces is `mv`'d to that video's `deletable/`
    (file-management section 5).
- **A vague comment is read, not asked about.** Take its most likely
  meaning given the frame and the region, do it, and state the reading
  in the report.
- **A comment that cannot be done** (it contradicts another comment, it
  needs something the package cannot make, its moment is past the end)
  is skipped and reported with the reason. One unfixable comment never
  stops the others.

## 6. Verify

1. Run the same `--at` audit again and compare the new sheet with the
   first, comment by comment: the change each one asked for is visible
   at its moment, and nothing else moved.
2. Run the whole-video audit as stage-canvas-html section 7 says (fix
   what it finds, then run it the second time). Report `edit`
   `completed`.
3. Report `render` `started`. Render once, exactly as stage-canvas-html
   section 8 says, with the output `<r>renders/<video>.mp4`. The renderer
   moves the previous render to `<r>renders/deletable/`, so the version the
   reviewer watched is kept.
4. Host the new render as file-management section 6 says:
   `cd "<cm>" && spira assets upload <r>renders/<video>.mp4`.

## 7. Deliver

1. Copy the new render into this task directory, so the console can
   serve it: `cp "<cm>/<r>renders/<video>.mp4" results/<video>.mp4`.
2. Call `submit_result` with `video` = `results/<video>.mp4`,
   `publicUrl` = the hosted URL, and `report` = one line per comment, in
   the packet's order:

   ```
   #3 00:04.12 fixed: headline moved up to y 420, clear of the face
   #4 00:07.03 partly: music bed kept at its level (fixed by the renderer); sfx 06_pop swapped for 02_tick
   #5 00:11.20 partly: asks for text at x 1040, outside the safe zone; set at x 960 instead
   #6 00:31.00 not fixed: moment is past the end of the video (29.4 s)
   ```

   Each line says what changed, not what is on screen.
3. Report `render` `completed`, and end with the same lines and the
   hosted URL as the final message.
