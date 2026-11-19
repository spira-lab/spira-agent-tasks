# House rules (from the Super Mario template, 2026-11-15)

Rules the owner gave over time, written down so every agent running this folder follows them. "Nova" means whichever agent runs this folder.

1. **Reply where the request came from.** When a request comes in on Lark, every follow-up (results,
   links, blockers, questions) goes back in that Lark chat or thread, not only in the desktop chat. Use
   `python3 "Lark connect/lark-nova.py" reply <message_id> --thread` (every reply goes in a thread,
   see `Lark connect/nova-lark.md`).
   (The owner, 2026-10-29.)
2. **Acknowledge owner DMs first.** When the owner DMs on Lark, reply in that DM right away, even just
   "On it, I'll ping you when X". Do this before finishing in-flight work, then follow up when it's done.
   (The owner, 2026-11-12.)
3. **Send Lark replies as text, not files.** Write long drafts to a scratch file and send them with
   `--text "$(cat draft.txt)"`. `--file` sends a .txt attachment, so use it only for real deliverables
   (videos, images, docs). (The owner, 2026-11-07.)
4. **Team docs need no approval.** Anyone on the team may ask for a Lark doc. Build it and share it right
   away (`python3 Agents/NovaOM/tools/nova-doc-share.py <docx token> <requester open_id>`). The requester
   and the owner get full_access, the team group gets view. Public links and outside parties still need a
   fresh OK. (The owner, 2026-10-30.)
5. **Walkthrough docs.** A task walkthrough doc (Lark docx) has:
   - each step with IN/OUT pictures in grids, and the finished video at the end;
   - the source reel link at the top of Step 1;
   - the exact prompt under each generation step, word for word from the task's metadata JSON, with the
     tool, credits, settings and job ID. Failed 0-credit attempts are left out; local steps say "no prompt".

   Build it with `Agents/NovaOM/tools/nova-walkthrough-doc.py <steps.json> "<title>" <final video>`.
   (The owner, 2026-11-05.)
6. **Never suggest the owner do work by hand.** When a tool or provider is down, offer only options the
   agents carry out: waiting and retrying, another provider, or a tool-list change the owner approves.
   (The owner, 2026-11-14.)
7. **Relay the owner's fix orders exactly.** Pass a fix instruction to Atlas as the owner said it. Never
   add changes of your own to the set, outfit or composition. A "new plate" is a fresh generation of the
   same scene and layout. Only technical guardrails (checks, budget, asking before overspending) may be
   added. (The owner, 2026-11-14.)
8. **Higgsfield CLI is for approved use only.** `Bash(higgsfield:*)` stays in
   `Agents/AtlasPM/docs/atlas-allowed-tools.txt`. Designers use the usual Spira Wan route unless the
   owner OKs Higgsfield for a specific job or outage. When Wan recovers, tell Atlas to go back to the Spira
   route. (The owner, 2026-11-14.)
9. **Report a 4th fix request.** When a video has had 3 revisions and someone asks for a 4th fix, do
   not start it. Report in the request's thread, tagging the owner (ou_51ce6f46d54cf00324117fffed05336d)
   and Jekylle (ou_d570668ca100d265524c3a1bd2ca9536), with the video's revision history and credits so far,
   and attach the current video. Wait for their call. (The owner, 2026-11-18.)
10. **A revision regenerates the whole clip.** When a generated clip needs correcting, regenerate that
    entire clip. Never regenerate just a portion of it, run eye or feet passes, splice in pieces of other
    takes, or swap frames. Partial fixes drift, cause more hallucinations and more revisions, and end up
    costing more (Task 640). Edit-only fixes that regenerate nothing (captions, colours, audio, keys) are
    still fine. If the whole clip would take the video past the credit cap, ask the owner first. (The owner,
    2026-11-18: "also revisions moving forward should be regenerating the entire clip of what's need correction not a portion of it as it will cause drift and lead to more revision like the 640.")
