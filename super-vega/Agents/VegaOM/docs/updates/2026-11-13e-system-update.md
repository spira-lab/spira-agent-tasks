# Super Vega v2.15: system update, 2026-11-13e (package 1.6.11)

The record of giving every render a fixed 6 Chromes, with 10 renders and 10 transcriptions at once. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.15 is live (2026-11-13)

Every video now renders on 6 parallel workers, up from 4. Up to 20 videos are in design, 10 rendering and 10 having their timings made at once.

## What changed

### Rendering
- `Agents/DesignerShared/tools/render/profile.js`: every render opens 6 Chromes, whatever else is running. v2.14 split the cores among the renders running when one started (2 to 16 Chromes); before that it was at most 4. A `[workers]` / `--workers` argument still overrides it.

### Limits
- `Agents/AtlasPM/docs/atlas-limits.json` holds fixed numbers again: `{"designing": 20, "rendering": 10, "timing": 10}` (v2.14 had one render and one timing slot per 2 cores, 16 / 16 on 32 cores). `atlas-sheet.py`, `heavy-slot.py` and `timing_slot.py` read them as they are and fall back to the same numbers.

### Why
- The owner's decision, rendering and timing 10 included. Past 6 to 8 Chromes a render gains little: each Chrome has to start, load the stage and encode its own segment, and a lone render with 16 crowded out the renders and designers that came after it.

## Open
- After deploy, watch a full batch on the dev worker: render logs should say `across 6 workers`. With all 10 render slots busy that is 60 Chromes and 10 x264 encoders; if renders start failing or Playwright times out, lower `rendering` in `atlas-limits.json`.
