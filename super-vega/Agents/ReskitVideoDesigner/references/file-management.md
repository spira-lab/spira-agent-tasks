# File management (Re-skit)

The shared skill `Agents/DesignerShared/skills/file-management.md` decides every path, name and
move. This file only says how a re-skit fits it. Where the two differ, the shared skill wins,
with one exception that Atlas's closing text makes: **NN is the Task ID** (as for the Avatar
Designer), never a count of folders. The Brand number goes in the metadata.

## A video's files

```
Project/<BrandName>/
  editable/
    NN-name-MM-DD.html               the editable: a page that lists the build and embeds it
    materials/
      NN-name-MM-DD/
        plan.md                      the single record of the video (below)
        edit.json                    the build file: segments, overlays, sound (build_edit.py reads it)
        chain.json                   the generation plan you keep by hand (`chain.json`)
        source/                      source.mp4, info.json, timings.json, dna.md, frames, captures for this video
        assets/                      plates, outfit sheet, b-roll HTML and its renders, overlay PNGs and their HTML, masks
        gen/ref/                     reference clips sent to the video model
        gen/out/                     clips that came back (the chosen take only)
        music/                       briefs, lyrics, takes, transcripts of takes
        deletable/                   rejected takes, replaced files, scratch files
  renders/
    NN-name-MM-DD.mp4                the final video
    deletable/                       NN-name-MM-DD_draft.mp4, NN-name-MM-DD_share.mp4, older renders
  metadata/
    NN-name-MM-DD.json               every job, model, prompt, credit, the source link, the lessons
```

- `python3 <reskit>/tools/reskit.py new "<Brand>" <Task ID> --brand-number <n>` makes all of
  it at once. Run it before anything else; on a resumed session it prints the existing paths.
- The editable page is rewritten by every build. Never edit it by hand: change `edit.json`,
  then build again. It is an HTML file so Jani's backup and the Data Cleaner find the video;
  it is not a stage, and `render-fast.js` is never run on it.
- **A rejected or replaced take is moved to `deletable/`**, keeping its name (you move it when you redo a job). There are no suffixed copies left in place (`_v1`, `_failed`):
  `gen/out/` and `assets/` hold only what the build uses.
- The share copy and the drafts live in `renders/deletable/`, so `renders/` holds exactly one
  file per video.
- At the render, move the working files (frame folders, contact sheets) to `deletable/`. Keep
  `chain.json`, `edit.json` and `plan.md`.
- Never delete anything. Throwaway intermediates go to the session scratchpad.

## Brand-level files (the one place in Agents/ you write)

Personas, the outfit ledger and the brand's truth file belong to the brand, not to one video,
and must survive Jani's backups (Jani clears `Project/`). They live in Vega's client assets:

```
Agents/VegaOM/client-assets/<BrandName>/
  personas/<Name>/
    source/                  the given avatar image, or the Soul base image if one was made
    sheet_4k.png             the master character sheet (never edited in place)
    sheet.html               how the sheet was assembled, when built from photos
    outfits/                 one sheet per outfit: <YYYY-MM-DD>_<short-outfit-name>.png
    outfits.md               the outfit ledger (persona-and-outfits.md)
  brand/
    truth.md                 facts with sources and dates (brand-truth-and-text.md)
    logo/                    the real logo, from the brand's own site or the request
    ui/                      real screenshots and captures of the product
```

`Agents/VegaOM/client-assets/<BrandName>/personas/` and `.../brand/` are the **only** places in
`Agents/` this designer writes. Never touch the brand's other files there (the logo and product
images Vega keeps at the top of the brand's folder): read them, copy them into the video's
materials when a build needs them.

## The plan file

`plan.md` is the single record of a video, written as you go:

- what drives the source, with its timings
- the new story in one sentence, and the keep/cut/rewrite table
- the persona and the outfit chosen, and the ledger entry it created
- the generation plan: every job with model, settings and expected credits (read from `spira ai models get`), and the total
- the **job log** (last section of the file): you append one row per job the
  moment it finishes, with its job ID, model, settings, credits and render time
- the result: what was delivered, planned against actual credits, what was not verified

## The metadata file

`metadata/NN-name-MM-DD.json` follows the shared schema (root, task_id, brand_number, name,
brand, created, editable, assets, renders) and adds:

- `style`: `re-skit`; `build`: the edit.json path; `plan`: the plan.md path
- `source`: `{link, file, title, uploader, fetched}`
- `story`: the new story in one sentence
- `persona`: `{name, sheet, outfit, outfit_sheet, ledger}`
- `music`: where the soundtrack came from (kept source audio, generated, library) and why
- `assets[]`: every job, written by you the moment the job exists: label, job ID,
  model, the exact inputs and prompt, result URLs, file, credits and where the credit figure
  came from. Add an entry yourself for anything else that costs credits (a Scribe transcript
  through `make-timings.py` prints its credits).
- `credits_total`: the sum of every asset's credits (you keep it up to date)
- `renders[]`: written by `build_edit.py final`
- `lessons[]`: proposed lessons (`reskit.py lesson`)
- `risks[]`, `unverified[]`: what you flag and what you could not check

Inputs for generation are public URLs made with `host_file`: host only what a job needs, never anything personal.
