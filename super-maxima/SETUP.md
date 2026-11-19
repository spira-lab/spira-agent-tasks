# Setting up an agent on a new machine

The same files run on every machine (Nova, Mario, Mars, ...). Two small files, kept out of git, make
each machine's agent its own. A `git pull` never changes them, so it never changes who an agent is.

## 1. Get the code

```bash
git clone https://github.com/spira-lab/spira-super-nova.git "Super Nova"
```

To update later, inside the folder:

```bash
git add -A && git commit -qm "local work" ; git pull --no-edit
```

Your projects, batch sheets, logs, Lark inbox and backups are not in git, so a pull never touches
them. The production ledgers (outfits, used ideas, angles) are merged line by line
(`.gitattributes`), so your own entries are kept. Only the main agent (Nova) pushes. Brand DNA and
assets come from her: ask in the group for a brand change, never push one.

Task IDs and output counts live in the shared Lark Base (`Agents/NovaOM/docs/tracker.json`), the same
for every agent. Your agent.json says `"tracking": "base"`.

## 2. Make `agent.json` (who this agent is)

Copy `agent.example.json` to `agent.json` and fill it in:

- `name`, `emoji`, `pronouns`: the agent's identity (e.g. Mars).
- `photo`, `photo_url`, `photo_description`, `photo_folder`: its own face. Never reuse Nova's.
- `session_name`: the name of this machine's main Claude session.
- `atlas_permission_mode`: match the main agent's mode.
  - Claude app (the main session asks before risky actions): leave it empty. Atlas uses its
    approved-tools list.
  - Terminal in bypass mode (`claude --dangerously-skip-permissions` or `--permission-mode
    bypassPermissions`): set `bypassPermissions`. Otherwise messages between the main agent and
    Atlas are held for approval and expire, and designers are refused tools.

Atlas always runs with `Agents/AtlasPM/docs/atlas-guard-settings.json`. Its guard
(`Agents/AtlasPM/tools/atlas-guard.py`) blocks git push/reset, sudo, recursive deletes outside
`Project/`, edits to permission and identity files, and Higgsfield without the owner's approval, in
every mode, bypass included.

## 3. Make `Lark connect/config.json` (which Lark bot it runs as)

Copy `Lark connect/config.example.json` to `Lark connect/config.json` and fill in this machine's Lark
bot: `app_id`, `lark_profile`, `bot_open_id`, `owner_open_id`, `chats`, `default_chat`, `people`.

## 4. Start

Open the folder in Claude Code and tag the agent (`@<name>`). Then say "start Lark".
