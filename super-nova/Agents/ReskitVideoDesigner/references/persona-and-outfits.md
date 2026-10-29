# Persona and outfits

The persona is the brand's recurring face. Viewers recognise her or him across videos, so
identity must hold perfectly while the look changes every time. The source creator's face or
likeness is **never** used: the person on screen is always recast (the owner's rule, 2026-10-24).

The Avatar Designer is the one source of personas (the owner's rule). Everything below follows
its method (`Agents/AvatarDesigner/skills/avatar-designer.md`) and the shared prompting and
toolkit skills; Re-skit only adds the character sheet and the outfits on top.

All persona files live in `Agents/NovaOM/client-assets/<BrandName>/personas/<Name>/`
(file-management.md), never in `Project/`.

## 1. Which persona

1. **The request gives one** (`Use this avatar image: <path or URL>`): that is the persona.
   Never make another beside it, and never run Soul to "match" it.
   - Look in `client-assets/<BrandName>/personas/` for a folder whose `source/` holds that image
     (or a sheet made from it). If there is one, use its `sheet_4k.png` and its `outfits.md`.
   - Otherwise register it: make `personas/<Name>/` (the name from the request or the file name;
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
   so fix the prompt rather than generating a batch to pick from.
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
  (`node <reskit>/tools/render_html.js sheet.html sheet_4k.png 3840 2160 1`). Keep every panel
  at or below its photo's native resolution where possible.

Resolution matters: a sheet assembled from small panels gives the video model little facial
detail, and close-ups suffer first. Save it as `personas/<Name>/sheet_4k.png` and start an empty
`outfits.md` (section 5).

## 4. Outfits: decided first, never repeated

Every video starts its visual work by choosing and generating the outfit. Nothing else that
shows the persona (plates with her, clips, b-roll featuring her) is generated before the outfit
exists and has been checked, because every later reference carries it.

**Choosing.** The outfit fits the scene (lounging at home, a night out, a café, a commute) and
the brand's voice; contrasts clearly with what the source performer wears, so the result never
reads as a copy; and contrasts with the background so the persona separates from the room.
Read the persona's whole `outfits.md` first: an outfit, or a near-variant of one (same garment
type in the same colour), that appeared in any previous video is not used again. Colours and
garment types already used are off the table for the main pieces.

**Generating.** One GPT Image 2 edit of the persona's **original** `sheet_4k.png`, `16:9`, `4K`.
Never edit an earlier outfit sheet: each edit softens identity a little, and chained edits drift
into a different person. The prompt has three parts:

1. What stays: "Edit this character sheet. Keep the same person in every panel with the exact
   same face, hair, expression, skin, body shape and size, pose, camera angle and framing, and
   keep the same seven-panel layout, the black borders, the plain light-grey studio backdrop and
   the name label." Name the accessories that stay.
2. What changes, and only that: "Only change the outfit, identically in every panel: …",
   described concretely (garments, colours, fabric, fit), plus footwear for the full-body panels.
3. "Keep the clean photographic look of the sheet, no other text."

The outfit job is `"hold": true` in the chain: when it lands, look at it (face, hair and body
match the original sheet in every panel; the outfit is identical across panels), then
set `"approved": true` on it in `chain.json`. Only then do you submit the clips. A failed
check is a redo with a tighter prompt (at most 2 extra).

Save the approved sheet in `personas/<Name>/outfits/<YYYY-MM-DD>_<short-outfit-name>.png`
(copy it from the video's `assets/`, where `wait_ai_job` saved it) and append it to the ledger.

## 5. The ledger

`personas/<Name>/outfits.md`, newest last:

```
| Date | Video | Outfit (exact description) | Sheet file |
|---|---|---|---|
| 2026-10-19 | CookiyLabs 14-cookiylabs-10-19 | oversized dusty-lilac crewneck sweatshirt, light-grey jersey lounge shorts | outfits/2026-10-19_lilac-sweatshirt.png |
```

The Video column is `<BrandName> <video name>`, so the row points back to its metadata.
