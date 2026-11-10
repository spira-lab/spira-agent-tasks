---
name: cloning-toolkit
description: Supplementary knowledge for the Cloner video designer. Which tools exist for a clone, what each is good and bad at, when to reach for which, what to do when one fails, and what everything costs. Sits on top of the shared toolkit (Agents/DesignerShared/skills/toolkit.md), which wins on every shared model. Read it to reason about a plan, not to follow it line by line.
---

# Cloning toolkit

This is field knowledge from real tests, not a recipe. Every video you
clone is different, so no fixed sequence fits all of them. Use this to
understand what each tool does well, where it breaks, and why. Then build
the plan that fits the video in front of you.

Three things are always in tension: **quality, speed and cost**. A tool
that wins on one usually loses on another. Decide which matters most for
the shot you're making, and choose on purpose.

Model behaviour, prices and limits change. Treat everything here as a
strong prior, and confirm with the model's own schema before you rely on
it.

**How this fits "regenerate, don't reuse".** Several techniques below
pass a source clip or a still of the source into a model. That is
borrowing the source's **movement, timing and layout**, never its pixels.
The person, the room and the products in the output are always newly
generated, and the source creator's face never survives into the clone.
If a technique would put the source's actual pixels into the clone, it's
the wrong technique.

`<shared>` is `Super Vega/Agents/DesignerShared`; `<cloner>` is
`Super Vega/Agents/ClonerVideoDesigner`.

## Before anything: the pre-requisite check

Run `python3 "<cloner>/tools/prereq_check.py"` at the start of every
clone. A missing login, model, tool or renderer found at the end costs
the whole run. Where files go is in `clonerfilemanagement.md` and the
shared file-management skill.

## Everything runs through submit_ai_job and wait_ai_job

Every generation and processing job (images, personas, video, cut-outs,
voice, music, transcripts, source understanding) is a Spira AI job run with
the tools on the MCP server `worker_tools`: `submit_ai_job`, `wait_ai_job`
and `host_file`, as the toolkit's submit_ai_job / wait_ai_job / host_file
steps describe. Never run a job through the `spira` CLI. Local tools only
handle files: ffmpeg for cutting, joining and inspecting, and the shared
tools. A remote file is fetched with the `ai` tool's download action (never
curl or wget).

- **Before the first call to any model**, read its schema:
  `spira ai models get <model-id>` (read-only docs). It lists the accepted fields,
  allowed values, notes and live prices. The notes often warn of a limit
  before you hit it.
- **Every input must be a public URL.** Host local files as the shared
  toolkit section 2 says (`host_file`, `path` root-relative, the URL it
  returns is the input); never re-host a job's output or a `static.viralwell.ai` URL.
- **A set of jobs:** write one payload file per job, submit them all in
  one turn (one `submit_ai_job` call each, `modelId` and `inputs`), write
  each returned `jobId` to its `.pending` file at once, then wait on all of
  them in one turn (one `wait_ai_job` call each, with `jobId` and `saveTo`).
  A single job is the same two calls. `wait_ai_job` waits 300 s by default
  and up to 600 with `timeoutSec`; on `stillRunning: true` call it again
  with the same `jobId` and `saveTo` (Wan jobs can take 30 minutes: wait
  again until done).
- **Never block the whole clone on one job, and never poll from the
  shell.** Submit every independent job together and keep working on the
  stage while they render. Video jobs take one to more than ten minutes.
- **Check a job:** call `wait_ai_job` again with the same `jobId`: it
  returns `status`, `resultUrls` for the output and the provider's error
  when it failed, and is not charged again. The charge is the live price
  times what was billed.
- **Credits come from the job,** never the balance (the account is
  shared). See the skill, section 12.
- **Record speed, cost and quality for every job** in `jobs.md` and the
  metadata. That's how you choose better next time.

## The persona

The persona comes from the request's avatar image, or is made by the
Avatar Designer's method (the skill, section 6): one Higgsfield Soul base
in the prompting skill's format, one GPT Image 2 clean-up edit, the
checks. Every later step inherits its quality.

**Casting choices that go into the Soul format's slots:**

- **Who she or he is:** an explicit adult age, the ethnicity or
  nationality, the gender. Choose the ethnicity for the clone's language
  and audience, and **against** the source performer (see the recast
  lesson), not by default.
- **One vibe word** matched to the energy of the video: warm, cheerful,
  playful, confident, soft. One vibe, not a list.
- **Hair, concretely:** length, texture, colour, styled casually. Specific
  hair makes a persona recognisable from clip to clip.
- **A simple everyday outfit:** one or two plain pieces, at most one small
  accessory. Busy patterns, logos and statement pieces date the persona
  and clash with the brand. Never the product: Soul can't take a product
  image; products go in at the edit or clip stage.
- **Framing for the widest shot the clone needs.** Edits can crop in, but
  they can't invent a body the base doesn't show; GPT Image 2 fills the
  gap with whatever body it is shown.
  - **Full body, head to toe:** outfit changes, try-ons, fashion, dance,
    anything showing the whole figure, and always when the brand sells by
    size. (A waist-up base for a plus-size outfit reel gave two rounds of
    slim stills before a full-body base fixed it in one.)
  - **Waist up:** only for talking heads that never show more.
- **A plain lived-in setting** in daylight. Video models treat this room
  as *her room*; a calm room serves every later shot.
- **Hands empty and relaxed** whenever the clip will put something in
  them, so no phone or prop leaks into Wan's hands.

**GPT Image 2 edits from the persona** (`gpt-image-2`, `9:16`, `2K`):
pass the persona as `referenceImage` and describe only the change, in the
prompting skill's persona-edit format: what stays (always including
**body shape and size**, the attribute that drifts most), what changes
and only that, and the headroom line.

- **Always edit from the persona source, never from a previous edit.**
  Chained edits drift into a different person. The one exception is the
  quiet still for off-camera videos, edited from the sharp still.
- **Don't describe her appearance when you pass her image.** The
  reference carries the likeness; describing it fights it.
- **If the reference doesn't show a trait the clone needs, fix the
  reference, don't describe the trait.**
- **Change as little as possible per edit.** One edit that changed
  outfit, location and framing together came back with a head too big
  for the body; the outfit change alone was clean.
- **For a product,** pass the product image as a reference and say how it
  appears: worn, held, applied. Video models drop props they don't see.
- **For variants** (two outfits, hair up and down), each is its own edit
  from the source, never stacked. Only when the clone needs them.

**Never put another person's body in an image request.** Whatever body
the model can see, it draws. The first Cloner run sent the source
performer's photo as a "pose reference": every still came out with the
performer's slim build instead of the plus-size persona's, through three
rounds of "keep her body". When the clone copies the source's movement,
you need no pose still: Wan replaces the person in the source clip
directly. The one exception is the Kling dance pose still. If you need a
still in a pose, describe the pose in words and state the framing ("her
whole body fills about two thirds of the frame height").

**Elements on a transparent background:** GPT Image 2 with "transparent
background" in the prompt (shared toolkit 3c), for photographic elements
layered in the stage. Anything that can be drawn is better drawn in HTML
and CSS.

**Language.** A script written natively plus a matching persona gave by
far the most convincing results. A translated script on a mismatched face
reads as dubbed.

## Choosing the video model

Choose by what the shot has to do, not by habit.

### WHEN the persona talks to camera from new lines → Gemini Omni Flash 1.1

`gemini-omni-flash-1.1`, 4/6/8/10 s, `9:16`, `1080p`, 2–4 min. Follow the
shared toolkit 3e for the job, the batch, the cut-off check and the
one-model rule (Seedance 1.5 Pro only as the whole-video fallback). Never
`gemini-omni-video`: it is retired.

It has the best talking-head voice and pacing, and it pronounced every
brand name correctly. Seedance got half of them wrong.

- **The single image you pass becomes the first frame.** Compose the still
  as the opening shot. If the scene should open differently (an empty
  room, someone walks in later), make a separate opening still and pass
  the persona as a second reference.
- **Chunk with the shared chunker** (4.9–5.2 syllables per second of
  speaking time; an Omni clip speaks for its length minus 1 s). Never by
  hand, never by the target duration.
- **Writing the lines:** aim for about 3.8 words per second of target
  length; the chunker then sets each clip's length from the syllables.
- **Mixed language** (for example Taglish): every chunk opens in English
  and carries the second language inside it; an all-English chunk on a
  Filipina persona switched to an American accent. English-heavy lines run
  longer than their syllable count suggests: pass the English words' counts
  as they are said in the chunker's JSON script (`"syllables"`).
- **Camera angle changes mid-talk work** when prompted.
- **It cannot change what an existing person says**, and it **ignores the
  persona image when a video is attached**: never use Omni for motion
  transfer.

### WHEN one person is on camera and someone talks off camera → quiet shot + speech clips

An interviewer asking questions, a voice naming items for a tier list, a
friend prompting from behind the phone. All clips on Omni Flash 1.1.

1. Two stills with GPT Image 2:
   - **Sharp:** an edit from the persona as the shot opens on the answer.
     Fix its framing here.
   - **Quiet:** an edit from the **sharp** still: only a quiet, agreeing
     expression with lips closed and a small change in pose, same camera,
     framing, room and light.
2. The off-camera lines with ElevenLabs (the voice the request gives;
   skill section 9), each measured.
3. Submit together:
   - **One quiet shot:** `generationType: first_last_frames_to_video`,
     `referenceImage: [quiet, sharp]`, duration = the longest off-camera
     line plus a short beat, rounded up to 4/6/8/10 s. Prompt: "The person
     in image 1 stays quiet with their lips closed and nods with an
     agreeing expression. No camera movements, no text on screen, camera
     is static and not moving." Never write "listen": it makes the person
     talk.
   - **One speech clip per answer:** the sharp still as the only
     reference, in the prompting skill's talking-head format.
4. Per beat: the same quiet shot, its end kept and its early silence cut
   to fit that off-camera line, joined to that beat's speech clip, its own
   audio muted, the off-camera line laid on top.

Don't put the quiet beat inside the speech clip (Omni starts the line at
the top of the clip), and never use a frame from a generated clip as the
reference for another generation.

### WHEN the clone copies the source's footage → Wan 3.0 replacement, clip by clip

Whenever the clone follows the source's own shots: a reaction,
a gesture tied to graphics, an outfit-change reel, any business with a
prop. **Wan replaces the person in each source clip** with the persona,
wearing the brand's product, in a recoloured or restyled setting. Motion,
timing, camera and foreground objects come from the source; identity,
outfit and setting come from your reference images.

**Why:** in the BloomChic tests it beat the stills-then-motion pipeline on
every count: the plus-size body held (no other body was ever shown), the
face matched the persona exactly, every product rendered accurately, the
motion matched beat for beat, and no stills were needed: 107 credits and
about 22 minutes for a 14 s clone, against 417 for the first run.

Use only Wan for this. Kling moves a still, so mixing the two within one
clip set conflicts. Dances stay on Kling end to end.

**The request:**
- `wan-3.0`, `generationType: reference_to_video`, `resolution: 720p`,
  `size: 9:16`, `duration` in whole seconds (2–30).
- `sound: false` when music or a separate voice goes on afterwards;
  `sound: true` only when the person must speak a new line.
- **`referenceVideo`:** one source clip (15 s at most in total), audio and
  metadata stripped, burned-in text removed (see the lessons).
- **`referenceImage`, in this order** (up to 10): the full-body persona;
  the outfit, one product image per piece; the anchor images, such as the
  background plate.
- **Name them in the prompt by order:** video 1, image 1, image 2 …

**The prompt's shape:** what each reference is, what to replace, what to
change, what to retain. In Test B:

> Video 1 is the video, image 1 is the new person of a plus size woman, image 2 is the outfit image, image 3 is the background. Replace the person from the video with the person from image 1 wearing image 2, barefoot. Replace the floor carpet and the couch with the ones from image 3. Keep the camera, the ceiling fan and every movement from video 1.

**Principles for Wan 3.0:**

- **Anchor anything that must stay the same with an image, not words.**
  Wan regenerates each clip from scratch, so whatever is only described
  drifts from clip to clip ("peach carpet, brown couch" came out a
  different shade in every clip). A background plate, the persona, the
  outfit, any recurring prop, as images. It matters most when the video
  is split across several clips.
- **Describe what to change and what to retain, and never write "keep
  everything else exactly the same".** It contradicts the edit and invites
  the model to keep what you wanted gone. Name the retained things.
- **Say when each referenced object appears.** A reference with no timing
  is shown for the whole clip and can take over anything else in the
  hands. Write the timeline: "He is holding a bitten cardboard, then at 5
  seconds he reveals he is taking a bite of the chicken burger from image
  2." Take the times from the source (Gemini is close; frames are exact).
- **Describe the result, not the removal.** "Show this same room with an
  empty floor: nobody lying on the carpet, nothing on the floor" worked
  where "remove the person" failed.
- **Name every change, because references leak:** shoes from the product
  photo's model, the source performer's footwear, tights. If she should be
  barefoot, say "barefoot", in every clip.
- **Several people:** map every person by position to their image, say
  "each with the face, hair and clothes from their own image" and the
  exact head count; run the first clip alone as the check (see the
  lessons). Check every face against its persona: no source face may
  survive.

**The background plate** (the most useful anchor): a still of the source
where the room is visible, edited once with GPT Image 2 to the empty
result with the colour or style changes, naming the few things to retain
(camera view, fixed objects, furniture shape). About 35 s, one 2K edit.

**Splitting a source longer than one run** (15 s of reference video):
cut one clip per look or scene at the source's own transitions, overlap
each a little into its neighbours, give every clip the same anchors,
strip the audio. For a single continuous shot up to about 20 s, speed it
to just under 15 s, run one clip and slow it back (see the lessons).

**Joining the clips:** Wan redraws transition objects (a fan blade, a
door, a passing body) in its own place and time, so cutting at the
source's timestamps can show the change. Find in each clip the frame
where **its own** transition covers the subject most, cut out of one and
into the next on its own matching frame, trim each with ffmpeg
(re-encoded, exact frame) before placing it, and check the frames either
side of every cut.

**Cost and speed:** 720p 6.18 credits per second, 3–8 min per clip.
1080p is 12.35, double; use it only when truly needed.

### WHEN creating a dance video or dance scene → Kling 3.0 Motion Control

On a dance reel Kling copied the routine move for move with the persona's
identity, room and framing intact, and extended cleanly past its limit.
Don't mix Wan replacement and Kling within the same dance. The shared
toolkit 3h has the job's inputs.

1. **Pose still:** GPT Image 2 with the persona plus a plain still of the
   source's first frame. **The one exception to "never put another
   person's body in an image request".** Keep the persona's own body shape
   and size; don't copy the other person's face, hair, body, outfit or
   room. Spell out the framing (same headroom, distance, crop, size in
   frame) and compare it side by side with the first frame; check the body
   closely when the dancer's build differs.
2. **Kling 3.0 Motion Control** (`kling-3.0-motion-control`, `mode: pro`):
   the pose still as the image, the source clip with its audio stripped as
   the video.
   - **Fixed camera:** `characterOrientation: image` (reference 3–10 s).
   - **Moving camera** (selfie drift, push-in, mirror): `characterOrientation:
     video` (up to 30 s), and describe the camera move in the prompt.
   - **Name any object she handles**, or put it in the still: Kling copies
     body motion only.
3. **Longer than one run:** segments of 10 s or less; each next segment
   uses the **last frame of the previous Kling clip** as its image. Only
   for Kling dance clips.

**Watch for:** `sound: false` can still carry the source audio, so strip
it before upload; a 7 s request once came back 5.3 s and was billed 7 s;
Kling can't make new speech (the mouth copies the source's).

**Cost and speed:** 9.52 per second on pro, about 6–8 min per clip.

### WHEN a shot has no source footage to replace → Wan 3.0 image-to-video

For a shot that isn't in the source (an extra product close-up, a held
pose you added): `wan-3.0`, `generationType: image_to_video`, the still as
the only image, a one-sentence prompt for the small movement and the
camera. 4–5 s at 720p cost 25–31 credits and took 2–5 min, and it keeps
body and outfit exactly. Anything that exists in the source gets the
replacement approach above.

### WHEN the persona must copy the movement AND say a new line → Wan 3.0 only

Wan can copy the source's movement and add lip-synced new dialogue in one
pass (`sound: true`; about 31 credits for 5 s at 720p). Two things made it
work: **one short plain sentence** (a long prompt made Wan drop the motion
and cut away), and **ending with "matching mouth movements"** (without it
the line plays as a voice-over on a closed mouth).

> The woman from image 1 is holding her phone in both hands and performs the movements and facial expressions from video 1, and the person says "No I am not chatting anyone" matching mouth movements.

Keep the line to about 5 syllables per second of its slot. **Check lip
sync, not just audio:** transcribe with word times and look at the mouth
on each word.

### The source's own audio is never kept

When the motion is copied, the lips move to the source's words. The
Cloner never ships the source's voice or its music (the owner's rights
rule): a new line is spoken through Wan (above) or Omni, ambience is a
generated bed (ElevenLabs sound effects), and music is generated or from
the library. A request that truly needs the source's own performance or
audio is a Re-skit, not a clone: record that in the metadata and clone it
with new lines.

### WHEN a screen, laptop or app must appear

Every video model **redraws** screen content: text turns to near-gibberish
and layouts get reinvented. Omni Flash 1.1 with a screenshot came closest,
but none was pixel-exact.

- **If the UI must be exact,** generate the hands and device, then
  composite the brand's real screen onto it in the stage. Provided
  material wins; otherwise capture the brand's site with
  `node "<cloner>/tools/capture_site.js"`; otherwise design a believable
  screen in HTML in the brand's colours.
- **Frame laptops in 16:9, or pulled well back in 9:16.** Squeezing a
  laptop into a tall frame stretched it about 20%.
- **For pointing without tapping,** say it's an ordinary laptop, not a
  touchscreen, and the finger keeps a gap. **Naming buttons** invites
  tapping.

### WHEN mixing styles

A photoreal persona with a stylised character (for example anime) in the
same scene works on Omni Flash 1.1 when both are in the references.

## WHEN the clone needs music → understand the source's music, then Suno, generated long and cut

The Music line decides first: `no music` → none; `use music from the
library` → the shared library roll (skill section 9). Otherwise you
decide, as below.

Generated music goes boring in predictable ways. Short generations are
all intro and never reach a hook. Mood words ("playful, airy, clean")
describe nothing a model can play. And the trend texture of many reels
(slowed, sped up, drenched in reverb) is processing done to a song, not
something a prompt can describe. Each step below answers one of those.

**Mirror what the source has, nothing more:**
- **Music only if the source has music.** A source with only natural
  sound or a voice gets no music.
- **Instrumental by default** (Suno custom mode, `instrumental: true`,
  style tags only). **Vocals only when the video needs them**: the source
  is a song or a sung trend whose vocal hook is part of what drives it.
  Decide from the understanding step below, not by default, and never ask.

**1. Understand the source's music. Three ears, each wrong somewhere.**
- **Name it if you can:** the sound name, if the request or the source page gives one. Knowing it's a "slowed" edit explains the
  tempo and texture.
- **Gemini listens for the *what*:** vocals and lyrics, instruments,
  genre, structure: the source-understanding job (the skill, section 7).
- **Measure the *numbers*:** tempo, key, energy over time, where hits land
  against the cuts (librosa, through `music_cut.py`). Gemini once said
  ~120 BPM where four measurements agreed on 99.4. Trust the measurement.
- **Confirm vocals with Whisper in lyrics mode:**
  `python3 "<cloner>/tools/lyrics_check.py" transcribe <audio> <out.txt>`.
  In default mode Whisper writes "music" over a sung hook; a lone "Thank
  you" on an instrumental is not proof of vocals.

**2. Brief the original song, not the edit.**
- `suno-music`, `mode: v5_5`, `customMode: true`, `instrumental` as decided;
  with vocals, your own lyrics in `prompt`. One job = 2 songs of about 65 s.
- **Lyrics** (vocals only): a short original hook, chorus written first so
  the hook arrives early. Match the source's emotional register and theme,
  never its words.
- **Style tags in genre and trend vocabulary:** genre, the defining sounds,
  the vocal type (or none), and the *original* tempo: for a slowed source,
  the measured tempo ÷ about 0.8. No artist or song names, no mood words
  without a sound behind them.

**3. Generate a full song, never the video's length.** The hook sits in
the middle.

**4. Match the edit with processing, then cut to the video:**
`music_cut.py`, run with the `MUSIC_PYTHON` that `prereq_check.py` prints:

```bash
<MUSIC_PYTHON> "<cloner>/tools/music_cut.py" "<materials>/audio/take.mp3" "<materials>/audio/cut.wav" --length 14 --cuts 4.8,6.6,9.5,12.5 --target-bpm 99.4 --reverb 0.3
```

It slows or speeds the take to the measured tempo (pitch moves with it, as
in real slowed edits), adds reverb, picks the best window from a chorus
starting on a sung phrase, and nudges the start so accents land on the
cuts. It needs librosa, scipy and soundfile. IF no Python has them, use
the take as is, extended or trimmed with `<shared>/tools/bgm-extend.py`,
and record that.

**5. Pick the take yourself, by measurement:** tempo, vocal presence and
phrasing, energy shape, accents on the cuts. The other take goes to
`deletable/`. Record that the mix was measured, not heard.

**Lyrics must be original, never copyrighted.** Never copy, quote or
lightly reword the source song's lyrics, never build the hook on its title
phrase, never borrow from any other known song. Check before generating:

```bash
python3 "<cloner>/tools/lyrics_check.py" check "<materials>/audio/lyrics.txt" "<materials>/audio/source-lyrics.txt" --title "<song title>"
```

It flags any shared run of 4+ words and any title hook word; rewrite until
it passes. The same rule covers style tags: describe the sound, never name
the artist or song.

## Cut-outs (persona over a new background or graphics)

Pixelcut, exactly as the shared toolkit 3f says (`mode: Transparent`, VP9
WebM with real alpha, decode with `-c:v libvpx-vp9`, the alpha check, the
WebM used as it is).

## When a job fails

Read the error before reacting.

**`content_flagged`, or a fast `provider_error`** on content that is
obviously fine elsewhere, is a **filter decision**. Filters give no
reasons: don't guess one and present it as the cause. **Never tweak inputs
to sneak past a filter.** Retrying the same inputs once is fair. There is
no fallback model: Wan replacement and the Kling dance route work
differently, so swapping one for the other mid-clone conflicts. If either
refuses a clip, change the source clip or the approach, and record it.

**Every request to one model failing,** even trivial ones, is an
**outage**. Probe with a cheap harmless 4 s job once. Omni Flash 1.1 has no
backup route. Wait and retry on a schedule within the run; IF it stays
down, reply FAILED with the outage as the reason. Never switch to an
unlisted model.

**FAILED with `error: null`:** call `wait_ai_job` again with the same `jobId`
before planning a retake (see the lessons).

**Rejections are free.** Charges land only on completed jobs.

## Checking your output

Look before you deliver.

- **Frames:** compare against the source at the same timestamps: identity,
  pose, props, hands, framing, the shape of objects (laptops, phones).
  **No source face, hair or signature accessory survives.**
- **Burned-in text:** the source's captions or tags must not reappear.
- **Speech:** transcribe with `make-timings.py --txt` and check the words,
  then that the mouth forms them; check every speaking clip's **tail**
  against its own noise floor (see the lessons).
- **Cuts:** a big jump between consecutive frames means the model cut
  away, usually a sign it ignored the reference.
- **Audio:** loudness and clipping. Several Omni chunks: measure each
  chunk's pitch and level; a big spread is a lesson to propose (the voice
  match tool is not installed).
- **Length:** models round durations. Trim to the beat.

## Writing prompts

**Match the language to the look.** Decide which visual world the source
lives in: a phone held by hand, front camera, a lived-in room, window
light → **UGC casual**. A locked-off or moving rig, shaped light,
deliberate depth of field, a set, a grade → **professional**. Models
follow vocabulary more than intent.

- **WHEN it's UGC casual, never use professional photography or
  videography language, lighting included.** No lens or camera terms
  (85mm, bokeh, DSLR, cinematic, shallow depth of field), no lighting
  setups (softbox, key light, rim light, golden hour), no production words
  (colour grade, film look, editorial, campaign). Describe what a person
  filming on a phone would notice: *daylight from the window, the lamp is
  on, phone held at arm's length, a quick snapshot*. One "softbox" turns a
  believable UGC shot into a polished ad.
- **WHEN it's a professional shot, do the opposite:** craft vocabulary on
  purpose (lens, lighting setup and direction, camera move, depth of
  field, grade).
- **Keep one world per prompt.** If the source mixes them, describe what
  the camera actually sees and lean toward its dominant feel.
- **The finishing line changes with the world:** "Keep the casual quick
  phone snapshot look, no filters" is the UGC finish.
- **Short beats detailed.** Say what each reference is, then what to
  replace, change and retain, plus the prop or line. Add a clause only
  when a test shows it fixes a specific problem ("barefoot").
- **Never write "keep everything else exactly the same".**
- **Let references carry identity.** Never re-describe a person you pass
  as an image.
- **Name what matters and can't be seen:** the handled prop, the spoken
  line, the camera move.
- **WHEN the person must not talk, use no speech words at all** (*listen,
  hear, answer, question, conversation*). "Stays quiet with their lips
  closed and nods with an agreeing expression" kept the lips closed.
- **Pronunciation:** spoken brand names follow the Reword table in
  `<shared>/skills/working-memory.md` (read only).

## Where this knowledge is thin

Trust your checks more than this file here, and record in the metadata
that you were on new ground:

- **Wan 3.0 at 720p:** held up for full-body figures and the face matched
  the persona exactly. Tight close-ups at 720p are less proven: look
  closely at the first one.

## Cost and speed at a glance

Live Spira prices, 2026-10-24 (`spira ai models get <id>`). These
replace the older figures in the original Cloner notes. Always confirm
with `models get` before planning.

| Job | Model | Price | Typical render |
|-|-|-|-|
| Persona base | `ai-influencer-image` (Soul) | 7 per image | under 1 min |
| Persona edits, plates, elements | `gpt-image-2` | 4 (1K), 5 (2K), 8 (4K) | about 40 s |
| Talking to camera | `gemini-omni-flash-1.1` | 41 / 54 / 68 / 81 (4/6/8/10 s, any resolution) | 2–4 min |
| Talking-head fallback (whole video only) | `seedance-1.5-pro` | 8.86/s at 1080p with sound | about 3 min |
| Person replacement, extra shots, motion + speech | `wan-3.0` | **720p 6.18/s** (480p 3.09, 1080p 12.35) | 3–8 min per clip |
| Dances only | `kling-3.0-motion-control` | 9.52/s pro, 7.14/s standard | 6–8 min per clip |
| Cut-out | `pixelcut-video-background-removal` | 2.2/s of source | about 1 min |
| Source understanding | source-understanding job (Gemini 3.1 Pro, skill section 7) | about 2 | about 30 s |
| Transcript | `make-timings.py` (Scribe) | about 1 per minute | seconds |
| Music | `suno-music` (`v5_5`, custom mode) | 7 per job = 2 songs of about 65 s | about 25 s |
| Voice line | `elevenlabs-text-to-speech` | 0.01 per character | seconds |
| Ambience bed, sound effect | `elevenlabs-sound-effects` | 12 per generation (0.5–30 s) | seconds |

Rough cost per 10 s of persona video: **Wan 720p about 62 < Omni Flash
about 81 < Wan 1080p about 124.** A 14 s outfit-change clone by Wan
replacement: 107 for the clips, plus about 5 for the plate. A 15 s clone
lands at about 95–130 in all.
