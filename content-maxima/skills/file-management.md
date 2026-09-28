---
name: file-management
description: Where every file of a video session lives, how it is named, what happens to it when it is replaced or rejected, and how a finished render is published. Fixed procedure. Apply to every file created, moved, or replaced in a video session.
---

# File Management

This is a fixed procedure. Other skills say what a file is for; this
skill says where it goes, what it is called, and what happens to it when
it is superseded.

## 1. The root

The **root** is the folder the session was opened in, your working
directory. Every file the session creates goes inside it, and every path
here is relative to it. The package folders (`skills/`, `stage/`,
`tools/`, `sfx/`, `music/`) may sit in the same folder; they are read
from and never written to, and nothing is built inside them.

## 2. Layout

```
<root>/
  editable/
    NN-name-MM-DD.html          one editable per video (a copy of the stage template)
    materials/
      NN-name-MM-DD/            everything that editable references
        script.txt              the approved script, verbatim
        vo.mp3                  voice-over (dry: no effects mixed in)
        bgm.mp3                 background music
        timings.json            word timestamps for the VO
        sfx/                    the sound effects the editable uses
        <images, clips, cut-outs, fonts>
        jobs/                   generation payloads; never referenced
        deletable/              rejected, replaced, unused and working files
  renders/
    NN-name-MM-DD.mp4           the current render of each editable
    deletable/                  replaced renders
```

## 3. Naming

Every video has one name, `NN-name-MM-DD`, shared by its editable, its
materials folder, and its render.

- **NN**: two-digit sequence number within this root: the highest
  number in `editable/` plus one, `01` if there is none. Never reuse a
  number, even if an earlier video was abandoned.
- **name**: the brand name if a brand has been mentioned; otherwise the
  video's topic. Lowercase letters and digits, words joined by hyphens.
- **MM-DD**: month and day the editable was created, joined by a hyphen.

The name is assigned once, when the editable is created, and never
changes. Edits, re-renders, and later sessions keep it.

## 4. The editable

Create it, its materials folder, and the script in one step:

```bash
N=NN-name-MM-DD
mkdir -p editable/materials/$N/deletable editable/materials/$N/jobs renders/deletable
cp <package>/stage/stage-9x16.html editable/$N.html
sed -i.bak "s/EDITABLE-NAME/$N/g" editable/$N.html && rm editable/$N.html.bak
printf '%s\n' "<the approved script>" > editable/materials/$N/script.txt
```

An edit to a video is made to the same editable; never create a second
html for the same video. IF an editable is rebuilt from scratch, move the
old one to its materials `deletable/` first.

## 5. Materials

- Everything the editable references lives in its materials folder and
  is referenced as `materials/NN-name-MM-DD/<file>`. Nothing in
  `deletable/` or `jobs/` may be referenced.
- Only material in use stays in the folder proper. The moment a file is
  rejected, replaced, or turns out to be unused (the second take of a
  music job, a Soul base image once the edit is in, a contact sheet),
  `mv` it to `deletable/` under the same name (adding `_2`, `_3` on a
  collision). The generation's payload stays in `jobs/`, so the asset can
  be made again.
- Never delete. The `deletable/` folders are the operator's to empty.
- Tool working files (audit and cover sheets, the cover still, a
  reference video and its frames) are written straight to `deletable/`
  by the tools.

## 6. Renders and publishing

- `tools/render/render.js` writes `renders/NN-name-MM-DD.mp4`, moving a
  previous render to `renders/deletable/NN-name-MM-DD_<YYYYMMDD-HHMM>.mp4`
  first, so `renders/` holds exactly the current render of each editable.
- A finished render (rendered, checked, cover set) is published to the
  Social Post Assets library:

  ```bash
  tools/publish.sh renders/NN-name-MM-DD.mp4               # lists the tags
  tools/publish.sh renders/NN-name-MM-DD.mp4 "<tag>"       # uploads, prints the asset id and URL
  ```

  Every upload needs a tag that already exists; the CLI cannot create
  one, and an unknown tag fails before anything is transferred. Match the
  video to the tag for its brand or kind. IF no existing tag fits, do not
  file it under an approximate one (there is no delete command): leave
  it unpublished and say so in the final message.
- Only the current render is published. A re-render that supersedes a
  published video is published again; removing the superseded asset is
  the operator's call.
