# Brand truth and text

Text is where a skit becomes the brand's. It is also where a video can quietly start lying.
This file is the logic for changing text without drifting.

## The brand-truth file

Each brand has one truth file, `Agents/VegaOM/client-assets/<BrandName>/brand/truth.md`, and
each video adds to it what it needs (read it first; earlier videos may already hold what you
need, but re-check any row older than 30 days that your story leans on). Every entry is a fact
with its source and the date it was checked:

```
| Fact | Exact wording / number | Source | Checked |
|---|---|---|---|
| Free plan includes 3 exports per day | "3 free exports daily" | brand pricing page URL | 2026-01-15 |
| Bestselling product | "Cloud Runner", 12.4k reviews | brand store page URL | 2026-01-15 |
| The brand has no live chat support | absent from site, help centre, app UI text | site + app strings | 2026-01-15 |
```

Other designers may be working on the same brand at the same time. Add rows only with
`python3 <shared>/tools/brand-lock.py append <truth.md> @<textfile>`; an in-place edit of a row
(a re-check), and a new capture into `brand/ui/`, go inside
`python3 <shared>/tools/brand-lock.py <BrandName> -- <command>`, reading the file again first.

**Sources, in order of trust:**
1. Material the request provides (product image, logo, screenshots, files named in the
   instructions). It always wins.
2. The brand's DNA (`Brand DNA: <path>` in the instructions; `reskit.py dna` fetches it).
3. The brand's own product: its site, store listing, app, in-product text. Capture it yourself
   with `node <reskit>/tools/capture_site.js <url> <client-assets>/<BrandName>/brand/ui/<YYYY-MM-DD>`
   (screenshots, logo candidates, colours, the page text).
4. Reputable reporting, for outside events only.

Record what the brand does **not** have, too, when the skit tempts you to imply it.

Outside events that the hook depends on (a competitor's news, a trend, a launch) are verified
with a fresh search, recorded with the exact status and date, and worded to match that status.
"Filed for bankruptcy and will shut down if no buyer is found" is not "is shutting down"; the
honest hook is "might be shutting down". Nothing you cannot verify goes on screen; note it in
the metadata's `unverified`.

## Changing text without drifting

**Start from the source's form, not from a blank page.** The source's caption has a format
("pov: that friend who…"), a length, a register and a position on screen. The new caption keeps
that form and changes the content. The same goes for the spoken lines: keep the line's job in
the scene (a complaint, a reveal, a deflection) and give it a true brand meaning, through cuts
and overlays, or by re-voicing it: new words with the same job, the same length and the same
rhythm, aimed at the brand's message.

**Re-voiced and added lines are claims too.** A spoken line is held to the same rule as an
overlay: every factual phrase in it points to a row in `truth.md`, recorded in the dialogue
script. Write it the way the source person talks (their register, their slang, their deadpan or
their excitement), not the way an ad talks: the persona is a person describing her life, not a
narrator reading features. One brand point per line; the joke or the turn carries it.

**Write in the market's language.** The instructions name the language and market; captions,
pop-ups and simulated content are written in it. Kept source speech stays as it is; re-voiced and
added lines are written in the market's language.

**Every claim traces to the truth file.** Before an overlay is rendered, each factual phrase in
it must point to a row in `truth.md` (put the row in the keep/cut/rewrite table). Opinions and
jokes are fine ("it's even better", "he REMEMBERED 😭") as long as the thing they react to is
real. If no row supports a claim, rewrite the line or drop it.

**When the footage implies something untrue, reframe the text, don't bend the fact.** If the
source person raises a phone to her ear and the brand has no calls, the text says what she is
really doing in the brand's world ("voice chatting", if voice messages exist). If a line
mentions a platform, a competitor or a name that isn't part of the brand's world, cut the word
at its word boundaries rather than redefining it on screen.

**Simulated content stays inside the brand's reality.** Chat messages, notifications and lists
shown in b-roll can be written fresh, but only with features, names and numbers that exist.
Character names, counts, tags and descriptions come from the brand's real catalogue. A message's
style copies how the product really writes (for example narration in italics and dialogue in
bold, if that is how the product's replies look).

**The story must be a believable situation for a real customer.** Exaggeration is the joke;
deception isn't. A simulated conversation should be the kind of thing that makes a customer
react the way the source's person reacts. If it would make a customer quit the product instead
(an AI that is rude rather than teasing, a product that fails), rewrite it.

**Other companies are not named by default.** Naming a competitor and saying something about
it is a legal question. Use the unnamed version ("the app I've used for years"). Name one only
when the instructions explicitly ask for it, and then record the claim and its source in the
metadata's `risks` so Vega can flag it.

**No brand names inside generated speech or song lyrics.** Generators mispronounce them. The
brand name goes on screen. (For any other hard word in a line Wan will say, the shared Reword
table in `DesignerShared/skills/working-memory.md` gives spellings that are said right; the
on-screen text keeps the real spelling.)

## Overlay style

- **No boxes or containers.** Plain text: white, a soft dark edge or shadow for captions, a
  heavy dark outline for pop-up stickers. Small enough to look native, not like an ad.
- **The caption** (`tools/caption.html`) copies the source caption's style and position (often
  mid-frame), with balanced line breaks (`text-wrap: balance`) so no word sits alone on the
  last line.
- **Pop-ups** (`tools/popup.html`) are the commentary voice: short, lowercase, one punchline
  each, a slight tilt and a three-frame pop-in. Each one lands on the exact word it reacts to
  (take the time from `source/timings.json`) and holds until the moment passes or the shot cuts.
- **Text beats** (`tools/beat.html`) that replace the source's own caption moments (for example a
  two-part setup over a reaction) use the source's caption style at the same height.
- Render every overlay from its HTML (`render_html.js`, several at once with `--batch` through
  `heavy-slot.py`), and
  keep the HTML beside the PNG in `assets/`, so a text change is a re-render, not a redesign.
- The brand's logo appears only as the real file (from the request, or captured from the
  brand's site), never an emoji or a lookalike. Brand colors from the request win over captured
  ones.

## Safe area

Social platforms cover parts of the frame. In a 1080x1920 frame, keep all text and anything
that must be read out of:
- the **bottom ~20%** (below y 1536): caption, username, music ticker
- the **right column** (x over 940, between y 900 and 1600): like, comment and share buttons
- the **top 150 px**: tabs and status

Check by drawing these zones over frames from the draft (`reskit.py safe <frame> <out>`).
Inside a simulated app screen, place pop-ups in a clear band between UI elements, not over the
reply box or the navigation at the bottom.
