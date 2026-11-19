# Generation playbook

Field knowledge for making the pieces of a skit. The shared toolkit (`DesignerShared/skills/toolkit.md`)
governs the CLI, hosting and every model it names; this file adds what a re-skit needs on top.
Prices change: `spira_chain.py price <chain.json>` reads the live price list for every job in
the chain, and is the figure that goes in the plan.

## What each tool is for

| Need | Model | Notes and live price (2026-10-24, check with `price`) |
|---|---|---|
| A new persona's base image | `ai-influencer-image` (Soul) | 9:16, 1080p, ~7. Only when no persona exists (persona-and-outfits.md). |
| Persona clean-up, character sheet, outfit sheets, background plates, a prop | `gpt-image-2` | Edits from a reference image. 1K ~4, 2K ~5, 4K ~8. 16:9 4K for sheets, 9:16 2K for plates. |
| Replacing the person in a source clip | `wan-3.0`, `reference_to_video` | **Approved** (the owner, 2026-10-24). 720p 6.18/s, 1080p 12.35/s. Whole seconds, 2–30 s output; up to 15 s of reference video; reference video plus output at most 30 s (checked at submission, nothing charged on refusal). 4–25 min per clip. |
| The same clip, with the person saying new or re-voiced lines | `wan-3.0`, `reference_to_video`, `"sound": true` | Same price: sound costs nothing extra. The words, their times and the voice go in the prompt; the reference clip is silent ("Changing what people say", below). |
| A shot that does not exist in the source | `wan-3.0`, `image_to_video` | From a still; a one-sentence prompt for the small movement (and, with `"sound": true`, its line). Same price. |
| Music | `suno-music`, custom mode | Only for `Music: original` or a source with no music (organic videos keep the source's music). ~7 per job, two takes. Instrumental unless the video needs vocals (below). |
| Transcripts and checks | `make-timings.py` (Scribe, Whisper fallback) | About 1 credit a minute; it prints the credits. |

Nothing else: no other image or video model, no lip-sync route, no Gemini Omni (any version), no
Seedance, no chunker. Every spoken line in a re-skit is made by Wan 3.0 over the source's motion.

## Running jobs

Every generation of a video goes in one chain file, `materials/chain.json`, run by
`tools/spira_chain.py` (its header has the format). It does what the shared `spira-jobs.py` does
(submit everything first, then wait, download each result) and adds what a re-skit needs and
`spira-jobs.py` does not cover: jobs that wait on other jobs' results (clips need the outfit and
the plates), waits longer than the CLI's 10-minute default (Wan clips run up to 25 minutes),
the outfit hold, the 2-extra-generations limit, and the credits of every job recorded in the
metadata the moment it lands. Use `spira-jobs.py` directly only for a set of independent jobs
outside the chain, such as a batch of transcripts' sources or a one-off still, and record those
jobs in the metadata yourself.

```json
{"jobs": [
 {"label": "outfit", "model": "gpt-image-2", "out": "assets/outfit_sheet.png", "hold": true,
  "inputs": {"size": "16:9", "resolution": "4K", "referenceImage": ["@/abs/.../personas/Mia/sheet_4k.png"], "prompt": "<outfit prompt>"}},
 {"label": "plate_a", "model": "gpt-image-2", "out": "assets/plate_a.png",
  "inputs": {"size": "9:16", "resolution": "2K", "referenceImage": ["@assets/src_a.png"], "prompt": "<plate prompt>"}},
 {"label": "clip_A", "model": "wan-3.0", "out": "gen/out/A.mp4",
  "inputs": {"generationType": "reference_to_video", "duration": "4", "resolution": "720p", "size": "9:16", "sound": false,
             "referenceVideo": ["@gen/ref/A.mp4"], "referenceImage": ["{{outfit}}", "{{plate_a}}"], "prompt": "<clip prompt>"}},
 {"label": "clip_B", "model": "wan-3.0", "out": "gen/out/B.mp4",
  "inputs": {"generationType": "reference_to_video", "duration": "10", "resolution": "720p", "size": "9:16", "sound": true,
             "referenceVideo": ["@gen/ref/B.mp4"], "referenceImage": ["{{outfit}}", "{{plate_b}}"], "prompt": "<dialogue prompt>"}},
 {"label": "music", "model": "suno-music", "out": "music/take.mp3",
  "inputs": {"mode": "v5_5", "customMode": true, "instrumental": true, "style": "<genre, sounds, tempo, energy>", "title": "<title>"}}
]}
```

- `@<path>` uploads a local file once; a hosted URL (`https://static.viralwell.ai/...`, such as
  the request's logo or product image) passes as it is. `{{label}}` is another job's result,
  and the job waits for it. Never re-upload a CLI output.
- Start it with the Bash tool's `run_in_background` (`python3 <reskit>/tools/spira_chain.py run
  <chain.json>`), then do the hands-on work. When you need its results, block with `wait --for
  9` (under the 10-minute Bash limit), never a polling loop. `status` shows every job.
- The job IDs are saved the moment they exist, so running the chain again never resubmits a
  job. A job that is merely slow (some sit QUEUED for 20 minutes) is never resubmitted: a
  duplicate costs the full price again.
- The statuses the CLI really returns (spira 0.0.32) are QUEUED, RUNNING, COMPLETED, FAILED and
  CANCELED, in capitals in `jobs status`; `jobs wait` ends with a lower-case `"status":
  "completed"`. Compare them case-insensitively. The chain handles them (it re-checks a FAILED job
  once, since a job can flip), and reads the job's charge from `jobs status` (`data.credits`).
- **At most 2 extra generations per job** (the toolkit's rule): `redo <chain.json> <label> "<why>"`
  moves the current take to `deletable/` and queues one more; a third redo is refused. Then
  keep the best take and say what is wrong in your final line.
- Credits: the job's own charge when the CLI reports one, else the live price-list figure for
  those inputs. Never the account balance: other sessions share it.

## Reference clips for person replacement

One clip per camera setup (`reskit.py probe` lists the scene changes). A clip must never
contain a cut: frame rounding at a shot boundary easily drags one frame of the next shot in, so
end each clip a few frames before the next cut. Cut each clip to a whole number of seconds
and a little longer than its slot, so the edit can trim to the beat. That length is usually the
generation's duration too; when new dialogue needs a longer delivery, the generation's duration is
set longer and the reference stays as it is ("Changing what people say"). When the usable part is shorter, the last frame is held to the whole second, trimmed
on the **input** side so the hold really happens. Audio stripped, 30 fps:

```
python3 <reskit>/tools/reskit.py cutref <source.mp4> <start> <usable_len> <whole_seconds> gen/ref/A.mp4 --mask assets/caption_mask.png
```

It prints the scene changes inside the clip and refuses one that has any.

## A shot longer than one reference

Wan reads at most 15 s of reference video, and the reference and the output together can't pass
30 s (both checked at submission; a refused job costs nothing). So one continuous camera setup
longer than about 15 s can't be copied in one job. Decide by what the rest of the shot is carrying.

**When the later part is about beats more than exact movement** (who speaks, a reveal, a reaction,
something handed over), copy the opening and extend it (the owner's choice, 2026-11-06):

- The first clip is an ordinary clip: the opening stretch of the source as its reference (up to
  15 s), its own length as output, so it copies the source exactly.
- The second job continues that clip. Video 1 is the first clip's own result, with its sound, so
  the faces, the room and the voices carry on (in the chain, `"referenceVideo": ["{{clip_A}}"]`).
  The same character sheets, plates and props go in as images, named as before. The prompt opens
  "Extend Video 1 forward by [N] seconds, continuing seamlessly from its last frame: same people,
  same place, same lighting, same camera, same voices", then gives what the rest of the source does
  as a shot list with times from the extension's start: who is framed, where the camera moves,
  what the hands do, and how a reveal faces the camera. The lines follow, timed the same way.
- It returns only the new part, as long as its `duration`. Video 1 is at most 15 s and Video 1
  plus the extension at most 30 s, so the first clip's length decides how much is left to extend.
- What you trade: the extension stages your shot list, not the source's frames. The beats land
  where you put them, but the gestures and camera are Wan's own. So write the shot list from the
  source's frames, beat by beat, and describe a reveal exactly (who holds what, which way it faces).

**Talking heads: one copied clip, everything else extends it** (the owner's standing rule,
2026-11-09). Don't cut a talking head into separately generated shots. Each separately generated
clip invents its own voice, so the tone drifts from clip to clip; an extension carries the first
clip's voice. So:
- Generate a clip from the source video only when that part brings a new action together with a
  change of camera angle or shot (a cut to a new setup, a reaction from another angle). Such a clip
  can run in parallel with A.
- When a part is only more movement in the same setup (gestures, leaning in, holding up the prop),
  don't copy it from the source: describe that motion in the extension's prompt instead.

**A talking head longer than one extension: extend the first clip again for every part** (the
owner, 2026-11-09). Don't chain parts (C extending B, D extending C). Every part B, C, D… extends
the first clip A: each job's Video 1 is A itself, with its sound. Every part then starts from the
same face, outfit, prop, room and voice, so nothing drifts from part to part, and the parts can run
side by side instead of waiting on each other.
- Size: Video 1 at most 15 s, Video 1 plus the part at most 30 s. A clip comes back a few
  hundredths of a second over its duration, so trim A just after its last word (14.9 s for a 15 s
  clip) before using it as Video 1, and keep each part at most 30 s minus A.
- Split the script at sentence ends. Time each part's lines at the source's syllable rate with
  about 0.3 s between sentences, leave about a second after the last word, and round the duration
  up to the next whole second.
- Each part's prompt opens the same way ("Extend Video 1 forward by [N] seconds, continuing
  seamlessly from its last frame: same person, same place, same lighting, same camera, same
  voice"), carries the same images named as before, gives a one-line shot (the same framing as
  video 1, the camera still, talking with natural hand gestures, holding the same prop), the
  delivery for that part (warmer, softer, upbeat), and its lines with times.
- Joins: A to B is seamless, since B starts on A's last frame. C, D… also start on A's last frame,
  so B to C and C to D cut as jump cuts on the same framing, which reads naturally in a talking
  head. Cut each part just after its last word.
- Tested on GenSpark Video 1: A 14 s plus three parts of 13, 16 and 14 s, every line came back in
  order and the face, glasses, outfit and voice stayed the same across all four.

**When the exact movement matters all the way through**, copy each part from its own reference.
Never for a talking head: it always extends its first clip, as above (the owner, 2026-11-09).
Each later clip starts fresh from the plates, and if its reference opens on a blurred or moving
frame, the clip can open on the plate's own view instead of the source's framing. So start each
later reference on a clear frame, overlap it with the previous clip by a second or so, and join
inside the motion.

Two shortcuts don't work. A full-length reference is refused. Squeezing the source by speeding it
up so all of it fits under 15 s keeps the lines on time, but the clip only loosely follows the
camera for the first half and then settles into one static wide shot.

**Joining the parts.** Cut where the first clip moves fast (a whip pan, a turn), on its most
blurred frame. A hard cut there reads as the camera arriving. A crossfade between two different
sharp frames shows both people at once for a moment. Take the first clip's audio up to the cut
and the second's from it.

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
the restyle in everyday words. Close with the casual phone look. Look at the finished plate up
close before any clip uses it: whatever it shows, Wan paints back, a logo on a cup or a laptop
included, even when the clip's prompt says no logos. A plate with another company's mark on it
gets a second edit that changes only that object. A full restyle sometimes moves
the camera; that is fine for a video-model reference (the model takes the camera from the source
clip). If a plate must line up exactly with the source, ask only for a material swap: same
shapes, new colours and materials.

## The person-replacement prompt

The shape that keeps working: say what each reference is, what to replace, what changes, and
what to retain.

> Video 1 is the video, image 1 is a character sheet of the new person, image 2 is the
> background. Replace the girl in video 1 with the woman from image 1, wearing the outfit
> from image 1, with only the [accessory] from image 1. Replace the room with the room from
> image 2. Keep the camera and every movement, gesture and facial expression from video 1. She
> holds her phone as in video 1. Remove the caption text from the middle of the frame, so there
> is no text on screen.

What makes it hold:
- **Point to the references, never describe what they show** (the owner's rules, 2026-10-30 and
  2026-11-05): every clip says "the woman from image 1", "wearing the outfit from image 1", "the
  room from image 2", and never names a garment, a colour, a hairstyle, a face feature, or what an
  object looks like. The sheet and the plate carry the look. Clips are generated independently, so
  descriptions drift: each clip reads them a little differently, and across a multi-scene video the
  outfit, the hair and the props stop matching from one cut to the next. The same pointing words in
  every clip keep them consistent. A described clip can happen to look
  right on its own; across several clips it doesn't hold.
- **Name the accessories you want and say "only".** The source performer's jewellery leaks
  otherwise (a cross necklace, rings, a watch).
- **Name every prop the person holds, by what it is, not how it looks** ("her phone", "a mug"),
  and when a prop appears only part way through, say at what second. The request's product, when
  it can be held or worn, can replace the source's prop here (add the product image as a third
  reference and say "the [product] from image 3", nothing about its look).
- **Never write "keep everything else exactly the same."** Name what is retained instead.
- **Describe the result, not the removal.**
- **Write the shared parts once and reuse them word for word** in every clip of the video: the
  reference sentence, the replace sentence, the keep sentence, the voice. Only the setup-specific
  parts change (which plate, which props, which lines).
- `"sound": false` when the source's voices are kept: the clip's sound comes from the build.
  `"sound": true` when the person says new or re-voiced lines (next section).

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

## Changing what people say (re-voice and added speech)

Wan 3.0 copies the source's motion and, with `"sound": true`, speaks lines written in the prompt,
lip-synced to that motion, in a voice described in words. This replaces what the person says
while keeping everything they do. It works only when **no source speech reaches the model**.
Whether it works depends on what reaches the model, not on the prompt's length or detail: a
reference that still carries the source's speech (in the video or as reference audio) brings the
old words back, and burned-in captions come back as invented ones. With those kept out and the
lines written in with their times, the new words come back in order and on their beats.

### When

Section 7.4 of the skill decides: re-voice a line when its job in the scene fits a true brand
situation but its words aim elsewhere; add speech to a silent source when the action has a
talk-to-camera beat. Once any of a person's lines is re-voiced, all of that person's speech in
the video is generated, from one full script.

### How

What decides whether it works is what reaches the model and how precisely the words are placed.
The points below are the reasoning behind the tests above; sources come in every shape, so apply
the reason, not the letter.

- **The model copies whatever speech it hears.** So the reference clip goes in silent (`cutref`
  strips the audio) and `referenceAudio` is left out. If a scene must open with a non-dialogue sound
  that nobody's new words replace (a chant by people off camera, a song hook), that sound can be
  audio 1, named as what it is; the voice of a person whose words change never goes in.
- **It also redraws whatever text it sees.** If the source has burned-in captions, mask them first
  (`mask`, then `cutref --mask`), or invented captions come back.
- **It only says what it is told, where it is told.** Write every line spoken in the clip's span,
  from the dialogue script, with its time in seconds from the clip's start (source time − clip
  start). For a talking source, take the times from each source line's first word in
  `timings.json`. For a silent source, read them off the frames: where the person turns to the
  camera, holds something up, or the action lands. Kept lines go in word for word, off-camera
  speakers too, so one generated voice carries everything. Close the list with "and nobody says
  anything else", or the model may fill the gaps.
- **A line has to fit the mouth it is given.** If the source person talks, the new line wants about
  the same syllables as the one it replaces (within about 15 %) and the same pauses; a longer line
  gets rushed or cut off, a much shorter one leaves the mouth moving with nothing said. If you're
  adding speech where the source is silent, keep it short (about 4 syllables a second of the
  window at most) and put it where speaking would look natural.
- **When the dialogue needs more time than the source gives, lengthen the clip, not the
  reference.** Wan 3.0 can carry a performance past the end of its reference: it follows the
  reference's motion for as long as the reference runs, then continues the same performance on its
  own, with the person, the outfit, the room, the camera and even the way they move staying
  consistent (the owner, 2026-11-05). The limit is the reference and the output together: Wan
  refuses a job whose reference video plus output passes 30 s, so a longer output means a shorter
  reference. When both matter, decide which carries more: the source's motion (keep more
  reference) or the room to talk (keep more output). So if the brand's message needs a
  longer delivery than the source line allows (a fuller explanation, a closing line, a tag), give it
  room: set the clip's `duration` to what the delivery needs and write the lines on that longer
  timeline. The reference clip stays the source's own length, as the source needs it: never pad,
  loop or slow it to match. Cramming a long line into a short slot gets it rushed or cut off; this
  is the better choice. Look at the continued stretch in the strip like any other footage, and let
  the source's own ending stand when the dialogue fits inside it.
- **The voice comes from words.** Use the persona's `voice.md` sentence plus the delivery this scene
  needs, the same words in every clip, so the clips sound alike. Ask for no music in the clip: if
  the source had music, it comes back in the build (the skill's "Speech in a re-voiced video").

A prompt shape that has held (the person-replacement prompt with the sound and the lines added).
Adapt it to the source: a scene with nobody else drops the off-camera part, a street scene names
the street, a source with no captions drops that sentence. The pointing words ("from image 1",
"from image 2") stay, so multi-scene clips keep matching:

> Video 1 is the video, image 1 is a character sheet of the new [woman/man], image 2 is the
> background[, audio 1 is the [what it is] that opens the scene]. Replace the [girl/guy] in video 1
> with the [woman/man] from image 1, wearing the outfit from image 1, with only the [accessory]
> from image 1. Replace the [place] with the [same word] from image 2. Keep the
> camera and every movement, gesture and facial expression from video 1. [Props, by what they are.]
> Remove the caption text from the [part] of the frame, so there is no text on screen.
> Sound: [where it is], no music. The [woman/man] is [voice.md sentence],
> speaking [delivery]; [her/his] mouth moves with [her/his] own words. [Off-camera speakers: who
> they are, one short voice description.] They speak these exact words, and nobody says anything
> else: [Speaker] ([t] s): "[line]" [Speaker] ([t] s): "[line]" ...

### Checking

Transcribe every speaking clip the moment it lands (`make-timings.py <clip> --txt
<materials>/deletable/check --language <code>`) and read it against its lines: every word, in
order, each starting within about half a second of its time; none of the source's old words; no
added lines; no music. Look at the strip for the mouth moving with the words and for leftover
text. A clip that fails is `redo` with the cause fixed (a line too long for its slot is shortened
in the dialogue script, and every clip that speaks it is checked against the new words), within
the 2-extra limit. You can't hear the voice: say in the metadata's `unverified` that the voice
match across clips was checked by transcript and description only.

## B-roll and simulated screens

When the story needs to show the brand as its own shot (a full-frame screen, a list, a
notification), build the b-roll; don't generate it. Video models redraw small screen text into
near-gibberish, so a product UI is rebuilt in HTML from the brand's real
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

## Phone screens in the scene: two passes

Whenever the source shows a phone or tablet screen that must show the brand (someone scrolls a
phone, holds a tablet up to the camera), the screen is drawn by Wan in a second pass, not laid on
top in the edit (the owner's rule, 2026-11-06). Laptops and monitors are overlaid in the edit
instead ("Laptop and monitor screens in the scene: overlay", below; the owner's rule, 2026-11-07).

**Why not the other ways.** On a phone, laying rendered screens onto a green or white screen in the edit
(corner tracking, homographies) reads as an overlay: the screen is flatter, sharper and more
evenly lit than everything around it, and its corners slip whenever a finger or a hand covers
them. Asking Wan to draw the screen in the same pass that recasts the scene leaks the source's
own screen into it: it copies the source app's reactions (a like animation, a header, a logo),
invents buttons, and can skip the screen states the story needs. Splitting the job keeps each
pass simple.

**Pass 1, the scene with a plain green screen.** The full clip as any other recast: sheets,
plate, source motion, sound if the clip speaks. The screen is described only by when it is
green, tied to what the hands do: "from [the moment the screen should change, e.g. when the
hand first acts on it] until [it turns away], the whole screen is a solid, flat, bright green, evenly lit,
with nothing on it: no text, no icons, no pictures; nothing appears on the screen when [the hand]
taps". Moments where the screen should show something the
model can draw on its own (a camera viewfinder of the people in front of it, a dark or sleeping screen) can
stay in pass 1. Look at the green stretch before going on: clean green with the hand in front of
it is what pass 2 needs; any leftover source content on it goes into a rerun, not into pass 2.
Then measure where the green really starts and ends, frame by frame, on the landed clip: it often
runs earlier or later than the times the prompt asked for, and pass 2's length (and price) comes
from the measured stretch, not the planned one.

**Pass 2, only the green stretch, filled.** Cut the stretch where the green is visible out of
pass 1 (from just before the green appears to just after it goes, at most 5–6 s) and send it
silent as video 1, with the screen video (below) as video 2, no images. The prompt keeps
everything and changes one thing, a shape that has held: "Keep video 1 exactly as it is: the same
people, place, hands, device, camera position and every movement, frame by frame. Change only the
[device]'s screen: wherever it is solid green, it shows video 2 instead, exactly as recorded,
fitted to the screen in the device's perspective and lit like a screen in [the light of the
scene], with [the hand or finger] in front of it: [the states in order, each tied to the hand
action that brings it]. Where the screen shows [what pass 1 kept], keep it as it is.
Every word on the screen is clear, sharp and spelled exactly as in video 2; nothing on the screen
is garbled, rewritten or invented. Nothing else appears on the screen. No green is left on the
screen." Sound off: the sound comes from pass 1.

**Splice and check the joins.** Put pass 2 back over the same span of pass 1 and use pass 1's
audio throughout. The build takes one file per clip, so splice first: one ffmpeg pass that trims
pass 1 around the stretch and puts pass 2 in its place (a trim-and-concat, or pass 2 overlaid on
pass 1 with a short alpha fade at each end), written as the clip's single landed file, and give
that file to the build like any other clip. Keep the unspliced passes beside it. The first join is usually seamless because pass 2 starts from pass 1's frame;
by its end pass 2 can drift a little (the framing shifts a few pixels), so look at the frames
either side of the second join and, if it jumps, cover it with a 3–4 frame crossfade or move the
join to where the camera or the device is moving. A screen that changes at the join reads as the
person switching apps or pages.

**What it costs, and how to keep it down.** Pass 2 is extra only for the stretch it covers, so
the second pass is the screen's seconds, not the clip's: keep that stretch to the time the green
is actually visible. Choose resolution by how close the screen is. When the screen fills a good
part of the frame and its words must read, pass 2 at 1080p; when the screen is small or brief,
720p is enough. Pass 1 follows the video's own resolution choice; when the two passes differ,
check the joins for a visible change in sharpness (not yet tested; both passes were 1080p in the
test that set this method). A rerun of a failed single pass costs more than the second pass does.

**Limits to plan around.** The reference videos together are at most 15 s, and reference video
plus output at most 30 s; pass 2's two short videos fit easily.

### Building the screen video (video 2)

The screen video is what the model copies onto the device, so it has two jobs: look like the
brand's real product on that device, and be easy for the model to copy without mistakes. Build
it for the device the source shows (a phone or a tablet), at that device's real proportions and
with what that device's screen would really show around the page: a phone's status bar and
browser bar, a tablet's split views. Match the screen's shape to the one in the source, or
the model has to stretch it.

**As close to the real thing as possible.** Start from the brand's live product: capture it
(`capture_site.js`, or the request's material) at the device's size and rebuild the page from
it, with its real copy, colours, font, logo, buttons and the order of its sections, the way a
visitor would see it on that device. Show a scripted visit rather than animating stills: real
scrolling with momentum, a button that presses, a page or panel that slides in, typing that
appears letter by letter, the way the product itself behaves. Never record a sign-in, a form
submission or anything that creates an account; the rebuilt page shows what the action would
open.

**Recording it sharp.** A scripted page recorded in headless Chrome through the shared
playwright-core works: Chrome's screencast with timestamps, rebuilt into a constant 30 fps with
ffmpeg's concat durations (the frames only arrive when something changes). The screencast sends
frames at the page's CSS size, so a device scale factor alone comes back blurry: render at 2x by
making the viewport twice the device's size and zooming the page by 2, and remember that
positions the page measures for its own animation then come back zoomed. A window smaller than
the viewport crops or squeezes the frames; check the first frame's size before trusting a take.

**As clear as possible for the model.** Fill the screen from edge to edge with the real page:
empty space at the top or bottom of a state invites the model to invent something there (a tab
bar, a row of labels), and what it invents is garbled.
Numbers are the riskiest: a garbled price or amount is a false claim, so check every number in
the result against the source of truth.

**Timed to the hands, not the clock.** The model times the screen's changes to the action it
sees in video 1, not to video 2's own clock (tested with scrolls and taps on a phone; expect the
same of clicks and typing, and check it); moving every event a second earlier in video 2 changed
nothing. When the source has several actions close together, the model tends to tie the change
to the most visible one (a firm double tap rather than the light tap before it), so the change
may land later than the action you planned it for: check where it landed before timing text or
pop-ups to it. So video 2 needs the right states in the right order, one state change per
action, and can be short (3–4 s) to fit the reference budget. Give each state its own clear
beat, few and distinct. If the source's action should change nothing on the new screen (it
triggered something in the source's app), video 2 shows no change there and the prompt says
nothing appears.

## Laptop and monitor screens in the scene: overlay

When the source films a laptop or a monitor (or a TV) whose screen must show the brand, the
screen is laid on in the edit, not drawn by Wan (the owner's rule, 2026-11-07: on Task 277 the
drawn laptop screen looked worse than Task 95's overlay). Phones and tablets stay with the two
passes above. Keep the screens on the device instead of cutting to flat full-frame inserts:
1. Make one still plate per camera angle with GPT Image 2 from a source frame: same angle, the
   device pulled back so all four screen corners are in frame, a plain logo-free lid, and "one
   flat solid pure green colour filling the entire display edge to edge inside the thin black
   bezel: no browser, no window, no interface, no text, no reflections".
2. Rebuild every product state as one HTML page selected by URL hash (`screens.html#plan2`) at
   1440x900, scale 2, and render them all with `render_html.js --batch`.
3. Composite in Python (numpy + Pillow; cv2 is not installed). Find the corners from the green
   mask (TL/BR = min/max of x+y, TR/BL = max/min of x−y). Solve the homography by SVD, with the
   screen padded about 10 px past the green edge, and warp each state on. Despill only clearly
   green pixels (`g > max(r, b) + 18`), or warm walls turn olive, and set leftover green edge
   pixels to bezel black. Move a virtual phone camera over the plate (an eased push per shot plus
   a small sine wobble) and put the screen through the same transform, so it never slips. Give
   the screen a filmed look: a 0.7 px blur, contrast `*0.94 + 10`, a soft vignette and grain.
4. Keep the source's cut times as the shot boundaries. Cut any finger tapping the screen and use
   a drawn cursor in the HTML. Encode the frames (`libx264 -crf 16`) as one `insert`.
Worked example to reuse: `<reskit>/examples/laptop-overlay/composite.py` with its `screens.html`
(Task 58's laptop b-roll; the plates and rendered PNGs it reads are not kept, only the code); the step-by-step walkthrough doc is
https://ljpp9tldvzuk.jp.larksuite.com/docx/XWBddt6KWojencxzHbCjaedtpTh. This only works when the
screen shots have no person in them. When hands or a person stay in front of the screen,
generate the clip with "a plain glowing white screen", track the bright screen per frame and
multiply the UI into it (Task 61), so the hands stay in front.

**Locked to the screen when the camera moves or something passes in front** (the owner,
2026-11-07). The overlay must sit exactly on the screen and keep the device's perspective in
every frame, never a flat picture sliding over a moving shot, and stay put and behind whatever
briefly covers it (a hand, a finger, an arm, a cup, a phone, a person walking past):
- Find the screen on every frame, not once per shot: the green (or bright white) mask of that
  frame, its four corners taken from straight lines fitted to each side's edge pixels and
  intersected, so a finger over one corner or a glint on one edge can't drag it.
- Smooth the corners over 3–5 frames so the screen doesn't shimmer, but no more: heavy smoothing
  makes it lag behind a quick camera move.
- When something covers part of the screen, the tracking ignores it. Fit each edge only to the
  stretch of it that is still visible; a corner or a whole edge that is hidden is carried from
  the visible ones' motion and the last clean frames (the screen's shape stays the same from
  frame to frame), never re-fitted to the outline of the hand or object. When it moves away, the
  screen must not jump: compare the carried corners with the re-found ones and blend over a few
  frames if they differ.
- Whatever is in front stays in front. Draw the page only where that frame's mask shows green
  (or white) inside the tracked screen, so the hand or object covers the page exactly as it
  covered the screen; soften the mask's edge by about 1 px and despill green off the hand's
  edges so it has no halo. A finger or object that crosses the bezel keeps its own pixels.
- Warp each frame's state with that frame's own homography, so the page tilts, foreshortens and
  scales with the lid or the monitor as the camera moves. On a still plate with a virtual camera,
  the screen goes through the same transform as the plate.
- Check before READY: a frame sheet across the fastest camera move and across every moment
  something passes in front, and zoomed crops of the four corners on the first, middle and last
  frames of every screen shot and on the frames just before, during and after each obstruction.
  The page's edges run along the bezel's edges with no green or white showing and nothing
  spilling onto the bezel or the room; a slip, a wobble, a jump after an obstruction, a page
  showing through a hand, or a page that leans differently from the lid is a fix, not a note.

## Music

**Organic videos keep the source's own music** (the owner's rule, 2026-11-02, replacing the rule
of 2026-10-24 for organic posts): an organic re-skit uses the source's sound the same way the source
creator did, so there is no licensing reason to replace it, and generated tracks sounded like a
boring stock ad library (Vizard test, Tasks 98-102). With no `Music:` line:

- **Keep the source audio, music and all.** Kept source **voices are always pitch-adjusted** (the
  owner's rule): +0.6 semitones by default (`pitch_semitones` in the build), resampled and
  tempo-corrected so length and lip sync hold. +1.5 sounded processed. **Music is never pitched**
  (the owner, 2026-11-18: "The pitch adjustment is for voice not music"): a source that is only a
  song is kept at its original pitch (`"audio": "music"`, the source as the music, `"pitch": false`).
- **New dialogue over the source's song:** keep the song where no old voice is heard and carry the
  new lines on it; where old voices and the song can't be parted, bed the new lines on a speech-free
  stretch of the source's music, never cut mid-word. Note it in `music`.
- **Inserts and the end card** ride the same source music (continuous bed, `music_under_lu`
  about 14-18), never a generated track.
- **Source music shorter than the edit:** repeat it seamlessly (the owner, 2026-11-03; Vizard
  Tasks 98 and 102): cut the repeat on a bar or phrase boundary (use the measured tempo and the
  beat grid from `audio-probe`) with a short crossfade so the join can't be heard, never mid-word,
  and end on the final fade. This is a musical repeat of the song, not the room-tone loop forbidden
  below (a short raw slice looped under a hold).
- **Speech added to a music-only source:** keep the song and lay the new lines on it, the song about
  14 LU under the voice (at its original pitch: music is never pitched), so it still plays like the trend
  it came from with a person talking over it.
- **A source with no music at all** may get an original track (the `Music: original` rules below).

The request's `Music:` line wins: `no music` means none is added (kept source audio only);
`use music from the library` means a track from `DesignerShared/music/`; **`original`** (ad videos,
where someone else's song can't be used) means an original track generated to the source's genre,
tempo, energy shape and vocal style, as follows:

- **Vocals only when the video needs them:** a source that is a song or a sung trend gets an
  original song with lyrics (`"instrumental": false` and the lyrics in `prompt`); everything else
  is instrumental.
- **Never brief in stock-ad words** (upbeat, bright, plucky synths, claps, cheerful, playful,
  inspiring, corporate): name the specific scene or subgenre and its texture instead.

Measure the source first (`reskit.py audio-probe <file> --drop`): tempo (an onset-autocorrelation
estimate, which may read double or half time), brightness, bass weight, and the energy shape
over time (where the drop or the hook is). Speech recognition often hears nothing under a rap or
a dense beat; silence is not proof of no vocals. Look at the source's info (`source/info.json`
names a track when the platform knows it) and the frames (someone mouthing words).

Brief Suno in custom mode: genre and the defining sounds, vocal type, the measured tempo, and the
energy shape in plain sound words. Lyrics: hook first, about the brand's story but never naming
the brand (generators mangle names), no profanity, no lines borrowed from known songs (search
any line you're unsure of). One job returns two takes (`take.mp3`, `take_b.mp3`). Transcribe both
with word timestamps (`make-timings.py`) and pick the take and the window by measurement: the
hook or drop lands on the edit's turning point, and the window never starts mid-word. The
rejected take goes to `deletable/`.

## Composing the edit

`edit.json` rebuilds the whole edit (`build_edit.py`'s header has the format). Each kept segment
comes from its generated clip at `source time − clip start`, or from the source (caption masked)
as a stand-in while the clip renders, so the edit can be built and reviewed before generation
finishes. Inserts and b-roll are concatenated in place. Overlays are full-frame transparent PNGs
or pop-up stickers with exact in and out times; pop-ups get the three-frame scale-in. With
`"audio": "clips"` (a re-voiced video), each segment's sound is its own generated clip's audio,
cut at the same points as the picture; a kept source music bed rides under it (`music` with
`"pitch": false`: music keeps its original pitch). With `"audio": "source"`, source
audio is cut with matching segment boundaries and 30 ms fades at every cut; inserted silence is
covered with room tone from a truly quiet stretch of the source (`roomtone`). **Never loop room tone that has music, voices or a steady tone in it** (the owner, 2026-10-29: a looped slice under the end card sounds like a skipping CD): the slice must be at least 10 dB below the source and 0.5 s longer than the longest insert or hold, so it never repeats; the build stops otherwise. When the source has music or voices under everything, set `roomtone` to null and carry the inserts and the end card on one continuous music bed (`music`, `music_under_lu` about 14-18) that ends on the build's final 1.5 s fade, never a join at the cut. The build reports an audio loop under a room-tone fill and any dropout (more than 6 dB down for about 0.1 s) at an insert cut as problems: fix them before READY. A held last frame
reads as the video getting stuck when the shot already lasts long enough for its text: then end
on real footage and start the text earlier. Hold the last frame (`end_hold`) only when the final
shot is genuinely too short to read the line (under a second), and keep it to about 1.5 s.

The audio is mixed and checked on its own, then attached to the picture; the final mix sits at
about -16 LUFS with true peak under -1 dBTP, measured with ffmpeg ebur128, like the shared
render. The share copy (under 30 MB) goes beside the drafts in `renders/deletable/`.
