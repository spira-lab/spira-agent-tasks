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
- Span (`endTime` present): `endMs = round(endTime * 1000)`. A layer or
  sound the comment adds gets `data-start = ms` and lasts `endMs - ms`;
  a change to what is already there applies only between them.
- Region: `null` = whole frame; else `x*W, y*H, width*W, height*H`, `W x H`
  the `#stage` size (1080 x 1920 unless made at another ratio,
  stage-canvas-html section 9). `regionPx` only WHEN `canvas` equals it.
- Point: `x*W, y*H` on the same `#stage`; `pointPx` only WHEN `canvas`
  equals it. It marks the element there, not an area to fill.
- Ignore `targets`, `stale`, `madeAgainstVersion`.
- Attachments: each `attachments[].path` is relative to the **edit task**
  directory (the one whose `comments/` holds the JSON), not to `<cm>`.
  Copy it in before referencing it:
  `cp "<edit-task>/comments/media/<run>/<file>" "<cm>/<r>editable/materials/<video>/<sub>/"`
  (`<sub>`: `sfx/`, `img/`, `elements/` or `clips/`). Keep the JSON's file where it
  is. Never reference a path under `comments/` from the stage, and never
  treat `path` as a URL.

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
- the element under the region (or at the point), by absolute px position and size
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
- **Supplied material** (the comment's `attachments` hold an `image`,
  `animated` or `video` file): that file **is** the material, used exactly
  as supplied; `needs generation` is `no`. Never regenerate it, edit it
  with an image model, upscale, cut out, recolour, crop, filter or
  restyle it, or bring it "into the video's look". Only WHEN the
  comment's `text` asks for a change to the file itself (remove its
  background, make it black and white) do that one change, to a new
  file beside the original, and say so in the report. Placement and
  appearance per 5a.
- **Visual material** (background, b-roll, element) that a comment asks
  for **without supplying a file**: generate per toolkit 3d or 3c and
  prompting, in the video's look, and swap it in.
- **Presenter**: appearance is 3b on the base, then redo the clips that
  show it (3e, or 3j when the voice is given) and their cut-out (3f); a
  new presenter is 3a and every clip; a gesture redoes those clips (3e
  prompt, or 3h from a reference video); placement is html only.
- **Sound**: a new track per creative-video-production section 1; a
  volume or a lowered moment per stage-canvas-html section 5's
  attributes; new words or voice remake the speech by its source (3e,
  3j, 3i), then timings, captions and the scenes they move. A remade
  voice is not levelled yet: take `data-levelled` off `#vo`.
- **Whole video** (script, length, style, hook, ratio): still this
  editable; redo the scene table first, keep what the comment leaves.
- **Brand**: colours and type from `<cm>/skills/brands/<brand>.md` when
  the comment names that brand; a logo only from an image URL in the
  comment or that file, fetched into materials. Never draw one; without
  it the brand is its name in text.
- **Out of scope** (post caption, cover): skip, say so.

### 5a. A comment that carries a `selection`

WHEN a comment has `selection`, it is a choice the reviewer made in a
picker. Do what it says, in place of re-reading `text` for that part;
`text` still covers anything the selection does not. Each kind below is
otherwise an ordinary stage fix; one that names an attachment is
supplied material (section 5) and never goes to visual-material
generation.

- **`subtitle`** — `selection.style` holds `{behavior, font, size, color,
  highlightColor, top, textTransform?, outline?, background?, wordScale?}`.
  Run `tools/captions.py` with `--style <behavior> --top <top> --size
  <size> --color <color> --hl <highlightColor>`, then, after the marker
  block, set `.cc-phrase` to `font-family: '<font>'`, the
  `text-transform`, `-webkit-text-stroke: <outline>px rgba(0,0,0,.55)`
  (`0` when `outline` is absent), `background`/`padding`/`border-radius`
  when `background` is set, and `wordScale` as a larger `.w` font-size.
  Copy the font from `<cm>/fonts/` into the materials and declare it.
  Never edit inside the markers and never rewrite caption words; this
  comment changes the look only.
- **`audio`** — `role: 'sfx'` is a cue at the comment's moment:
  `<audio class="sfx" src="materials/<video>/sfx/<file>" data-at="<ms>"
  data-gain-db="<gainDb>">`, alongside the existing slots. `role: 'bed'`
  replaces the music bed (`#bgm`), and its `gainDb` is applied as that
  tag's `data-gain-offset-db`, never by re-encoding the file. The voice
  stays the loudest sound; the four level attributes of
  stage-canvas-html section 5 are the only way to change a level.
- **`image`** — its own absolutely positioned layer inside `#stage`,
  entering and leaving on CSS animations (stage-canvas-html section 4,
  rule 10).
- **`element`** — `element.kind` decides the markup:
  `text` writes a text layer with the given `font`, `size`, `color`;
  `shape` writes the inline SVG in the given `color`;
  `emoji` writes the glyph at the given `size`;
  `animated` is a `<video muted playsinline preload="auto"
  data-start="<ms>">` pointing at the copied `elements/` file, kept to
  `holdMs` when it is given and to the end when it is not.

**Where an image or element goes.** The reviewer placed it by hand, so
the comment's `region` (its `regionPx` on the stage, section 3) **is**
its box: put it exactly there, from the comment's moment. A picture or
an animated sticker fits inside the box at its own aspect, centred,
never stretched; text uses the box as its block (left/top/width from the
box, font size as given, shrunk only if the text would overflow it).
`anchor`/`scale` only describe the same box in words — use them only for
a comment without a `region`. A box in the face area or outside the safe
area (creative-video-production section 9) moves to the nearest allowed
spot, its size kept, reported as `partly`.

**How a supplied picture or sticker looks.** Exactly like its file:
- `<img>` or `<video>` sized to the box with `object-fit: contain`, the
  copied file as its `src`. It is not a frame-filling layer: when its
  aspect differs from the box or the frame, the margin stays empty and
  it is never switched to `cover`; an audit note that it falls short of
  an edge is reported, not "fixed".
- No `filter`, `backdrop-filter`, `mix-blend-mode`, `clip-path`, `mask`,
  `border-radius`, `border`, `box-shadow`, or resting `opacity` below 1
  on it or any wrapper around it.
- Entry and exit use only opacity, translate and uniform scale, on a
  wrapper, and rest at `opacity: 1; transform: none` while it shows.
- Nothing is layered over its box except the captions.

IF a selection cannot be honoured as written (its font is missing from
`<cm>/fonts/`, an attachment's file will not open, the anchor is outside
the safe area), make the nearest allowed change and report what you
changed instead — `partly`, naming it.

### 5b. A timeline edit (`selection.type: "timeline"`)

The reviewer cut the video by hand on a timeline; this comment is that
cut. Make the stage play exactly the timeline, **seamlessly**: nobody
watching may see or hear where it was cut. Do it last, after every other
comment (their times are pre-cut stage times).

**Read it.** `timeline` follows the video editor's model, all in
seconds: `elements[]` each `{id, type, source, start, length, startFrom,
volume, region?}` and `tracks[]` each `{kind, elementIds}`.
- `start`/`length`: where it plays on the **new** video. `startFrom`: the
  in-point in its source.
- `source.kind`: `base` = the stage as it is now (picture and its whole
  mix), the range `[startFrom, startFrom+length]` of stage time;
  `attachment` = `attachments[source.index]`, a clip (`video`) or a
  sound (`audio`); `detached` = the sound of clip `source.from`, on that
  clip's own timeline.
- `volume`: 1 = as it is, 0 = silent, up to 2. As a gain:
  `dB = 20*log10(volume)`, clamped to -40..+6.
- `main` track: the new video, end to end from 0; its end is the new
  `data-duration`. `overlay` track: clips over it in their `region`.
  `audio` track: sounds over it.
- There may be several `overlay` and several `audio` tracks. Nothing
  overlaps within one track. Overlay tracks stack in their order in
  `tracks[]`: a later one is drawn above an earlier one.
- Besides `video` and `audio`, an overlay track may hold:
  `type: "image"` (`{id, type, source: {kind: "attachment", index},
  start, length, region}`, an `image` attachment);
  `type: "graphic"` (`{id, type, graphic, start, length, region}`, where
  `graphic` is a `text`, `shape` or `emoji` exactly as in a section 5a
  `element`); and a `video` with `loop: true`, an animated sticker (its
  attachment is `animated`), silent, repeating its file for `length`.
  These have no `startFrom` and no `volume`.

**Plan it** as one table before touching anything, from the main track:
the new video is its elements back to back.

| new from–to | source | stage from–to (base) or file | volume | note |

`base` rows in source order; a range of stage time that no `base` row
covers is **cut**. IF `base` rows are out of source order or overlap,
report `partly` and keep source order.

0. **The voice keeps its level.** IF `#vo` has no `data-levelled` yet and
   this edit rewrites `materials/<video>/vo.mp3` (a cut or a splice), first
   level it once exactly as the renderer does: move it to
   `deletable/vo-original.mp3`, then `ffmpeg -i deletable/vo-original.mp3
   -af loudnorm=I=-16:TP=-1.5:LRA=7 -ar 48000 -b:a 320k vo.mp3`, and add
   `data-levelled` to `#vo`. Cut and join that file. A voice already
   marked is never levelled again: a shorter voice levelled again comes
   out at another level.
1. **Cuts.** For each cut range of stage time:
   - Snap each edge to the nearest gap between spoken words
     (`materials/<video>/timings.json`) within ±150 ms, else to a
     scene boundary within ±150 ms; never cut inside a word. Write the
     snapped edges in the table; report each shift over 40 ms.
   - Voice: move `materials/<video>/vo.mp3` to that folder's `deletable/`,
     then write the cut version back as `vo.mp3`: the range taken out
     with ffmpeg and the two sides joined by a 40 ms crossfade
     (`atrim` both sides + `acrossfade=d=0.04`). `#vo` keeps its src.
   - Script: drop the words that fall wholly inside the range from
     `materials/<video>/script.txt`, then rerun `tools/make-timings.py`
     on the new `vo.mp3` and `tools/captions.py` (stage-canvas-html
     section 2).
   - Stage: a scene, layer, `sfx` cue or clip wholly inside the range is
     removed; one that straddles it is trimmed to the side that stays.
     Every `animation-delay`, `data-start`, `data-at` and duck range after
     the range moves earlier by its length; then `data-duration` drops by
     it.
2. **A clip spliced into main** (an `attachment` row): at its `start`,
   the new video makes room for its `length`. Everything after it moves
   later by `length`; the voice-over gets that much silence there
   (ffmpeg `anullsrc` + concat, written back as `vo.mp3` the same way;
   `tools/make-timings.py` and `tools/captions.py` again). The clip fills the
   frame as its own scene:
   `<video muted playsinline preload="auto" data-start="<ms>">` on a
   file trimmed to `[startFrom, startFrom+length]` without sound
   (`ffmpeg -ss <startFrom> -t <length> -i <file> -an …` into
   `materials/<video>/clips/`), cover-fit to the stage. Trimming and this
   cover-fit are the only changes a spliced clip gets; otherwise it is
   supplied material (section 5), its picture never re-graded or
   regenerated.
3. **Overlay clips**: the same trimmed, silent file in a wrapper placed
   exactly at `region` (section 3 maps it to stage px, its own aspect,
   centred, never stretched), from `start` for `length`, then gone.
3b. **Stills, drawings and stickers on overlay tracks**: each is a layer
   placed exactly at its `region`, from `start` for `length`, then gone —
   made and styled as the section 5a `image` / `element` of the same
   kind (its box is `region`, never stretched). A `loop` sticker
   longer than its file is laid as back-to-back copies of
   `<video muted playsinline preload="auto" data-start="<ms>">`, the
   last one cut at the element's end. Stack the layers in track order
   (a later overlay track above an earlier one); captions stay above
   all of them. Report them on the same one line (`2 stills, 1 text,
   1 sticker over`).
4. **Sound of clips and the audio track.** Every clip whose `volume` > 0
   and every `audio` element is one cue:
   cut its sound to `[startFrom, startFrom+length]` with ffmpeg
   (`-vn -ss -t`, 30 ms fade in and out) into `materials/<video>/sfx/`,
   then `<audio class="sfx" src="…" data-at="<start ms>"
   data-gain-db="<dB>">`. A `detached` element cuts from its clip's file.
   `volume: 0` writes nothing; below 0.01 (-40 dB) use -40.
5. **Volume of a `base` row other than 1** (the stage's own mix in that
   range): there is no level for the whole mix. Lower the bed with one
   `#bgm data-duck` entry for that range (`dB` < 0 only), and set each
   `sfx` cue inside it to its gain plus `dB`. The voice is left as it is;
   report `partly` saying the voice keeps its level. A row above 1 can
   only be met on cues: report `partly`.
6. **Seams.** At every join on main (a cut, a spliced clip) the picture
   crossfades over 6–12 frames (CSS opacity on the scene wrappers, rule 10)
   unless the two sides are the same shot, where a clean cut is smoother.
   The music bed is **not** cut: the renderer lays it to the new length,
   so it runs straight through every join. No clip sound starts or stops
   without its 30 ms fade.
7. **Check.** `data-duration` = the main track's end within one frame
   (42 ms); audit at each join (`--at` 200 ms before and after) and see
   no jump, no doubled frame, no half word in captions.

Report it as **one** line: `#n fixed: cut at 0:06.2–0:09.0 (snapped
+60 ms), clip beach.mp4 2.0–7.0 s spliced at 0:06.2, 2 cuts, new length
0:22.0`, or `partly` with each shortfall named.

**Changes written on the cut's output.** A comment with a `cutAnchor`
was written while the cut was still a preview. Do it **after** this
section, and place it by its anchor, not by its `time`:
- `source.kind: "base"`, `seconds`: that second of the video as it was —
  find the main piece that plays it (it is a `base` row whose
  `[startFrom, startFrom+length]` holds `seconds`) and use
  `start + (seconds - startFrom)` on the new timeline.
- `source.kind: "clip"`, `elementId`, `offsetSeconds`: inside that
  spliced clip, `offsetSeconds` from its in-point, so it is inside the
  window that clip now occupies. Never place it outside that window: if
  the clip was cut away since (no such element), skip the comment and
  report it `not fixed, the clip it was written on is gone`.
- `end`, when present: place it the same way; the span runs between the
  two placed points.
Everything else about such a comment (its region, its `selection`, its
attachments) applies as usual.

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
- A comment is `fixed` only when the video does what it asked and nothing
  it did not. Anything the work or the renderer adds or moves that the
  comment did not ask for (a fade, a level, a sound laid on another slot)
  is a shortfall: `partly`, naming it.
- Hard rules beat comments (creative-video-production section 9: safe
  zone, grid, nothing over the face, levels): make the nearest allowed
  change and report it.
- Levels change only through stage-canvas-html section 5's attributes
  (`#vo`/sfx `data-gain-db`, `#bgm` `data-gain-offset-db`, `data-duck`),
  never a volume filter or re-encode; the bed's `data-gain-db` stays as
  copied and the voice stays loudest. The one exception is a timeline
  edit (5b): it levels the voice-over once (step 0), cuts and joins it and
  trims clip sounds with ffmpeg, but still sets every level by attribute. Replace the bed only WHEN a comment
  asks for other music, chosen per creative-video-production section 1,
  its `gain_db` copied exactly.
- New material only WHEN a comment needs it and supplies no file,
  generated per toolkit
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
   and nothing else moved. Each supplied image or sticker: its copy under
   `materials/` has the same `sha256sum` as its file under `comments/media/`
   (a spliced or overlay clip is trimmed, so it is checked by eye), its
   layer's `src` is that copy, and its CSS has none of what 5a forbids.
   Fix any miss before going on.
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
   changed and, WHEN something was generated, what and its credits; a
   supplied file is "used as supplied", or names the one change its
   comment asked for:

   ```
   #3 00:04.12 fixed: headline moved up to y 420, clear of the face
   #4 00:06.00 fixed: new outfit; base edit + 3 clips regenerated (~60 credits)
   #5 00:09.50 fixed: logo image placed top right, used as supplied
   ```
3. Report `render` `completed`; end with the same lines and the URL.
