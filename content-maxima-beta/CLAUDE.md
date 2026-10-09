# Content Maxima

A skills package that turns a script, a brief, or an idea into a finished
9:16 video for Reels and TikTok. It is not an application: there is nothing
to build, no test suite, no dev server. The work of a session is to read
the procedures in `skills/` and follow them, generating materials as
Spira AI jobs submitted with the `submit_ai_job` tool (never through the
Spira CLI) and assembling them in an HTML stage that renders to MP4.

## Start here, every session

Read `skills/creative-video-production.md` first. It is the entry point and
names the other skills, which are essential and never skipped:
`toolkit.md`, `prompting.md`, `stage-canvas-html.md`, `file-management.md`,
`known-methods.md`, plus `skills/working-memory.md` for its Preferences. This file
is a map; where it and a skill disagree, the skill wins.

## Package and root

The package (`skills/`, `stage/`, `tools/`, `sfx/`, `music/`, `styles/`, `fonts/`, `docs/`) is
read from, never written to. Session output goes to the root, the folder
the session was opened in, under `editable/` and `renders/`, which are
gitignored. `file-management.md` governs every path.

## Looking at images

Every image the session looks at (a style sheet, a contact sheet, the
audit sheet, a generated sheet or persona, a photo the user supplied) is
opened through the tool, never by reading the image file itself:

```bash
tools/view-image.sh <image> <materials>/<name>/deletable [--crop x,y,w,h]
```

Read the path it prints. An image whose long edge is 1024 px or less is
printed as it is; a larger one is scaled to half its width and height,
never below a 1024 px long edge, into `deletable/view/`. For small type
or an edge, look at a region at full resolution with `--crop` (source
pixels) instead of the whole image larger.

The copy is only for knowing what the image shows. Everything the video
uses takes the original: what the editable references, the sheet given
to `cut-sheet.py`, a file passed to `spira assets upload`, and every job
input such as `referenceImage` (the original or its hosted URL), never a
file from `deletable/view/`. A position or size measured on the copy is
scaled back by the `source WxH` the tool prints before it is used. The
audit flags an editable that references the copy; nothing checks an
upload or a job input, so this rule is the only guard there.

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
python3 tools/pace-clips.py <materials>/<name> th-01.mp4=<words> ...  # speed up Seedance clips 5+ words short of their slot
python3 tools/make-timings.py <materials>/<name>/vo.mp3 [--from clips... | --recording <url>]  # word timings (and the VO from clips or a recording)
python3 tools/cut-sheet.py grid|elements <sheet.png> ... --names a,b  # cut one generated sheet into its images
python3 tools/captions.py <root>/editable/<name>.html            # word-per-word captions from the timings
node tools/render/audit.js <root>/editable/<name>.html [--at ms,...]  # leaks, text, files, frame sheet
node tools/render/render.js <root>/editable/<name>.html <root>/renders/<name>.mp4
spira assets upload <root>/renders/<name>.mp4                  # host the finished render
tools/style-sheet.sh <url or path> <materials>/<name>/deletable # style reference contact sheet
tools/view-image.sh <image> <materials>/<name>/deletable [--crop x,y,w,h]  # the copy of an image to look at
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
