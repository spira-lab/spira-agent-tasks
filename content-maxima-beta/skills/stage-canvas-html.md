---
name: stage-canvas-html
description: Set up the HTML stage canvas for a video animation, the rules for animating inside it, the audit, the sound effects, and the render to MP4. Fixed procedure. Use before building any video.
---

# Stage Canvas HTML

This is a fixed procedure. Follow it exactly. Do not improvise the harness;
creative decisions are not made here.

## 1. Start from the template

Every video is a copy of `stage/stage-9x16.html`, made by
`tools/new-video.sh` (file-management section 4). Never edit the template
itself, and never build a video from a blank file. The copy gives you:

- A **9:16 canvas**, `<div id="stage">`, at a fixed **1080 x 1920 px**.
- A **voice-over slot**, `<audio id="vo">`, and a **music slot**,
  `<audio id="bgm">`. Delete a tag the video does not use.
- **Video clip support**: every `<video>` inside `#stage` follows the
  stage clock (rule 11).
- **Sound-effect support**: `<audio class="sfx">` tags play at their time
  in the preview and are mixed by the renderer (section 5).
- A **timeline object**, `window.STAGE`, with `play()`, `pause()`,
  `restart()`, `seek(ms)`, `onFrame(fn)`, `time`, `playing`, `timings`,
  `duration`, `width`, `height`. `onFrame(fn)` calls `fn(t)`, `t` being the
  stage time in milliseconds, on every frame while playing, on every
  `seek`, and on `restart`; the renderer seeks every frame it captures, so
  a JS-driven element that derives its state from `t` alone renders
  exactly as it previews (rule 6).
- Preview controls, guide overlays, and a word readout for the operator;
  `?render` hides them and places the canvas at 1:1. Do not edit them.
  The guides (`TikTok UI`, `Reels UI`, `Centre`, `Thirds`) draw the safe
  zone and the stage grid of creative-video-production section 9.

## 2. Voice-over timings (as soon as the VO file exists)

Every timed element is placed against the spoken words:

```bash
python3 tools/make-timings.py <materials>/<name>/vo.mp3
```

(`--from <clip> <clip> ...` builds `vo.mp3` from talking-head clips first:
toolkit 3e. `--recording <url or path>` builds it from the user's own
recording: toolkit 3j.)

This runs Whisper (`small`, multilingual, the language detected from the audio, word timestamps) and writes `timings.json`
next to the audio, where the harness loads it from:

```json
{ "source": "vo.mp3", "duration": 39.14,
  "segments": [ { "start": 0.0, "end": 2.12, "text": "…" } ],
  "words":    [ { "w": "If", "s": 0.0, "e": 0.16 } ] }
```

Use `words[].s` as the `animation-delay` of anything that appears as a
word is said, and `segments` to find sentence boundaries for scene
changes. Whisper timestamps are accurate to roughly 50 ms. Re-run it
whenever the VO file changes.

**Set the video length.** The video ends one second after the last
spoken word: `data-duration` on `#stage`, in milliseconds, is the last
word's `e` plus 1000. The harness holds the last frame there and the
renderer uses it as the MP4 length. The last scene holds on that frame;
it has no exit.

## 3. Where things go

- Video CSS goes in the `<style>` block **below** the comment
  `Video content styles go below`. Do not touch the harness CSS above it.
- Video markup goes **inside** `<div id="stage">`. Anything outside the
  stage is not part of the video.
- Video JavaScript goes in a **new** `<script>` tag after the harness
  script. Do not edit the harness script.
- Each scene is a container with the class `scene` and an id (`#s1`,
  `#s2`, ...); the audit finds scenes by it. Kinetic-type words are
  elements with the class `w` (a key word also `k`), each phrase in its
  own parent; the audit checks phrases by it. Captions are not written by
  hand: section 6.
- **Plan the scenes once, then build skeleton first, scenes in parallel.**
  A scene is one look that holds for a few seconds; the changes inside
  it (cards, words, zooms) carry the pace. A 30-second video has at most
  6 or 7 scenes, about one per sentence; more scenes are more to write
  and check, not a better video. Decide them all before the first edit,
  as one scene table (time window, what it shows, which assets), and
  build from it without re-deciding each scene as you reach it. Then
  write the skeleton in one edit and have the scenes written in parallel
  by subagents (section 3b). Never the whole file in one write: a very
  large write takes minutes with nothing on disk.
- **No session-built helper writes the editable.** No build script,
  generator, or template filler that takes timings and emits the html;
  a helper costs the time to write it, run it, and debug it, and can
  stall at each step. The package's own tools are the only other
  writers: `tools/captions.py` (section 6) and `tools/assemble-scenes.py`
  (section 3b). Everything else is written by hand from `timings.json`,
  with the numbers in the CSS and markup.
- **Do not read the stage template.** Section 1 is its interface; the
  copy is your editable, and reading 23 KB of harness only fills the
  context.
- **Type comes from the package's `fonts/` library.** Read
  `fonts/fonts.md` (the table of families, what each looks like, and the
  `@font-face` to write), pick the families the style calls for, copy
  their files into `materials/<name>/fonts/`, and declare them at the
  top of the video CSS. Nothing is fetched from the web (rule 8). The
  installed system fonts (`Noto Sans`, `DejaVu Sans`, ...) are fallbacks
  only, never the video's type; `Noto Color Emoji` is the emoji font. Do
  not list or inspect the system fonts. The audit flags a font that
  failed to load and a video whose text is all in system fonts.

## 3b. Scenes in parallel

Writing six scenes one after another is the longest stretch of a
session. The skeleton is yours; the scenes are written at the same time
by subagents, each from the same scene table, and one tool puts them in.

**1. The skeleton, in one edit**, once the scene table is final and the
timings exist. It is everything the scenes share, so they come out as
one video:

- In the video CSS: the `@font-face` declarations; the type system as
  classes (a headline class, an accent, a pill, a card, a caption face)
  with the reference's treatment; the palette as CSS variables on
  `#stage`, each background read against the persona's outfit so the
  cut-out stays a figure (creative-video-production section 5); the
  shared `@keyframes` the video will use (an entry, a pop,
  a slide, a wipe); each scene's **exit** on its container, `#sN { … }`
  (rule 10); and one marker pair per scene for its own rules:

  ```css
  /* scene:s1 */
  /* /scene:s1 */
  ```

- Inside `#stage`: the audio slots, the `.sfx` tags, `data-duration`,
  and one container per scene with its marker pair:

  ```html
  <section class="scene" id="s1"><!-- scene:s1 --><!-- /scene:s1 --></section>
  ```

Then run `tools/captions.py` (section 6) so the caption block exists and
its position is known.

**2. The scenes, in one turn.** Launch the subagents with the Agent
tool, all in the same turn, two or three adjacent scenes each, and wait
for them. Each brief carries what that subagent cannot see:

- Its rows of the scene table: time window, what the scene shows, the
  assets it uses as `materials/<name>/<file>` with their pixel size (for
  the persona cut-out, which sides are cropped), and the words spoken in
  its window with their `s` and `e` from `timings.json`, pasted in.
- The skeleton's vocabulary: the class names, the CSS variables, the
  shared `@keyframes`, and where the captions sit (`--top`), so nothing
  lands on them. It uses these and adds nothing that duplicates them.
- The rules: it reads `skills/stage-canvas-html.md` sections 3 and 4
  itself, and no other skill.
- What it writes: `materials/<name>/scenes/sN.html`, the markup that
  goes inside `#sN` (no `<script>`, no `<style>`, no exit animation: the
  container has it), and `materials/<name>/scenes/sN.css`, with every
  selector scoped to `#sN` and every scene-local `@keyframes` named
  `sN-…`. It never touches the editable, never references `deletable/`
  or `jobs/`, and never generates or fetches an asset: a missing one is
  reported, not made.
- Its reply: one line per scene, what it placed and any asset it could
  not use and why.

**3. Assemble**, once every subagent has replied:

```bash
python3 tools/assemble-scenes.py <root>/editable/<name>.html
```

It checks every fragment (markers present, no `<script>`, selectors
scoped, no `transition` / `vw` / `vh` / `animation: none`, files exist
and are not in `deletable/` or `jobs/`, no id used twice) and prints one
line per problem, writing nothing until all pass; then it puts each
fragment between its markers and moves `scenes/` to `deletable/scenes/`.
From here the editable is the only source: the audit's fixes (section 7)
are made in it directly, never by rewriting a fragment. A problem the
tool reports in a fragment is fixed in that fragment and the tool run
again; a scene the subagent could not finish is written by hand into
its markers.

Look at the first audit sheet for the join between scenes as much as
for each scene: the same type, the same palette, entries of one family.
A scene that looks like a different video is restyled with the
skeleton's classes, not left as its own.

## 4. Rules for animating inside the stage

These rules exist so Play, Pause, Play from start, and frame-by-frame
rendering all behave. Break them and playback or the MP4 will be wrong.

1. **All layout is in absolute pixels for a 1080 x 1920 canvas.** Position
   with `position: absolute` and px values. Never use `vw`, `vh`, `%` of the
   viewport, or media queries. The canvas is scaled as a whole; you design at 1:1.
2. **Use CSS animations (`@keyframes` + `animation`) for motion.** They are
   what the controls and the renderer drive.
3. **Every animation has `animation-fill-mode: both`.** Without it, elements
   snap to their base style before the delay starts and after the animation
   ends, and finished animations drop out of seeking.
4. **Sequence with `animation-delay`.** Time the whole video from t = 0 of
   the stage timeline. Do not chain animations with JavaScript timers.
5. **Do not use `transition` for timed motion.** Transitions cannot be paused,
   restarted, or seeked. Use `@keyframes`.
6. **Do not use `setTimeout`, `setInterval`, or `requestAnimationFrame` for
   timing.** If JavaScript must drive something (a counter, a canvas element),
   register it with `STAGE.onFrame(t => ...)` and derive its state from `t`
   in milliseconds. The state must be a pure function of `t`.
7. **No autoplay.** The stage loads paused on the first frame.
8. **No external network requests.** Fonts, images, and video files are
   local files referenced by relative path. The renderer runs offline.
9. **Do not use `animation-play-state` or `animation: none` in video CSS.**
   The harness owns those properties.
10. **Never put an entry and an exit animation of the same property on one
    element.** With `fill-mode: both`, the exit's backwards fill (for
    example `opacity: 1`) applies from t = 0 and wins over the entry's
    `opacity: 0`, so the element is visible before it should be. Put every
    exit on the scene's container (`#sN`) or a wrapper, and every entry on
    the thing that enters. The audit catches a violation as a leak.
11. **Video clips go in as `<video>` elements, never as frame sequences.**
    A talking-head cut-out (alpha WebM), footage, or any other clip is a
    `<video>` inside `#stage` with `muted playsinline preload="auto"` and
    `data-start="<ms>"`, the stage time at which the clip's own time is 0.
    The harness and the renderer drive it; write no sync script and
    extract no frames. Before its start the clip holds its first frame and
    after its end its last, so put its entry and exit on a wrapper with
    CSS animations, as for any element. An alpha WebM keeps its
    transparency on the stage and in the render.

## 5. Sound effects

Each cue is one tag inside `#stage`, next to the audio slots:

```html
<audio class="sfx" src="materials/<name>/sfx/03_whoosh.mp3" data-at="1600"></audio>
```

`data-at` is the stage millisecond the sound starts; put a whoosh's peak
on the cut it serves, not after it. The file is the one fetched into
`materials/<name>/sfx/` when the sound was chosen
(creative-video-production section 1).

Every effect plays at the volume stored in its file. The library is
already levelled, one sound at a time, against a voice at −16 LUFS, the
level the renderer sets every voice-over to; the renderer adds no gain
to an effect. Never set, scale, or calibrate an effect's volume: no
volume attribute, no gain filter, no re-encoded copy. WHEN a sound feels
too loud or too soft for a moment, choose a different sound. A library
music bed is set 10 dB under the voice by the gain on its tag,
`data-gain-db`, which is copied from the music pick's reply
(creative-video-production section 1): the renderer applies it as a
fixed gain and stops before the capture when it is missing or is not
that track's value. Never estimate, round, or change it, and never
scale or re-encode the bed. Generated music, which has no stored gain,
carries no `data-gain-db` and is levelled to -26 LUFS. Do not
pre-mix effects into
`vo.mp3`; the VO file stays the dry voice that the timings came from.

## 6. Captions

Word-per-word captions are mechanical, so a tool writes them:

```bash
python3 tools/captions.py <root>/editable/<name>.html [--style highlight|appear] [--top 1390] [--size 66] [--color #fff] [--hl #ffcf33]
```

It aligns the script with the timings, so every word carries the
script's spelling and Whisper's timing; splits the words into one-line
phrases where the sentence reads best; shrinks a phrase that is wider
than the 700 px caption block; and writes the markup and CSS between
`captions:start` / `captions:end` markers, centred on x 540. `highlight`
lights each word as it is spoken; `appear` brings each word in as it is
spoken (creative-video-production section 7 decides which). Run it once
the timings exist, and again whenever the VO or script changes.

Restyle with CSS after the marker block: `#captions` (the layer),
`.cc-phrase` (position, size, colour, font), `.cc-phrase .w` (a word), and
the `ccHl` keyframes (the highlight). The captions come out in no font of
their own: set `.cc-phrase` to the caption face of the video's type
system (creative-video-production section 5). Never edit inside the markers, never
write caption words by hand, and do not reuse the `cc-` names.

A caption **style chosen by the user** arrives with its own numbers
(behaviour, font, size, colour, highlight colour, top). The generator's
flags take behaviour/top/size/colours; everything else — the face, the
case, the outline, a box behind the phrase, a larger spoken word — is the
`.cc-phrase` / `.cc-phrase .w` CSS after the markers. Restyling never
changes which words appear when: that comes from the timings.

## 6b. Layers a change adds

An edit may bring its own files (a sound, a still, an animated sticker).
They must be copied into `materials/<name>/` first — the stage loads
nothing from the network (section 4, rule 8) and nothing from outside the
editable's own folder.

- **Image**: `<img>` in an absolutely positioned wrapper inside `#stage`,
  sized in stage pixels, entering and leaving on CSS animations
  (section 4, rule 10). Give it a wrapper if it needs both an entry and an
  exit, exactly like a scene element.
- **Animated sticker**: `<video muted playsinline preload="auto"
  data-start="<ms>" src="materials/<name>/elements/<file>">`. The harness
  and the renderer seek it; write no sync script and extract no frames
  (section 4, rule 11). WebM only: its transparency has to survive.
- **Extra sound**: a short cue is one more `<audio class="sfx" data-at>`
  (section 5). A different music bed replaces `#bgm`, with the library
  entry's own `data-gain-db` copied exactly, or a generated bed levelled
  by loudnorm. There is no fourth audio slot.
- **Text or emoji**: ordinary absolutely positioned text inside `#stage`
  — the same rules as any other type in the video (section 3).

These layers are content, not chrome: they live inside `#stage`, they do
not touch the harness CSS, and the audit must pass with them in place.

## 7. Audit

Run the whole-video audit twice: once when every scene is written, and
once after fixing what it found. Not after each scene: problems are
cheaper to fix together.

```bash
node tools/render/audit.js <root>/editable/<name>.html
```

To look at a stretch while building, add `--at` with the moments to see:
only those frames are shot, and only that stretch is checked, so it takes
seconds instead of a full pass. Use it instead of writing a script to
screenshot or inspect the page.

The audit is the measurement of the layout, so the layout is written
before it is measured. Where a cut-out, a headline or a layer lands on
the stage is checked by writing the scenes and running `--at` on them,
never worked out beforehand by probing the materials with ffmpeg or
Python, or by reading the audit's code: what it relies on is section 3,
and each line it prints says what is wrong and where.

```bash
node tools/render/audit.js <root>/editable/<name>.html --at 7400,8100,9000
```

It seeks the stage in the renderer's own view and prints `audit clean` or
one line per problem:

- `leak @t`: an element whose entry has not started is already visible
  (rule 10, a `stroke-dasharray` shorter than its path, a second
  animation without its own delay). Checked on the first frame and 0.4 s
  before each scene.
- `text @t`: a phrase or any other text (a headline, a pill, card copy)
  outside the safe zone, a caption over two lines, or a line holding a
  single short non-key word.
- `edge @t`: a frame-filling layer (a clip, a still, a painted
  background) that stops a sliver short of the canvas edge, or a cut-out
  whose cropped side ends inside the canvas.
- `font:` a font that failed to load, or text set only in system fonts.
- `cut-out:` talking-head clips on the stage with none of their cut-outs.
- `file:` a referenced file that is missing, or sits in `deletable/` or
  `jobs/`.
- `console:` a page error.
- `N video seeks timed out`: the Lambda was slow to decode a clip. It is
  not a problem in the editable: run the audit once more, and never
  remove, swap, or re-cut a clip because of it. IF it is still there,
  render anyway and say so in the final message.

The first audit of a video also prepares the all-keyframe copies of its
clips that the render uses (`intra: N encoded`), so it takes longer;
later audits and the render reuse them.

Each line says how to fix it; fix them all in as few edits as you can,
then run it the second time. It also writes
`materials/<name>/deletable/audit-sheet.jpg`: the first frame, each scene
0.6 s in, and the last frame, or the `--at` moments. Look at it on the
first run (this sheet is read as it is, never scaled: it is the check a
render would otherwise be spent on). The
tool's output is the whole interface: do not read its source.

## 8. Render

```bash
node tools/render/render.js <root>/editable/<name>.html <root>/renders/<name>.mp4
```

Arguments are the editable and the output; there is no frame-rate
argument. The renderer reads `data-duration`, `#vo` and `#bgm` (with its
`data-gain-db`), and the
`.sfx` tags from the editable; there is nothing else to configure. It
moves an existing render to `renders/deletable/` first, captures every
frame on AWS Lambda in parallel chunks, mixes the audio (voice at -16
LUFS, effects under it, bed 10 dB under it, faded in 1 s and out 1.5 s), checks
the file (duration, frame count, stereo). Output is 1080 x 1920 H.264
with stereo AAC at 24 fps, the rate of the Omni clips, so each output
frame is one clip frame. A clip at any other rate repeats or drops
frames on the stage, which shows as the presenter juddering; the
renderer names such a clip in a warning (toolkit section 3, Frame rate).
The render is final as it comes out, with no cover or other step after
it.

Expect about a minute for a video up to two minutes long. IF it prints `check FAILED` or `video seeks
timed out`, fix the cause before anything else. Render once, after the
audit is clean and the sound effects are placed: every re-render is
another minute of capture.

## 9. Other aspect ratios

Default is 9:16. For another ratio change only `#stage { width; height }`
in CSS, `STAGE_W`, `STAGE_H` in the harness JS, and the `<title>`,
keeping the shorter side at 1080 px: 16:9 is 1920 x 1080, 1:1 is
1080 x 1080, 4:5 is 1080 x 1350. The safe zone and caption rules are
9:16 rules; place key elements by eye for other ratios.
