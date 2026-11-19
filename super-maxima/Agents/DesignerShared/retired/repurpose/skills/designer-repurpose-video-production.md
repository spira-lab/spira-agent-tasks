---
name: designer-repurpose-video-production
description: A designer skill, shared by every Super Nova video designer. After a designer renders its original video, it turns that video into the number of organic repurposes the request asks for (up to twenty), each reading as a native post but not matching the original or each other as a duplicate. Free: nothing is generated.
---

# Repurpose Video Production

## 1. The task

This is **a designer skill**, shared by every video designer; it is not an
agent. Atlas never uses it: after a designer has rendered its original
video, Atlas only tells that designer to use it:

```
Read: <super>/Agents/DesignerShared/repurpose/skills/designer-repurpose-video-production.md and Create <N> of repurpose videos.
```

The designer, which already knows the video it just made, produces **N**
repurposed versions of it (up to twenty). With the original that makes
N + 1 posts. Repurposes are not projects and get no Task ID or Brand
number of their own: they carry the original's name with a Rep suffix.

Every version must pass two tests at once. To a viewer, it is an organic,
native post: full-bleed video, the same person, the same words, nothing
that looks like a template or a designed backdrop. To a duplicate
matcher, it is a different upload: far from the original and far from
every other version in the ways matchers compare video.

Nothing is generated. No image, clip, voice, music, or translation. The
cost of a repurpose is render time only.

## 2. Principles

**What a matcher sees.** Platforms compare perceptual hashes of frames
(the layout of light and dark, not the colours), audio fingerprints, and
timing. So the changes that count are changes of geometry, sound, and
time. Colour grades, filters, and textures move a frame hash by 0 to 2
bits out of 64: on their own they change nothing a matcher looks at.
That is why a set of recoloured, refiltered copies still reads as the
same video. Grade and texture are seasoning on top of real changes,
never the change itself.

**What moves the hash**, measured on a real source, in bits out of 64
(10 or fewer usually means the same image):

| Change | Bits |
|---|---|
| Colour grade, mono, filter | 0 to 2 |
| Tilt 2 degrees | 8 |
| Punch-in 1.12 | 10 |
| Blur frame (video inset on its own blurred copy) | 12 |
| Bold border | 18 |
| Punch-in 1.25 on the face | 24 |
| Mirror, whole frame | 32 |
| Mirror, video layers only | 18 to 22 |

Mild edits land close to each other as well as to the original. The
set only works when variants combine changes and no two share the same
geometry.

**Organic, not designed.** Every variant is the video itself, full-bleed
or framed the way creators frame their own posts: mirrored, punched in,
tilted like a hand-held phone, inset on a blurred copy, bordered, jump
cut, slightly faster. Never place the video on a designed backdrop,
behind masks, or in cards. The exceptions read as reposts: one
profile-and-quip post, and a header above every video placed low, so
no frame has an empty top.

**Mirror the picture, never the motion.** Only the persona's picture
flips. The layout, every card, and every word stay where they were, and
every animation keeps its direction: a layer that slides left still
slides left. Mirroring the finished MP4, or the whole stage, sends the
motion the wrong way and flips every word. So a mirrored variant is
built from the editable, with each video layer flipped in place.

**Keep the top; crop the bottom.** A talking head edited frame keeps its cards,
UI and graphics in the upper part, and the space below the captions is
mostly empty. So every zoom and every tilt pushes the image down: of what it
removes, about a quarter comes off the top and the rest off the bottom,
with the captions always whole in frame. A zoom crops the top slightly;
it never pins the top edge, and it is never anchored on the face or the
bottom, which throws away the visuals.

**Soft grounds.** Borders are soft two-stop washes, pastel or dusty,
never a solid saturated colour: a vibrant border overpowers the video.
The wash is chosen to stand off the picture on the cover and for most of
the running time.

**Quality holds.** Punch-ins stay at or under about 1.22, where upscaling
is invisible on a phone. Blur frames and borders scale the picture down.
Everything that the source's own renderer draws, text and graphics, is
redrawn crisp in the editable route rather than scaled.

**Adaptive, never tuned.** Every video is built differently, for its own
goal. Nothing here assumes a layout. The builder measures each source
first and every choice follows from those measurements.

## 3. The builder

`<repurpose>/tools/repurpose.py` does the whole job. Do not build
variants by hand: the tool holds the geometry, the text rule, the
quality caps, and the gate, and hand-built variants drift back into
templates.

What it measures on the source:

- **Caption rows**, from the word timings: it compares the change across
  each word start with the change over the same span inside the word.
  Captions change at word starts; motion changes all the time.
- **The source's cuts**, from ffmpeg's scene scores with a threshold set
  by that video.
- **The top of the moving subject in each scene**, so punch-ins keep the
  head in frame with room above it, and reframe at the source's own cuts
  where a jump is invisible.
- **The source's tone**, so borders and the post's ground stand off the
  picture.

What it builds from that:

- **Mirrored bases**, rendered from a copy of the editable through
  the designer's own renderer. Every `<video>` and `<canvas>` on the stage
  is flipped about its own centre, and nothing else is. A cutout and the
  background behind it flip together, so they stay aligned. It works on
  any video, whatever its markup.
- **Measured, not assumed.** An in-place flip moves the hash only as far
  as the video layers fill the frame. So during selection the builder
  renders each mirrored or zoomed base at 5 fps and hashes those frames.
  That adds about two minutes.
- **Caption faces.** In the editable, the text lines that sit in the
  measured caption rows are switched to a package face (DejaVu Sans,
  Serif, or Mono Bold). A line is never wider than the original caption
  was, because the original was made to fit its frame and its
  animation. Faces are dealt
  across the set, so some variants keep the original, others do not.
- **Geometry**: punch-ins of different strengths, each pushed down to keep
  the top and the caption rows whole; hand-held shake; off-centre
  holds, a gentle punch-in sitting left or right that keeps centred
  captions whole; tilts of up to 2.5 degrees in either direction,
  also pushed down; blur frames and
  wash borders with the video placed high, centred, or low in the frame;
  and combinations. Each geometry exists mirrored and straight.
- **Time and sound**: every variant runs 2 to 5 percent faster, some
  with the pitch nudged a couple of percent, one with jump cuts on the
  longest pauses (never in the hook).
- **Seasoning**: grade, halation, film plates from `filter/`, vignette.
- **One profile-and-quip post**: a profile from `fropile/`, a quip in
  the package font, the video through a rounded window.
- **Headers above low videos.** A video placed low never leaves the top
  empty. The space above it holds one of two headers:
  - **Profile and quip**, like a post. Used only where there are at
    least 250 px of room.
  - **The quip alone**, bold and centred, like a caption.

  The headers sit below the platform's top bar. On a border the ink is
  dark; on a blur frame it follows the picture's tone, and white text
  gets a soft shadow.
- **Nothing repeats.** Every quip and every profile is used once in a
  set. A ledger in the source's `renders/` folder,
  `.repurpose-ledger.json`, remembers what earlier videos used. Profiles
  another video used go to the back of the line, and a quip another
  video used is refused. The ledger is written only after a full render,
  so a preview and its render match.

Then it previews every candidate, and **the duplicate gate** keeps the
N (`--count`, at most twenty) that are at least 16 bits from the original and 12 bits from
every other kept variant. It caps repeated devices, at most eight blur
frames and seven borders, so no single look dominates.

Keeping the top narrows the field: top-anchored zooms and tilts sit
close together in hash space, so the variety comes mostly from where an
inset sits and how big it is. Some videos yield fewer than asked for; the
builder says so, and `--dry-run` shows the count in seconds before
anything renders. After the full render, the gate runs again on the finished
files.

## 4. The run

`<super>` is the Super Nova folder; `<repurpose>` is
`<super>/Agents/DesignerShared/repurpose`; `<designer>` is the designers'
shared folder, `<super>/Agents/DesignerShared` (it holds the renderer);
`<root>` is the video's brand folder, `<super>/Project/<BrandName>`.

You run unattended inside Atlas's batch: nobody reviews a preview, so
render the finished set straight away.

1. **Write eight quips**, each one line reacting to the video the way
   a poster captions a repost: a hook, not a description. No two alike,
   and none reused from another video. No single word alone on a second
   line. Keep them under about ten words; a header has room for two or
   three lines. One goes to the post, the rest to the headers. Without
   quips, the post and every low-placed variant are skipped.
2. **Render** the set, N being the count Atlas asked for:

   ```bash
   python3 <repurpose>/tools/repurpose.py --source <root>/renders/<name>.mp4 --count <N> \
     --cm <designer> --quip "<quip 1>" --quip "<quip 2>" ... --quip "<quip 8>" --out <root>/renders
   ```

   **The order is fixed, and the builder follows it:** it first builds
   **every** repurpose editable (one `-repbase-` page per mirrored or
   zoomed base, beside the source editable), then renders them **one at a
   time**, then renders the final variants, three at once (`--jobs 3`, the
   default). When rendering is done, it moves every repurpose editable to
   the video's materials `deletable/` folder.

   **On a render error** it deletes that editable (or that variant) and its
   failed output, builds a new editable, and renders it once more. Only
   once: a second error skips it, and the gate fills the set from the
   next candidates.

   It renders into `renders/` as `NN-name-MM-DD-RepNN.mp4`, moves any
   earlier file of the same name to `renders/deletable/`, and ends with
   the duplicate gate. Before that gate, it checks the rendered files
   themselves. A variant that fails is replaced by the next candidate that
   clears every real file by 2 bits; only that one renders again. The set
   is recorded in `renders/<name>-repurpose.json`. To redo one or two
   variants, use `--only` with their numbers; to re-check a finished set
   and replace only what fails, use `--repair` with the same quips.
3. **Reply.** Your final line to Atlas carries the count actually
   delivered: `DONE <render path> <total credits> <minutes> REP <n>`.

`--dry-run` measures and selects without rendering and prints each kept
variant's recipe: a quick way to see the count first. `--preview-only`
(into `renders/deletable/<name>-repurpose-preview/`) is only for working
with a user directly, who wants to see the set before it renders.

Overrides, only when the session knows better than the measurement:

- `--caption-band Y0,Y1` when the captions sit somewhere detection missed.
- `--no-mirror` when the footage itself carries text that must not flip:
  a screen recording, a product label, a sign. The page's own text is
  always handled; text burned into video pixels cannot be.

IF the builder reports a shortfall, fewer than N distinct enough for this
video, deliver what passed and report that number in `REP <n>`. Never
loosen the gate to fill the count.

**Several videos: one at a time.** Atlas lets only one designer repurpose
at a time and waits for it to finish before asking the next, so
repurposing never runs side by side. Each base renders in Chrome with four
workers, which already fills the GPU.

The builder moves its repurpose editables to `deletable/` even when a run
stops on an error. IF a run was killed outright, the next run of the
builder deletes the `-repbase-` pages it left behind before building new
ones; nothing stale is reused. A failed render is never left in
`renders/`.

## 5. Hard rules

- **Work only inside the Super Nova folder.** Every skill, doc, and tool
  you read comes from inside it. Copies of this skill exist elsewhere on
  this machine and are outdated: never read, search for, or follow them.
- **Two folders, and they are not the same.** The *package*,
  `<repurpose>`, holds `skills/`, `tools/`, `filter/`, `fropile/`, and
  `fonts/`; it is read from, never written to. The *root* is the video's
  brand folder, `<super>/Project/<BrandName>`; every output goes there.
  Never write an absolute path from memory.
- **The original is untouchable.** Its editable, materials, and render
  are never edited, moved, renamed, or deleted. The builder writes a
  repurpose editable beside it for each mirrored base, and moves them all
  to the materials `deletable/` folder when rendering is done.
- **Every variant is free.** IF a change would need any generation, it
  is not part of this skill.
- **Readable text never reads mirrored, and no motion runs backwards.**
- **The gate decides.** A variant that fails the duplicate gate is not
  delivered, however it looks.
- **The designers' shared folder is required:** the builder uses its renderer
  (`--cm <designer>`). Nothing of it is duplicated here.
- Use only the approved tool list: one `python3` command per step, no
  shell loops.
- Do not read any other file in the root, the shared folder, or your style folder. The
  exceptions are the skills in section 6 and the source editable the
  builder uses.

## 6. The other skills

These are the designers' shared skills, in `<designer>/skills/`; you have
already read them for the original.

- **file-management**: where every file lives. A variant is named after
  its source with a Rep suffix: `NN-name-MM-DD-RepNN`, so the third
  repurpose of `03-novaskin-09-21` is `03-novaskin-09-21-Rep03`. Number (the
  Brand number), name, and date are the source's.
- **stage-canvas-html**: the renderer the builder calls for mirrored bases.
- **known-methods**: what is already proven to work or fail.
- **working-memory**: its Design approach and word fixes. Nothing about the
  brand is there; the brand's instructions come in Atlas's request.

## 7. ffmpeg lessons the builder already follows

Kept for whoever maintains the tool.

- Screen-mode blends run on YUV chroma unless both inputs are forced to
  `format=gbrp` right before the blend; otherwise everything turns
  magenta.
- `rotate` with `fillcolor=none` leaves stale frames in the uncovered
  area; always give it an explicit colour and size.
- A generated `color` base plus `overlay=...:shortest=1` drops a frame;
  place video on a canvas with `pad` instead.
- `shortest=1` never belongs on an overlay whose top layer is a single
  still image.
- Verify outputs by frame count, never by duration.
- A single-frame test cannot reproduce buffer bugs; check a real render
  just after a scene change.
- This ffmpeg build has no text filters; all text is drawn as images.
- A base rendered by the designer's renderer carries 96 kHz audio, not the
  source's 48 kHz. `asetrate` for pitch assumes the input rate, so
  without an `aresample` to the source rate first, the voice comes out
  twice as long and an octave low. So every variant takes its sound
  from the source file, resampled to the source rate first, never from
  a rendered base. Each file is checked as soon as it renders: sound and
  picture must end together, at the length its speed implies. A fault
  costs one variant, not a rerun of the set.
