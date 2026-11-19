# Hermes — Working memory

What the user asked Hermes to remember, kept across sessions. His upload tool reads it.
Written only when the user (through Nova) asks Hermes to remember, change, or forget something.

## Upload tags

Which Spira Social Post Assets tag each brand's or product's videos and carousels are uploaded
under. A row with a Product applies to that product; a row with the Product empty applies to the
rest of the brand. **For** says which rows of a batch the tag is for: `videos`, `carousels`
(every slide of a carousel), or empty for both. A row for the kind (videos or carousels) wins over
a row for both; then the product's own row wins over the brand's. The Tag ID is what the tool
uploads with; the tool checks it still exists in Spira before every upload.

| Brand | Product | For | Tag (category / tag) | Tag ID |
|---|---|---|---|---|
| Cookiy Labs | Cookiy Earn Text Agent |  | Cookiy / US | 340d2cc0-5d3a-437c-9ac6-26d28a27d684 |
| Cookiy Labs | Cookiy Insights |  | Cookiy / US | 340d2cc0-5d3a-437c-9ac6-26d28a27d684 |
| PartGenie |  | videos | PartGenie / US - Video | 397757ef-85b4-4ba9-be5d-6f8afd939554 |
| PartGenie |  | carousels | PartGenie / US - Photo Carousel | 61d84a98-34e7-4055-ab46-8000cd24dd53 |

- 2026-10-29 (Jekylle): PartGenie carousels (carousel slides, any PartGenie product) go under
  PartGenie / US - Photo Carousel; PartGenie videos keep PartGenie / US - Video.
- 2026-11-03 (Angelica, in Lark): Cookiy Insights videos go under the same Cookiy / US tag as
  Cookiy Earn.
