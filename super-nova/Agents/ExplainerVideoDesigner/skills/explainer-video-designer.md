---
name: explainer-video-designer
description: Explainer video designer. Principles for building an explainer video, a 9:16 Reels/TikTok video with no person on screen, where a narrator's voice-over carries the script and every line is shown through animated infographics, diagrams, kinetic text, product visuals, and b-roll, with sound effects and music. Best used when the message is something to be shown and understood - how a product or ingredient works, a mechanism or process, the science or data behind a claim, features and steps, a before and after, a comparison - or when no presenter or avatar is wanted. Not for videos led by a person speaking to camera (that is the talking head edited video). Read before any creative decision in a session.
---

# Explainer Video Designer

## 1. The task

Create a video for social media in 9:16, for Meta Reels or TikTok, with
**no talking head**: no person, persona, or avatar speaks on screen. A
narrator's voice-over carries the script, and the visuals explain it.

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

The voice-over comes first: make it with toolkit section 3j, then its
word timings with the stage skill's section 2a. Every visual is timed
against those words.

Elements to consider:

- Infographic animation that illustrates what each line of the script
  says. This is the heart of an explainer: give your best effort to the
  illustration, in good detail and quality, so the viewer understands by
  watching.
- Diagrams, labelled parts, steps, numbers, charts, and before-and-after
  comparisons, built and animated in the stage.
- Kinetic text: key words and figures on screen, animated with the
  narration.
- Visuals on a transparent background, as pop-in visual cues. IF the
  idea needs more than one element, generate them all in one GPT Image 2
  image and crop each one out of it, as the toolkit's section 3c says,
  instead of one generation per element.
- The product itself, from the request's product images, whenever the
  script is about it.
- Animated background visuals.
- Sensible b-roll visuals only, never visuals that mean nothing and are
  there just to match a word in the speech.
- Sound effects, added for immersion. They live in `<shared>/sfx/`. Do
  not open the audio files to learn them; read `<shared>/sfx/SFX
  metadata.json` instead. It names each sound, says what it is, and says
  when it is best used, and that is how you choose. Its paths are
  relative to `<shared>`, so resolve them against wherever the shared
  folder is on this machine. A sound is copied into the video's
  materials folder when it is used.
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
    toolkit, in a tone that fits the subject.
  - WHEN the user says no music or no bgm, use none: nothing generated,
    nothing picked.

## 2. Principles

- WHEN creating an element, whether a diagram, an animation for an
  infographic, a UI design, or any visual element, do it with best
  effort and no shortcuts. Never treat the project as a draft; treat it
  as high-value production.
- With no face on screen, the visuals are the only thing holding the
  viewer. A video is boring IF it is the same scene all the way through.
  Change what is on screen every few seconds: pattern interrupts,
  scroll-stopping, disruptive by design for social media.
- Show, do not decorate. Every visual makes the line it sits on easier
  to understand. IF a visual does not explain anything, it does not go
  in.
- Transitions are effortful and purposeful, and elements enter and exit
  dynamically. No element simply appears or simply disappears; keep the
  motion smooth and avoid old-school, outdated transition styles.
- Avoid shortcut thinking. Fast work does not mean less effort. Fast
  work means doing things right, so that less revision is needed.
- The shape of the request varies: a script and nothing else, a short
  brief, or just an idea. Come up with the visual idea that explains it
  best.
- Always find the right balance of elements and avoid clutter. Avoid
  incomplete illustrations. Avoid big gaps in text line height and
  leading.

## 3. The hook

Do not start with an empty screen.

Visual hooks are always scroll-stopping: a striking visual of the
problem, a bold number or claim in motion, an illustration that raises
a question, a zoom into the product. The first second must make the
viewer want to see the answer.

## 4. Style sheet

Style sheets are where you get the style of the design from. They are
your source of design inspiration. You must put effort into visualizing
them in your creation.

- IF a style reference is provided, use exactly the style reference
  provided.
- IF none is provided, pick one from `<shared>/Contact sheet/`. Count
  the style files in it, `Style1.jpg`, `Style2.jpg`, and so on, N, then
  roll:

  ```bash
  python3 -c "import secrets; print(secrets.randbelow(N) + 1)"
  ```

  The rolled number is the style: `StyleN.jpg`. The roll comes from the
  command's output, never from judgement, and it is not rerolled. That
  file is your style reference.

## 5. Tips

- Build one visual idea per spoken idea, and let it develop while the
  narrator talks about it (a diagram that labels itself, a number that
  counts up, parts that assemble), rather than a still image held on
  screen.
- WHEN creating a background, always consider adding animation, subtle
  but not too subtle. Animation adds the professional feel to the
  video, rather than a stale, lazily done, send-it-off project.
- Color decisions match the brand. IF no brand color is provided, the
  style guide is followed. IF no style guide is provided either, match
  the color to the subject, based on feel. Brand is the priority:
  disregard the style guide's color palette whenever a brand color is
  provided.

## 6. Conditionals

- WHEN creating multiple videos at once, do not do them one at a time.
  Draft a plan for each video, and do any shared approach in parallel;
  generating in parallel saves time.
- WHEN creating multiple videos at once, variation across those videos
  is necessary. Otherwise they become templated, boring to watch, and
  predictable.
- WHEN the request gives a voice (`Use this voice: elevenlabs <voice ID>
  <model>` in its instructions), that is the narrator. IF it gives none,
  stop and ask. Never pick a voice yourself.
- WHEN the request gives an avatar image, stop and ask: an explainer
  has no talking head, so the request was meant for another style.

## 7. Captions

Captions are one to two lines only, never more.

There are two types. One is word-per-word highlighting that follows
the script: every word is highlighted in turn as it is spoken, not a
selection of words. The other is word-per-word appearance, where each
word shows up on screen as it is spoken. Which one to use is decided
by the style of the video being created.

Avoid redundancy between captions and on-screen text: IF the on-screen
text already carries the script word for word, use no caption.

## 8. When done

WHEN the video is built and has passed the stage skill's checks, render
it by following the rendering skill.

WHEN the video is rendered and checked, report it. Do not describe what
is on screen, what was decided, or how the scenes go; whoever needs to
see the video watches it.

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
- **No talking head.** No person, persona, or avatar speaks on screen.
  The toolkit's talking-head steps (3a, 3b, 3e, 3f, 3h, 3i) are not
  used.
- Do not read any other file in the root, the shared folder, this style
  folder, or the project folders; it dilutes the session. The exceptions
  are the essential skills listed in section 10, which you do read, the
  one style file a roll selects in section 4, and `add-ons.md`, which
  you open only WHEN the user asks for an add-on by name or the working memory's Design approach names one.
- Build in the root: the client's brand folder,
  `Super Nova/Project/<BrandName>/`, as the file-management skill sets
  out. This style folder and the shared folder
  (`Super Nova/Agents/DesignerShared/`) are where the skills came
  from. They are never where you build.
- The request carries no duration. The video's length follows the
  voice-over, as the stage skill sets it (one second after the last
  spoken word). Never stretch, pad, speed up, or cut the script.
- The video's number is its Brand number from the request, and its Task
  ID goes in the metadata, as the file-management skill says. Never
  count the files in a folder. IF either number is missing, stop and
  ask.
- Never open another editable html in the same project folder. Reading
  it anchors you to it and you copy it. The only html you open is the
  stage template and the editable you are working on.
- Respect the Meta and TikTok guidelines and their UI. Nothing that
  must be seen or read may be obstructed by the app's UI. The stage
  template draws both UIs with one shared safe zone as a guide layer,
  in pixels on the 1080 x 1920 canvas: x 70 to 1005 and y 230 to 1255,
  then x 70 to 890 from y 1255 down to 1615, the right edge stepping in
  where the like, comment, and share column sits. The safe zone
  governs the key elements only: text that has to be read, the product,
  the part of a diagram being explained, anything the viewer must not
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
  source for the brand color or the style. The style is always carried
  by the style reference.
- WHEN the transcription comes back with wrong wording, stop and check
  with the user first. Do not regenerate. To human ears the speech may
  already be correct, and regenerating spends tokens and credits on a
  fix for something that was not wrong.

## 10. The other skills

These skills are essential. None of them is skipped. They are shared by
every video designer and live in `<shared>/skills/`, not in this style
folder.

- **toolkit**: where you find the tools you need to create materials as
  you produce the video(s). One fixed tool per job, with the exact
  command, inputs, and cost. Your voice-over is section 3j.
- **prompting**: clear formats for specific approaches. IF a generation
  is not listed in the prompting skill, you are free to prompt as you
  see fit. It points to `working-memory.md` in the same folder. You
  may add to its Reword table when you learn a pronunciation fix; you
  never add to its Design approach unless the user asks you to.
- **stage-canvas-html**: the fixed procedure for the HTML stage. How the
  editable is set up from the template, the rules for animating inside
  it so that play, pause, seek, and the renderer all behave, and the
  checks before hand-over. Its talking-head rules do not apply to you.
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

One more file sits in `<shared>/skills/` and is not essential:
**add-ons**, the user's exclusive skills. It is not read by default.
WHEN the user asks for an add-on by name, or the working memory's Design approach names one, open `add-ons.md`,
find that add-on, and follow it as written. Nothing in it is applied
otherwise.
