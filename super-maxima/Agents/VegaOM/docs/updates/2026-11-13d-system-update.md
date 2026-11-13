# Super Vega v2.14: system update, 2026-11-13d (package 1.6.10)

The record of letting the parallel limits follow the machine and use all of it. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.14 is live (2026-11-13)

The team now works on as many videos at once as the machine can take. On today's 32-core worker that is up to 20 in design, 16 rendering and 16 having their timings made at once, and a render that runs alone uses the whole machine.

## What changed

### Limits
- `Agents/AtlasPM/docs/atlas-limits.json` holds `{"designing": 20, "cpus_per_render": 2, "cpus_per_timing": 2}`: designing is a fixed 20 (was 8); rendering and transcribing are the worker's cores divided by their number, at least 2. `heavy-slot.py` and `timing_slot.py` count the cores themselves.
- 32 cores (dev): 20 designing, 16 rendering, 16 transcribing (was 8 / 4 / 4). 16 cores (prod): 20 / 8 / 8. Designing 20 is the owner's call.
- `render/profile.js`: a render splits the cores with the renders running when it starts (the `.who` files of `heavy-slot.py`): cores ÷ (2 × renders running) Chromes, 2 to 16 (was at most 4). On 32 cores a lone render opens 16 Chromes, the second 8, and so on.

### Why
- The owner's decision: CPU is the only limit, memory is not. Batches on the 32-core dev worker averaged about 50% CPU: 4 renders × at most 4 Chromes used half the cores at best, a lone render could not use the idle ones, and with 8 in design the heavy steps of the videos seldom overlapped.

### Docs
- Atlas's and Vega's skills, the SOP and its card, the rosters, the workflow page, `rendering.md` (which still said 2 timing slots) and the designers' skills describe the limits as following the cores.

## Open
- After deploy, watch the dev worker during a full batch: CPU should stay near 100% while any video renders or transcribes. If CPU still has idle stretches with 20 in design, raise `designing`; if model calls or AI jobs start failing on rate limits, lower it.
