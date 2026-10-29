---
name: atlas-project-manager
description: Atlas, the project manager. The planning step of Nova's own loop for every video task, one video or many, as a batch sheet (a single video is a batch of one). Each video is made by its own designer, handed over by Nova through the Agent tool (or done inline by Nova when the Agent tool is unavailable). Videos are produced one after another. Use when Nova has a filled batch sheet and is about to run it.
---

# Atlas — Project Manager (Batch Planning and Hand-off)

Atlas is not a separate agent or process. This skill is the planning part of
**Nova's own loop**: Nova reads it when she has a batch sheet to run and follows
it herself. She does not produce any video herself: each row is made by one
designer, from start to finish. It designs the video, renders it, and does
what comes after, in one go, because the designer that built the video holds the
build context. Nova's job here is the hand-offs and the order.

## Project boundary

**Work only inside the Super Nova folder.** Every skill, doc, and tool an agent reads comes from inside it. Copies of these skills exist elsewhere on this machine and are outdated: never read, search for, or follow them. IF a skill or file you need is not inside the folder, stop and say so in the result; never fetch it from outside.

`atlas-sheet.py` refuses any row whose skill path is outside the folder.

## Where things are

- `<super>` is the Super Nova folder. `<atlas>` is
  `<super>/Agents/AtlasPM`, the folder that holds this skill.
- `<super>/Project` is the build folder. Each designer saves its video in
  the client's brand folder, `<super>/Project/<BrandName>/`, from the row's
  Brand column (blank: `Project/Brandless/`).
- Atlas's files, all named `atlas-` so they never clash with other agents' files:

  | File | Path |
  |---|---|
  | This skill | `<atlas>/atlas-project-manager.md` |
  | Sheet tool | `<atlas>/tools/atlas-sheet.py` |
  | Blank batch sheet | `<atlas>/docs/atlas-batch-template.md` |
  | Designer list (style → designer skill) | `<atlas>/docs/atlas-designers.json` |
  | Batch sheets | `<atlas>/batches/atlas-batch-<YYYY-MM-DD>-<label>.md`, one file per batch, each with its `.agents.json` session record beside it |

- The default video designer skill each designer reads is
  `<super>/Agents/TalkingHeadEditedVideoDesigner/skills/talking-head-edited-video-designer.md`. A row's Style picks the designer from the
  designer list (e.g. `explainer` → `<super>/Agents/ExplainerVideoDesigner/skills/explainer-video-designer.md`); the
  "Read the skill" column can name another designer in `<super>/Agents/`.
- The sheet is the batch sheet Nova builds with `nova-batch.py`: a Markdown file in
  `<atlas>/batches/` whose table has a Task ID and a Script column.

## How it runs

The whole job is one native Claude Code session: Nova's. There is no
window, nobody to answer questions mid-run, no second agent process and no
background launcher.

- The session works in `<super>/Project`, with read access to
  `<super>/Agents`.
- Never write shell loops or `$(...)` variables: use the tools (`atlas-sheet.py`,
  the designer's own tools) instead.
- **Videos run one after another.** Only one row is in production at a time: take
  a row, hand it over, record its outcome, then take the next. A request is never
  split across batches and a second sheet is never started while the current one
  still has rows to start.
- **Never end the turn while a row is in production.** The final `submit_result`
  comes only after every row is done, failed, or stopped with a question.
- Progress goes out through `report_progress` (see "Reporting"); generation
  goes through `submit_ai_job` / `wait_ai_job`, and a file that needs a public URL
  through `host_file`. The designers' skills name these themselves.

## Handing a row to a designer

Two ways, and the same request either way:

1. **Sub-agent (preferred).** Start one sub-agent with the SDK's Agent tool,
   named `Designer` followed by the row's Task ID (for example `Designer07`), and
   brief it with the request and the closing text below. It reads the designer's
   skill path and works in the task folder `<super>/Project`. It replies with
   one line.
2. **Inline (when the Agent tool is unavailable).** Nova reads the designer's
   skill herself (the path in the row's "Read the skill") and does the designer's
   role, following that skill exactly, then records the outcome the same way.
   Never open a skill you do not need to: in the sub-agent case Nova passes the
   path only and the designer reads it.

## Receiving a sheet

Nova creates the sheet and fills every row except the script; the Script
Writer (Echo) fills the scripts. Before anything else, run
`atlas-sheet.py <sheet.md> summary`. IF any row is `draft` (its style needs a
script and it has none yet), Echo is not finished: do not run the sheet and finish
the scripts first. Rows of a **scriptless** style have no script by design: they
are pending from the start, and their designer works from the Instructions
column.

When you add a new designer to the list, mark a scriptless style
`{"skill": "<path>", "script": "none"}`; a plain path means the style needs
a script.

**Clone and Re-skit rows** (styles `clone` and `re-skit`; the owner's rules, 2026-10-24): scriptless rows whose request carries `This is the source video: <link>`. They run like every other row, with no cap of their own. They never stop for plan approval and run straight through. Their READY editable may be a build script rather than an HTML stage; pass it on as usual. They also write brand-level files outside `Project/`, in `Agents/NovaOM/client-assets/<Brand>/` (`personas/`, `brand/`, `voice.md`); that is expected, not a stray file.

**Avatar rows** (style `avatar`, output type `avatar-image`; the owner's
rule, 2026-10-22): one avatar image per row, made by the Avatar Designer,
never a video. Its designer gets **only what the avatar looks like**: the
row's request, as `next` prints it, carries just the Task ID, the skill,
the numbers and the avatar description (or "No description given"). Pass
it on exactly like that and never add a script, logo, color, product,
music or style reference to it. The designer replies DONE with the
PNG's path.

**Carousel rows** (any style ending in "carousel", e.g. `corporate carousel`;
output type `carousel`; the owner's decisions, 2026-10-27): one 4:5
carousel per row (4 to 7 slides, 1080×1350 JPEGs), made by that style's
carousel designer (`corporate carousel`: the Corporate Carousel Designer;
more carousel designers will follow), never a video. An old sheet's Style
`carousel` is the same as `corporate carousel` (renamed 2026-10-27). It is
**not** scriptless: its Script is Echo's topic angle, so a carousel row
is a draft until Echo fills it. Its request, as `next` prints it, carries
only the Task ID, the skill, the brand and its numbers, the instructions
(with `Product: <name>.` when there is one and `Brand website: <url>`)
and the topic angle. Pass it on exactly like that, with the usual
closing text. The designer replies DONE with the carousel's **folder** path
(`Project/<Brand>/carousels/<name>`), not a render file.

**Choosing the designer is Atlas's job.** Each row's Style names the video
style; `atlas-sheet.py` looks it up in the designer list,
`<atlas>/docs/atlas-designers.json` (a blank Style uses the default,
talking head edited). IF a style has no designer, `next` stops with
`no designer for style`: that row cannot run; say so in the result. When a
new designer is added to `<super>/Agents/`, add its style to the list.

## Before the first row

Settle everything from the sheet and stop with a clear message when something
needs the user.

- **Check the build folder.** Run `pwd`. It must be `<super>/Project`.
  IF it is anything else, stop and say `wrong build folder: <pwd>`: a batch's
  `editable/`, `renders/`, and `metadata/` must never land beside the agents' files.
- **Rows left mid-way.** IF the summary shows rows marked designing or
  rendering, they are left over from a run that was cut off. Do not start them
  again on your own: unless the user's request says to resume them (then
  resume each from its recorded session, or by briefing a new designer with the
  row's request and its recorded files), report them as unfinished and ask. A
  row marked **ready** is not interrupted: its design is finished and saved, and
  it only needs its render step.
- Each row carries a Task ID and a Brand number, both issued by Nova.
  The designer names the video's files by the Task ID and records both
  numbers in its metadata; never by the next number found in `editable/`.
  Here is why: finished videos get moved out to backup, so the root no
  longer holds them. Counting what is in the folder would restart the
  numbering and hand out numbers already used by videos made before,
  and looking a video up by its number would then find two. The Task ID
  is the one number that stays unique however the folders are cleared.
- Read the clock with `date` and keep it as the batch start time.

## The request

`atlas-sheet.py next` builds each row's request in this format. A line whose
column is blank is left out; Task ID, the skill, and the script are
always there.

```
Task ID: <Task ID>
Read this skill first: <Read the skill>
Brand: <Brand>
Brand number: <Brand number>
This is the style: <Style ref>
This is the product image: <Product>
Use this brand logo: <Brand logo>
Use this brand color: <Brand color>
Music: <Music>
These are the instructions: <Instructions>
Here is the script:
<Script>
Read this skill right after you complete the video and continue: <After video skill>
```

The Music column takes `library`, `none`, or blank for generated music.
The Product column takes a product image's link or file path, or stays
blank when the video has no product. Brand logo takes the logo image's
link or file path, and Brand color takes the colour as a hex code, such
as `#1E40AF`, or several separated by commas; both stay blank when not
given. Brand assets are the paths and links the batch tool already took from
the client ledger (`Agents/NovaOM/client-assets/<BrandName>/`); pass them as printed.

The Topic column, at the far right, is for the user's review only: it
records which audience or subject each script is for. Ignore it.
`atlas-sheet.py` never puts it into a request, and nothing in the batch reads
or changes it.

## The loop: one row at a time

Run this loop until the batch is finished:

1. **Take the next row.**

   ```bash
   python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> next
   ```

   It marks that row designing and prints its Task ID and its request. IF it
   prints NONE, no rows are left to start: go to "The report".

2. **Hand it over.** Give the designer (sub-agent, or Nova inline) the request
   exactly as printed, followed by this closing text and nothing else, with
   `<sheet.md>` as the sheet's full path and `<atlas>` as the full path of
   `Agents/AtlasPM`:

   ```
   This is one task of an unattended batch; no one can answer questions. Your Task ID is this video's number: use it as the NN in the video's name, not the next number in editable/.
   Do the whole video: build it, run the stage skill's checks, render it, then IF your request named a skill to read after the video is complete, read and follow it. When everything is finished, your final reply is exactly one line: DONE <render path> <total credits> <minutes>. IF you could not finish, reply FAILED <short reason>. IF you stopped because a skill told you to check with the user, reply QUESTION <what you needed to ask>.
   Just before that final reply, record it on the batch sheet with this command, using done, failed, or question to match your line: python3 "<atlas>/tools/atlas-sheet.py" "<sheet.md>" mark <Task ID> <done|failed|question> --if designing "<your line>"
   ```

   Record which session owns the row when a sub-agent was started (its agent
   ID): `python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> agent <Task ID> <agent id>`.

3. **Record the outcome.** The designer marks its own row. IF its reply reached
   you but the row still shows `designing`, record the reply yourself, with `--if`
   so a late line never moves a row backwards: DONE is `done`, FAILED is `failed`,
   QUESTION is `question`, anything else is `failed` with the reply as the result:

   ```bash
   python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> mark <Task ID> <done|failed|question> --if designing "<its line>"
   ```

   IF a designer ended without any reply line, mark the row `failed` with
   `--if` and "ended without a reply".

4. **Report progress, then go back to 1** (see "Reporting").

**Questions are Nova's to answer, straight away.** A designer's `QUESTION` is
decided by Nova herself (see her skill, "Answering agents' questions"): she
resumes the row's own designer with the decision (or briefs a new one with the
row's request, its recorded files and the answer), marks the row `designing`
with `--if question`, and carries on. A row never waits for the end of the
batch on a question she can answer. IF the answer is for the user to decide, the
row stays `question` and goes into the report.

## Reporting

`report_progress` goes out at the **stages** intake, assign, produce and deliver:

- **assign:** once the sheet is checked and its first row is being handed over.
- **produce:** one `report_progress` per video as it finishes, one short line:
  brand and number, Task ID, style or language, `<n> of <total> done`, and a
  `FAILED` or `QUESTION` row the same way. Never hold a finished video back
  until the batch ends, and never wait on one to send the next line.
- **deliver:** at the close (see "The report").

Do not log outputs yet: logging happens once, at the batch's close, from `tally`.

## Hard rules

- Never produce, fix, or finish a video outside the designer's own skill, and
  never redo a designer's task. A failed or questioning row is recorded and
  left for the user; the batch moves on.
- Never hand a row to a session that did not design it, when a recorded session
  exists: fixes and answers go to the row's own designer.
- Never produce two videos at once: one row is in production at a time.
- Never end the turn while a row is in production.
- Never retry or redo a row on your own. A retry spends credits twice.
  A redo happens only when the user orders it.
- Never open a skill you hand over: a designer's skill or an After
  video skill. Pass their paths only (the sheet tool writes them into each
  request); the designer reads them. The only exception is the inline fallback
  above.

## Redo and cancel (only on the user's order)

A FAILED row stays in the sheet as it is until the user decides. Nothing is
redone or cancelled on Atlas's own.

- **Redo.** The Data Cleaner archives the failed attempt's files and sets
  the row back to `pending`. The same sheet is then run again, and that row runs
  like any pending row: a **new** designer, from scratch, with the same Task ID
  and Brand number. The failed session is never resumed.
- **Cancel.** The Data Cleaner archives the files, removes the row from
  the sheet, and frees its numbers. Nothing is left to do.

## The report

WHEN the batch is finished (`next` printed NONE and no row is `designing`), run
`atlas-sheet.py <sheet.md> summary`, read the clock again, and report in a few
lines: how many rows finished, failed, and stopped with a question, the Task IDs
of every row that did not finish, the total credits as the sum of the DONE lines,
and the minutes the batch took from the start time. Nothing about what the
videos show.
