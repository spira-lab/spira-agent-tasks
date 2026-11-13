# Super Vega v2.13: system update, 2026-11-13c (package 1.6.9)

The record of putting rendering back to 4, with 8 videos in design and 4 transcriptions. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.13 is live (2026-11-13)

The team works on up to 8 videos at a time, with 4 rendering and 4 having their timings made at once.

## What changed

### Limits
- `Agents/AtlasPM/docs/atlas-limits.json`: designing 8, rendering 4 (was 2 in v2.12), timing 4. The fallbacks in `atlas-sheet.py` and `heavy-slot.py` match.

### Why
- The owner's decision, same day as v2.12. With 4 render slots, more of the 8 videos in design can render as soon as they are ready instead of waiting for a slot.

### Docs
- Atlas's and Vega's skills, the SOP and its card, the rosters, the workflow page, `rendering.md` and the re-skit designer's skill say 4 rendering.

## Open
- After deploy, watch the worker for a few hours: memory should stay well under the task's limit with 4 renders running (frames sit in `/dev/shm`; if memory runs short, set rendering to 3), and CPU should stay busy without long idle stretches.
