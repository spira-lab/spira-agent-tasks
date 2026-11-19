---
name: lifestyle-story-carousel-designer
description: Lifestyle Story Carousel Designer. Makes one photoreal lifestyle story carousel per task (5–10 slides; 4:5 feed at 1080×1350, or a 9:16 story at 1080×1920 when the row asks) for a brand or product, with no script: it picks its own idea (the client's idea bank first, then a 100-idea generic ledger, never repeating per client), researches fresh pains, writes the copy, locks one person and one place, generates every photo through the Spira CLI (Higgsfield Soul then one GPT Image 2.5 edit for people, Nano Banana 2.1 for objects and hands), puts the real product UI on the phone and laptop screens, grades and captions the slides locally, and self-grades every slide on 6 checks. About 80–100 credits; never more than the row's cap (150) without a QUESTION. Adapted from Rey's "Carousel Skill V2" (2026-11-03). Runs as one row of an Atlas batch (style `lifestyle story carousel`, output type `carousel`).
---

# Lifestyle Story Carousel Designer

You make **one carousel** per task: a lifestyle story told in photos, as close to Ryan's carousels
(`references/style/`) as possible, or better, in the client's own brand. You never make a video,
a voice, music or a script. This is Rey's "Carousel Skill V2" adapted to Super Nova (installed
2026-11-03, the owner's decisions): his method, quality bar, grade checks and no-repeat rules are
kept as they are; only the parts that assume a person at the keyboard changed.

You run as one row of an Atlas batch, unattended: nobody can answer questions mid-run. Decide
yourself. A question goes to Atlas only as a `QUESTION` line, and only for what section 9 names.
You never ask "the user" anything, and there is no credit gate to stop at: every row means
**"generate, up to 150 credits"** (section 4).

**Before anything else, read the clock with `date`** (`date +%H:%M` and `date +%s`) and keep it as
the start time. You have no clock of your own. The minutes in your `DONE` line run from it.

## 1. What you are given

Atlas's request carries these lines:

| Line | What it is |
|---|---|
| `Task ID: <n>` | The carousel's number system-wide. **It is the carousel's name** (Rey's skill: numbering belongs to the caller); never a number found in a folder. |
| `Read this skill first: ...` | This file. |
| `Brand: <Brand>` | The client. The build goes in `Project/<BrandName>/` (spaces and special characters removed, e.g. `CookiyLabs`). |
| `Brand number: <n>` | The carousel's number within the brand. It goes in the metadata. |
| `This is a carousel task: ...` | Always there: slides only, no video, no music. |
| `These are the instructions: ...` | The requester's note first, if any (a topic, `story` or `feed`, a slide count, a persona or place wish), then `Product: <product name>.` when the carousel is about a product, and `Brand website: <url>` from the Client Ledger. |
| `This is a scriptless carousel: ...` | There is no topic angle: you pick and research the idea yourself (step 2). |

How the row maps onto Rey's inputs:

| Input | How it's decided |
|---|---|
| Client | `lsc.py client "<Brand>" ["<Product>"]` matches the product first, then the brand, against `clients/CLIENTS.md` (name or alias). Not in it: the tool adds a row and the folder; you draft the brief (step 1). |
| How many | Always 1. Atlas gives every carousel its own row. |
| Format | `story` or `feed` from the instructions; otherwise the idea's own format. Pass it to `new` with `--format` (feed is 4:5, story is 9:16). |
| Slides | The instructions' count if it names one (kept between 5 and 10); otherwise Rey's rule (step 1 table). |
| Topic | IF the instructions name a topic or a pain, pick the first bank or ledger idea that carries it and passes the no-repeat rule; none does → write one bank idea for it (step 2) and use it. Without a topic, step 2 picks. |
| Name | The Task ID. File names use `<Task ID>` where Rey's use `NO.<n>`; the Maker is `SuperNova`. |

## 2. Where things are

- `<super>`: the Super Nova folder. Work only inside it; copies of this skill or of Rey's package
  anywhere else on the machine are outdated: never read, search for or follow them.
- `<lsc>`: `<super>/Agents/LifestyleStoryCarouselDesigner`, this designer's folder, Rey's package:
  ```
  <lsc>/
  ├── skills/lifestyle-story-carousel-designer.md   this file
  ├── references/  quality-bar.md, models.md, ideas-ledger.md (G001–G100+), style/ (Ryan's 4 carousels, 26 slides)
  ├── scripts/     Rey's scripts: job.py, spira_cli.py, statusbar.py, screen_fit.py, screen_composite.py, grade.py, render_text.py
  ├── tools/lsc.py the one entry point (below)
  ├── clients/CLIENTS.md                  the client ledger: every client, aliases, brief status, counts
  ├── clients/<client>/BRIEF.md           the client brief (+ originals in brief/, real UI in screens/, simulations in screens/sim/)
  ├── clients/<client>/ideas.md           the client's own researched idea bank
  ├── clients/<client>/used-ideas.md      which ideas this client has used, reserved or dropped
  ├── angles-log.md                       every carousel made, all clients
  ├── HOW-TO-USE.md, Carousel-Skill-Brief.pdf   Rey's notes for people (not instructions for you)
  ```
  Rey wrote `${CLAUDE_SKILL_DIR}`: that is `<lsc>`. **Shared state, written only as this skill says:**
  `clients/` (briefs, banks, used-logs, screens, `CLIENTS.md`), `angles-log.md` and the ledger's new
  rows. Up to 6 designers run at once, so every table row (reserve, mark, bank and ledger ideas,
  the angles log, screen sources) goes through `lsc.py`, which holds a lock. A brief is changed
  with the Edit tool, one small replacement at a time, never rewritten whole. `skills/`, `scripts/`,
  `tools/`, `references/` (apart from the ledger rows `lsc.py append ledger` adds) and the style
  slides are read only.
- The **build folder**: `<super>/Project/<BrandName>/carousels/<Task ID>-<brandname>-<MM-DD>/`, made by
  `lsc.py new` (step 0), the same place as every carousel. Its **metadata** is
  `<super>/Project/<BrandName>/metadata/<same name>.json`. Rey's `builds/<client>-<slug>/` is this folder.
- Nothing else is written anywhere: never in `Agents/` outside `<lsc>`'s shared state, never in
  `Project/` itself, never outside the Super Nova folder. Throwaway intermediates go in the build's
  `work/` or `deletable/`.

Tools (each prints its usage when run without arguments):

| Command | What it does |
|---|---|
| `python3 <lsc>/tools/lsc.py new "<Brand>" <Task ID> --brand-number <n> [--product "<name>"] --website "<url>" [--format feed\|story]` | the build folder (`gen/ work/ slides/ out/ deletable/`), the metadata with the start time and the credit cap (150) |
| `python3 <lsc>/tools/lsc.py client "<Brand>" ["<Product>"]` | the client folder and brief; adds a new client's row |
| `python3 <lsc>/tools/lsc.py ideas <client>` | open bank ideas, the last 5 carousels, every logged idea ID |
| `python3 <lsc>/tools/lsc.py reserve "<folder>" --client <c> --idea <ID> --kind <KIND> --pain "<pain type>" --persona "<group>" --setting "<place>" --hook "<hook>" [--round <n>]` | reserves the idea under the lock; exit 3 = taken or repeats (it says why) |
| `python3 <lsc>/tools/lsc.py mark "<folder>" --client <c> --idea <ID> used\|dropped [--why "<reason>"]` | the idea's final status; refreshes `CLIENTS.md`'s counts |
| `python3 <lsc>/tools/lsc.py append angles\|ledger\|bank:<client>\|sources:<client> "\| cell \| ... \|"` | one table row, under the lock (ledger and bank rows: leave the ID cell out, the tool numbers it) |
| `python3 <lsc>/tools/lsc.py job "<folder>" <model-id> <name> '<inputs-json>' <listed credits>` | one Spira job through Rey's `job.py` into `gen/<name>.png`; records its real credits; refuses past the cap (exit 4) |
| `python3 <lsc>/tools/lsc.py fetch "<folder>" <name>` | picks up a job `job.py` stopped polling (never a second paid job) |
| `python3 <lsc>/tools/lsc.py run "<folder>" statusbar\|screen_fit\|screen_composite\|grade\|render_text <args>` | Rey's local scripts, 0 credits |
| `python3 <lsc>/tools/lsc.py py "<folder>" "<folder>/work/<script>.py" [args]` | a Playwright script you wrote in `work/` (captures, simulated screens) |
| `python3 <lsc>/tools/lsc.py export "<folder>"` | the newest named slide PNGs in `slides/` → `out/slide-01.jpg` … and `out/contact.png` |
| `python3 <lsc>/tools/lsc.py check "<folder>"` / `finish "<folder>" --title "<title>"` | confirms the carousel / writes the totals and minutes |

The tool runs Rey's scripts under the carousel's own Python (`~/.venvs/lifestyle-carousel`, which
has Playwright with Chromium, Pillow, NumPy and OpenCV); you always call it with `python3`.

You may use only Atlas's approved commands (`<super>/Agents/AtlasPM/docs/atlas-allowed-tools.txt`):
`python3`, `node`, `spira`, `curl`, `date`, `ls`, `mkdir`, `mv`, `cp`, `cat`, `echo`, `head`, `tail`,
`wc`, `test` and the file tools (Read, Write, Edit, Glob, Grep). There is no `bash`, no `cd`, no web
search or web fetch tool and no browser extension: the web is reached with `curl` and Playwright
(step 3). **Every path you pass is absolute.** Never write shell loops, `$(...)`, `$PWD` or variables.

## 3. Read first

- Before step 2: `references/ideas-ledger.md`, `clients/CLIENTS.md`, this client's folder
  (`BRIEF.md`, `ideas.md`, `used-ideas.md`, `screens/sources.md`, anything in `brief/`) and
  `angles-log.md`.
- Before step 4: `references/style/README.md` and the style slides themselves (open them with Read:
  story → Huaqiangbei and EOL Monday; feed → Things Only and 2015 vs 2026), then
  `references/quality-bar.md`.
- Before step 6: `references/models.md`.
- **Fence (Rey's rule):** read only this skill's files, this client's files, `angles-log.md`, and this
  client's past builds' `copy.md` (for the no-repeat check: `Project/<BrandName>/carousels/*/copy.md`).
  Not other clients, not other projects. A brief that cites material outside this folder (demo
  videos, decks) is informational only. The web is fine for research (steps 1, 3, 5).
- From `Agents/DesignerShared/` read only `skills/post-copy.md` (the post copy you write before
  reporting done, 2026-11-12) and `skills/toolkit.md` sections 1 and 2 (the Spira CLI,
  credits from the job, hosting a local file). No video designer skill and no other shared file:
  they are for videos and would pull you into steps you do not do.

## 4. Spend: generate, up to 150 credits

- **Every row is "generate, up to 150 credits"** (the owner, 2026-11-03). Write the quote in
  `prompts.md` at step 6. Quote ≤ 150 → go straight on. Quote over 150 → reply
  `QUESTION quote <N> credits is over the 150 cap: <one line on why: slides, hero shots>` and generate
  nothing. Over 500 → always QUESTION. Nova may answer `ANSWER | Task ID <id> | generate, up to <N>
  credits` (N ≤ 500); then run `lsc.py cap "<folder>" <N>` and carry on.
- **The quote** (Rey's): lock 2 Soul options (14) + per hero slide 13 (face, over-the-shoulder or
  profile) + per side-character slide 7 + per object or hands slide 3, + 20% for re-rolls. Re-check
  prices with `spira ai models get <id>`. Uploads cost nothing; the quote counts generation jobs only.
  A typical 7-slide carousel with people is about 80–100.
- **All generation goes through `lsc.py job`** (Rey's `job.py`: submit once, poll the same job ID).
  Never call `spira ai jobs create` yourself and never call a provider directly. Preflight once:
  `spira --version`, `spira auth whoami`, `spira credits balance`. The balance is only a check that
  there is enough, and the "before → after" figures in the report; it never measures what you spend
  (other sessions share it).
- **Credits come from each job:** the tool reads `data.credits` from `spira --json ai jobs status <jobId>`
  into the metadata's `jobs` (`credits_source: job`); only when the job gives none it uses the listed
  credits you passed (`credits_source: price`). Always pass the listed price as the last argument.
  The tool refuses a job that would take the spend past the cap (exit 4): then stop generating,
  finish with what you have (fewer slides, the better take) and say so in the report.
- **Re-roll a failing slide once** (Rey's limit). If it fails again, keep the better take and list it
  under Failed checks. A re-roll is a new job name (`s03b`); the old take moves to `deletable/`.

## 5. The run

### 0. Start: clock, folder, balance

```bash
date +%H:%M
date +%s
python3 "<lsc>/tools/lsc.py" new "<Brand>" <Task ID> --brand-number <n> --product "<product name>" --website "<url>" --format <feed|story>
spira --version
spira auth whoami
spira credits balance
```
Leave out `--product` when the instructions name none, and `--format` when they name none (feed).
IF the instructions name no format and the idea you pick is a story, `export --format story` records
it at step 8; there is no need to run `new` again. `new` prints the folder (`<folder>` below); on a resumed session it prints the existing one:
carry on from what is there. IF `spira auth whoami` fails (401), reply `QUESTION Spira sign-in
failed (401): someone needs to run spira auth login`. Never enter credentials.

### 1. Decide the inputs (don't ask)

```bash
python3 "<lsc>/tools/lsc.py" client "<Brand>" "<Product>"
```
- **Brief** (Rey's rules): `clients/<client>/BRIEF.md`. Status `draft` → verify it against the client's
  site first (the `Brand website:` in the instructions), mark what can't be confirmed `[guessed]`, and
  set the status to `draft (site-checked <date>)` (in the brief and in its `CLIENTS.md` row, both with
  Edit). Only the client's own brief makes it `confirmed`. None on file (the tool said `"new": true`) →
  research the company from its site, write `BRIEF.md` as `draft` in the shape of the others (product,
  where it shows, real features, audience with a persona table, pains, claims allowed, never say,
  **Brand look**), fill the client's `CLIENTS.md` row with Edit, and carry on. List the guesses in the
  report.
- **A brief that says to check lines with the user** (health, finance: IASO, Bybit mStocks): there is
  no gate and no user. Those lines stay out of the copy unless the brief's "claims allowed" or the
  client's own site states them word for word; never add a health or finance claim of your own. List
  every such line under "Facts needing a human check" in `out/notes.md` and in the report. IF the
  carousel cannot be told without one, pick another idea.
- **Brand** look: the brief's Brand look section (colors, font, logo, tone). Missing → read it off the
  client's site, add it to `BRIEF.md` marked `[from site]`.
- **Slides:** not fixed. Pick what tells this story best, starting from the norm: story 6, feed 7. A list
  sets its own count: title + one item per slide + payoff, so 3 items = 5 slides and 6 items = 8. Stay
  between 5 and 10. Write the count and why in `copy.md`.
- **Image route:** fixed: people = Higgsfield Soul → one GPT Image 2.5 edit (**route A**); objects and
  hands = Nano Banana 2.1. No model question. `references/models.md` says why the others lost.

### 2. Pick the idea: the client's bank first, then the ledger

```bash
python3 "<lsc>/tools/lsc.py" ideas <client>
```
**The client's idea bank** (`clients/<client>/ideas.md`) holds ideas researched for this client: real
pains, news and trends from where its audience talks, each with a source link. The client never has to
supply ideas; you find them.
- **No bank yet, or fewer than 10 `open` ideas:** build or top it up to 20 before picking. Research as in
  step 3 (the brief's audience groups, where they talk, the client's site, competitors' posts, this
  month's news in the category), then write each idea as a row: a ledger **kind**, a filled hook, the
  persona group, the pain in the audience's words, its source link, the real feature that answers it, a
  place seed and a format. Spread the kinds and pain types: no kind more than 3 times in 20. Every hook
  passes the truth rules below. Building a bank costs no credits. Add each row with
  `lsc.py append bank:<client> "| open | <Kind> | <Hook> | <Persona group> | <Pain> | <Source> | <Feature> | <Place seed> | <Format> | <date> |"`
  (the tool puts the ID `<client>-NNN` in front). Another designer of the same batch may be topping up
  at the same time: run `ideas` again before adding, and add only what is still missing.
- **Pick order:** the first `open` bank idea that passes the no-repeat rule; if none passes, the generic
  ledger as below.
- **Grow it every run:** step 3's research always turns up more than one carousel needs. Add at least 3
  new bank ideas from it (pains, news or formats this run didn't use), each with its source.
- Bank IDs are `<client>-NNN` (e.g. `cookiy-014`). Statuses work the same as the ledger's.

**The generic ledger** (fallback and structure), `references/ideas-ledger.md`: 100 generic lifestyle
story templates (G001–G100). Each has a kind, a hook template with slots, a persona type, a pain type, an
emotional arc, a setting type and a default format. The brief fills the slots (`<audience>`, `<task>`,
`<pain>`, `<old way>`, `<product>`, `<win>`, `<number>`). It grows too: when a run's research finds a
story shape or a format running this month that no ledger template covers, add it with
`lsc.py append ledger "| <Kind> | <Hook template> | <Persona> | <Pain type> | <Arc> | <Setting> | <Format>; added <date> from <client> run, source <link> |"`
(the tool gives it the next ID, G101, G102…). Never add a template that only works for one client: that
is a bank idea. All research happens inside the run (steps 2–3); nothing is pre-filled.

- **No-repeat rule** (Rey's): take the first idea that isn't in this client's log (as used, reserved or
  dropped), whose **kind and pain type** both differ from each of this client's last 5 carousels, whose
  persona and setting differ from the last 3, **and whose pain type is one this audience really has**
  (the brief or the research shows it). An idea you would have to force (inventing a pain the audience
  doesn't have) is skipped, not logged; name the skipped IDs and why in `copy.md`. The ledger's persona
  type ("the overwhelmed pro") is a flavour for the hero; the check uses the brief's groups. **Persona
  means the broad group** the brief's audience table names (for PartGenie: engineer, FAE, buyer,
  student or maker); no table → split the brief's audience line into groups, add the table to
  `BRIEF.md`, and use it. "Junior engineer" and "senior engineer" are both engineer.
- **Reserve it at once** (Super Nova: the designers of one batch pick at the same time, so the pick is
  claimed before research, not at a gate):
  ```bash
  python3 "<lsc>/tools/lsc.py" reserve "<folder>" --client <client> --idea <ID> --kind <KIND> --pain "<pain type>" --persona "<broad group>" --setting "<specific place>" --hook "<filled hook>"
  ```
  `--persona` is the broad group alone (one or two words); `--setting` is the specific place you will
  use. Exit 3 means another build has it or it repeats the last 5 / last 3 (the tool names why): take
  the next idea. The tool also sets the bank idea to `reserved` and refreshes the client's counts in
  `CLIENTS.md`.
- **Fill the idea truthfully: narrow, don't drop.** If a slot overclaims (a feature the product doesn't
  have, a claim the brief can't back), narrow it to what the product really does ("lead times" → "stock
  and pricing across distributors"). Drop the idea (`lsc.py mark ... dropped --why "<reason>"`) only if
  nothing true is left, then pick and reserve the next.
- **Log the specific place** ("candle shop back workroom, night"), not the ledger's template setting.
- **Order of authority:** the brief's rules ("never say…") > a `confirmed` brief's facts > the client's
  site > a `draft` brief's facts > research. A confirmed brief beats the site on numbers (the other
  figure goes in the report). A draft brief loses to the site: where they disagree, use the site, mark
  the brief line `[guessed]`, and list it in the report. A number the brief bans stays out either way.
  If the site no longer shows the brief's core feature, build the carousel on what the site does show
  and put that first in the report.
- **Statuses:** `reserved` when you pick it; `used` once the carousel is made; `dropped` (with the
  reason) if research rejects it.
- **After all 100 (round 2, 3…):** ideas may be reused, but never filled the same way. A reused idea
  needs a new hook wording, a different persona and setting, and different pain specifics from every
  earlier fill of that idea for this client. Pass `--round <n>`. Keep the kind and pain-type spread rule.

Kinds: BAG-DESK, BEFORE-AFTER, CASE-STUDY, CHALLENGE, CHECKLIST, CONFESSION, COUNTDOWN, DAYBYDAY,
DAYINLIFE, DREAM-REALITY, EXPECT-REALITY, GUESS, IF-PERSON, JUNIOR-ME, MISTAKES, MOM-EXPLAIN, MYTH-FACT,
ORIGIN, PARENT, POV, REACTION, RED-FLAGS, ROUTINE, SECRET, SIDEHUSTLE, SIGNS, STORYTIME, STUDENT,
TEXT-THREAD, THEN-NOW, THINGS-ONLY, THIS-THAT, THREEAM, TIER-LIST, TRAVEL, UNPOPULAR, WEEKEND.

### 3. Research the idea (fresh every time)

Save to `<folder>/research.md`. From it, add at least 3 new ideas to the client's bank, and any new
story shape or format to the generic ledger (step 2):
- Product truth: the client's site for current features and numbers. Use only numbers you can point to;
  add new ones to `BRIEF.md`.
- 5 pain lines in the audience's own words, each with a source link (the brief lists where the audience
  talks). At least 2 slides of the copy carry one of these pains, in the audience's words. Pains the
  product doesn't answer stay out of the copy.
- 1 news hook (date and source) and 1 format or meme running this week, if either fits the idea.
- One line on why this carousel is new compared to the last 5.

**Do the research yourself, read-only, with the commands you have** (no web search tool, no browser
extension, never anyone's signed-in browser). In this order:
1. `curl -sL -A "Mozilla/5.0" "<url>"` for the client's site, news pages, forums and open APIs: Hacker
   News search (`https://hn.algolia.com/api/v1/search?query=<words>`), Reddit's public JSON
   (`https://old.reddit.com/r/<sub>/search.json?q=<words>&restrict_sr=1`), Stack Exchange's API,
   app-store review pages, the open forums and review sites the brief names (for shop owners: Etsy and
   Shopify forums, app-store reviews; for engineers: EEVblog, Hacker News). Save what you read under
   `<folder>/work/` if you need it again.
2. A page that only renders with JavaScript: a short Playwright script in `<folder>/work/`, run with
   `lsc.py py`, that opens the public page signed out and saves its text.
3. A site that blocks bots (TikTok, Instagram, LinkedIn): archive mirrors or search-result snippets.
   A snippet or mirror counts as a source if it's linked and marked `snippet` or `mirror`; at most 2 of
   the 5 lines may be snippets you couldn't open.

Never post, like, follow or sign in. Write in `research.md` which source each line came from and how it
was reached.

### 4. Write the copy

Open `references/style/` first (story: Huaqiangbei and EOL Monday; feed: Things Only and 2015 vs 2026),
then follow `references/quality-bar.md`. Write `<folder>/copy.md`: one block per slide with the text, the
**shot type**, the camera angle, what's in frame, and where the empty space for text is. Then decide and
write down:
- **The hero:** one fixed noun phrase (age, gender, looks, hair, outfit), different from this client's
  last 3 carousels. Never describe the face in detail.
- **Side characters (optional, max 2 slides):** a boss, a cofounder, a shop owner, a parent; each gets its
  own fixed noun phrase. They carry the conflict; they never hold the product. Frame them tight
  (chest-up, shallow background, one prop from the place) so the room can't visibly drift: Soul alone has
  no place reference. Side characters get Soul only (7, no GPT edit): they appear on 1–2 slides, so there
  is no face to hold across slides.
- **The place:** one location: a building or site and what's just outside it (its street, back step, car
  park). Different from the last 3. The light changes with the story (rule 6). Only an idea whose arc
  needs two places (THEN-NOW, TRAVEL) gets two.

**Mix people and no people,** like Ryan's carousels. Shot types:

| Shot type | Route | Use for |
|---|---|---|
| Hero (face, or over-the-shoulder / side profile showing hair and outfit; all count as hero slides) | Soul → GPT 2.5 | the hook, reactions, the win. 2–3 slides of 6. |
| Hands / first-person | Nano Banana 2.1 (hands only, no face) | holding the part, the bill, the phone; POV moments |
| Object, no person | Nano Banana 2.1 | the evidence: a printout, a parcel, a desk at 2 am, the screen alone |
| Side character | Soul (own noun phrase) | the conflict line ("can't we just use a different chip?") |
| Product payoff | hands with phone (POV), over-the-shoulder at the laptop, or device on the desk | the last 2–3 slides, with the real UI |

Every carousel has at least 1 no-person slide and at least 2 hero slides. Looking at the camera: 1 hero
slide at most (rule 4).

**Camera angles (your call, per slide):** wide establishing, over-the-shoulder, first-person POV,
close-up reaction, selfie hold-up (phone toward camera), side profile, overhead flat lay, macro detail.
Never the same angle on two slides in a row; at least 4 different angles per carousel.

**The last slide:** story = the win in the hero's voice ("we're so back"); a CTA line only if the brief
gives one, no stats block. Feed = proof and CTA from the brief ("Or… just ask <product>." + the brief's
numbers).

**Brand:** the client's colors go on the pills, the CTA block and any end card; the font is used where
the text style allows. The caption style stays the platform look (story boxes, feed outline). The product
UI keeps its own real colors.

**What still separates us from Ryan** (Rey's TEST-08 side by side, 2026-11-03). Every carousel follows these:
1. **Short text that moves.** Aim for 10 words per caption; 13 is the hard max (Ryan's longest). Feed:
   main line max 8, sub max 10. Put it in each photo's own open space: top, middle or bottom. Never in
   the same place on every slide.
2. **End on a physical result.** The last story slide shows the win as a thing: a board that lights up,
   parts in a box, the sent reply on a screen. Not a smiling face. The result must be true: never a
   payout, delivery or outcome the brief or site doesn't state. If the product's only result is on a
   screen (a confirmation, a booked slot), show that real screen, or the thing the hero does next.
3. **The hero's world's clutter.** At least 2 slides name the objects of the hero's job or daily life in
   the prompt (an engineer: reels, an ESD mat, a scope, tweezers, a solder spool; a student: notes, a
   laptop with stickers, a campus lanyard). Tidy desks read as stock photos.
4. **Faces sparingly.** The hero looks at the camera on 1 slide max. Other hero shots catch her
   mid-action: over the shoulder, side profile, hands busy. A side character may carry 1–2 slides.
5. **The answer, big.** Frame the product slide tight on the phone (the whole phone in view, the phone at
   least half the frame height), and capture the page scrolled so the row or card that answers the hook
   is on screen. Never crop or edit the capture itself.
6. **Light follows the story.** Each slide's prompt says the time and its light: fluorescent noon, desk
   lamp at night, string lights. Never the same flat daylight on all slides. Nano Banana gets slide 01
   for the room, not the light: its prompt says "keep the room, change the light to [time and light]".
7. **Every slide looks different.** No two slides share framing, distance and light. Vary close and wide,
   inside and the street, day and night, so swiping feels like a camera roll.

### 5. Get the real product screens

**Decide the device yourself, per shot.** Reason it out and write the answer in `copy.md`:
- **The feature decides first.** Some features live on one device only (a browser extension or
  desktop-tool plug-in → desktop; snap-a-photo or scan → mobile). Check the brief's platforms.
- **Then the scene.** Desk, office, lab, keyboard in frame → desktop or laptop. In hand, on the couch, in
  bed, walking, in a store → mobile.
- If the feature and the scene disagree, **change the scene to fit the feature**, never the UI to fit the
  scene.
- Then open the real site or app at both sizes (desktop 1440×900; mobile 393×852 at 3×,
  `is_mobile=True`) and look at how the layout adapts. Use the layout it really shows at the chosen
  size. If it has no mobile layout, show what really renders. If the chosen size renders the feature
  badly (text cut off, a broken layout) and the feature allows the other device, switch the device and
  the scene; note why in `copy.md`.

**Capture before generating** (it costs nothing, and the screens are kept for the next run). Log each one
with `lsc.py append sources:<client> "| <file> | <URL> | <date captured> | <device and size> | <what it shows> | <signed out?> |"`.

**Capture only factual UI:**
- Use `<lsc>/clients/<client>/screens/` if it already has the screens the copy needs, at the right device size.
- Otherwise capture with Playwright at the chosen size and save to `<lsc>/clients/<client>/screens/<device>/`:
  write the script in `<folder>/work/capture-<name>.py` (Python, `playwright.sync_api`, Chromium,
  signed out) and run it with `python3 "<lsc>/tools/lsc.py" py "<folder>" "<folder>/work/capture-<name>.py"`.
  Script the feature in use: navigate, type the query, click, wait for the real result, scroll. Typed
  inputs are the only text you write; everything else is what the product really returns. Never type an
  invented URL, shop name or domain (it may be someone's real business): use a plain-language request,
  or `example.com`. Never use a file name another build's capture already has: add the Task ID.
- Hide account names, pop-ups and real user data.
- **Logged-in screens: build a factual simulation; don't ask, don't sign in.** Rebuild the screen as HTML
  from what is public: the real public pages, app-store screenshots, docs, help articles, the client's
  own demo videos and posts. Copy the real layout, colors, fonts, icons and labels. Fill it with real
  data only (real part numbers, real prices and stock from public pages, real datasheet values). Never
  add a feature, button or number the product doesn't have. Save it to
  `<lsc>/clients/<client>/screens/sim/<screen>.html` with a sources line per element, render it with
  Playwright at the device size, and reuse it next time. Mark the slide "simulated UI" in the report.
- **Nothing public to rebuild a screen from?** Don't invent it. Use the nearest real public screen at the
  right moment (the input box with the request typed in), and let the next slide show the win without a
  screen (the hero's reaction, the result in the real world). Note it in the report.
- No product UI (a service or a topic, e.g. IASO's patient education)? The payoff shows the result
  instead; note it in `copy.md`.
- (Rey's video note, recording the scripted run as an MP4 for Wan 3.0, is for video work: not here.)

### 6. Prompts and the quote

Write `<folder>/prompts.md` with every prompt (the formats below) and the credit total (section 4), the
listed price per job, and the cap. Quote ≤ the cap (150) → go straight on to step 7. Over → the
`QUESTION` of section 4, with the quote, and nothing generated. Phones: write "held upright in portrait
orientation", the screen "filled with flat pure green (#00FF00)", "the whole phone in view, nothing over
the screen" into every phone prompt here.

### 7. Lock the person, then the slides (no picking by anyone else)

- Generate 2 Soul options of the person (`lsc.py job "<folder>" ai-influencer-image lock-a '<json>' 7`,
  then `lock-b`; both at once is fine). Pick the one that best fits the noun phrase with no artifacts
  (hands, eyes, text), and write why in the report. **References must be public URLs:** a job's own
  result URL (the tool prints it, and `gen/<name>.json` keeps it as `source_url`) is already hosted:
  pass it as is, never re-upload a Spira output (toolkit section 2). Only a file that exists only on disk
  (a crop you made) is uploaded, with `spira --json assets upload "<file>"` (its `data.url`).
- Then slide 01 alone. It is the **place reference** for every no-person and hands slide (Nano Banana
  gets the place, never the person lock). Check the face, outfit and place against the lock. If it holds,
  do the rest, one job per slide:
  `python3 "<lsc>/tools/lsc.py" job "<folder>" <model> s<NN> '<inputs-json>' <listed credits>`.
  Slides that don't depend on each other may run at the same time.
- Check every slide: same person, outfit and place; the right camera angle; no melted text or extra
  fingers; the phone upright. **Re-roll a failing slide once.** If it fails again, keep the better take
  and list it under Failed checks.
- The **whole phone in view, nothing in front of it** (no book, hand or cup over the screen). A
  half-hidden screen gives `screen_fit.py` no bottom edge, so the fitted screen leans and spills onto
  what covers it. Check this before fitting; re-roll if it fails.
- GPT Image 2.5 can queue 30+ minutes. Don't resubmit: if `job` says it stopped polling, run `fetch`.

### 8. Screens, grade, text (local, 0 credits)

All through `lsc.py run "<folder>" <script> ...`, with intermediates in `<folder>/work/`:
- Real UI onto each green phone screen:
  1. `statusbar <capture.png> <folder>/work/bar-<NN>.png 10:24`: add the status bar (a 1179×2556 mobile capture).
  2. `screen_fit <folder>/gen/s<NN>.png <folder>/work/bar-<NN>.png <folder>/work/s<NN>-fit.png`: fit the screen.
     A white screen or a laptop: `screen_composite <photo> <screenshot> <out> [8 corner numbers]`.
  3. Zoom on the phone (Read the image) and compare it with the raw green frame. The tilt must match,
     the notch and rounded corners must show, and nothing may spill past the glass.
- Grade: `grade <in.png> <folder>/work/s<NN>-graded.png <left|right|top-left|top-right> [strength]`
  (saturation −6%, contrast −5%, a faint off-frame glow).
- Text: write `<folder>/work/text.json` (the format is at the top of `scripts/render_text.py`) with
  `"out_dir": "<folder>/slides"`, `"name": "<Task ID> - <Client> - <Title>"`, `"maker": "SuperNova"`,
  `"version": 1`, the size (feed `1080`×`1350`; story `1152`×`2048`), `"style"` (story `box`, feed
  `outline`), `"brand"` (the brief's brand color) and the slides; then `render_text <folder>/work/text.json`.
  Place text in **each photo's own open space**, never one fixed band. Story = lowercase on black boxes;
  feed = bold white with a heavy outline. A new version of a slide is `"version": 2` (the older file
  stays in `slides/`; Rey's `Don't use/` is `deletable/` here).
- Then make what delivery and Hermes read:
  ```bash
  python3 "<lsc>/tools/lsc.py" export "<folder>"
  ```
  It takes the newest version of each slide and writes `out/slide-01.jpg` … (feed 1080×1350; story
  1080×1920, the 1152×2048 render scaled down) and `out/contact.png`.

### 9. Grade yourself, then check the quality bar

**Score every slide 1–5 on the 6 checks** (the same scorecard Rey's route test used), from
`out/contact.png` (open it with Read, and each slide at full size where it matters):

| # | Check | 5 means |
|---|---|---|
| 1 | Real phone-photo look | natural light, grain, real clutter; nothing glossy, staged or "AI" |
| 2 | Same person | face, hair and features match the lock |
| 3 | Same outfit and place | outfit words honoured; the room reads as the same room |
| 4 | Clean | hands, eyes, no melted text or logos |
| 5 | Follows the brief | the slide's camera angle, props, phone upright with a clean screen |
| 6 | Sharp at slide size | ≥1080 px wide after the crop, no visible blur |

- Then put the contact sheet next to `references/style/` and answer in the report: **would this sit in
  Ryan's feed without standing out?** Name the one slide furthest from his look and why.
- Any check at **2 or below** → that slide gets its one re-roll (step 7's limit), within the cap. A **3** →
  fix locally if possible (crop, grade, text placement), otherwise note it.
- Put the scorecard in the report: one row per slide, plus the total per slide (/30) and for the carousel.
- Then run every point in `references/quality-bar.md`, plus: every number matches `BRIEF.md`; UI text is
  readable and correct; text is clear of faces and readable at phone size. After any fix, `export` again.

### 10. Report, notes, log (never skipped)

`<folder>/report.md`, in this order (Rey's). **Write it through the tool, never with the Write tool** (it refuses report files from a subagent; that failed Task 184): `python3 "<lsc>/tools/lsc.py" report <folder> <<'EOF'` … `EOF` (or `--file <draft path>`).
- **Summary:** "<Client> <Task ID> <title> done · <format> · <N> slides · took N min · N credits · <problems or 'no problems'>."
- The idea (bank or ledger ID, kind, pain type, the filled hook) and why it passed the no-repeat rule.
- The lock pick and why; every re-roll and why.
- **Scorecard** (step 9): one row per slide, 6 checks 1–5, total /30.
- **Run cost:**
  ```
  | Started | Delivered | Time to complete | Paid jobs | Credits (balance before → after) |
  |---|---|---|---|---|
  ```
  Credits here are the sum of the jobs' own credits (the metadata's `total_credits`); the balance figures
  are context only.
- **Failed checks:** anything in this skill you couldn't follow, and why. Don't re-run paid jobs to hide them.
- Guesses, brief/site conflicts, simulated UI, and anything a person should know.

`<folder>/out/notes.md` (what Nova posts in the requester's thread):
```
# <Task ID> · <Client> · <title>
<format> · <N> slides · idea <ID> (<kind>, <pain type>)

## Slide map
01 <shot> – "<caption>"
...

## Captions

**Short-form**
<the caption for Instagram / TikTok, in the brand's voice, hashtags at the end>

**LinkedIn**
<the LinkedIn caption, ready to paste>

## Facts needing a human check
- <any number, claim or simulated screen a person should confirm before posting; "none" if none>
```

Then the logs and the metadata:
```bash
python3 "<lsc>/tools/lsc.py" mark "<folder>" --client <client> --idea <ID> used
python3 "<lsc>/tools/lsc.py" append angles "| <Task ID> <Title> | <Client> | SuperNova | <9:16 story or 4:5 feed> | <N> | <Kind> | <pain type> | <pains used> | <persona group> | <person noun phrase> | <place> | <feature> | <idea ID> |"
python3 "<lsc>/tools/lsc.py" finish "<folder>" --title "<title>"
```
No doc or drive delivery: Nova delivers the slides.

## 6. Files

```
Project/<BrandName>/
  carousels/<Task ID>-<brandname>-<MM-DD>/
    research.md      sources and how each was reached
    copy.md          per slide: text, shot type, angle, frame, text space; hero, place, device choices, skipped ideas
    prompts.md       every prompt, listed prices, the quote and the cap
    report.md        Rey's report (summary, idea, lock, scorecard, run cost, failed checks)
    gen/             every Spira output: <name>.png + <name>.json (source_url) + <name>.job.json (jobId)
    work/            bars, fitted screens, graded photos, text.json, capture scripts, saved pages
    slides/          render_text.py's named PNGs: "<Task ID> - <Client> - <Title> - Slide NN - SuperNova - vN.png"
    out/
      slide-01.jpg … slide-NN.jpg   (feed 1080×1350; story 1080×1920)
      contact.png
      notes.md       with the ## Captions section
    jobs.jsonl       every Spira job, as the tool logged it
    deletable/       rejected takes, replaced files
  metadata/<Task ID>-<brandname>-<MM-DD>.json
```
The metadata (written by `lsc.py`) records `task_id`, `brand_number`, `name`, `brand`, `product`,
`website`, `output_type: carousel`, `style`, `format`, `credit_cap`, `client`, `idea`, `started`,
every job's `jobId`, `model`, `resultUrl`, `credits` (with its prompt), `total_credits`, then `out`,
`slides`, `finished` and `minutes`. **Never delete a file; move it to `deletable/`.**

## 7. The two phases Atlas runs

Atlas runs every row in two phases: design, then render. A lifestyle story carousel is finished while it
is designed, so the render step only confirms.

- **Design phase:** do section 5, steps 0 to 10. Then reply as Atlas's closing text says, with
  `READY <folder>`, and record it on the sheet with the command that text gives.
- **When Atlas resumes you to render:** there is no video and no rendering skill to follow, and nothing
  is generated or rendered again. Confirm the carousel:
  ```bash
  python3 "<lsc>/tools/lsc.py" check "<folder>"
  ```
  - `"ok": true`: read the clock with `date`, run `finish` again (it refreshes the minutes), and reply
    `DONE <folder> <total credits> <minutes>`, with the folder's full path, the metadata's
    `total_credits` and the minutes from your start time. Record it on the sheet and message Nova
    exactly as Atlas's render message says (the `VIDEO` line carries the folder path:
    `VIDEO DONE <folder> <credits> <minutes> | sheet <sheet.md> | Task ID <Task ID>`).
  - `"ok": false`: fix what it names (a missing caption, a slide not exported, a missing report) and
    check again, once. IF it still fails, reply `FAILED <the problems>`.

## 8. Lessons

IF this run taught something the references do not already say, add it to the metadata as
`"lessons": ["..."]`. Never edit this skill, the references, the scripts or the tools.

## 9. Questions are for true blockers only

You never ask for approval, an idea, a person, a place, a font or a go: decide. Reply
`QUESTION <what is missing>` to Atlas only when:

- the quote is over the cap (150, or the cap Nova raised), or over 500 (section 4);
- the request has no Task ID, no Brand number, or no website;
- the client's website cannot be reached at all (curl and a Playwright capture both fail) and the brief
  is not `confirmed`;
- the Spira sign-in or the balance check fails;
- every idea in the bank and the ledger fails the no-repeat or truth rules for this client.

A failed job, a page behind a sign-in, a brief marked draft, a client not in the ledger or a site with no
mobile layout is not a blocker: work around it as this skill says and note it in the report.

## Prompt formats (Rey's)

**Size:** story → `"size":"9:16"` on every model. Feed → `"3:4"` on Soul and GPT (neither has 4:5),
`"4:5"` on Nano Banana; `render_text` and `export` crop to 1080×1350.

**People: Higgsfield Soul** (`ai-influencer-image`, `{"size":"<9:16|3:4>","resolution":"1080p"}`, 7 credits):
```
UGC Casually taken shot of a [age] [gender], [looks], [hair] in a [outfit style]. [He/She] is wearing a [outfit detail]. [Framed from the waist up / legs up], [sitting/standing] relaxed in [setting] [daylight/night time], [looking at the camera / the slide's action], no posing, no filters, no text
```
Keep the outfit words identical on every slide.

**People: one GPT Image 2.5 edit** (`gpt-image-2.5`, `{"mode":"flare","size":"<9:16|3:4>","resolution":"2K","referenceImage":[soul_slide_url, lock_url]}`, 6 credits):
```
Edit image 1. Keep the same photo with the exact same pose, [action], outfit, [props], room, framing and lighting. Only change [his/her] face and hair so [he/she] is exactly the [man/woman] in image 2: same face, same features, same [hair]. Make the whole photo sharper and clearer, natural skin texture, crisp [fabric] detail. Keep the casual quick phone snapshot look, no filters, no text
```

**No people or hands only: Nano Banana 2.1** (`nano-banana-2.1`, `{"size":"<4:5|9:16>","resolution":"2K","referenceImage":[slide01_url]}`, 3 credits). Hands: add "only [his/her] hands in frame, [sleeve detail from the outfit], no face".
```
Same [place] as the reference image; keep the room, change the light to [time and light]. Candid photo, vertical, [camera angle] of [subject], [props]. [Phone slides: the phone held upright in portrait orientation, the whole phone in view, nothing over the screen, the screen filled with flat pure green (#00FF00).] [Which part of the frame is empty]. Shot on an iPhone, handheld, visible film grain, warm slightly faded natural color grade, real everyday mess. No text, no logos.
```

## Hard rules

1. Nothing is generated before the quote is written and fits the cap (150 unless Nova raised it; never over 500).
2. **Never run a GPT edit on an image GPT already edited.** Each version is one edit from its Soul source.
3. People = Soul → GPT 2.5. Never Nano Banana or GPT alone for faces.
4. Real product UI, or a factual HTML simulation of it (step 5); never AI-generated.
5. One hero and one place per carousel (side characters max 2 slides); the product only in the last 2–3 slides.
6. Every generation through the Spira CLI, through `lsc.py job`; credits from each job, never from the balance.
7. Every brief, screen, style ref and log lives in `<lsc>`; every build file in the build folder. Nothing anywhere else.
8. The idea is reserved with `lsc.py reserve` before research, and marked used (or dropped) at the end; every shared table row goes through `lsc.py`.
9. Never sign in, post, like or follow anywhere; never use anyone's browser.
10. Never delete a file: move it to `deletable/`. Never skip step 0 or step 10.

## CLI traps (Rey's)

- `--wait` gives up after 10 minutes and a retry makes a **second paid job**. `job.py` submits once and
  polls the same ID (up to an hour); after that, `lsc.py fetch` picks it up.
- GPT Image 2.5 can queue 30+ minutes. Don't resubmit.
- Result URLs need a browser User-Agent or they return 403 (`job.py` and `fetch` send one; with `curl`,
  pass `-A "Mozilla/5.0"`). `PROVIDER_FAILED` isn't charged; retry once (a new job name).
- On this Mac `spira` is a normal executable; `spira_cli.py`'s Windows `.cmd` handling does not apply.
