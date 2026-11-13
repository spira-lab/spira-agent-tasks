---
name: podcast-video-designer
description: Podcast video designer. The fixed procedure for building a podcast video, a 9:16 Reels/TikTok clip of two AI co-hosts in conversation, each line spoken in its own voice and lip-synced, cut like a real podcast edit with full shots, pre-lap cuts, split-screen listening shots, jump zooms, captions, and a music bed. Best used when the message works as a conversation between two people - a topic discussed back and forth, a question and its answer, two takes on news or a trend, myth against fact, a story told between hosts. Needs a two-speaker script. Not for one person speaking to camera (that is the talking head edited video) or a narrator with no one on screen (that is the explainer). Read before any decision in a session.
---

# Podcast Video Designer

## 1. The task

Create a podcast video for social media in 9:16, for Meta Reels or
TikTok: two co-hosts talking, from a two-speaker script. Every step
below is fixed and done in order.

Your materials:

- This style folder, `<podcast>` = `Super Vega/Agents/PodcastVideoDesigner/`:
  this skill, the **podcast toolkit** (`skills/podcast-toolkit.md`), and
  the podcast tool (`tools/podcast.py`).
- The designers' shared folder, `<shared>` = `Super Vega/Agents/DesignerShared/`:
  the shared skills and the stage template.

Before deciding anything, open `<shared>/skills/working-memory.md` and
read its Design approach: it applies to every video, without being asked
again. An entry that names a brand or a product applies only to that
brand's or product's videos. Everything else about the brand comes in
the request, from its instructions and fields; follow those.

Also before anything else, read the clock with `date` and keep the
result as the start time. You have no clock of your own; the machine
does.

**The script.** Two speakers, `Podcaster 1` and `Podcaster 2`. Every turn starts with the speaker's label and a colon (`Podcaster 1: ...`), and each turn is one line of the edit. In the request the script may arrive on one line; the labels still mark every turn. Write
the script verbatim to `script.txt` in the materials folder. IF the
script does not have exactly two labelled speakers, stop and ask.

The procedure below is the whole build. A logo, a product image, a style
reference, or sound effects are used only when the request's
instructions say how; never improvise one in.

## 2. The build

`<m>` is the video's materials folder, `<root>/editable/materials/<name>/`
(the file-management skill sets the root and the name). Create the
editable, the materials folder, and the metadata file first, as
file-management says. Commands are in the podcast toolkit.

### Step 1. The co-hosts and the room

From the topic and the script, decide the two personas (who they are and how they look), the environment, the emotion of the conversation (serious, fun, or scary), and daytime or nighttime. The script never fixes their gender, age, or look; you cast them. Podcaster 1 is persona 1, on the left; Podcaster 2 is persona 2, on the right.

1. Generate both personas with Higgsfield Soul, both at once (toolkit
   section 3).
2. Generate the 16:9 2K two-shot of both, with the two Soul images as
   references, in the two-shot format (toolkit section 4).
3. Cut it in half and pad each half to a square: `split`.

### Step 2. The voices

Choose each co-host's voice from the voice library by their look
(toolkit section 5). Never the same voice for both. Then write
`<m>/cast.json`:

```json
{"speakers": {
  "Podcaster 1": {"side": "left",  "tag": "M", "voice": "<voice URL>"},
  "Podcaster 2": {"side": "right", "tag": "F", "voice": "<voice URL>"}
}}
```

The labels are exactly as they appear in the script. The tag goes into
every file name: `M` and `F`, or `M1` and `M2` for two men, `F1` and `F2` for two women.

Then `lines`. It splits the script into its lines (`lines.json`) and
prints them; check that every turn is there. Put any Reword spelling
into that line's `say` (toolkit section 6).

### Step 3. The conversation track

1. Voice every line as its own clip with `submit_ai_job` /
   `wait_ai_job` (toolkit section 6): `lines/01_M.mp3`,
   `lines/02_F.mp3`, and so on, in parallel batches of about 3.
2. `join`: the lines joined in order with a 0.35 second pause between
   turns, into `vo.mp3`. It notes the start and end time of every line.
   The edit is timed from these.

### Step 4. Plan the shots, before any clip is rendered

Read the line times `join` printed and choose:

- **Pre-lap cuts.** A few lines where the cut lands on the next person
  before the current speaker finishes. `mark <m> prelap <n> ...`, n
  being the next person's line. Their audio gets 1 second of silence at
  its start, so their clip starts 1 second early: they sit silent while
  the previous line ends, then they speak. Never choose a pre-lap cut
  out of a line shorter than about 1.5 seconds (the tool refuses it).
- **Listening shots.** One or two long lines from one speaker.
  `mark <m> listen <n>`, n being the long line. The other person's
  previous line gets silence at its end, equal to the pause, the long
  line, and the pause. That silent part becomes their listening footage
  in the split screen.

Then `pad`: it writes each line's padded audio (`lines/NN_TAG-pad.mp3`)
and the time each clip starts on the timeline (`clip_start` in
`lines.json`).

### Step 5. The talking clips

1. `host_file` for the two padded halves and every padded line; write
   the URLs into `cast.json` and `lines.json`.
2. Test: submit the shortest line only (toolkit section 7) and look at a
   frame from it. IF the person, the framing, or the lip-sync is wrong,
   stop and fix it before rendering the rest.
3. Submit every other line, in batches of about 3, into
   `clips/NN_TAG.mp4`.
4. `check`: every clip as long as its audio, the pre-lap and listening
   silences still there. Submit a failing clip again for that line only.

### Step 6. Word timings and captions

1. `align`: ElevenLabs Scribe (Whisper only as the
   fallback, 2026-10-22), word timestamps on `vo.mp3`, then the
   words aligned to the script, so captions use the script's exact
   spelling (e.g. Niño) with Whisper's timing. Saved as `timings.json`.
2. `captions`: the caption groups, at most 3 words, broken at
   punctuation, quoted phrases kept together, never split across
   speakers. Saved as `captions.json`.

### Step 7. The music

Generate an instrumental that fits the topic with Eleven Music, about
the video's length plus 1 second (toolkit section 8), saved as
`bgm.mp3`. Then `music`, and put the `data-volume` and `data-under` it
prints on the editable's bgm tag: the music sits about 16 dB under the
voices.

### Step 8. The edit

Build the edit in the HTML stage, as the stage skill sets out. The
editable is a copy of `<shared>/stage/stage-9x16.html`, and everything
it loads lives in `materials/<name>/`: `vo.mp3`, `bgm.mp3`,
`timings.json`, and `clips/`.

- **`vo.mp3` is the master audio.** Every clip is a muted `<video>`
  placed at its `clip_start` on the timeline (`data-start` in
  milliseconds), as the stage skill's rule 11 says.
- **Full shots.** The clip fills the whole 9:16 screen: no black
  anywhere, the person always centred. The padding's black side bars
  stay off screen: size the square so the picture inside it (the width
  `split` printed) is wider than the frame, plus any sideways shift used
  to centre the person.
- **Split screen for listening shots.** The speaking person on top, the
  listening person at the bottom, each half 1080 x 960 with no gap, both
  filled and centred, the black bars off screen in each half. The
  listener's footage is the silent end of their previous clip.
- **Pre-lap.** Cut to the next person about 0.65 seconds before the
  current line ends, while the previous speaker is still talking: that
  is the moment their early clip starts.
- **Zoom-ins are cuts, not moves.** In moments of tension, jump straight
  to a tighter framing (1.25 to 1.3x) on a key word, and cut back out
  when the moment passes. Use the word times in `timings.json` to land
  each cut just before its word. No animated zoom.
- **Captions.** From `captions.json`: the script's wording with the
  word timings. Bold white with a black outline; the word being spoken
  is highlighted in yellow. Full shots: centred just below y 1255, over
  the chest and clear of the face. Split screen: on the seam between the
  two halves, so no face is covered. Write the caption data into the
  editable and draw the current caption with `STAGE.onFrame`, as a pure
  function of the time (stage skill, rule 6).
- **Every cut is instant, and none leaks.** A shot's cut-in goes on the
  shot's container and its cut-out on an inner wrapper, never both on
  one element (stage skill, rule 10); a zoom-in and its zoom-out go on
  two nested wrappers the same way. With `fill-mode: both`, a cut put on
  the wrong element shows its shot, or its zoom, from the first frame.
  Run the stage skill's leak audit before each shot's start.
- **The length.** The video ends one second after the last spoken word,
  as the stage skill sets it.
- **No black frames.** Before rendering, step through the whole
  timeline in the browser: every cut, every split screen, every zoom,
  the first and last frames. Nothing black may show anywhere.

### Step 9. Render and check

Render with the rendering skill. Then check the finished video for
black:

```bash
python3 <podcast>/tools/podcast.py black <root>/renders/<name>.mp4
```

IF it reports black, fix the edit and render once more.

## 3. When done

State the credit cost of the production as one total: the sum of the
`credits` recorded on every asset and render entry in the video's
metadata file. Never use the account balance for this; other sessions
spend from the same balance at the same time. Only the total is
reported, never a breakdown.

Read the clock again with `date` and state how many minutes the
production took, from the start time to now, as one number.

- **Assigned by Atlas:** your final reply is exactly one line:
  `DONE <render path> <total credits> <minutes>`. Nothing else.
- **Working with the user directly:** send the video file, with one line
  naming the video and the two numbers, the numbers in bold.

Never delete anything and never ask about deleting. The `deletable/`
folders stay as they are; the whole project is backed up by Jani, the
backup agent.

## 4. Hard rules

- **Work only inside the Super Vega folder.** Every skill, doc, and tool an agent reads comes from inside it. Copies of these skills exist elsewhere on this machine and are outdated: never read, search for, or follow them. IF a skill or file you need is not inside the folder, stop and ask the user; never fetch it from outside.
- Follow the steps in order. Never render a talking clip before the
  shots are planned and the audio is padded; the plan lives in the
  audio.
- Use the podcast tool for every step it covers; never write shell
  loops.
- Do not read any other file in the root, the shared folder, this style
  folder, or the project folders; it dilutes the session. The exceptions
  are the skills listed in section 5, and `add-ons.md`, which you open
  only WHEN the user asks for an add-on by name or the working memory's
  Design approach names one.
- Build in the root: the client's brand folder,
  `Super Vega/Project/<BrandName>/`, as the file-management skill sets
  out. This style folder and the shared folder are where the skills came
  from. They are never where you build.
- Besides what the html references, the materials folder keeps the
  podcast's working files: `script.txt`, `cast.json`, `lines.json`,
  `captions.json`, `persona/`, and `lines/`. They are the record of the
  edit and stay where they are.
- The video's number is its Brand number from the request, and its Task
  ID goes in the metadata, as the file-management skill says. Never
  count the files in a folder. IF either number is missing, stop and
  ask.
- The request carries no duration. The video's length follows the
  conversation track. Never stretch, pad, speed up, or cut the script.
- Never open another editable html in the same project folder. The only
  html you open is the stage template and the editable you are working
  on.
- Respect the Meta and TikTok UI: the faces and the captions stay inside
  the stage template's safe zone, and captions are centred on the canvas
  at x 540, at most 700 wide.
- Never invent a brand logo. A logo is used only when the request gives
  it and its instructions say to show it.
- WHEN the transcription comes back with wrong wording, the alignment
  keeps the script's words; never regenerate a line because Whisper
  heard it differently.

## 5. The other skills

Essential, none skipped:

- **podcast-toolkit** (this folder): every tool, command, and cost of a
  podcast video, the voice library, and the podcast tool.

From `<shared>/skills/`:

- **toolkit**: section 1 (the CLI) and section 2 (hosting local files)
  only. Its tool map is not yours.
- **prompting**: section 1 (principles), section 2 (the Higgsfield Soul
  format), and section 6 (speech and the Reword table).
- **stage-canvas-html**: the fixed procedure for the HTML stage and its
  checks.
- **rendering**: the one command that renders the finished editable.
- **file-management**: where every file lives and what it is called.
- **known-methods**: what is already proven to work or fail.

One more file sits in `<shared>/skills/` and is not essential:
**add-ons**. It is not read by default. WHEN the user asks for an add-on
by name, or the working memory's Design approach names one, open
`add-ons.md`, find that add-on, and follow it as written.
