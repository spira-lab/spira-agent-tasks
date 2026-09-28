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
- Sound effects, added for immersion. Choose them from
  `sfx/SFX metadata.json`, which names each sound, says what it is, and
  says when it is best used; never open the audio files to learn them.
  How a chosen sound is placed and how loud it plays is in the stage
  skill.
- Background music. Three cases, decided by what the user said:
  - WHEN the user says to use music from the library, pick from the
    package's `music/` folder. Count the tracks in it, N, then roll:

    ```bash
    python3 -c "import secrets; print(secrets.randbelow(N) + 1)"
    ```

    The tracks are numbered, `Music1.mp3`, `Music2.mp3`, and so on;
    the rolled number is the track. The roll comes from the command's
    output, never from judgement, and it is not rerolled. Do not open
    the tracks to learn them.
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

Do not start with an empty screen: the first frame already shows the
hook.

Visual hooks are always scroll-stopping. A zoom out, a motion reaction,
highlighted text with a talking head, an illustration of curiosity:
these are some of the hook styles you could use. A hook is necessary to
make the video interesting to view.

## 4. Style reference

A style reference is where the design comes from. WHEN the user
provides one (a style sheet, or a reference video turned into a contact
sheet as working memory says), put real effort into carrying its look
into the video: palette, type, layout, card and sticker treatment,
pacing. It is a source of look, never of story. IF none is provided,
decide your own style.

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
  style reference is followed. IF there is none either, match the
  color to the type of video you are creating, based on feel. Brand
  is the priority: disregard the reference's palette whenever a brand
  color is provided.

## 6. Several videos in one request

Do not make them one at a time. Draft a plan for each, run every
generation of every video in one parallel batch, and give each video
its own concept: several videos that look alike are templated, boring
to watch, and predictable.

## 7. Captions

Captions are one to two lines only, never more.

There are two types. One is word-per-word highlighting that follows
the script: every word is highlighted in turn as it is spoken, not a
selection of words. The other is word-per-word appearance, where each
word shows up on screen as it is spoken. Which one to use is decided
by the style of the video being created.

Captions and any on-screen text carry the script's spelling, never the
transcription's. WHEN Whisper hears a word differently from the script
(a hyphenated word split, a brand name misheard), keep its timing and
write the script's word. Do not regenerate the voice for it: to human
ears the speech is usually right.

## 8. When done

A video is done when it is rendered, its cover is set, and it is
published (file-management section 6). Then:

1. WHEN the `submit_result` tool is available, call it with the render
   as `video`, the published URL as `publicUrl`, and a post caption as
   `caption`.
2. End with a short final message: the video's name and published URL,
   and anything you had to assume or skip, such as a tag that did not
   exist. Do not describe what is on screen; the operator sees it.

Credits and minutes are measured by the platform from the jobs the run
started; do not tally them. Deletable files are kept: the operator
empties them, never the session.

## 9. Hard rules

- Read only what the skills tell you to: the essential skills in
  section 10, `working-memory.md`, `sfx/SFX metadata.json`, the stage
  template, and the editable you are working on. Never open another
  editable html in the root; reading it anchors you to it and you copy
  it. Open `add-ons.md` only WHEN the user asks for an add-on by name
  or a Preference names one.
- Respect the Meta and TikTok guidelines and their UI. Nothing that
  must be seen or read may be obstructed by the app's UI. The safe
  zone, in pixels on the 1080 x 1920 canvas, is x 70 to 1005 and y 230
  to 1255, then x 70 to 890 from y 1255 down to 1615, the right edge
  stepping in where the like, comment, and share column sits. It
  governs the key elements only: faces, the talking head, text that has
  to be read, the product, anything the viewer must not miss. It does
  not bound the composition. Backgrounds, animated backgrounds, ambient
  and secondary visuals, and the extension of the scene run to the
  edges and under the UI; a lower half left empty because it is outside
  the safe zone is wrong. The canvas centre is x 540, y 960, and the
  safe zone sits off it: compose to the canvas, then check the key
  elements against the zone.
- Captions sit in the lower part of the canvas, centred on x 540, never
  on the safe zone. A block up to 700 wide centred there clears the
  icon column at x 890; keep the wrap width within that and never shift
  the block sideways.
- The voice is always the loudest thing in the mix. Sound effects sit
  under it and above the music bed; the renderer sets the levels.
- Never invent a brand logo. A logo is used only when the user provides
  it. IF none is provided, the brand is shown by its name in text, and
  nothing is drawn, generated, or approximated to stand in for a logo.

## 10. The other skills

These skills are essential. None of them is skipped.

- **toolkit**: the one model for each job, how a generation is run
  (`tools/gen.py`), and what each costs.
- **prompting**: the fixed prompt format for each model. IF a
  generation is not listed there, prompt as you see fit under its
  principles. It points to the Reword table in `working-memory.md`,
  which you may add to when you learn a pronunciation fix.
- **stage-canvas-html**: the HTML stage. How the editable is set up,
  the rules for animating inside it, the audit, the sound effects, and
  the render.
- **file-management**: where every file lives, what it is called, what
  happens to it when it is replaced, and how a render is published.
- **known-methods**: methods proven to work and to fail, with the
  reason. Read it so a failure already paid for is not paid for again.

One more file sits beside these and is not essential: **add-ons**, the
user's exclusive techniques. WHEN the user asks for an add-on by name,
or a Preference in working memory names one for the brand or project
at hand, open `add-ons.md`, find that add-on, and follow it as written.
