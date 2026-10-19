---
name: edit-video-content-maxima
description: Edit a content-maxima video according to review comments, in its own editable, under content-maxima's rules; re-audit, render, host, report per comment. Read when edit-video-by-comment routes `content-maxima` here.
---

# Edit a content-maxima Video

The video is a content-maxima **editable** (HTML stage) rendered to MP4.
Edit that same editable with content-maxima's tools and rules. Nothing is
rebuilt and no new video is started.

- `<cm>`: the linked task directory ending in `/content-maxima`. IF none is
  listed or it does not exist: `report_error` (package not installed).
- `<video>`: file name of `source.video.path` without `.mp4` (`NN-name-MM-DD`).
- `<r>`: the part of `source.video.path` before `renders/`, empty in the
  standard layout (`7f3c2a91/renders/final.mp4` gives `7f3c2a91/`). Every
  path below carries it.

## 1. Rules of the directory

- Run every content-maxima command as one call from `<cm>`, absolute path
  each time: `cd "<cm>" && node tools/render/audit.js <r>editable/<video>.html --at 4200`.
- Package folders (`skills/`, `stage/`, `tools/`, `sfx/`, `music/`,
  `styles/`, `fonts/`) are read only.
- Touch only `<r>editable/<video>.html`, `<r>editable/materials/<video>/`,
  `<r>renders/<video>.mp4` and what the renderer moves to
  `<r>renders/deletable/`. Other editables may belong to a live run: never
  open or take from them.
- No `tools/new-video.sh`, new html, materials folder, name, concept,
  script, style, music or persona roll, unless a comment asks for that
  change.

Read in one turn before the first edit (they win where they apply; this
skill replaces what they say about making a new video):
`<cm>/skills/stage-canvas-html.md`, `<cm>/skills/file-management.md`,
`<cm>/skills/known-methods.md`, `<cm>/skills/creative-video-production.md`
sections 1, 7, 9; `<cm>/skills/toolkit.md` and `prompting.md` only WHEN a
comment needs new material.

## 2. Find the video

`<cm>/<r>renders/<video>.mp4`, `<cm>/<r>editable/<video>.html` and
`<cm>/<r>editable/materials/<video>/` must exist. IF the path has no
`renders/` or any is missing: `report_error` naming what was looked for.
Never pick a video by guessing (newest, only, similar name).

IF `source.videoChanged`: the comments describe an earlier render. Edit
the current editable, but confirm each comment on the first audit sheet
(section 4); one whose moment no longer shows what it describes is `not
fixed`, video changed after review. Never restore the old version.

Report `inspect` `started`.

## 3. Map comments onto the stage

Comments were written on the whole render placed from 0 s, so comment
time is stage time.

- Moment: `ms = round(time * 1000)`; never `frame` (render is 24 fps).
- Region: `null` = whole frame; else `x*W, y*H, width*W, height*H`, `W x H`
  the `#stage` size (1080 x 1920 unless made at another ratio,
  stage-canvas-html section 9). `regionPx` only WHEN `canvas` equals it.
- Ignore `targets`, `stale`, `madeAgainstVersion`.

Check: `durationSeconds` within 0.1 s of `data-duration`/1000 and `canvas`
the aspect of `#stage`. IF not, scale times by
`data-duration / (durationSeconds*1000)` and regions by aspect, confirm on
the audit sheet, and say so in the report. A moment past the end is
skipped and reported.

## 4. Look before editing

One audit with every comment's moment:
`cd "<cm>" && node tools/render/audit.js <r>editable/<video>.html --at <ms>,<ms>,...`
It writes `<r>editable/materials/<video>/deletable/audit-sheet.jpg`, what
the reviewer saw. Then find in the editable:

- the scene: `#s1`, `#s2`... stacked, later above; a scene ends at the
  delay of its exit animation on `#sN`;
- the element under the region, by absolute px position and size
  (stage-canvas-html section 4, rule 1) and `animation-delay`; a clip's own
  time is `ms - data-start`, an effect plays from `data-at`.

Decide every fix first, as one table, then build from it without
re-deciding:

| # | ms | scene | element | meaning | change | needs generation |
|---|----|-------|---------|---------|--------|------------------|

Report `inspect` `completed`, `edit` `started`.

## 5. By kind of change

Sort each fix-table row into one kind; section 6 rules apply to all.

- **Stage** (animation, timing, text, captions, layout, effects): html
  only, stage-canvas-html sections 3 to 6. No generation.
- **Visual material** (background, b-roll, element): generate per toolkit
  3d or 3c and prompting, in the video's look, and swap it in.
- **Presenter**: appearance is 3b on the base, then redo the clips that
  show it (3e, or 3j when the voice is given) and their cut-out (3f); a
  new presenter is 3a and every clip; a gesture redoes those clips (3e
  prompt, or 3h from a reference video); placement is html only.
- **Sound**: a new track per creative-video-production section 1; a
  volume or a lowered moment per stage-canvas-html section 5's
  attributes; new words or voice remake the speech by its source (3e,
  3j, 3i), then timings, captions and the scenes they move.
- **Whole video** (script, length, style, hook, ratio): still this
  editable; redo the scene table first, keep what the comment leaves.
- **Brand**: colours and type from `<cm>/skills/brands/<brand>.md` when
  the comment names that brand; a logo only from an image URL in the
  comment or that file, fetched into materials. Never draw one; without
  it the brand is its name in text.
- **Out of scope** (post caption, cover): skip, say so.

## 6. Fix rules

- Change only what a comment asks: no restyling, reordering, new colours,
  effects or music unless named. One scene's comment never "improves"
  another.
- Edit the html by hand in several small edits, never a rewriting script
  or one whole-file write (stage-canvas-html section 3).
- Timing lives in `animation-delay`, `data-start`, `data-at`, a scene's
  exit delay and `data-duration`; stage-canvas-html section 4 rules hold,
  rule 10 above all (exit on the scene or a wrapper, never beside the entry).
- Speech is word for word (creative-video-production section 1). WHEN a
  comment changes what is said: remake the voice by the route toolkit
  section 3 names, rerun `tools/make-timings.py` and `tools/captions.py`,
  reset `data-duration` (stage-canvas-html section 2), retime affected
  scenes, and flag it in the report as the costliest fix.
- Captions: restyle via `.cc-phrase` CSS after the marker block and
  regenerate with `tools/captions.py`; never edit inside the markers
  (stage-canvas-html section 6). A misspelt word follows the script.
- Hard rules beat comments (creative-video-production section 9: safe
  zone, grid, nothing over the face, levels): make the nearest allowed
  change and report it.
- Levels change only through stage-canvas-html section 5's attributes
  (`#vo`/sfx `data-gain-db`, `#bgm` `data-gain-offset-db`, `data-duck`),
  never a volume filter or re-encode; the bed's `data-gain-db` stays as
  copied and the voice stays loudest. Replace the bed only WHEN a comment
  asks for other music, chosen per creative-video-production section 1,
  its `gain_db` copied exactly.
- New material only WHEN a comment needs it, generated per toolkit
  section 1 with its models and prompting formats, matching the video's
  look. Payload and `.pending` go in `<cm>/<r>editable/materials/<video>/jobs/`.
  `wait_ai_job` saves only here, so `saveTo` is `work/<video>/<file>`;
  then `mv` it into the materials folder and delete the `.pending`. IF
  interrupted, wait on the ids in existing `.pending` records before
  submitting. The replaced file goes to that video's `deletable/`.
- A job input is a URL (toolkit section 2): a job's output by its
  `resultUrls[0]`; a file made or changed on disk (a re-paced clip, a
  converted voice-over) hosted with `host_file`. Never host any file
  with `spira assets upload`, which puts it in the user's own uploads;
  the new render is hosted with `host_file` too (section 7).
- A vague comment: take its most likely meaning from frame and region, do
  it, state the reading. One that cannot be done (contradicts another,
  impossible, past the end) is skipped with the reason; it never stops
  the rest.

## 7. Verify and render

1. Rerun the same `--at` audit; each asked change is visible at its moment
   and nothing else moved.
2. Whole-video audit per stage-canvas-html section 7, fix, run again.
   Report `edit` `completed`, `render` `started`.
3. Render once per stage-canvas-html section 8 to `<r>renders/<video>.mp4`
   (the previous render is kept in `<r>renders/deletable/`).
4. Host: `host_file` (`worker_tools`) with `path` the absolute
   `<cm>/<r>renders/<video>.mp4`; its `url` is the `publicUrl`.

## 8. Deliver

1. `cp "<cm>/<r>renders/<video>.mp4" results/<video>.mp4`.
2. `submit_result`: `video` = `results/<video>.mp4`, `publicUrl` = hosted
   URL, `report` = one line per comment in packet order, saying what
   changed and, WHEN something was generated, what and its credits:

   ```
   #3 00:04.12 fixed: headline moved up to y 420, clear of the face
   #4 00:06.00 fixed: new outfit; base edit + 3 clips regenerated (~60 credits)
   ```
3. Report `render` `completed`; end with the same lines and the URL.
