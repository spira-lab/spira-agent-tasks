---
name: toolkit
description: Which tool to use for each production step, how a generation is run with tools/gen.py, and each model's inputs, cost, and caveats. Fixed choices. Consult before generating any asset; never substitute a model.
---

# Toolkit

Every generated asset comes from the Spira CLI (`spira`, the npm package
`@spira-lab/cli`). This document names the one model for each job, so no
session spends credits or context finding it. The choices are fixed: do
not substitute another model because it looks similar or cheaper.

## 1. Running a generation

The preflight is the task's requirements check; `spira auth whoami`
passing is all a generation needs. Do not check the balance: other
sessions share it, and the platform measures what this run spends.

Run every command from the root, with root-relative paths; never `cd`
into a folder (a later command then resolves its paths from the wrong
place). Use only the commands and flags this skill gives: `spira` has no
wait flag of its own beyond what `gen.py` wraps.

Every generation is one command. Write the job's full inputs to a
payload file first, then:

```bash
python3 tools/gen.py <model-id> <payload.json> <materials>/<name>/<out-file>
```

It submits the job, waits (20 minutes by default; `--timeout 30m` to
raise it), downloads the result to `<out-file>` (a job's extra results
land beside it as `<name>-2.<ext>`), checks alpha on `.webm` results and
on transparent-background `.png` results, and prints its job id and
`url: <resultUrl>`.
Pass that URL into the next job that needs the result. Payload files
are working files: keep them in `<materials>/<name>/jobs/`, which is
never referenced by the html.

On failure it prints the job's status and exits 1. Read the error and
fix the payload before resubmitting once; never resubmit an unchanged
payload in a loop.

**Independent jobs run in parallel, in one command.** Whenever jobs do
not depend on each other's results, start them all at once and wait.
Leave their output on the terminal, never redirected to files: each
result prints as whole lines, and the job ids in that output are how the
platform bills the run.

```bash
M=editable/materials/<name>
python3 tools/gen.py seedance-1.5-pro $M/jobs/th-01.json $M/th-01.mp4 &
python3 tools/gen.py seedance-1.5-pro $M/jobs/th-02.json $M/th-02.mp4 &
python3 tools/gen.py suno-music $M/jobs/bgm.json $M/bgm.mp3 &
python3 tools/gen.py gpt-image-2 $M/jobs/broll-1.json $M/broll-1.png &
wait
```

Serial waiting costs the sum of the job times; parallel costs the
longest one. A job that depends on another's output starts the moment
that output is in, not after the whole batch. Plan the order so the
longest chain starts first: for a talking head that is Soul, then the
persona edit, then the clips, then the cut-outs (with the user's own
photo it is the speech, then the clip: 3j); music, b-roll, and elements
run beside it.

To inspect a model's inputs and prices: `spira ai models get <modelId>`.

## 2. Hosting local files

Every model input that is an image or a video must be a public HTTPS
URL.

- **The file came from a job.** Its `url:` is already hosted. Pass it
  straight into the next job; never re-upload a job's output.
- **The request already gives a public URL** (an avatar photo, a product
  image). Pass it straight into the job; never download and re-upload it.
- **The file exists only on disk** (a frame cut locally, a render). Host
  it with `spira assets upload <file>`; the hosted address is its
  `url:` line.

## 3. Tool map

| Step | Model ID | Credits |
|------|----------|---------|
| Persona base image | `ai-influencer-image` | 6.25 per image |
| Persona clean-up edit | `gpt-image-2` | 3.3 (1K), 3.45 (2K), 6.15 (4K) |
| Transparent-background element | `gpt-image-2` | same |
| Stock still for b-roll | `gpt-image-2` | same |
| Talking-head clip | `seedance-1.5-pro` | per second, see 3e |
| Talking head from the user's photo | `elevenlabs-text-to-speech` + `heygen-avatar-4` | see 3j |
| Talking-head cut-out | `bria-video-background-removal` | 0.42 per source second |
| Background music | `suno-music` | 6.6 per track |
| Avatar motion control, persona driven by a reference video | `kling-3.0-motion-control` pro | 9.52 per second |

## 3a. Persona base image: `ai-influencer-image`

This is Higgsfield Soul. It is the first step of every persona and is
never skipped: no other model produces the base likeness.

**The one exception: the user provides the photo.** WHEN the user
hands over a photo to use as the avatar, skip Soul, the clean-up edit
(3b), and Seedance (3e). The talking head is made from the photo as
given, in section 3j.

Payload: `{"prompt":"<persona description>","size":"9:16","resolution":"1080p"}`.
`size` also takes 16:9, 4:3, 3:4, 1:1, 2:3, 3:2; `resolution` 720p or
1080p (use 1080p).

The likeness is realistic but the output is raw, with visible blur. It
is never used directly; it is the reference for 3b, which is mandatory.

## 3b. Persona clean-up edit: `gpt-image-2`

Takes the Soul output as the reference and returns the
production-ready persona image.

Payload: `{"prompt":"<edit instruction>","referenceImage":["<soul url>"],"size":"9:16","resolution":"2K"}`.

The prompt (format in the prompting skill) must:

- Keep the exact same person, face, hair, skin, and build as the
  reference, and sharpen and clean it, removing blur and artefacts.
- **Give headspace above the head.** The whole head and hair sit fully
  inside the frame with clear empty space above them. Without this line
  the model crops the crown, and the image is useless as a talking-head
  reference.

**With a product.** When the persona must hold or wear a product, the
product image (a hosted URL) is the second reference:
`"referenceImage":["<soul url>","<product url>"]`. The prompt then also:

- Says which reference is the person and which is the product, and that
  the product is reproduced exactly as in its reference: shape, colour,
  label, proportions.
- States whether the product is **worn** or **held**, and if held, how:
  which hand, the grip (fingers wrapped around it, pinched by the cap,
  resting flat in the palm), where it sits in frame (chest height,
  beside the face, toward the camera), and which side faces the camera.
- States that it is **held steadily**: still hand, firm grip, product
  fully in focus, no motion, not tilting or slipping.

Inputs: `referenceImage` (array of URLs), `size` (`auto`, 1:1, 9:16,
16:9, 4:3, 3:4), `resolution` (`1K`, `2K`, `4K`). Unsupported:
`auto`+`2K`, `auto`+`4K`, `1:1`+`4K`. Use `9:16` with `2K` for the
persona.

## 3c. Transparent-background elements: `gpt-image-2`

For any cut-out element that sits on the stage: props, icons, objects,
stickers. Several elements are one sheet (creative-video-production
section 1): up to six in one `1:1` `2K` image (2048 x 2048), 3.45 credits
for all of them. Payload:
`{"prompt":"Four separate objects arranged in a 2x2 layout with wide empty space between them, each object whole and not touching any other: <element>, <element>, <element>, <element>. On a transparent background, PNG with alpha, no backdrop, no shadow on the ground, no frame, no text","size":"1:1","resolution":"2K"}`.

Then cut them out, naming them in reading order (left to right, top to
bottom):

```bash
python3 tools/cut-sheet.py elements <materials>/<name>/el-sheet.png --names el-piston,el-wing,el-flag,el-helmet
```

Each object is cropped with a small margin, and anything belonging to
another object is cleared from its crop. Move the sheet to `deletable/`
once the cut-outs are in. A single element on its own is the same prompt
with one object at `1:1` `1K`.

The prompt must say transparent background in those words; it does not
happen by default, and a white or grey backdrop cannot be keyed cleanly
afterwards. `gen.py` warns when the PNG came back without alpha.

## 3d. Stock stills for b-roll: `gpt-image-2`

Several stills are one collage (creative-video-production section 1): a
`9:16` `4K` image comes back 2160 x 3840, so a 2 x 2 collage cuts into four
frames of exactly 1080 x 1920, full-bleed on the stage, for 6.15 credits
in all. Payload:
`{"prompt":"A 2x2 collage of four separate photographs in four equally divided frames, edge to edge, no border, no outline, no gaps, no dividing lines. Top left: <scene>. Top right: <scene>. Bottom left: <scene>. Bottom right: <scene>. Photographic, natural light, no text, no logos","size":"9:16","resolution":"4K"}`.

Then cut the frames out, named in reading order:

```bash
python3 tools/cut-sheet.py grid <materials>/<name>/broll-sheet.png 2x2 --names broll-track,broll-engine,broll-cockpit,broll-daily
```

Frames used as insets or cards are cut from the same collage and cropped
on the stage with `object-fit: cover`. The provider sometimes returns a
collage smaller than asked (1024 x 1536 instead of 2160 x 3840);
`cut-sheet.py` then warns that the frames are under the stage width. Keep
those frames for insets and cards only, and generate each full-bleed still
on its own. A single still on its own is
`{"prompt":"<scene>, photographic, natural light","size":"9:16","resolution":"2K"}`
(1152 x 2048); never `1K` for a full-bleed still, which comes back
640 x 1136.

## 3e. Talking-head clip: `seedance-1.5-pro`

Animates the cleaned persona image into a speaking clip. Payload:
`{"prompt":"<line and delivery>","referenceImage":["<persona url>"],"duration":"8","size":"9:16","resolution":"1080p","sound":true}`.

Inputs: `referenceImage` (up to 2 URLs; one for a talking head),
`duration` (`4`, `8`, or `12`, nothing else), `size`, `resolution`
(`480p`, `720p`, `1080p`), `sound` (boolean). `referenceAudio` and
`referenceVideo` are not supported; the spoken line goes in the prompt.

**Clips are exactly 4, 8, or 12 seconds.** The script is split into
chunks that each read aloud inside one of those lengths, one job per
chunk, at 3.2 to 3.4 words per second:

| Duration | Words per chunk |
|----------|-----------------|
| 4 s | 13 to 14 |
| 8 s | 26 to 27 |
| 12 s | 38 to 41 |

Count each chunk's words against this table before submitting. Never
write a segment that needs 5, 9, or 15 seconds; trim the words to the
slot, never stretch the slot to the words.

**All chunks are one batch.** Write every chunk's payload
(`jobs/th-01.json`, `jobs/th-02.json`, ...), then run them all in one
parallel command (section 1), then every cut-out in one parallel
command (3f). Running the clips one at a time is the single biggest
waste of time in the kit.

**Plan while the clips render.** The clips take three to four minutes.
Start their batch with the Bash tool's background mode and use the wait:
decide every scene (what it shows, which assets, roughly where each
sentence falls) and write the CSS and skeleton that do not depend on
exact timings. When the plan is written, block on the batch:

```bash
python3 tools/gen.py --await $M/th-01.mp4 $M/th-02.mp4 $M/th-03.mp4
```

It returns as soon as every clip has finished and prints what each
generation printed. Timings, clip placement and captions come after it.
Wait on background generations only this way: never with `sleep`,
`pgrep` or a polling loop (a `pgrep -f` loop matches itself and never
ends; on staging one ran into the tool's 10-minute timeout).

The clips' own audio is the voice-over. Build it and its timings in one
step, clips in order, then place the clips back to back on the stage:

```bash
python3 tools/make-timings.py <materials>/<name>/vo.mp3 --from th-01.mp4 th-02.mp4 th-03.mp4
```

The clips keep the persona image's framing: the face sits where it sits
in `persona.png`, so plan the layout around it from that image, and check
it on the stage with `audit.js --at`. Do not cut frames out of the clips
to look at them.

Cost per second at `standard`:

| Resolution | Sound off | Sound on |
|------------|-----------|----------|
| 480p | 0.88 | 1.75 |
| 720p | 1.97 | 3.94 |
| 1080p | 4.43 | 8.86 |

An 8-second 1080p clip with sound is about 71 credits. Use `720p` for
tests and `1080p` for the final.

## 3f. Talking-head cut-out: `bria-video-background-removal`

Removes the background from a Seedance or HeyGen clip so the talking head sits on
the stage with real transparency. Payload:
`{"referenceVideo":["<clip url>"],"mode":"Transparent","preserveAudio":true,"autoZoom":false}`,
written to `<name>.webm`.

**`mode` must be the word `Transparent`.** `spira ai models get` lists
only solid colours and says transparent output is not available; both
are wrong for this purpose and are ignored. `Transparent` returns a VP9
WebM with true alpha (verified 2026-09-20); a colour mode returns an
opaque MP4. Never use a colour mode and never add a chroma-key step.
`gen.py` warns when the WebM came back without alpha.

**The Bria output is final.** Do not mask, matte, crop, re-key, or
otherwise adjust it. IF it keeps an object the person holds or touches,
such as a laptop, a phone, or a mug, that object is part of the
cut-out. The only reasons to touch the result are a missing alpha
channel or the user asking for a change.

The WebM goes on the stage as a `<video>` element, never as extracted
frames (stage-canvas-html, rule 11).

**Every talking-head clip is cut out, in one batch.** As soon as the
clips are in, submit every clip to Bria in one parallel command
(section 1), never one at a time, and never skip a clip because the
scene plan shows it whole: the cut-out is what the scenes are layered
with (creative-video-production section 5), and deciding per clip is
how sessions stopped using it at all.

## 3g. Background music: `suno-music`

The music bed under the voice. Payload:
`{"mode":"v5_5","customMode":true,"instrumental":true,"style":"<style>","title":"<title>"}`,
written to `bgm.mp3`. A job returns two takes: use `bgm.mp3` and move
`bgm-2.mp3` to deletable (file-management section 5).

- **Always instrumental. Never lyrics.** Sung words fight the voice and
  neither is intelligible. `instrumental` only takes effect in custom
  mode, which is why `customMode` is true; there is no `prompt` in
  custom mode, since there it is lyrics.
- **`style` is genre, mood, tempo, and instruments only.** Suno rejects
  a style that names an artist, a brand, a sport, or anything it reads
  as a producer tag ("motorsport" was rejected), and the CLI reports it
  only as `provider_error`. Describe the sound, not the subject: "sleek
  cinematic electronic, driving pulse, 110 bpm, synth bass".

## 3h. Avatar motion control: `kling-3.0-motion-control`

Transfers the motion of a reference video onto the persona image: the
persona moves the way the person in the reference moves, keeping the
persona's identity. For the avatar only: never used to animate
graphics, props, products, text, or b-roll stills.

Payload:
`{"prompt":"<optional guidance>","referenceImage":["<matching image url>"],"referenceVideo":["<motion clip url>"],"characterOrientation":"image","duration":"<clip length>","mode":"pro","sound":false}`.

`referenceImage` is exactly one URL (the persona), `referenceVideo`
exactly one URL (the motion source), `characterOrientation` `image`
(identity from the image, motion from the video), `duration` 3 to 15 by
the second, then 20, 25, 30 (the billing length; the motion follows the
reference), `mode` `pro`, `sound` false unless asked. Cost is 9.52
credits per second.

**When a source video's motion is to be copied:**

1. **Make the matching image first**: the persona edit (3b) with the
   avatar in the same position as the person in the source at the
   moment the copied motion begins: same pose, framing, side to camera.
2. **Clip only the motion itself**:
   `ffmpeg -y -ss <start> -to <end> -i <source> -an -c:v libx264 -crf 17 <clip>.mp4`.
3. **One clip and one image per motion.** Motions that differ in
   context are cut and run separately.
4. **A clip under 3 seconds is extended, then the output trimmed**:
   `ffmpeg -y -i <clip>.mp4 -vf tpad=stop_mode=clone:stop_duration=<s> -c:v libx264 -crf 17 <clip>-ext.mp4`,
   then `ffmpeg -y -i <output>.mp4 -t <real length> -c:v libx264 -crf 17 -c:a copy <output>-trim.mp4`.
5. Host the clip (section 2), set `duration` to its length, and run.
   Rejected clips, extended intermediates, and untrimmed outputs go to
   deletable.

## 3i. Voice-over without a presenter: `elevenlabs-text-to-speech`

For a VO explainer with no talking head. Payload:
`{"text":"<the script>","voiceId":"21m00Tcm4TlvDq8ikWAM","providerModelId":"eleven_v3"}`,
written to `vo.mp3`, then `python3 tools/make-timings.py <materials>/<name>/vo.mp3`.
Voices proven on this account: `21m00Tcm4TlvDq8ikWAM` (female) and
`iP95p4xoKVk53GoZ742B` (male), both on `eleven_v3`; use the one that fits
the video, unless a brand file names its own. Cost is 0.01 credits a
character. The voice is ElevenLabs, so `data-sfx-under="14"` on `#vo`.

## 3j. Talking head from the user's photo: `heygen-avatar-4`

Only WHEN the user provides a photo; without one, the talking head is
the usual Soul, 3b, and Seedance route. The request always carries an
ElevenLabs voice ID. Two jobs, in order:

1. **Speech**, the whole script in one job with that voice ID on
   ElevenLabs V2:
   `{"text":"<the script>","voiceId":"<the voice ID from the request>","providerModelId":"eleven_multilingual_v2"}`,
   written to `vo.mp3`. Build the timings from it straight away
   (`python3 tools/make-timings.py <materials>/<name>/vo.mp3`), then
   host it with `spira assets upload` (section 2).
2. **Talking head**, the photo lip-synced to that speech:
   `{"referenceImage":["<photo url>"],"referenceAudio":["<vo.mp3 url>"],"size":"9:16","resolution":"1080p","mode":"stable","talkingStyle":"stable"}`,
   written to `th-01.mp4`. Use `720p` for tests.

One clip covers the whole voice-over: no 4/8/12-second chunks. It is cut
out with 3f like any talking-head clip and goes on the stage at
`data-start="0"`. The voice is ElevenLabs, so `data-sfx-under="14"` on
`#vo`. Cost is 10 credits a second.

## 4. Do not use

Anything not listed above, including other image models
(`nano-banana-*`, `seedream-*`, `flux-kontext`), other video models
(`kling-*` other than 3.0 motion control, `seedance-2.*`, `veo3.1`,
`heygen-avatar-4` outside 3j), and any other lip-sync route. The one exception is a model
the user names explicitly in the request: then use it for that request,
reading its inputs and prices with `spira ai models get <modelId>`.
IF a step seems to need a tool that is neither listed nor named by the
user, do without it and say so in the final message.
