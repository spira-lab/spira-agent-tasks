# Canvas facts (the only fixed things about the output)

- Each slide is 1080×1350 px (4:5). Export JPEG quality 92.
- Safe area for text and the swipe cue: 80 px from the sides, 84 px from the top, 120 px from the bottom. Objects and photos may bleed; words may not.
- The HTML is yours to write from an empty file. The renderer only needs this convention: one element per slide with `class="slide"` and `id="s1" … "sN"`, each exactly 1080×1350. Everything else (fonts, structure, CSS, layering) is decided by the design brief for this brand.
- The swipe cue and slide counter, if you use them, sit in the same place on every slide.
- Text is never under an object unless the overlap is deliberate and under 10%. A headline must read in one second at phone size.
- Fonts load from Google Fonts or from `gen/` as local files; the renderer waits for them.
