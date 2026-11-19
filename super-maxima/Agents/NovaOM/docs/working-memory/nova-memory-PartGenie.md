# Nova — Working memory — PartGenie

Preferences the user has given for this brand, applied to every task for it without asking
again. One preference per line: what, and when it applies. Written only when the user asks
Nova to remember something. Never added, changed, or removed otherwise.

## Production

How the batch sheet rows for this brand are filled.

- Explainer rows (the owner's word, 2026-10-24): the narrator is **Brian**. Put in Instructions: "Use this voice: elevenlabs nPczCjzI2devNBz1zQrb eleven_multilingual_v2 (Brian, PartGenie's narrator)."

## After a video is done

Follow-up assignments Nova makes as soon as Atlas reports the video done.

- PartGenie re-skits from Jekylle's doc "PartGenie - 20 videos to re-skit" (https://ljpp9tldvzuk.jp.larksuite.com/wiki/NcxUwS3cGiWToqkh7rNjW0KKpDc; Tasks 405-424 = sets 1-20; Jekylle's request, 2026-10-28): put each finished video into that doc, under its own numbered request section (after that set's instruction), as a playable video with a one-line `Task NNN · <set title>` caption. A helper agent does it (lark-cli docs +media-insert --as user, then block_move_after), a few videos at a time as they finish; never overwrite the doc and never touch the other sets' text.
- Re-skit test doc (Angelica, 2026-10-30): Angelica shares PartGenie re-skit test requests as a to-do checklist in "Re skit PartGenie" (https://ljpp9tldvzuk.jp.larksuite.com/wiki/IS60wAV5FiylRNktgemjhrEmpig). When a requested video is done (generated), tick its checkbox: `python3 Agents/NovaOM/tools/nova-doc-tick.py <doc url> <item>`. Item to task map in Agents/AtlasPM/batches/atlas-batch-2026-10-30-partgeniedoc.doc-map.json (item 1 = Task 82).
- Re-skit doc "5 PartGenie – Reskit Videos" (Angelica, 2026-11-02; https://ljpp9tldvzuk.jp.larksuite.com/wiki/QNtdwbWSZiOb8Pk39UfjMl1Upzd): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-02-partgeniereskit5.doc-map.json (items 1-5 = Tasks 93-97).
- Re-skit doc "5 talking head videos | 5 reaction re skit videos" (Angelica, 2026-11-06; https://ljpp9tldvzuk.jp.larksuite.com/wiki/V1Riwr29kixolOk3sTKjyiampIf): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-06-partgeniereskitdoc2.doc-map.json (items 1,2,4,6-10 = Tasks 253-260; item 3 = Task 261, item 5 = Task 262, both trimmed to 25 s).
- Re-skit doc "5 PartGenie re skit videos" (Angelica, 2026-11-09; https://ljpp9tldvzuk.jp.larksuite.com/wiki/JUotwhQzUiQPD1kTmghj5q5xpLg): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-09-partgeniereskitdoc3.doc-map.json (items 1-5 = Tasks 289-293).
- Re-skit doc "For PartGenie Testing Videos - PartGenie – Reskit Videos" (new teammate ou_56b8e568be425f47efa3d3a0f565fb72, 2026-11-10; https://ljpp9tldvzuk.jp.larksuite.com/wiki/ZuifwKX8OiLwn3knmQDjNasupRc): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-10-partgeniereskitdoc4.doc-map.json (item 1 = Task 327).
- Re-skit doc "4 PartGenie - Reskit videos" (Angelica, 2026-11-10; https://ljpp9tldvzuk.jp.larksuite.com/wiki/JRrtwkpxViXEkikdTW4jNkdPpfb): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-10-partgeniereskitdoc5.doc-map.json (items 1-4 = Tasks 340-343). These test videos never mention PartGenie or its tools.
- Re-skit doc "5 PartGenie - Reskit videos" (Angelica, 2026-11-16; https://ljpp9tldvzuk.jp.larksuite.com/wiki/IMZnwNFOMiXDGfkOhLhj2U2qpAe): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-16-partgeniereskitdoc6.doc-map.json (items 1-5 = Tasks 512-516, item 6 = Task 522). Her standing instructions for this doc: change all personas; new background music inspired by the original; if featuring PartGenie, organic and not salesy; no PartGenie end cards.
- Re-skit doc "3 PartGenie - Reskit videos" (Angelica, 2026-11-17; https://ljpp9tldvzuk.jp.larksuite.com/wiki/LSLowzu7miWhbekfKcHjFHdDp6g): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-17-partgeniereskitdoc7.doc-map.json (items 1-3 = Tasks 589-591). Her standing instructions for this doc: new background music inspired by the original; if featuring PartGenie, organic and not salesy; no PartGenie end cards.
- Re-skit doc "2 PartGenie Re-skit Videos" (teammate ou_56b8, 2026-11-18; https://ljpp9tldvzuk.jp.larksuite.com/wiki/PgsawUoMWiFw45k7zMqjxJc0ppe): tick each item's checkbox when its video is generated, with the same tool. Map in Agents/AtlasPM/batches/atlas-batch-2026-11-18-partgeniereskitdoc8.doc-map.json (items 1-2 = Tasks 654-655). Standing instructions: new background music inspired by the original; if featuring PartGenie, organic and not salesy; no PartGenie end cards.
- Tag request (teammate ou_56b8e568be425f47efa3d3a0f565fb72, 2026-11-18 09:29, "Can you tag me on Angelica's Partgenie thread videos and carousels this week?"): until Sun 2026-11-22, after every PartGenie video or carousel delivered in one of Angelica's threads, reply in that thread with `--mention ou_56b8e568be425f47efa3d3a0f565fb72` (nova-deliver.py has no mention option, so it is a short follow-up reply). Drop this line after 2026-11-22.

## Other

- 2026-11-03: NO.044 doc had no edit access for the bot or the owner; the owner asked for a copy instead: https://ljpp9tldvzuk.jp.larksuite.com/docx/OX3RdPrfroOLwvxP7aQj6SX7pUb (all 5 boxes ticked, owner full access, group view). Use the copy from now on.
