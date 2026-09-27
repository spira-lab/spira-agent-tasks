---
name: stage-canvas-html
description: Set up the HTML stage canvas for a video animation, the rules for animating inside it, and how to export it. Fixed procedure. Use before building any video.
---

# Stage Canvas HTML

This is a fixed procedure. Follow it exactly. Do not improvise the harness;
creative decisions are not made here.

## 1. Start from the template

Every video is a copy of the template `stage/stage-9x16.html`. Where the
copy goes, what it is called, and where every file it uses lives are fixed
by the file-management skill; follow it for every path mentioned here.
Never edit the template in place. Never build a video from a blank file.

The template gives you:

- A **9:16 canvas** (`#stage`) at a fixed logical resolution of **1080 x 1920 px**.
  It is centered in the window and scaled to fit, with **black** around it,
  so the canvas edges are always visible.
- A **60 px strip** at the top reserved for the controls. The canvas never
  overlaps it, whatever the window shape.
- **Controls** at the top-left, outside the canvas: one `Play` / `Pause`
  toggle button, `Play from start`, and a timecode readout in seconds.
- **Guide toggles** next to the controls: `TikTok UI`, `Reels UI`, `Centre`
  (X and Y axes through the centre with 5% rulers), and `Thirds` (3 x 3
  division). They overlay the canvas for layout
  checks, stack independently, are off by default, and are never rendered.
  Both UI guides draw the same safe zone: x 70 to 1005 and y 230 to
  1255, then x 70 to 890 down to y 1615 where the icon column sits.
  Do not edit the guide markup or CSS.
- A **voice-over slot**: `<audio id="vo" src="materials/EDITABLE-NAME/vo.mp3">`
  at the top of the stage. Play, Pause, Play from start, and seek drive it
  in sync, and while playing the audio is the master clock. Set `src` to
  the VO file as the file-management skill places it, or delete the tag if
  the video has no VO.
- A **word readout** next to the timecode. If the video's `timings.json`
  (see step 2a) exists, the harness loads it and shows the word being
  spoken at the current time, while playing and after a seek. Use it to
  find where a component should land.
- A **background-music slot**: `<audio id="bgm" src="materials/EDITABLE-NAME/bgm.mp3"
  loop data-volume="0.14">` next to the VO. It follows play, pause, and seek,
  loops in the preview, and plays at the low `data-volume` for feel only;
  the render sets the real level. Delete the tag if there is no music.
- **Video clip support**: every `<video>` inside `#stage` follows the
  stage clock. Play, Pause, Play from start, and seek drive it, and the
  renderer seeks it frame by frame. See rule 11.
- A **timeline object** on `window.STAGE` with `play()`, `pause()`, `restart()`,
  `seek(ms)`, `onFrame(fn)`, `time`, `playing`, `timings`, `duration`,
  `width`, `height`.
- A **render mode**: opening the file with `?render` hides the controls and
  places the canvas at 1:1 in the top-left corner. The renderer uses this.

## 2a. Voice-over timings (do this as soon as the VO file exists)

Every timed element is placed against the spoken words, so produce the
word timestamps before designing any timing:

```bash
python3 <package>/tools/make-timings.py <path to vo.mp3>
```

This runs Whisper (`small.en`, word timestamps on) and writes
`timings.json` next to the audio, which is where the harness loads it from:

```json
{ "source": "vo.mp3", "duration": 39.14,
  "segments": [ { "start": 0.0, "end": 2.12, "text": "…" } ],
  "words":    [ { "w": "If", "s": 0.0, "e": 0.16 } ] }
```

Use `words[].s` as the `animation-delay` of anything that must appear as a
word is said, and `segments` to find sentence boundaries for scene changes.

**Set the video length.** The video ends exactly one second after the
last spoken word: put `data-duration` on `#stage`, in milliseconds, equal
to the last word's `e` from `timings.json` plus 1000. The harness stops
playback and holds the last frame there, and the renderer uses it as the
MP4 length. The last scene must be designed to hold on that frame; do not
add an exit to the final scene.
Whisper timestamps are accurate to roughly 50 ms; that is tighter than the
eye can tell. Re-run the script whenever the VO file changes.

## 2b. Text sweep

After building phrases, run this in the console. It seeks to each phrase
at the moment its last word has landed and reports safe-zone hits
(left < 70, top < 230, bottom > 1615, right > 1005, or right > 890 for
a phrase whose bottom is below y 1255) and lines holding a single
short non-key word. Fix every line it prints.

```js
(async () => { STAGE.pause(); const st=document.getElementById('stage').getBoundingClientRect(); const sc=st.width/1080; const res=[];
 for (const ph of document.querySelectorAll('.ph')) { const ws=[...ph.querySelectorAll('.w')]; if(!ws.length) continue;
  const t=Math.max(...ws.map(w=>parseFloat(w.style.animationDelay)))+0.5; STAGE.seek(t*1000); await new Promise(r=>setTimeout(r,120));
  if (parseFloat(getComputedStyle(ph).opacity)<0.5) continue; const b=ph.getBoundingClientRect(); const lines=[];
  ws.forEach(w=>{ const r=w.getBoundingClientRect(); const cy=(r.top+r.bottom)/2; let L=lines.find(l=>Math.abs(l.cy-cy)<r.height*0.6); if(!L){L={cy,words:[]}; lines.push(L);} L.words.push(w); });
  const lonely=lines.filter(l=>l.words.length===1&&!l.words[0].classList.contains('k')&&l.words[0].textContent.length<=9).map(l=>l.words[0].textContent);
  const left=Math.round((b.left-st.left)/sc), right=Math.round((b.right-st.left)/sc), bottom=Math.round((b.bottom-st.top)/sc), top=Math.round((b.top-st.top)/sc); const flags=[]; const rLim=bottom>1255?890:1005;
  if(left<70) flags.push('left '+left); if(right>rLim) flags.push('right '+right+' (limit '+rLim+')'); if(bottom>1615) flags.push('bottom '+bottom); if(top<230) flags.push('top '+top); if(lonely.length) flags.push('lonely: '+lonely.join('|'));
  if(flags.length) res.push(ph.closest('.scene').id+' '+ph.className+' @'+t.toFixed(1)+': '+flags.join(', ')); } console.log(res); })();
```

## 2. Where things go

- Video CSS goes in the `<style>` block **below** the comment
  `Video content styles go below`. Do not touch the harness CSS above it.
- Video markup goes **inside** `<div id="stage">`. Nothing visual goes
  outside it; anything outside the stage is not part of the video.
- Video JavaScript goes in a **new** `<script>` tag after the harness script.
  Do not edit the harness script.
- **Build the editable in stages, never in one write.** First the
  skeleton: scene containers, the audio tags, `data-duration`. Then one
  scene at a time, each as its own edit. A single write of the whole
  file takes minutes with nothing visible until it lands, and an
  interruption loses all of it; scene by scene, progress is on disk as
  it happens and an interruption loses one scene.
- **Write the editable by hand. Never build a helper that writes it.**
  No build script, no generator, no template filler that takes timings
  and emits the html. You are the generator: read `timings.json`, write
  the CSS and markup with the numbers in them. A helper costs the time
  to write it, then the time to run it, then the time to debug it, and
  it can stall at any step; editing the file directly costs only the
  edit. The judgement that writing it by hand is impractical is a human
  one, and it is wrong here.

## 3. Rules for animating inside the stage

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
7. **No autoplay.** The stage loads paused on the first frame. The user
   presses Play.
8. **No external network requests.** Fonts, images, and video files are
   local files referenced by relative path. The renderer runs offline.
9. **Do not use `animation-play-state` or `animation: none` in video CSS.**
   The harness owns those properties.
10. **Never put an entry and an exit animation of the same property on one
    element.** With `fill-mode: both`, the exit's backwards fill (for
    example `opacity: 1`) applies from t = 0 and wins over the entry's
    `opacity: 0`, so the element is visible before it should be. Put the
    entry on the container and the exit on an inner wrapper, or vice versa.
    Put every exit on the scene's container element (`#sN`), and every
    entry on the thing that enters; a container has no entry, so it never
    conflicts. After building a scene, run the leak audit below at 0.4 s
    before each scene's start and confirm it lists nothing.

```js
// Leak audit: paste in the console; lists visible elements of each scene
// just before that scene starts. Adjust the [id, startSeconds] list.
(async () => { STAGE.pause(); const st=document.getElementById('stage').getBoundingClientRect();
 const scenes=[['s1',0],['s2',7.2]]; const out={};
 for (const [id,start] of scenes) { const t=Math.max(0,start-0.4); STAGE.seek(t*1000); await new Promise(r=>setTimeout(r,250));
  const leaks=[]; document.querySelectorAll('#'+id+' *').forEach(el=>{ let o=1,e=el; while(e&&e.id!=='stage'){o*=parseFloat(getComputedStyle(e).opacity);e=e.parentElement;}
   const r=el.getBoundingClientRect(); if(o>0.05&&r.width>2&&r.height>2&&r.bottom>st.top&&r.top<st.bottom&&['IMG','P','SPAN','PATH'].includes(el.tagName)) leaks.push(el.tagName+'.'+el.getAttribute('class')); });
  out[id+'@'+t]=leaks.slice(0,8); } console.log(out); })();
```

11. **Video clips go in as `<video>` elements, never as frame sequences.**
    A talking-head cut-out (alpha WebM), footage, or any other clip is a
    `<video>` inside `#stage` with `muted playsinline preload="auto"` and
    `data-start="<ms>"`, the stage time at which the clip begins. The
    harness plays, pauses, and seeks it with the stage, and the renderer
    seeks it frame by frame, so write no sync script and extract no
    frames. Before its start the clip holds its first frame and after
    its end its last; put its entry and exit on a wrapper with CSS
    animations as for any element, so it is invisible outside its
    window. An alpha WebM keeps its transparency on the stage and in
    the render.

## 3a. First-frame audit

Before checking anything else, seek to 0 and look at the frame. Nothing
that belongs to a later moment may be visible: no stray line segment, no
glyph at the wrong scale, no image showing through a mask. The usual
causes are a `stroke-dasharray` shorter than its path, a second animation
on an element that did not get its own delay, and an entry/exit pair on
one element (rule 10). Fix them here; they are far cheaper to see on one
still than in a render.

## 4. Verify before handing over

Open the editable in a browser and check, in this order:

1. Black on the sides, 9:16 canvas centered, controls top-left outside the canvas.
2. The first frame is correct while paused (nothing has moved or faded in yet).
3. `Play` runs the whole piece to its end state, the VO plays with it, and the button reads `Pause` while playing.
4. `Pause` freezes everything, including anything JS-driven, and the button reads `Play` again.
5. `Play from start` restarts from the true first frame, including delayed elements.
6. `?render` shows the canvas at 1:1 with no controls and no guides.

Checking playback from a script is fine, but a synthetic `click()` carries
no user activation, so the browser blocks the audio and the elapsed clock
sits at 0 while `playing` is true. Mute the `<audio>` tags before driving
the controls from the console, or press the buttons by hand; a stuck clock
under script control is the block, not a harness bug.

## 5. Export to MP4

One command. `tools/` is in the package; the editable and the output
are in the root (see the file-management skill), so give the renderer
the package's tools path and the root's file paths:

```bash
node <package>/tools/render/render.js <root>/editable/<name>.html <root>/renders/<name>.mp4 30
```

Requirements on the machine: Node, ffmpeg, Google Chrome (or set
`CHROME_PATH` to another Chromium binary), and `npm install` run once in
the package's `tools/render`. Step 2a additionally needs `pip install openai-whisper`.

Arguments are the editable, the output path (both as the file-management
skill gives them), the frame rate, and optionally the worker count
(default 4). The renderer reads `data-duration`, the `#vo` source and the
`#bgm` source straight out of the editable, so there is nothing else to
configure.

What it does, in order: serves the editable's folder over a local port, opens
the page at `?render` in several headless Chrome instances, gives each a
slice of the timeline, captures every frame as JPEG, encodes each slice to
its own H.264 segment, concatenates the segments, then mixes the audio
(voice normalised to -16 LUFS, music bed built to length by
`tools/bgm-extend.py` and laid 20 LU under the voice, one second fade in
and 1.5 out) and trims to `data-duration`. Sound effects, when mixed,
sit between the two: about 8 LU under the voice, so clearly above the
bed and never over the words. WHEN the voice was made with ElevenLabs,
directly or through the Spira CLI, including speech that drives a
talking head, sound effects sit lower: about 14 LU under the voice.
ElevenLabs speech lands quieter against the effects at the same
setting, and at 8 LU they overpower it. Output is 1080 x 1920, 30 fps,
H.264, stereo AAC.

**Do not change these three settings.** They were measured on a 40-second,
1204-frame video and each one is the reason the render is fast:

- **JPEG frames, not PNG.** Encoding the screenshot is about two thirds of
  the entire cost: 305 ms per frame as PNG against 74 ms as JPEG. Quality
  92 is visually indistinguishable from PNG at full resolution, including
  on serif text and soft glows. The MP4 lands roughly 60 percent larger
  because compression noise gives the encoder extra detail to spend bits
  on; that is file size, not visible quality, and it does not matter for
  social delivery.
- **Four workers.** Four saturates a 12-core machine. Six, eight and ten
  all finish in the same wall time while per-frame cost rises, so extra
  workers only contend. Use fewer only on a smaller machine.
- **`process.exit(0)` at the end.** The local server holds Chrome's
  idle keep-alive sockets, so without the explicit exit the render
  finishes but the process hangs and every timing looks wrong.

Painting the page and seeking the timeline are not bottlenecks: seeking
costs about 14 ms a frame even with three hundred animations, and the
turbulence glow filter is not a meaningful factor. Do not spend effort
optimising either, and do not reach for GPU rasterisation flags.

Expected wall time is roughly 0.8 seconds per second of finished video, so
a 40-second video takes about 35 seconds and a 95-second video about 80.
If a render takes several minutes, something has regressed; check the
three settings above before anything else.

**After rendering**, confirm the file: duration matches `data-duration`,
frame count matches duration times frame rate, the audio stream is stereo,
and two or three frames pulled from the MP4 match the browser. Never ship
a render nobody has looked at.

**Then set the cover.** The cover is the still a player shows before the
video plays. It is stored inside the MP4 as its own image, beside the
video, so the first frame stays as it is and the hook keeps its motion.
The cover is the clearest poster frame within the video, never the first
frame: a moment where the key element is fully built, sharp, and
readable, nothing mid-transition, mid-fade, or half built.

1. Lay the whole video out as one sheet, one frame per second, six
   across. The tiles run left to right, top to bottom; tile n is the
   frame at n minus 1 seconds, so the first tile is the first frame and
   is never the pick.

   ```bash
   ffmpeg -y -i <root>/renders/<name>.mp4 -vf "fps=1,scale=216:-1,tile=6x<rows>" -frames:v 1 <materials>/deletable/cover-sheet.jpg
   ```

   where rows is the video's seconds divided by six, rounded up.

2. Look at the sheet, choose the clearest poster frame, and take it at
   full size from its second:

   ```bash
   ffmpeg -y -ss <seconds> -i <root>/renders/<name>.mp4 -frames:v 1 <materials>/deletable/cover.png
   ```

3. Embed it as the cover, without re-encoding the video:

   ```bash
   ffmpeg -y -i <root>/renders/<name>.mp4 -i <materials>/deletable/cover.png -map 0 -map 1 -c copy -c:v:1 png -disposition:v:1 attached_pic <root>/renders/<name>.cover.mp4
   mv <root>/renders/<name>.cover.mp4 <root>/renders/<name>.mp4
   ```

The sheet and the cover image are working files and stay in deletable;
every render gets its cover set again after it is made.

## 6. Other aspect ratios

Default is 9:16. If a different ratio is requested, change **only** these
three places, keeping the shorter side at 1080 px:

- In CSS: `#stage { width; height }`
- In JS: `STAGE_W`, `STAGE_H`
- In the `<title>` (cosmetic)

| Ratio | Width x Height |
|-------|----------------|
| 9:16  | 1080 x 1920    |
| 16:9  | 1920 x 1080    |
| 1:1   | 1080 x 1080    |
| 4:5   | 1080 x 1350    |
