# Super Vega v2.16: system update, 2026-11-14 (package 1.6.13)

The record of fixing re-skit jobs that stalled for an hour and ended with no video. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.16 is live (2026-11-14)

Re-skit jobs no longer stop halfway. A long re-skit now runs through to the finished video instead of ending after about ten minutes of rendering, and a re-skit with a new persona plans every image it needs before it spends anything. Progress checks on a batch work again in the cloud.

## What changed

### Re-skit runs in the foreground
- `task-definition.json`, the `reskit` sub-task, rule (3): Vega hands the one row to the Re-skit designer with the Agent tool and `run_in_background: false`, and his turn waits on it until the designer's DONE, FAILED or QUESTION line. No Atlas wait loop and no `sleep`. FAILED or QUESTION ends the job with `report_error`.
- The worker now lets background sub-agents run up to 1 hour after the main turn ends (it was 10 minutes). Batches still hand designers over in the background; a designer that runs past the hour is still stopped.

### Atlas sheet locks on the cloud disk
- `Agents/AtlasPM/tools/atlas-sheet.py`: `statuses`, `held_slots` and `recover` open their lock files readable (`"a+"`). On the cloud workspace a shared lock needs a readable file, so `wait`, `next` and `slots` failed with EBADF and `recover` silently listed nothing. `recover` now prints `skip <sheet>: <error>` for a sheet it cannot read.

### Re-skit chain check
- `Agents/ReskitVideoDesigner/tools/reskit.py chain-check <materials>` (new, read-only): every `needs` and `{{label}}` names a job in `chain.json`, a `{{label}}` is in that job's `needs`, the needs have no cycle, and every row of the plan's generation table is a job in the chain. Lists every problem and exits non-zero.
- `references/generation-playbook.md`: the `chain.json` example starts with a new persona (`persona_soul` → `persona_edit` → `sheet` → `outfit`, `outfit` needing `sheet`); an existing persona's sheet stays a local `@` file. Every planned row is in the chain before the first submit.
- `skills/reskit-video-designer.md` 7.6 step 4 and 7.7: run `chain-check` before the first submit and again on a resumed session; a chain that cannot pass ends with `FAILED`.

### Why
- A live re-skit (2026-11-14) handed its designer over in the background. Ten minutes after Vega's turn ended, the run closed and the designer died with it, twice. Its `chain.json` had no `sheet` or `outfit` job while every clip needed `outfit`, so the resumed designer had nothing it could submit. `atlas-sheet.py wait` failed with EBADF, so Vega fell back to `sleep` polling.

## Open
- On the next live re-skit: the designer should run past 10 minutes and reach `submit_result`; `atlas-sheet.py <sheet> wait 5` and `recover` in the worker should print statuses with no EBADF. The second early stop of 2026-11-14 (3 minutes after the restart) is not explained yet; if a run ends early again, look for `No 'idle'` in the worker's debug log.
