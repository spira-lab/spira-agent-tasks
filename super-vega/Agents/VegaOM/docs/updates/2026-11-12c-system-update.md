# Super Vega v2.08: system update, 2026-11-12c (package 1.6.4)

The record of Vega's new look. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.08 is live (2026-11-12)

Vega has a new look: silver-white hair, a cream blazer and the orange Spira sweater. Every photo he shares from now on, on request or with an announcement, shows the new Vega.

## What changed

### Assets
- `Agents/VegaOM/assets/Vega photo-01.png`: replaced with the owner's new photo of Vega (2048 × 2048, head and shoulders on a cyan background).
- `Agents/VegaOM/assets/Vega photo-02.png` and `Vega photo-03.png`: removed.

### Skills
- `Agents/VegaOM/skills/generate_my_avatar.md`: the character is now short swept-up silver-white hair, dark eyebrows, no glasses, a cream blazer over an orange sweater with the Spira mark (no lanyard). Each picture passes two references, the Vega photo then the logo, and the prompt and the checks name the new features. When both tries fail, the Vega photo is sent as it is, whatever the topic.
- The hosted-URL list `assets/vega-photos/reference-urls.txt` now keeps each file's size (`<file name> <size> <url>`); a line without the current size is from an older photo and the file is hosted again once.
- `Agents/VegaOM/vega-operations-manager.md`: the own-photo row points to the one Vega photo.

## Not carried over
- Photos of Vega made before this update keep the old look; they stay in `assets/vega-photos/` and only serve to avoid repeating a place or outfit.

## Open
- Check one requested photo and one broadcast preview: the new face and hair, no glasses, the Spira logo on the chest.
