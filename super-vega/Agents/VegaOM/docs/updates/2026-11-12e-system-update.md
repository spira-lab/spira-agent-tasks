# Super Vega v2.10: system update, 2026-11-12e (package 1.6.6)

The record of the 2 + 2 slots: 2 renders and 2 transcriptions at once, 4 videos in design. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.10 is live (2026-11-12)

Videos now come out at a steady pace instead of several at once after a long wait. The team works on up to 4 videos at a time, with 2 rendering and 2 having their timings made at once, and making the timings is faster.

## What changed

### Platform (not in the package)
- `apps/cc-engine/Dockerfile`: faster-whisper is installed next to openai-whisper, with the `medium.en` and `medium` models (int8) preloaded, so `make-timings.py` uses faster-whisper instead of falling back to the slower Whisper command line, and no first run downloads a model.

### Tools
- New `Agents/DesignerShared/tools/timing_slot.py`: at most 2 Whisper transcriptions at once (`timing` in `atlas-limits.json`), each at 8 threads. A tool waits up to 5 minutes for a slot, then exits 75 with "run the same line again".
- `make-timings.py` (one slot for all its files), `ClonerVideoDesigner/tools/lyrics_check.py`, `ClonerVideoDesigner/tools/music_cut.py` and `QuillBW/tools/quill-video.py` take a timing slot around their transcription and run at 8 threads.
- `Agents/AtlasPM/tools/atlas-sheet.py slots`: also shows `timing`, `timing_cap` and who holds each timing slot.

### Limits
- `Agents/AtlasPM/docs/atlas-limits.json`: designing 4 (was 6), rendering 2, timing 2 (new).

### Docs
- Atlas's and Vega's skills, the SOP, the rosters, the workflow page and the designer skills say up to 4 at a time, 2 rendering and 2 transcribing; `rendering.md`, `stage-canvas-html.md` and `toolkit.md` say Whisper tools take a timing slot themselves (never inside `heavy-slot.py`) and exit 75 means run the same line again.

## Not carried over
- Starts are not staggered: up to 4 videos still start together; the timing slots queue their transcriptions.

## Open
- After deploy, watch 1 to 2 hours of a batch: videos should land at a steady pace, and `make-timings.py` should print `[faster-whisper]`.
