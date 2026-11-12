# Super Vega v2.12: system update, 2026-11-13b (package 1.6.8)

The record of putting rendering back to 2 while keeping 8 videos in design and 4 transcriptions. Vega reads it when anyone asks what changed, or when told to announce the update. Only the  section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.12 is live (2026-11-13)

The team works on up to 8 videos at a time, with 2 rendering and 4 having their timings made at once.

## What changed

### Limits
- : designing 8, rendering 2 (was 4 in v2.11), timing 4. The fallbacks in  and  match.

### Why
- The owner's decision, same day as v2.11. A render holds its frames in memory, so 2 at a time keeps the worker's memory safe; with 8 videos in design and 4 timing slots, the waiting and the transcriptions still overlap with the renders.

### Docs
- Atlas's and Vega's skills, the SOP and its card, the rosters, the workflow page and  say 2 rendering.

## Open
- After deploy, watch the worker for a few hours: CPU should stay busy without long idle stretches, and renders should not queue so long that videos wait on them for most of their time.
