# Plan: install the Carousel Designer (2026-10-27)

Requested by the owner on Lark (DM, 2026-10-27 01:41). Source skill: `~/Desktop/Agent incubator/Corporate carousel/`, which holds:
- `SKILL.md`;
- 6 reference docs;
- 7 scripts;
- an empty run history.

## What the skill does today
- **Input:** one website link, plus an optional angle.
- **Output:** 4–7 slides at 1080×1350 (JPEG), a contact sheet, `notes.md` with captions, and an editable `slides.html`.
- **How it works:**
  - Scrapes the site for copy, fonts, colours and product photos.
  - Writes a design brief and the slide copy.
  - Makes images with GPT Image 2 through Spira, referencing real product photos when they exist.
  - Lays out the slides in HTML and renders them with headless Chrome.
- **Memory:**
  - Alternates dark and light themes between runs.
  - Keeps the last 30 runs so that subject, angle and cover headline never repeat.
- **Cost:** about 50 credits per carousel, the skill's own estimate.
- **Prerequisites (all checked and present on this Mac):**
  - Chrome;
  - Python with PIL, numpy and scipy;
  - the Spira CLI.

## What has to change so it works in our system
1. **Backup first.** Zip `Agents/` and `Lark connect/` into `Backup/`, and log it in the backup ledger.
2. **Install as a designer.** Create the designer's folder (renamed later the same day to `Agents/CorporateCarouselDesigner/`) with:
   - its skill (now `skills/corporate-carousel-designer.md`);
   - `references/` for the 6 docs;
   - `tools/` for the 7 scripts;
   - `state/`.
   The path inside the skill now points to our folder instead of the Desktop.
3. **Inputs come from the batch row.** The designer receives:
   - the Task ID and brand number;
   - the brand and product;
   - the topic angle (written by Echo);
   - the product website (from the ledger's Website column).
   It does not need a script, music, logo or style reference.
4. **The topic angle is written by Echo and never repeats.**
   - A carousel row needs a "script" before it runs, and for this style the script is just the topic angle (one line, plus an optional one-line direction).
   - Echo writes it and checks it with `echo-similar.py`, then records it.
   - Each brand gets its own carousel angle record, separate from its video angles. Video angles therefore don't block carousel angles, and carousel angles never repeat.
   - The skill's own 30-run memory stays in place to vary the look (theme, layout, fonts).
5. **Website handover.** Today the ledger website is passed only to Cloner and Re-skit. Carousel would be the third.
6. **Sheet and batch tools.**
   - `vega-batch.py new "<brand>" N --type carousel` sets style `carousel`; duration and music are not used.
   - `atlas-sheet.py` adds the `carousel` output type.
   - Atlas's designer list adds `carousel` as a style that needs a script, the script being Echo's angle.
   - `vega-output.py` already has a `carousel` type for the output log.
7. **Atlas's rules for carousel rows** follow the same pattern as avatar rows:
   - READY when the slides are made.
   - The render step confirms the slides and the designer replies `DONE <slides folder> <credits> <minutes>`.
   - It takes a render slot for only a few seconds.
8. **Our designer rules are added to the skill:**
   - Read the start time with `date`.
   - Name files by Task ID and save them in `Project/<Brand>/`.
   - Record each job's real cost from `spira --json ai jobs status <jobId>` (data.credits). Today's `gen_image.sh` throws the job ID away, so it changes to keep it.
   - Record the outcome on the sheet.
   - Ask questions through Atlas: `QUESTION` lines instead of "ask the user".
9. **Fix the parts that assume a person is watching:**
   - "Real screenshot from a browser the user signed into" becomes: capture the public site with the Cloner's `capture_site.js`, or use a labelled empty slot.
   - "Ask the user for a hosted link" becomes: use the local file in the layout without generating from it.
10. **Run-memory safety.** Up to 6 designers can run at once. The history `record` step gets the same file lock that the theme step already has, so two carousels finishing together don't overwrite each other.
11. **Uploads (Hermes).**
    - Hermes's tool only picks up `.mp4` today, so it gets carousel support: each slide uploads as an image under the brand's tag, in slide order.
    - The upload tag is asked per brand, as usual.
12. **Delivery on Lark.** In the requester's thread, post the contact sheet and the slides, plus the captions from `notes.md`.
13. **Report and docs.** Then publish the report and the workflow.
    - **Report:**
      - Carousel Designer added under Designers.
      - Carousels counted per brand.
    - **Workflow and SOP:**
      - Workflow schema updated.
      - SOP line: "@Vega make N carousels for <brand>".
    - **Records:**
      - Dev note added.
      - Update record (v2.1).
14. **Live test.** Make one carousel for one brand (about 50 credits), check it with you, then fix anything that comes up.

## Decisions for the owner
1. **Name and style:** "Carousel Designer", style `carousel`. Recommended.
2. **Separate carousel angle record per brand**, so video angles don't block carousel angles. Recommended.
3. **Test brand for the first live run.** Suggested: PartGenie or Spira.
4. **Slide size:** keep 1080×1350 (4:5, made for Instagram and LinkedIn), or also make 9:16 for TikTok.
