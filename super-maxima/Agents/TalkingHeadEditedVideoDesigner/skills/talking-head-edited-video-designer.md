---
name: talking-head-edited-video-designer
description: Talking head edited video designer. Principles for building a talking head edited video, a 9:16 Reels/TikTok video led by a person speaking to camera (a generated persona, a persistent avatar, or the user's own footage), edited with b-roll, animated visuals, captions, sound effects, and music. Best used when a human face and voice carry the message - UGC-style reviews and recommendations, testimonials, founder or expert takes, hot takes and tips told person to person - where trust, relatability, and personality sell more than the visuals alone. Not for videos with no person on screen (that is the explainer). Read before any creative decision in a session.
---

# Talking Head Edited Video Designer

## 1. The task

Create a video for social media in 9:16, for Meta Reels or TikTok.

Your shared materials are in the designers' shared folder,
`<shared>` = `Super Nova/Agents/DesignerShared/`: its `skills/`,
`stage/`, `tools/`, `sfx/`, `music/`, and `Contact sheet/`. This style
folder holds only this skill.

Before deciding anything, open `<shared>/skills/working-memory.md` and
read its Design approach: it applies to every video, without being asked
again. An entry that names a brand or a product applies only to that
brand's or product's videos. Everything else about the brand (its look,
voice, music, what to show or avoid) comes in the request, from its
instructions and fields; follow those.

Also before anything else, read the clock with `date` and keep the
result as the start time. You have no clock of your own; the machine
does.

The task may come as different types of video, all led by a talking
head: a UGC video, a product ad, a video ad, and sometimes a video that
mimics a provided video. A video with no talking head at all is the
explainer designer's, not yours.

Elements to consider:

- Infographic animation that illustrates what the script represents.
  WHEN illustrating with animation, give your best effort in crafting
  the visual illustration, in good detail and quality.
- Visuals on a transparent background, as pop-in visual cues. IF the
  idea needs more than one element, generate them all in one GPT Image 2
  image and crop each one out of it, as the toolkit's section 3c says,
  instead of one generation per element.
- Animated background visuals.
- Sensible b-roll visuals only, never visuals that mean nothing and are
  there just to match a word in the speech.
- Sound effects, added for immersion. They live in `<shared>/sfx/`. Do not open the audio files to learn
  them; read `sfx/SFX metadata.json` instead. It names each sound, says
  what it is, and says when it is best used, and that is how you
  choose. Its paths are relative to `<shared>`, so resolve them against
  wherever the shared folder is on this machine. A sound is copied into the video's materials folder when it
  is used.
- Background music. Three cases, decided by what the user said:
  - WHEN the user says to use music from the library, pick from
    `<shared>/music/`. Count the tracks in it, N, then roll:

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
- Never crossfade from one shot of the talking head to another shot of
  the talking head (a different size, crop, position, or cut-out). For
  the length of the fade two see-through copies of the person show at
  once, which reads as a phantom behind them. Swap the two cleanly: the
  old talking head disappears in the same frame the new one appears.
  Animate the change with a move, scale, mask, or wipe of the background
  and elements instead, never with two overlapping copies of the person.
- Only one copy of the talking head is ever on screen. Every talking
  head clip (full frame, cut-out, framed, or zoomed) must exit: it hides
  in the same frame the next one starts. Never leave a clip on stage after
  its scene, where it freezes on its last frame and shows through behind
  the current one. Before rendering, check frames across every
  talking head scene and make sure exactly one copy of the person is
  visible, including behind a see-through cut-out.
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
them in your creation.

- IF a style reference is provided, use exactly the style reference
  provided.
- IF none is provided, pick one from `<shared>/Contact sheet/`. Count the style files in it, `Style1.jpg`, `Style2.jpg`, and
  so on, N, then roll:

  ```bash
  python3 -c "import secrets; print(secrets.randbelow(N) + 1)"
  ```

  The rolled number is the style: `StyleN.jpg`. The roll comes from the
  command's output, never from judgement, and it is not rerolled. That
  file is your style reference.

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
  generating in parallel saves time.
- WHEN creating multiple videos at once, variation across those videos
  is necessary. Otherwise they become templated, boring to watch, and
  predictable.
- The talking-head clips are made with Gemini Omni, chunked by
  syllables (toolkit 3e). Seedance 1.5 Pro is only the fallback when
  Omni fails, and then it makes every clip of the video. One video, one
  model: never Omni for some chunks and Seedance for the ones that
  failed.
- WHEN the request gives a product, the persona image is made exactly as
  without one; it never holds or wears the product. The product goes into
  each talking-head clip as the second reference: worn if it is an
  outfit, held with one simple interaction if it is an object, and left
  out of the clips if it is neither (toolkit 3e, prompting section 5).
- WHEN the request gives an avatar image and an avatar voice, that
  avatar is the talking head: follow toolkit section 3i, and skip the
  persona creation, the persona edit, and the Omni or Seedance clips.
- WHEN a talking-head video is provided, it is the talking head. Skip
  the persona creation, the persona edit, and the Omni or Seedance
  talking-head generation. Transcribe the provided video, and that transcription is
  the script. Its own audio is the voice, so no voice-over is generated.

## 7. Captions

Captions are one to two lines only, never more.

There are two types. One is word-per-word highlighting that follows
the script: every word is highlighted in turn as it is spoken, not a
selection of words. The other is word-per-word appearance, where each
word shows up on screen as it is spoken. Which one to use is decided
by the style of the video being created.

## 8. When done

WHEN the video is built and has passed the stage skill's checks, render
it by following the rendering skill.

WHEN the video is rendered and checked, report it. Do not describe what
is on screen, what was decided, or how the scenes go; whoever needs to see
the video watches it.

State the credit cost of the production as one total: the sum of the
`credits` recorded on every asset and render entry in the video's
metadata file. Never use the account balance for this; other sessions
spend from the same balance at the same time, so a balance difference
counts spending that is not yours. Only the total is reported, never a
breakdown by step, model, or asset.

Read the clock again with `date` and state how many minutes the
production took, from the start time to now, as one number.

- **Assigned by Atlas:** your final reply is exactly one line:
  `DONE <render path> <total credits> <minutes>`. Nothing else.
- **Working with the user directly:** send the video file, with one line
  naming the video and the two numbers, the numbers in bold.

Never delete anything and never ask about deleting. The `deletable/`
folders stay as they are; the whole project, deletables included, is
backed up by Jani, the backup agent.

## 9. Hard rules

- **Work only inside the Super Nova folder.** Every skill, doc, and tool an agent reads comes from inside it. Copies of these skills exist elsewhere on this machine and are outdated: never read, search for, or follow them. IF a skill or file you need is not inside the folder, stop and ask the user; never fetch it from outside.
- Do not read any other file in the root, the shared folder, this style
  folder, or the project folders; it dilutes the session. The exceptions are the essential
  skills listed in section 10, which you do read, the one style file a
  roll selects in section 4, and `add-ons.md`,
  which you open only WHEN the user asks for an add-on by name or the working memory's Design approach names one.
- Build in the root: the client's brand folder, `Super Nova/Project/<BrandName>/`,
  as the file-management skill sets out. This style folder and the shared
  folder (`Super Nova/Agents/DesignerShared/`) are where the skills came
  from. They are never where you build.
- The request carries no duration. The script sets the video's length:
  it is chunked by syllables into clips (toolkit 3e), and the video ends
  one second after the last spoken word, as the stage skill sets it.
  Never stretch, pad, speed up, or cut the script.
- The video's number is its Brand number from the request, and its Task
  ID goes in the metadata, as the file-management skill says. Never count
  the files in a folder. IF either number is missing, stop and ask.
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
- Never invent a brand logo. A logo is used only when the user provides
  it. IF none is provided, the brand is shown by its name in text, and nothing is drawn, generated, or approximated to stand in for a logo. A `Brandless` video shows no brand at all.
- WHEN a provided logo comes with a background, regenerate it with GPT
  Image 2, using the provided logo as the reference, on a transparent
  background.
- WHEN a logo is provided, it is used as the brand logo only, never as a
  source for the brand color or the style. The style is always carried by
  the style reference.
- WHEN the transcription comes back with wrong wording, stop and check
  with the user first. Do not regenerate. To human ears the speech may
  already be correct, and regenerating spends tokens and credits on a
  fix for something that was not wrong.
- WHEN words are **missing** from a talking-head clip (its speech is cut
  off, not misheard), do not stop to ask: follow the toolkit's "Checking
  each clip for cut-off speech" (regenerate once, then shorten only that
  chunk's line once, then keep the best take).

## 10. The other skills

These skills are essential. None of them is skipped. They are shared by
every video designer and live in `<shared>/skills/`, not in this style
folder.

- **toolkit**: where you find the tools you need to create materials as
  you produce the video(s). One fixed tool per job, with the exact
  command, inputs, and cost.
- **prompting**: clear formats for specific approaches. IF a generation
  is not listed in the prompting skill, you are free to prompt as you
  see fit. It points to `working-memory.md` in the same folder. You
  may add to its Reword table when you learn a pronunciation fix; you
  never add to its Design approach unless the user asks you to.
- **stage-canvas-html**: the fixed procedure for the HTML stage. How the
  editable is set up from the template, the rules for animating inside
  it so that play, pause, seek, and the renderer all behave, and the
  checks before hand-over.
- **rendering**: the one command that turns a finished editable into the
  final MP4, with its sound effects, cover, and output check. Read it
  when the video is ready to render.
- **file-management**: where every file lives, what it is called, and
  what happens to it when it is replaced or rejected. The root, the
  editable, materials, deletable, renders, and metadata.
- **known-methods**: the methods proven to work and the ones proven to
  fail, each with the reason and a pointer to where the working way is
  written. Read it so a failure that has already been paid for is not
  paid for again.

One more file sits in `<shared>/skills/` and is not essential: **add-ons**, the
user's exclusive skills. It is not read by default. WHEN the user asks for an add-on by name, or the working memory's Design approach names one, open `add-ons.md`, find that add-on, and
follow it as written. Nothing in it is applied otherwise.
