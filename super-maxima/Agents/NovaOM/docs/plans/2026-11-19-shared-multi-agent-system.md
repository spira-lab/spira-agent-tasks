# Plan: one shared system for all agents (2026-11-19)

Requested by the owner (Leo) in the Lark group "Agent minis operations", 2026-11-18 23:56 (points 1 to 4)
and 2026-11-19 00:14 ("let's continue on the above plan 2 to 4"). Item 5 added 2026-11-19 00:48 ("Add it
to the update plans"). Announced to the SuperMaxima group on 2026-11-19 00:32 after the owner's OK.

Agents: Nova (this Mac, Claude app), Mario, Mars (terminal) and any new mini. **Max is frozen as the
prototype** (the owner, 2026-11-19: "we do not touch Max anymore"); Max was synced to Nova's 2026-11-18
system as the rollback point and is left out of everything below.

Source of truth for the code: this Mac's copy (the owner, 2026-11-18). Shared repo:
`github.com/spira-lab/spira-super-nova` (main = 694b830 after tonight's sync; Boris's earlier work on
branch `boris-xplat-2026-11-18`).

## Already done
1. Git repo updated: this Mac's system pushed to spira-lab/spira-super-nova and JeffHM14/super-nova
   (no force push).

## Decisions so far
- Lark Base for the shared tracking sheet: approved (the owner, 2026-11-19 00:23).
- Who claims a Task ID: Atlas, when a batch sheet is made (as today). Designers and the main agent
  update the row.
- Brand DNA owner: the main agent (Nova). Other minis pull only and ask in the group for changes.
- Iris (the report artifact) stays only on the main agent. It publishes under this Mac's Claude
  account, so other minis switch Iris off. The Base is the shared report anyone can open.
- Brand files stay inside spira-super-nova (the owner, 2026-11-19 00:50). They are already tracked
  there (565 files in client-assets). Only the main agent pushes brand changes.

## Order (each step starts with a system backup, the owner's rule of 2026-10-24)

### Step A: agent identity (point 4) and Atlas mode (point 5)
0. Back up `Agents/` and `Lark connect/` into `Backup/` and add a ledger row.
1. One local identity file per machine, `agent.json`, kept out of git: name, emoji, pronouns, avatar
   image, Lark profile and groups, and `atlas_permission_mode`.
2. Neutral names in the shared system (e.g. `Agents/OpsManager/` in place of `NovaOM`, `ops-*.py` in
   place of `nova-*.py`). CLAUDE.md, the hooks and the tools read the name and photo from agent.json.
3. Atlas mode follows the main agent's mode on that machine (point 5). The launcher passes
   `--permission-mode` from agent.json. Mars (terminal, bypass) gets `bypassPermissions`. This Mac
   (Claude app) keeps the allowed-tools list. Reason: Mars's main session runs in bypass and its Atlas
   didn't, so cross-session messages expired unapproved and designers were refused tools (Mars's
   report, 2026-11-19). Lark is the way in, so devices must not need approvals.
4. Guards that still hold in bypass (settings deny rules and a PreToolUse hook, both in the repo):
   - Block deletes outside `Project/`, `git push`/`reset`/force, `sudo`, and edits to settings or
     permission files.
   - A credit-cap check: stop any Spira job that would take a task past 500 credits without the
     owner's OK.
   - Higgsfield only with the owner's approval for that job.
5. Setup instructions in the repo: how to make agent.json and which mode to pick (terminal in bypass:
   Atlas in bypass; Claude app: allowed list).
6. Test on this Mac (Nova still works, Atlas runs a small batch, Lark still answers), then push to
   spira-lab. Mars pulls and fills its own agent.json.

### Step B: shared brand DNA and assets (point 3)
0. Back up.
1. Move the brand files (client-assets: truth, DNA links, personas, voices, anchor sheets, logos) to
   the shared place (they stay in spira-super-nova). Every agent pulls them.
2. Production records that change during work (outfit ledgers, used ideas) move to the shared Base,
   not git, so two agents never clash.
3. Tools read brand files from the shared location. Test, then push.

### Step C: one shared tracking sheet (point 2)
0. Back up.
1. One Lark Base table, one row per task: Task ID (auto-number), agent, brand, brand number, output
   type, style, requester, status, credits, date, video/doc link.
2. Task IDs come from the Base's auto-number, so two agents writing at once still get different IDs.
   Agents add rows and update only their own.
3. The task-ID and output-count tools write to the Base through one small tracking tool (run with
   python3, already allowed for Atlas). Atlas never gets lark-cli itself.
4. Reports read only the Base, so every agent shows the same counts. Projects stay on each machine.
5. Fresh start (the owner, 2026-11-19 01:02: "restart the counters ... the report starts at 0 on all
   brands again"): the Base starts at Task ID 1, and every brand's brand number and output counts start at 0. Each
   agent's old local register, monthly counts and Iris history are archived into its Backup folder,
   not deleted. Old video file names keep their old numbers; new names include the date, so they
   can't clash.
6. Test, then push.

## Status (2026-11-19 01:30)

- Step A done: agent.json and the Lark config are out of git, the loader and listener read the name
  from agent.json, Atlas runs in the machine's own mode, and the guard hook is on. Tested here in the
  normal mode. Bypass is untested (this session can't start one).
- Step B done: brand files stay in the repo, and only the main agent pushes. The production ledgers
  merge line by line (`.gitattributes`).
- Step C done: Lark Base "Spira Agents Task Tracker"
  (https://ljpp9tldvzuk.jp.larksuite.com/base/R3l9b36PAa8iHysamPWj5zUNpie), table Tasks, starting
  empty at Task ID 1. `tools/track.py` plus nova-task-id, nova-batch, nova-deliver, hermes-upload,
  nova-output and Iris use it. The old local counters are archived in Backup/.
- Still to do: the owner adds each mini's Lark app to the Base with edit access (Nova's bot couldn't
  add other apps). The credit-cap hard stop needs credits per task in the Base, added later. The
  ledgers aren't shared across agents yet (each mini keeps its own, merged on pull). A full ledger
  move into the Base is a later step.

