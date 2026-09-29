# Cookiy

Preferences the user set for every Cookiy project, and for no other
brand. Read this file when the brand is Cookiy; they apply without being
asked again.

- WHEN the request gives the Davin avatar photo and an ElevenLabs voice
  ID, the talking head is HeyGen driven by ElevenLabs speech. Skip Soul,
  the persona edit, and Seedance (toolkit 3a, 3b, 3e); the photo is used
  as given, hosted only if it is not already a public URL (toolkit
  section 2). Two jobs, in order:

  1. The speech, the whole script in one job on ElevenLabs V2, written
     to `vo.mp3`:

     ```json
     {"text":"…","voiceId":"<the voice ID from the request>","providerModelId":"eleven_multilingual_v2"}
     ```

     Build the timings from it (`python3 tools/make-timings.py <materials>/<name>/vo.mp3`),
     then host it with `spira assets upload`.
  2. The talking head, the photo lip-synced to that speech, written to
     `th-01.mp4`:

     ```json
     {"referenceImage":["<photo url>"],"referenceAudio":["<vo.mp3 url>"],"size":"9:16","resolution":"1080p","mode":"stable","talkingStyle":"stable"}
     ```

  One clip covers the whole voice-over: no 4, 8, or 12-second chunks.
  It is cut out with Bria like any talking-head clip (toolkit 3f) and
  goes on the stage at `data-start="0"`. The voice is ElevenLabs, so
  `data-sfx-under="14"` on `#vo`. Cost is 10 credits a second.
