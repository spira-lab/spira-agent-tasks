---
name: prompting
description: How to write prompts for the generation models in the toolkit, and the fixed prompt format for each model. Use every time a prompt is written for Higgsfield Soul, GPT Image 2, or a talking-head clip (Gemini Omni, or Seedance 1.5 Pro as the fallback).
---

# Prompting

Prompts are written the same way every time so the output is steady.
The principles apply to every prompt; the formats below are filled in,
not rewritten.

## 1. Principles

1. **The simpler the prompt, the better.** Detail past what the shot
   needs causes drift: the model is forced into a scene or a pose it
   cannot resolve and hallucinates to satisfy the words. Describe the
   state, not the mechanics. Let the model decide how a body sits, how a
   hand rests, how light falls, and it produces the natural version.
2. **Be decisive. Never write "or".** A model cannot choose between two
   ideas. It leans on the first, or merges both, and the merge is a
   hallucination. One subject, one outfit, one setting, one action.
3. **UGC shots use no professional photography or cinematography
   language.** No lens, no focal length, no bokeh, no golden hour, no
   rule of thirds, no dolly, no rack focus, no colour grade. Those words
   force a professional look into the image and the motion and pull it
   away from a casual UGC shot. Casual does not mean candid: the person
   knows the phone is there and looks at it.
4. **No examples in a prompt.** A model anchors on an example and
   reproduces it instead of the thing asked for. State what is wanted
   directly.

## 2. Higgsfield Soul (`ai-influencer-image`)

Fill the slots. Drop a slot only where the format says it may be
dropped.

```
UGC Casually taken shot of a [age] [gender], [pretty/handsome/cute good looking], [beautiful and attractive with a natural easy smile, or the description that fits], [hair style] in a [outfit style], [what it is not, when needed; remove if unnecessary]. [He/She] is wearing a [outfit detail]. [Framed from the legs up if standing, waist up if sitting], [standing/sitting] relaxed in [setting location] [daylight/night time], looking at the camera, no posing, no filters, no text
```

## 3. GPT Image 2, persona edit

The Soul output is the reference, or the user's own image when they
provided one to use as the avatar. The prompt keeps everything and
changes only what is named.

```
Edit this photo. Keep the same person with the exact same face, hair, expression, skin, body, outfit, pose, room and lighting. Only change [the part that needs replacing]: replace it [replacement instruction]. Also reframe slightly so there is clear empty space above [his/her] head, roughly a head height of room between the top of [his/her] hair and the top of the frame, still framed from the [legs up/waist up]. Keep the casual quick phone snapshot look, no filters, no text
```

- The "Only change" sentence is included only when something must be
  edited or fixed. With nothing to change, omit it and the prompt is
  keep, reframe, keep the look.
- Whatever is being replaced comes out of the keep list. If the outfit
  changes, the first sentence no longer says "outfit"; if the hair
  changes, it no longer says "hair". Keeping and changing the same thing
  in one prompt is a contradiction the model resolves by drifting.
- A product never goes into the persona edit. The persona is edited the
  same way with or without a product; the product enters in the
  talking-head clip (section 5).

## 4. GPT Image 2, transparent background

Keep it very simple: say what the visual is, then instruct a
transparent background. Nothing else.

```
[the visual], on a transparent background, PNG with alpha, no backdrop, no shadow on the ground, no frame
```

WHEN several elements are generated in one image, lay them out as a grid
of equal sections, one element per section, named in order:

```
A grid of [cols] columns by [rows] rows of equal sections, one element centered in each section: [element one]; [element two]; [element three]; [element four]. Each one isolated element, fully inside its own section, on a transparent background, PNG with alpha, no backdrop, no shadow on the ground, no frame, no grid lines
```

The elements are listed left to right, then top to bottom.

WHEN several full-screen shots are generated as one collage, name the
grid, place each shot, and forbid anything between them:

```
A 2 by 2 grid of four different full-bleed vertical photographs that fill the whole image edge to edge: top left, [shot one]; top right, [shot two]; bottom left, [shot three]; bottom right, [shot four]. The four photographs meet directly with no gaps, no gutters, no borders, no strokes, no outlines, and no frames between them.
```

## 5. Talking-head clip: Gemini Omni (and Seedance 1.5 Pro as the fallback)

The same format for both models; one video uses one model only (toolkit
3e). The cleaned persona image is the reference. The line is the script
chunk for this clip, from the chunker's `chunks.json`.

```
The person says: “[line]”
The camera remain static and steady on position.
No camera movements, No background music, No sound effects, No special effects, No text on screen.
```

**With a product.** The persona image is the first reference and the
product image the second. What the product is decides the format (toolkit
3e): an outfit is worn, an object is held, and anything else is left out
of the clip, which then uses the plain format above.

An outfit, worn:

```
The person is wearing the [product] from the second image and says: “[line]”
The [product] looks exactly as in its image: same shape, colour, pattern, and proportions.
The camera remain static and steady on position.
No camera movements, No background music, No sound effects, No special effects, No text on screen.
```

An object, held, with one simple interaction and nothing more: holding it
up beside the face, turning its front to the camera, or using it the way
it is meant to be used. One interaction per clip, kept simple; the line
stays the same.

```
The person is holding the [product] from the second image, [one simple interaction], and says: “[line]”
The [product] looks exactly as in its image: same shape, colour, label, and proportions.
The camera remain static and steady on position.
No camera movements, No background music, No sound effects, No special effects, No text on screen.
```

## 6. Speech

WHEN a prompt carries words to be spoken, the talking-head line or a VO
script, the model will get some of them wrong: brand names, product
names, acronyms, unusual spellings, words borrowed from another
language. Before writing the prompt, open `working-memory.md`, which
sits beside this skill in the designers' shared folder, and check its Reword section. Any word listed there goes into the
spoken line in its reword spelling, not its original.

IF you hear a word mispronounced in the output and it is not in the
list, find a spelling that makes the model say it right and add the
pair to the Reword table, so the next session does not repeat the
search.

The reword lives in the spoken line only. In the subtitle, the caption,
and any text on screen where the word appears, use the original word,
spelled as the user or the brand spells it. The viewer reads the real
word and hears it said right.

## 7. Edge case

Any generation that has no format above is prompted freely, as you see
fit, under the principles in section 1.
