---
name: file-management
description: Layout of this task directory and what may be written where. Apply to every file this task creates, moves or reads.
---

# File Management

Paths are relative to this task directory.

```
CLAUDE.md, skills/   the package: read only
comments/            review JSON files the video editor writes, one per submission
work/<video>/        where wait_ai_job saves, before the file is moved on
results/<video>.mp4  copy of the new render, delivered by submit_result
```

- `comments/` is read only: never edit, move or delete a file there. It is
  the record of what each run was asked.
- Write only under `work/` and `results/`. Create no other folder.
- Never delete a file and never free space. On a size error, retry once,
  then `report_error`.
- `submit_result` files must be inside this directory, so the new render
  is copied to `results/`.
- Files in a linked task directory (the video being edited) follow that
  package's own `skills/file-management.md`.
