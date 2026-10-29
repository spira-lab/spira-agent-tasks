# Nova — Working memory — Cookiy Labs

Preferences the user has given for this brand, applied to every task for it without asking
again. One preference per line: what, and when it applies. Written only when the user asks
Nova to remember something. Never added, changed, or removed otherwise.

## Production

How the batch sheet rows for this brand are filled.

- Brand logo: use exactly as provided; never redraw, recolour, or regenerate it. Put in Instructions: "Use the brand logo exactly as provided; never redraw, recolour, or regenerate it."
- Cookiy Earn only: WHEN the user asks for the **Davin** avatar, fill the row with
  - `Avatar image=Agents/NovaOM/client-assets/CookiyLabs/CookiyLabs_avatar_Davin.png`
  - `Avatar voice=elevenlabs tximUd8WQcg4iM1FuJZQ eleven_multilingual_v2`
  - `Style=talking head edited`
- Cookiy Earn Text Agent only: every video (any style: talking head, explainer, podcast, ...) is always **organic** (`--type organic-video`).
## After a video is done

Follow-up assignments Nova makes as soon as Atlas reports the video done.

- Felix (Jekylle's request, 2026-10-22): **only when Hermes finishes uploading** Cookiy videos to Spira, say in the result report that the upload is finished, so Felix and the requester can be told. No tagging happens in this session.

## Other

- When Ken (Jekylle) or Angelica assign Cookiy videos (the owner's rule, 2026-10-26): before building the batch, tell the requester how many Cookiy videos are already made and uploaded (for today, and this week with `nova-output.py count CookiyLabs week <today>`) and how many are still needed for the weekly target of 42, so they only ask for what is left. The weekly count starts from uploaded videos (the owner, 2026-10-25): videos made but not uploaded are tests, not official Cookiy.

- Weekly target (2026-10-15): Cookiy Earn content is **42 videos per week** (Monday to Sunday; original videos logged for Cookiy Labs, repurposes not counted). Nova reports how many are still missing when asked.
- Data: the 16 Cookiy videos made on 2026-10-13 were tests, not official content. They are logged under `Test`, not Cookiy Labs, so they never count in Cookiy reports.

- Use the existing Cookiy Earn logo (CookiyLabs_logo.png) as the Cookiy Labs brand logo for every Cookiy Labs product, including Cookiy Earn Text Agent. User's words: "We can use the same logo from cookiy earn only". Already hosted and local; no re-upload. (from Quill's approved brief)
