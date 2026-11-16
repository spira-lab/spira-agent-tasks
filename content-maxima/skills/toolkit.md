---
name: toolkit
description: Which tool to use for each production step, how a generation is run with submit_ai_job and wait_ai_job, and each model's inputs, cost, and caveats. Fixed choices. Consult before generating any asset; never substitute a model.
---

# Toolkit

Every generated asset is a Spira AI job, run with two tools on the MCP
server `worker_tools`: `submit_ai_job` and `wait_ai_job`. This document
names the one model for each job, so no session spends credits or context
finding it. The choices are fixed: do not substitute another model because
it looks similar or cheaper.

## 1. Running a generation

The preflight is the task's requirements check; `spira auth whoami`
passing is all a generation needs. Do not check the balance: other
sessions share it, and the platform measures what this run spends.

**Never run a job through the `spira` CLI** — no `spira ai jobs create`,
`wait` or `status`, in any form. A CLI submission charges the operator on
the spot, outside this task's bill. The CLI is used only for what this
skill names below (hosting the finished render, model docs).

Run every command from the root, with root-relative paths; never `cd`
into a folder (a later command then resolves its paths from the wrong
place).

Every generation is three steps:

1. **Write the payload** — the job's full inputs object — to
   `<materials>/<name>/jobs/<out-file>.json`. It is the record of what was
   asked. Payload files are working files, never referenced by the html.
2. **Submit** with `submit_ai_job`: `modelId` is the model id, `inputs` is
   the same object as the payload file. It returns the `jobId`. Write
   `{"jobId": "<id>", "model": "<model-id>"}` to
   `<materials>/<name>/jobs/<out-file>.pending` at once.
3. **Collect** with `wait_ai_job`: `jobId`, and `saveTo` set to
   `<materials>/<name>/<out-file>`. It waits (300 s by default; pass
   `timeoutSec` up to 600 for video), saves the result there (a job's extra
   results land beside it as `<name>-2.<ext>`), and returns `status`,
   `resultUrls` and `saved`. Delete the `.pending` file once the result is
   saved. Never download a result yourself with `curl`.

Pass `resultUrls[0]` into the next job that needs the result.

`status: "FAILED"` carries the provider's error. Read it and fix the
payload before resubmitting once (a new `submit_ai_job`, a new
`.pending`); never resubmit an unchanged payload in a loop.

`stillRunning: true` means the wait timed out, not that the job failed:
call `wait_ai_job` again with the same `jobId` and `saveTo`. `saveError`
means the job finished but its download failed: call `wait_ai_job` again
with the same `jobId` and `saveTo` — it returns at once and is not charged
again. IF a session was cut off
(a restart), read every `jobs/*.pending` and call `wait_ai_job` on the id
it holds. **Never call `submit_ai_job` for an output that has a `.pending`
record** — that pays twice for one output. Delete a `.pending` file only
to deliberately replace that job.

`wait_ai_job` checks alpha itself: every saved `.png` and `.webm` comes
back in `saved` with `hasAlpha`. `hasAlpha: false` on a file whose payload
asked for a transparent background means it has no alpha channel and must
be regenerated.

**Independent jobs run in parallel.** Whenever jobs do not depend on each
other's results, submit them all in one turn — one `submit_ai_job` call
each — then wait on them all in one turn — one `wait_ai_job` call each.
Calls in the same turn run at once; one after another costs the sum of
the job times.

Serial waiting costs the sum of the job times; parallel costs the
longest one. A job that depends on another's output starts the moment
that output is in, not after the whole batch. Plan the order so the
longest chain starts first: for a talking head that is Soul, then the
persona edit, then the clips, then the cut-outs (with the user's own
photo the chain starts at the persona edit, or at the voice-over in 3j); music, b-roll, and elements
run beside it.

To inspect a model's inputs and prices: `spira ai models get <modelId>`.

## 2. Hosting local files

Every model input that is an image, a video, or audio must be a public
HTTPS URL. Everything else stays on disk: the stage and the renderer
read the materials folder, and nothing is hosted for them.

- **The file came from a job.** Its `resultUrls[0]` is already hosted.
  Pass it straight into the next job; never host a job's saved output.
- **The request already gives a public URL** (an avatar photo, a product
  image). Pass it straight into the job; never download and re-host it.
- **The file exists only on disk and goes into a job** (a clip
  cut into parts, a re-encoded supplied clip, a voice-over converted from a recording). Host it with the
  `host_file` tool (`worker_tools`), `path` root-relative; the URL it
  returns is the job's input. Host nothing a job does not take.
- **Never host any file with `spira assets upload`**, intermediate or
  finished. That files it among the user's own uploads, where the user
  sees it. The finished render is hosted with `host_file` too
  (file-management section 6).

## 3. Tool map

**Where the voice comes from decides the talking head.** There are
four sources, and the request says which:

- **Auto** (nothing said about the voice): the talking-head clips speak
  the script, and their audio is the voice-over (3e: Gemini Omni Flash
  1.1).
- **An ElevenLabs voice ID** (`ElevenLabs voice ID:` in the request):
  the script is spoken with that voice (3j step 1).
- **The user's own recording** (`Voice-over:` in the request, an audio
  file in place of the script): it is the voice-over as it is. Nothing
  spoken is generated, and its words are the script (3j step 1).
- **A supplied talking-head video** (`Talking head supplied video:` in
  the request): the video is the talking head and its own audio the
  voice-over; its words are the script. Nothing is generated for the
  presenter or the speech (3k).

With a voice ID or a recording, the voice-over exists before the
talking head, so a talking head is HeyGen lip-synced to it (3j), never
Omni, whose clips make their own speech.

The voice source picks the route to the talking head, never whether
there is one: every video has a talking head unless the request
explicitly says otherwise (creative-video-production section 1). Only a
video that is presenter-less by that rule uses the voice-over directly
(3i).

| Step | Model ID | Credits |
|------|----------|---------|
| Persona base image | `ai-influencer-image` | 6.25 per image |
| Persona clean-up edit | `gpt-image-2` | 3.3 (1K), 3.45 (2K), 6.15 (4K) |
| Transparent-background element | `gpt-image-2` | same |
| Stock still for b-roll | `gpt-image-2` | same |
| Talking-head clip | `gemini-omni-flash-1.1` | per clip, see 3e |
| Talking head speaking a given voice-over (voice ID or recording) | `heygen-avatar-4` | see 3j |
| Talking head supplied by the user | none: the video itself | 0, see 3k |
| Talking-head cut-out | `pixelcut-video-background-removal` | 2.2 per source second |
| Talking-head cut-out, fallback only | `bria-video-background-removal` | 0.42 per source second |
| Background music | `suno-music` | 6.6 per track |
| Avatar motion control, persona driven by a reference video | `kling-3.0-motion-control` pro | 9.52 per second |

**Frame rate.** The render is always 30 fps. A generated clip need not
be: `gemini-omni-flash-1.1` is 24 fps (240 frames in a 10 s clip), HeyGen
is 25 fps, and the cut-out (3f) keeps the rate of the clip it is given. The audit and the
render interpolate every clip that is not 30 fps to 30 (motion
interpolation, in the all-keyframe copies under
`materials/<name>/deletable/intra/`), so nothing is to be done about
it. The first audit of a video pays for this, a few minutes, and later
audits and the render reuse the copies. Never convert a clip's frame
rate yourself.

## 3a. Persona base image: `ai-influencer-image`

This is Higgsfield Soul. It is the first step of every persona and is
never skipped: no other model produces the base likeness.

**The one exception: the user provides the photo.** WHEN the user
hands over a photo to use as the avatar (or a video, from which a clear
frame is taken), skip Soul. Host the photo only if it is not already a
public URL (section 2). This is a `Presenter photo:` or a `Presenter
reference video:`, which give only the face. A `Talking head supplied
video:` is not this: it is the finished talking head and skips 3a
entirely (3k). Then:

- **With a voice ID or a recording** (section 3): skip the clean-up
  edit (3b) and the talking-head clips (3e) too. The talking head is HeyGen from the photo
  as given, section 3j.
- **On Auto voice:** the photo takes Soul's
  place as the reference for the clean-up edit (3b), which still gives
  the headspace above the head. The edited image goes into the
  talking-head clips (3e) as usual.

Payload: `{"prompt":"<persona description>","size":"9:16","resolution":"1080p"}`.
`size` also takes 16:9, 4:3, 3:4, 1:1, 2:3, 3:2; `resolution` 720p or
1080p (use 1080p).

The likeness is realistic but the output is raw, with visible blur. It
is never used directly; it is the reference for 3b, which is mandatory.

## 3b. Persona clean-up edit: `gpt-image-2`

Takes the Soul output (or the user's photo, 3a) as the reference and
returns the production-ready persona image.

Payload: `{"prompt":"<edit instruction>","referenceImage":["<soul url>"],"size":"9:16","resolution":"2K"}`.

The prompt (format in the prompting skill) must:

- Keep the exact same person, face, hair, skin, and build as the
  reference, and sharpen and clean it, removing blur and artefacts.
- **Give headspace above the head.** The whole head and hair sit fully
  inside the frame with clear empty space above them. Without this line
  the model crops the crown, and the image is useless as a talking-head
  reference.

**A product never goes into this edit.** With or without a product, the
edit is the same: the Soul output (or the user's photo) alone, cleaned
and reframed. The product enters in the talking-head clips, where Omni
takes the persona and the product image together (3e).

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
afterwards. `wait_ai_job` reports `hasAlpha: false` when the PNG came back without alpha.

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

## 3e. Talking-head clips: `gemini-omni-flash-1.1`

Animates the cleaned persona image into speaking clips. **One model for
the whole video.** Every clip of a video comes from Gemini Omni Flash 1.1;
there is no other talking-head clip model. IF a clip comes back `FAILED`
again after its one corrected resubmission (section 1), or every
submission fails at once (`provider_error` on submit: Omni is down), stop
and say so in the final message; never make the clips with another model.

Omni makes only 9:16 and 16:9. A video whose output ratio is neither
(1:1) still uses 9:16 clips: the cut-out (3f) places the person on the
stage at that ratio.

**Chunking is by syllables, with `tools/chunker.py`.** The script is
never changed: the tool splits it at sentence ends (and at a comma,
colon or dash only when that is what lands a chunk in the band) and
gives each chunk a clip length so it is spoken at 4.7 to 5.0 syllables a
second (never over
5.2: above that Omni cuts the end off or rewrites the line). Run it on
the saved script before any clip is written:

```bash
python3 tools/chunker.py <materials>/<name>/script.txt <materials>/<name>/jobs/plan.json
```

It prints one line per chunk (length, syllables, pace, its exact text)
and writes `plan.json`; one job per chunk, in order, with that text and
that `duration`. A chunk flagged `[fallback]` (4.0 to 5.2) is fine; one
flagged `[UNDER 4.0]` risks silence at its end, and is used only when
the tool finds nothing better. The tool counts English by rules: WHEN
it gets a brand name or an odd word wrong, write the script as
`script.json`, `{"text": "<the script>", "syllables": {"<word>": <n>}}`,
and run the tool on that instead. WHEN it stops on a stretch too long
for any clip with no comma in it, tell the user the sentence is too long
to say in one clip; never reword it.

**Payload**, persona only:
`{"prompt":"<line and delivery>","referenceImage":["<persona url>"],"duration":"8","size":"9:16","resolution":"1080p"}`.
`duration` is `4`, `6`, `8` or `10`; `size` `9:16` or `16:9`;
`resolution` `1080p` (720p and 1080p cost the same). No
`generationType`: with one image Omni opens on the persona image, so the
clip keeps `persona.png`'s framing.

**With a product** (a product image in the request, to be shown in the
presenter's hand): the product image is the second reference, and the
prompt says the person holds it and does one or two simple things with
it (prompting skill section 5):
`{"prompt":"<line, product and delivery>","generationType":"reference_to_video","referenceImage":["<persona url>","<product url>"],"duration":"8","size":"9:16","resolution":"1080p"}`.
Every clip of the video takes the same two references. In this mode Omni
does not open on the persona image, so the room or the framing can shift
(a test put the presenter on a different chair): plan the layout from
the clips, not from `persona.png`. Once `th-01.mp4` is in, make its
contact sheet, `tools/style-sheet.sh <materials>/<name>/th-01.mp4
<materials>/<name>/deletable`, look at it as in 3k step 5, and check the
layout on the stage with `audit.js --at`.

**All chunks are one batch.** Write every chunk's payload
(`jobs/th-01.json`, `jobs/th-02.json`, ...), submit them all with
`submit_ai_job` in one turn, wait on them all with `wait_ai_job` in one
turn (section 1), then every cut-out the same way (3f). Running the
clips one at a time is the single biggest waste of time in the kit.

**Plan while the clips render.** The clips take two to four minutes.
Submit the whole batch, then do not wait yet: decide every scene (what
it shows, which assets, roughly where each sentence falls) and write the
CSS and skeleton that do not depend on exact timings. When the plan is
written, wait on the batch — one `wait_ai_job` per clip, all in one
turn, each with its `saveTo`.

They return as soon as each clip has finished. Timings, clip placement
and captions come after them. Wait on a submitted job only this way:
never with `sleep`, `pgrep` or a polling loop (a `pgrep -f` loop matches
itself and never ends; on staging one ran into the tool's 10-minute
timeout).

The clips' own audio is the voice-over. Build it and its timings in one
step, clips in order, then place the clips back to back on the stage:

```bash
python3 tools/make-timings.py <materials>/<name>/vo.mp3 --from th-01.mp4 th-02.mp4 th-03.mp4
```

Without a product, the clips keep the persona image's framing: the face
sits where it sits in `persona.png`, so plan the layout around it from
that image, and check it on the stage with `audit.js --at`. Do not cut
frames out of the clips to look at them; the one contact sheet of a
product clip (above) is the exception.

Cost per clip (the same at 720p and 1080p): 4 s 41, 6 s 54, 8 s 68,
10 s 81 credits.

## 3f. Talking-head cut-out: `pixelcut-video-background-removal` (fallback `bria-video-background-removal`)

Removes the background from an Omni, HeyGen, or supplied (3k) clip so the talking head sits on
the stage with real transparency. Payload:
`{"referenceVideo":["<clip url>"],"mode":"Transparent"}`,
written to `<name>.webm`.

**`mode` must be the word `Transparent`.** It returns a VP9 WebM with
true alpha; a colour mode returns an opaque MP4. Never use a colour mode
and never add a chroma-key step. The model takes no other field.
`wait_ai_job` reports `hasAlpha: false` when the WebM came back without alpha.

**Bria is only the fallback.** WHEN a clip's Pixelcut job comes back
`FAILED` again after its one corrected resubmission (section 1), or
Pixelcut fails every submission at once (it is down), cut that clip out
with Bria instead:
`{"referenceVideo":["<clip url>"],"mode":"Transparent","preserveAudio":true,"autoZoom":false}`,
written to the same `<name>.webm`. `mode` must be `Transparent` here too
(Bria's default is green). Bria costs 0.42 credits per source second
and takes the same 60 s at most. Never run both on the same clip, and
say in the final message which clips fell back.

**The cut-out takes at most 60 s of source.** A longer clip is divided at a
segment boundary (the `segments` in `timings.json`) into parts of 60 s or
less, re-encoded H.264, then each part hosted with `host_file` (section
2) and cut out in one batch, each
`.webm` at its own `data-start` (3e). A longer source is rejected at
submit, so this is not a way to save a generation.

**The cut-out is final.** Do not mask, matte, crop, re-key, or
otherwise adjust it. IF it keeps an object the person holds or touches,
such as a laptop, a phone, or a mug, that object is part of the
cut-out. The only reasons to touch the result are a missing alpha
channel or the user asking for a change.

The WebM goes on the stage as a `<video>` element, never as extracted
frames (stage-canvas-html, rule 11).

**Every talking-head clip is cut out, in one batch.** As soon as the
clips are in, submit every clip for its cut-out in one turn and wait on them in
one turn (section 1), never one at a time, and never skip a clip because the
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

Only for a video the request explicitly makes presenter-less
(creative-video-production section 1); a VO explainer otherwise still
has a talking head and never comes here. WHEN the voice comes from a
voice ID or a recording (section 3), the voice-over is 3j step 1
instead, and nothing here applies. Payload:
`{"text":"<the script>","voiceId":"21m00Tcm4TlvDq8ikWAM","providerModelId":"eleven_v3"}`,
written to `vo.mp3`, then `python3 tools/make-timings.py <materials>/<name>/vo.mp3`.
Voices proven on this account: `21m00Tcm4TlvDq8ikWAM` (female) and
`iP95p4xoKVk53GoZ742B` (male), both on `eleven_v3`; use the one that fits
the video, unless a brand file names its own. Cost is 0.01 credits a
character.

## 3j. Talking head speaking a given voice-over: `heygen-avatar-4`

WHEN the voice comes from a voice ID or the user's recording (section
3). The presenter is the user's photo as given (3a), or without one the
cleaned persona image (3a, then 3b), and it starts beside step 1. Two
steps, in order:

1. **The voice-over**, `vo.mp3`, one file for the whole video.
   - **A voice ID:** the whole script in one job with that voice on
     ElevenLabs V2:
     `{"text":"<the script>","voiceId":"<the voice ID from the request>","providerModelId":"eleven_multilingual_v2"}`,
     written to `vo.mp3`, then its timings:
     `python3 tools/make-timings.py <materials>/<name>/vo.mp3`.
   - **A recording:** no job, and it comes first in the session, before
     the concept: its words are what the video is about. Start the
     video with the request's script, or with none
     (`tools/new-video.sh "<brand, or voiceover>" < /dev/null`), then
     one command converts the recording to `vo.mp3` as it is, builds
     its timings, and, unless a script was saved, writes the
     transcript to `script.txt` as the script:
     `python3 tools/make-timings.py <materials>/<name>/vo.mp3 --recording <recording url or path>`.
     Read the transcript it prints and settle the concept from it. In
     a written `script.txt` correct only the spelling of names
     (captions carry it). Never cut, retime, or regenerate the
     recording: its length is the video's length.

   The `vo.mp3 url` the talking head takes (section 2): with a voice ID
   it is the ElevenLabs job's `resultUrls[0]` (the timings step only
   reads the file); with a recording, `vo.mp3` was converted on disk, so
   host it with `host_file`.
2. **Talking head**, the presenter lip-synced to that voice-over:
   `{"referenceImage":["<photo or persona url>"],"referenceAudio":["<vo.mp3 url>"],"size":"9:16","resolution":"1080p","mode":"stable","talkingStyle":"stable"}`,
   written to `th-01.mp4`. Use `720p` for tests.

One clip covers the whole voice-over: no chunks. It is cut
out with 3f like any talking-head clip (split first if over 60 s) and
goes on the stage at `data-start="0"`. Cost is 10 credits a second.

## 3k. Talking head supplied by the user: no generation

WHEN the request has `Talking head supplied video: <url>`. That exact
video is the talking head of the finished video, and its own audio is
the voice-over. Skip the persona (3a), the avatar edit (3b), the
talking-head clips (3e), and HeyGen (3j); generate no speech (3i). It comes first in the
session, before the concept: its words are what the video is about.

1. **Start the video with no script**:
   `tools/new-video.sh "<brand, or talking head>" < /dev/null`.
2. **Bring the clip in as `th-01.mp4`**, re-encoded to H.264 so the
   stage and the renderer play it (an upload may be MOV or HEVC), then
   host it with `host_file` (section 2):
   `ffmpeg -y -v error -i "<url>" -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart <materials>/<name>/th-01.mp4`.
3. **Submit its cut-out (3f) at once**, with the hosted `th-01.mp4` as
   the input, and do steps 4 and 5 while it renders.
4. **The clip's own speech is the voice, and Whisper transcribes it**,
   in one command:
   `python3 tools/make-timings.py <materials>/<name>/vo.mp3 --recording <materials>/<name>/th-01.mp4`.
   It takes the audio out of the clip as `vo.mp3` (the speech heard in
   the finished video), runs Whisper on it for every word's timing
   (`timings.json`), and writes Whisper's transcript to `script.txt` as
   the script. Read the transcript it prints and settle the concept
   from it. Correct only the spelling of names in `script.txt` (captions
   carry it). Whisper detects the language: a clip in Hindi stays in
   Hindi. Never cut, retime, mute, or re-voice the clip's speech: it is
   the narration, and its length is the video's length.
5. **Look at where the person is**, from a contact sheet of frames
   across the clip:
   `tools/style-sheet.sh <materials>/<name>/th-01.mp4 <materials>/<name>/deletable`.
   Open only `deletable/contact-sheet.jpg`. Note where the face and the
   body sit in the frame, how much of it they fill, whether they move,
   and where the free space is, and plan where every animated element
   lands from that: beside, above, or below the person, never over the
   face (creative-video-production section 9). A generated clip keeps
   `persona.png`'s framing; a supplied clip has no such image, so this
   sheet is how its framing is known.

On the stage the clip goes in at `data-start="0"`, as a HeyGen clip
does, and its cut-out carries the scenes like any talking head
(creative-video-production section 5). The video elements stay muted;
`vo.mp3` plays the clip's speech from the same start, so the lips and
the voice stay in sync. The output ratio is the clip's own ratio.

**Captions follow the clip's speech.** `tools/captions.py` (stage skill
section 6) times every word from Whisper's `timings.json` and writes it
as `script.txt` has it, so the subtitles match what the person says,
word for word, in the clip's language.

## 4. Do not use

Anything not listed above, including other image models
(`nano-banana-*`, `seedream-*`, `flux-kontext`), other video models
(`kling-*` other than 3.0 motion control, `seedance-2.*`, `veo3.1`,
`seedance-1.5-pro`, `gemini-omni-flash-1.1` outside 3e,
`heygen-avatar-4` outside 3j), and any other lip-sync route. The one exception is a model
the user names explicitly in the request: then use it for that request,
reading its inputs and prices with `spira ai models get <modelId>`.
IF a step seems to need a tool that is neither listed nor named by the
user, do without it and say so in the final message.
