# Content Maxima

A skills package that turns a script, a brief, or an idea into a finished
9:16 video for Reels and TikTok. It is not an application: there is nothing
to build, no test suite, no dev server. The work of a session is to read
the procedures in `skills/` and follow them, generating materials as
Spira AI jobs submitted with the `submit_ai_job` tool (never through the
Spira CLI) and assembling them in an HTML stage that renders to MP4.

## Start here, every session

Read `skills/creative-video-production.md` first. It is the entry point: it
defines the task, the principles, the hook, the captions, the hard rules,
and it names the five other skills that are essential and never skipped.

This file is the map, not a substitute. Nothing here replaces a skill, and
where the two ever disagree, the skill wins.

| Skill | What it settles |
|-------|-----------------|
| `creative-video-production.md` | The task, the creative principles, the hard rules. Read first. |
| `toolkit.md` | One fixed model per job, submitted with `submit_ai_job` and collected with `wait_ai_job`. Never substitute a model. |
| `prompting.md` | The fixed prompt format for each model. |
| `stage-canvas-html.md` | The HTML stage: setup, the animation rules that keep play/pause/seek/render honest, the audits, the export. |
| `file-management.md` | Where every file lives, what it is called, what happens when it is replaced, and where a finished render is published. |
| `known-methods.md` | Approaches already proven to work or to fail, with the reason. Read so a paid-for failure is not paid for twice. |

Two more sit beside them: `working-memory.md` (read for its Preferences
before deciding anything, every session) and `add-ons.md` (opened only when the user names an add-on, or a Preference
in working memory names one).

## The package and the root are different folders

The **package** is this repository: `skills/`, `stage/`, `tools/`, `sfx/`,
`music/`, `fonts/`, `docs/`. It is read from, never written to, except
`skills/working-memory.md` (below).

The **root** is the folder the session was opened in. Every file a session
creates goes there, under `editable/`, `renders/`, and `metadata/`.

They are often the same folder, and that is a trap: a session that builds
in the package by accident looks correct until the package is cloned
somewhere else. `file-management.md` governs every path.

`editable/`, `renders/` and `metadata/` are gitignored for exactly this
reason — session output is never committed.

## Rules that apply before the skills are read

- **Read only what you are told to read.** The skills above, plus the stage
  template, and the editable you are working on. Opening other files in the
  root or the package dilutes the session, and opening another editable
  anchors you to it and you copy it.
- **Never edit `stage/stage-9x16.html`.** Every video is a copy of it. A
  change to the template is a separate task.
- **Never invent a brand logo.** A logo is used only when the user provides
  one; otherwise the brand is its name in text.
- **Never open credential files** such as `.env` files. Never print or paste a secret value out of them.
- **Nothing reaches `main` except through a pull request.**

## Record a corrected approach in known-methods

WHEN a session takes an approach that turns out to be wrong, spirals on it,
and is only unstuck after the user debugs it, the fix is written into
`skills/known-methods.md` before the session moves on. The next session
reads that file and does not pay for the same detour again.

The user asks for this by name: "record the right approach in
known-methods.md". The entry is short and has the three parts the existing
entries use:

- **Works:** the approach that turned out to be right.
- **Fails:** the approach taken first, and what it cost.
- **Where:** the skill and section that holds the instruction itself.

The why lives in `known-methods.md`; the instruction lives in the skill it
points to. If the working way is not written anywhere yet, write it into
the right skill first, then point the entry at it.

## Working memory

`skills/working-memory.md` holds the Preferences and the Reword table.
Read it at the start of every task. It is the one file in the package a
session writes to: a Reword pair on its own (`skills/prompting.md`
section 6), a Preference only when the user asks for one.

## Layout

| Folder | Holds |
|--------|-------|
| `skills/` | The procedures above |
| `stage/` | `stage-9x16.html`, the 9:16 template every editable is copied from |
| `tools/` | The renderer and the helper scripts |
| `sfx/` | Sound-effect metadata. Choose from `sfx/SFX metadata.json`; the audio is hosted and fetched with `tools/fetch-resource.py` |
| `music/` | Music metadata. Choose from `music/Music metadata.json`; the audio is hosted and fetched with `tools/fetch-resource.py` |
| `fonts/` | The type library (SIL OFL), indexed in `fonts/fonts.md` |
| `docs/` | The README cards and `steps.html`, which generates them |

## Commands

```bash
# fetch a hosted music track or sound effect into the video's materials
python3 tools/fetch-resource.py <music|sfx>/<file> <root>/editable/materials/<name>/<dest>

# talking-head chunks by syllables
python3 tools/chunker.py <materials>/<name>/script.txt <materials>/<name>/jobs/plan.json

# word timings for the VO, written as timings.json beside it (and the VO from clips or a recording)
python3 tools/make-timings.py <root>/editable/materials/<name>/vo.mp3 [--from clips... | --recording <url>]

# cut one generated sheet into its images
python3 tools/cut-sheet.py grid|elements <sheet.png> ... --names a,b

# word-per-word captions from the timings
python3 tools/captions.py <root>/editable/<name>.html

# render the editable to MP4 (editable, output, [fps, default 24])
node tools/render/render.js <root>/editable/<name>.html <root>/renders/<name>.mp4

# host the finished render; returns its URL
host_file renders/<name>.mp4   (worker_tools)

# refresh the README cards after editing docs/steps.html
node docs/render-steps.js
```

`tools/bgm-extend.py` builds the music bed and is called by the renderer;
it is not run by hand.

Every generated asset is a Spira AI job submitted with `submit_ai_job` and
collected with `wait_ai_job`, as `toolkit.md` section 1 says. Never
`spira ai jobs`.

## What the machine needs

Node, ffmpeg, Python 3, curl, and Google Chrome (or `CHROME_PATH` set to
another Chromium). Run `npm install` once in `tools/render`; its one
dependency is playwright-core, which drives the local Chrome. Timings
additionally need `pip install openai-whisper`; reference videos from a
URL need `yt-dlp`. The Spira CLI (`npm install -g @spira-lab/cli`) must be
signed in: jobs and `host_file` run as that account.
