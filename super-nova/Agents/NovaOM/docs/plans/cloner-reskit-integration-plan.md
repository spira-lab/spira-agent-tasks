# Plan: adding the Cloner and Re-skit agents to Super Nova

Status: INSTALLED (2026-10-24), tests on Test still to do. No system backup was taken before the install (a miss); one was taken after it: `Backup/back-up after installing Cloner and Re-skit 2026-10-24.zip`. Both skills were reviewed in full, read only, from `~/Downloads/Cloner Skill/` and `~/Downloads/Re-skit Skill/`.

## 0. What the two agents are, and which one gets a request

| | **Cloner** | **Re-skit** |
|---|---|---|
| What it does | Rebuilds a reference video's format for a brand: new lines, a new persona, new shots (Soul → GPT Image 2 plates → Wan/Omni/Kling clips, voice, music) in the house stage editable | Keeps the source's real motion, timing and voices, recasts the person (Wan person-replacement), and changes the meaning with cuts, overlays and rebuilt product screens |
| Typical source | ads, explainers, talking heads, product demos | trending skits, reactions, memes |
| Script | writes its own lines (scriptless for Echo) | rewrites through keep/cut/rewrite of the source's dialogue (scriptless) |
| Cost | ~95–130 credits for 15 s (first runs up to ~420) | ~140 credits per video, ~280 at 1080p |

**Routing rule for Nova:**
- **Re-skit** when the request keeps the source's own performance or audio ("re-skit", "same skit with our product", trends, reactions).
- **Cloner** when the format is rebuilt with new lines or a new voice ("clone this ad / video for Cookiy").
- If the wording doesn't make it clear, Nova asks the requester one question.

## 1. How Atlas assigns them

- Two new styles in `Agents/AtlasPM/docs/atlas-designers.json`, both scriptless:
  - `"clone": {"skill": "Agents/ClonerVideoDesigner/skills/cloner-video-designer.md", "script": "none"}`
  - `"re-skit": {"skill": "Agents/ReskitVideoDesigner/skills/reskit-video-designer.md", "script": "none"}`
- The same two phases as every designer:
  - **Design → READY:** source analysis, plan, persona and plates, all generations, the edit built.
  - **Render → DONE:** final render, checks, the share copy, then the `DONE <mp4> <credits> <minutes>` line (an `.mp4` in `renders/`, so Lark, Hermes and Iris work unchanged).
- **Concurrency:** no cap of their own; they run in the usual 6 designing / 2 rendering (the owner's rule, 2026-10-24, replacing a proposed cap of 2).
- **Approval gate (Re-skit's "nothing paid before go"):**
  - The designer stops at the plan with `QUESTION plan ready: <story in one line>, <n> jobs, ~<credits> credits`.
  - Nova posts it in the requester's thread, and the requester says go.
  - Plans over **400 credits** also need the owner's OK.
  - Atlas's existing QUESTION → ANSWER loop handles this.

## 2. How a request reaches Atlas

New column on the batch sheet, **Source video** (link or file). It is passed to the designer as `This is the source video: <link>`, and is not mixed up with Style ref.

```
nova-batch.py new "<Brand>" <n> --type organic-video|ad-video --style clone|re-skit \
  --source "<link>" [--avatar-image <persona>] [--product ...] --instructions "<language, market, what to change, music, competitor naming>"
```

- **Scriptless:** no Echo step. Rows are pending at once.
- **Persona:** the brand's avatar from the Avatar Designer (`Avatar image`). Each designer makes one only when none is given.
- **Request patterns:**
  - Lark: `@Nova clone this for Cookiy: <link>`
  - Lark: `@Nova re-skit this trend for PartGenie: <link>`
- **Code changes:**
  - `atlas-sheet.py`: COLS, `build_request`, a `scriptless` check.
  - `nova-batch.py`: a `--source` flag.
  - Nova's skill: routing and the request format.

## 3. Same project folder as every agent

Both skills are **adapted** into our layout, not installed as they are:

```
Project/<BrandName>/                      (same brand key as everyone: CookiyLabs, not cookiy-labs)
  editable/NN-name-MM-DD.html             Cloner: the stage editable. Re-skit: a stub that points to its build script
  editable/materials/NN-name-MM-DD/       source/, plan.md, persona/, stills/, clips/, audio/, build_edit.sh, jobs log (+ deletable/)
  renders/NN-name-MM-DD.mp4               the final video (+ deletable/ for old renders)
  metadata/NN-name-MM-DD.json             every job, model, prompt, credits, the source link, the method
```

- **NN is the Task ID.** It is never a count of folders.
- Failed takes go to `deletable/`, not to suffixed copies in place.
- **Brand-level assets that must survive backups** move out of `Project/` into `Agents/NovaOM/client-assets/<Brand>/`, because Jani clears Project:
  - Re-skit's `personas/` character sheets and the `outfits.md` never-repeat ledger;
  - Re-skit's `brand/truth.md`;
  - the Cloner's `brand-assets/`.
- Remove the hard-coded `/Users/leo/...` path and every path outside Super Nova. Tools are called from `Agents/<Agent>/tools/`.

## 4. Backup (Jani)

- Both agents write `metadata/NN.json` and an editable entry. Jani then recognises each video, backs up its whole `materials/NN/` folder with it, and records it in Nova's backup ledger.
- Brand-level assets live in `client-assets/`, outside Project, so a backup never clears a persona sheet or the outfit ledger.
- Their designer sessions are backed up the same way as the other designers'.
- **Test:** a `jani-backup.py plan` dry run on one test clone and one test re-skit, checking that every file is listed as part of its video and nothing lands in "other items".

## 5. Conflicts: what changes in the two skills (the shared rules win)

| Their rule | Our rule (kept) |
|---|---|
| Own `render-fast.js`, `stage-9x16.html`, `bgm-extend.py` (copies, 1 line older) | Use the shared ones; delete the copies |
| Whisper for timings and checks | `make-timings.py` (Scribe first, Whisper fallback) |
| Pace ≤ 4.0 syllables/s, no pad (Cloner) | Shared chunker: 4.9–5.2/s with Omni's 1 s silence pad |
| `gemini-omni-video` | Retired. Only `gemini-omni-flash-1.1` |
| Credits from the account balance before and after | Credits from each job (the account is shared) |
| One shared "Clone Source Understanding" workflow | One workflow per run, named with the Task ID (6 can run in parallel) |
| Polling loops, zsh scripts, Chrome binary, `sips` | `spira-jobs.py` waits; scripts run through `python3`/`node` or a few named tools added to Atlas's allowed list |
| Suno with lyrics | Instrumental unless the requester asks for vocals (owner decision below) |
| Unlimited retakes | At most 2 extra generations per clip, as in the toolkit |
| Recall/lessons file written inside the skill folder | Lessons go in the video's metadata; Nova adds them to a shared lessons file on the owner's OK |

Also needed: the ElevenLabs model IDs, and the missing voice-match tool (`match.py`).

## 6. Nova's roster, Lark and the docs

- **Nova's skill:** add both agents to the roster table and reply style (🧬 **Cloner**, 🎭 **Re-skit**), plus the routing rule and the request format.
- **Lark notes:** how the team asks, and how the plan approval appears in the thread.
- **One roster file**, `Agents/NovaOM/docs/nova-roster.json`, listing every agent (name, emoji, role, styles, status). The report, the workflow schematic and the SOP all read it, so a new agent is added in one place.
- **Updated:** the workflow schematic (both agents, the Source video column, the approval gate) and the SOP Lark doc (two new request types).

## 7. The report (Iris)

- **New page: "Skills used."** Videos per style per month and per brand (talking head, explainer, podcast, avatar, clone, re-skit), with credits per style. Counted from the batch sheets' Style and DONE lines.
- **"Agents" button:** opens a panel listing the agents available, with what each does and its status (from `nova-roster.json`).
- **New section "Agents in the system"** on the main page: cards for each agent and the designer styles Atlas can assign.

## 8. Schema updates

- **Batch sheet:** the new `Source video` column. Old sheets stay valid.
- **Designer metadata JSON:** `source`, `method`, `jobs[]` with credits, and `approval` (who said go, when).
- **New:** `nova-roster.json`.
- **Updated:** the workflow schematic and the dev notes.

## 9. Context budget and order of work

- **Can I carry this forward?** I can't read my exact context use. This session has been compacted once and has run a very long day, so it is heavily used. **Don't start implementing in this session.**
- **Order:**
  1. Now: save a full handover to memory, covering this plan file, the open items and the standing rules.
  2. 4:00 AM update: reset the context (fresh Nova session) and confirm the Lark loop and memory load.
  3. Fresh session: implement sections 1–8. The two skill adaptations are done by helper agents, each reviewed before install.
  4. Test both on **Test**: one clone and one re-skit, each under ~150 credits, including a Jani dry run and a report check.
  5. Then announce on Lark and update the SOP.
- The full install, tests included, likely won't fit in the 4:00–5:00 window. The context reset fits, and so does a start on the installs. Tests and client use follow.

## 10a. The owner's decisions (2026-10-24)

1. **Wan 3.0:** approved for shared use. Add it to the toolkit's model map.
2. **Pace:** the shared `chunker.py` rule (4.9–5.2 syllables/s, Omni clip length minus 1 s) whenever Omni Flash 1.1 speaks. Drop the Cloner's 4.0 rule.
3. **Vocals in music:** the agent decides on its own, without asking the requester. It makes music with vocals only when the video needs them (e.g. the source is a song or a sung trend); otherwise it stays instrumental.
4. **Rights:** cloning a format is common practice and allowed. Never use the source creator's actual face or likeness; always recast the person. **Re-skit always pitch-adjusts the kept source audio.**
5. **No approval gates.** Re-skit and Cloner never stop for plan approval; they run straight through. Spend stays visible through the credits line and the report. (This replaces §1's approval gate.)
6. **Personas:** the Avatar Designer is the one source of personas, including Re-skit's character sheets.
7. **Brand material:** the designer takes UI screenshots itself by visiting the brand's website. If none can be found or provided, it creates a believable one. Material the requester provides always wins.
8. **Brand DNA for every agent:** Nova supplies the brand's DNA (and its brand material) to every designer that needs it, including Cloner and Re-skit, whenever the brand has one in the ledger.
9. **Lessons file:** yes. Designers propose lessons in their metadata, and Nova adds them to the shared lessons file.

## 10. Decisions needed from the owner (answered in 10a)

1. **Wan 3.0:** approve it for shared use (both agents depend on it)?
2. **Pace rule:** the shared 4.9–5.2 with the 1 s pad (recommended), or the Cloner's 4.0?
3. **Vocals in music:** allowed in clones and re-skits only when the requester asks?
4. **Rights:** downloading third-party social videos, and keeping the source creator's audio or footage, internal tests only, or also client uploads? Naming competitors: never by default?
5. **Plan approval:** the requester approves, with the owner's OK needed above 400 credits?
6. **Personas:** the Avatar Designer is the one source of personas. Should it also make Re-skit's 7-panel character sheets?
7. **Brand material for Re-skit** (UI screenshots, screen recordings): who supplies it?
8. **Lessons files:** may the designers propose additions, with Nova writing them after your OK?
