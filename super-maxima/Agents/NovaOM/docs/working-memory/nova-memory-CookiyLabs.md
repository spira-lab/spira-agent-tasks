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

- Tag Felix (Jekylle's request; the owner's rule on Lark 2026-10-22): **only when 📤 Hermes finishes uploading** Cookiy videos to Spira, post the update on Lark and tag both **Felix** and the requester (`--mention ou_af846c2c7ad422c12391adf5e0ba550b,<requester id>` with `--text`). When a Cookiy batch is done rendering, tag **only the requester**, not Felix.
- Re-skit request doc (Angelica, 2026-10-29): Angelica shares a Cookiy Lark document with the re-skit video requests as a to-do checklist. When a requested video is done (generated), tick its checkbox in that doc. Doc: https://ljpp9tldvzuk.jp.larksuite.com/wiki/R1Fvw0dTZiehoYktFfXjmYiDpSb ("20 Re-skits Videos Cookiy Earn Text Agent"; items 1-20 = Tasks 33-52, map in Agents/AtlasPM/batches/atlas-batch-2026-10-29-cookiylabsdoc.doc-map.json). Tick with `python3 Agents/NovaOM/tools/nova-doc-tick.py <doc url> <item>` (works as Nova's bot).

## Other

- When Ken (Jekylle) or Angelica assign Cookiy videos (the owner's rule, 2026-10-26): before building the batch, tell them in their thread how many Cookiy videos are already made and uploaded (for today, and this week with `nova-output.py count CookiyLabs week <today>`) and how many are still needed for the weekly target of 42, so they only ask for what is left. The weekly count starts from uploaded videos (the owner, 2026-10-25): videos made but not uploaded are tests, not official Cookiy.

- Weekly target (2026-10-15): Cookiy Earn content is **42 videos per week** (Monday to Sunday; original videos logged for Cookiy Labs, repurposes not counted). A daily reminder checks it and posts on Lark how many are still missing.
- Data: the 16 Cookiy videos made on 2026-10-13 were tests, not official content. They are logged under `Test`, not Cookiy Labs, so they never count in Cookiy reports.

- Use the existing Cookiy Earn logo (CookiyLabs_logo.png) as the Cookiy Labs brand logo for every Cookiy Labs product, including Cookiy Earn Text Agent. User's words: "We can use the same logo from cookiy earn only". Already hosted and local; no re-upload. (from Quill's approved brief)
- Cookiy re-skit thread (Angelica, 2026-10-28): that Lark thread is for Cookiy Text Agent **re-skit** videos only (her correction, same day). When any other request (another brand, or Cookiy talking heads) arrives in that thread, post its confirmation, videos and close in a new message in the group (its own thread), not in the Cookiy thread.
- 2026-11-03: Angelica's doc "8 Cookiy Insights – Reskit Videos" (https://ljpp9tldvzuk.jp.larksuite.com/wiki/Hqetw6NMAismuWkCwp9jPKKApNb) items 1–8 = Tasks 105–112 (Cookiy Labs #30–37, product Cookiy Insights), sheet atlas-batch-2026-11-03-cookiyinsights.md (+ .doc-map.json). Deliver in her thread om_x100b61b11e01c8a4ed08a3930a30548, tick each box, and place each video in the doc under its item.
- 2026-11-03: Cookiy Insights logo: the ledger logo (client-assets/CookiyLabs/CookiyLabs_logo.png) is the Cookiy Earn logo. For Cookiy Insights rows, add to the instructions: "Ignore the brand logo file (it is Cookiy Earn); use cookiy.ai's own Cookiy logo." Also: the owner cut the $7M+ funding claim from the DNA, so add "Do not mention funding or investors" to Cookiy Insights rows (Task 110 showed it, captured from cookiy.ai).
- 2026-11-03: Angelica's doc "8 Cookiy Earn Text Agent – Reskit Videos" (https://ljpp9tldvzuk.jp.larksuite.com/wiki/WdLPwZaL0iLwlbkcX9GjLrTgp1b; Lark thread om_x100b61a0937eecaceda9ac5d222a67e): tick each item when its video is generated (nova-doc-tick.py). Map in Agents/AtlasPM/batches/atlas-batch-2026-11-03-cookiyearnreskit.doc-map.json (items 1,2,3,4,7 = Tasks 179-183; item 6 = Task 185; items 5, 8 pending Angelica).
