---
name: atlas-project-manager
description: Atlas, the project manager. The planning step of Vega's own loop for every video task, one video or many, as a batch sheet (a single video is a batch of one). Each video is made by its own designer, handed over by Vega through the Agent tool (or done inline by Vega when the Agent tool is unavailable). Videos are produced in parallel, as many at a time as the machine takes: up to 8 designing, 4 rendering and 4 transcribing. Use when Vega has a filled batch sheet and is about to run it.
---

# Atlas — Project Manager (Batch Planning and Hand-off)

Atlas is not a separate agent or process. This skill is the planning part of
**Vega's own loop**: Vega reads it when he has a batch sheet to run and follows
it himself. He does not produce any video himself: each row is made by one
designer, from start to finish. It designs the video, renders it, and does
what comes after, in one go, because the designer that built the video holds the
build context. Vega's job here is the hand-offs, the slots and the outcomes.

## Project boundary

**Work only inside the Super Vega folder.** Every skill, doc, and tool an agent reads comes from inside it. Copies of these skills exist elsewhere on this machine and are outdated: never read, search for, or follow them. IF a skill or file you need is not inside the folder, stop and say so in the result; never fetch it from outside.

`atlas-sheet.py` refuses any row whose skill path is outside the folder.

## Where things are

- `<super>` is the Super Vega folder. `<atlas>` is
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
  | Parallel limits (designing 8, rendering 4, timing 4) | `<atlas>/docs/atlas-limits.json` |
  | Batch sheets | `<atlas>/batches/atlas-batch-<YYYY-MM-DD>-<label>.md`, one file per batch, each with its `.agents.json` session record beside it |

- The default video designer skill each designer reads is
  `<super>/Agents/TalkingHeadEditedVideoDesigner/skills/talking-head-edited-video-designer.md`. A row's Style picks the designer from the
  designer list (e.g. `explainer` → `<super>/Agents/ExplainerVideoDesigner/skills/explainer-video-designer.md`); the
  "Read the skill" column can name another designer in `<super>/Agents/`.
- The sheet is the batch sheet Vega builds with `vega-batch.py`: a Markdown file in
  `<atlas>/batches/` whose table has a Task ID and a Script column.

## How it runs

The whole job is one native Claude Code session: Vega's. There is no
window and nobody to answer questions mid-run. Each row's designer is a
**background sub-agent** of that session (the owner's decision, 2026-11-10).

- The session works in `<super>/Project`, with read access to
  `<super>/Agents`.
- Never write shell loops or `$(...)` variables: use the tools (`atlas-sheet.py`,
  the designer's own tools) instead.
- **Videos run in parallel.** At most **8 rows are designing at once across the
  whole employee**, every batch sheet counted together, at most **4 renders**
  and at most **4 Whisper transcriptions** (timings, lyrics, music cuts, Quill's
  video reads) run at once; the timing slots are separate from the render slots.
  All three limits are in `<atlas>/docs/atlas-limits.json` and are enforced
  by the tools, not by counting yourself: `next` prints `FULL` instead of a row when
  8 are designing, every render goes through `heavy-slot.py` (see the closing
  text), and every Whisper tool takes a timing slot itself (exit 75 = slots busy,
  run the same line again). `atlas-sheet.py <sheet.md> slots` shows how many are in use.
- A request is never split across batches. A new batch may start while another
  still has rows in production: it takes the slots the other leaves free (a tail
  hand-off). Each batch is reported and closed on its own.
- **Never end the turn while a row is in production.** A background designer lives
  only as long as Vega's turn: when the turn ends, every designer still working is
  stopped with it. The final `submit_result` comes only after every row is done,
  failed, or stopped with a question.
- Progress goes out through `report_progress` (see "Reporting"); generation
  goes through `submit_ai_job` / `wait_ai_job`, and a file that needs a public URL
  through `host_file`. The designers' skills name these themselves.

## Handing a row to a designer

Two ways, and the same request either way:

1. **Background sub-agent (preferred).** Start one sub-agent with the SDK's Agent
   tool **in the background** (`run_in_background: true`), named `Designer`
   followed by the row's Task ID (for example `Designer07`), and brief it with the
   request and the closing text below. It reads the designer's skill path and
   works in the task folder `<super>/Project`. It replies with one line, which
   reaches you as its completion notice. Record its agent ID right away (see the
   loop): it is how you answer its question or pick it up after a restart.
2. **Inline (when the Agent tool is unavailable).** Vega reads the designer's
   skill himself (the path in the row's "Read the skill") and does the designer's
   role, following that skill exactly, then records the outcome the same way.
   Inline rows run one at a time: Vega cannot design two videos himself at once.
   Never open a skill you do not need to: in the sub-agent case Vega passes the
   path only and the designer reads it.

## Receiving a sheet

Vega creates the sheet and fills every row except the script; the Script
Writer (Echo) fills the scripts. Before anything else, run
`atlas-sheet.py <sheet.md> summary`. IF any row is `draft` (its style needs a
script and it has none yet), Echo is not finished: do not run the sheet and finish
the scripts first. Rows of a **scriptless** style have no script by design: they
are pending from the start, and their designer works from the Instructions
column.

When you add a new designer to the list, mark a scriptless style
`{"skill": "<path>", "script": "none"}`; a plain path means the style needs
a script.

**Clone and Re-skit rows** (styles `clone` and `re-skit`; the owner's rules, 2026-10-24): scriptless rows whose request carries `This is the source video: <link>`. They run like every other row, with no cap of their own. They never stop for plan approval and run straight through. Their READY editable may be a build script rather than an HTML stage; pass it on as usual. They also write brand-level files outside `Project/`, in `Agents/VegaOM/client-assets/<Brand>/` (`personas/`, `brand/`, `voice.md`); that is expected, not a stray file.

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

**Lifestyle story carousel rows** (style `lifestyle story carousel`,
output type `carousel`; the owner's decisions, 2026-11-03): the one
**scriptless** carousel style, made by the Lifestyle Story Carousel
Designer (photoreal people stories, 5 to 10 slides, 4:5 or a 9:16 story
when the instructions ask). Echo writes nothing for it: the designer
picks and researches its own idea, so the row is pending from the start
and its request ends with "This is a scriptless carousel" instead of a
topic angle. Pass it on exactly like that, with the usual closing text.
It replies DONE with the carousel's folder path like any carousel row.
The designer never waits at a credit gate: each row may spend up to 150
credits, and a quote over that comes back as a `QUESTION` with the quote,
like any other question for Vega. Expect about 80 to 100 credits per row.

**Corporate or lifestyle.** A request for "carousels" that names neither
kind is decided by Vega before the sheet is built (his skill,
"Which carousel designer"); the Style column then names the kind.

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
- **Rows left mid-way.** Two cases:
  - **This run was restarted** (the session was told it is resuming after a
    restart): its designing rows are yours. Follow "After a restart" below, with
    no question to the user.
  - **Rows from an earlier run** (the summary shows rows marked designing or
    rendering in a sheet this run never started): they were cut off. Do not
    start them again on your own: unless the user's request says to resume them
    (then follow "After a restart" for them), report them as unfinished and ask.
    They still count against the 8 slots, so a `FULL` that names such rows is
    a question for the user too.
  A row marked **ready** is not interrupted: its design is finished and saved,
  and it only needs its render step.
- Each row carries a Task ID and a Brand number, both issued by Vega.
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
the client ledger (`Agents/VegaOM/client-assets/<BrandName>/`); pass them as printed.

The Topic column, at the far right, is for the user's review only: it
records which audience or subject each script is for. Ignore it.
`atlas-sheet.py` never puts it into a request, and nothing in the batch reads
or changes it.

## The loop: fill, wait, handle, fill again

Run this loop until the batch is finished:

1. **Fill the free slots.** Run `next` again and again until it prints `FULL` or
   `NONE`:

   ```bash
   python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> next
   ```

   Each time it prints a row, it has marked that row designing: hand it over at
   once (step 2) before the next `next`. `FULL <n>/<cap>` means every slot is
   taken (it lists the rows holding them); `NONE` means no row of this sheet is
   left to start.

2. **Hand it over.** Start the row's designer in the background with the request
   exactly as printed, followed by this closing text and nothing else, with
   `<sheet.md>` as the sheet's full path, `<atlas>` as the full path of
   `Agents/AtlasPM` and `<shared>` as the full path of `Agents/DesignerShared`:

   ```
   This is one task of an unattended batch; no one can answer questions. Your Task ID is this video's number: use it as the NN in the video's name, not the next number in editable/.
   Other designers are working at the same time, each on its own video. So: run every render through the render slots, as python3 "<shared>/tools/heavy-slot.py" <Task ID> -- <render command> with a Bash timeout of 600000, and when it exits 75 run the same line again. Transcriptions (make-timings.py and the other Whisper tools) queue for the 4 timing slots on their own; when one exits 75, run the same line again too. Write a brand's shared files (brand/truth.md, brand/outfits.md, personas/, voice.md, brand/ui/, the lessons files) only through python3 "<shared>/tools/brand-lock.py", as your skill says. Keep throwaway files in <scratchpad>/t<Task ID>/ only, and never read or run another task's files. The moment submit_ai_job returns a job id, write it into your metadata or chain.json with status "submitted".
   Do the whole video: build it, run the stage skill's checks, render it, then IF your request named a skill to read after the video is complete, read and follow it. When everything is finished, your final reply is exactly one line: DONE <render path> <total credits> <minutes>. IF you could not finish, reply FAILED <short reason>. IF you stopped because a skill told you to check with the user, reply QUESTION <what you needed to ask>.
   Just before that final reply, record it on the batch sheet with this command, using done, failed, or question to match your line: python3 "<atlas>/tools/atlas-sheet.py" "<sheet.md>" mark <Task ID> <done|failed|question> --if designing "<your line>"
   ```

   Record which session owns the row right after starting it (its agent ID):
   `python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> agent <Task ID> <agent id>`.

3. **Wait.** When no slot is free or no row is left to start, wait for a row to
   change, with a Bash timeout of 600000 (add `--also <other sheet>` for each other
   batch of yours still in production):

   ```bash
   python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> wait 540
   ```

   A designer's completion notice that arrives meanwhile is handled straight
   away, the same as a changed row. On a timeout, wait again.

4. **Handle each changed row.**
   - `done`: `host_file` its render when the reply needs a public link, then one
     `report_progress` line (see "Reporting").
   - `failed`: one `report_progress` line with the reason.
   - `question`: answer it now (see below), continue the row's own designer through
     its agent ID with the answer, then
     `atlas-sheet.py <sheet.md> mark <Task ID> designing --if question "<answer>"`.
   - A designer's reply reached you but its row still shows `designing`: record
     the reply yourself, with `--if` so a late line never moves a row backwards:
     DONE is `done`, FAILED is `failed`, QUESTION is `question`, anything else is
     `failed` with the reply as the result:

     ```bash
     python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> mark <Task ID> <done|failed|question> --if designing "<its line>"
     ```

     IF a designer ended without any reply line, mark the row `failed` with
     `--if` and "ended without a reply".

5. **Go back to 1.** The batch is finished when `next` prints `NONE` and
   `atlas-sheet.py <sheet.md> list designing` prints nothing: go to "The report".

## After a restart

A deploy or a crash restarts the session. Vega's own session is resumed; his
background designers are not, but everything they did is on disk. Pick every
designing row up again, without submitting any job a second time:

1. `python3 "<atlas>/tools/atlas-sheet.py" <sheet.md> recover` prints one JSON line
   per designing or question row of every batch sheet: its agent ID, its
   metadata and `chain.json` files, and `jobs_in_flight`, the jobs submitted
   with no result recorded.
2. For each job in `jobs_in_flight`, `wait_ai_job` it and write the result back
   into its file. **Never submit it again**: it has been paid for.
3. Continue the row's designer through its agent ID. IF that does not work, start
   a new background designer for the row with its request
   (`atlas-sheet.py <sheet.md> request <Task ID>` prints it again) and the usual
   closing text, telling it which files are already made and which job IDs it
   must not submit again (it waits for those), and record its new agent ID.
4. A row whose files show a job started but no job ID recorded cannot be told
   apart from one never submitted: mark it `question` with what you found, and
   report it. Never guess.

Then carry on with the loop from step 3.

**Questions are Vega's to answer, straight away.** A designer's `QUESTION` is
decided by Vega himself (see his skill, "Answering agents' questions"): he
resumes the row's own designer with the decision (or briefs a new one with the
row's request, its recorded files and the answer), marks the row `designing`
with `--if question`, and carries on. A row never waits for the end of the
batch on a question he can answer. IF the answer is for the user to decide, the
row stays `question` and goes into the report.

## Reporting

`report_progress` goes out at the **stages** intake, assign, produce and deliver:

- **assign:** once the sheet is checked and its first rows are being handed over
  (say how many run at once).
- **produce:** one `report_progress` per video as it finishes, in the order they
  finish, one short line:
  brand and number, Task ID, style or language, `<n> of <total> done`, and a
  `FAILED` or `QUESTION` row the same way. Never hold a finished video back
  until the batch ends, and never wait on one to send the next line. In a Lark
  chat (the turn offers `send_lark_media`), the finished render itself goes out
  with `send_lark_media` at the same moment.
- **deliver:** at the close (see "The report").

Do not log outputs yet: logging happens once, at the batch's close, from `tally`.

## Hard rules

- Never produce, fix, or finish a video outside the designer's own skill, and
  never redo a designer's task. A failed or questioning row is recorded and
  left for the user; the batch moves on.
- Never hand a row to a session that did not design it, when a recorded session
  exists: fixes and answers go to the row's own designer.
- Never have more rows designing than the limit (8, across every batch sheet) and
  never claim a row any other way than `next`: it is what keeps the count. Never
  run a render outside `heavy-slot.py`.
- Never end the turn while a row is in production: it stops every background
  designer still working.
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
lines: how many rows finished, failed, and stopped with a question, every row
listed by Task ID order (not the order they finished), the Task IDs of every
row that did not finish, the total credits as the sum of the DONE lines,
and the minutes the batch took from the start time. Nothing about what the
videos show.
