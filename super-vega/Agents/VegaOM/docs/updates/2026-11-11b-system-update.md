# Super Vega v2.05: system update, 2026-11-11 (package 1.6.1)

The record of the Spira logo update to Vega's photo. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

👕 Super Vega v2.05 is live (2026-11-11)

Every new photo of Vega now shows the Spira logo on his clothes, whatever he wears that day.

## What changed

### Skills
- `Agents/VegaOM/skills/generate_my_avatar.md`: the company logo `assets/Spira logo.png` is passed as the fourth reference image, after the three Vega photos. The logo (the orange mark and the words "Spira AI") is always printed on the chest of his top, or on the jacket or coat over it; the badge may be left out when the scene cannot have it, the logo never. The prompt names the logo and now ends with "No other readable text." A lost or distorted logo counts as a reason for the one retry, and the check of the result looks for it.
- The hosted URL cache `vega-photos/reference-urls.txt` gets a fourth line for the logo; when only that line is missing, only the logo is hosted.

### Assets
- **New** `Agents/VegaOM/assets/Spira logo.png` (130 × 48): the Spira logo. Never sent on its own.

## Not carried over
- Nothing. The fallback stays as it was: the three Vega photos already wear the Spira sweatshirt.

## Open
- Check that the first photo after the update hosts the logo and adds its line to `reference-urls.txt`.
- Check across a few photos that the logo is readable and not distorted on different outfits.
