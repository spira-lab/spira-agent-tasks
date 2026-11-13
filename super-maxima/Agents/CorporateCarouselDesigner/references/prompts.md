# Image generation prompts (GPT Image 2 via submit_ai_job)

All AI models run as Spira AI jobs with the `submit_ai_job` and `wait_ai_job` tools: submit with `modelId` and `inputs`, collect with `wait_ai_job` (`jobId`, `saveTo` the output file; the result is saved there, never download it with curl or wget). Never run a job through the `spira` CLI, and never call OpenAI, Kling, ElevenLabs, or any provider directly. Image model is `gpt-image-2` (text-to-image and image-to-image). Independent images are submitted together in one turn and waited on together in one turn. Model inputs and prices: `spira ai models get gpt-image-2` (read-only docs). After each job, record it with `carousel.py record-job`.

## IF a real product image exists → reference it
`research/images.txt` and `research/img/` hold product image candidates found on the site. Look at them. If any shows the actual product (device, packaging, app screen, vehicle, garment, whatever the brand sells), then every generated image that depicts the product must use it as `referenceImage`, so the product keeps its real shape, color, proportions, and marks. Run `gpt-image-2` image-to-image with `submit_ai_job` (one job per image) and `wait_ai_job`:
- `inputs` `{"prompt":"<prompt>","size":"1:1","resolution":"2K","referenceImage":["<public image url from images.txt>"]}`, `saveTo` `<folder>/gen/product_cut.png`
- `inputs` `{"prompt":"<prompt>","size":"3:4","resolution":"2K","referenceImage":["<public image url>"]}`, `saveTo` `<folder>/gen/product_scene.png`
Then record each job: `python3 "<carousel>/tools/carousel.py" record-job "<folder>" <jobId> <credits> "<out.png>" --url <resultUrl> --prompt "<prompt>"`.
- Isolated element from reference: "Using the referenced product exactly as it is, recreate it as a photoreal cutout on a fully transparent background (PNG with alpha), new angle: <three-quarter / top-down / side>, studio lighting from top-left, no cast shadow on the background, no added text or logos beyond those on the product itself, no other objects."
- Full image from reference: "Using the referenced product exactly as it is, place it in <scene from the customer's day>, <mood, palette, lens>, shallow depth of field, no added text, no other brands."
- Multiple products or angles: one call per product; do not combine references.
- Verify likeness against the source before using. If the generation changes the product's shape or marks, regenerate with a shorter prompt or crop the real photo instead.
The reference must be a public URL. The site's own image URLs qualify. A local file (a capture of the site, a file named in the request) is never sent to generation and never hosted for it: use the local file directly in the layout, as it is.

## IF no product image exists → generic objects
Only then generate stand-in objects from the brand's world, with no markings, in the mood and palette the design brief sets. For software brands with no physical world, generate the world their users work in (bench, board, parts, desk, the moment of the problem) and use real screenshots for the product itself; never invent the product's screens. At least one generated visual per carousel is mandatory, and the hook slide always has one (the owner, 2026-10-27).

Model: `gpt-image-2`. Sizes: `3:4` for collage (4K allowed), `1:1` 2K for cutout sheets (1:1 does not allow 4K). Cost at Spira's live price (2026-10-27): about 4 credits at 1K, 5 at 2K, 8 at 4K per call (check `spira ai models get gpt-image-2`); budget up to about 25 per carousel. Write the object list from the brand's world as found in research: the physical things its customers touch, plus the props the design system uses.

## Cutout sheet (one call for all elements)
"Generate the image with a fully transparent background (PNG with alpha channel). Photoreal product-photography cutouts, studio lighting from top-left, no cast shadows on the background, no text, no markings, no labels, no logos. Arrange in a loose grid with generous clear space between every item so each can be cropped: 1) <object from the brand's world>; 2) <object>; … N) <object>. Consistent scale, consistent lighting."
Props (tape, paper, sticky notes, stamps, pens) are generated only if `design-brief.md` item 7 calls for them, with the reason from the brand's site. Most brands need none.
Verify alpha with PIL (`getchannel('A').getextrema()` must include 0). Split with `tools/split_cutouts.py` (connected components; never grid-cut). Name the pieces in reading order.

## Collage (full-bleed backgrounds, one call)
"One single image that is a 2x2 grid collage of four separate photographs, filling the frame edge to edge. Absolutely no gaps between panels, no borders, no strokes, no frames, no text, no watermark. All four: <mood, palette, lens derived from the brand's site and the chosen theme>. Top-left: <scene from the customer's day>. Top-right: <scene>. Bottom-left: <abstract texture from the brand's material world>. Bottom-right: <scene>."
Split with `tools/split_collage.py`. Each panel ≈ 1080×1440 from a 2160×2880 output.

## Atmosphere layer (full-bleed environment behind content)
When design-brief item 7 calls for it: one `3:4` `2K` or `4K` image of the brand's environment in the mood the influence sets, no text, no people's faces unless the brand uses them, composed with empty space where the headline will sit. Place it full-bleed under the content at reduced opacity or under a color wash from the palette. One call per carousel is usually enough; the collage prompt can supply four variants.

## Single cover photo
Same as one panel, `3:4` `2K`. Whenever paper, screens, or packaging appear, add "all printed text intentionally blurred and unreadable".

## Rejection rules
Reject panels with readable product markings, brand names, logos, legible text, or wrong anatomy. Regenerate the one call rather than retouching.
