---
name: edit-video-by-comment
description: Entry of the edit-video-by-comment task. Reads the review JSON the opening message names under comments/, checks it, routes to the editing skill for the type that made the video. Read first, every session.
---

# Edit Video by Comment

This skill reads and routes only; it edits nothing.

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
  `renders/` folder).

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
| `region` | `{x, y, width, height}` 0 to 1 on the canvas, top-left; `null` = whole frame; `regionPx` in canvas pixels |
| `text` | what to change |
| `targets`, `stale`, `madeAgainstVersion` | about the editor draft, not the video |

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
