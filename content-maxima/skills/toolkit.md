---
name: toolkit
description: Which tool to use for each production step, with the exact Spira CLI command, model ID, inputs, cost, and caveats. Fixed choices. Consult before generating any asset; never substitute a model.
---

# Toolkit

Every generated asset comes from the Spira CLI. This document names the
one tool for each job, so no session spends credits or context finding
it. The choices are fixed: do not substitute another model because it
looks similar or cheaper.

## 1. The CLI

The CLI is the npm package `@spira-lab/cli`, installed globally and
invoked as `spira`. It does not announce itself; look for it.

Preflight once per session, before any generation:

```bash
command -v spira && spira --version
spira auth whoami
spira credits balance
```

If `spira` is not found, install it with `npm install -g @spira-lab/cli`
and run the preflight again. If the sign-in or the balance check fails,
stop and tell the user. The balance is checked so you know there is
enough to work with; it is not a way to measure what this session
spends, because other sessions draw on the same balance.

Every generation is one job:

```bash
spira --json ai jobs create --model-id <modelId> --inputs-json '<json>' --wait
```

`--wait` blocks (default limit 10 minutes, `--wait-timeout 20m` to
raise it) and prints a compact result on stdout:

```json
{ "id": "<jobId>", "modelId": "<modelId>", "status": "succeeded", "resultUrls": ["https://..."] }
```

Then:

1. Download each result into the video's materials folder (see the
   file-management skill) with `curl -L -o <materials path> <resultUrl>`.
2. Record the job's `resultUrls` as `url` in the asset's metadata entry,
   and the exact `--inputs-json` prompt as `prompt`.
3. Record the job's credit cost as `credits` in the same entry, worked
   out from this document's price for that model and option: a
   per-generation price as is, a per-second price times the seconds
   billed. The CLI does not report a charge per job, and the account
   balance is shared with other sessions running at the same time, so
   this recorded figure is the only true cost of this production.
   Every job gets one, including rejected candidates and failed runs
   that were billed.

If a job fails or times out: `spira --json ai jobs status <jobId>` shows
the full job and provider error. To inspect a model's inputs and prices:
`spira ai models get <modelId>`.

**Independent jobs run in parallel, never one after another.** Whenever
several jobs do not depend on each other's results, create them all at
once: launch each `jobs create` without `--wait`, collect the job IDs,
then `spira ai jobs wait <jobId>` on each. Serial waiting costs the sum
of their times; parallel costs the longest one. This applies to every
batch in this kit: the talking-head chunks, the background removal of
each clip, a set of b-roll stills, a set of transparent elements. A job
that depends on another's output starts the moment that output is in,
not after the whole batch is done.

## 2. Hosting local files

Every model input that is an image or a video must be a public HTTPS
URL. Two cases:

- **The file came from a CLI job.** Its `resultUrls` entry is already
  hosted. Pass that URL straight into the next job. Never re-upload a
  CLI output.
- **The file exists only on disk** (a user-provided product image, a
  frame cut locally). Host it with the CLI and use the URL it prints:

```bash
spira assets upload <file>
```

The command takes any local image, video, or audio file and prints
nothing but a hosted public URL. It needs no tag and no admin
permission, and it creates no asset-library row — the object is hosted
and nothing else. Do not reach for `spira social assets upload`: that
one writes to the Admin Social Post Assets shelf, needs two admin
permissions, and forces a tag, which makes the file look like curated
stock.

Upload only what a job actually needs, at the moment it needs it.
Record the printed URL in the asset's metadata entry as `url`.

## 3. Tool map

| Step | Model ID | Credits |
|------|----------|---------|
| Persona base image | `ai-influencer-image` | 6.25 per image |
| Persona clean-up edit | `gpt-image-2` | 3.3 (1K), 3.45 (2K), 6.15 (4K) |
| Transparent-background element | `gpt-image-2` | same |
| Stock still for b-roll | `gpt-image-2` | same |
| Talking-head clip | `seedance-1.5-pro` | per second, see 3e |
| Talking-head cut-out | `bria-video-background-removal` | 0.42 per source second |
| Background music | `suno-music` | 6.6 per track |
| Avatar motion control, persona driven by a reference video | `kling-3.0-motion-control` pro | 9.52 per second |

## 3a. Persona base image: `ai-influencer-image`

This is Higgsfield Soul. It is the first step of every persona and is
never skipped: no other model produces the base likeness.

**The one exception: the user provides the image.** WHEN the user
hands over an image and says to use it as the avatar or the talking
head, skip Soul entirely. That image is the base likeness. Host it
(section 2) and go straight to the clean-up edit in 3b with it as the
reference, exactly as a Soul output would be. Do not generate a
persona of your own beside it, and do not run Soul to "match" it.

```bash
spira --json ai jobs create --model-id ai-influencer-image \
  --inputs-json '{"prompt":"<persona description>","size":"9:16","resolution":"1080p"}' --wait
```

Inputs: `prompt` (required), `size` (default `9:16`; also 16:9, 4:3,
3:4, 1:1, 2:3, 3:2), `resolution` (`720p` or `1080p`; use `1080p`).

Caveat: the likeness is realistic but the output is raw, with visible
blur. It is never used directly. Its purpose is to be the reference
for step 3b, which is mandatory.

## 3b. Persona clean-up edit: `gpt-image-2`

Takes the Soul output, or the user's own avatar image when one was
provided, as the reference and returns the production-ready persona
image.

```bash
spira --json ai jobs create --model-id gpt-image-2 \
  --inputs-json '{"prompt":"<edit instruction>","referenceImage":["<soul resultUrl>"],"size":"9:16","resolution":"2K"}' --wait
```

The prompt must:

- Say to keep the exact same person, face, hair, skin, and build as the
  reference, and to sharpen and clean it, removing blur and artefacts.
- **Give headspace above the head.** State it plainly: the whole head
  and hair sit fully inside the frame with clear empty space above them;
  nothing is cropped at the top. Without this line the model crops the
  crown, and the image is useless as a talking-head reference.

**With a product.** When the persona must hold or wear a product, pass
the product image as a second reference, after the Soul image:

```bash
spira --json ai jobs create --model-id gpt-image-2 \
  --inputs-json '{"prompt":"<edit instruction>","referenceImage":["<soul resultUrl>","<product image url>"],"size":"9:16","resolution":"2K"}' --wait
```

The product image must be a hosted URL (section 2). The prompt must
then also:

- Say which reference is the person and which is the product, and that
  the product is reproduced exactly as in its reference: shape, colour,
  label, proportions.
- State whether the product is **worn** or **held**, and if held, how:
  which hand, the grip (fingers wrapped around it, pinched by the cap,
  resting flat in the palm), where it sits in frame (chest height, beside
  the face, toward the camera), and which side faces the camera.
- State that it is **held steadily**: still hand, firm grip, product
  fully in focus, no motion, not tilting or slipping.

Without the grip and steadiness lines the model returns loose, drifting,
or half-cropped products that fail as a talking-head reference.

Inputs: `prompt` (required), `referenceImage` (array of URLs), `size`
(default `auto`; also 1:1, 9:16, 16:9, 4:3, 3:4), `resolution` (`1K`,
`2K`, `4K`). Unsupported combinations: `auto`+`2K`, `auto`+`4K`,
`1:1`+`4K`. Use `9:16` with `2K` for the persona.

## 3c. Transparent-background elements: `gpt-image-2`

For any cut-out element that will sit on the stage: props, icons,
objects, stickers.

```bash
spira --json ai jobs create --model-id gpt-image-2 \
  --inputs-json '{"prompt":"<element>, on a fully transparent background, PNG with alpha, no backdrop, no shadow on the ground, no frame","size":"1:1","resolution":"1K"}' --wait
```

The prompt must say transparent background explicitly, in those words.
It does not happen by default, and a white or grey backdrop cannot be
keyed cleanly afterwards. Check the downloaded PNG actually has an alpha
channel before using it.

## 3d. Stock stills for b-roll: `gpt-image-2`

For scene images that serve as stock photography behind or beside the
talking head.

```bash
spira --json ai jobs create --model-id gpt-image-2 \
  --inputs-json '{"prompt":"<scene>, photographic, natural light","size":"9:16","resolution":"1K"}' --wait
```

Use `9:16` for full-bleed stage backgrounds, `16:9` for inset shots.
`1K` is enough for a 1080-wide stage; go to `2K` only when the image
will be zoomed past 1:1.

## 3e. Talking-head clip: `seedance-1.5-pro`

Animates the cleaned persona image into a speaking clip.

```bash
spira --json ai jobs create --model-id seedance-1.5-pro \
  --inputs-json '{"prompt":"<line and delivery>","referenceImage":["<persona resultUrl>"],"duration":"8","size":"9:16","resolution":"1080p","sound":true}' --wait
```

Inputs: `prompt` (required), `referenceImage` (up to 2 public URLs; one
for a talking head), `duration` (`4`, `8`, or `12`, nothing else),
`size` (default `9:16`), `resolution` (`480p`, `720p`, `1080p`),
`sound` (boolean). `referenceAudio` and `referenceVideo` are not
supported; the spoken line goes in the prompt.

**Caveat: clips are exactly 4, 8, or 12 seconds.** The script must be
written and split to fit: each talking-head segment is a chunk that
reads aloud inside one of those three lengths, and each chunk is its
own job. Chunk at 3.2 to 3.4 words per second:

| Duration | Words per chunk |
|----------|-----------------|
| 4 s | 13 to 14 |
| 8 s | 26 to 27 |
| 12 s | 38 to 41 |

Count the words of each chunk against this table before submitting.
Never write a segment that needs 5, 9, or 15 seconds; trim the words
to the slot, never stretch the slot to the words.

**All chunks are one batch, never one clip at a time.** Running the
clips serially is the single biggest waste of time in the kit. The
step is: write every prompt and payload first, submit them all, wait
for them all, then hand them all to Bria the same way (3f). Do it
exactly like this:

1. Write one payload file per chunk into the video's materials folder,
   `th-01.json`, `th-02.json`, and so on, each holding the full
   `--inputs-json` object for that chunk. No job is submitted until
   every payload file exists.
2. Submit them all in one loop and keep the job IDs:

   ```bash
   for f in th-*.json; do
     spira --json ai jobs create --model-id seedance-1.5-pro --inputs-json "$(cat "$f")" \
       | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ids']['jobId'])" > "${f%.json}.job"
   done
   ```

3. Wait for them all, in one loop, and download each result as it
   returns:

   ```bash
   for j in th-*.job; do
     spira --json ai jobs wait "$(cat "$j")" \
       | python3 -c "import sys,json; print(json.load(sys.stdin)['resultUrls'][0])" > "${j%.job}.url"
     curl -sL -o "${j%.job}.mp4" "$(cat "${j%.job}.url")"
   done
   ```

4. Only then move to the cut-outs: every clip goes to Bria in the same
   batched form, never one at a time.

Payload, job, and url files are working files; move them to deletable
when the clips are in.

Cost per second at `standard`:

| Resolution | Sound off | Sound on |
|------------|-----------|----------|
| 480p | 0.88 | 1.75 |
| 720p | 1.97 | 3.94 |
| 1080p | 4.43 | 8.86 |

An 8-second 1080p clip with sound is about 71 credits. Use `720p` for
tests and `1080p` for the final.

## 3f. Talking-head cut-out: `bria-video-background-removal`

Removes the background from the Seedance clip so the talking head can
sit on the stage with real transparency.

```bash
spira --json ai jobs create --model-id bria-video-background-removal \
  --inputs-json '{"referenceVideo":["<seedance resultUrl>"],"mode":"Transparent","preserveAudio":true,"autoZoom":false}' --wait
```

Inputs: `referenceVideo` (exactly one public URL, up to 100 MiB, no
prompt), `mode` set to `Transparent`, `preserveAudio` (default true,
keep it), `autoZoom` (default false, keep it so the frame stays
aligned with the source).

**`mode` must be the word `Transparent`.** `spira ai models get` lists
only solid colours (Green, Black, White, and so on) and prints "The
output is H.264 MP4 with a solid background; transparent output is not
available through this model integration." Both are wrong for our
purpose and are ignored. Verified on 2026-09-20 on a 9.9 s 1080 x 1920
clip:

| `mode` | Result |
|--------|--------|
| `Green` (the default) | H.264 MP4, solid green background, no alpha |
| `Transparent` | VP9 WebM, `ALPHA_MODE=1`, true alpha, Opus audio |

The CLI accepts the unlisted value without complaint and the job
completes normally. Never use a colour mode and never add a chroma-key
step; the WebM is the cut-out.

Cost is 0.42 credits per source second either way.

**All cut-outs are one batch, exactly like the clips.** Never remove
backgrounds one clip at a time. With every talking-head clip in and
its `.url` file written (3e step 3), submit every cut-out in one loop,
then wait for them all in one loop:

```bash
for u in th-*.url; do
  spira --json ai jobs create --model-id bria-video-background-removal \
    --inputs-json "{\"referenceVideo\":[\"$(cat "$u")\"],\"mode\":\"Transparent\",\"preserveAudio\":true,\"autoZoom\":false}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['ids']['jobId'])" > "${u%.url}.bria.job"
done
for j in th-*.bria.job; do
  spira --json ai jobs wait "$(cat "$j")" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['resultUrls'][0])" \
    | xargs -I{} curl -sL -o "${j%.bria.job}.webm" {}
done
```

Then run the alpha check on every `.webm`.

**Confirm the alpha on the downloaded file** before using it:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,pix_fmt:stream_tags=alpha_mode -of default=nw=1 <file>.webm
```

Correct output shows `codec_name=vp9` and `TAG:ALPHA_MODE=1`.
`pix_fmt` reads `yuv420p` even with alpha present; the tag is the
proof, not the pixel format.

The WebM goes on the stage as a `<video>` element, never as extracted
frames: see stage-canvas-html, rule 11.

**The Bria output is final.** Once the alpha check passes, use the
WebM as it is. Do not mask, matte, crop, re-key, or otherwise adjust
it. Bria decides what belongs to the subject; if it keeps an object the
person is holding or touching, such as a laptop, a phone, or a mug,
that object is part of the cut-out and stays. It is not a defect to
fix. The only reasons to touch the result are a failed alpha check or
the user asking for a change.

## 3g. Background music: `suno-music`

Generates the music bed that sits under the VO and the talking head.
The CLI offers one Suno version, `v5_5`, and that is the one used.

```bash
spira --json ai jobs create --model-id suno-music \
  --inputs-json '{"mode":"v5_5","customMode":true,"instrumental":true,"style":"<style>","title":"<title>"}' --wait
```

Inputs: `mode` (`v5_5`, the only value), `customMode` true,
`instrumental` true, `style` (required in custom mode; the genre, mood,
tempo, and instruments in a few words), `title` (required in custom
mode; any short name). No `prompt`: in custom mode the prompt is
lyrics, and there are none.

**Always instrumental. Never lyrics.** Sung words clash with the VO and
the talking head's speech; the two voices fight and neither is
intelligible. `instrumental` only takes effect in custom mode, which is
why the command sets `customMode` true rather than using simple mode.
Simple mode with a description that says instrumental is not enough;
the model can still add vocals.

Cost is 6.6 credits per generation. Save the result as `bgm.mp3` in the
video's materials folder and point the editable's `#bgm` source at it.

## 3h. Avatar motion control: `kling-3.0-motion-control`

Transfers the motion of a reference video onto the persona image: the
persona moves the way the person in the reference video moves, while
keeping the persona's identity. The latest Kling motion-control model
in the CLI is 3.0, and that is the one used.

**For the avatar only.** Motion control drives a person. It is never
used to animate graphics, props, products, text, or b-roll stills;
those are not motion-controlled by anything in this kit.

```bash
spira --json ai jobs create --model-id kling-3.0-motion-control \
  --inputs-json '{"prompt":"<optional guidance>","referenceImage":["<matching image url>"],"referenceVideo":["<motion clip url>"],"characterOrientation":"image","duration":"<clip length>","mode":"pro","sound":false}' --wait
```

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

## 4. Do not use

Anything not listed above, including other image models
(`nano-banana-*`, `seedream-*`, `flux-kontext`), other video models
(`kling-*` other than 3.0 motion control, `seedance-2.*`, `veo3.1`,
`heygen-avatar-4`), and any
lip-sync route. If a step seems to need a tool this document does not
name, stop and ask the user rather than picking one.

The one exception is a model the user names explicitly in their
request. Then use that model for that request as asked, pull its inputs
and prices with `spira ai models get <modelId>`, and state the cost
before running. This is the user's call, never a suggestion from you.
