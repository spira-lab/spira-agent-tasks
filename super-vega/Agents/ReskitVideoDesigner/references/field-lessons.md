# Field lessons

What happened on real jobs, so the next plan starts from known ground. Read it before planning,
together with the shared `Agents/DesignerShared/docs/designer-lessons.md`.

**You never write to this file** (or to the skill or the other references). A job that teaches
something new proposes it in its metadata (`python3 <reskit>/tools/reskit.py lesson <materials>
"<lesson>"`); Vega adds it to the shared lessons file after the owner's OK (the owner's rule,
2026-10-24).

## Success rates so far

| Step | Result | Notes |
|---|---|---|
| Person replacement, `wan-3.0` reference-to-video, 720p, sheet + plate | **13 of 14 clips passed first time** | Identity, outfit, room, props and motion held across selfie, seated, standing, walking and a camera whip. The one failure was a prompt asking for a different gesture than the reference clip (below). |
| Outfit edits of a character sheet, `gpt-image-2` | 3 of 3 | Same face in all seven panels each time, outfit identical across panels. |
| Background plates, `gpt-image-2` | 6 of 7 | One full restyle moved the camera angle; a minimal material swap of the same plate kept it. |
| Original music, `suno-music` | usable on the first job when the brief was right | One job was wasted by briefing an instrumental for a source that had rap vocals. |
| Simulated product screens (HTML + headless Chrome) | worked once rebuilt from real screenshots | The first version, guessed from the web, was rejected as not looking like the real product. |

Render times for 4–13 s Wan clips ranged from 4 to 23 minutes; a few sit QUEUED for 20 minutes
before running. They do finish; don't resubmit (a duplicate costs the full price again).

## Lessons

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

**Practical tooling.**
Tools take absolute paths (background runs don't start in the project folder). The asset CDN
refuses Python's default user agent; the tools download with `curl` and a browser agent. An
ffmpeg limiter (`alimiter`) raises the level by itself unless its auto-level is off, which pushed
a -16 LUFS mix to -14.5; the build turns it off. Headless Chrome through playwright sets any
viewport size exactly (the old ~500 px minimum window of the Chrome command line no longer
applies), but large images still need shrinking so they load before the screenshot.
