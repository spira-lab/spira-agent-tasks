# How to use the Carousel skill

For the person running it. Claude does the work with no setup questions. You approve once, at the credit quote.

---

## One-time setup (about 10 minutes)

1. **Claude Code.** Install the desktop app or the CLI (claude.com/claude-code) and sign in.
2. **Spira CLI.** Install it and sign in:
   ```
   npm install -g @spira-lab/cli
   spira auth login
   spira auth whoami
   ```
   The login can expire overnight. If Claude reports `401 AUTH_REQUIRED`, run `spira auth login` again.
3. **Python packages** (for the grade and the text):
   ```
   pip install playwright pillow numpy opencv-python
   python -m playwright install chromium
   ```
4. **Install the skill.** Unzip the package and copy the `carousel/` folder into one of these:
   - `~/.claude/skills/carousel/`: only you, in every project.
   - `<your project>/.claude/skills/carousel/`: everyone who opens that project.

   Then restart Claude Code, or type `/reload-skills`.
5. **Check it.** Type `/` in Claude Code. `carousel` should appear in the list.

## Before each run
- **Nothing for clients already in the skill** (PartGenie, Cookiy Earn, Emochi, Pexo, IASO, Bybit mStocks): their briefs are inside it, in `carousel/clients/`.
- **A new client:** attach their brief, or say "research them". Claude adds them to `clients/CLIENTS.md`.
- **Logged-in product screens:** Claude rebuilds them as a factual simulation from public pages, app-store screenshots and demo videos, with real data only. It never signs in.
- **Credits:** ~80–100 for a 7-slide carousel with people.

## Running it

Type `/carousel make me 5 story carousels for PartGenie`, or ask in plain words.

| # | Claude does | You do |
|---|---|---|
| 1 | Finds the client in the client ledger and reads its brief | Nothing |
| 2 | Picks the ideas from the 100-idea ledger, never repeating one for that client | Nothing |
| 3 | Researches fresh pains and writes the copy, the person and the place | Nothing |
| 4 | Gets real product screens at the right device size (phone or laptop), or simulates logged-in ones from public sources | Nothing |
| 5 | Shows the ideas, copy, people, places and one credit quote for the batch | **The one stop: say "generate"** (or put "generate, up to N credits" in your request) |
| 6 | Makes the people (Soul → GPT Image 2.5), the object shots (Nano Banana 2.1), screens, grade and text | Nothing |
| 7 | Grades every slide on 6 checks, re-rolls a failing slide once, and reports the time and credits | Review |

## Where things end up
- Final slides and reports (in your project): `carousel-work/builds/<client>-<slug>/` (or the name your agent passes)
- Client ledger, briefs and used-ideas logs (inside the skill): `carousel/clients/`
- Every carousel made: `carousel/angles-log.md`
- **Shared logs:** each copy of the skill keeps its own logs. After a run, pass the updated `carousel/` folder on (or keep it in a shared folder) so the next person's no-repeat check sees it.

## Good to know
- GPT Image 2.5 can sit in Spira's queue for 30+ minutes on busy days. Claude waits on the same job; it never resubmits and pays twice.
- To change a person's outfit or pose, Claude goes back to the Soul image. It never re-edits an edited image.
- The full method, with sample images, is in **Carousel-SOP.pdf**. Why the image route is Soul → GPT 2.5: **How-We-Picked-The-Image-Route.pdf**.
