---
name: edit-video-by-comment
description: Entry point of the edit-video-by-comment task. Reads the review comment JSON (`video_review`), checks it, keeps a copy, and routes to the editing skill for the task type that made the video. Read first, every session.
---

# Edit Video by Comment

A reviewer watched a finished video in the video editor, paused on
frames, marked areas, and wrote what to change. The editor exported
those comments as one JSON. This task makes the changes in the video
itself, where it was made, and renders it again.

This skill only reads the JSON and decides which editing skill does the
work. It edits nothing.

## 1. Find the review JSON

Take it from the first of these that exists:

1. the task input `review` (the Task contract's "Inputs provided by the
   operator"), a JSON string;
2. a JSON object pasted into the opening message.

IF there is none, call `report_error` saying the review JSON is missing,
and stop.

## 2. Check it

The JSON must have all of these:

- `"kind": "video_review"` and `"schemaVersion": 2`;
- `comments`, an array (it may be empty);
- `taskType`, the first key: the task type that made the video (not
  `null`);
- `source`, an object (not `null`) with `"kind": "agent-job"`: the agent
  task whose result video was reviewed;
- `source.video.path`, the result video's path relative to that task
  type's directory (for content-maxima a file under a `renders/` folder,
  ending in `.mp4`). It must be relative, with no `..` segment.

IF any is missing or different, call `report_error` naming each problem,
and change nothing. A packet whose `taskType` or `source` is `null` was
made on a draft that is not an agent task's result: there is no
workspace to edit it in. A `source.kind` other than `agent-job` is a
source this task cannot edit.

IF `comments` is empty, there is nothing to change: say so in the
final message and stop without editing or rendering.

## 3. Keep a copy

Before any other step, write the JSON exactly as received to

```
reviews/<YYYYMMDD-HHMM>-<video>.json
```

in this task directory, `<video>` being the file name of
`source.video.path` without its extension. It is the record of what
this task was asked.

## 4. What the JSON holds

Every route reads the same packet:

| Field | Meaning |
|---|---|
| `taskType` | the task type that made the video; routing reads it |
| `source.kind` | where the video came from; `agent-job` is the only one |
| `source.taskId` | the task that made the video |
| `source.userId` | the operator that task belongs to |
| `source.title`, `source.name` | that task's title and name, for the report only |
| `source.video.path`, `source.video.publicUrl` | its current result video: path relative to that task type's directory, hosted URL |
| `source.reviewedVideoUrl`, `source.reviewedResultAt` | the video the reviewer actually watched, and when that result was submitted |
| `source.videoChanged` | `true` when that task rendered again after the review draft was built: the comments are about an earlier version than the current one |
| `draftId`, `draftVersion` | the editor draft the comments were written on |
| `canvas` | `{width, height}` of that draft |
| `fps` | the draft's frame rate, which need not be the video's |
| `durationSeconds` | the draft's length |
| `comments[]` | one entry per comment, in time order |

The other `source` fields (`sessionId`, `runId`, `status`, `createdAt`,
`completedAt`, `caption`) are informational: no step reads them, and the
runtime's task records are not readable from here.

Each comment:

| Field | Meaning |
|---|---|
| `id`, `index` | identity; `index` is the `#n` the reviewer saw, from 1 |
| `time` | seconds from the start: the moment the comment is about |
| `frame`, `timecode` | the same moment at the draft's fps, `mm:ss.ff` |
| `region` | `{x, y, width, height}` normalized 0 to 1 on the canvas, top-left origin; `null` means the whole frame |
| `regionPx` | `region` in the draft canvas's pixels |
| `text` | what to change |
| `targets` | the editor elements under the region; on a finished render this is the render clip itself, not the video's own parts |
| `stale`, `madeAgainstVersion` | whether the editor draft changed after the comment |

## 5. Route

| `taskType` | Read and follow |
|---|---|
| `content-maxima` | `skills/edit-video-content-maxima.md` |

IF `taskType` is any other value, call `report_error` saying which task
types this task can edit, and stop. Never route by guessing from other
fields: a video's files are only known by the type that made it.

**The video must be this operator's.** The routed type's directory is a
linked task directory in the file access rules, and its path holds this
operator's directory as `user_<id>`, where `<id>` is the operator's user
id exactly (a `source.userId` of `usr_9a1b` is the directory
`user_usr_9a1b`). IF `source.userId` is set and `user_` + `source.userId`
is not that path segment, the video lives in another operator's
workspace, which this task cannot reach: call `report_error` saying the
edit task has to be created by that operator, and change nothing.

Report the `route` stage `completed`, then open the routed skill and
follow it from its first section. Its stages are `inspect`, `edit` and
`render`.
