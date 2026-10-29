---
name: toolkit
description: Which tool to use for each production step, with the model ID, inputs, cost, and caveats, and how a generation is run with submit_ai_job, wait_ai_job and host_file. Fixed choices. Consult before generating any asset; never substitute a model.
---

# Toolkit

Every generated asset is a Spira AI job, run with the tools on the MCP
server `worker_tools`: `submit_ai_job`, `wait_ai_job` and `host_file`.
This document names the one tool for each job, so no session spends
credits or context finding it. The choices are fixed: do not substitute
another model because it looks similar or cheaper.

## 1. Running a generation

The worker has already checked the sign-in; there is no preflight. The
price of a job comes from this document, from `spira ai models get
<modelId>`, or from the quote `submit_ai_job` returns. Do not check the
balance: other sessions share it.

**Never run a job or an upload through the `spira` CLI**, and never
write a script that wraps it. The CLI is for `spira ai models get <modelId>`
only (reading a model's docs).

Every generation is three steps:

1. **Write the payload**, the job's full inputs object, to
   `<materials folder>/<out-file>.json`. It is the record of what was
   asked.
2. **Submit** with `submit_ai_job`: `modelId` is the model id, `inputs` is
   the same object as the payload file. It returns the `jobId`. Write
   `{"jobId": "<id>", "model": "<model-id>"}` to
   `<materials folder>/<out-file>.pending` at once.
3. **Collect** with `wait_ai_job`: `jobId` (`timeoutSec` up to 600 for
   video). It waits and returns the result URLs only. Download each URL
   into the video's materials folder (see the file-management skill) with
   the `ai` tool's download action; never with `curl` or `wget`, which are
   denied. Delete the `.pending` file once the result is saved.

Then:

1. Record the job's result URL as `url` in the asset's metadata entry,
   and the exact inputs prompt as `prompt`.
2. Record the job's credit cost as `credits` in the same entry: the quote
   `submit_ai_job` returned, or when it gave none, this document's price
   for that model and option (a per-generation price as is, a per-second
   price times the seconds billed). Never use the account balance: it is
   shared with other sessions running at the same time. Every job gets
   one, including rejected candidates and failed runs that were billed.

If a job fails, `wait_ai_job` returns the provider's error: read it, fix
the payload, and resubmit once; never resubmit an unchanged payload in a
loop. If the wait times out (`stillRunning`), call `wait_ai_job` again
with the same `jobId`. IF a session was cut off, read every
`*.pending` file and call `wait_ai_job` on the id it holds; never call
`submit_ai_job` for an output that has a `.pending` record. To inspect a
model's inputs and prices: `spira ai models get <modelId>`.

**Independent jobs run in parallel, never one after another.** Whenever
several jobs do not depend on each other's results, submit them all in
one message (one `submit_ai_job` call each), then wait on them all in one
message (one `wait_ai_job` call each). Serial waiting costs the sum of
their times; parallel costs the longest one. This applies to every batch
in this kit: the talking-head chunks, the background removal of each
clip, a set of b-roll stills, a set of transparent elements. A job that
depends on another's output starts the moment that output is in, not
after the whole batch is done. Never wait with `sleep` or a polling loop.

## 2. Hosting local files

Every model input that is an image, a video, or audio must be a public
HTTPS URL. Three cases:

- **The file came from a job.** Its result URL is already hosted. Pass
  that URL straight into the next job. Never host a job's output.
- **The file is already hosted on Spira**: its URL starts with
  `https://static.viralwell.ai/`, like the logo and product images the
  request gives from the brand's records. Use that URL as is. Never
  host it again.
- **The file exists only on disk** (a frame cut locally, a re-encoded
  clip, a persistent avatar, a file given only as a local path). Host
  it with the `host_file` tool (`worker_tools`), `path` as the local
  file path; the URL it returns is the job's input. Never upload
  through the `spira` CLI.

Host only what a job actually needs, at the moment it needs it.
Record the returned URL in the asset's metadata entry as `url`.

## 3. Tool map

| Step | Model ID | Credits |
|------|----------|---------|
| Persona base image | `ai-influencer-image` | 7 per image |
| Persona clean-up edit | `gpt-image-2` | 4 (1K), 5 (2K), 8 (4K) |
| Transparent-background element | `gpt-image-2` | same |
| Stock still for b-roll | `gpt-image-2` | same |
| Talking-head clip | `gemini-omni-flash-1.1` | per clip, see 3e (41 to 81; 108 with a video input) |
| Talking-head clip, fallback only (whole video, 3e) | `seedance-1.5-pro` | per second, see 3e |
| Talking-head cut-out | `pixelcut-video-background-removal` | 2.2 per source second |
| Background music | `suno-music` | 7 per track |
| Avatar motion control, persona driven by a reference video | `kling-3.0-motion-control` pro | 9.52 per second |
| Video from a reference or an image, person replacement (Cloner, Re-skit; approved by the owner 2026-10-24) | `wan-3.0` | 6.18 per second at 720p, 12.35 at 1080p (3.09 at 480p); wait with `timeoutSec` 600 (the maximum) and call `wait_ai_job` again while it reports `stillRunning` |
| Sound effect from a prompt (Cloner, Re-skit) | `elevenlabs-sound-effects` | 12 per generation |
| Persistent avatar voice (only with an avatar in the request, 3i) | `elevenlabs-text-to-speech` | 0.01 per character |
| Persistent avatar talking head (only with an avatar in the request, 3i) | `heygen-avatar-4` | 10 per second |
| Narrator voice-over (only for a video with no talking head, 3j) | `elevenlabs-text-to-speech` | 0.01 per character |

The toolkit is shared by every video designer. The talking-head steps (3a, 3b, 3e, 3f, 3h,
3i) are used only by a style that has a talking head; a style with none skips them.

## 3a. Persona base image: `ai-influencer-image`

This is Higgsfield Soul. It is the first step of every persona and is
never skipped: no other model produces the base likeness.

**The one exception: the user provides the image.** WHEN the user
hands over an image and says to use it as the avatar or the talking
head, skip Soul entirely. That image is the base likeness. Host it
(section 2) and go straight to the clean-up edit in 3b with it as the
reference, exactly as a Soul output would be. Do not generate a
persona of your own beside it, and do not run Soul to "match" it.

Payload (`submit_ai_job`, `modelId` `ai-influencer-image`):
`{"prompt":"<persona description>","size":"9:16","resolution":"1080p"}`.

Inputs: `prompt` (required), `size` (default `9:16`; also 16:9, 4:3,
3:4, 1:1, 2:3, 3:2), `resolution` (`720p` or `1080p`; use `1080p`).

Caveat: the likeness is realistic but the output is raw, with visible
blur. It is never used directly. Its purpose is to be the reference
for step 3b, which is mandatory.

## 3b. Persona clean-up edit: `gpt-image-2`

Takes the Soul output, or the user's own avatar image when one was
provided, as the reference and returns the production-ready persona
image.

Payload (`submit_ai_job`, `modelId` `gpt-image-2`):
`{"prompt":"<edit instruction>","referenceImage":["<soul result url>"],"size":"9:16","resolution":"2K"}`.

The prompt must:

- Say to keep the exact same person, face, hair, skin, and build as the
  reference, and to sharpen and clean it, removing blur and artefacts.
- **Give headspace above the head.** State it plainly: the whole head
  and hair sit fully inside the frame with clear empty space above them;
  nothing is cropped at the top. Without this line the model crops the
  crown, and the image is useless as a talking-head reference.

**With a product, the edit is the same.** The persona image never
holds or wears the product: the edit takes the Soul output alone, exactly
as when there is no product. The product enters later, in the
talking-head clip, as its second reference (3e).

Inputs: `prompt` (required), `referenceImage` (array of URLs), `size`
(default `auto`; also 1:1, 9:16, 16:9, 4:3, 3:4), `resolution` (`1K`,
`2K`, `4K`). Unsupported combinations: `auto`+`2K`, `auto`+`4K`,
`1:1`+`4K`. Use `9:16` with `2K` for the persona.

## 3c. Transparent-background elements: `gpt-image-2`

For any cut-out element that will sit on the stage: props, icons,
objects, stickers.

Payload (`submit_ai_job`, `modelId` `gpt-image-2`):
`{"prompt":"<element>, on a fully transparent background, PNG with alpha, no backdrop, no shadow on the ground, no frame","size":"1:1","resolution":"1K"}`.

The prompt must say transparent background explicitly, in those words.
It does not happen by default, and a white or grey backdrop cannot be
keyed cleanly afterwards. Check the downloaded PNG actually has an alpha
channel before using it.

**More than one element is one generation.** IF the video needs several
elements, generate them in one image laid out as a grid of equal
sections, one element in each section (the prompting skill gives the
format), at `2K` so each keeps enough pixels once cut out. Then cut them
apart, giving the same grid:

```bash
python3 <shared>/tools/crop-elements.py <sheet.png> <materials folder>/elements --grid <cols>x<rows>
```

It cuts each section and trims it to its element, saving `element-01.png`
onward, left to right, then top to bottom, the order the prompt listed
them in. It skips an empty section and prints each file with its section,
so you can tell which is which.
The sheet itself goes to deletable once the elements are cut.

## 3d. Stock stills for b-roll: `gpt-image-2`

For scene images that serve as stock photography behind or beside the
talking head.

Payload (`submit_ai_job`, `modelId` `gpt-image-2`):
`{"prompt":"<scene>, photographic, natural light","size":"9:16","resolution":"2K"}`.

Use `9:16` for full-bleed stage backgrounds, `16:9` for inset shots.
A single full-screen shot is generated at `2K`: at `1K` a 9:16 image
comes back at only 640 x 1136, below the 1080 x 1920 canvas, and looks
soft.

**More than one full-screen shot is one generation.** IF the video needs
two or more full-screen shots, generate them together as one collage:
`9:16` at `4K`, which comes back at 2160 x 3840, a 2 x 2 grid of four
shots at exactly the canvas size each. The shots meet edge to edge with
no gaps, no borders, no strokes, and no outlines between them (the
prompting skill gives the format). One 4K generation costs 8 credits,
less than two separate 2K ones (10). Then split it:

```bash
python3 <shared>/tools/split-collage.py <collage.png> <materials folder>/shots
```

It cuts each shot along its real seams, which the generator can place a
few pixels off the grid lines, and saves `shot-1.png` onward at exactly
1080 x 1920, left to right, then top to bottom. For more than four
shots, generate a second collage. The collage itself goes to deletable
once the shots are cut.

## 3e. Talking-head clip: `gemini-omni-flash-1.1` (Seedance 1.5 Pro only as the fallback)

Animates the cleaned persona image into a speaking clip. **Gemini Omni
1.1 Flash (`gemini-omni-flash-1.1`) makes every talking-head clip.** In
this skill "Omni" always means that model. Never use `gemini-omni-video`:
it is retired from the Spira CLI (since 0.0.26) and a job with it fails.
Seedance 1.5 Pro is the fallback, used only when Omni fails, and then for
the whole video.

**One model per video.** Every talking-head clip of a video comes from
the same model. Never make some chunks with Omni and the failed ones with
Seedance: the face, the voice, and the look change from clip to clip and
every cut shows it.

- An Omni job fails: `wait_ai_job` returns the provider's error.
  Run that chunk once more with Omni.
- IF it fails again, or Omni is down or refuses the persona, **switch
  the whole video to Seedance**: move every Omni `th-*` file to
  deletable (their credits stay recorded in the metadata), chunk the
  script again with `--model seedance`, and make **every** chunk with
  Seedance, including the ones Omni already delivered.
- IF Seedance fails as well, stop: that is a FAILED video (to Atlas) or a
  question for the user. Never go back to mixing.

### Checking each clip for cut-off speech

Omni sometimes ends a clip's speech early and drops the last words of its
line (e.g. a 30-word, 8-second chunk lost its last 7 words). Check every
talking-head clip as soon as it arrives, before it goes on the stage:

```bash
python3 <shared>/tools/make-timings.py <clip.mp4> --txt <materials folder>/deletable/clip-check --language <code> --prompt "<brand, product, and other names in the line>"
```

It writes `<clip>.txt` there, transcribed with local Whisper.

Compare that text with the chunk's `text` in `chunks.json`. A word heard
differently (a brand name, a similar-sounding word) is **not** a
cut-off: it is spoken, and the rule on wrong wording in the designer's
skill applies. A **cut-off** is words missing from the speech: the
transcript stops before the line's last words, or skips a phrase.

On a cut-off, this order, at most **two extra generations** for that
chunk, never more:

1. **Regenerate once:** the same chunk, the same text, duration, model,
   and prompt.
2. **IF it is still cut off,** shorten **only that chunk's line**: keep
   its meaning, its sentence ends, and its place in the script; drop or
   tighten words until it reads at about 4.5 syllables per second of
   speaking time (Omni: the clip length minus 1 s) for the same clip
   length. Put the new wording in `script.txt` too, so the
   captions and the voice-over timings match, and generate it once.
3. **IF it is still cut off,** stop regenerating. Keep the most complete
   take, make the captions match exactly what is spoken, and say so in
   your final line (e.g. `READY <path> (clip 5 cut off after 2 retries)`).

Record every extra generation and its credits in the metadata. Never
slow the whole script down to prevent this: the other chunks keep their
pace.

### Chunking by syllables

Clips come only in fixed lengths: Omni **4, 6, 8, or 10** seconds,
Seedance 4, 8, or 12. The script is split into chunks, each spoken in one
clip, at **4.9 to 5.2 syllables per second of speaking time**. Omni leaves
about **1 second of silence in every clip** (about 0.6 s before the speech
and 0.4 s after; the owner's finding, 2026-10-22), so an Omni clip's
speaking time is its length minus 1 s: a 6-second clip has 5 seconds to
speak. Seedance has no such pad. Never chunk by hand or by word count; the
chunker does it and applies the pad:

```bash
python3 <shared>/tools/chunker.py <materials folder>/script.txt <materials folder>/chunks.json
```

- It never changes the script. It splits only at sentence ends, groups
  sentences into chunks, and gives each chunk the clip length that puts
  it at 4.9 to 5.2 syllables per second. Where no grouping can, it uses
  4.0 to 5.2 and marks the chunk `[fallback]`. It never goes over 5.2:
  above that, Omni cuts the line off. A chunk marked `[UNDER 4.0: silence
  risk]` is its last resort; the speech may end before the clip does.
- It prints one line per chunk and writes `chunks.json`: each chunk's
  `text` and `duration`. Each chunk is one clip, with exactly that text
  and that duration.
- It counts syllables by rule. A brand or product name, or any word the
  speech is told to say differently (the Reword table), can be
  miscounted. Count such a word as it is said and pass the counts in a
  JSON script instead of `script.txt`:
  `{"text": "<the script>", "syllables": {"cookiy": 2}}`.
- IF it stops with `sentence N alone is over 47 syllables; split it`
  (Omni; 62 for Seedance), that sentence is too long for one clip. In the JSON script,
  end it at its natural break (a full stop where the comma or clause
  break is), without changing a word, and run it again.
- For the Seedance fallback, add `--model seedance`: it plans 4, 8, and
  12 second clips instead.

`chunks.json` is a working file; move it to deletable when the clips are
in.

### The Omni job

Payload (`submit_ai_job`, `modelId` `gemini-omni-flash-1.1`):
`{"prompt":"<line and delivery>","referenceImage":["<persona result url>"],"duration":"<4|6|8|10>","size":"9:16","resolution":"1080p"}`.

Inputs: `prompt` (required; the spoken line goes in it, in the
prompting skill's format), `referenceImage` (the persona; with a product,
the persona first and the product second), `duration` (`4`, `6`, `8`, or
`10`, from `chunks.json`), `size` (**always `9:16`**; Omni's default is
16:9), `resolution` (**always `1080p`**; Omni's default is 720p, at the
same price). Omni makes the speech itself: there is no `sound` input. Its
other inputs (`referenceVideo`, `characterIds`, `audioProfileIds`,
`voicePresetId`, `seed`) are not used unless the user names them.

**With a product.** The persona image never holds or wears the product
(3b). The product goes into the clip instead, decided by what it is:

- **An outfit** (clothing, shoes, jewellery, anything worn): the person
  is **wearing** it.
- **An object** (anything that can be held): the person is **holding**
  it, with one simple interaction.
- **Neither** (a logo, an app screen, a service, anything that cannot be
  worn or held): it is **not used** in the clip. The clip is made exactly
  as without a product.

When it is worn or held, `referenceImage` is
`["<persona url>","<product image url>"]`, the product image a hosted URL
(section 2), and the prompt follows the prompting skill's product
format.

Cost per clip at 1080p (the same price at 720p and 360p, so always
1080p):

| Duration | Credits |
|----------|---------|
| 4 s | 41 |
| 6 s | 54 |
| 8 s | 68 |
| 10 s | 81 |
| Any clip with a `referenceVideo` (a fix of an earlier clip) | 108 flat |

Per second, the 10 s clip is the cheapest (8.1) and the 4 s the
dearest (10.25), so fewer, longer clips cost less; the chunker already
weighs this.

### All chunks are one batch, never one clip at a time

Running the clips serially is the single biggest waste of time in the
kit. The step is: write every prompt and payload first, submit them all,
wait for them all, then hand them all to Pixelcut the same way (3f). Do it
exactly like this:

1. Write one payload file per chunk into the video's materials folder,
   `th-01.json`, `th-02.json`, and so on, each holding the full
   `--inputs-json` object for that chunk: its text in the prompt, its
   `duration` from `chunks.json`. No job is submitted until every payload
   file exists.
2. Submit them all with `submit_ai_job` in one message, one call per
   payload (`modelId` `gemini-omni-flash-1.1`, `inputs` the payload file's
   object), and write each returned `jobId` to `th-NN.pending`.

3. Wait for them all with `wait_ai_job` in one message, one call per
   `jobId`, then download each result URL with the `ai` tool's download
   action as `th-NN.mp4` and keep the URL as `th-NN.url`. Never use
   `curl` or `wget`.

4. Only then move to the cut-outs: every clip goes to Pixelcut in the same
   batched form, never one at a time.

Payload, pending, and url files are working files; move them to deletable
when the clips are in.

### Seedance 1.5 Pro: the fallback only

Used only after a switch under the one-model rule, and then for every
chunk of the video. Chunk with `chunker.py --model seedance`, write the
payloads under the same `th-NN` names (the Omni files are already in
deletable), and run the same batch steps with `seedance-1.5-pro` in
place of `gemini-omni-flash-1.1`.

Payload (`submit_ai_job`, `modelId` `seedance-1.5-pro`):
`{"prompt":"<line and delivery>","referenceImage":["<persona result url>"],"duration":"8","size":"9:16","resolution":"1080p","sound":true}`.

Inputs: `prompt` (required), `referenceImage` (up to 2 public URLs: the
persona, then the product when there is one), `duration` (`4`, `8`, or
`12`, nothing else), `size` (default `9:16`), `resolution` (`480p`,
`720p`, `1080p`), `sound` (boolean, `true`). `referenceAudio` and
`referenceVideo` are not supported; the spoken line goes in the prompt.

Cost per second at `standard`:

| Resolution | Sound off | Sound on |
|------------|-----------|----------|
| 480p | 0.88 | 1.75 |
| 720p | 1.97 | 3.94 |
| 1080p | 4.43 | 8.86 |

An 8-second 1080p clip with sound is about 71 credits. Use `1080p`.

## 3f. Talking-head cut-out: `pixelcut-video-background-removal`

Removes the background from the talking-head clip so the talking head can
sit on the stage with real transparency. Pixelcut is the only cut-out
model; never use `bria-video-background-removal` (replaced by the owner's
decision, 2026-10-20).

Payload (`submit_ai_job`, `modelId` `pixelcut-video-background-removal`):
`{"referenceVideo":["<clip result url>"],"mode":"Transparent"}`.

Inputs: `referenceVideo` (exactly one public URL, up to **100 MiB** and
**60 seconds**, no prompt) and `mode` set to `Transparent`. Nothing else:
`preserveAudio` and `autoZoom` are not supported. The frame stays aligned
with the source clip.

**Size and length limits.** Check the clip before submitting. IF it is
over 100 MB, re-encode it below that, host the result (section 2), and
submit that URL instead:

```bash
ffmpeg -y -i <clip> -c:v libx264 -crf 20 -preset fast -c:a copy <clip>-small.mp4
```

A clip over 60 seconds is rejected at submit: split it and run each part.

**`mode` is always `Transparent`.** It outputs VP9 WebM with a real alpha
channel; every colour mode (Black, White, Green, Blue, Magenta) outputs a
solid-background H.264 MP4 and is never used. Never add a chroma-key step;
the WebM is the cut-out.

**The cut-out has no audio.** Pixelcut drops the sound. The talking
head's speech comes from the original clip (`th-NN.mp4`, same timing and
length as its cut-out): wherever the speech audio is needed, take it from
that clip, never from the WebM.

Cost is 2.2 credits per source second.

**All cut-outs are one batch, exactly like the clips.** Never remove
backgrounds one clip at a time. With every talking-head clip in and
its `.url` file written (3e step 3), submit every cut-out at once with
`submit_ai_job` (`modelId` `pixelcut-video-background-removal`, the
clip's hosted URL from its `.url` file as `referenceVideo`, in one
message), then wait for them all with `wait_ai_job` in one message and
download each result as `th-NN-cut.webm`.

Then run the alpha check on every `.webm`.

**Confirm the alpha on the downloaded file** before using it:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,pix_fmt:stream_tags=alpha_mode -of default=nw=1 <file>.webm
```

Correct output shows `codec_name=vp9` and `TAG:ALPHA_MODE=1`.
`pix_fmt` reads `yuv420p` even with alpha present; the tag is the
proof, not the pixel format. To look at the frames with ffmpeg, decode
with `-vcodec libvpx-vp9`; the default VP9 decoder drops the alpha plane
and the cut-out looks opaque.

The WebM goes on the stage as a `<video>` element, never as extracted
frames: see stage-canvas-html, rule 11.

**The cut-out output is final.** Once the alpha check passes, use the
WebM as it is. Do not mask, matte, crop, re-key, or otherwise adjust
it. Pixelcut decides what belongs to the subject; if it keeps an object
the person is holding or touching, such as a laptop, a phone, or a mug,
that object is part of the cut-out and stays. It is not a defect to
fix. The only reasons to touch the result are a failed alpha check or
the user asking for a change.

## 3g. Background music: `suno-music`

Generates the music bed that sits under the VO and the talking head.
The CLI offers one Suno version, `v5_5`, and that is the one used.

Payload (`submit_ai_job`, `modelId` `suno-music`):
`{"mode":"v5_5","customMode":true,"instrumental":true,"style":"<style>","title":"<title>"}`.

Inputs: `mode` (`v5_5`, the only value), `customMode` true,
`instrumental` true, `style` (required in custom mode; the genre, mood,
tempo, and instruments in a few words), `title` (required in custom
mode; any short name). No `prompt`: in custom mode the prompt is
lyrics, and there are none.

**Always instrumental. Never lyrics.** (One exception, the owner's rule of 2026-10-24: the Cloner and Re-skit may decide for themselves to add vocals when the video needs them, e.g. when the source is a song.) Sung words clash with the VO and
the talking head's speech; the two voices fight and neither is
intelligible. `instrumental` only takes effect in custom mode, which is
why the command sets `customMode` true rather than using simple mode.
Simple mode with a description that says instrumental is not enough;
the model can still add vocals.

Cost is 7 credits per generation. Save the result as `bgm.mp3` in the
video's materials folder and point the editable's `#bgm` source at it.

## 3h. Avatar motion control: `kling-3.0-motion-control`

Transfers the motion of a reference video onto the persona image: the
persona moves the way the person in the reference video moves, while
keeping the persona's identity. The latest Kling motion-control model
in the CLI is 3.0, and that is the one used.

**For the avatar only.** Motion control drives a person. It is never
used to animate graphics, props, products, text, or b-roll stills;
those are not motion-controlled by anything in this kit.

Payload (`submit_ai_job`, `modelId` `kling-3.0-motion-control`):
`{"prompt":"<optional guidance>","referenceImage":["<matching image url>"],"referenceVideo":["<motion clip url>"],"characterOrientation":"image","duration":"<clip length>","mode":"pro","sound":false}`.

Inputs: `referenceImage` (exactly one URL, the persona),
`referenceVideo` (exactly one URL, the motion source),
`characterOrientation` (`image`: the identity comes from the image and
the motion from the video; `video` reverses that), `duration` (3 to 15
by the second, then 20, 25, 30; it is the billing length, and the
motion itself follows the reference video), `mode` is `pro`, `prompt`
(optional), `sound` (keep the reference video's own audio; false unless
asked). Both references must be hosted URLs (section 2).

Cost is 9.52 credits per second in pro. A 5 second clip is about 48
credits.

**Procedure when a source video's motion is to be copied.**

1. **Make the matching image first.** Generate an image of the avatar
   in the same position as the person in the source at the moment the
   copied motion begins: same pose, same framing, same side to camera.
   Use the persona edit (3b) with the persona as reference and describe
   the position. You decide what that image is from what is being
   copied; the model needs a start that already matches, or the
   transfer fights it.
2. **Clip only the portion to be mimicked.** Cut the source down to the
   motion itself, nothing before or after:

   ```bash
   ffmpeg -y -ss <start> -to <end> -i <source> -an -c:v libx264 -crf 17 <clip>.mp4
   ```

3. **One clip and one image per motion.** If the source holds several
   motions that differ in context, cut each one out separately, make a
   matching image for each, and run each as its own job. You decide how
   many cuts from how the motions differ.
4. **If a clip is too short, extend it, then trim the output.** The
   model needs at least 3 seconds. Hold the last frame to reach it, run
   the job at that length, and cut the returned video back to the real
   motion length:

   ```bash
   ffmpeg -y -i <clip>.mp4 -vf tpad=stop_mode=clone:stop_duration=<seconds to add> -c:v libx264 -crf 17 <clip>-ext.mp4
   ffmpeg -y -i <output>.mp4 -t <real length> -c:v libx264 -crf 17 -c:a copy <output>-trim.mp4
   ```

5. Host the clip (section 2), set `duration` to the clip's length, and
   run. Rejected clips, extended intermediates, and untrimmed outputs go
   to deletable per file-management.

Kling 2.6 motion control (`kling-2.6-motion-control`) also exists. It
requires a prompt, takes a 3 to 30 second reference video, and sets the
output resolution (720p at 5.5 per second, 1080p at 9) instead of a
mode. It is not used unless the user names it.

## 3i. Persistent avatar (given in the request)

WHEN the request gives an **avatar image** and an **avatar voice**
(`Use this avatar image: ...` and `Use this avatar voice: elevenlabs
<voice ID> <model>`), that avatar is the talking head. Skip the Higgsfield
Soul persona step (3a), the GPT Image 2 persona edit (3b), and the
Omni or Seedance talking-head clips (3e). Instead:

1. **Speech.** Make the voice-over with ElevenLabs, the full approved
   script as the text, with the voice ID and model from the request:

   Payload (`submit_ai_job`, `modelId` `elevenlabs-text-to-speech`):
   `{"text":"<full approved script>","voiceId":"<voice ID>","providerModelId":"<model>"}`.

   Download the result as `vo.mp3` into the materials folder. Its result
   URL is already hosted, so pass it straight to HeyGen.
2. **Talking head.** Host the avatar image if it is only a local path
   (section 2), then make the talking head with HeyGen, driven by that
   speech:

   Payload (`submit_ai_job`, `modelId` `heygen-avatar-4`):
   `{"referenceImage":["<avatar image url>"],"referenceAudio":["<vo.mp3 url>"],"size":"9:16","resolution":"1080p"}`.

No chunking: the full script is one speech file and one HeyGen job, not
split into clip-length pieces; the chunking in 3e does not
apply. Credits: ElevenLabs 0.01 per character of the script; HeyGen 10
per second of the clip. The HeyGen output is the talking head and goes
through the rest of the pipeline (cut-out, stage) as any talking-head
clip would.

## 3j. Narrator voice-over (no talking head)

WHEN the video has no talking head (an explainer), the script is spoken
by a narrator: one voice-over made with ElevenLabs, the full approved
script as the text.

Payload (`submit_ai_job`, `modelId` `elevenlabs-text-to-speech`):
`{"text":"<full approved script>","voiceId":"<voice ID>","providerModelId":"<model>"}`.

The voice comes only from the request (`Use this voice: elevenlabs
<voice ID> <model>` in its instructions). IF it gives none, stop and
ask; never pick one yourself. Download the result as `vo.mp3` into the materials
folder. No chunking: the full script is one speech file. Credits: 0.01
per character of the script.

## 4. Do not use

Anything not listed above, including other image models
(`nano-banana-*`, `seedream-*`, `flux-kontext`), other video models
(`kling-*` other than 3.0 motion control, `seedance-2.*`, `veo3.1`), and
any lip-sync route. `heygen-avatar-4` and `elevenlabs-text-to-speech` are
used only for a persistent avatar given in the request (3i), for a
narrator voice-over (3j). If a step seems to need a tool this document does not
name, stop and ask the user rather than picking one.

The one exception is a model the user names explicitly in their
request. Then use that model for that request as asked, pull its inputs
and prices with `spira ai models get <modelId>`, and state the cost
before running. This is the user's call, never a suggestion from you.
