---
name: podcast-toolkit
description: The podcast designer's own toolkit. Which tool to use for each step of a podcast video, with the exact Spira CLI command, model ID, inputs, cost, the voice library, and the podcast tool that runs every mechanical step. Fixed choices. Consult before generating any asset; never substitute a model.
---

# Podcast Toolkit

This is the podcast designer's toolkit. It replaces the shared toolkit for
everything except two sections of it, which you do read:
`<shared>/skills/toolkit.md` **section 1 (the CLI)** and **section 2
(hosting local files)**. Nothing else in the shared toolkit applies to a
podcast video.

`<podcast>` is this designer's folder, `Super Nova/Agents/PodcastVideoDesigner`.

## 1. Tool map

| Step | Model ID | Credits |
|------|----------|---------|
| Persona base image, one per co-host | `ai-influencer-image` (Higgsfield Soul) | 7 per image |
| Two-shot of both co-hosts, 16:9 2K | `gpt-image-2` | 5 |
| Each line's voice | `elevenlabs-voice-clone-tts` | 0.01 per character |
| Each line's talking clip | `heygen-avatar-4` | 10 per second |
| Background music | `elevenlabs-music-generation` | 0.25 per second |
| Word timings | ElevenLabs Scribe via the Spira CLI (Whisper `medium.en` as fallback) | about 1 credit a minute |

## 2. The podcast tool

`<podcast>/tools/podcast.py` runs every mechanical step: the line
voices and talking clips (at most 3 jobs at a time, failed jobs
retried), the audio padding and joining, the uploads, the checks, the
word alignment, the captions, the music level, and the black check. Use
it for those steps; never do them by hand and never write shell loops
(the approved tool list refuses them).

```bash
python3 <podcast>/tools/podcast.py <command> <materials folder> [...]
```

`<materials folder>` is the video's materials folder,
`<root>/editable/materials/<name>/`. The commands, in the order the skill
uses them: `lines`, `split`, `tts`, `join`, `mark`, `pad`, `upload`,
`heygen --test`, `heygen`, `check`, `align`, `captions`, `music`, and
`black <render>`. Run it with no arguments for the full usage.

Every generation the tool runs is added to the video's metadata file
with its credits. If a line or a clip is generated again, the old file
moves to the materials `deletable/` folder first and its metadata entry
follows it.

## 3. Persona base images: `ai-influencer-image`

One Soul image per co-host, both submitted at once (they do not depend
on each other). The prompt is the Higgsfield Soul format in the
prompting skill (section 2), filled for that persona, sitting, framed
from the waist up.

```bash
spira --json ai jobs create --model-id ai-influencer-image \
  --inputs-json '{"prompt":"<persona, Soul format>","size":"9:16","resolution":"1080p"}' --wait
```

Save them as `persona/soul-left.png` and `persona/soul-right.png` in the
materials folder: left is persona 1, right is persona 2.

## 4. The two-shot: `gpt-image-2`

One 16:9 image at 2K of both co-hosts together, with the two Soul images
as references, persona 1 first.

```bash
spira --json ai jobs create --model-id gpt-image-2 \
  --inputs-json '{"prompt":"<two-shot format>","referenceImage":["<soul-left url>","<soul-right url>"],"size":"16:9","resolution":"2K"}' --wait
```

The prompt is this format, filled in:

```
UGC Casually taken wide shot of two podcast co-hosts in the middle of a [emotion: serious, fun, or scary], focused conversation in a [environment shot], [daytime or nighttime]. On the left is the [persona 1, short description] from the first reference image: same face, [hair], [facial hair, if any], wearing [outfit]. On the right is the [persona 2, short description] from the second reference image: same face, [hair], [facial hair, if any], wearing [outfit]. Keep both of their faces, hair and outfits exactly as in the references, [expressions: serious, neutral, happy, or sad]. Their bodies and faces are turned toward each other in three-quarter profile, looking at each other, not at the camera. Each has a podcast microphone. Camera pulled back so there is generous clear headroom above both of their heads. [environment] Framed from the waist up, sitting relaxed, no posing, no filters, no text
```

- Fill each slot with one choice; never write "or" in the prompt (the
  prompting skill's principle 2).
- The expressions are never scared and never surprised.
- Save it as `persona/two-shot.png`.

Then cut it in half and pad each half to a square, with no crop:

```bash
python3 <podcast>/tools/podcast.py split <materials> <materials>/persona/two-shot.png
```

It writes `persona/left.png` and `persona/right.png` (the two halves) and
`persona/left-sq.png` and `persona/right-sq.png` (each half padded to a
square with black on its left and right, e.g. 1024 x 1152 becomes
1152 x 1152). It prints how wide the picture is inside the square: the
edit uses that to keep the black bars off screen.

## 5. The voice library

Four voices, hosted on Spira. Each is passed as the `referenceAudio` of
every line its co-host speaks.

| Voice | Use it for | URL |
|---|---|---|
| Lower pitch male | a more masculine looking man | `https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791755975208-084b4fc6-6ef0-4246-a9aa-426fb713c4dd.mp3` |
| Neutral pitch male | a man with a neutral look | `https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791756290365-832f3100-e8a6-47f9-af29-c68a97d83ed1.mp3` |
| Neutral pitch female | a woman with a neutral look | `https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791758915383-941c1422-f5ae-490b-86ce-2c610b268aee.mp3` |
| High pitch female | a cuter woman who looks like she has a higher voice | `https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791758683505-f05fdc89-30ad-4ec6-b926-d042bc2ee0c8.mp3` |

- **Never the same voice for both co-hosts.**
- Two men: one of each male voice, each by his look.
- Two women: one of each female voice, each by her look.
- A man and a woman: each gets the voice of their own gender that fits
  their look.

## 6. Line voices: `elevenlabs-voice-clone-tts`

Every line of the script is its own clip, voiced with ElevenLabs Voice
TTS: `providerModelId` `eleven_multilingual_v2`, `qualityMode` `stable`,
the co-host's voice URL as `referenceAudio`. The tool does it:

```bash
python3 <podcast>/tools/podcast.py tts <materials>
```

At most 3 jobs run at a time, and a failed job is retried: sending
every line at once makes requests fail. The files are numbered in
script order with the speaker in the name, `lines/01_M.mp3`,
`lines/02_F.mp3`, and so on. A line that still fails after its retries
is listed; run it again with `--only <n>`.

The spoken text is each line's `say` in `lines.json`. It starts as the
script's text; a word in the working memory's Reword table goes into
`say` in its reword spelling (prompting skill, section 6). The script's
own spelling stays in `text`, which is what the captions use.

## 7. Talking clips: `heygen-avatar-4`

One clip per line: the co-host's padded square half as
`referenceImage`, that line's padded audio as `referenceAudio`, size
`1:1`, resolution `1080p`, mode `stable`, talkingStyle `stable`. The
tool does it, after `pad` and `upload`:

```bash
python3 <podcast>/tools/podcast.py heygen <materials> --test
python3 <podcast>/tools/podcast.py heygen <materials>
```

`--test` renders the shortest line only and saves a frame from it to
look at (`clips/NN_TAG-frame.jpg`). Look at it before anything else
renders. Without `--test`, every line still missing a clip renders, 3
at a time, failed jobs retried, into `clips/NN_TAG.mp4`. Then:

```bash
python3 <podcast>/tools/podcast.py check <materials>
```

It confirms every clip is as long as its padded audio and that the
pre-lap and listening silences are still in the clip. A clip that fails
is rendered again with `heygen <materials> --only <n>`.

Credits: 10 per second of the clip, padding included.

## 8. Background music: `elevenlabs-music-generation`

One instrumental that fits the topic, about the video's length plus 1
second (a whole number of seconds, at most 300).

```bash
spira --json ai jobs create --model-id elevenlabs-music-generation \
  --inputs-json '{"prompt":"<the mood, instruments, and tempo that fit the topic>. A sparse instrumental bed, no vocals, no drops, no builds, a soft ending.","duration":"<seconds>"}' --wait
```

Save it as `bgm.mp3` in the materials folder. Then set its level:

```bash
python3 <podcast>/tools/podcast.py music <materials>
```

It measures `vo.mp3` and `bgm.mp3` and prints the `data-volume` and
`data-under` to put on the editable's bgm tag, so the music sits about
16 dB under the voices in the preview and in the render.

Credits: 0.25 per second.

## 9. Do not use

Anything not listed above. No talking-head pipeline from the shared
toolkit (Seedance, Pixelcut cut-outs, Kling motion control), no
`elevenlabs-text-to-speech` with a voice ID, no `suno-music`, no other
image or video model. IF a step seems to need a tool this document does
not name, stop and ask the user rather than picking one.

The one exception is a model the user names explicitly in their request.
Then use that model for that request as asked, pull its inputs and
prices with `spira ai models get <modelId>`, and state the cost before
running.
