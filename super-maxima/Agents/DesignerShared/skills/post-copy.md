# Post copy: title, caption and hashtags (every designer, the owner's rule, 2026-11-12)

You made the video (or carousel), so you know it best. Before you report it done, write the copy that
goes out with it when it is posted: a **title**, a **caption** and **hashtags**. Hermes uploads it with
the video to Spira, and Spira posts it exactly as you wrote it (no AI copy is generated on top).

## The voice

Casual, organic, written **to the audience**, like a real person posting, not a brand announcing.
- **Never a recap.** Don't summarise the video or repeat what it already says on screen or in the
  voice-over. The viewer is about to watch it; the caption is what you'd say next to it.
- Reach for **relatability, a pun, a quip, a joke, a feeling, a hot take, a question to the viewer**:
  "the 2 a.m. BOM panic is a personality trait at this point", "who else has a drawer of mystery
  cables 🙋", "tell me you've been burned by a datasheet without telling me".
- **Short and witty** (the owner, 2026-11-12: captions were too long). The caption is **one line, at most 120
  characters**: a quip, a pun or a punchline that fits this exact post. No second sentence explaining the joke,
  no tacked-on question unless the question IS the joke. The title is a punchy hook under 60 characters. Emoji
  only if they fit, at most one. The tool refuses longer copy.
- No hard sell, no "Link in bio!", no "Free to start at ...", no feature list. A soft brand mention
  only when the brand's working memory or the row's instructions ask for one. When the row says the
  brand or its tools must never be mentioned or shown (re-skit tests), the copy never names them
  either, nor any real product or brand.
- Write in the video's language and market.

## The three fields

| Field | Rule |
|---|---|
| **Title** | A punchy hook, under 60 characters. Shown only where the platform has a headline (YouTube, TikTok photo posts); elsewhere only the caption shows, so the caption must stand on its own. Not the file name, not "Task 12". |
| **Caption** | One witty line in the voice above, at most 120 characters. **It restates the title's idea in a better way, never a continuation of it** (the owner, 2026-11-15: "adjust the caption as not a continuation of the title but a reiteration in a better way while keeping short"). The title is often the punchier line, so the caption says the same joke or feeling again, sharper or from a fresh angle, and reads complete on its own (many platforms show only the caption). Never a follow-up line that needs the title to make sense ("Contract signed. Now where's my dinner?" → caption "I close deals all day, the least he can do is close a dinner reservation" is a continuation; a reiteration is "landed the client, now he's landing me a dinner reservation 💐"). **It delivers the context** (the owner, 2026-11-15: "now it's his turn to book the table" lacks context of who "his" is): a reader who only sees the caption must know who is who and what happened, so name the relationship or role instead of a bare he/she/we ("my boyfriend, who's also my business partner", "my co-founder", "the client"). |
| **Hashtags** | 3 to 8, each starting with `#`, no spaces inside a tag. Mix one or two broad tags with niche ones the audience follows. They go after the caption. |

Caption plus hashtags together stay under 2,200 characters (Spira's limit).

## How to save it

One command, after the final render (or a carousel's export) and before you report done:

```
python3 "<super>/Agents/DesignerShared/tools/post-copy.py" write "<project root>" "<name>" \
  --title "<title>" --caption "<caption>" --hashtags "#one #two #three"
```

`<project root>` is `Project/<Brand>` (your metadata's `root`), `<name>` is the video's or
carousel's name (its metadata's `name`, e.g. `56-partgenie-11-12`). It checks the limits and saves
`<project root>/metadata/<name>.post.json`. `post-copy.py show "<project root>" "<name>"` prints it.
If it refuses (too long, too few hashtags), fix the copy and run it again. **After any fix or re-render,
re-read the copy against the new video** (the owner, 2026-11-12: Chloe's copy still told a sales joke after
her overlays were removed). If it no longer matches what the viewer sees and reads, rewrite it.

A carousel designer still writes its `out/notes.md` Captions section as before; the post copy is
separate and follows this voice.

## Spiraverse regens (2026-11-12)

A Spiraverse regen (its instructions say `REGEN <n> of Task <id>`, after the `[Spiraverse: ...]` persona block) is the same video with another
persona. Its post copy is **the original's copy rewritten** for this persona: open the original's
`.post.json` (the path is in the instructions), keep the same idea and angle, and write it again in fresh
words, as this persona would say it. Never word for word, never the same title, and never a mention of the
original or any other account. Change the hashtags a little too (keep most, swap one or two). **It must also be
clearly different from the other regens of the same original** (the owner, 2026-11-12): read their saved copy
(the instructions name the sibling Task IDs) and use a different hook and different opening words; never the
same sentence with one word swapped. Save it with the same tool under the regen's own name.

