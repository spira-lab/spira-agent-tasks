# Field lessons

What happened on real jobs, so the next plan starts from known ground. Read it before planning,
together with the shared `Agents/DesignerShared/docs/designer-lessons.md`.

**You never write to this file** (or to the skill or the other references). A job that teaches
something new proposes it in its metadata (`python3 <reskit>/tools/reskit.py lesson <materials>
"<lesson>"`); Nova adds it to the shared lessons file after the owner's OK (the owner's rule,
2026-10-24).

## Success rates so far

| Step | Result | Notes |
|---|---|---|
| Person replacement, `wan-3.0` reference-to-video, 720p, sheet + plate | **13 of 14 clips passed first time** | Identity, outfit, room, props and motion held across selfie, seated, standing, walking and a camera whip. The one failure was a prompt asking for a different gesture than the reference clip (below). |
| Outfit edits of a character sheet, `gpt-image-2` | 3 of 3 | Same face in all seven panels each time, outfit identical across panels. |
| Background plates, `gpt-image-2` | 6 of 7 | One full restyle moved the camera angle; a minimal material swap of the same plate kept it. |
| Original music, `suno-music` | usable on the first job when the brief was right | One job was wasted by briefing an instrumental for a source that had rap vocals. |
| Simulated product screens (HTML + headless Chrome) | worked once rebuilt from real screenshots | The first version, guessed from the web, was rejected as not looking like the real product. |
| Re-voicing, `wan-3.0` reference-to-video with sound on, 720p | **held every time no source speech reached the model**; failed every time it did | Every planned word came back in order and on its time when the reference was silent and the lines were written with times. With the source's speech in the reference video or audio, the old words came back. |
| A single take longer than one reference, `wan-3.0` | **copying the opening and extending it worked** | Copying the second half from its own reference opened on the plate's view; a sped-up reference lost the camera after half its length. |
| Brand screens on a phone in the scene, `wan-3.0` | **two passes worked; one pass and overlays didn't** | Laid-on screens read as overlays and slipped under fingers. One pass copied the source screen's reactions, invented buttons and skipped states. Green screen first, then only the green stretch filled from a screen video, showed every state in order with no copied content. |

Render times for 4–13 s Wan clips ranged from 4 to 23 minutes; a few sit QUEUED for 20 minutes
before running. They do finish; don't resubmit (a duplicate costs the full price again).

## Lessons

**Source speech in the reference brings the old words back.**
When the source's audio was in the reference video or sent as reference audio, Wan replaced the
person well but its soundtrack was essentially the source's own audio: old words, old voice, the
new script ignored, or a mix of old and new words. A silent reference with no reference audio, the
voice described in words and every line written with its start time, gave every new word on time.

**Burned-in captions in the reference come back as invented captions.**
Captions left in a reference reappear in the result as the model's own, often misspelled. Masked
first, they don't.

**Re-voice the whole speaking part from one script.**
The voice is generated from a description, so a kept source line beside a generated one changes
voice at the cut. Writing the kept lines into the script word for word keeps one voice through
the video, and the same voice sentence in every clip keeps clips close.

**A clip can run longer than its reference.**
With the clip's duration set past the reference's length and a line written there, the model
followed the reference's motion for its length, then continued the performance itself: same
person, room and way of moving, every line heard. Wan 3.0 can continue a performance like this (the owner, 2026-11-05),
so a longer delivery is a matter of a longer duration, not a longer reference. The ceiling is the
reference and the output together: Wan rejects a job whose reference video plus output passes
30 s (a 15 s reference allows at most 15 s out; a 10 s reference, 20 s). A line placed in the continued stretch can start slightly earlier than
asked.

**A long single take: copy the opening, then extend it.**
A 24 s handheld shot was too long to copy in one job. The first 12 s copied as an ordinary clip.
That clip went back in as Video 1 with "Extend Video 1 forward by 12 seconds", the same images, a
timed shot list of the source's remaining beats and the remaining lines. Wan returned only the new
12 s, continuing straight on with the same faces, room and voices. Every beat landed close to its
time, and the reveal faced the camera as described. Its gestures and camera were its own, not the
source's. The owner preferred this to copying the second half from its own reference (2026-11-06).

**A later part copied from its own reference opened on the plate's view.**
The second half of the same shot, copied from its own reference, began on a reference frame
blurred by a whip pan. Wan opened that clip on a wide view taken from the background plate, which
was not in the source. The second half also brought back what the plate held, where the first half
had kept it out of sight.

**Every part extending the first clip kept a long talking head consistent** (the owner,
2026-11-09). A 57 s talking head was made as one copied clip A and three parts that each extended
A (not each other). Every line came back in order, and the face, outfit, prop and voice matched
across all parts. The only seam is a jump cut between parts, on the same framing.
Separately generated talking-head clips drift in voice tone from one to the next; extensions keep
the first clip's voice. Copy a new clip from the source only for a new action with a new camera
angle or shot; same-setup movement goes in the extension's prompt.

**Squeezing the source to fit one reference didn't hold.**
The whole 24 s source sped up four times (a 6 s reference) with a 24 s output kept every line on
time. But the clip followed the source's camera only loosely for about half its length, then sat
on one static wide shot to the end.

**A logo in the plate came back despite the prompt.**
Takeaway cups with a coffee chain's mark were in a background plate. "Plain cups, no logos" in the
clip prompt didn't stop Wan from painting the mark back. Editing the plate to plain mugs did.

**Describing the look drifts across scenes** (the owner, 2026-11-05).
Naming the outfit, hair, items or objects in clip prompts makes clips of a multi-scene video come
back different from each other. Pointing to the references ("the outfit from image 1") in the
same words in every clip holds, even where a single described clip happens to look right.

**A screen drawn in the same pass as the recast leaks the source's screen.**
Asked to recast the people and put a new screen on the device in one generation, Wan copied the
source app's own reactions onto the new screen (a like animation, a header from the source
creator's profile), invented a button, and never showed the last screen state. With the screen
plain green in the first pass and only that stretch filled in a second pass, none of it came
back and every state appeared in order.

**The screen follows the hands, not the screen video's clock.**
Moving every event in the screen video a second earlier changed nothing: the screen still changed
with the hand's own actions in the source, scrolling when the hand scrolled and opening when it
tapped. The screen video sets the order of the states; the hand in the source sets their timing.

**Overlays read as overlays** (the owner, 2026-11-06).
Screens tracked onto a green or white screen in the edit looked flatter, sharper and more evenly
lit than the scene, and slipped when a finger covered a corner. A screen the model draws takes the
scene's light, glare and perspective. This holds for phones; on a laptop the overlay won (next).

**Laptop and monitor screens: the overlay looked better** (the owner, 2026-11-07).
Task 277 remade Task 95's laptop shots with the screen drawn by Wan in two passes; the owner
judged Task 95's overlay the better result. Laptops and monitors are overlaid again, with the
screen tracked and kept in perspective on every frame so it doesn't slip when the camera moves
or when a hand or object briefly covers it.

**A second pass drifts a little by its end.**
Re-running a 5 s stretch kept the first frame almost identical to the first pass, but by the end
the framing had shifted a few pixels, which showed as a small jump at the second join. A 4-frame
crossfade hid it.

**Empty space on a screen video gets filled with invented UI.**
A state that left blank space at the bottom of the screen came back with a made-up app tab bar
with garbled labels, and a mid-size heading garbled too. Rebuilt to fill the screen edge to edge
with real content, the redo came back clean.

**The green stretch landed longer than asked.**
Pass 1 was asked for green between two moments and came back green from a little earlier to a
little later. Pass 2 was priced for the planned stretch and had to be a second longer. Measure the
landed green before cutting or pricing pass 2.

**The screen changed on the most visible tap, not the first one.**
The source had a light tap followed by a firm double tap; the new screen changed on the double
tap, about a second after the planned moment. Text timed to the planned moment had to move.

**The off-camera filmer's hands kept the source's jewellery.**
Asked for "plain hands with no jewellery", the clip kept the bracelets and long nails of the
source creator's hands. Hands that come into frame from the camera follow the reference closely;
changing them is a gesture-level change, not a prompt detail.

**A generated outfit carried another company's logo.**
An outfit sheet's sneakers came out with a recognisable brand mark, and the clips copied it. Check
the outfit sheet for logos and marks before approving it.

**A prompt can't replace a gesture that's in the reference clip.**
Asked to have the person text on her phone instead of holding it to her ear, the model kept the
arm going up to the ear and added a phone held in both hands, giving three hands. Keep the
source's action and change its meaning with text, or make a new shot. A text overlay ("ending up
voice chatting him") over the original phone-to-ear pose was the version that shipped.

**Thin caption masks leave ghost letters.**
A mask of only the bright text pixels, lightly dilated, left the text's dark outline behind, and
the letters stayed readable. Dilating far enough to cover the outline left a soft smear instead,
which the model repainted cleanly in every clip.

**A reference clip picked up one frame of the next shot.**
A clip ending 0.02 s before a cut contained a frame of the next shot after frame rounding. Scan
every reference clip for scene changes (`cutref` does), and end it a few frames before a cut.

**A held frame didn't happen because a second `-t` overrode the first.**
`-ss S -i src -t LEN … -t DUR` plays real footage for DUR. Trim on the input side
(`-ss S -t LEN -i src`) and the `tpad` hold works. `cutref` does it this way.

**Speech recognition hearing nothing under a beat isn't proof of no vocals.**
A source with rap vocals measured as "instrumental" and the first music job came back wrong.
When the source is music, look for other evidence (the platform's track info, people mouthing
words, the genre) and treat lyrics-mode silence as inconclusive.

**A music window that starts mid-word sounds broken.**
Pick the window from word timestamps so the first sound is a clean entry, then check where the
hook and the edit's turning point land.

**Restyling a room can move the camera.**
A full restyle produced a different angle; asking only for new colours and materials on the same
shapes kept the framing. For video-model references the angle matters less (the camera comes
from the source clip); for plates that must line up with footage it matters.

**Text with boxes looked like an ad; text under the platform UI was unreadable.**
White boxes behind captions and pop-ups were rejected; plain outlined text was approved. Pop-ups
placed low in the frame were covered by the platform's caption and buttons; moved into the safe
area they read cleanly.

**A freeze-frame ending felt stuck when it wasn't needed.**
Holding the last frame for 1.5 s worked when the final shot was under a second long and the line
needed reading time. The same hold at the end of a shot that already ran long looked like the
video froze.

**A simulated conversation that was too cold read as a reason to quit the product.**
One-word replies made the product look bad rather than making the situation funny. The fix was a
real back-and-forth where the character stays in character and teases, and each step was held
long enough to read (about 2.5–3 s).

**A small pitch lift worked; a bigger one sounded processed.**
+1.5 semitones was too high; +0.6 semitones (resample and tempo-correct, so length and lip sync
hold) was approved. Kept source audio is now always pitch-adjusted (the owner's rule).

**A guessed UI and a stand-in emoji logo were caught immediately.**
Rebuilding the screen from real screenshots and a screen recording (real header, navigation,
row layout, unread dots, timestamp style, narration style) and pulling the real logo from the
brand's own site fixed it. Also clean the recording: paint out the recording dot, and don't show
account names or third-party IP from the catalogue.

**The footage implied a feature the brand doesn't have.**
A phone-call pose suggested voice calls; the brand only has voice messages. Checking the brand's
own pricing and app strings caught it, and the text was written around what exists.

**A news hook was stronger than the facts.**
"About to shut down" was stated about a competitor whose real status was a bankruptcy filing with
a sale pending. The hook became "might be shutting down", and the named-competitor version was
delivered separately and flagged for a legal check.

**A delivered video was missing its vocal, and an intermediate test hid it.**
A one-step render (video + vocal + instrumental through one filter graph) came out with only the
instrumental, while a separate mono test of "the same chain" sounded fine. Render the audio mix
on its own, check it, then attach it to the video (`build_edit.py` does). Verify the delivered
file itself: transcribe it, and if speech recognition hears only "music", treat that as a failure
to investigate, not a quirk to explain away.

**Practical tooling.** Tools take absolute paths (background runs don't start in the project
folder). The asset CDN refuses Python's default user agent; the tools download with `curl` and a
browser agent. An ffmpeg limiter (`alimiter`) raises the level by itself unless its auto-level
is off, which pushed a -16 LUFS mix to -14.5; the build turns it off. Headless Chrome through
playwright sets any viewport size exactly (the old ~500 px minimum window of the Chrome command
line no longer applies), but large images still need shrinking so they load before the
screenshot. `build_edit.py` and `reskit.py audio-probe` need numpy; a python3 without it fails,
so run them with a python that has it. `reskit.py strip --times` takes times on the clip's own
clock, not the source's. After a redo, the chain's running "credits so far" line can undercount;
the total comes from each job's own charge.
