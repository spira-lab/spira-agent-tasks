# Persona and outfits

The persona is the brand's recurring face. Viewers recognise her or him across videos, so
identity must hold perfectly while the look changes every time. The source creator's face or
likeness is **never** used: the person on screen is always recast (the owner's rule, 2026-10-24).

The Avatar Designer is the one source of personas (the owner's rule). Everything below follows
its method (`Agents/AvatarDesigner/skills/avatar-designer.md`) and the shared prompting and
toolkit skills; Re-skit only adds the character sheet and the outfits on top.

All persona files live in `Agents/VegaOM/client-assets/<BrandName>/personas/<Name>/`
(file-management.md), never in `Project/`.

**Other designers work at the same time** (up to 4, 2026-11-12), and may be making a video of
the same brand. So:
- A persona folder you make **new** is named `personas/<Name>-t<Task ID>/` (e.g. `Mia-t291/`),
  so two designers registering one at once never write into the same folder. An existing
  folder keeps its name, whatever it is.
- Before making a new persona or a new `voice.md`, look in `personas/` again: one may have
  appeared since you last looked (another designer's `-t` folder made for the same image or
  brand). Reuse it when it fits.
- Append to `outfits.md` only with
  `python3 <shared>/tools/brand-lock.py append <persona>/outfits.md @<textfile>`, and write a new
  `voice.md` inside `python3 <shared>/tools/brand-lock.py <BrandName> -- bash -c "<command>"`,
  checking first that it is still missing.

## 1. Which persona

First read the Design approach in `Agents/DesignerShared/skills/working-memory.md`: an entry
there about personas (e.g. a new persona for every video) wins over the steps below.

1. **The request gives one** (`Use this avatar image: <path or URL>`): that is the persona.
   Never make another beside it, and never run Soul to "match" it.
   - Look in `client-assets/<BrandName>/personas/` for a folder whose `source/` holds that image
     (or a sheet made from it). If there is one, use its `sheet_4k.png` and its `outfits.md`.
   - Otherwise register it: make `personas/<Name>-t<Task ID>/` (the name from the request or the file name;
     a first name that fits the brand when there is none), copy the image into `source/`, and
     build the sheet from it (section 3).
2. **None is given, but the brand already has a persona** in `client-assets/<BrandName>/personas/`:
   use it (the most recently used one when there are several, from the ledgers' last dates).
3. **None at all:** make one by the Avatar Designer's method, then the sheet (section 2).

## 2. Making a persona (the Avatar Designer's method)

Read `prompting.md` sections 1–3 and `toolkit.md` 3a–3b. Then:

1. **Decide the person** in one line: an explicit adult age, a look and nationality chosen for
   the brand's audience and language, gender, one vibe word that matches the brand's energy.
   Choose decisively (never "or"). Write it in the plan.
2. **Base likeness:** one Soul job (`ai-influencer-image`, `9:16`, `1080p`) in the prompting
   skill's Soul format, framed for the widest shot you will ever need: **full body, standing
   relaxed, hands empty at the sides**, a plain lived-in room in daylight, looking at the camera.
   Everyday words, no lens or lighting words. One image; a second image is a different person,
   so fix the prompt rather than generating a batch to pick from. **Outfit: the kind only**
   (the owner's rule, 2026-10-30; section 4): in the Soul format's outfit slot write only the
   general kind of attire (e.g. "in a casual home outfit"), never a garment or a colour, and
   leave out its "is wearing a [outfit detail]" sentence.
3. **Clean-up edit:** one GPT Image 2 job (`9:16`, `2K`) in the persona-edit format, the Soul
   result as `referenceImage`.
4. **Check** it as the Avatar Designer does: the person decided, sharp face, no artefacts or
   distorted hands, no text. At most 2 extra generations in all.

Put these jobs in the chain like any other (they are its first jobs, and the sheet needs them),
save the base and the edit in `personas/<Name>/source/`, and record them in the video's metadata.

## 3. The character sheet

The best reference for a video model is a **character sheet**: one 16:9 image with seven views
of the same person on a plain backdrop. A large three-quarter waist-up view on the left; three
headshots (three-quarter, front, profile) across the top right; three full-body views
(three-quarter, front, side) across the bottom right; a name label underneath; black borders,
plain light-grey backdrop.

- **From one image** (the usual case): one GPT Image 2 edit of the persona image into the
  layout above, `16:9`, `4K`: "the same person in every panel, plain light-grey studio
  backdrop, black borders, name label <Name>". Mark it `"hold": true` in the chain and check
  every panel for identity, body shape and proportions before anything uses it. If a panel
  drifts, redo the sheet from the persona image with a tighter prompt; never patch a sheet from
  another edit.
- **From several real photos of the person** (when the brand provides them): no generation.
  Copy `tools/sheet_template.html` into the persona folder as `sheet.html`, set the seven
  `src` attributes and the name, and render it at 3840x2160
  (`python3 <shared>/tools/heavy-slot.py <Task ID> -- node <reskit>/tools/render_html.js sheet.html sheet_4k.png 3840 2160 1`). Keep every panel
  at or below its photo's native resolution where possible.

Resolution matters: a sheet assembled from small panels gives the video model little facial
detail, and close-ups suffer first. Save it as `personas/<Name>/sheet_4k.png` and start an empty
`outfits.md` (section 5).

Sheets made before this layout was settled may have another arrangement (more panels, no borders,
no name label). Use them as they are, and word the outfit prompt for the layout the sheet actually
has; never remake a persona's sheet just to match.

## 4. Outfits: decided first, never repeated

Every video starts its visual work by choosing and generating the outfit. Nothing else that
shows the persona (plates with her, clips, b-roll featuring her) is generated before the outfit
exists and has been checked, because every later reference carries it.

**Choosing: the kind of attire only, never the garment or the colour** (the owner's rule,
2026-10-30). Decide only the general kind the scene and the brand's voice call for: a home
outfit, lounge wear, office wear, gym wear, going-out clothes, a café look. Never decide or
write an exact garment (sweatshirt, cardigan, blazer, crop top, ...), a colour, a fabric or a
fit, in this prompt or any other: the image model interprets the kind and picks its own pieces
and colours. Choosing them ourselves kept landing on the same few colours (mint green, olive
green, orange-brown) video after video. Read the persona's whole `outfits.md` first: when the
latest entries share a kind, pick another kind where the scene allows it.

**Generating.** One GPT Image 2 edit of the persona's **original** `sheet_4k.png`, `16:9`, `4K`.
Never edit an earlier outfit sheet: each edit softens identity a little, and chained edits drift
into a different person. The prompt has three parts:

1. What stays: "Edit this character sheet. Keep the same person in every panel with the exact
   same face, hair, expression, skin, body shape and size, pose, camera angle and framing, and
   keep the same seven-panel layout, the black borders, the plain light-grey studio backdrop and
   the name label." Name the accessories that stay.
2. What changes, and only that: "Only change the outfit, identically in every panel, to a
   <kind of attire, e.g. casual home outfit>, with matching footwear in the full-body panels."
   Nothing more: no garments, colours, fabric or fit. The model chooses them.
3. "Keep the clean photographic look of the sheet, no other text."

The outfit job is `"hold": true` in the chain: when it lands, look at it (face, hair and body
match the original sheet in every panel; the outfit is identical across panels and reads as the
kind asked for; it is not a near-copy of an outfit in the ledger or of what the source performer
wears; it stands out from the setting; and nothing on it carries another company's logo or mark,
shoes included, since the clips copy it faithfully), then set `"approved": true` on it in
`chain.json`. Only then do you submit the clips. A failed check is a redo (at most 2 extra) with
the same kind-only prompt, or another kind; tightening the prompt never means adding a garment
or a colour.

Save the approved sheet in `personas/<Name>/outfits/<YYYY-MM-DD>_<short-outfit-name>.png`
(copy it from the video's `assets/`, where `wait_ai_job` saved it) and append it to the ledger.

## 4a. The voice

When a video re-voices or adds speech, the persona speaks in a voice Wan 3.0 generates from words.
So she sounds the same across videos, her voice is written once and kept:
`personas/<Name>/voice.md`, one sentence in plain words: an explicit adult age, nationality and
accent, pitch, and the voice's texture. Write it the first time she speaks, choosing what suits her look and the
brand's audience, and never change it. Each clip adds only the delivery the scene needs (deadpan,
excited, sighing) after it. Never base it on the source performer's voice, and never send that
voice to the model.

## 5. The ledger

`personas/<Name>/outfits.md`, newest last:

```
| Date | Video | Outfit (exact description) | Sheet file |
|---|---|---|---|
| 2026-10-19 | CookiyLabs 14-cookiylabs-10-19 | oversized dusty-lilac crewneck sweatshirt, light-grey jersey lounge shorts | outfits/2026-10-19_lilac-sweatshirt.png |
```

The Video column is `<BrandName> <video name>`, so the row points back to its metadata. The
Outfit column records the kind asked for and what the model made, so the next check can spot a
repeat. It is a record only: never copy it into a prompt.
