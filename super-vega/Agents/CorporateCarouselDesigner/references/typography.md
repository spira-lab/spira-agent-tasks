# Typography

**Find the brand's faces.** `research/style.json` lists `font_families` from the CSS, `font_faces` from @font-face declarations, and `google_fonts` from any Google Fonts link. Confirm against the rendered site if in doubt (headless Chrome screenshot of the homepage).

**Use them, in this order of preference.**
1. The brand's own face is on Google Fonts → load it with a `<link>` in your HTML.
2. The brand's face is commercial (e.g. a licensed grotesk) → pick the closest Google face in the same class and weight range, and write the substitution in notes.md. Class map: geometric sans → Inter Tight / Manrope / Plus Jakarta; neo-grotesk → Inter / Work Sans; humanist sans → Source Sans 3 / Nunito Sans; transitional serif → Source Serif 4 / Newsreader; old-style serif → EB Garamond / Cormorant; display serif → Fraunces / Playfair Display; mono → JetBrains Mono / IBM Plex Mono; rounded → Nunito / Quicksand.
3. The site uses a system font stack → treat the brand as neutral and choose one pairing that fits its register, state why.

**Pairing rules.** One display face, one text face at most; mono only if the brand uses it or the content is data. Headline size follows the layout you designed, not a fixed number. Never carry a face from a previous run; `state/history.json` is also a record of looks, check it.

**Weights.** Load only the weights you use. Display headlines usually 500–700 for sans, 400–500 for serif.
