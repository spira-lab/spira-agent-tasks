# Super Vega v2.04: system update, 2026-11-11 (package 1.6.0)

The record of the Vega photo update. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

📸 Super Vega v2.04 is live (2026-11-11)

1. Vega now has a face. Ask Vega for a photo in any group or private chat and you get a new picture of the day, showing the mood of the moment.
2. Every message Vega sends to all groups now comes with a photo of Vega.

## What changed

### Skills
- **New** `Agents/VegaOM/skills/generate_my_avatar.md`: Vega's own photo. One GPT Image 2 edit (`9:16`, `1K`, about 4 credits) from the three Vega photos, with a new outfit, place and expression each time to show the mood of the day; at most one retry; if both tries fail, one of the three photos is sent as it is. Sent with `send_lark_media` when someone asks; attached to every `broadcast_lark_message` preview. No Atlas, no output log, no dev-note line for a photo.
- **Vega** (`vega-operations-manager.md`): the file table lists the new skill; "Announcing a system update" makes the photo before the preview and attaches it, and every other broadcast gets one too.
- **Vega is "he"**, matching the photos: every skill, doc and tool that spoke of Vega as "she" now says "he" (Vega's skill, Atlas, Quill, Iris, the shared file-management skill, the SOP, rosters and Vega's docs and tools). Echo, Iris, Jani and the personas are unchanged.

### Assets
- **New** `Agents/VegaOM/assets/Vega photo-01.png`, `Vega photo-02.png`, `Vega photo-03.png` (2048 × 2048): the references for the Vega character.
- Generated photos and the cache of the references' hosted URLs live in `Agents/VegaOM/assets/vega-photos/` (ignored by `.gitignore`, kept by package updates).

## Not carried over
- Taken from Nova's `generate_my_avatar` skill, rewritten for the Vega character and the employee's tools (`submit_ai_job`, `wait_ai_job`, `host_file`, `send_lark_media`, `broadcast_lark_message`) instead of the `spira` CLI and `lark-nova.py`.

## Open
- The first photo hosts the three references and writes `vega-photos/reference-urls.txt`; check it is written and reused.
- Check that the generated character keeps the face, curly hair and glasses across all three references.
