# Vega — Working memory — IASO

Preferences the user has given for this brand, applied to every task for it without asking
again. One preference per line: what, and when it applies. Written only when the user asks
Vega to remember something. Never added, changed, or removed otherwise.

## Production

How the batch sheet rows for this brand are filled.

- Style: `explainer`, always, for every IASO video.
- No avatar: never fill Avatar image or Avatar voice for IASO.
- Instructions, on every IASO row: "Use this voice: elevenlabs cgSgspJ2msm6clMCkdW9 eleven_v3. Transitions are always effortful and purposeful; elements enter and exit dynamically, nothing simply appears or disappears. Never show the IASO logo or the word IASO on screen. Background music tone: scientific, not sad."
- Style sheets (the owner's OK, 2026-10-22): every IASO row gets a style reference from `Agents/VegaOM/client-assets/IASO/style-sheets/` (IASO_Style1.jpg … IASO_StyleN.jpg, all files in the folder), rotating through them across rows and batches (pass with `--style-ref` or set each row's `Style ref`). New sheets added to the folder join the rotation.
- Translation requests (an IASO video in another language): same voice; put the language in Instructions.

## After a video is done

Follow-up assignments Vega makes as soon as Atlas reports the video done.

## Other
