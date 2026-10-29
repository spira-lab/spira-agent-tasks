# Working memory

Shared by every video designer, kept across sessions. It holds two things: the **design
approach** (how designers work) and **word fixes** (the Reword table). A design approach entry
applies to every video, unless it names a brand or a product: then it applies only to that
brand's or product's videos. Nova, the operations manager, keeps the brands' standing
preferences; those reach a designer through the request: its instructions, music, voice, and
the other fields Atlas passes on.

Entries are facts, one per line, not instructions. The Reword table is the only section you
add to on your own. The design approach is written only when the user asks for one to be
recorded; never add, change, or remove an entry otherwise.

## Design approach

How videos are made: every video, unless an entry names a brand or a product. An entry may name an add-on from `add-ons.md`;
then that add-on applies wherever the entry does.

- WHEN the user provides a video URL or a local path to a video as the
  style reference, use the `Style ref contact sheet` add-on.
- WHEN a request carries a Task ID, the Task ID is the video's number. Use
  it as the NN in the video's name, padded to two digits, never the next
  number counted in `editable/`. Finished videos are moved out to backup,
  so counting the folder would reuse numbers already given to earlier
  videos.
- WHEN the request is for Cookiy Earn (brand Cookiy Labs) and the script
  has the speaker introduce themselves in a profession, the persona is
  made to reflect that profession: someone who looks like they do that
  work, dressed and set the way that profession is.
- WHEN the request is for Cookiy Earn (brand Cookiy Labs, any Cookiy Earn
  product), no riser sound effects are used, and sound effects are kept
  simple and sparse: only a few, on the moments that matter, never on
  every cut or element.
- WHEN asked to translate a video into another language, translate the
  script, generate a new voice-over from the translated script with the
  same voice the original used, apply it to the video, and adjust the
  timing of every element to the new voice-over. Captions and any
  on-screen text that carries the script follow the translated script.
  Save it as a new editable, with its own materials, metadata, and
  render, named with the language as a prefix on the title and the same
  video number as the original: `NN-<lang>-name-MM-DD`, so
  `03-glowlabco-09-21` in Spanish becomes `03-es-glowlabco-09-21`. The
  number is kept, not incremented; the language is what tells the two
  apart.

## Reword

Words the speech models get wrong, and the spelling that makes them say
it right. The reword is used only inside a spoken line in a prompt.
Captions, subtitles, and any text on screen always use the original.

| Original | Reword for speech |
|----------|-------------------|
| Claude | Clawed |
| GitHub | Git-Hub |
| Cookiy | Cookie |
| Seriph (Sun Seriph) | Serriff |
| Match AHHH | Matchah |
| Seriph (Sun Seriph) | Sair-iff (Sun Sair-iff); "Sun Serif" came out as "sirette" |
| UVA / UVB | U. V. A. / U. V. B. |
| B-roll | Bee roll |
| Pediophobia | Peedee-oh-phobia; "Pedyo Phobia" came out as "pebio phobia" |
| Brightkey (Realty) | Bright-key; "Brightkey" came out as "Breaky" |
| Velta | Vell-tah ("Vell-tah Studio"; plain "Velta Studio" came out as "Veta Studio") |
| IronLoop (IronLoop Fitness) | Ironloop (one word; "IronLoop" came out as "Iron Lab you", "Iron Loop" as "Iron Sue", "Iron Lewp" as "Iron Lab") |
| Freelancing | free lancing ("Freelancing" came out as "Freakalancing") |
| Whitespace | white space ("whitespace" came out as "Clevestide") |
| Kilohms (10 kΩ) | ten kilo-ohms ("10 kilohms" was transcribed as "ten kelms" with Brian, eleven_multilingual_v2) |
