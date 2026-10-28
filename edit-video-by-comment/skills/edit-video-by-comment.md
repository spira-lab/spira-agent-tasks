---
name: edit-video-by-comment
description: Entry of the edit-video-by-comment task. Reads the review JSON the opening message names under comments/, checks it, routes to the editing skill for the type that made the video. Read first, every session.
---

# Edit Video by Comment

This skill reads and routes only; it edits nothing.

**Estimate run.** IF the opening message asks for an estimate: read the
review JSON, check it (section 2), then follow only
`skills/edit-cost-estimate.md` and stop. A later message confirming the
estimate starts the edit: begin at section 1 here.

## 1. Read the review JSON

Read the `comments/` file the opening message names. IF no file is
named, the path is not under `comments/` or has a `..` segment, or the
file is missing or not JSON: `report_error` saying which, and stop.

## 2. Check it

Required, else `report_error` naming each problem and change nothing:

- `"kind": "video_review"`, `"schemaVersion": 2`, `comments` an array;
- `taskType` not `null` (a `null` one was made on a plain draft: there is
  no workspace to edit);
- `source` an object with `"kind": "agent-job"`;
- `source.video.path` relative, no `..` (content-maxima: a `.mp4` under a
  `renders/` folder);
- every `attachments[].path` starts with `comments/media/`, has no `..`,
  and names a file that exists here. IF one is missing: `report_error`
  naming it and change nothing — a comment whose media did not arrive
  cannot be honoured.

IF `comments` is empty, say so and stop without editing.

## 3. Fields

| Field | Meaning |
|---|---|
| `taskType` | type that made the video; routing reads it |
| `source.taskId`, `source.userId` | that task, and the operator it belongs to |
| `source.title`, `source.name` | for the report only |
| `source.video.path`, `.publicUrl` | current result: path relative to that type's directory, hosted URL |
| `source.reviewedVideoUrl`, `.reviewedResultAt` | the version the reviewer watched |
| `source.videoChanged` | `true`: the task re-rendered after the review; comments describe an earlier version |
| `canvas`, `fps`, `durationSeconds` | the editor draft's size, frame rate (not the video's), length |
| `comments[]` | in time order |

Other `source` fields are informational. Each comment:

| Field | Meaning |
|---|---|
| `index` | the `#n` the reviewer saw, from 1 |
| `time` | seconds from the start; `frame`/`timecode` are the same at the draft's fps |
| `endTime`, `endTimecode` | optional: the change applies only in `[time, endTime)`. Preserve the original before the start and restore it at the end; verify frames outside as well as inside. `region` is read on the frame at `time` |
| `region` | `{x, y, width, height}` 0 to 1 on the canvas, top-left; `null` = whole frame; `regionPx` in canvas pixels. For a hand-placed image/element it is the exact box, overriding safe-zone, face and grid placement; do not relocate it |
| `point` | optional: a spot the reviewer pinned on the frame at `time`, `{x, y}` 0 to 1 on the canvas, top-left; `pointPx` in canvas pixels. The change is about what is at that spot, not a box around it |
| `scope` | optional: `video` = the whole video (ignore `time`), `frame` = the frame at `time`, `region` = `region` at `time`, `point` = what is at `point` at `time`; absent: `region` decides |
| `text` | what to change |
| `attachments` | optional: media this comment brings, each `{kind, path, mime, durationMs?, width?, height?}` (`kind`: `audio`, `image`, `animated`, or `video` — a timeline edit's clips, or on a plain comment a reference clip its `text` describes). `path` is relative to **this** task directory (`comments/media/<run>/…`) and the file is already there — copy it into the video's materials and reference it; never fetch a URL. It is the reviewer's own file, used exactly as supplied, never regenerated or restyled. A selection's index (`attachmentIndex`, `source.index`) counts in this list from 0 |
| `selection` | optional: what the reviewer picked instead of describing it (a subtitle style, an element, an attachment's role or placement, or `type: "timeline"`: the reviewer's own cut of the video). Its shape is that picker's; read it as data and follow it exactly |
| `cutAnchor` | optional: the change was written on a cut that has not run yet. `{cutNoteId, outputSeconds, source}` — `source.kind: "base"` gives the second of the video as it is now, `source.kind: "clip"` a second into the clip with that `elementId` in the cut; `end`, when present, places `endTime` the same way |
| `targets`, `stale`, `madeAgainstVersion` | about the editor draft, not the video |

A comment's `selection` beats its prose where they describe the same
thing: it is a choice, not a suggestion. `attachments` without a
`selection` means `text` says what to do with them.

**Order.** A packet holds at most one timeline edit. Do the comments
without `cutAnchor` first (their `time` is on the video as it is), then
the timeline edit, then the comments with `cutAnchor` — those were
written on the cut's output, and `source` says where each lands, so never
re-map their `time` yourself.

## 4. Route

| `taskType` | Read and follow |
|---|---|
| `content-maxima` | `skills/edit-video-content-maxima.md` |

Any other value: `report_error` naming the types this task can edit.
Never route by guessing from other fields.

The routed type's linked directory holds this operator as `user_<id>`.
IF `source.userId` is set and `user_` + `source.userId` is not that
segment, the video is another operator's: `report_error` saying that
operator must create the edit task, and change nothing.

Report `route` `completed`, then follow the routed skill from its first
section (stages `inspect`, `edit`, `render`).
