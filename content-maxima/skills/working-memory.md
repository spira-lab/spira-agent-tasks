# Working memory

A living record kept across sessions. Entries are facts, one per line,
not instructions. The Reword table is the only section you add to on
your own. Preferences are written only when the user asks for one to be
recorded; never add, change, or remove a preference otherwise.

## Preferences

Things the user has said they prefer, to be applied without being asked
again. One per line: what, and where it applies. A preference may name
an add-on from `add-ons.md`; then that add-on applies wherever the
preference does.

- IASO only: never use a talking head. Applies to every project for the
  IASO brand and to no other brand or project.
- WHEN the user provides a video URL or a local path to a video as the
  style reference, use the `Style ref contact sheet` add-on.
- IASO only: produce the VO with this command, the text being the
  approved script:

  ```bash
  spira ai jobs create --model-id elevenlabs-text-to-speech --inputs-json '{"text":"…","voiceId":"cgSgspJ2msm6clMCkdW9","providerModelId":"eleven_v3"}' --wait --json
  ```
- IASO only: transitions are always effortful and purposeful, and
  elements enter and exit dynamically. No element simply appears or
  simply disappears.
- IASO only: do not add the IASO logo or the word IASO as text on
  screen. Avoid redundancy between caption subtitles and on-screen
  text: IF the on-screen text already covers the script word per word,
  use no caption subtitle.
- IASO only: WHEN several visual elements are needed, generate them in
  one GPT Image 2 request, listing every element in the prompt on a
  transparent background, instead of one request per element. When the
  output returns, cut each element out of it and use those cut-outs as
  the elements of the video. One request for many elements costs less
  than many requests.
- IASO only: WHEN generating background music, the tone is scientific,
  not sad.
- IASO only: WHEN asked to translate a video into another language,
  translate the script, generate a new VO from the translated script
  with the IASO VO command, apply it to the video, and adjust the
  timing of every element to the new VO. Captions and any on-screen
  text that carries the script follow the translated script. Save it
  as a new editable, with its own materials, metadata, and render,
  named with the language as a prefix on the title and the same video
  number as the original: `NN-<lang>-name-MM-DD`, so `03-iaso-09-21`
  in Spanish becomes `03-es-iaso-09-21`. The number is kept, not
  incremented; the language is what tells the two apart.

## Reword

Words the speech models get wrong, and the spelling that makes them say
it right. The reword is used only inside a spoken line in a prompt.
Captions, subtitles, and any text on screen always use the original.

| Original | Reword for speech |
|----------|-------------------|
| Claude | Clawed |
| GitHub | Git-Hub |
| Cookiy | Cookie |
