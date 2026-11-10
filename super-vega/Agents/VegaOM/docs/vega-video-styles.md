# Vega — Video Styles

Owned by Vega. The video styles she can assign, and when to choose each. Vega writes the
style name in the batch sheet's **Style** column; Atlas picks the designer for it. The names
must match Atlas's designer list exactly (`Agents/AtlasPM/docs/atlas-designers.json`), and
the sheet tool refuses a style that is not on it.

**Script:** a style that *needs a script* gets one from Echo. A *scriptless* style gets none: Vega puts what the designer needs in the Instructions column and skips Echo.

Only assign a style marked **available**. A **planned** style has no designer yet: tell the
user it is not available.

| Style (exact name) | Status | Script | What it is | Choose it when |
|---|---|---|---|---|
| `talking head edited` | **available** | needs a script (Echo) | A 9:16 Reels/TikTok video led by a person speaking to camera (generated persona, persistent avatar, or the user's own footage), edited with b-roll, animated visuals, captions, sound effects, and music | A human face and voice should carry the message: UGC-style reviews and recommendations, testimonials, founder or expert takes, hot takes and tips told person to person; trust, relatability, and personality sell it. The default when nothing points elsewhere |
| `reaction` | planned | _to be defined_ | _To be defined_ | _To be defined_ |
| `timelapse` | planned | _to be defined_ | _To be defined_ | _To be defined_ |
| `narration` | planned | _to be defined_ | _To be defined_ | _To be defined_ |
| `explainer` | **available** | needs a script. Echo has no explainer writing style yet: until one exists, the user supplies the script | A 9:16 Reels/TikTok video with **no talking head**: a narrator voice-over with animated infographics, diagrams, kinetic text, product visuals, and b-roll | The message is something to show and understand: how a product or ingredient works, a mechanism or process, the science or data behind a claim, features and steps, before and after, comparisons; or no presenter or avatar is wanted. Needs a narrator voice: put `Use this voice: elevenlabs <voice ID> <model>` in Instructions (from the brand's working memory, or ask the user) |
| `podcast` | **available** | needs a script (Echo: podcast conversational). A user's own script must be two speakers labelled `Podcaster 1:` and `Podcaster 2:`, one turn per line | A 9:16 Reels/TikTok clip of two AI co-hosts in conversation, each line in its own voice and lip-synced, cut like a podcast edit (full shots, pre-lap cuts, split-screen listening shots, jump zooms, captions, music) | The message works as a conversation between two people: a topic discussed back and forth, a question and its answer, two takes on news or a trend, myth against fact, a story told between hosts. The co-hosts are generated for each video, so no avatar columns |
| `avatar` | **available** | scriptless | Avatar images only (Higgsfield Soul + GPT Image 2), one per row, brand `Avatar` | Someone asks only for avatar images; with no description, the designer picks the person |
| `clone` | **available** | scriptless; needs `--source <link>` | Rebuilds a reference video's format for the brand: new lines, voice, persona and shots (Soul, GPT Image 2 plates, Wan 3.0 / Omni Flash 1.1 / Kling clips, music) in the house stage editable | "Clone this ad/video for <brand>": the format is kept and the content is new |
| `re-skit` | **available** | scriptless; needs `--source <link>` | Keeps the source's real motion, timing and voices (pitch-adjusted), recasts the person (Wan 3.0 person replacement) and changes the meaning with cuts, overlays and rebuilt product screens | Trending skits, reactions and memes: "re-skit this for <brand>" |
| `corporate carousel` | **available** (new, 2026-10-27; named `carousel` until the same day, and an old sheet's `carousel` still means it) | needs a script: Echo writes the **topic angle** (corporate carousel topic angle style), not repeated within the brand's last 75 carousels | Not a video: a 4–7 slide corporate carousel by the Corporate Carousel Designer (1080×1350 JPEGs, 4:5) in the brand's own look, from the angle and the brand's website, with captions. Output type `carousel`; made with `vega-batch.py new "<brand>" N --type carousel [--product ...]` (corporate carousel is the default style for that type; later carousel kinds, e.g. a lifestyle carousel, use `--style "<kind> carousel"` and share output type `carousel`); the brand needs a Website in the ledger | Someone asks for carousels or slide posts for a brand (Instagram, LinkedIn) |
