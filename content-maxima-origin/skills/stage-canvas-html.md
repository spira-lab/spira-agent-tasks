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
  `TikTok UI` and `Reels UI` draw the app UI and the one safe zone
  (creative-video-production section 9); `Centre` and `Thirds` are
  optional aids for placing by eye.

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
- **Build the editable in stages, one scene at a time.** As many scenes
  as the video needs; there is no cap. Plan them before the first edit
  (time window, what each shows, which assets), reading each scene's
  background colour against the persona's outfit so the cut-out stays a
  figure on it (creative-video-production section 5). First the
  skeleton: scene containers, the audio and sfx tags, `data-duration`.
  Then one scene per edit, and check that scene (section 7) before the
  next one is written. A single write of the whole file takes minutes
  with nothing on disk, and an interruption loses all of it; scene by
  scene, an interruption loses one scene.
- **Write the editable by hand. Never build a helper that writes it.** No
  build script, generator, or template filler that takes timings and
  emits the html. You are the generator: read `timings.json`, write the
  CSS and markup with the numbers in them. A helper costs the time to
  write it, run it, and debug it, and can stall at each step. The one
  exception is the captions, which the package's own tool writes
  (section 6).
- **Type comes from the package's `fonts/` library.** Read
  `fonts/fonts.md` (the table of families, what each looks like, and the
  `@font-face` to write), pick the families the style calls for, copy
  their files into `materials/<name>/fonts/`, and declare them at the
  top of the video CSS. Nothing is fetched from the web (rule 8). The
  installed system fonts (`Noto Sans`, `DejaVu Sans`, ...) are fallbacks
  only, never the video's type; `Noto Color Emoji` is the emoji font. Do
  not list or inspect the system fonts. The audit flags a font that
  failed to load and a video whose text is all in system fonts.

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
12. **One person on screen, never a ghost.** Two copies of the presenter
    visible at once, at different sizes or places, read as a phantom.
    - When the scene before and the scene after both show the person, the
      change between them is a cut for the person: the outgoing scene's
      exit is a one-frame step on the incoming scene's first frame, never
      a fade, and the incoming scene shows its person at full opacity from
      that frame. The new look arrives with the new scene's background and
      elements, never with a fading person.
    - Every element that holds a clip hides, as a cut, at its clip's end
      (its `data-start` plus its length) or at its scene's end, whichever
      comes first. A clip holds its last frame after it ends, so nothing
      that is not hidden stays frozen behind the next shot.
    - Cover before you uncover: when the room goes away behind a cut-out,
      the new background is fully in before the full shot starts to fade;
      when the room comes back, the full shot is fully in before the
      background leaves. Time both from the same millisecond values.
13. **The cut-out sits exactly on the person.** A clip and its cut-out,
    when both are in a scene, go in one wrapper and both videos fill it the
    same way (`position: absolute; left: 0; top: 0; width: 100%; height:
    100%; object-fit: cover; object-position: 50% 50%`). Every size or
    position change, a zoom, a resize, a move, is an animation of that
    wrapper, never of one video inside it; the room shows or hides with the
    full shot's opacity alone. Then a resize into or out of the room never
    pulls the cut-out off the person.
14. **Gradient text gets room on all four sides.** `background-clip: text`
    paints the letters only inside the element's box, and tight headline
    leading makes that box smaller than the letters: the tails of g, j, p,
    q and y, tall capitals, accents and italic overhangs are cut flat.
    Every gradient-text element is an inline-block with padding on all
    four sides and the same negative margin, so the box grows and the
    layout does not move, and its parents never have `overflow: hidden`:

    ```css
    .grad { display: inline-block; padding: 0.25em 0.15em; margin: -0.25em -0.15em;
      background: <the gradient>; -webkit-background-clip: text; background-clip: text;
      color: transparent; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
    ```

## 5. Sound effects

Each cue is one tag inside `#stage`, next to the audio slots:

```html
<audio class="sfx" src="materials/<name>/sfx/03_whoosh.mp3" data-at="1600"></audio>
```

`data-at` is the stage millisecond the sound starts; put a whoosh's peak
on the cut it serves, not after it. Fetch each sound you use into
`materials/<name>/sfx/` first: `python3 tools/fetch-resource.py
sfx/<file> editable/materials/<name>/sfx/<file>` (the audio is hosted,
not in the package).

Every effect plays at the volume stored in its file. The library is
already levelled, one sound at a time, against a voice at −16 LUFS, the
level the renderer sets every voice-over to; the renderer adds no gain
to an effect. WHEN a sound feels too loud or too soft for a moment,
choose a different sound. A library
music bed is set 10 dB under the voice by the gain on its tag,
`data-gain-db`, which is the chosen entry's `gain_db`
(creative-video-production section 1): the renderer applies it as a
fixed gain and stops before the capture when it is missing or is not
that track's value. Never estimate, round, or change it, and never
scale or re-encode the bed. Generated music, which has no stored gain,
carries no `data-gain-db` and is levelled to -26 LUFS. Do not
pre-mix effects into
`vo.mp3`; the VO file stays the dry voice that the timings came from.

**Level adjustments, only when the request or a review comment asks for
one.** These optional attributes are the only way to change a level;
never a gain filter or a re-encoded file. The voice stays the loudest
sound.

| Attribute | On | Effect |
|---|---|---|
| `data-gain-db="-3"` | `#vo` | voice after its −16 LUFS levelling, −12 to +6 |
| `data-levelled` | `#vo` | the file is already levelled to −16 LUFS (an edit levels it before cutting it), so the renderer does not level it again; a voice made anew drops it |
| `data-gain-db="-6"` | an `audio.sfx` | that effect, −40 to +6 |
| `data-gain-offset-db="-4"` | `#bgm` | on top of its `data-gain-db` (kept as copied), −20 to +6 |
| `data-duck="1200-3400:-8,9000-12000:-6"` | `#bgm` | music lowered by dB in each ms range, 300 ms ramps, 0 to −30, no overlaps |
| `data-match-lufs="-27.7"` | `#bgm` | the bed as heard in this video (its stretch, ducking and fades) brought to this loudness before `data-gain-offset-db`, −60 to −5; set only when an edit swaps the bed for another kind, and kept on later renders |

`#bgm data-muted` silences the bed without removing its source. `#stage`
`data-sfx-offset-db` (-20 to +6) scales the whole sound-effects group after
individual cue levels; `data-sfx-muted` silences that group without removing cues.
These attributes are changed only on an explicit sound-level request. Group
levels are absolute, never cumulative. Rendering writes a `.mp4.audio` directory
beside the video with neutral-group FLAC stems and a version-bound manifest
(its `bgm.lufs` is the bed's loudness as heard, before the group level);
keep it with the render so Edit can audition the same mix.

The renderer stops on a value out of range.

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

## 7. Audit

**Check every scene as soon as it is written**, before the next one:

```bash
node tools/render/audit.js <root>/editable/<name>.html --at <entry>,<middle>,<before exit>
```

The three moments are the scene's own: its start, its middle, and just
before its exit (the last scene, which has no exit, uses its last
frame). Only those frames are shot, and leaks and text are checked only
within 0.5 s of them, so it takes seconds whatever the length of the
video. One run covers the checks a scene needs:

1. **Leaks**: nothing of the scene is visible before its entry.
2. **Text scan**: every text of the scene inside the safe zone,
   captions on one or two lines, no line holding a lone short word.
3. **First frame**: after the first scene, add `0` to the moments.
   Nothing that belongs to a later moment may be visible on frame 0: no
   stray line segment, no glyph at the wrong scale, no image showing
   through a mask.
4. **Looking at it**: open `materials/<name>/deletable/audit-sheet.jpg`
   with Read and look at every frame as a viewer would: the composition,
   nothing over the face, the cut-out sitting on the person, the text
   legible against what is behind it. This is the look in the browser;
   do not write a script to screenshot or inspect the page instead.

Fix what it found, run the same `--at` once more to confirm, then write
the next scene. When every scene is written, run the whole-video audit
before the render, and again after fixing what it found:

```bash
node tools/render/audit.js <root>/editable/<name>.html
```

The audit is the measurement of the layout: never work out beforehand
where a layer lands by probing the materials with ffmpeg or Python, or
by reading the audit's code. Each line it prints says what is wrong and
where.

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

Each line says how to fix it. Every run also writes
`materials/<name>/deletable/audit-sheet.jpg`: the `--at` moments, or for
the whole-video audit the first frame, each scene 0.6 s in, and the last
frame. Look at it every time; it is the check a render would otherwise
be spent on. The tool's output is the whole interface: do not read its
source.

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
