# Super Vega v2.07: system update, 2026-11-12b (package 1.6.3)

The record of how finished videos and carousels reach Spira's Social Post Assets library. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

🗂️ Super Vega v2.07 is live (2026-11-12)

Uploaded videos and carousels now appear in Social Post Assets under their tag. Each video becomes one video asset and each carousel one album with its slides in order, ready for the team to pick up and post.

## What changed

### Tools
- New worker tool `upload_social_post_asset`: uploads one video, or a carousel's slides in order as one album, into Social Post Assets under a Tag ID and returns the asset ID. It needs the operator's Spira account to have Admin access and the Social Post Assets manage permission; without it the upload fails with `FORBIDDEN`. An unknown Tag ID fails with `Tag not found.`.
- `Agents/HermesMU/tools/hermes-upload.py`: `plan` now gives one item per video and one per carousel (slides sorted by number), and `record` logs the asset ID, asset type, files and sizes per item. An item is skipped only when the same files, sizes and Tag ID were already uploaded.

### Skills
- `Agents/HermesMU/hermes-media-uploader.md`: Hermes uploads with `upload_social_post_asset` instead of `host_file` (which only hosted a link and filed nothing), stops with `FAILED` on a permission or tag error, and lists each item's asset ID in his `UPLOADED` reply.
- `Agents/HermesMU/docs/hermes-working-memory.md`: the Tag ID is what the upload uses; Spira refuses one that no longer exists.
- `Agents/VegaOM/vega-operations-manager.md` and `docs/vega-subagent-roster.md`: Hermes's description and reply match what he now does.

## Not carried over
- Entries in `hermes-upload-log.json` from before this update (one per file, no asset ID) are not counted as uploaded: those videos and carousels are uploaded once more, this time into Social Post Assets.

## Open
- Check on a live batch with 1 video and 1 carousel that both appear under their tag in Social Post Assets, the carousel's slides in order, and that an account without the permission gets `FAILED` with the reason.
