---
name: edit-cost-estimate
description: Estimate run of edit-video-by-comment. Prices each comment from this table alone and calls submit_estimate once. Read only this file and the review JSON.
---

# Edit Cost Estimate

An estimate run prices the comments; it edits nothing. Speed matters: it
must finish in seconds.

- Read the review JSON and this file. Nothing else: no other skill, no
  editable, no video, no frames, no audit, no job.
- Never call `submit_ai_job`, `wait_ai_job`, `host_file` or
  `submit_result`; they are refused here.
- Call `submit_estimate` once, then stop.

IF the JSON fails the check in `edit-video-by-comment.md` section 2, call
`report_error` instead.

## 1. Prices (credits)

Copied from content-maxima `skills/toolkit.md` section 3; the toolkit is
the source and a price change there is made here too.

| Model | Unit | Credits |
|---|---|---|
| `ai-influencer-image` (persona base, 3a) | image | 6.25 |
| `gpt-image-2` 2K (clean-up 3b, element sheet 3c: up to 6 per image) | image | 3.45 |
| `gpt-image-2` 4K (b-roll still 3d) | image | 6.15 |
| `gemini-omni-flash-1.1` (talking-head clip 3e) | clip of 4 / 6 / 8 / 10 s | 41 / 54 / 68 / 81 |
| `heygen-avatar-4` (voice given, 3j) | second | 10 |
| `pixelcut-video-background-removal` (cut-out 3f) | source second | 2.2 |
| `suno-music` (3g) | track | 6.6 |
| `kling-3.0-motion-control` pro (3h) | second | 9.52 |
| `elevenlabs-text-to-speech` (3i) | character | 0.01 |

Free: the render, the audit, `host_file`, timings, captions, supplied
files, and any job that fails or is cancelled.

## 2. By kind of change

Sort each comment into the kinds of `edit-video-content-maxima.md`
section 5 from its `text`, `selection` and `attachments`. A comment may
need more than one line.

| Kind | Lines |
|---|---|
| Stage, supplied material, placement, volume, brand, any `selection` (5a) but a said-again line, timeline cut (5b) | none: 0 |
| `speech` selection with `voice: true` | the clip that says the line: clip + cut-out |
| Visual material, a still | one `gpt-image-2` 4K per still |
| Visual material, elements | one `gpt-image-2` 2K per 6 elements |
| Presenter appearance | `gpt-image-2` 2K ×1, then every clip that shows the presenter: clip + cut-out |
| New presenter | `ai-influencer-image` ×1, `gpt-image-2` 2K ×1, then every clip: clip + cut-out |
| Gesture | the affected clips: clip + cut-out; from a reference video, `kling-3.0-motion-control` for its seconds instead |
| New music | `suno-music` ×1 |
| New words or voice | the affected clips: clip + cut-out; with no presenter, `elevenlabs-text-to-speech` for the new characters |
| Whole video | every clip: clip + cut-out, plus what else it names |
| Out of scope | none: 0, and say it will not be done |

**Clip + cut-out** is, per clip, one `gemini-omni-flash-1.1` clip of its
seconds (or `heygen-avatar-4` for its seconds when the comment gives a
voice) plus `pixelcut-video-background-removal` for the same seconds.

## 3. Seconds

The JSON has no clip list, so take seconds from it:

- "Every clip" is `durationSeconds`.
- "The affected clips" span `time` to `endTime`; without `endTime`, one
  8-second clip around `time`. A said-again line is at least one 8-second
  clip: the clip that says it usually holds more than the line.
- Clip seconds round up to a sum of 4, 6, 8 and 10 (8 by default): 5 s
  is 6, 9 s is 10, 20 s is 10 + 10.

When unsure between two readings, price the dearer one and say so in the
comment's `note`.

## 4. Agent work

`agentCredits` = 30 + 5 per comment. These are starting values, to be
recalibrated against the recorded estimate-versus-actual of past edits.

## 5. Submit

`submit_estimate` with:

- `comments`: one entry per comment, in order:
  `{n, kind, items: [{model, qty, unit, credits}], note}`. `n` is the
  comment's `index`; `credits` is `qty` × the unit price; a free comment
  has `items: []`.
- `agentCredits`: from section 4.
- `summary`: one sentence for the reviewer.

The total is summed from these by the tool; do not add one.
