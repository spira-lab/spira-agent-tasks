# Plan: install the Lifestyle Story Carousel Designer (2026-11-03)

Approved by the owner on 2026-11-03. Source: Rey's "Carousel Skill V2" (a zip; read, never run from
inside it). It holds:
- `SKILL.md` and `HOW-TO-USE.md`, plus the brief PDF;
- `references/`: the quality bar, model prices and the route test, the 100-idea generic ledger, and
  Ryan's 4 carousels (26 slides) as the target look;
- `scripts/`: 7 Python scripts (`job.py`, `spira_cli.py`, `statusbar.py`, `screen_fit.py`,
  `screen_composite.py`, `grade.py`, `render_text.py`);
- `clients/`: the client ledger, 6 briefs (PartGenie, Cookiy Earn, Emochi, Pexo, IASO, Bybit mStocks),
  used-ideas logs and real product screens; `angles-log.md` (9 carousels made so far).

## What the skill does
- **Input:** a client and, optionally, a format (story or feed) and a topic. No script.
- **Output:** 5–10 photoreal slides (4:5 feed or 9:16 story), with `research.md`, `copy.md`, `prompts.md`
  and `report.md`.
- **How it works:**
  - Picks its own idea: the client's researched idea bank first, then the 100-idea ledger, with a
    no-repeat rule per client (kind and pain type vs the last 5, persona and place vs the last 3).
  - Researches fresh pains, writes the copy, locks one person and one place.
  - People: Higgsfield Soul, then one GPT Image 2.5 edit (route A). Objects and hands: Nano Banana 2.1.
  - Real product UI on green phone screens (Playwright captures, or a factual HTML simulation).
  - Local grade and text (Playwright), then a 6-check self-grade per slide.
- **Cost:** about 80–100 credits per carousel.
- **Its one stop** was a credit gate before generating.

## What changed so it works in our system
1. **Backup first** (already done before this install): `Backup/back-up before Lifestyle Story Carousel
   install 2026-11-03.zip` (Agents/ and Lark connect/), logged in `Backup/backup-ledger.md`.
2. **Installed as a designer:** `Agents/LifestyleStoryCarouselDesigner/` with Rey's `references/`,
   `scripts/`, `clients/`, `angles-log.md`, `HOW-TO-USE.md` and the brief PDF copied in, and the skill
   rewritten as `skills/lifestyle-story-carousel-designer.md`. `${CLAUDE_SKILL_DIR}` is that folder.
   Rey's method is kept as it is: route A, the quality bar, the 7 "what separates us from Ryan" rules,
   the 6 grade checks, the no-repeat rules and re-roll once.
3. **Style and output type:** style `lifestyle story carousel`, output type `carousel` (an image post,
   logged with `nova-output.py ... carousel` like corporate carousels). `corporate carousel` is unchanged.
4. **Scriptless.** In Atlas's designer list as `{"skill": ..., "script": "none"}`, so Echo writes
   nothing and the batch tool makes the rows `pending` at once (like clone and re-skit). The batch tool
   already adds `Product:` and the ledger Website to the instructions for every carousel style; the
   requester's note (topic, story or feed, slide count) goes in `--instructions`.
5. **Atlas's request** for a scriptless carousel row (`atlas-sheet.py`): the same lines as a
   corporate carousel, but "4:5 unless the instructions ask for a 9:16 story" and "This is a scriptless
   carousel" instead of the topic angle. The corporate carousel's request is unchanged.
6. **No credit gate.** Every Atlas row is "generate, up to 150 credits". A quote over 150 comes back as
   `QUESTION` with the quote (over 500: always). Nova asks the requester and answers
   `generate, up to <N> credits`; the designer raises its cap with `lsc.py cap`. The job tool refuses a
   job that would pass the cap.
7. **One entry point, `tools/lsc.py`** (Atlas's approved commands have only `python3`, no bash, no cd):
   - `new`: the build folder `Project/<Brand>/carousels/<TaskID>-<brand>-<MM-DD>/` and its metadata.
   - `client`, `ideas`, `reserve`, `mark`, `append`: the shared client files, under one lock. Up to 6
     rows run at once, so the idea is **reserved when it is picked** (Rey reserved it at the gate),
     and the reserve refuses a taken or repeating idea. Bank and ledger rows get their IDs from the tool.
   - `job` / `fetch`: one Spira job through Rey's `job.py` (submit once, poll the same ID); the job's
     real credits (`data.credits`) go into the metadata, never the balance.
   - `run` / `py`: Rey's local scripts and the designer's own Playwright captures.
   - `export`: the newest named slide PNGs to `out/slide-01.jpg` … (feed 1080×1350, story 1080×1920)
     and `out/contact.png`, which Nova's delivery and Hermes read (Hermes takes `out/slide-*.jpg` in
     order; the contact sheet and notes are never uploaded).
   - `check` / `finish`: confirm-only render step, then `DONE <folder> <credits> <minutes>`.
8. **Our designer rules in the skill:** read the clock with `date`; name by Task ID; build in
   `Project/<Brand>/carousels/`; `out/notes.md` with a `## Captions` section (short-form and LinkedIn)
   and "Facts needing a human check"; READY / DONE / FAILED / QUESTION lines and the `VIDEO DONE`
   message to Nova as Atlas's texts say; never delete (rejected takes go to `deletable/`, Rey's
   "Don't use/"); read only toolkit sections 1–2 from `DesignerShared/`, like the corporate designer.
9. **Parts that assumed a person:**
   - Research had web search and the user's Chrome; Atlas's designers have neither, so research uses
     `curl` (open APIs: Hacker News, Reddit's JSON, Stack Exchange) and signed-out Playwright pages,
     with Rey's snippet and mirror rules.
   - Health and finance briefs said "check those lines with the user": with no gate, those lines stay
     out unless the brief or the site states them word for word, and they are listed for a human check
     in `notes.md`.
   - The 401 "tell the user to log in" is a QUESTION.
10. **Mac fixes.**
    - `statusbar.py` loaded `C:/Windows/Fonts/seguisb.ttf`. It now loads SF Pro Semibold
      (`/System/Library/Fonts/SFNS.ttf`), then Helvetica Neue Medium, Arial Bold, then Pillow's default.
    - The other Windows-only paths were in examples and notes only (`render_text.py`'s docstring,
      `models.md`); `spira_cli.py` already handles the Mac.
    - Python: Homebrew's python3 refuses `pip install --user` (PEP 668), so the packages (Playwright +
      Chromium, Pillow, NumPy, OpenCV) are in their own venv, `~/.venvs/lifestyle-carousel`. `lsc.py`
      re-runs itself under it, so every command is still `python3 ...`.
11. **Client names.** Our ledger's Cookiy Earn Text Agent and Cookiy Earn Sell Session are aliases of
    Rey's Cookiy Earn client. The brand name Cookiy Labs alone, or Cookiy Insights, becomes its own
    client, so Earn posts never carry the B2B product.
12. **Docs:**
    - Nova's skill: the style list, and "Which carousel designer", with lifestyle only when the requester
      asks for lifestyle, story, photo or people carousels, the 150 cap, and delivery.
    - The other docs: the SOP mirror (section 2c), video styles, the roster and subagent roster, Atlas's
      skill, Hermes's skill, the client ledger's Website note, the workflow schema page, and the dev notes.

## Not changed
- Echo: no writing style, nothing to write (scriptless rows are never `draft`, so `echo-plan.py` skips them).
- Iris, Jani, Hermes's code and the Data Cleaner work as they do for corporate carousels: the style is
  counted by name, the folder is a carousel folder, and the slides are `out/slide-*.jpg`.

## Open
- The SOP's Lark doc still needs the same section 2c edit (the local mirror is updated; nothing was
  posted to Lark).
- First live run: one carousel for one brand (about 80–100 credits), checked with the owner.
- Rey's Cookiy Earn log holds a stale reservation (G001, build `fresh-agent-test-3`); it blocks G001 for
  Cookiy until someone marks it used or dropped.
