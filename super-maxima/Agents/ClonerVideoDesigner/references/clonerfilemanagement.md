---
name: cloner-file-management
description: The Cloner's additions to the shared file-management skill - what goes in each of the clone's working subfolders, how jobs are logged, and the clone's metadata fields. The shared skill (Agents/DesignerShared/skills/file-management.md) wins on everything it covers. Read it before creating any file.
---

# Where the Cloner saves its work

The shared file-management skill is the rule: the brand folder
`Super Nova/Project/<BrandName>/`, one editable per video in
`editable/`, its materials in `editable/materials/NN-name-MM-DD/`, the
render in `renders/`, the metadata in `metadata/`. This file only adds
what a clone needs on top of it.

- **BrandName** is the house brand key (spaces and special characters
  removed, capitals kept): `CookiyLabs`, never `cookiy-labs`. Reuse the
  brand folder when it exists.
- **NN is the Task ID**, two digits at least. Never a count of folders.
- **name** is the brand in lowercase letters and digits (`cookiylabs`);
  **MM-DD** is the day the editable was created. The source's own short
  title goes in the metadata as `source_title`.
- Nothing is written in `Agents/`, except the text record of a persona
  you made, `Agents/NovaOM/client-assets/<BrandName>/personas/<Name>/<Name>.md`
  (the skill, section 6). Persona images stay in the clone's `persona/`
  folder (the owner's rule, 2026-11-17). Nothing is written in Downloads or outside Super Nova;
  throwaway scratch goes in the session scratchpad or the system temp
  folder.

## Inside the materials folder

```
editable/materials/NN-name-MM-DD/
  source/        source.<ext> (the downloaded or copied source), info.json (spira media info),
                 source.txt (transcript), frames/, understanding.md, brand-dna.<ext>,
                 brand/ (screenshots captured or provided, products.json if pulled),
                 cuts/ (source clips cut for Wan or Kling: audio stripped, text removed)
  plan.md        what drives the source, the shot list, the approach per shot, the casting,
                 the lines, the music decision, the generation plan with expected credits
  script.txt     the clone's lines, when Omni speaks them (the chunker's input)
  persona/       each persona used: <Name>.png and <Name>.json (made for this clone), or
                 <Name>.md pointing to the anchor sheet in client-assets
  stills/        background plates, persona edits, transparent elements, each with its prompt JSON
  clips/         every generated clip with its payload JSON, .job and .url files; the trimmed
                 clips the stage plays (<clip>-trim.mp4)
  audio/         vo.mp3 and timings.json, bgm.mp3, music takes, cuts, lyrics.txt,
                 source-lyrics.txt, lyrics check output, ambience, sound effects
  jobs.md        one line per Spira job (below)
  deletable/     rejected takes, placeholders, retakes, working files no longer needed
```

- **The editable references only files in this folder**, by relative
  path (`materials/NN-name-MM-DD/clips/c1-trim.mp4`), and never anything
  in `deletable/`. The renderer serves only from the editable's folder.
- **Prompt or payload next to every generated file,** same stem
  (`plate-1.png` and `plate-1.json`).
- **Don't delete anything.** A rejected or replaced file moves to
  `deletable/` with its name (`_2`, `_3` on a collision) and its metadata
  entry is updated, as the shared skill says.

## jobs.md

One line per job, written the moment it is submitted, completed when it
finishes:

```
<label> | <job id> | <model> | <settings> | <credits> | <seconds> | <status>
```

For example `wan-c2 | 6f2… | wan-3.0 | r2v 720p 9:16 9s sound:false | 55.62 | 318 | completed`.
The same facts go in the metadata's `jobs`.

## The metadata

`metadata/NN-name-MM-DD.json` is required for every clone. It holds the
shared skill's fields (`root`, `task_id`, `brand_number`, `name`, `brand`,
`created`, `editable`, `assets`, `renders`; all paths absolute, prompts
verbatim), plus:

```json
{
  "style": "clone",
  "source": { "link": "<the request's source>", "file": "/abs/.../source/source.mp4",
              "sound_name": "<from spira media info, or null>" },
  "source_title": "fan-outfit-change",
  "brand_dna": "<url or null>",
  "method": "wan replacement, 4 clips | kling dance | omni talking head | ...",
  "workflow": "Clone Source Understanding <Task ID>",
  "personas": [ { "name": "Maya", "file": "/abs/...", "origin": "request | made | reused",
                  "client_assets": "/abs/.../client-assets/<BrandName>/personas/Maya/" } ],
  "music": { "decision": "generated instrumental | generated with vocals | library MusicN | none",
             "why": "one line" },
  "jobs": [ { "label": "wan-c2", "job_id": "...", "model": "wan-3.0", "settings": { },
              "credits": 55.62, "credits_source": "job | price | estimate",
              "seconds": 318, "status": "completed | failed | rejected" } ],
  "planned_credits": 118,
  "total_credits": 121.4,
  "report": { "unverified": ["mix measured, not heard"], "new_ground": [], "flaws": [] },
  "lessons": [ { "area": "...", "applies_when": "...", "failed": "...", "why": "...",
                 "fixed_by": "...", "carry_forward": "...", "not_for": "..." } ]
}
```

- **Credits.** Each job's credits come from the job itself (`data.credits`
  in `spira --json ai jobs status`), or the live price times the seconds
  billed when the job carries none. Never from the account balance.
  Every asset entry carries its `job_id`; the job's credits sit on its
  first asset entry and `0` on any further file from the same job (Suno's
  second song). `total_credits` is the sum of `jobs[].credits`, and must
  equal the sum of the assets' credits: a difference means a job is
  missing from one list. A failed job that was not billed has `0`.
- **Lessons.** A run issue that teaches something becomes one entry in
  `lessons`, in the format of `cloner-lessons.md`. A clean run has an
  empty list. Lessons are proposals: Nova adds approved ones to the shared
  lessons file. Never write to the skill or its references.
- **No clock file and no balance.** The start time comes from `date` at
  the start, the minutes from `date` at the end.
