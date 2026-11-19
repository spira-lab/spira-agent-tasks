# Super Nova v2.01: system update, 2026-10-27

The record of the Carousel Designer install, which the owner approved on Lark (DM, 2026-10-27 11:06). Kept for reference: Nova reads it when anyone asks what changed. The team announcement covered only the items marked **(team)**.

## Before the change
- **(team)** New requests were paused, and the pause was announced to the group (with Nova's photo).
- System backup: `Backup/back-up before installing Carousel Designer 2026-10-27.zip` (Agents/ and Lark connect/, 11,479 files, 487 MB, `zip -T` OK), logged in `Backup/backup-ledger.md`.

## New agent
- **(team)** 🖼️ **Carousel Designer** installed (renamed the same day: now the Corporate Carousel Designer, `Agents/CorporateCarouselDesigner/`; see "Rename" below), adapted from the owner's "Corporate carousel" skill.
  - What it makes: 4–7 slides at 1080×1350 (4:5, the default and only size), a contact sheet, captions (short-form and LinkedIn) and an editable `slides.html`.
  - Its inputs are the topic angle (from Echo) and the brand's or product's website (from the ledger).
  - Its output goes to `Project/<Brand>/carousels/<TaskID>-<brand>-<MM-DD>/`, with metadata in `Project/<Brand>/metadata/`.
  - Like the other designers, it runs as an Atlas row. It reads the start time, records each job's real credits (`data.credits`) and sends questions to Atlas. It finishes with `DONE <folder> <credits> <minutes>`.
  - One Python entry point, `tools/carousel.py`, runs the original shell scripts, because Atlas's approved commands don't include bash.
  - The run memory (`state/`) alternates dark and light themes and keeps looks from repeating. Its record step is now locked, so 6 carousels at once can't overwrite each other.
  - Product UI is never mocked: the designer uses a public-site capture (the Cloner's `capture_site.js`) or a labelled empty slot.
- **(team)** Ask with `@Nova make N carousels for <brand>`. The brand needs a Website in the client ledger.

## System changes
- **Sheet and batch tools.**
  - `nova-batch.py --type carousel` sets style `carousel`, keeps the ledger lookup and adds `Product:` and `Brand website:` to the instructions.
  - It refuses a missing website, an unknown product or Brandless before any number is issued.
  - The website handover now covers clone, re-skit and carousel.
- **Atlas.**
  - `atlas-sheet.py` has output type `carousel`, with a carousel-only request.
  - `carousel` is in Atlas's designer list as a style that needs a script.
  - A "Carousel rows" section was added to Atlas's skill.
- **Echo.**
  - The "script" for a carousel row is the topic angle: a new writing style, carousel topic angle.
  - **Separate carousel angle record per brand** (the owner's decision), `scripts/<Brand>/carousel-angles.json`. A carousel angle can't repeat within the brand's last 75 carousels (the owner set the window the same day; it started as never-repeat), and video angles never block them.
- **Hermes:** uploads each slide in order, as images under the brand's tag.
- **Jani:** a carousel folder and its metadata are backed up, checked and cleared as one set.
- **Report:**
  - The Carousel Designer appears in the Designers team (status new).
  - Each brand card shows a Carousels count.
  - Carousel credits are counted.
- **Docs:**
  - **(team)** The SOP (Lark doc) has a new section, "2c. Carousels", and PartGenie's target is corrected to 50 a week (10 a day).
  - The workflow schema is at v9.
  - Nova's skill has a "Carousel requests" section.
  - The video styles doc and the batch template were updated.
  - The client ledger's Website note now includes Carousel.
- Nova's rule: every upgrade update to the team goes out with Nova's photo.

## Rename (later the same day)
- The owner's decision (2026-10-27): the Carousel Designer is now the 🖼️ **Corporate Carousel Designer**, because more carousel designers will follow (a Lifestyle Carousel Designer and others). Backup first: `Backup/back-up before renaming to Corporate Carousel Designer 2026-10-27.zip`.
  - Folder `Agents/CorporateCarouselDesigner/`, skill `skills/corporate-carousel-designer.md`; style `corporate carousel`. Output type stays `carousel` for every carousel designer, and so does Nova's output log type.
  - Carousel family: any style ending in "carousel" takes the carousel path in Atlas, Nova's batch tool and Echo (no duration, the topic angle as its script, the website handover, the carousel folder, the carousel angle record, Hermes's slide upload, Jani's carousel set). A new carousel kind needs only its designers.json entry and its own skill; Echo gives it the corporate carousel's topic angle until it has a writing style of its own.
  - `nova-batch.py --type carousel` uses `corporate carousel` unless `--style "<kind> carousel"`; it refuses a carousel style with no designer in Atlas's list.
  - Old sheets' Style `carousel` reads as `corporate carousel` (Atlas's `_aliases`, Echo, Iris). Nothing in `Project/` or in finished sheets was renamed; Echo's carousel angle records (`scripts/<Brand>/carousel-angles.json`, 75 window) are unchanged and shared by every carousel style.
  - Echo's writing style row is now video style `corporate carousel` (`styles/CorporateCarousel-TopicAngle/echo-corporate-carousel-topic-angle.md`).

## Open
- Upload tag for carousel slides. PartGenie's saved tag is "PartGenie / US - Video". Decide whether carousels get their own tag.
- The Data Cleaner doesn't move a carousel's folder on a redo or cancel; only the metadata moves. It is left as is until it comes up.
- Fact to confirm from the test: slide 4 says PartGenie has 56M+ parts (homepage), but the site's FAQ says over 35 million.

## Live test
- PartGenie #31 (Task 366): 5 slides, 5 credits (one GPT Image 2 call), about 9 minutes in all. No questions.
- The owner approved the test carousel (2026-10-27 11:40, "Good result, I am Happy with it") and named this update **Super Nova v2.01**.
