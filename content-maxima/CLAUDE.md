# Content Maxima

A skills package that turns a script, a brief, or an idea into a finished
9:16 video for Reels and TikTok. It is not an application: there is nothing
to build, no test suite, no dev server. The work of a session is to read
the procedures in `skills/` and follow them, generating materials through
the Spira CLI and assembling them in an HTML stage that renders to MP4.

## Start here, every session

Read `skills/creative-video-production.md` first. It is the entry point and
names the other skills, which are essential and never skipped:
`toolkit.md`, `prompting.md`, `stage-canvas-html.md`, `file-management.md`,
`known-methods.md`, plus `skills/working-memory.md` for its Preferences. This file
is a map; where it and a skill disagree, the skill wins.

## Package and root

The package (`skills/`, `stage/`, `tools/`, `sfx/`, `music/`, `styles/`, `docs/`) is
read from, never written to. Session output goes to the root, the folder
the session was opened in, under `editable/` and `renders/`, which are
gitignored. `file-management.md` governs every path.

## Record a corrected approach in known-methods

WHEN a session takes an approach that turns out to be wrong and is only
unstuck after the user debugs it, and the user asks to "record the right
approach in known-methods.md", write the working way into the skill that
owns it first, then add a short entry to `skills/known-methods.md` with
the three parts the existing entries use: **Works**, **Fails** (and what it
cost), **Where**.

## Commands

```bash
tools/new-video.sh "<topic>" <<< "<script>"                   # start a video: name, folders, template, script
python3 tools/gen.py <model-id> <payload.json> <out-file>     # one generation: submit, wait, download
python3 tools/make-timings.py <materials>/<name>/vo.mp3 [--from clips...]  # word timings (and the VO from clips)
python3 tools/cut-sheet.py grid|elements <sheet.png> ... --names a,b  # cut one generated sheet into its images
python3 tools/captions.py <root>/editable/<name>.html            # word-per-word captions from the timings
node tools/render/audit.js <root>/editable/<name>.html [--at ms,...]  # leaks, text, files, frame sheet
node tools/render/render.js <root>/editable/<name>.html <root>/renders/<name>.mp4 30
tools/set-cover.sh <root>/renders/<name>.mp4 <seconds>
spira assets upload <root>/renders/<name>.mp4                  # host the finished render
tools/style-sheet.sh <url or path> <materials>/<name>/deletable # style reference contact sheet
node docs/render-steps.js                                       # refresh the README cards
```

`tools/bgm-extend.py` builds the music bed and is called by the renderer.

## What the machine needs

Node, ffmpeg (with libvpx), Python 3, and curl. Run `npm install` once in
`tools/render`. The render and the audit run their browser on AWS Lambda:
`CM_RENDER_LAMBDA` and `CM_RENDER_BUCKET` name the function and its bucket
(set on the worker), with AWS credentials allowed to use them. Timings need `pip install openai-whisper`; reference
videos from a URL need `yt-dlp`. The Spira CLI (`npm install -g
@spira-lab/cli`) must be signed in.
