# Nova — Lark video docs (standard format)

When the user asks Nova to put finished videos into a Lark doc ("compile them to a Lark doc", "put these videos in a doc"), Nova assigns a helper agent and gives it this format. Nova never builds the doc herself. The format was set by the user on 2026-10-13/14.

## Format

- **Title:** the one the user gives. If they give none, use a short name for the set, e.g. `IASO - Myeloma & CAR-T Explainers`.
- **No commentary:** no intro, no notes, no "listen for" lines, only the videos and their titles. Add QA notes only when the user asks for them.
- **Order:** by video number (Task ID), lowest first.
- **3 columns on every row,** with each video in its own cell and the title above the video. A short last row still has 3 columns: its unused cells stay empty, so every video shows at the same size.
- **Titles are body text** (a plain paragraph), never a heading: `NN · <short title>`, e.g. `17 · CAR-T side effects: CRS & ICANS`.
- **Full-quality files.** Lark docs accepted files up to ~85 MB. Compress a scratchpad copy only when Lark refuses a file, and say so under that video.
- Create the doc as the **user** (`--as user`), in the user's own space.

## How it's built (lark-cli 1.0.81, `--as user`)

1. **Rows:** one `<grid>` per row, holding 3 `<column width-ratio="0.333333">` cells. Each cell starts with `<p>NN · Title</p>`, and an empty cell is `<column width-ratio="0.333333"><p></p></column>`. Create the doc with all rows at once: `docs +create --content '<title>…</title><grid>…</grid>…'`. (A grid with 2 columns gets resized to 0.5 each, which makes those videos wider; always use 3.)
2. **IDs:** `docs +fetch --detail with-ids` once, to get each cell's title `<p>` id.
3. **Videos, one at a time:** `docs +media-insert --doc <id> --file <path> --type file --file-view preview` makes an inline-playing `<figure view-type="Preview">` at the end of the doc. Move it into its cell with `docs +update --command block_move_after --block-id <cell title p id> --src-block-ids <figure block_id>`. Retry on HTTP 429 with a pause. Read the JSON from stdout only, because progress messages go to stderr.
4. **Fixes in place:** `block_replace` (e.g. a heading to `<p>`), `block_insert_after`, `block_move_after`, `block_delete`. Never re-upload a video that is already in the doc.
5. **Verify:** fetch the doc once and check the row and cell count, that every video is in the right cell, and that the titles are body text.

## Docs made so far

| Doc | Link | Videos |
|---|---|---|
| Cookiy Earn Text Agent - QA | https://ljpp9tldvzuk.jp.larksuite.com/docx/BInUd90MBog5tQx7MwbjraMmpUb | 05–16 (brought up to this standard on 2026-10-14) |
| IASO - Myeloma & CAR-T Explainers | https://ljpp9tldvzuk.jp.larksuite.com/docx/Y5SVdss0qoHUmKxokpmj4rBupJg | 17–36 |
| Gemini Omni Test - Results & Findings | https://ljpp9tldvzuk.jp.larksuite.com/docx/CdmCdaDKXoShcyxfKBJjMQJlpOf | Test 37–38 (a report: text + videos) |
| Cookiy Earn Text Agent - 2026-10-15 | https://ljpp9tldvzuk.jp.larksuite.com/docx/K3IwdJRoro3bzox7E5Ijgp9zpeh | 41–46 |
| Cookiy Earn Text Agent - Professions (78–85) | https://ljpp9tldvzuk.jp.larksuite.com/docx/R1yodl07DoZoelx9GvjjE7kjpSf | 78–85 (replaced 70–77 on 2026-10-15) |
| Cookiy Earn Text Agent - Experts (150–158) | https://ljpp9tldvzuk.jp.larksuite.com/docx/VieKdGWCWoQ2vMxKA14jPl7MpMc | 150–158 |
| PartGenie - Videos #01–10 | https://ljpp9tldvzuk.jp.larksuite.com/docx/ULcDdWeaBoNusNxn8kOj3Unrpkb | PartGenie #01–10 (Tasks 263–265, 270–276) |
| MyClaw - Re-skit Videos | https://ljpp9tldvzuk.jp.larksuite.com/docx/XX7od7CpEoWdhnxXH0QjUlwrpJe | 653, 656, 658, 657 (caption + hashtags under each video; for Ryan, 2026-11-18; made as bot because user login was missing; row 1 full, row 2 holds 657 with 2 empty cells) |
