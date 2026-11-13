# Super Vega v2.02: system update, 2026-11-10 (package 1.4.0)

The record of the Lifestyle Story Carousel Designer install and the upstream studio update that came with it. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

🧭 Super Vega v2.02 is live (2026-11-10)

1. New designer: 📸 Lifestyle Story Carousel Designer. Realistic lifestyle story carousels in 4:5 or 9:16. People shots use Higgsfield Soul + GPT Image 2.5, product shots use Nano Banana 2.1; each carousel is capped at 150 credits. It has its own idea bank, per-client briefs and a no-repeat rule. Ask with "@Vega make N lifestyle carousels for <brand>".
2. Atlas now picks the carousel type: corporate or lifestyle.
3. Re-skit: re-voicing, a dialogue script template, freeze frames for long clips, a two-pass green screen and a background-noise check, plus many lessons from live runs.
4. Echo Explainer: new Practical Walkthrough style.
5. Hermes: the tag ledger now records what each tag is for (videos, carousels or both) and merges duplicate tags.
6. Long sources need an OK first: for clone and re-skit, any source over 30 s is measured and its length and credit estimate are sent to you before that row is built.
7. New brands: Genspark, MenuSifu, Spira (brand facts, logos, working memory).
8. 20 new contact-sheet styles (Style13-32).
9. Updated SOP, workflow map, client ledger and working memory.

## What changed

### New agent
- 📸 **Lifestyle Story Carousel Designer**, `Agents/LifestyleStoryCarouselDesigner/` (Rey's Carousel Skill V2).
  - 5-10 photoreal slides, 4:5 feed (default) or 9:16 story, one person and one place across the slides, the real product UI on the screens, a local grade and text render, a 6-check self-grade and captions.
  - People: Higgsfield Soul + GPT Image 2.5. Objects: Nano Banana 2.1. Capped at 150 credits per row; a quote over the cap comes back as a `QUESTION` for the user.
  - Jobs go through `submit_ai_job` and parallel `wait_ai_job`; `tools/lsc.py record` keeps each job's real credits against the cap.
  - Scriptless: Echo writes nothing for these rows. The designer picks its idea from the client's idea bank, then the 100-idea ledger, never repeating one for that client.
  - Its shared files belong to the session and survive package updates: `angles-log.md`, `references/ideas-ledger.md` and every file under `clients/`.
  - Registered in `CLAUDE.md`, `Agents/VegaOM/docs/vega-roster.json`, `vega-subagent-roster.md` and `Agents/AtlasPM/atlas-designers.json`.

### System changes
- **Vega** (`vega-operations-manager.md`): two carousel styles (corporate is the default, lifestyle only when asked for), a "Lifestyle story carousel requests" section, the source-length check (`tools/vega-source-length.py`, over 30 s needs the requester's OK with a credit estimate) and "Announcing a system update".
- **Batch tool** (`tools/vega-batch.py`): `--style "lifestyle story carousel"` rows start `pending`, with no Echo step.
- **Atlas** (`atlas-project-manager.md`, `atlas-designers.json`, `atlas-sheet.py`): the carousel picker (corporate or lifestyle) and the lifestyle designer's row.
- **Re-skit** (skill, `references/` brand-truth-and-text, field-lessons, file-management, generation-playbook, persona-and-outfits; `scripts/build_edit.py`, `scripts/reskit.py`): re-voicing, the dialogue script template, freeze frames for long clips, the two-pass green screen, the noise-floor check, the audio "clips" mode in `build_edit.py`, and the lessons from live runs. New example: `examples/laptop-overlay/`.
- **Echo** (`echo-styles.md`, `echo-style-cycle.json`): new style `styles/Explainer-PracticalWalkthrough/`.
- **Hermes** (skill, working memory, `hermes-upload.py`): a `For` column in the tag ledger (videos, carousels or both), duplicate tags merged, carousel slides logged in order. Files are still hosted with `host_file`.
- **Iris** (`iris-config.json`) and **DesignerShared** (`designer-lessons.md`, `working-memory.md`): new lessons and settings.
- **Contact sheet**: Style13-32 (20 new styles).

### Brands and docs
- New client assets: Genspark, MenuSifu and Spira (`truth.md`, logos); Test logos; the PartGenie logo. Updated `truth.md` for CookiyLabs, PartGenie and Test.
- New working memory: Genspark, MenuSifu. Updated: CookiyLabs, IASO.
- Updated: `vega-client-ledger.md` (new clients), `sop-requesting-vega.md`, `super-vega-workflow.html`, `vega-dev-notes.md`, `vega-asset-ids.md`, `vega-video-styles.md`, `plans/cloner-reskit-integration-plan.md`.
- New: `docs/plans/2026-11-03-lifestyle-story-carousel-install.md` and this record.
- `task-definition.json`: package 1.4.0; new optional requirements `numpy + pillow` and `playwright (Python)`; opencv now also serves the lifestyle carousel's screen fit and composite.

## Not carried over
Vega doesn't use Lark for documents and generates only through `submit_ai_job`, so these upstream parts were left out:
- The Lark document share, tick and walkthrough tools, and the Lark doc links in the SOP and memory.
- The operations manager's avatar instructions and photos, and the rule that every update message goes out with the manager's photo.
- The `spira_chain.py` change.
- The lifestyle designer's own `scripts/job.py` and `spira_cli.py` (they submitted and waited through the paid CLI).
- Hermes's CLI album upload for carousels.

## Open
- The first live lifestyle carousel run has not happened yet.
- The lifestyle designer's Python dependencies (`playwright`, `numpy`) are optional requirements; a run may need `pip install` first.
- Users who already have the package keep their own copies of the lifestyle designer's `clients/` files, the angles log and the ideas ledger; a package update never overwrites them.
