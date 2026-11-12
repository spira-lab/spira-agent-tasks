# Super Vega v2.11: system update, 2026-11-13 (package 1.6.7)

The record of opening the limits: 8 videos in design, 4 rendering and 4 transcribing at once. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.11 is live (2026-11-13)

The team now works on up to 8 videos at a time, with 4 rendering and 4 having their timings made at once. While some videos wait for their clips, others render, so videos keep coming out instead of in waves.

## What changed

### Limits
- `Agents/AtlasPM/docs/atlas-limits.json`: designing 8 (was 4), rendering 4 (was 2), timing 4 (was 2). The tools' fallbacks (`atlas-sheet.py`, `heavy-slot.py`, `timing_slot.py`) match.

### Why
- With 4 in design the videos moved in step: about half an hour all waiting on generation (worker CPU near 0), then half an hour all transcribing and rendering (CPU at 100). More videos at once lets the waiting and the heavy steps overlap; the machine shares the CPU between them.
- Renders and Whisper runs still take a slot each, so the memory they use stays bounded.

### Docs
- Atlas's and Vega's skills, the SOP and its card, the rosters, the workflow page and the designer skills say up to 8 at a time, 4 rendering and 4 transcribing.

## Open
- After deploy, watch the worker for a few hours: CPU should stay busy without long idle stretches, and memory should stay well under the task's limit with 4 renders running.
