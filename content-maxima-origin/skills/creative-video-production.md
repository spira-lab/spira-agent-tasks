---
name: creative-video-production
description: Creative video production and principles for building a video: what the task is, how to reason about it, and the hard rules. Read before any creative decision in a session.
---

# Creative Video Production

## 1. The task

Create a video for social media in 9:16, for Meta Reels or TikTok.

Before deciding anything, open `skills/working-memory.md` and read its
Preferences. WHEN a preference names the brand or the
kind of project in front of you, it applies, without being asked
again.

Also before anything else, read the clock with `date` and keep the
result as the start time. You have no clock of your own; the machine
does.

**The script.** WHEN the user gives a script, it is spoken word for word:
never shorten, reword, or speed it up to fit a target length. Before any
generation, plan it with `tools/chunker.py` (toolkit 3e): the clip
lengths it adds up to, at 4.7 to 5.0 syllables a second, are its length.
IF that runs past the requested length, make the video as long as the
script needs and say so in the final message. Only a brief or an idea is
written to length. WHEN the user gives a voice-over recording, the
recording is the script and its length is the video's length; no script
is written and no speech is generated (toolkit section 3).

The task may come as different types of video: a UGC video with a
talking head, a VO explainer video, an animated short, a product ad, a
video ad, and sometimes a video that mimics a provided video.

**Every video has a talking head.** A presenter is the default, whatever
the type: an explainer, a product ad, or a list of tips still has a
person speaking it. WHEN the request gives no presenter photo, no
presenter video, and no supplied talking-head video, make one: the
persona from toolkit 3a, then the route section 3 of the toolkit names
for the voice. A chosen voice, a voice-over recording, a
product image, or a script that reads like an explainer never means no
talking head. Leave the presenter out only WHEN:

- the request explicitly says so: no talking head, no presenter, no
  avatar, faceless, voice-over only, or the like;
- a brand file that applies says never to use one.

Only then is the video presenter-less, with the voice-over from toolkit
3i. Not being sure a presenter fits is not a reason to leave one out.

**A supplied talking-head video is the talking head.** WHEN the request
has `Talking head supplied video:`, that exact video is the talking
head of the finished video, and its own voice is the voice-over. It
replaces every step that makes a presenter or speech: no Soul persona
(toolkit 3a), no GPT Image 2 avatar edit (3b), no talking-head clips (3e),
no HeyGen (3j), and no ElevenLabs (3i). Go straight to building the
video with it. Its speech is the script, word for word and in its own
language: nothing is written around it, and it is never muted,
re-voiced, cut, or retimed. Everything else applies as for any talking
head: the cut-out (3f), the animated elements, and the scene
variety of section 5. Toolkit 3k is the procedure.

Elements to consider:

- Infographic animation that illustrates what the script represents.
  WHEN illustrating with animation, give your best effort in crafting
  the visual illustration, in good detail and quality.
- Visuals on a transparent background, as pop-in visual cues.
- Animated background visuals.
- Sensible b-roll visuals only, never visuals that mean nothing and are
  there just to match a word in the speech.
- Sound effects, added for immersion. Choose them from
  `sfx/SFX metadata.json` (read it whole with `cat`), which names each sound, says what it is, and
  says when it is best used; never open the audio files to learn them.
  Each entry also has a category, tags and an intensity (subtle, medium
  or strong): subtle effects suit small on-screen moments, strong ones
  only the big moments.
  The audio is hosted, not in the package: fetch each sound you use into
  the video's materials with `python3 tools/fetch-resource.py sfx/<file>
  editable/materials/<name>/sfx/<file>`.
  Each sound plays at the volume stored in its file; adjust it only when
  asked (stage-canvas-html section 4a).
  How a chosen sound is placed is in the stage skill.
- Background music. Three cases, decided by what the user said:
  - WHEN the user says no music or no bgm, use none: nothing generated,
    nothing picked.
  - WHEN the user asks for new, original or generated music, generate
    it with the toolkit.
  - Otherwise, including WHEN the user says nothing about music, choose
    from the library, `music/Music metadata.json` (read it whole with
    `cat`); never open the tracks to learn them. Each entry gives the
    track's genre and style, mood, energy, tempo, instruments,
    structure, what it is best for and what to avoid it for, and its
    `gain_db`. Shortlist
    every track that fits the video's topic and tone, and the style the
    user asked for if they named one. Leave out tracks whose entry has
    `starts_immediately: false` or a `longest_silence_s` above 2, unless
    nothing else fits. Count the shortlist, N, then roll:

    ```bash
    python3 -c "import secrets; print(secrets.randbelow(N) + 1)"
    ```

    The rolled number is the track's position in the shortlist. The
    roll comes from the command's output, never from judgement, and it
    is not rerolled; it keeps one favourite from being picked every
    time. IF nothing fits, shortlist the whole file. The track is
    hosted, not in the package: fetch it as the bed with
    `python3 tools/fetch-resource.py music/<file>
    editable/materials/<name>/bgm.mp3`, and put the entry's `gain_db`
    on the music tag exactly as it reads: `<audio id="bgm" …
    data-gain-db="<gain_db>">`. It sits that track 10 dB under the
    voice and already honours a `mix_note` about the level; it is never
    estimated, rounded, or changed by ear, and the renderer refuses a
    library bed without it or with a value that is not the track's.
    Generated music carries no `data-gain-db`. WHEN the chosen entry
    carries a `mix_note`, follow it when laying the bed.

## 2. Principles

- WHEN creating an element, whether a UI design to illustrate
  something, an animation for an infographic, or any visual element, do
  it with best effort and no shortcuts. Never treat the project as a
  draft; treat it as high-value production.
- A video is boring IF it is the same scene all the way through. Put
  effort into mixing things up: pattern interrupts, scroll-stopping,
  disruptive by design for social media, changing things every few
  seconds. Not every talking head needs the talking person on screen
  from beginning to end.
- Avoid shortcut thinking. Fast work does not mean less effort. Fast
  work means doing things right, so that less revision is needed.
- The shape of the request varies. Some start as a descriptive ask,
  some as a very simple ask of what video to produce, some as a script
  and nothing else, some as just an idea. Come up with the idea that
  results in the best video for it. You are not bound to the listed
  video types alone.
- WHEN animating transitions, keep the animation smooth and avoid
  old-school, outdated transition styles.
- Always find the right balance of elements and avoid clutter. Avoid
  incomplete illustrations. Avoid big gaps in text line height and
  leading.

## 3. The hook

Do not start with an empty screen.

Visual hooks are always scroll-stopping. A zoom out, a motion reaction,
highlighted text with a talking head, an illustration of curiosity:
these are some of the hook styles you could use. A hook is necessary to
make the video interesting to view.

## 4. Style sheet

Style sheets are where you get the style of the design from. They are
your source of design inspiration. You must put effort into visualizing
them in your creation. A style sheet is provided in the chat. IF none
is provided, ignore this section and decide your own style.

## 5. Tips

**Type is designed, never default.** Every video has a type system
taken from its style sheet, or decided to fit the video when none is
given: a headline face, an accent treatment, and a caption face, from
the `fonts/` library (stage skill section 2). Carry the style's
treatment: weight contrast (a heavy word beside light ones), an italic
serif accent word inside a sans headline, a coloured key word, a
highlight box or pill behind a word, tight tracking on stacked lines,
outline or glow where the style has it. Headlines are set tight, line
height 0.95 to 1.1. Text set in the system fonts with one weight and one
colour is a draft.

- WHEN making a talking head with a disappearing background, use the
  main talking head video, with the background-removed talking head on
  top, and fade the background out.
- Play with different zoom sizes of the talking head throughout the
  video, scene to scene.
- Word-per-word zoom in on the avatar is good for tension lines; it
  brings impact to the delivery.
- WHEN creating a background, always consider adding animation, subtle
  but not too subtle. Animation adds the professional feel to the
  video, rather than a stale, lazily done, send-it-off project.
- Color decisions match the brand. IF no brand color is provided, the
  style guide is followed. IF no style guide is provided either, match
  the color to the type of video you are creating, based on feel. Brand
  is the priority: disregard the style guide's color palette whenever a
  brand color is provided.

## 6. Conditionals

- WHEN creating multiple videos at once, do not do them one at a time.
  Draft a plan for each video, and do any shared approach in parallel;
  rendering in parallel saves time.
- WHEN creating multiple videos at once, variation across those videos
  is necessary. Otherwise they become templated, boring to watch, and
  predictable.

## 7. Captions

Captions are one line per phrase, made by `tools/captions.py` (stage
skill section 4b); style them, never write them by hand.

There are two types. One is word-per-word highlighting that follows
the script: every word is highlighted in turn as it is spoken, not a
selection of words (`--style highlight`). The other is word-per-word
appearance, where each word shows up on screen as it is spoken
(`--style appear`). Which one to use is decided by the style of the
video being created.

Captions and any on-screen text carry the script's spelling, never the
transcription's; the tool already does this for captions.

## 8. When done

WHEN the video is rendered and checked, it is finished, and a finished
video is published rather than left in the local workspace: host it with
the `host_file` tool, as file-management section 6 says, and record the
hosted URL in its metadata. Then, WHEN the `submit_result` tool is
available, call it with the render as `video`, the hosted URL as
`publicUrl`, and a post caption as `caption`.

Then report to the user. Do not describe what is on screen, what was
decided, or how the scenes go; the user sees all of that in the video.
The report is one line naming the video and its hosted URL, then the
minutes taken, then the deletable sizes below. Nothing else. Put the
numbers in bold so they can be spotted at a glance: the minutes taken
and the three sizes. Everything else stays plain. Credits are measured
by the platform from the jobs the run started; do not tally them.

Read the clock again with `date` and state how many minutes the
production took, from the start time to now, as one number.

Then delete the deletable files created during the production, without
asking, to reduce the space the project takes, and report three sizes:
the project's total size before, the size of the deletable files
removed, and the size that remains.

## 9. Hard rules

- Do not read any other file in the root, the package, or the project
  folders; it dilutes the session. The exceptions are the essential
  skills listed in section 10, `skills/working-memory.md`,
  `sfx/SFX metadata.json`, `music/Music metadata.json` and
  `fonts/fonts.md`, which you do read, and `add-ons.md`,
  which you open only WHEN the user asks for an add-on by name or a
  Preference in working memory names one.
- Build in the root: the folder the session was opened in. The package
  is where the skills came from, and it may be a different folder. It
  is never where you build, even when everything you read lives there.
- Never open another editable html in the same project folder. Reading
  it anchors you to it and you copy it. The only html you open is the
  stage template and the editable you are working on.
- Respect the Meta and TikTok guidelines and their UI. Nothing that
  must be seen or read may be obstructed by the app's UI. The stage
  template draws both UIs with one shared safe zone as a guide layer,
  in pixels on the 1080 x 1920 canvas: x 70 to 1005 and y 230 to 1255,
  then x 70 to 890 from y 1255 down to 1615, the right edge stepping in
  where the like, comment, and share column sits. The safe zone
  governs the key elements only: faces, the talking head,
  text that has to be read, the product, anything the viewer must not
  miss. It does not bound the composition. The composition fills the
  whole 1080 x 1920 canvas: backgrounds, animated backgrounds, ambient
  and secondary visuals, and the extension of the scene run to the
  edges and under the UI. A lower half left empty because it is outside
  the safe zone is wrong; the zone tells you where the key elements go,
  not where the picture stops. Never treat a safe zone as the true
  centre. The canvas centre is x 540, y 960, and the safe zones sit off
  it; compose to the canvas, then check the key elements against the
  zone. Captions and subtitles sit in the lower part of the canvas,
  centred on the canvas at x 540, never on the safe zone. A block up to
  700 wide centred there clears the icon column at x 890; keep the wrap
  width within that and never shift the block sideways. A caption whose
  centre is not x 540 is wrong, and so is one that runs under the
  like, comment, and share buttons.
- The voice is always the loudest thing in the mix. Sound effects sit
  under it and above the music bed. The levels are fixed by default: each
  effect plays at the volume stored in its file and the renderer sets the
  voice and the bed (a library bed at the `data-gain-db` copied from its
  entry). A session changes a level only when the request or a review
  comment asks, and only with the attributes of stage-canvas-html
  section 4a.
- Never invent a brand logo. A logo is used only when the user provides
  it. IF none is provided, the brand is shown by its name in text, and
  nothing is drawn, generated, or approximated to stand in for a logo.
- WHEN the transcription comes back with wrong wording, stop and check
  with the user first. Do not regenerate. To human ears the speech may
  already be correct, and regenerating spends tokens and credits on a
  fix for something that was not wrong.

## 10. The other skills

These skills are essential. None of them is skipped.

- **toolkit**: the one model for each job, how a generation is run
  (`submit_ai_job`, then `wait_ai_job`), its inputs, and what each costs.
- **prompting**: clear formats for specific approaches. IF a generation
  is not listed in the prompting skill, you are free to prompt as you
  see fit. It points to `skills/working-memory.md`. You
  may add to its Reword table when you learn a pronunciation fix; you
  never add to its Preferences unless the user asks you to.
- **stage-canvas-html**: the fixed procedure for the HTML stage. How the
  editable is set up from the template, the rules for animating inside
  it so that play, pause, seek, and the renderer all behave, the checks
  before hand-over, and the export to MP4.
- **file-management**: where every file lives, what it is called, and
  what happens to it when it is replaced or rejected. The root, the
  editable, materials, deletable, renders, and metadata.
- **known-methods**: the methods proven to work and the ones proven to
  fail, each with the reason and a pointer to where the working way is
  written. Read it so a failure that has already been paid for is not
  paid for again.

One more file sits beside these and is not essential: **add-ons**, the
user's exclusive skills. It is not read by default. WHEN the user asks
for an add-on by name, or a Preference in working memory names one for
the brand or project at hand, open `add-ons.md`, find that add-on, and
follow it as written. Nothing in it is applied otherwise.
