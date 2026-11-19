# Nova — Working memory — Emochi

Preferences the user has given for this brand, applied to every task for it without asking
again. One preference per line: what, and when it applies. Written only when the user asks
Nova to remember something. Never added, changed, or removed otherwise.

## Production

How the batch sheet rows for this brand are filled.

- Instructions on every Emochi video (the owner's rule, 2026-10-26): "No on-screen source lines or citations. Keep the objective strong: lean into the character.ai controversy (c.ai could shut down; who gets your private chats) and the switch to Emochi. Don't water down the angle for IP or sourcing caution, and don't drop beats because sources differ. Approved framing: c.ai is shutting down (say it plainly, no hedging). Never invent a specific event: no claim that c.ai's data leaked, was exposed or hacked, and no claim that Disney bought c.ai."
- Social framing (the owner's word, 2026-10-26): "c.ai is shutting down", said plainly. Don't play safe: no "might/could shut down" or "if nobody buys it" hedging. Use the owner's or requester's wording as given. (Also in the designers' Emochi truth file, `client-assets/Emochi/brand/truth.md`.)

- Re-skit end card (Jekylle, 2026-11-17, after approving Task 548): every Emochi re-skit ends on Jekylle's end card, `Agents/NovaOM/client-assets/Emochi/brand/endcard/emochi-endcard-2026-11-17.mp4` (3.5 s, 1080x1920, no audio: Emochi icon, "Start any drama with any character", 4.5 stars, 10M+ downloads, Google Play badge; source: Lark folder https://ljpp9tldvzuk.jp.larksuite.com/drive/folder/ZwJLfEZ69l36XfdRQxJj4biMpFf). Put in Instructions: "End the video on the Emochi end card, Agents/NovaOM/client-assets/Emochi/brand/endcard/emochi-endcard-2026-11-17.mp4, used as is (no other end card); keep the music running under it."

- Emochi personas (the owner, 2026-11-19): a request naming Emochi and one of its 8 personas (Ashley, Gabby, Jasmine, Lexi, Mia, Natalie, Rachel, Zoe) uses that persona as the on-camera creator, built with `nova-emochi.py new` (see "Emochi personas" in Nova's guide). No regens. Hermes uploads each under its own persona tag in the Emochi category.

## After a video is done

Follow-up assignments Nova makes as soon as Atlas reports the video done.

## Other

- first project (2026-10-26): videos nudging character.ai users to switch to Emochi (from Quill's approved brief)


## Lark Drive folder (the owner, 2026-10-27)
- Finished Emochi videos the owner asks for go to the Lark folder "NO.029 Emochi": https://ljpp9tldvzuk.jp.larksuite.com/drive/folder/RY9ofhW6klCV1LdgdcfjbGPhpGh (token RY9ofhW6klCV1LdgdcfjbGPhpGh).
- Upload with `lark-cli drive +upload --as user --folder-token RY9ofhW6klCV1LdgdcfjbGPhpGh --file <render> --name "<name>"`. The bot identity has no Drive scope, so `--as bot` fails.
- Name files like the folder's others: `NO.029 - Emochi - <next number> <short title> - Nova - v1.mp4`. Nova's 14 = Emochi #04 Lilith (Task 325), 15 = Emochi #05 Snow (Task 326).
