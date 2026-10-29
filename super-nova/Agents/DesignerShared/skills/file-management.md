---
name: file-management
description: Where every file of a video session lives, how it is named, and what happens to it when it is replaced or rejected. Fixed procedure. Apply to every file created, moved, or replaced in a video session.
---

# File Management

This is a fixed procedure. Other skills say what a file is for; this
skill says where it goes, what it is called, and what happens to it when
it is superseded. Nothing about paths, folders, or naming is decided
anywhere else.

## 1. Super Nova, the Project folder, and the brand folder

Everything lives inside the **Super Nova** folder:

```
Super Nova/
  Agents/                         every agent; read from, never written to
    DesignerShared/               the shared folder: what every video designer uses
    <Style>VideoDesigner/         one folder per video style, holding its style skill
  Project/                        where every video project is saved
    <BrandName>/                  one folder per client brand: the root
```

The **shared folder** is `Super Nova/Agents/DesignerShared/`, the folder
that holds the shared `skills/`, `stage/`, `tools/`, `sfx/`, `music/`, and
`Contact sheet/`. Your own **style folder** (e.g.
`Agents/TalkingHeadEditedVideoDesigner/`) holds only your style skill. Both
are read from, never written to.

The session is opened in `Super Nova/Project/`. The **root** of a video
is its client's **brand folder**, `Project/<BrandName>/`. Every path in this
document is relative to the root, and every file the session creates goes
inside it. Nothing is written anywhere else, except throwaway
intermediates, which go in the session scratchpad.

- **BrandName** is the brand as given in the request, with spaces and
  special characters removed and capitalization kept: "Glow Lab Co."
  becomes `GlowLabCo`. It is the same name the operations manager uses for
  the brand in her own files, so one brand has one folder everywhere.
- Create `Project/<BrandName>/` the first time a brand has a video. Every
  later video of that brand goes into the same folder.
- IF the request's brand is `Brandless`, or it names no brand, the video is a generic one for no client: use `Project/Brandless/`. A Brandless video shows no brand at all: no brand name, no logo, nothing drawn or written to stand in for one (the word "Brandless" never appears on screen).
- Never build in `Super Nova/` itself, in `Project/` itself, or anywhere
  in `Agents/`.

## 2. Layout

```
Project/<BrandName>/
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
in the brand folder the first time they are needed. The only other folder
at the top level of the brand folder is `archive/`, which belongs to the
Data Cleaner: it holds failed attempts. Never write to it and never read
from it.

## 3. Naming

Every video has one name, `NN-name-MM-DD`, shared exactly by its
editable, its materials folder, its render, and its metadata file.

- **NN**: the video's **Task ID**, from the request. It is unique across
  the whole system, so it never repeats however the folders are cleared.
  It is padded to at least two digits (`7` becomes `07`).
  - Every request carries two numbers, both issued by the operations
    manager (Nova): the **Task ID** (system-wide) and the **Brand
    number** (per brand, its place in the brand's own count). The Task
    ID goes in the name; both go in the metadata file (the owner's
    decision, 2026-10-24, matching how videos were already named).
  - Never number a video by counting the files in `editable/`, `renders/`,
    or `metadata/`. Finished videos are moved out to backup, so the folders
    no longer hold them; counting would reuse numbers.
  - IF the request is missing either number, stop and ask before creating
    any file. Never make one up.
  - A redo has the same Task ID and Brand number as the failed attempt.
    The failed attempt has already been moved to `archive/`, so build from
    scratch as for a new video.
- **name**: the brand name, lowercase, letters and digits only, words
  joined by hyphens (`GlowLabCo` → `glowlabco`). IF the brand is `Brandless` (or there is none), the video's topic in two to four words, in the same form (`ai-side-hustles`), so brandless videos tell apart.
- **MM-DD**: month and day the editable was created. Hyphen, not slash:
  a slash is the path separator and cannot appear in a filename.

The name is assigned once, when the editable is created, and never
changes. Edits, re-renders, and later sessions keep it.

Examples: `161-iaso-10-21` in `Project/IASO/`, `244-test-10-23` in
`Project/Test/` (its Brand number, 09, is in the metadata).

## 4. The editable

- Create it by copying `stage/stage-9x16.html` from the shared folder to
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
- Never delete anything. The `deletable/` folders are never emptied;
  they are backed up with the rest of the project by Jani, the backup agent.
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

## 7. Metadata

`metadata/NN-name-MM-DD.json` is created with the editable and updated on
every asset generation, replacement, move, and render. All paths are
absolute. Prompts and scripts are stored verbatim, so any asset can be
regenerated after its file has been deleted.

```json
{
  "root": "/abs/path/to/Super Nova/Project/NovaSkin",
  "task_id": "01",
  "brand_number": "01",
  "name": "01-novaskin-09-20",
  "brand": "NovaSkin",
  "created": "2026-09-20",
  "editable": "/abs/path/to/root/editable/01-novaskin-09-20.html",
  "script": {
    "file": "/abs/path/to/root/editable/materials/01-novaskin-09-20/script.txt",
    "text": "the approved script, verbatim"
  },
  "assets": [
    {
      "file": "/abs/path/to/root/editable/materials/01-novaskin-09-20/hero.webp",
      "status": "in-use",
      "kind": "image",
      "tool": "generator or process used",
      "prompt": "the exact prompt or instruction used, verbatim",
      "source": "/abs/path of the sheet it was cut from, or null",
      "url": "output URL returned by the generative AI service, or null",
      "credits": 5,
      "generated": "2026-09-20T14:02",
      "replaced_by": null
    }
  ],
  "renders": [
    {
      "file": "/abs/path/to/root/renders/01-novaskin-09-20.mp4",
      "rendered": "2026-09-20T15:10",
      "status": "current",
      "fps": 30,
      "duration_ms": 40140
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

## 8. Checklist before hand-over

- `editable/` holds one html per video plus `materials/`, nothing else.
- Every file the html references exists in `materials/NN-name-MM-DD/`,
  and none is in a `deletable/` folder.
- Every file in the materials folder proper is referenced by the html,
  or is `script.txt`, `vo.mp3`, `bgm.mp3`, or `timings.json`.
- `renders/` holds one mp4 per editable.
- The metadata file lists every asset and render with a verbatim prompt
  and an absolute path that exists.
