# Super Vega v2.03: system update, 2026-11-10 (package 1.5.0)

The record of the parallel-production update. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

🧭 Super Vega v2.03 is live (2026-11-10)

1. Videos are now made in parallel: up to 6 at a time across all batches, instead of one after another. A batch of 5 re-skits should take roughly half the time it used to.
2. At most 2 videos render at the same moment, so the machine stays responsive; the others keep designing meanwhile.
3. When a new request comes in while a batch is running, its videos start as soon as a slot frees up. Each batch is still reported and closed on its own.
4. You still get one progress message per video, now in the order they finish. The final report lists them by task number.
5. After a system restart, the videos in progress pick up where they left off. Generations already paid for are waited for, never made again.
6. Designers working on the same brand at the same time no longer step on each other: personas, outfits and brand facts are shared safely.

## What changed

### Tools
- **Atlas** (`Agents/AtlasPM/tools/atlas-sheet.py`):
  - `next` counts the designing rows across every batch sheet in `Agents/AtlasPM/batches/` and prints `FULL <n>/<cap>` at the cap, claiming nothing.
  - New `slots` (designing and rendering counts against the caps), `recover` (every designing or question row with its agent ID, its metadata and chain files, and the jobs submitted but not finished) and `request <Task ID>` (a row's request, to brief a new designer after a restart).
  - New `Agents/AtlasPM/docs/atlas-limits.json`: `{"designing": 6, "rendering": 2}`.
- **New** `Agents/DesignerShared/tools/heavy-slot.py`: runs a heavy command (render, build, composite, HTML batch render, frame encode) in one of the 2 render slots; exit 75 when every slot stayed busy for 5 minutes.
- **New** `Agents/DesignerShared/tools/brand-lock.py`: runs a command under a brand's lock, or appends a line to a shared file (`truth.md`, `outfits.md`, lessons files) under a lock.
- Locks live in `.locks/` at the top of the package (ignored by `.gitignore`, kept by package updates).

### Skills
- **Vega** (`vega-operations-manager.md`): "One video at a time" became "Parallel slots"; designers are handed over as background sub-agents; new section "After the system is updated: merge `Backup/package-update-*/`".
- **Atlas** (`atlas-project-manager.md`): "How it runs" and the loop rewritten as fill, wait, handle, fill again; never end the turn while a row is in production (background designers end with the run); "Rows left mid-way" split into a restart in this run and rows from an earlier run; new section "After a restart"; the closing text adds the render slot, brand lock, own scratch folder and job IDs written at submission.
- **DesignerShared**: `rendering.md` wraps the render in `heavy-slot.py`; `file-management.md` adds the own scratch folder `<scratchpad>/t<Task ID>/`, the brand-lock rule and the submitted-job entry in the metadata.
- **Re-skit** (skill, `references/` file-management, persona-and-outfits, brand-truth-and-text, generation-playbook): `build_edit.py`, HTML batch renders and composites through `heavy-slot.py`; new persona folders named `<Name>-t<Task ID>`; ledger and truth rows appended through `brand-lock.py`.
- **Cloner** (skill, `clonerfilemanagement.md`) and **Avatar Designer**: the same persona folder naming, brand lock, scratch folder and job IDs at submission.
- Rosters (`vega-roster.json`, `vega-subagent-roster.md`) and `task-definition.json` (package 1.5.0) describe parallel production.

### Engine
- An agent-employee's package update now moves every file it replaces whose content changed to `Backup/package-update-<timestamp>/` before replacing it, instead of deleting it. Files the team writes inside shipped files (lessons, brand truth, outfit ledgers, dev notes, the backup ledger) are no longer lost on an update.

## Not carried over
- Nothing from upstream; this update was made here.

## Open
- After this update lands, look for `Backup/package-update-*/` and merge the team's own lines back (the Vega skill's merge section), then log it in `vega-dev-notes.md`.
- The first live parallel batch (3-4 mixed videos, then 6) has not run yet: watch `atlas-sheet.py slots`, file clashes, credits against serial runs and one progress message per video.
- A restart that lands within the seconds a `submit_ai_job` call is still open makes the engine refuse to resume the run; with 6 designers this window is wider. Watch how often it happens.
