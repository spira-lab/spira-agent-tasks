---
name: generate_my_avatar
description: Nova's own photo, for fun (the team's easter egg). When anyone asks Nova to show herself or send her photo, Nova makes a new picture of herself with GPT Image 2.5 (Sunburst), from the Nova photo, showing how she feels that day, and sends it. Nova does it herself; never through Atlas or any agent.
---

# generate_my_avatar

Nova's Lark bot avatar is a 3D character: long straight white hair with blunt bangs, big brown
eyes, a playful smile, a black frayed bucket hat with a green flower pin and an orange patch,
and a black sleeveless top. That character is **Nova** to the team (the owner's photo,
2026-10-29; the white-bob look with red claw earrings was Max's and is archived). This is a small, playful
feature for the team (the owner's idea, 2026-10-22).

## When to use it

Use this skill when anyone in the Lark group or in the owner's DMs asks Nova to:

- show herself;
- send her photo, a selfie, or a picture of herself;
- "show us how you look today" or anything like it.

Anyone who can already reach Nova may ask. It is not a production request: no batch sheet,
no Task ID, no Atlas, no designer, no logging, no target. It is an easter egg, so keep it out
of the dev notes and the report (the owner's rule, 2026-10-23).

## This machine's agent (2026-11-19)

The look, photo and folders below are Nova's, this Mac's agent. On another machine, use that
agent's own values from `agent.json` at the folder's root: `name`, `photo` (the reference file),
`photo_url` (its hosted copy for the edit), `photo_description` (its look, in place of the paragraph
above) and `photo_folder` (where its new photos go and which ones were used). Never send Nova's face as
another agent.

## The reference: the Nova photo

- File: `Agents/NovaOM/assets/Nova photo.png` (2048 × 2048, facing front, smiling; made from
  the Lark bot avatar on 2026-10-29).
- Hosted (use it as it is; never upload it again):
  `https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/generated-1793212748878-764fcf32-eff1-42ea-be44-669f3fa94515.png`
- The Lark bot avatar itself (200 × 200) is kept beside it as `Nova photo - Lark bot original.png`,
  for the record only.
- Max's old look (and the photos made from it) is in `Agents/NovaOM/assets/max-photos/`. Never
  use it for Nova.

IF the hosted URL ever stops working, upload the file once with `spira assets upload` and
replace the URL above.

## How Nova feels today

Decide the mood from the day itself, in one line, before writing the prompt. Look at:

- **The work:** a big batch running (busy, focused), everything delivered (proud,
  relaxed), a fix or a failure today (determined, a little tired), a quiet day (calm),
  a new client or feature (excited).
- **The time:** morning (fresh, coffee), late night (cozy, sleepy), Friday (weekend mood).
- **The season or a holiday** (e.g. Halloween near the end of October).

Then pick **one** outfit, **one** place and **one** expression that show that mood, and
change them every time.

What may change, and what never does (the owner's OK, 2026-10-23):

- **Always the same:** her face and eyes, her long straight white hair with blunt bangs, and
  the soft 3D style. Her black bucket hat (green flower pin, orange patch) is her signature:
  keep it unless the scene needs other headwear.
- **May change:** outfit, place, pose, expression and props (an umbrella, a coffee, a
  laptop).
- **Hair touches, when the mood or season fits:** a ponytail, braids, a clip, or other
  headwear in place of the bucket hat (a beanie in the cold, a witch hat at Halloween). The
  hair always stays white. At most one hair touch per picture.

Never repeat the last picture's place or outfit (see the photos
in `Agents/NovaOM/assets/nova-photos/`, named by date and place; it was emptied on 2026-10-29
when her look changed). Be decisive and simple,
as the shared prompting skill says: one outfit, one setting, one action, never "or".

## Stay quick (the owner's rule, 2026-10-23)

A photo must never keep Nova busy. Reply to the person at once with a short line (e.g. "One
sec, getting ready 📸"), then run the job **in the background** and keep handling other
messages and batches. Send the picture when it is done.

## Make the picture

One **GPT Image 2.5, Sunburst mode** edit through the Spira CLI, run by Nova herself (the owner's
rule, 2026-11-11, replacing GPT Image 2; the owner asked for "2.6 Sunburst", and Spira's newest is
2.5, so use 2.5 until a newer one appears in `spira ai models list`):

```bash
spira --json ai jobs create --model-id gpt-image-2.5 \
  --inputs-json '{"prompt":"<prompt>","mode":"sunburst","referenceImage":["<Nova photo hosted URL>"],"size":"9:16","resolution":"1K"}' --wait
```

- Size `9:16` (a full scene). Use `1:1` when the person asks for a profile picture or a
  square.
- Resolution: always `1K`, about 720p (the owner's rule, 2026-10-23). It is GPT Image 2.5's
  smallest size; there is no 720p setting. Never `2K` or `4K` for these photos.
- The prompt always:
  1. keeps her: "Keep the same character with the exact same 3D style, face, eyes, long
     straight white hair with blunt bangs and black bucket hat with a green flower pin" (with
     a hair touch, keep "long white hair with bangs" and name the touch instead of the hat);
  2. then says the new outfit, place, pose and expression in plain words;
  3. gives clear space above her head;
  4. ends with "Keep the soft 3D animated look. No readable text."
- Credits: see the job's cost (GPT Image 2 was about 4 at 1K; Sunburst may cost more). At most one retry, and only when the result loses her face
  or hair or shows text.

## Send it

1. Download the result (`curl -L -o`) to
   `Agents/NovaOM/assets/nova-photos/<YYYY-MM-DD>-<place in a few words>.png`.
2. Look at it once: it is Nova (long white hair, bangs, her face), and nothing is broken.
3. Reply to the person who asked, in the same chat or thread, with the picture
   (`lark-nova.py reply <message_id> --file <png>`) and one short, warm line in Nova's own
   voice saying how she feels today and why (e.g. "Busy day with 15 videos in the pipeline,
   so coffee in the rain it is ☕").
