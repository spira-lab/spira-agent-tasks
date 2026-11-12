# Super Vega v2.06: system update, 2026-11-12 (package 1.6.2)

The record of how finished work reaches a Lark chat. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

📬 Super Vega v2.06 is live (2026-11-12)

Each video now shows up in the conversation the moment it is finished, no need to ask for it. When the whole batch is done, Vega posts one closing message saying so, with every video's status and credits.

## What changed

### Skills
- `Agents/VegaOM/vega-operations-manager.md`: in a Lark chat (the turn offers `send_lark_media`), each finished video is sent with `send_lark_media` right away (a carousel its contact sheet and slides, an avatar its PNG). "Delivering the result" now has two cases: in a task, `submit_result` as before; in a Lark chat, the last reply is the delivery, opening with one line saying the whole batch is finished, then the `report` lines, then any FAILED rows or open questions, with links only for videos that were not sent. Workflow steps 6 and 7 and avatar step 4 say the same.
- `Agents/AtlasPM/atlas-project-manager.md`: the "produce" report line notes that in a Lark chat the render goes out with `send_lark_media` at the same moment.

### Shared employee rules
- The digital employee's own rules map the task steps to chat: a `report_progress` for a finished item becomes `send_lark_media` of that item, and `submit_result` becomes the closing "all done" reply. Before, both steps were simply skipped in chat, so nothing arrived until someone asked.

## Not carried over
- Nothing. Agent-job tasks deliver exactly as before.

## Open
- Check on a live batch of 2 or more videos in Lark that each video appears as it finishes, and that the last reply opens with "all done" and does not repeat links for videos already sent.
