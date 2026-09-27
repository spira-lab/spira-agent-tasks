---
name: file-management
description: Where every file of a video session lives, how it is named, and what happens to it when it is replaced or rejected. Fixed procedure. Apply to every file created, moved, or replaced in a video session.
---

# File Management

This is a fixed procedure. Other skills say what a file is for; this
skill says where it goes, what it is called, and what happens to it when
it is superseded. Nothing about paths, folders, or naming is decided
anywhere else.

## 1. The root folder and the package folder

There are two folders, and they are not the same thing.

The **root** is the folder the session was opened in: the working
directory assigned to the session in the UI. It is not chosen, named,
or searched for; it is where you already are. Every path in this
document is relative to it, and every file the session creates goes
inside it. Nothing is written anywhere else, except throwaway
intermediates, which go in the session scratchpad.

The **package** is the folder that holds `skills/`, `stage/`, `tools/`,
`sfx/`, and `music/`. You know where it is because you read the skills
from it. It may be inside the root or somewhere else entirely; either
way it is read from, never written to. The location of the package
never changes where the root is. A session opened in one folder that
reads its skills from another still builds in the folder it was opened
in.

## 2. Layout

```
<root>/
  editable/
    NN-name-MM-DD.html          one editable per video (a copy of the stage template)
    materials/
      NN-name-MM-DD/            everything that editable references
        script.txt              the approved script, verbatim
        vo.mp3                  voice-over
        bgm.mp3                 background music
        timings.json            word timestamps for the VO
        <images, cut-outs, pose frames, fonts>
        deletable/              rejected, replaced, and unused materials
  renders/
    NN-name-MM-DD.mp4           the current render of each editable
    deletable/                  replaced, test, and partial renders
  metadata/
    NN-name-MM-DD.json          prompts, scripts, and absolute paths for the editable
```

Create `editable/`, `renders/`, `renders/deletable/`, and `metadata/`
in the root the first time they are needed. Nothing else is added at
the top level of the root.

## 3. Naming

Every video has one name, `NN-name-MM-DD`, shared exactly by its
editable, its materials folder, its render, and its metadata file.

- **NN**: two-digit sequence number of the video within this root. Take
  the highest number already present in `editable/` and add one; use
  `01` if the folder is empty. Never reuse a number, even if an earlier
  video was abandoned.
- **name**: the brand name if any brand has been mentioned in the session;
  otherwise the video's topic or title. Lowercase, letters and digits
  only, words joined by hyphens.
- **MM-DD**: month and day the editable was created. Hyphen, not slash:
  a slash is the path separator and cannot appear in a filename.

The name is assigned once, when the editable is created, and never
changes. Edits, re-renders, and later sessions keep it.

Examples: `01-iaso-09-20`, `02-morning-routine-09-21`.

## 4. The editable

- Create it by copying `stage/stage-9x16.html` from the package to
  `editable/NN-name-MM-DD.html` in the root. The template itself is never edited or
  built in; if the template needs a change, that is a separate task.
- Create `editable/materials/NN-name-MM-DD/` and its `deletable/`
  subfolder, and the metadata file (section 7), at the same time.
- In the copy, replace `EDITABLE-NAME` in the two `<audio>` `src`
  attributes with the video's name. The harness finds `timings.json`
  from the html filename by itself.
- An edit to a video is made to the same editable. Never create a second
  html for the same video. If an editable is rebuilt from scratch, the
  old one moves to its materials `deletable/` folder first.

## 5. Materials

- Everything the editable references lives in its materials folder and is
  referenced as `materials/NN-name-MM-DD/<file>`. Nothing referenced may
  live anywhere else, and nothing in `deletable/` may be referenced.
- Only material in use stays in the folder proper. The moment a file is
  rejected, replaced, superseded, or turns out to be unused, move it to
  `deletable/`. Generation sources the html does not reference (contact
  sheets, object sheets) go to `deletable/` as soon as the assets have
  been cut from them; the metadata records where each asset came from.
- A move into `deletable/` keeps the filename. On a name collision append
  `_2`, `_3`, and so on.
- Never delete on your own decision. The `deletable/` folders are
  emptied only when the user says so, which is asked at hand-over.
- `timings.json` is written next to the audio, which is already the
  materials folder; no move is needed.

## 6. Renders

- A render is written to `renders/NN-name-MM-DD.mp4`.
- Before rendering, if `renders/NN-name-MM-DD.mp4` already exists, move it
  to `renders/deletable/NN-name-MM-DD_<YYYYMMDD-HHMM>.mp4`, the suffix
  being the file's modification time. `renders/` therefore holds exactly
  one file per editable: the current one.
- Test renders and partial renders go straight to `renders/deletable/`.
- Render intermediates (frame captures, segments, mixed audio) are not
  kept. Point the renderer at the session scratchpad for them; if it
  leaves any beside the output, move them to `renders/deletable/`.

### A finished render is published, not left in the workspace

A render that is finalized and ready to publish does not end its life in
the root. It is uploaded into the Social Post Assets library with the
Spira CLI. `renders/` keeps the local copy, which stays the one current
file per editable; the upload is a copy out, not a move.

```bash
spira social assets tags                        # list tags, note the id
spira social assets upload <render path> --tag <id or name>
```

- Every upload needs a tag, and the CLI cannot create one. `--tag` is
  checked against the tags that already exist, and an unknown name fails
  with `VALIDATION_FAILED` before anything is transferred. List the tags
  first and match the video to the tag for its brand.
- IF no existing tag fits the video, ask the user to create one and
  wait for it. Never file a video under an approximate tag: there is no
  delete command, so a wrong tag cannot be undone from the CLI.
- Only the current render is uploaded. Nothing in `renders/deletable/`
  is ever published.
- A re-render that supersedes a published video is uploaded again once
  it is final; removing the superseded asset is the user's to do.
- Record the upload in the render's metadata entry (section 7).

## 7. Metadata

`metadata/NN-name-MM-DD.json` is created with the editable and updated on
every asset generation, replacement, move, and render. All paths are
absolute. Prompts and scripts are stored verbatim, so any asset can be
regenerated after its file has been deleted.

```json
{
  "root": "/abs/path/to/root",
  "name": "01-iaso-09-20",
  "brand": "IASO",
  "created": "2026-09-20",
  "editable": "/abs/path/to/root/editable/01-iaso-09-20.html",
  "script": {
    "file": "/abs/path/to/root/editable/materials/01-iaso-09-20/script.txt",
    "text": "the approved script, verbatim"
  },
  "assets": [
    {
      "file": "/abs/path/to/root/editable/materials/01-iaso-09-20/hero.webp",
      "status": "in-use",
      "kind": "image",
      "tool": "generator or process used",
      "prompt": "the exact prompt or instruction used, verbatim",
      "source": "/abs/path of the sheet it was cut from, or null",
      "url": "output URL returned by the generative AI service, or null",
      "credits": 3.45,
      "generated": "2026-09-20T14:02",
      "replaced_by": null
    }
  ],
  "renders": [
    {
      "file": "/abs/path/to/root/renders/01-iaso-09-20.mp4",
      "rendered": "2026-09-20T15:10",
      "status": "current",
      "fps": 30,
      "duration_ms": 40140,
      "published": {
        "tag": "IASO",
        "asset_id": "2a629f8e-b6ba-4a94-80b3-5a4db6971d40",
        "url": "https://static.viralwell.ai/…/….mp4",
        "uploaded": "2026-09-20T15:22"
      }
    }
  ]
}
```

- Every generated asset gets an entry the moment it is generated,
  including candidates that are later rejected. `credits` is the
  job's cost from the toolkit's price table, recorded at submission;
  the production's total cost is the sum of every `credits` in the
  file. When the generator
  returns an output URL, record it in `url`; it is the way back to the
  original once the local file and its source sheet are gone. `status` is `in-use` or
  `deletable`; when a file moves, update `file` to its new path and set
  `replaced_by` to the path of what took its place.
- The VO entry records the TTS or recording tool used; its prompt is the
  script text. The BGM entry records where the track came from.
- Each render gets an entry; a replaced render's `status` becomes
  `deletable` and its `file` is updated to the new path.
- `published` is `null` until the render is uploaded to Social Post
  Assets, and then holds the tag it was filed under, the `assetId` and
  the `url` the upload returned. They are the way to the published copy
  once the local file is gone.

## 8. Checklist before hand-over

- `editable/` holds one html per video plus `materials/`, nothing else.
- Every file the html references exists in `materials/NN-name-MM-DD/`,
  and none is in a `deletable/` folder.
- Every file in the materials folder proper is referenced by the html,
  or is `script.txt`, `vo.mp3`, `bgm.mp3`, or `timings.json`.
- `renders/` holds one mp4 per editable.
- Every finished render has been uploaded to Social Post Assets, and its
  metadata entry carries the `published` object the upload returned.
- The metadata file lists every asset and render with a verbatim prompt
  and an absolute path that exists.
