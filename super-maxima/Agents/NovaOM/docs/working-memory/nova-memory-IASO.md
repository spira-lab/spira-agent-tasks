# Nova — Working memory — IASO

Preferences the user has given for this brand, applied to every task for it without asking
again. One preference per line: what, and when it applies. Written only when the user asks
Nova to remember something. Never added, changed, or removed otherwise.

## Production

How the batch sheet rows for this brand are filled.

- Style: `explainer`, for every IASO video, unless the request asks for a talking head (next line).
- No avatar: never fill Avatar image or Avatar voice for IASO, except on a talking-head row (next line).
- Talking head (Jekylle, 2026-11-05, after the Task 207 v3 test): when an IASO talking-head video is asked for, use style `talking head edited` with one of the two IASO personas, `Agents/NovaOM/client-assets/IASO/personas/sg_female_front.png` or `sg_male_front.png` (the requester says which; ask if not). No Avatar voice. Instructions: "Make her/his talking-head clips with gemini-omni-flash-1.1 using Omni's own native generated voice, in Singaporean English with a Singapore accent: no ElevenLabs voice-over, no HeyGen lip-sync. Build the voice track and caption timings from the Omni clips' own audio; check every clip for cut-off or changed words and regenerate a clip once if words are missing. Only one on-screen text for the end CTA." Plus the usual IASO line (transitions, no IASO logo or word on screen, scientific music), leaving out its ElevenLabs voice. The Omni native voice is for IASO talking heads only, never other brands.
- Talking-head outfits (Jekylle, 2026-11-05): every IASO talking-head video dresses the persona (female or male) in a different outfit: not the T-shirt from the persona photo and not an outfit used in an earlier IASO talking-head video. Both personas are physicians (Jekylle, 2026-11-05), so the outfit is always physician attire (white coat, scrubs) or a casual professional outfit. Add to Instructions: "She/he is a physician: change her/his outfit to new physician attire or a casual professional outfit, different from the persona photo and from earlier IASO talking-head videos (check Project/IASO/renders); keep the same face and hair."
- Instructions, on every IASO row: "Use this voice: elevenlabs cgSgspJ2msm6clMCkdW9 eleven_v3. Transitions are always effortful and purposeful; elements enter and exit dynamically, nothing simply appears or disappears. Never show the IASO logo or the word IASO on screen. Background music tone: scientific, not sad."
- Style sheets (the owner's OK, 2026-10-22): every IASO row gets a style reference from `Agents/NovaOM/client-assets/IASO/style-sheets/` (IASO_Style1.jpg … IASO_StyleN.jpg, all files in the folder), rotating through them across rows and batches (pass with `--style-ref` or set each row's `Style ref`). New sheets added to the folder join the rotation.
- Translation requests (an IASO video in another language): same voice; put the language in Instructions.
- Languages (Max's IASO protocol from Jekylle's brief 2026-10-15; Angelica's OK to copy it, 2026-11-03): unless the request names languages, rotate every batch's rows through Vietnamese, English (Singapore), Malay, Thai, Indonesian, repeating, so each gets about the same number. Append to each non-English row's Instructions: "For IASO no talking head, translate the script to this language: <language>. Make this video only in <language>: translate the script, generate the voice-over from the translation with the same voice, and put captions and all on-screen text in <language>. No English version." English rows get: "Language: English (Singapore market); no translation."
- Duration: 65 s (`--duration 65`); the final audio must be 60 to 70 seconds (same protocol).
- Echo brief, every IASO batch (same protocol; add these lines as Notes from Nova): "Educational videos about multiple myeloma and CAR-T, not product ads; the goal is medical awareness, not selling. Topics: multiple myeloma, relapsed disease, how CAR-T works, eligibility, preparation, side effects, follow-up, caregivers, treatment abroad. Fresh hooks every batch: check iasobio.com news, cartservice.top, current myeloma and CAR-T news, and awareness days; describe company news as company-reported; never present a trial or designation as an approval. Structure: a hook (a question, a surprising fact, or 'Did you know...'), one main idea explained simply, then a practical takeaway, usually a question to ask your doctor. 160-165 spoken words. The narration never says IASO, FUCASO, cartservice.top or any product name. No cure promises, never diagnose the viewer, never suggest supplements replace treatment. Plain, conversational English with no idioms, wordplay or country-specific references, so it translates cleanly; keep country-dependent advice (visas, insurance, carrying medicines, approvals) general. Each script file lists, off-screen and never spoken: sources, date checked, word counts, and an image cue. Writing style: Echo's explainer style (practical walkthrough)." (Switched from actionable educator on the owner's OK, 2026-11-06.)
- Optional end card (same protocol): "Learn more: cartservice.top".

## After a video is done

Follow-up assignments Nova makes as soon as Atlas reports the video done.

## Other
