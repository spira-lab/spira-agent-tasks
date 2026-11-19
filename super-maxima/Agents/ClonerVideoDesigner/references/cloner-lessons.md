---
name: cloner-lessons
description: Read-only record of Cloner runs that had issues, why they failed, and what fixed them, adapted to the house rules. Read before writing plan.md. Never written by a designer - new lessons are proposed in the video's metadata ("lessons") and Nova adds approved ones.
---

# Cloner lessons

What went wrong in past runs, why, and what fixed it. **Read this before
writing `plan.md`.** If your plan repeats a known failure under the same
conditions, change the plan first.

**This file is read only.** A run that teaches something proposes a
lesson in its metadata's `"lessons"` list, in the entry format below.
Nova adds approved lessons to the shared lessons file. Never edit this
file, the skill or any shared file.

**What makes a lesson worth proposing:**
- Only runs that had issues. A clean run proposes nothing.
- Only what teaches something: a failure that cost real credits or
  quality, or needed a non-obvious fix. Skip trivial slips caught in
  seconds.
- Same cause as an entry below: propose it as an **Also seen** for that
  entry (date, project, what's new), only if it taught something new.
- An entry below marked ⏳ that your run fixed: propose the update.

Entry format (in the metadata as JSON fields of the same names):

```
### YYYY-MM-DD · brand/project · area
- **Applies when:** the conditions the failure and its fix hold for: kind of video and shot,
  speech, music or a held prop, the model and settings. This decides relevance.
- **Failed:** what came out wrong, in one line
- **Why:** the cause found, not a guess ("cause unknown" if not known)
- **Fixed by:** what worked, ✅ once verified in an output, ⏳ if not fixed yet
- **Carry forward:** the rule that avoids it next time, within those conditions
- **Not for:** any nearby case where the fix would do harm
- **Also seen:** YYYY-MM-DD · brand/project: what's new, if anything
```

**Only apply an entry when its "Applies when" matches your clone.** A fix
taken out of its conditions can break something else.

**House rules win over these notes.** Where an entry below was written
under the Cloner's old rules (its own renderer, Whisper first, the 4.0
syllable pace, one shared workflow, retakes without a cap), the
adaptation is noted in the entry in *italics*.

---

### 2026-10-22 · sugo/03 + 04 · Needless Wan split
- **Applies when:** Wan 3.0 `reference_to_video` on a single continuous shot just over the 15 s reference cap (here 16.02 s), where the last spoken word ends before 15 s.
- **Failed:** an even split (0–9 s + 7–16 s) put a visible seam mid-speech and cost 117 credits instead of ~93.
- **Why:** planned by duration without checking where the speech ends; the last 1 s was silent smiling.
- **Fixed by:** ✅ speeding the whole source to just under 15 s (`setpts`, re-timed to 30 fps, cut to 14.97 s, because rounding put the first try at 15.07 s and over the cap), one Wan clip, then slowing the output back by the same factor and trimming to the source length. Frame checks at start, middle and end matched the source audio with no drift. At ×1.34 the slowed clip shows ~22 distinct fps; at ×1.07 there's no visible cost.
- **Carry forward:** for a single continuous shot up to about 20 s, speed it to just under 15 s, run one clip and slow it back instead of splitting. Above ~×1.35 the motion gets visibly choppier; for longer shots split at a pause in speech.
- **Not for:** shots whose ending carries a beat (a gesture, a reveal, a caption) after 15 s.

### 2026-10-22 · sugo · Parallel source understanding
- **Applies when:** source understanding for several sources at the same time.
- **Failed:** the understanding files came back crossed between videos (2 credits each).
- **Why:** the old script set the video URL on one shared workflow, so parallel runs overwrote each other's input.
- **Fixed by:** ✅ *by design in this install: `understand_source.py --task-id` creates one workflow per run, named `Clone Source Understanding <Task ID>`.*
- **Carry forward:** always pass the Task ID; never run the understanding on a workflow another run uses.

### 2026-10-19 · bybit/07-most-likely-coworkers · Wan gesture not in the reference window
- **Applies when:** Wan 3.0 `reference_to_video` person replacement, where the prompt asks for a gesture at a given second that the reference clip doesn't show at that moment.
- **Failed:** Wan followed the reference motion instead; the key ending beat was lost (75-credit clip, last 1.2 s unusable).
- **Why:** Wan copies the reference video's motion; a prompt line can't add a gesture the clip doesn't contain.
- **Fixed by:** ✅ a 3 s clip cut from the source window where the gesture actually happens (19 credits), same references, gesture named in the prompt. The voice line moved 1.2 s earlier so the beat holds to the end.
- **Carry forward:** when a beat depends on a gesture, find the source window where the people actually do it, and cut the reference clip there. Wan's prompt can reinforce motion but not replace it.
- **Not for:** props or identity, which Wan does take from images and words.

### 2026-10-19 · bybit/07-most-likely-coworkers · Voice assembly silenced lines
- **Applies when:** cutting a TTS take into lines with ffmpeg and using a fade inside the same command.
- **Failed:** 12 of 13 lines were silent in the first render. The renderer still reported `ok` (it checks for stereo audio, not content).
- **Why:** `-ss`/`-to` after `-i` (output seeking) keeps the original timestamps through the filters, so `afade=t=out:st=…` fired at that second of the full take, before each line.
- **Fixed by:** ✅ `-ss`/`-to` before `-i` (input seeking), then measuring every line's level in the assembled `vo` and transcribing the render.
- **Carry forward:** seek on the input when a filter uses times. After building any `vo`, measure each placed line's level, and transcribe the final render (`make-timings.py --txt`), not just the voice file.

### 2026-10-19 · bybit/05-sort-tasks-talking-head · Omni voice drift across chunks
- **Applies when:** a Gemini Omni Flash 1.1 talking head cut into many chunks (here 14), each generated separately from the same still.
- **Failed:** the voice drifted from clip to clip. Measured: median pitch spread 2.5 semitones (184–218 Hz), a 3.5 dB level spread, brighter timbre on some chunks.
- **Why:** each Omni job invents its voice afresh.
- **Fixed by:** ⏳ *in this install.* The original fix (a local Praat PSOLA pitch match, 1/3-octave EQ and level match against the most central take) used a `match.py` and `praat-parselmouth` that are not installed here. Spira now lists `elevenlabs-voice-changer` (speech to speech), but it is admin-only and not in either toolkit: not used.
- **Carry forward:** on any multi-chunk Omni talking head, measure each chunk's pitch and level before the build. Level-match chunks with ffmpeg (`loudnorm`/`volume`). IF the pitch spread is over about 1 semitone, record it in the metadata's report and propose the lesson; don't regenerate for it.
- **Not for:** a single-clip talking head, or a voice-over that isn't lip-synced (there, one ElevenLabs voice for the whole VO).

### 2026-10-19 · bybit/06-office-fire-drill · Recast mirrored the source
- **Applies when:** any clone that replaces the source's people with new personas.
- **Failed:** every persona prompt copied its source person's ethnicity, outfit and accessories (down to orange glasses). Wan output lookalikes of the original cast and the whole clone was rejected (182 credits to recast 8 personas and redo 6 clips).
- **Why:** the persona prompts were written from Gemini's description of each performer instead of casting against it.
- **Fixed by:** ✅ for each slot, a contrasting ethnicity (often gender), outfit colours and no signature accessories, and the new outfit named in every Wan prompt. All 6 clips passed first time; the side-by-side reads as a new cast.
- **Carry forward:** before deciding personas, list each source person's look and deliberately cast against it. Keep only what the gag needs (who carries what). Check a side-by-side with the source before READY. *The house rights rule makes this mandatory: never the source creator's likeness.*
- **Not for:** nothing: *lookalike briefs are refused under the rights rule; recast anyway and record it.*

### 2026-10-19 · bybit/06-office-fire-drill · Wan multi-person replacement
- **Applies when:** Wan 3.0 `reference_to_video` on a source clip with 2+ people to replace, prompt naming references only by order.
- **Failed:** Wan kept all three source men (faces, clothes) and the source's folding chair and toys; only the new laptop came through (31 credits).
- **Why:** the order-only prompt didn't anchor identities when several people share the frame.
- **Fixed by:** ✅ "Replace all three men in video 1 with the three new men from images 1, 2 and 3, each with the face, hair and clothes from his image" plus each man's role, and "there is no pillow and no folding chair".
- **Carry forward:** for multi-person clips, write the explicit all-people mapping from the first take, and expect big central source props to survive. Check every face against its persona: *a surviving source face is a named failure and gets a retake, within the 2-extra-generations cap.*
- **Not for:** single-person clips, where the order-only prompt works.
- **Also seen:** 2026-10-19 · bybit/07-most-likely-coworkers: ✅ 5 of 5 faces correct in all five clips (5 people, 6 refs: personas in position order plus a plate). The prompt mapped every person by position ("the man sitting at the front left is the man from image 1; …"), said "each with the face, hair and clothes from their own image", and added "There are exactly five people". The first clip went alone as the check before the others were submitted. Small accessories still leaked (rings, a watch).

### 2026-10-19 · bybit/06-office-fire-drill · Soul mirror selfies
- **Applies when:** Soul persona prompts that say "phone shot", full body.
- **Failed:** 4 of 8 personas came back as mirror selfies holding a phone (28 credits to retake). A phone in the persona risks leaking into Wan's hands.
- **Why:** "phone shot" with no photographer reads as a selfie.
- **Fixed by:** ✅ "taken by a friend" plus "hands empty and relaxed at the sides".
- **Carry forward:** *the house Soul format ("UGC Casually taken shot of …") does not say "phone"; keep it so. Put "hands empty and relaxed at the sides" in the format's slots whenever the clip puts something in the hands.*
- **Not for:** selfie-format sources, where the phone in hand is the shot.
- **Also seen:** 2026-10-19 · bybit/07-most-likely-coworkers: "taken by a co-worker" put the photographer's arm or phone at the left edge in 3 of 5 images. Cropped locally (0 credits).

### 2026-10-19 · bybit/05-sort-tasks-talking-head · Omni false start
- **Applies when:** Gemini Omni Flash 1.1 talking head, a sentence opening with a short imperative and an acronym ("Run a DCA bot on Bybit…").
- **Failed:** Omni restarted mid-line ("Run a DCA, run a DCA bot…").
- **Why:** cause unknown.
- **Fixed by:** ✅ no retake. The false start (found on a 20 ms level profile) was cut out at the silence before the restart, and the clip split into two segments joined by a zoom jump cut, the device the source uses between chunks. 0 credits.
- **Carry forward:** check every chunk's transcript (`make-timings.py --txt`) for repeated phrases. In a jump-cut format, cut a false start at the silence before the restart instead of retaking.
- **Not for:** formats with no jump cuts (one continuous take); retake there.

### 2026-10-19 · bybit/04-taped-flyer-montage · Printed text across stills
- **Applies when:** one printed design (poster, flyer, sign, label) must look identical across many stills or fast cuts, made with GPT Image 2 edits that get the artwork as a reference.
- **Failed:** all 19 edits spelled the words right, but each re-typeset the poster and moved or resized the paper. Across 0.33 s cuts it would flicker (95 credits).
- **Why:** GPT Image 2 treats the reference as content to redraw, not pixels to keep.
- **Fixed by:** ✅ keeping GPT's walls, paper, light and tape, and printing the exact artwork locally: detect the paper box, warp the plate so the box lands at one fixed position, rebuild the paper's light field, multiply the artwork onto it, keep only the tape inside the paper's edge bands. 0 extra credits.
- **Carry forward:** for a repeated printed design, plan the local print step from the start. *Or place the artwork as an element in the stage over a plate, when the surface is flat and still.*
- **Not for:** a design that appears once, or text that bends with a moving surface (Wan 3.0 kept this same poster legible in motion).

### 2026-10-19 · bybit/03-street-walk-outfit-tags · Wan copies burned-in text
- **Applies when:** Wan 3.0 `reference_to_video` where the source clip has on-screen text burned in (tags, captions, watermarks) that the clone redraws in the stage.
- **Failed:** Wan redrew the source's tags, legibly and at the same positions and frames (62 credits).
- **Why:** Wan copies everything visible in the reference video, not only motion.
- **Fixed by:** ⏳ for the original clone (local cleanup only); ✅ the mask method in Also seen.
- **Carry forward:** before uploading a reference clip, check its frames for burned-in text and remove it with a text-pixel mask (`removelogo`), not a `delogo` box, and add "no text on screen" to the prompt. Check the Wan output for the source's text before building on it.
- **Not for:** text that should stay as part of the scene (a sign, a shop name).
- **Also seen:** 2026-10-19 · bybit/06-office-fire-drill: a `delogo` box doesn't vanish either; Wan reproduced the blurred strip (38 credits to redo 2 clips). ✅ Fix: a mask of just the text pixels (threshold above 195 inside the caption box, combined with a darken blend across 4 frames so the moving person drops out, then 5× `dilation` to cover the shadow) and `removelogo=mask.png`. Check a zoomed crop of the cleaned reference before uploading.

### 2026-10-19 · bybit/02-ceo-qna-interview · Job status flip
- **Applies when:** any Spira job that runs far longer than its siblings and then reports FAILED.
- **Failed:** the job read FAILED with 0 credits and no error, while `latestExecution` already said SUCCESS with a result URL. Minutes later it read COMPLETED.
- **Why:** cause unknown, probably a provider retry that finished after the job was marked failed.
- **Fixed by:** ✅ reading `latestExecution.resultUrls` and the status again before retaking; the file was complete and saved a 68-credit retake.
- **Carry forward:** on FAILED with `error: null`, re-check `spira --json ai jobs status` and `latestExecution` before planning a retake. *The shared `spira-jobs.py wait` stops on "no result": check the status before resubmitting.*
- **Not for:** FAILED with a real error (`content_flagged`, `provider_error`).
- **Also seen:** 2026-10-19 · bybit/05-sort-tasks-talking-head: gpt-image-2 2K edit, FAILED after 7 min with `error: null`, `latestExecution` SUCCESS but `resultUrls: null`, never flipped. Resubmitted unchanged, it completed in 42 s; the failure cost 0. If the re-check shows no result URL, resubmit once unchanged (*it counts as one of the 2 extra generations only if it is billed*).

### 2026-10-19 · cookiy/01-marketing-tier-list · Omni dropped last sentence
- **Applies when:** Gemini Omni Flash 1.1 talking head, a chunk whose last sentence is a short contrast clause starting a new sentence ("…at scale, fast. But you only get…").
- **Failed:** Omni stopped after "fast." and never said the last sentence: silent with 2.4 s of clip left (54 credits). Not a time cut-off.
- **Why:** cause unknown; likely Omni read the full stop before "But" as the end of the line.
- **Fixed by:** ✅ joining that sentence to the previous one with a comma ("…at scale, fast, but you only get…").
- **Carry forward:** when writing lines, don't start a chunk's final sentence with "But"/"And" after a full stop; join it with a comma (*before chunking, since the chunker never changes the text*). Always check the audio level after the last transcribed word: a silent tail with headroom means a dropped line.
- **Not for:** chunks whose last words are cut off at the clip's end (the entry below).

### 2026-10-19 · spira/02-marketing-tier-list · Omni chunk length
- **Applies when:** Gemini Omni Flash 1.1 talking head, a chunk near the top of its pace band, especially a closing line with commas or emphatic repeats ("never, ever"), or 2+ sentences, or an opening interjection.
- **Failed:** the clip ran out and cut the last words (45 credits). *Measured then on the full clip length; the shared chunker now counts speaking time (length minus 1 s) and keeps 4.9–5.2.*
- **Why:** the syllable count doesn't account for the pauses Omni puts in at commas and in emphatic sign-offs.
- **Fixed by:** ✅ the same line at the next duration up.
- **Carry forward:** *pace is the shared chunker's (4.9–5.2, never above 5.2); never chunk by hand. On a cut-off, follow the shared toolkit's order: regenerate once, then shorten only that chunk's line, then keep the best take.* Check every chunk's **tail**: it passes only if the level reaches **that clip's own** noise floor (10th-percentile window) at least 0.15 s before the clip ends or the cut. Transcripts often drop words: check the last 2 s on their own.
- **Not for:** chunks well inside the band; don't push everything to a longer duration, which leaves dead air.
- **Also seen:** 2026-10-19 · bybit/02-ceo-qna-interview: a 4 s chunk at a low pace with an interjection plus two full stops still cut the last word; the level "decayed" to −43 dB against a −57 dB floor, passed review, and the requester caught it. A tail passes only on its own floor.
- **Also seen:** 2026-10-19 · bybit/05-sort-tasks-talking-head: a one-sentence 6 s chunk ending on a brand name plus a clause ran over (−41 dB in the last 100 ms against a −65 floor). Pace varies by line: always run the tail check.

### 2026-10-19 · spira/02-marketing-tier-list · Still framing for overlays
- **Applies when:** a talking-head still that must put the head at a precise height because graphics or captions sit over the body, made with GPT Image 2 edits.
- **Failed:** the first edit framed too tight; the retake with explicit percentages overshot wide (10 credits).
- **Why:** GPT Image 2 doesn't follow numeric framing positions reliably.
- **Fixed by:** ✅ cropping the wider still locally (ffmpeg `crop`/`scale`, bottom-aligned) to put the chin where the source has it, then passing the crop to Omni.
- **Carry forward:** ask for a slightly wide framing, then crop locally to the exact layout. Crop every still of the set with the same box.
- **Not for:** stills already tighter than needed.

### 2026-10-19 · kfc/01-bitten-sign-reveal · Wan references
- **Applies when:** Wan 3.0 `reference_to_video` person replacement, where a product photo is a reference image but the product is only on screen for part of the clip, and the person holds something else the rest of the time.
- **Failed:** Wan put the burger in his hand for the whole 15 s clip and the cardboard disappeared, which killed the gag (93 credits).
- **Why:** the prompt never said **when** the product appears.
- **Fixed by:** ✅ keeping the product photo and writing the timeline into the prompt: "He is holding a bitten cardboard, then at 5 seconds he reveals he is taking a bite of the chicken burger from image 2." Dropping the photo had also stopped the swap, but left a generic burger: the inferior fix.
- **Carry forward:** for every referenced object not on screen for the whole clip, say when it appears, or what it replaces and at what second. Name what the person holds before and after.

### 2026-10-19 · kfc/01-bitten-sign-reveal · Wan sound
- **Applies when:** Wan 3.0 `reference_to_video`, 720p, 15 s clips, `sound: true`, reference audio stripped, and a source with no speech and no music (crowd ambience, soft eating sounds).
- **Failed:** Wan's native audio was music in both 15 s takes. An 8 s clip with the same setup came back as ambience.
- **Why:** cause unknown.
- **Fixed by:** ✅ `sound: false` and one ElevenLabs sound-effects ambience bed under the whole person section, extended from its steady middle (12 credits; checked by spectrum and level, not by ear).
- **Carry forward:** under these conditions, plan `sound: false` and one `elevenlabs-sound-effects` bed covering every person clip, about 4 s longer than needed.
- **Not for:** clips where the person speaks a new line through Wan, sources whose own track is music (the Suno route), or a sound that must land on a frame (a crunch on a bite).

### 2026-10-19 · kfc/01-bitten-sign-reveal · Stage joins
- **Applies when:** a stage editable with full-frame clips stacked to play one after another, where a later `<video>` has `data-start` above 0.
- **Failed:** the later clip covered the earlier one from 0 s.
- **Why:** the stage shows a clip's first frame before its `data-start`, and the later `<video>` sits on top.
- **Fixed by:** ✅ `opacity:0` on the later clip's wrapper plus a stepped CSS animation to opacity 1 at its `data-start`, which the renderer seeks.
- **Carry forward:** every stacked clip after the first gets a hidden-until-`data-start` animation, on a wrapper (stage rule 11).
- **Not for:** a deliberate freeze-in.
- **Also seen:** 2026-10-19 · bybit/01-coworker-hype-dance: a *linear* 1 ms reveal gave a half-transparent ghost frame at each cut, because frame times (1366.67 ms) land inside the ramp when `data-start` is 1367. Use `steps(1,start)` for reveals and `steps(1,end)` for hides, and round `data-start` down to the frame time (frame n starts at n×33.333 ms).
- **Also seen:** 2026-10-19 · bybit/05-sort-tasks-talking-head: back-to-back clips with window times written to 4 decimals left a frame showing neither clip (black at two joins). Open each clip's window at its floored `data-start` and keep the previous clip visible one frame past its end. Scan every rendered frame's brightness (`signalstats` YAVG) rather than spot-checking cuts.
- **Also seen:** 2026-10-19 · bybit/06-office-fire-drill: captions timed with `animation-delay` + `animation-duration` vanished on out-of-order seeks. Fix: one full-length animation per caption (duration = stage length), stepped keyframes at its in/out percentages, `steps(1,end)`, `fill-mode: both` (*as the stage skill's rule 3 requires*).
