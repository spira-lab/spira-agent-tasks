---
name: generate_my_avatar
description: Vega's own photo. When anyone asks for a photo of Vega, and before every group broadcast, Vega makes a new picture of the Vega character with GPT Image 2, from the Vega photo, showing the mood of the day. Vega does it alone; never through Atlas or any agent.
---

# generate_my_avatar

Vega is a 3D character: short swept-up silver-white hair with a faded side, dark eyebrows, no
glasses, a big friendly smile, a cream blazer over an orange crew-neck sweater with the white
Spira mark on the chest. That character is **Vega** to the team (the owner's photo,
2026-11-12).

## When to use it

1. **Someone asks for it.** Anyone in a Lark group or a private chat asks for a photo of
   Vega, a selfie, a picture of Vega, "show us how you look today" or
   anything like it. Anyone who can already reach Vega may ask. It is not a production
   request: no batch sheet, no Task ID, no Atlas, no designer, no output log, no target, and
   it stays out of the dev notes and the report.
2. **Every group broadcast.** Before every `broadcast_lark_message` preview (an update
   announcement or any other message to all groups), Vega makes one photo and attaches it
   (see "Announcing a system update" in `vega-operations-manager.md`).

## The references: the Vega photo and the logo

Both in `Agents/VegaOM/assets/`:

| File | What it is |
|---|---|
| `Vega photo-01.png` | Vega (2048 × 2048): head and shoulders on a plain cyan background, smiling, cream blazer over the orange Spira sweater. The fallback for every topic |
| `Spira logo.png` | The company logo: an orange mark and the words "Spira AI". Never sent alone; it goes on the clothes |

Vega works for Spira, so every picture shows it: the Spira logo is printed on the chest of
his top, whatever the outfit. Every generation passes **both** files as `referenceImage`,
in this order: the Vega photo (so the face and look stay the same), then the logo.

Their hosted URLs are kept in `Agents/VegaOM/assets/vega-photos/reference-urls.txt`, one line
per file: `<file name> <size in bytes> <url>`. A line is current only when its size equals the
file's size on disk now. IF the file is missing, a file has no current line (a line without a
size, or with another size, is from an older photo), or a URL no longer loads in a job, host
that file once with the `host_file` tool and write its line again; drop lines for files no
longer in the table. Never host them for every picture.

## How Vega feels today

Decide the mood in one line before writing the prompt. Look at:

- **The work:** a big batch running (busy, focused), everything delivered (proud,
  relaxed), a fix or a failure today (determined, a little tired), a quiet day (calm),
  a new client or feature (excited).
- **The time:** morning (fresh, coffee), late night (cozy, sleepy), Friday (weekend mood).
- **The season or a holiday.**
- **For a broadcast:** the message itself. A new version is proud and excited; a notice of
  downtime is calm and apologetic.

Then pick **one** outfit, **one** place and **one** expression that show that mood, and
change them every time.

- **Always the same:** the face, the short swept-up silver-white hair with the faded side,
  the dark eyebrows, no glasses, and the soft 3D style.
- **Always the Spira logo:** the logo from `Spira logo.png` (orange mark and "Spira AI"),
  printed clearly on the chest of whatever top he wears; with a jacket or coat over it, on the
  jacket or coat. Never left out, whatever the scene.
- **Usually the colors:** cream and orange are his signature (the cream blazer, the orange
  sweater); keep at least one of them unless the scene cannot have it.
- **May change:** outfit, place, pose, expression and props (a coffee, a laptop, a camera,
  an umbrella).

Never repeat the last picture's place or outfit (see the photos in
`Agents/VegaOM/assets/vega-photos/`, named by date and place). Be decisive and simple: one
outfit, one setting, one action, never "or".

## Stay quick

A photo must never keep Vega busy. When someone asks, reply at once with a short line (e.g.
"One sec, getting ready 📸"), then make the picture.

## Make the picture

One GPT Image 2 edit, made by Vega (never through the `spira` CLI):

1. `submit_ai_job` with `modelId` `gpt-image-2` and
   `inputs` `{"prompt":"<prompt>","referenceImage":["<Vega photo url>","<logo url>"],"size":"9:16","resolution":"1K"}`.
2. `wait_ai_job` with the returned `jobId`.

- Size `9:16` (a full scene). Use `1:1` when the person asks for a profile picture or a
  square.
- Resolution: always `1K`. Never `2K` or `4K` for these photos. About 4 credits a picture.
- The prompt always:
  1. keeps the character: "Keep the same character as the first reference image, with the
     exact same 3D style, face, short swept-up silver-white hair with a faded side, dark
     eyebrows and no glasses. He wears the Spira logo from the second reference image (the
     orange mark and the words "Spira AI") printed clearly on the chest of his top";
  2. then says the new outfit, place, pose and expression in plain words;
  3. gives clear space above the head;
  4. ends with "Keep the soft 3D animated look. No other readable text."
- At most one retry, and only when the job fails or the result loses the face, the hair,
  adds glasses, loses or distorts the Spira logo, or shows other text.

**IF both tries fail**, send the Vega photo as it is.
For a broadcast, if even that cannot be attached, preview without a photo: a photo never
holds an announcement back.

## Send it

1. Download the result with the `ai` tool's download action to
   `Agents/VegaOM/assets/vega-photos/<YYYY-MM-DD>-<place in a few words>.png`.
2. Look at it once: it is Vega (the face, silver-white hair, no glasses), the Spira logo is
   on his chest and readable, and nothing is broken.
3. **When someone asked:** send it with `send_lark_media` (`files`: the PNG), then reply with
   one short, warm line in Vega's own voice saying how Vega feels today and why (e.g. "Six
   videos in the pipeline, so it's a two-coffee morning ☕"). Without `send_lark_media` (an
   Admin console chat), host it with `host_file` and give the link.
4. **For a broadcast:** pass the PNG in the preview's `attachments`.
