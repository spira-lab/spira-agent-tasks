---
name: creative-video-production
description: Creative video production and principles for building a video: what the task is, how to reason about it, and the hard rules. Read before any creative decision in a session.
---

# Creative Video Production

## 1. The task

Create a video for social media in 9:16, for Meta Reels or TikTok.

Before deciding anything, open `working-memory.md` beside the skills
and read its Preferences. WHEN a preference names the brand or the
kind of project in front of you, it applies, without being asked
again.

Also before anything else, read the clock with `date` and keep the
result as the start time. You have no clock of your own; the machine
does.

The task may come as different types of video: a UGC video with a
talking head, a VO explainer video, an animated short, a product ad, a
video ad, and sometimes a video that mimics a provided video.

Elements to consider:

- Infographic animation that illustrates what the script represents.
  WHEN illustrating with animation, give your best effort in crafting
  the visual illustration, in good detail and quality.
- Visuals on a transparent background, as pop-in visual cues.
- Animated background visuals.
- Sensible b-roll visuals only, never visuals that mean nothing and are
  there just to match a word in the speech.
- Sound effects, added for immersion. They live in the `sfx/` folder of
  the package, beside `skills/`. Do not open the audio files to learn
  them; read `sfx/SFX metadata.json` instead. It names each sound, says
  what it is, and says when it is best used, and that is how you
  choose. Its paths are relative to the package folder, so resolve them
  against wherever the package is on this machine. A sound is copied into the video's materials folder when it
  is used. WHEN a sound effect plays, it never overpowers the voice,
  and it is still audible over the background music: under the voice,
  above the bed. A sound effect the viewer notices more than the words
  is too loud. WHEN the voice comes from ElevenLabs, set the effects
  lower still; the stage skill gives the level.
- Background music. Three cases, decided by what the user said:
  - WHEN the user says to use music from the library, pick from the
    package's `music/` folder. Count the tracks in it, N, then roll:

    ```bash
    python3 -c "import secrets; print(secrets.randbelow(N) + 1)"
    ```

    The tracks are numbered, `Music1.mp3`, `Music2.mp3`, and so on;
    the rolled number is the track. The roll comes from the command's
    output, never from judgement, and it is not rerolled. There is no
    metadata for the music and no description per track; do not open
    the tracks to learn them, just use the one the roll names.
  - WHEN the user says nothing about music, generate it with the
    toolkit.
  - WHEN the user says no music or no bgm, use none: nothing generated,
    nothing picked.

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

Captions are one to two lines only, never more.

There are two types. One is word-per-word highlighting that follows
the script: every word is highlighted in turn as it is spoken, not a
selection of words. The other is word-per-word appearance, where each
word shows up on screen as it is spoken. Which one to use is decided
by the style of the video being created.

## 8. When done

WHEN the video is rendered and checked, it is finished, and a finished
video is published rather than left in the local workspace: upload it to
the Social Post Assets library with the Spira CLI, as file-management
section 6 says, and record the upload in its metadata.

Then send the video file to the user. Do not describe what is on screen, what was decided, or how the
scenes go; the user sees all of that in the video. The report is one
line naming the video, then the two numbers below, then the deletable
question. Nothing else. Put the numbers in bold so they can be spotted
at a glance: the credit total, the minutes taken, and the three sizes
in the deletable question. Everything else stays plain.

State the credit cost of the production as one total: the sum of the
`credits` recorded on every asset and render entry in the video's
metadata file. Never use the account balance for this; other sessions
spend from the same balance at the same time, so a balance difference
counts spending that is not yours. Only the total is reported, never a
breakdown by step, model, or asset.

Read the clock again with `date` and state how many minutes the
production took, from the start time to now, as one number.

Then ask the user whether they want the deletable files created during
the production deleted, to reduce the space the project takes. Give
three sizes with the question: the project's total size, the size of
the deletable files, and the size that remains after purging them.
Delete only IF the user says yes; the deletable folders are never
emptied on your own decision.

## 9. Hard rules

- Do not read any other file in the root, the package, or the project
  folders; it dilutes the session. The exceptions are the essential
  skills listed in section 10, which you do read, and `add-ons.md`,
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
- Sound effects are never louder than the voice. The voice is always
  the loudest thing in the mix; every sound effect sits under it, at the
  level the stage skill gives, while staying audible over the music.
- Never invent a brand logo. A logo is used only when the user provides
  it. IF none is provided, the brand is shown by its name in text, and
  nothing is drawn, generated, or approximated to stand in for a logo.
- WHEN the transcription comes back with wrong wording, stop and check
  with the user first. Do not regenerate. To human ears the speech may
  already be correct, and regenerating spends tokens and credits on a
  fix for something that was not wrong.

## 10. The other skills

These skills are essential. None of them is skipped.

- **toolkit**: where you find the tools you need to create materials as
  you produce the video(s). One fixed tool per job, with the exact
  command, inputs, and cost.
- **prompting**: clear formats for specific approaches. IF a generation
  is not listed in the prompting skill, you are free to prompt as you
  see fit. It points to `working-memory.md` in the same folder. You
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
