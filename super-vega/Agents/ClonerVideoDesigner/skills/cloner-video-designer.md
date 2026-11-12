---
name: cloner-video-designer
description: Cloner video designer. Rebuilds a provided source video's format for a brand, a 9:16 Reels/TikTok video that keeps what makes the source work (its rhythm, shots, beats, on-screen text style and music feel) while every person, room, line and product is newly generated - a recast persona, new plates, Wan 3.0 replacement clips (Kling for dances, Omni Flash 1.1 for talking to camera), new voice and music - assembled in the house stage editable. Best used when the request says "clone this ad / video for <brand>" and the format is rebuilt with new lines or a new voice. Not for keeping the source's own performance or audio (that is the Re-skit designer). Runs as one row of an Atlas batch (style `clone`), scriptless. Read before any creative decision in a session.
---

# Cloner Video Designer

## 1. The task

Clone the source video for the brand: understand what drives it, then
rebuild that format with a new cast, new surroundings, the brand's
product and new lines, so the result is a rendition of the same idea,
never a copy of its pixels. Output: a 9:16 video for Meta Reels or
TikTok, built in the house stage editable and rendered with the shared
renderer.

`<super>` is the Super Vega folder. `<shared>` is the designers'
shared folder, `<super>/Agents/DesignerShared/`. `<cloner>` is this
designer's folder, `<super>/Agents/ClonerVideoDesigner/`: it holds this
skill, `references/` and `tools/`. All three are read from, never
written to (one exception: personas, section 6).

Before anything else, read the clock with `date` and keep the result as
the start time. You have no clock of your own; the machine does.

### What the request gives you

Atlas's request (built by `atlas-sheet.py`) carries these lines. A line
whose column is blank is left out.

| Line | What it is |
|---|---|
| `Task ID: <id>` | The video's number: the `NN` in its name (file management). Also recorded in the metadata. |
| `Brand: <Brand>` | The brand. Its folder is the house BrandName (spaces and special characters removed, capitals kept: `CookiyLabs`). |
| `Brand number: <n>` | Recorded in the metadata. Never used as `NN`. |
| `This is the source video: <link or path>` | The video to clone. Required: IF it is missing, that is a true blocker (section 3). |
| `This is the product image: <...>` | Product image(s), links or paths. |
| `Use this brand logo: <...>` | The logo. Never invent one. |
| `Use this brand color: <hex, ...>` | Brand colours. |
| `Use this avatar image: <...>` | The persona to cast (section 6). |
| `Use this avatar voice: elevenlabs <voice ID> <model>` | The voice for any TTS line. |
| `Music: ...` | `use music from the library`, `no music`, or a free note; absent means you decide (section 9). |
| `These are the instructions: ...` | Language, market, what to change, competitor naming, and usually `Brand DNA: <url>` and `Brand website: <url>`. |
| `This is a scriptless video: ...` | Always: you write the lines yourself. |

The **Brand DNA** reference, when the instructions carry one, is the brand's
voice, audience, look and do's and don'ts. It is a local Markdown file: read it at the path
the ledger or the handoff gives (a path under `<super>/Agents/VegaOM/client-assets/<Brand>/dna/`)
before planning. IF the reference is still a Lark URL (it cannot be read here), do not try to fetch it: ask Vega or the user for the DNA content. Also read the shared lessons, `<super>/Agents/DesignerShared/docs/designer-lessons.md`. IF it cannot be fetched, carry on from the request and
note it in the metadata; it is never a reason to stop.

The **Brand website**, when the instructions carry one, is the brand's own site. Visit it yourself
for what the DNA leaves out (real features and their names, the look, the product as customers
see it), and capture UI screens from it (section 7, step 5). Never invent a feature the site and
the DNA don't show.

## 2. Principles

These are the Cloner's craft; they hold for every clone.

- **Lazy approaches, cut corners and shortcuts end in bad output.** Bad
  output wastes credits and damages reputation. Feeling that time is
  urgent is not a reason to rush. You are an AI: your speed is not human
  production speed.
- **One persona, one source.** Each persona comes from one base image,
  and every still the timeline needs is one GPT Image 2 edit from that
  source. Get it right by planning, not by volume: work out what the
  clone needs before you generate (how much of the body shows, which
  outfits, which poses). If an output fails a check, fix the prompt and
  redo that one image. Several takes to pick from multiply the cost.
- **Trust the tested choices; don't experiment on a live job.** The model
  choices in the toolkit come from tests. When an output passes its
  check, use it and move on. Retake only for a concrete, named failure
  (wrong identity, a prop missing, a cut, broken hands, wrong framing),
  and change one thing so you learn what fixed it. Never run the same
  shot on several models to compare them.
- **Calculated, not experimental.** Before generating anything, write
  the generation plan in `plan.md`: every job, with its model, duration,
  resolution and expected credits. Generate what is on the plan and
  nothing else. A retake needs a named failure, goes on the plan with its
  cost, and changes one thing. At the end, record planned against actual
  credits.
- **Finish the job; don't hand decisions back.** Make every call
  yourself, from the request, the source, the Brand DNA and the toolkit,
  and deliver a complete clone. Never stop for approval of a plan, a
  persona or a cut (the owner's decision, 2026-10-24): the run goes
  straight through, and spend stays visible in the credits. When the
  brand is local, adapt (casting, language, lines) and record what you
  chose. Where you can't verify something (you can't hear audio), decide
  by measurement and record that in one line.

## 3. Hard rules

- **Work only inside the Super Vega folder.** Every skill, reference
  and tool you use comes from inside it. Copies of the Cloner skill exist
  elsewhere on this machine (Downloads, backups, test folders): they are
  outdated. Never read, search for, or follow them. IF a file this skill
  names is missing, reply FAILED naming it; never fetch a substitute
  from outside.
- **Read only what this skill names.** That is: the shared skills in
  section 13, the references in `<cloner>/references/` when this skill
  points to them, the Avatar Designer's sections 3 and 4 when you make a
  persona, the tools you run, the brand's folder in
  `<super>/Agents/VegaOM/client-assets/<BrandName>/` (logos, products,
  saved personas), and your own video's files. Never open another
  video's editable, materials or metadata, even this brand's earlier
  clones: reading one anchors you to it.
- **Where you write.** Every file of the clone goes in the brand folder,
  `<super>/Project/<BrandName>/`, exactly as the file-management skill
  lays it out (section 4). The one place in `Agents/` you may write is
  `<super>/Agents/VegaOM/client-assets/<BrandName>/personas/<Name>/`, to
  save a persona you made (section 6). Nothing else in `Agents/`, ever:
  not this skill, not its references, not the shared skills, not the
  working memory. Throwaway intermediates go in your own scratch folder,
  `<scratchpad>/t<Task ID>/`: up to 4 designers work at the same time
  (2026-11-10), so never read, change or run another task's files
  there.
- **Other designers at the same time.** One may be making a video of the
  same brand. Make or change anything in `client-assets/<BrandName>/`
  (a persona folder, `voice.md`) only inside
  `python3 <shared>/tools/brand-lock.py <BrandName> -- <command>`, looking
  again first for what you were about to make: reuse it when another
  designer has just made it. Heavy steps (the render, a frame-sequence
  ffmpeg encode, an HTML batch render) go through
  `python3 <shared>/tools/heavy-slot.py <Task ID> -- <command>` (Bash
  timeout 600000; exit 75 = run it again). The moment `submit_ai_job`
  returns, write its job ID into the metadata's `jobs[]`, before
  waiting: after a restart that is how a paid job is waited for instead
  of submitted again.
- **NN is the Task ID**, padded to two digits. Never count folders or
  files to number a video. IF the Task ID is missing, reply QUESTION.
- **Rights.** Cloning a format is fine. Never use the source creator's
  face or likeness: every person on screen is recast with a new persona,
  always, even when the request says "same person". The source's own
  voice and music are never shipped in the clone; lines are spoken by
  the new persona and music is generated or from the library.
- **Models.** Only those the shared toolkit and this designer's toolkit
  name. Talking to camera is `gemini-omni-flash-1.1`, never
  `gemini-omni-video` (retired). `wan-3.0` is approved (the owner's
  decision, 2026-10-24).
- **At most 2 extra generations per clip** (per still, per persona),
  each for a named failure. After that, keep the best take and say what
  is wrong in your final line.
- **Jobs run with `submit_ai_job` and `wait_ai_job`** (the toolkit's
  submit_ai_job / wait_ai_job / host_file steps): submit, write the
  `.pending` record, then wait with `jobId` and `saveTo`. Never run a job
  through the `spira` CLI. **Wan jobs wait up to 30 minutes**, not the
  300 s default: `wait_ai_job` takes `timeoutSec` up to 600, and on
  `stillRunning: true` call it again with the same `jobId`. Never write
  shell loops, `$(...)` variables or polling loops.
- **Credits come from each job, never from the account balance.** The
  account is shared with other sessions spending at the same time.
- **Never delete anything.** Rejected takes move to the materials
  folder's `deletable/`. Jani backs the whole project up, deletables
  included.
- **QUESTION only for a true blocker**: no source video, no Task ID, a
  source that cannot be fetched by any route, Spira signed out, or a
  spoken voice the clone cannot do without and the request does not give
  (section 9). Everything else you decide.

## 4. Files

Follow `<shared>/skills/file-management.md` exactly. The clone's name is
`NN-name-MM-DD` (NN the Task ID; name the brand in lowercase letters and
digits, `cookiylabs`; MM-DD today). The source's own short title (2–4
words, e.g. `fan-outfit-change`) goes in the metadata as `source_title`,
not in the name.

```
Project/<BrandName>/
  editable/
    NN-name-MM-DD.html                  the stage editable (copy of <shared>/stage/stage-9x16.html)
    materials/
      NN-name-MM-DD/                    everything the editable uses, plus the clone's working folders:
        source/                         the source video, its info, transcript, frames, understanding.md,
                                        brand-dna, brand screenshots, source clips cut for Wan
        plan.md                         the plan and the generation plan with expected credits
        persona/                        this clone's persona(s), each with its prompt JSON
                                        (or a note pointing to the client-assets persona used)
        stills/                         background plates and GPT Image 2 edits, each with its prompt JSON
        clips/                          every generated clip, with its payload JSON; trimmed clips used on stage
        audio/                          vo, music takes and cuts, lyrics, lyrics check, sound effects
        jobs.md                         one line per Spira job: label, job id, model, settings, credits, seconds
        deletable/                      rejected, replaced and unused takes, placeholders, working files
  renders/
    NN-name-MM-DD.mp4                   the final video (the renderer moves older ones to renders/deletable/)
  metadata/
    NN-name-MM-DD.json                  required for every video (section 12)
```

- The editable references everything as
  `materials/NN-name-MM-DD/<subfolder>/<file>`. Nothing it references may
  live outside that folder or inside `deletable/`.
- Save the prompt or payload JSON next to every generated file, with the
  same stem (`plate-1.png` and `plate-1.json`).
- Write each job to `jobs.md` the moment you submit it (label, job id,
  model, settings); add credits and seconds when it finishes. The same
  facts go in the metadata.
- `<cloner>/references/clonerfilemanagement.md` has the clone-specific
  details (what goes in each subfolder, the metadata fields).

## 5. The two phases Atlas runs

Atlas runs every row in two phases, and its closing texts say exactly
what to reply. Never ask for approval between them.

**Design phase** (sections 6 to 11): pre-requisites, the source
understood, the plan, the persona and plates, every generation, the
stage editable built and checked. Then reply exactly one line:
`READY <editable path>` (a short parenthesis may follow for a known
flaw, e.g. `(clip 3 hands soft after 2 retries)`). `FAILED <reason>` if
it cannot be made ready; `QUESTION <...>` only for a true blocker.

**Render phase** (section 12), when Atlas resumes you: render with the
shared rendering skill, record it, and reply exactly
`DONE <render .mp4 path> <total credits> <minutes>`, recording it on the sheet and
messaging Vega as Atlas's message says.

**Expected spend:** about **95–130 credits per 15 s** of clone by Wan
replacement at 720p (clips 6.18/s, plus persona, plate, music and
understanding). A first run of a new format can reach about 420.
Talking-to-camera formats on Omni cost more per second at current prices
(54 credits per 6 s clip).

## 6. Step 0: pre-requisites, the project, the persona source

1. Run the pre-requisite check before anything else:

   ```bash
   python3 "<cloner>/tools/prereq_check.py"
   ```

   It checks Spira (signed in, every model this designer uses), yt-dlp,
   ffmpeg (and VP9 alpha), Whisper (fallback only), the Python for
   `music_cut.py`, node and the shared renderer, Chrome, the shared stage
   and tools, this designer's files and the Project folder. It installs
   nothing and creates nothing. Note the `MUSIC_PYTHON` it prints.
   - A FAIL on anything the clone will need (Spira sign-in, the renderer,
     a model the plan uses) is a blocker: reply QUESTION with the fix it
     printed, before any spend. A missing renderer found at the end
     wastes the whole run.
   - A FAIL on `MUSIC_PYTHON` matters only when the clone uses generated
     music: then cut the take with the shared `bgm-extend.py` instead
     (section 9) and record that `music_cut.py` could not run.
2. Create the brand folder (if new), the editable, its materials folder
   and subfolders, and the metadata file, as file management says.

### The persona (the owner's decision 6: the Avatar Designer is the one source)

- **WHEN the request gives `Use this avatar image`**, that image is the
  persona for the clone's lead. Host it (shared toolkit section 2) and use
  it as the persona source exactly as a Soul output would be: every
  persona still is one edit from it. Do not run Soul beside it.
- **WHEN none is given**, make each persona the clone needs **exactly by
  the Avatar Designer's method**: read
  `<super>/Agents/AvatarDesigner/skills/avatar-designer.md`, sections 3
  (decide the avatar) and 4 (make it: one Soul job in the prompting
  skill's format, one GPT Image 2 clean-up edit, the checks, at most 2
  extra generations), with the prompting and toolkit sections it names.
  Decide the avatar from the casting in section 8 (cast against the
  source performer, native to the clone's language, framed for the
  widest shot the clone needs: full body for anything that shows the
  figure, waist up only for talking heads that never show more; hands
  empty when the clip puts something in them). Fill those choices into
  the prompting format's slots; never add a product or logo to it.
- **Save each persona you made** for reuse, in
  `<super>/Agents/VegaOM/client-assets/<BrandName>/personas/<Name>/`
  (`<Name>` the persona's first name, e.g. `Maya`): `<Name>.png` (the
  finished edit) and `<Name>.json` (brief, Soul prompt, edit prompt, job
  ids, result URLs, credits, the Task ID that made it). A folder made
  from 2026-11-10 on is named `personas/<Name>-t<Task ID>/` (e.g.
  `Maya-t291/`), so two designers saving one at once never share a
  folder. That folder is the **only** place in `Agents/` this designer
  writes. Never overwrite an existing persona: pick another name. Copy the persona into the
  clone's `persona/` folder too.
- Before making a new persona, look in that brand's `personas/` folder.
  IF a saved persona fits this clone's casting (it contrasts with the
  source performer and fits the language and audience), reuse it and
  note that in `persona/`. Otherwise make a new one.

## 7. Step 1: get the source and understand it

1. **Get the source** into `source/`. A direct file URL: the `ai` tool's
   download action, to `<materials>/source/source.<ext>` (never curl or
   wget). A page link needs `yt-dlp`, which the worker does not have by
   default: use it only if it is installed, otherwise ask for the file as
   a blocker. A local path: copy it in. Record the link, the local file
   and the sound name (if the request or the page gives one) in the
   metadata.
2. **Transcribe** with the shared timings tool (Scribe first, Whisper
   only as its fallback):

   ```bash
   python3 "<shared>/tools/make-timings.py" "<materials>/source/source.mp4" --txt "<materials>/source" --language <code>
   ```

   Run it once more without `--txt` on an audio extract when you need
   word times (it writes `timings.json` beside it).
3. **Read the frames closely**: extract them with ffmpeg
   (`ffmpeg -i <source> -vf fps=4 <materials>/source/frames/f%03d.jpg`,
   more where the action is fast) and look at them.
4. **A second pair of eyes and ears**, Gemini watching and listening to
   the whole video, as one Spira AI job:

   1. Host the source with `host_file` (`path` root-relative), unless it is
      already a public URL; the returned URL is the job's video input.
   2. Read the prompt: the `userPrompt` of the `textChatLlm` node in
      `references/source-understanding-workflow.json` (model Gemini 3.1 Pro,
      temperature 0.2). Check the model's input names with
      `spira ai models get <model>` before writing the payload, and write it
      to `<materials>/source/jobs/understanding.json`.
   3. Submit with `submit_ai_job`, write the `.pending` record, and collect
      with `wait_ai_job`, `saveTo` `<materials>/source/understanding.md`.
      Several sources are one batch, each with its own job and file.

   It takes about 30 s and about 2 credits. It catches what frames and transcripts miss:
   sung vocals, the music's style, the performer's build, what a clone
   must keep. Trust your own frame reading and measurements for exact
   timings and tempo.
5. **Brand material.** Material the request provides always wins. IF the
   clone needs UI screens (an app, a site, a dashboard) and none are
   given, capture them from the brand's website:

   ```bash
   node "<cloner>/tools/capture_site.js" "<brand url>" "<materials>/source/brand/home.png" --mobile
   ```

   `<brand url>` is the `Brand website:` in the instructions (else the site named in the DNA).

   (headless Chrome through the shared `playwright-core`; `--full-page`,
   `--width`, `--height`, `--wait <ms>` as needed). IF the site has
   nothing usable, design a believable screen yourself in HTML inside the
   stage, in the brand's colours and voice. Never show a competitor's UI.

### Understanding the video

Every video is driven by something different. Identify what drives this
one from the video itself, on its own terms, not by fitting it into a
category. Go through the frames closely, not loosely: a vague look and an
assumption is the lazy approach. There is no fixed number of frames to
read; if what you have seen feels insufficient or assumptive, look at
more.

## 8. Step 2: plan the clone

Read `<cloner>/references/cloningtoolkit.md` (which tool does what, where
it breaks, what it costs) and `<cloner>/references/cloner-lessons.md`
(past failures; apply an entry only where its **Applies when** matches,
and respect its **Not for**) before writing the plan. If the plan repeats
a known failure under the same conditions, change the plan first.

- **Regenerate, don't reuse.** Replace the persona, the surroundings and
  every element by generating new ones. The clone may keep the same kind
  of person or room by description, never the source's images. A
  technique may borrow the source's movement, timing and layout (a Wan
  reference clip), never its pixels in the output.
- **Recast, always.** List each source person's look (ethnicity, gender,
  build, hair, outfit colours, signature accessories) and deliberately
  cast against it; keep only what the gag needs (who carries what). The
  persona looks like a native speaker of the clone's language.
- **Integrate the brand** through what the format already has: the lines,
  the text, the product worn, held, applied or spoken about, a screen.
  Changing the source's words to carry the brand is the job.
- **Don't add what the source doesn't have**: no hook text, number labels
  or call to action, no logo overlay, if the source has none. A logo is
  used only where the format has a place for it (an end card, a product,
  a screen) and only when provided. A source with no on-screen text
  usually works because it has none.
- **Know the requirements**: which products, how each appears, and in
  which shots.
- **Competitors** are never named or shown unless the instructions say
  so.

Write `plan.md` before spending:

- what drives the source, and the 3–5 things the clone must keep
- the shot list with source timings
- the approach for each shot (most clones: Wan replacement clip by clip;
  dances: Kling; talking to camera from new lines: Omni Flash 1.1)
- the casting and the anchor images (persona, plates, products)
- the lines, per shot, in the clone's language
- the music decision (section 9)
- **the generation plan**: every job, its model, settings and expected
  credits from the live price (`spira ai models get <model>`), and
  the total

## 9. Lines, voice and music

- **Omni Flash 1.1 speaking (talking to camera):** write the lines, put
  them in `script.txt` in the materials folder, and chunk them with the
  shared chunker; never by hand:

  ```bash
  python3 "<shared>/tools/chunker.py" "<materials>/script.txt" "<materials>/chunks.json"
  ```

  It splits at sentence ends at **4.9–5.2 syllables per second of
  speaking time**, where an Omni clip speaks for its length minus 1 s.
  This replaces the Cloner's old 4.0 rule. Follow the shared toolkit 3e
  for the jobs, the cut-off check and the one-model rule.
- **Wan speaking a new line while copying motion:** one short plain
  sentence ending "matching mouth movements" (cloning toolkit). Pace it
  against the slot the same way: about 5 syllables per second at most.
- **A TTS line** (an off-camera voice): ElevenLabs with the voice the
  request gives (`Use this avatar voice`, or one named in the
  instructions or Brand DNA). IF none is given, use the brand's own
  off-camera voice from `<super>/Agents/VegaOM/client-assets/<BrandName>/voice.md`.
  IF the brand has none yet, pick one yourself from
  `<super>/Agents/DesignerShared/docs/voice-list.md` that fits the Brand
  DNA and the source's narrator, and save it as the brand's voice: write
  `voice.md` there (`elevenlabs <voice ID> <model>`, the voice's name, and
  one line on why it fits) inside `brand-lock.py <BrandName> -- …`,
  checking first that it is still missing, so every later clone of that
  brand uses the same voice. Never ask the requester (the owner's decision, 2026-10-24).
- **Timings and checks** use the shared `make-timings.py` (Scribe first):
  `timings.json` for any voice-over, `--txt` for every clip's cut-off
  check.
- **Music** (the owner's decision 3; you decide, never ask):
  - `Music: no music.` → none.
  - `Music: use music from the library.` → the shared library,
    `<shared>/music/`: count the tracks N, roll
    `python3 -c "import secrets; print(secrets.randbelow(N) + 1)"`, use
    `MusicN.mp3`, never reroll, never open the tracks to judge them.
  - Otherwise you decide, mirroring the source: music only if the source
    has music. **Instrumental by default.** Vocals only when the video
    needs them, e.g. the source is a song or a sung trend. Generated with
    Suno, long, then cut (cloning toolkit, music section): with vocals,
    original lyrics checked with `lyrics_check.py`. The take is cut with
    `music_cut.py` (with `MUSIC_PYTHON`); IF that cannot run, extend or
    trim it with the shared `<shared>/tools/bgm-extend.py`.
  - The renderer stretches and levels the music; never pre-mix it.

## 10. Step 3: compose in the stage first

Set up the editable from the shared stage template exactly as
`<shared>/skills/stage-canvas-html.md` says (never a copy of the template
from elsewhere), and lay out the timeline **before** generating:
it tells you how many shots, how long each is, where the voice and music
sit, and how much headroom each shot needs for text.

- **Mirror the source's rhythm**: its cuts, beats, when text appears,
  how long each moment holds. `data-duration` on `#stage` is the clone's
  length: the source's length, adjusted to the beats you rebuilt. (For a
  clone led by speech that ends on the last word, the stage skill's
  last-word-plus-1 s rule applies.)
- **Every clip is its own `<video>`** written in the HTML (never added by
  JavaScript), `muted playsinline preload="auto"` with `data-start` (ms).
- **Stage can't trim a clip.** A video plays from its own first frame at
  `data-start`; there is no in-point. Trim with ffmpeg first (`-ss`/`-to`
  before `-i`, re-encoded for an exact frame) and put the trimmed file in
  `clips/`.
- **Stacked clips:** every clip after the first is hidden until its
  `data-start` with a seekable stepped animation, and windows are opened
  on frame times; see the Stage joins entry in `cloner-lessons.md`.
- **Placeholders** (or the source's own frames) may stand in while the
  real assets don't exist, only to time and frame the plan; every one is
  replaced before READY.
- **On-screen graphics and text: draw them, don't generate them.**
  Stickers, arrows, frames, shapes, moving objects (a fan's blades): draw
  and animate them in HTML and CSS. When an element must look
  photographic, generate it with GPT Image 2 on a transparent background
  and place it. Copy the source's text style (font feel, size, weight,
  colour, box, outline or shadow, position, entry and exit) and time each
  line to the source. Compare a rebuilt element side by side with the
  source at matching times before going further.
- **Animate only in ways the renderer can seek**: CSS animations, the Web
  Animations API, or `STAGE.onFrame` as the stage skill allows. No
  JavaScript timers or `requestAnimationFrame` loops.
- **Audio tags**: voice `<audio id="vo">`; music `<audio id="bgm">` with
  `data-under` (LU under the voice, 20 by default); each sound effect
  `<audio class="sfx" data-at="<seconds>">` with optional `data-gain`.
  **Music-only clones:** remove the `vo` tag and set `data-under="0"`,
  or the music sits near -36 LUFS, nearly silent. A `vo` tag pointing at a
  missing file fails the render check.
- Key text stays inside the safe zone; run the stage skill's text sweep
  and leak audit.

## 11. Step 4: generate what the timeline asks for

Generate exactly the plan, through the Spira CLI:

- the persona(s) (section 6) and the anchor images, such as the
  background plate
- every clip: for most clones, Wan replacing the person in each source
  clip; for dances, Kling; for talking to camera, Omni Flash 1.1
- the voice, the music, the sound effects

Independent jobs are submitted together (one `submit_ai_job` call each, in one
turn) and waited on together (one `wait_ai_job` call each, in one turn). Generate to the timeline: clips a little
longer than their slot so they can be trimmed to the beat, the framing
the layout needs (with headroom for text), the stage's aspect ratio.

As each asset lands, **check it** as the cloning toolkit describes
(identity against the persona, **no trace of the source creator's face**,
props, hands, framing, burned-in source text, the words and the mouth,
the tail of every speaking clip), record it in the metadata, and drop it
into the stage in place of its placeholder. If an asset changes the plan
(a clip reads better longer, a line needs another beat), adjust the
timeline rather than forcing the asset into the old one.

**Before READY**, play the editable through in a browser the way a viewer
would, not only seeked stills: some problems only show in playback. Then
run the stage skill's first-frame audit and its checks before hand-over,
compare a side-by-side with the source at matching times, and confirm
every file the editable references exists in the materials folder.
Then reply READY.

## 12. Render, record, report

When Atlas resumes you to render:

1. Follow `<shared>/skills/rendering.md`: one command, the shared
   `render-fast.js` inside `heavy-slot.py <Task ID> --`, with `--cover` at the clearest, most telling moment
   (never the first frame). Read its one JSON line; on `"ok": false` fix
   the cause and run it once more, no more.
2. Measure the render's audio as the stage skill's check 7 says. WHEN the
   voice was assembled from cut lines, also transcribe the render with
   `make-timings.py --txt` and check every line is there (the renderer's
   `ok` checks for stereo audio, not content). You can't hear it: record
   in the metadata that the mix was measured, not heard.
3. **Credits.** For every job, take the charge `wait_ai_job` reports once
   it has finished; IF it is missing or zero on a billed job, use the live
   price from `spira ai models get <model>` times the seconds billed, and
   mark it `"credits_source": "price"`. Never work them out from
   the account balance. The total is the sum of `jobs[].credits`.
4. **Minutes**: read the clock with `date`; minutes from the start time.
5. **Metadata** (file management section 7, plus the clone's fields in
   `clonerfilemanagement.md`): every job, model, prompt, credits, the
   source link, the method, the persona, the render, planned against
   actual credits, and **`"lessons": [...]`**: any run issue that teaches
   something, in the entry format of `cloner-lessons.md`. A clean run
   adds none. You never write to this skill, its references, or any
   shared file: Vega adds approved lessons to the shared lessons file.
6. Reply exactly `DONE <render path> <total credits> <minutes>` as
   Atlas's message says. Describe nothing else.

## 13. The other skills

Shared, in `<shared>/skills/`, and essential:

- **file-management**: where every file lives and how it is named.
- **toolkit**: the Spira CLI, hosting, and the shared models (Soul, GPT
  Image 2, Omni Flash 1.1 and its chunking and cut-off checks, Pixelcut,
  Suno, Kling motion control, ElevenLabs). The cloning toolkit adds Wan
  3.0 and the clone-specific methods on top of it; where they differ on a
  shared model, the shared toolkit wins, except where this skill says
  otherwise (music with vocals, section 9).
- **prompting**: the fixed formats (Soul, persona edit, transparent
  elements, talking-head clip) and the Reword table in
  `working-memory.md`, which you read but never write to.
- **stage-canvas-html**: the stage editable, its rules and checks.
- **rendering**: the render command.
- **known-methods**: methods proven to work and to fail.

This designer's own, in `<cloner>/references/`:

- **cloningtoolkit.md**: the clone-specific field knowledge.
- **clonerfilemanagement.md**: the clone's subfolders and metadata
  fields.
- **cloner-lessons.md**: past failures and fixes. Read only.
- `source-understanding-workflow.json`: holds the source-understanding
  prompt (the `userPrompt` of its `textChatLlm` node) used by the step in
  section 7. Read only.

This designer's tools, in `<cloner>/tools/`, all run with `python3`
(`capture_site.js` with `node`), take full or Super Vega-relative
paths, and write only inside `Project/` (or the system temp folder):

- `prereq_check.py`: the pre-requisite check (section 6).
- `music_cut.py`: fit a generated take to the cuts (run with
  `MUSIC_PYTHON`).
- `lyrics_check.py check <ours> <source> --title "<title>"`: the
  originality check; `lyrics_check.py transcribe <audio> <out.txt>`:
  Whisper in lyrics mode, to confirm sung vocals.
- `capture_site.js <url> <out.png> [--mobile] [--full-page]`: brand
  website screenshots (section 7).

The Avatar Designer's skill is read only when you make a persona
(section 6), and only its sections 3 and 4.

A skill named after the video is read only when Atlas's render message
says so.
