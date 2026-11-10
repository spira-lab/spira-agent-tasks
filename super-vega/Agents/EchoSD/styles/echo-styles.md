# Echo — Writing styles

Echo's guide for choosing a writing style. Every writing skill is for **one video style + one
writing style** (e.g. talking head edited + conversational hype). Vega gives the video style; Echo
picks the writing style from the rows for that video style, by "Choose it when".

Each skill lives in its own folder:
`styles/<VideoStyle>-<WritingStyle>/echo-<video-style>-<writing-style>.md`
e.g. `styles/TalkingHeadEdited-ConversationalHype/echo-talking-head-edited-conversational-hype.md`

Only rows marked **available** can be used. Add one row per new skill.

**Talking head pace.** Every talking head writing skill uses 3.7 to 4.0 words per second, whatever its samples sound like: it is the only pace the AI talking head model can speak at. A new talking head style keeps that line in its Length section.

**Podcast pace.** A podcast script is voiced line by line at about 2.6 to 2.8 words per second, with a 0.35 second pause at every change of speaker; its skill counts both. Every podcast script uses the speaker labels `Podcaster 1:` and `Podcaster 2:`, one turn per line, because the podcast designer splits the script on them.

**Carousel angle.** A carousel row's "script" (any video style ending in "carousel", e.g. `corporate carousel`; the old name `carousel` reads as `corporate carousel`) is its topic angle: one line, plus an optional one-line `Direction:`, for that style's carousel designer. It has no duration and no spoken words. Its angles are kept in their own record per brand (`scripts/<Brand>/carousel-angles.json`), shared by every carousel style and apart from the video angles. A carousel style with no rows of its own below uses the corporate carousel rows until it gets its own (the tools apply it).

**Cycling.** Echo never picks from this table alone: `tools/echo-cycle.py candidates "<video style>" [--product "<product>"]` puts the styles in order (least recently used first, the latest one last), so no style is worn out.

**Product writing styles.** Echo's working memory (`docs/echo-working-memory.md`) can tie a product to its own writing styles. That product's scripts cycle only through those styles, and those styles are never given to any other product or brand. The tools apply it.

| Video style | Writing style | Status | Skill file | Choose it when |
|---|---|---|---|---|
| talking head edited | conversational hype | available | `Agents/EchoSD/styles/TalkingHeadEdited-ConversationalHype/echo-talking-head-edited-conversational-hype.md` | The product or brand has something to be amazed by: how it works, a surprising number, a breakthrough, a new feature. Spoken, high-energy, "here's the crazy part" breakdowns told to the viewer like a friend |
| talking head edited | actionable educator | available | `Agents/EchoSD/styles/TalkingHeadEdited-ActionableEducator/echo-talking-head-edited-actionable-educator.md` | The product or brand can be taught: how to use it, steps, a framework, tips, mistakes to avoid, options compared. A practical, list-driven teacher ("step number one", "number three is") giving value the viewer can use right away |
| talking head edited | unfiltered insider | available | `Agents/EchoSD/styles/TalkingHeadEdited-UnfilteredInsider/echo-talking-head-edited-unfiltered-insider.md` | The product gives the viewer an edge: a shortcut, a little-known feature, a cheat code, a result with hard proof. Blunt, irreverent, contrarian ("you're doing it wrong", "almost unfair"), told like an insider sharing a secret |
| talking head edited | cookiy editorial | available | `Agents/EchoSD/styles/TalkingHeadEdited-CookiyEditorial/echo-talking-head-edited-cookiy-editorial.md` | **Cookiy Earn Text Agent only** (Echo's working memory). Editorial perspective: spoken straight to the viewer as "you" about what they already know from their work, who pays for it, and that one text to Cookiy turns it into paid gigs. No "I" or "we" |
| talking head edited | cookiy buyer | available | `Agents/EchoSD/styles/TalkingHeadEdited-CookiyBuyer/echo-talking-head-edited-cookiy-buyer.md` | **Cookiy Earn Text Agent only** (Echo's working memory). Buyer perspective: a business building a product, app or service speaks as "we", says the experience it is missing, and that Cookiy finds the experienced people for paid gigs; ends on the listener |
| talking head edited | cookiy professional | available | `Agents/EchoSD/styles/TalkingHeadEdited-CookiyProfessional/echo-talking-head-edited-cookiy-professional.md` | **Cookiy Earn Text Agent only** (Echo's working memory). Professional perspective: a working professional in the first person names their job, one piece of real judgment, who pays for it, and that Cookiy turns it into paid work; ends on "text Cookiy" |
| podcast | conversational | available | `Agents/EchoSD/styles/Podcast-Conversational/echo-podcast-conversational.md` | Any topic for a podcast video: two people talking about the product (or the brand) the way real people do, lived-in and unscripted, never a pitch. The only podcast writing style so far |
| corporate carousel | topic angle | available | `Agents/EchoSD/styles/CorporateCarousel-TopicAngle/echo-corporate-carousel-topic-angle.md` | Every corporate carousel row (video style `corporate carousel`, and any carousel style without rows of its own): one topic angle for a 4 to 7 slide corporate carousel about the product (or the brand), plus an optional one-line direction. The only carousel writing style so far |
