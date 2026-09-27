# Content Maxima

A skills package that turns a script, a brief, or an idea into a finished
9:16 video for Reels and TikTok. It is not an application: there is nothing
to build, no test suite, no dev server. The work of a session is to read
the procedures in `skills/` and follow them, generating materials through
the Spira CLI and assembling them in an HTML stage that renders to MP4.

## Start here, every session

Read `skills/creative-video-production.md` first. It is the entry point: it
defines the task, the principles, the hook, the captions, the hard rules,
and it names the five other skills that are essential and never skipped.

This file is the map, not a substitute. Nothing here replaces a skill, and
where the two ever disagree, the skill wins.

| Skill | What it settles |
|-------|-----------------|
| `creative-video-production.md` | The task, the creative principles, the hard rules. Read first. |
| `toolkit.md` | One fixed model per job, with the exact Spira CLI command and cost. Never substitute a model. |
| `prompting.md` | The fixed prompt format for each model. |
| `stage-canvas-html.md` | The HTML stage: setup, the animation rules that keep play/pause/seek/render honest, the audits, the export. |
| `file-management.md` | Where every file lives, what it is called, what happens when it is replaced, and where a finished render is published. |
| `known-methods.md` | Approaches already proven to work or to fail, with the reason. Read so a paid-for failure is not paid for twice. |

Two more sit beside them and are **not** read by default:
`working-memory.md` (read for its Preferences before deciding anything) and
`add-ons.md` (opened only when the user names an add-on, or a Preference
in working memory names one).

## The package and the root are different folders

The **package** is this repository: `skills/`, `stage/`, `tools/`, `sfx/`,
`music/`, `docs/`. It is read from, never written to.

The **root** is the folder the session was opened in. Every file a session
creates goes there, under `editable/`, `renders/`, and `metadata/`.

They are often the same folder, and that is a trap: a session that builds
in the package by accident looks correct until the package is cloned
somewhere else. `file-management.md` governs every path.

`editable/`, `renders/` and `metadata/` are gitignored for exactly this
reason — session output is never committed.

## Rules that apply before the skills are read

- **Read only what you are told to read.** The skills above, plus the stage
  template and the editable you are working on. Opening other files in the
  root or the package dilutes the session, and opening another editable
  anchors you to it and you copy it.
- **Never edit `stage/stage-9x16.html`.** Every video is a copy of it. A
  change to the template is a separate task.
- **Never invent a brand logo.** A logo is used only when the user provides
  one; otherwise the brand is its name in text.
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

## Layout

| Folder | Holds |
|--------|-------|
| `skills/` | The procedures above |
| `stage/` | `stage-9x16.html`, the 9:16 template every editable is copied from |
| `tools/` | The renderer and the two helper scripts |
| `sfx/` | Sound effects. Choose from `sfx/SFX metadata.json`; never open the audio |
| `music/` | The numbered music library, `Music1.mp3` upward |
| `docs/` | The README cards and `steps.html`, which generates them |

## Commands

```bash
# word timings for the VO, written as timings.json beside it
python3 tools/make-timings.py <root>/editable/materials/<name>/vo.mp3

# render the editable to MP4 (editable, output, fps)
node tools/render/render.js <root>/editable/<name>.html <root>/renders/<name>.mp4 30

# host a local file so a model can take it as a public URL
spira assets upload <file>

# refresh the README cards after editing docs/steps.html
node docs/render-steps.js
```

`tools/bgm-extend.py` builds the music bed and is called by the renderer;
it is not run by hand.

Every generated asset comes from the Spira CLI (`spira`, the npm package
`@spira-lab/cli`). Preflight it once per session as `toolkit.md` section 1
says, before any generation.

## What the machine needs

Node, ffmpeg, and Google Chrome (or `CHROME_PATH` set to another Chromium).
Run `npm install` once in `tools/render`. Timings additionally need
`pip install openai-whisper`.
