# Super Vega v2: system update, 2026-10-24

The full record of the 4:00–5:00 AM PHT update window (1–2 PM PDT, Oct 23) and the follow-ups
the owner asked for that day. Kept for reference: Vega reads it when anyone asks what changed. The owner named this update **v2** (2026-10-24); later updates are numbered from it (2026-10-27 = v2.01, the owner's name).
The team announcement covered only the items marked **(team)**.

## New agents
- **(team)** 🧬 **Cloner** installed (`Agents/ClonerVideoDesigner/`): rebuilds a source video's format for a brand with new lines, voice, persona and shots.
- **(team)** 🎭 **Re-skit** installed (`Agents/ReskitVideoDesigner/`): keeps a trend's motion and voices, recasts the person, changes the meaning.
- Both adapted to the house layout and shared rules: shared renderer and stage, Scribe timings, the shared chunker pace (4.9–5.2 syllables/s, Omni clip length − 1 s), Omni Flash 1.1 only, one Spira source-understanding workflow per run.
- The owner's rules for both:
  - no approval gates;
  - never the source creator's face, always recast;
  - Re-skit always pitch-adjusts kept source audio;
  - vocals in music only when the video needs them; the agent decides, never asks;
  - the agent captures UI screenshots from the brand's site, or makes believable ones; provided material always wins;
  - Vega supplies the brand DNA.
- Wan 3.0 approved for shared use.
- New batch sheet column **Source video**; `vega-batch.py --source` for styles `clone` and `re-skit`; Brand DNA and the **brand website** (new Website column in the client ledger) added to the instructions automatically, for clone and re-skit only.
- Atlas routes `clone` and `re-skit`. No cap of their own: they run in the usual 6 designing / 2 rendering. A proposed cap of 2 was removed by the owner.
- Brand files kept in `Agents/VegaOM/client-assets/<Brand>/`, outside Project, so backups never clear them:
  - `personas/`;
  - `brand/` (Re-skit's truth, outfits, screenshots);
  - `voice.md` (the Cloner's brand voice).
- The Cloner picks an off-camera voice from `Agents/DesignerShared/docs/voice-list.md` (8 tested ElevenLabs voices) when the brand has none, and saves it as the brand's voice.
- The Cloner's music tool: librosa and soundfile installed in `Agents/ClonerVideoDesigner/.music-venv` (the owner's OK), tested.
- Wan jobs wait up to 30 minutes (`spira-jobs.py wait --timeout 30m`); other jobs keep 10.
- Shared lessons file `Agents/DesignerShared/docs/designer-lessons.md`; only Vega writes to it.
- The Avatar Designer is the one source of personas and character sheets.
- Vega's roster `Agents/VegaOM/docs/vega-roster.json` lists every agent (15, Repurpose included as decommissioned); the report reads it.
- Not yet run on a real video: live tests come in dogfooding.

## Removed
- **(team)** **Repurpose** removed from every skill, tool, template and the report (the owner: never used). Folder moved to `Agents/DesignerShared/retired/repurpose/`. Old sheets and records read the same. It stays on the roster and the report as **decommissioned** (the owner's wish).

## Prices and credits
- Toolkit prices synced to Spira's live list, checked against real job charges:
  - Omni Flash 1.1: 41 / 54 / 68 / 81 for 4 / 6 / 8 / 10 s, the same at 720p and 1080p, and 108 with a video input;
  - GPT Image 2: 4 / 5 / 8;
  - Soul 7, Suno 7;
  - Wan 3.0: 6.18/s at 720p, 12.35/s at 1080p;
  - ElevenLabs sound effects: 12.
- Designers record each job's exact charge from `spira --json ai jobs status <id>` (`data.credits`), not from the price table.
- The chunker uses the new Omni prices; clip lengths unchanged on 12 real scripts.
- Past credits are not recounted (the owner's call). The top-up ask stays at 5,000.

## Workflow rules
- Files are named by Task ID (`NN` = Task ID) in the shared file rules and Atlas, matching the real names.
- IASO's angle check avoids only the angles of its last 100 scripts.
- Lark: one short line per finished video; credits go in the batch close.
- **System backup before every major update** (the owner's rule). Two taken today: after the install, and before removing repurpose (`Backup/backup-ledger.md`).

## Report (https://claude.ai/artifact/G6JCmYzX6z6JPazP93iBqJ)
- **(team)** **Agents view:**
  - the **Agents** button (all agents);
  - "Agents in the system", with **Managers, Helpers and Designers** as buttons that open their agents.
- The **Skills used** page.
- The Podcast Designer is marked **not ready**; Repurpose shows as **decommissioned**.
- Repurpose removed from the cards; today's dev notes added.

## Docs
- Workflow schematic (https://claude.ai/artifact/Ap42wEPiN7KsxEa3tasVvd) updated: six designer styles, the Source video column, the new agents, Repurpose decommissioned, the backup and credits rules, and the folder tree.
- **(team)** **SOP "How to Send a Request to Vega"** (https://ljpp9tldvzuk.jp.larksuite.com/docx/W5HSdeahGoZT2txVhcfjFj9ep8g), with section 2b on what a clone or re-skit request needs, and 4 infographics (sources in `Agents/VegaOM/docs/sop-art/`).
- Vega's skill, Atlas's skill, the video styles list and the Lark notes cover clone, re-skit, avatar images and the rules above.
- Dev notes: one line per change.

## Still open
- Live clone and re-skit tests (dogfooding), then the team announcement for live use.
- Podcast is not ready on the report only; Atlas still accepts podcast rows unless the owner says otherwise.
