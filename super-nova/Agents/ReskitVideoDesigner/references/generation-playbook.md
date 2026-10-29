# Generation playbook

Field knowledge for making the pieces of a skit. The shared toolkit (`DesignerShared/skills/toolkit.md`)
governs the submit_ai_job / wait_ai_job / host_file steps, hosting and every model it names; this
file adds what a re-skit needs on top. Prices change: read each model's price with
`spira ai models get <id>` (read-only), and that figure goes in the plan.

## What each tool is for

| Need | Model | Notes and live price (2026-10-24, check with `spira ai models get`) |
|---|---|---|
| A new persona's base image | `ai-influencer-image` (Soul) | 9:16, 1080p, ~7. Only when no persona exists (persona-and-outfits.md). |
| Persona clean-up, character sheet, outfit sheets, background plates, a prop | `gpt-image-2` | Edits from a reference image. 1K ~4, 2K ~5, 4K ~8. 16:9 4K for sheets, 9:16 2K for plates. |
| Replacing the person in a source clip | `wan-3.0`, `reference_to_video` | **Approved** (the owner, 2026-10-24). 720p 6.18/s, 1080p 12.35/s. Whole seconds, 2–30 s output; up to 15 s of reference video. 4–25 min per clip. |
| A shot that does not exist in the source | `wan-3.0`, `image_to_video` | From a still; a one-sentence prompt for the small movement. Same price. |
| A person speaking a new line | `gemini-omni-flash-1.1` | 4/6/8/10 s, 9:16, 1080p, the shared chunker's pace (below). Can't copy motion from a video. |
| Music | `suno-music`, custom mode | ~7 per job, two takes. Instrumental unless the video needs vocals (below). |
| Transcripts and checks | `make-timings.py` (Scribe, Whisper fallback) | About 1 credit a minute; it prints the credits. |

Nothing else: no other image or video model, no lip-sync route, no `gemini-omni-video` (retired).

## Running jobs

Every generation of a video is listed in one plan file, `materials/chain.json`, which you write
and update by hand. You submit and collect each job with the toolkit's `submit_ai_job` and
`wait_ai_job` steps (never the `spira` CLI, never a script), and host local inputs with
`host_file`. The file carries what a re-skit needs on top of a plain batch: jobs that wait on
other jobs' results (clips need the outfit and the plates), waits longer than one `wait_ai_job`
(Wan clips run up to 25 minutes: call it again on `stillRunning`), the outfit hold, the
2-extra-generations limit, and the credits of every job.

```json
{"jobs": [
 {"label": "outfit", "model": "gpt-image-2", "out": "assets/outfit_sheet.png", "hold": true, "expected_credits": 8,
  "inputs": {"size": "16:9", "resolution": "4K", "referenceImage": ["@/abs/.../personas/Mia/sheet_4k.png"], "prompt": "<outfit prompt>"}},
 {"label": "plate_a", "model": "gpt-image-2", "out": "assets/plate_a.png", "expected_credits": 5,
  "inputs": {"size": "9:16", "resolution": "2K", "referenceImage": ["@assets/src_a.png"], "prompt": "<plate prompt>"}},
 {"label": "clip_A", "model": "wan-3.0", "out": "gen/out/A.mp4", "needs": ["outfit", "plate_a"], "expected_credits": 25,
  "inputs": {"generationType": "reference_to_video", "duration": "4", "resolution": "720p", "size": "9:16", "sound": false,
             "referenceVideo": ["@gen/ref/A.mp4"], "referenceImage": ["{{outfit}}", "{{plate_a}}"], "prompt": "<clip prompt>"}},
 {"label": "music", "model": "suno-music", "out": "music/take.mp3", "expected_credits": 7,
  "inputs": {"mode": "v5_5", "customMode": true, "instrumental": true, "style": "<genre, sounds, tempo, energy>", "title": "<title>"}}
]}
```

- `@<path>` marks a local file: host it once with `host_file` and write the URL it returns in
  its place before submitting; a hosted URL (`https://static.viralwell.ai/...`, such as the
  request's logo or product image) passes as it is. `{{label}}` marks another job's result:
  that job waits, and you fill in its `resultUrls[0]` once it has landed. Never host a job's output.
- Each job entry also carries, as you update it: `status` (`pending`, `submitted`, `done`,
  `failed`), `job_id` (written the moment `submit_ai_job` returns it), `submissions` (how many
  times it was submitted), `credits` and `urls` once it lands, and `approved` on a `hold` job.
- **Parallel.** Submit every job whose `needs` are all `done` in one turn, one `submit_ai_job`
  call each, then wait on them all in one turn, one `wait_ai_job` call each with `saveTo` set to
  the job's `out` (a second result is saved beside it as `<name>-2.<ext>`; Suno's two takes are
  `take.mp3` and `take-2.mp3`). A job that depends on another starts the moment that one is in.
- A job with a `job_id` and no result is never submitted again; a job that is merely slow (some
  sit QUEUED for 20 minutes) is waited on, because a duplicate costs the full price again. After
  a restart, `wait_ai_job` every `submitted` job in `chain.json` first.
- A job that returns `FAILED` carries the provider's error: read it, fix the inputs in
  `chain.json`, and submit once more (a redo, counted below).
- **The outfit hold.** A `"hold": true` job keeps its dependents waiting until you have looked at
  its result and set `"approved": true`.
- **At most 2 extra generations per job** (the toolkit's rule): `submissions` never goes above
  3. A redo moves the current take to `deletable/` (keeping its name), marks its metadata asset
  `deletable` with the reason, and submits one more. When the limit is reached, keep the best
  take and say what is wrong in your final line.
- **Cost before spend:** `expected_credits` of every job (from `spira ai models get <id>`) is
  written into `chain.json` and the plan before the first submit, with the total.
- **Records.** The moment a job lands, add it to the metadata's `assets[]` (label, job ID, model,
  exact inputs and prompt, result URL, file, credits, where the credit figure came from), update
  `credits_total`, and append a row to the plan's job log (label, job ID, model, settings,
  credits, render time). A failed job's credits are what it reports, else 0, noted as such.
- Credits: the job's own charge when the result reports one, else the model's price for those
  inputs. Never the account balance: other sessions share it.

## Reference clips for person replacement

One clip per camera setup (`reskit.py probe` lists the scene changes). A clip must never
contain a cut: frame rounding at a shot boundary easily drags one frame of the next shot in, so
end each clip a few frames before the next cut. Cut each clip to a whole number of seconds
(that is the generation's duration) and a little longer than its slot, so the edit can trim to
the beat. When the usable part is shorter, the last frame is held to the whole second, trimmed
on the **input** side so the hold really happens. Audio stripped, 30 fps:

```
python3 <reskit>/tools/reskit.py cutref <source.mp4> <start> <usable_len> <whole_seconds> gen/ref/A.mp4 --mask assets/caption_mask.png
```

It prints the scene changes inside the clip and refuses one that has any.

**Burned-in text must go before upload**, because the video model redraws whatever text it
sees. Build a mask of only the text pixels, then mask with it:

```
python3 <reskit>/tools/reskit.py mask <source.mp4> assets/caption_mask.png <x0> <x1> <y0> <y1> [--th 228] [--dilate 14] [--times t1,t2,...]
```

It darken-blends frames from across the clip so the moving person drops out, keeps the bright
text inside the caption's box, and dilates generously: enough to cover the text's dark outline
or shadow too (with a thin dilation the letter shapes survive as dark ghosts). Check it: crop
the caption area of a frame and of the mask side by side. The result is a soft smear where the
letters were; the model repaints it as part of the person or set, and the new overlay usually
sits on the same spot anyway. Also say in the prompt "Remove the caption text from the … of the
frame, so there is no text on screen".

## Background plates

One plate per camera setup: a still from the source (`reskit.py still <video> <s> assets/src_a.png`,
a frame where the room is most visible), edited once with GPT Image 2. Describe the empty result
rather than the removal ("Show this same spot with nobody in it: no person, no hands and no
caption text"), keep the camera ("same camera position, height, angle, framing and lens
perspective"), name the fixed things that must stay (counter, door, bed, chair), then describe
the restyle in everyday words. Close with the casual phone look. A full restyle sometimes moves
the camera; that is fine for a video-model reference (the model takes the camera from the source
clip). If a plate must line up exactly with the source, ask only for a material swap: same
shapes, new colours and materials.

## The person-replacement prompt

The shape that keeps working: say what each reference is, what to replace, what changes, and
what to retain.

> Video 1 is the video, image 1 is a character sheet of the new person, image 2 is the
> background. Replace the girl in video 1 with the woman from image 1, wearing the [exact outfit]
> from image 1, with only the [accessory] from image 1. Replace the room with the room from
> image 2. Keep the camera and every movement, gesture and facial expression from video 1. She
> holds her phone as in video 1. Remove the caption text from the middle of the frame, so there
> is no text on screen.

What makes it hold:
- **Name the outfit in every clip.** Clips are generated independently; words keep them
  consistent alongside the sheet.
- **Name the accessories you want and say "only".** The source performer's jewellery leaks
  otherwise (a cross necklace, rings, a watch).
- **Name every prop the person holds**, and when a prop appears only part way through, say at
  what second. The request's product, when it can be held or worn, can replace the source's prop
  here (add the product image as a third reference and say "the [product] from image 3").
- **Never write "keep everything else exactly the same."** Name what is retained instead.
- **Describe the result, not the removal.**
- `"sound": false`: the clip's sound comes from the build, not from the model.

What it can't do: **a prompt can't replace a movement the reference clip contains.** Asked to
have the person text with both hands instead of raising a phone to her ear, the model kept the
arm going up to the ear *and* added a phone in both hands: three hands. When the source's action
doesn't fit the brand story, keep the action and change its meaning with text, cut the moment,
or make a new shot from a still (`image_to_video`).

**Check every clip against its source** the moment it lands:

```
python3 <reskit>/tools/reskit.py strip <source.mp4> gen/out/A.mp4 assets/check_A.jpg --offset <clip start>
```

Source frames above, clip frames below, at the same moments. Look for identity, the outfit on
every frame, the room, the props, hands, any leftover text, and that the motion lines up frame
for frame (the edit relies on the clip's timing matching the source's audio). Move check images
to `deletable/` once read. When the setup is new for this persona, the first clip can be read
alone before you rely on the rest; all clips still run in parallel.

## A new spoken line (rare)

A re-skit keeps the source's own voices. When the story truly needs a new line spoken on camera,
it is one Omni clip (`gemini-omni-flash-1.1`, 9:16, 1080p) from a still of the persona in the
outfit (a GPT Image 2 edit of the outfit sheet into one frame of the scene). Its pace is the
shared chunker's rule (the owner's rule, 2026-10-24): 4.9 to 5.2 syllables per second of
speaking time, the clip's length minus 1 s. Write the line to `materials/line.txt` and let the
chunker pick the length (`python3 <shared>/tools/chunker.py line.txt line-chunks.json`); never
pace it by hand. The prompt is the prompting skill's talking-head format. Check it for cut-off
speech with `make-timings.py --txt` as the toolkit says (3e), within the same 2-extra limit.

## B-roll and simulated screens

When the story needs to show the brand, build the b-roll; don't generate it. Video models
redraw screens into near-gibberish, so a product UI is rebuilt in HTML from the brand's real
material and rendered with headless Chrome through the shared playwright-core
(`node <reskit>/tools/render_html.js`).

**Copy the real thing.** Material the request provides always wins. Otherwise capture the
brand's public site yourself (`node <reskit>/tools/capture_site.js <url> <out dir> [--pages ...]
[--full]`; it hides cookie banners and never clicks or accepts anything). Save captures in
`client-assets/<BrandName>/brand/ui/<YYYY-MM-DD>/` and the chosen logo in `brand/logo/`, then
copy what this video uses into its `assets/`. Measure everything at the capture's native pixel
scale: header heights, avatar sizes, font sizes, greys, corner radii, spacing, how unread
messages are shown, how timestamps are written, what the reply box contains. Crop and reuse real
pixels where possible (status bar, header, navigation bar), and build the rest to the same
measurements. Populate it with the brand's real content (real product or character names, real
numbers, real tags), written in the style the product itself uses.

**When nothing real can be found** (no site, an app with no public screens, a sign-in wall):
design a believable screen from what is known: the brand's logo and colors, its real feature
names from the truth file, and the platform's native look (iOS or Android conventions). Never
invent a feature, a number or a name; say in the metadata's `unverified` that the screen is a
design, not a capture.

**Clean what isn't yours to show.** Paint out a screen-recording dot in the status bar. Never
show an account name, ID or personal data. Avoid third-party characters, other companies' IP and
real people's photos that appear in the brand's catalogue; pick the brand's own originals.

**Rendering details that bite.** A cropped image placed on a CSS background of the "same"
colour shows a faint box because of colour management; key the crop's background to transparent
(ffmpeg `colorkey`). Large images may not finish loading before the screenshot; shrink them
first. Render a 360x640 layout at scale 3 for a 1080x1920 result, or a capture's native width at
scale 1.

**Animate in ffmpeg**, writing each step to `assets/`: scroll a tall rendered list behind fixed
header and navigation layers with an eased offset; show a tap with a marker that has a dark fill
and a white ring (a white ring alone vanishes on bright art); push screens in from the right
over 0.3 s like a native app; reveal messages in steps; alternate two frames to animate a
waveform. Hold each new step long enough to read: about 2.5–3 s for a pair of chat messages.
The result goes in the build as an `insert`.

## Music

The agent decides the soundtrack itself (the owner's rule, 2026-10-24), from what the source's
audio is:

- **The source's own voices drive the skit** and their lips are copied into the new clips: keep
  the source audio. It is the only thing that stays in sync. It is **always pitch-adjusted**
  (the owner's rule): +0.6 semitones by default (`pitch_semitones` in the build), resampled and
  tempo-corrected so length and lip sync hold. +1.5 sounded processed.
- **The source's music is someone else's song:** replace it with an original track generated to
  the same genre, tempo, energy shape and vocal style. When the source's voices and that song are
  mixed together and can't be parted, keep the source audio pitch-adjusted, lay no second song
  over it, and note the kept song in the metadata's `risks`.
- **Vocals only when the video needs them:** a source that is a song or a sung trend gets an
  original song with lyrics (`"instrumental": false` and the lyrics in `prompt`); everything else
  is instrumental. This is the owner's decision for re-skits, over the toolkit's
  always-instrumental rule.
- The request's `Music:` line wins: `no music` means none is added (kept source audio only);
  `use music from the library` means a track from `DesignerShared/music/`.

Measure the source first (`reskit.py audio-probe <file> --drop`): tempo (an onset-autocorrelation
estimate, which may read double or half time), brightness, bass weight, and the energy shape
over time (where the drop or the hook is). Speech recognition often hears nothing under a rap or
a dense beat; silence is not proof of no vocals. Look at the source's info (`source/info.json`
names a track when the platform knows it) and the frames (someone mouthing words).

Brief Suno in custom mode: genre and the defining sounds, vocal type, the measured tempo, and the
energy shape in plain sound words. Lyrics: hook first, about the brand's story but never naming
the brand (generators mangle names), no profanity, no lines borrowed from known songs (search
any line you're unsure of). One job returns two takes (`take.mp3`, `take-2.mp3`). Transcribe both
with word timestamps (`make-timings.py`) and pick the take and the window by measurement: the
hook or drop lands on the edit's turning point, and the window never starts mid-word. The
rejected take goes to `deletable/`.

## Composing the edit

`edit.json` rebuilds the whole edit (`build_edit.py`'s header has the format). Each kept segment
comes from its generated clip at `source time − clip start`, or from the source (caption masked)
as a stand-in while the clip renders, so the edit can be built and reviewed before generation
finishes. Inserts and b-roll are concatenated in place. Overlays are full-frame transparent PNGs
or pop-up stickers with exact in and out times; pop-ups get the three-frame scale-in. Source
audio is cut with matching segment boundaries and 30 ms fades at every cut; inserted silence is
covered with room tone looped from a quiet stretch of the source (`roomtone`). A held last frame
reads as the video getting stuck when the shot already lasts long enough for its text: then end
on real footage and start the text earlier. Hold the last frame (`end_hold`) only when the final
shot is genuinely too short to read the line (under a second), and keep it to about 1.5 s.

The audio is mixed and checked on its own, then attached to the picture; the final mix sits at
about -16 LUFS with true peak under -1 dBTP, measured with ffmpeg ebur128, like the shared
render. The share copy (under 30 MB) goes beside the drafts in `renders/deletable/`.
