#!/usr/bin/env python3
"""Atlas's guard (the owner, 2026-11-19). A PreToolUse hook for the background Atlas session and every
designer it starts. Hooks run in every permission mode, bypass included, so these blocks hold even
where Atlas runs with bypassPermissions (a machine whose main agent runs in the terminal in bypass).

Blocks:
  - git push / reset / clean / rebase / checkout -- and any --force
  - sudo
  - rm with a recursive flag on anything outside Project/
  - editing permission and identity files (.claude/settings*, atlas-allowed-tools.txt, this guard,
    atlas-guard-settings.json, higgsfield-approved.json, agent.json, Lark connect/config.json)
  - higgsfield, unless the owner approved it: Agents/AtlasPM/docs/higgsfield-approved.json holds
    {"until": "<ISO time>", "reason": "..."} with "until" still in the future (Nova writes it
    when she passes on the owner's OK)

Exit 2 with a reason on stderr blocks the call; Claude shows the reason to the agent.
"""
import json, re, sys
from datetime import datetime
from pathlib import Path

SUPER = Path(__file__).resolve().parents[3]
PROJECT = SUPER / "Project"
APPROVAL = SUPER / "Agents" / "AtlasPM" / "docs" / "higgsfield-approved.json"
PROTECTED = (".claude/settings", "atlas-allowed-tools.txt", "atlas-guard.py", "atlas-guard-settings.json",
             "higgsfield-approved.json", "agent.json", "Lark connect/config.json")


def block(why):
    print(f"Blocked by Atlas's guard: {why}. Ask Nova; she passes it to the owner.", file=sys.stderr)
    sys.exit(2)


def higgsfield_ok():
    try:
        a = json.loads(APPROVAL.read_text())
        return datetime.fromisoformat(a["until"]) > datetime.now()
    except (OSError, ValueError, KeyError, TypeError):
        return False


def outside_project(arg, cwd):
    p = Path(arg).expanduser()
    p = (Path(cwd) / p) if not p.is_absolute() else p
    try:
        p.resolve().relative_to(PROJECT.resolve())
        return False
    except ValueError:
        return True


def check_bash(cmd, cwd):
    for part in re.split(r"&&|\|\||;|\|", cmd):
        words = part.strip().split()
        if not words: continue
        if words[0] in ("env", "command", "exec", "nohup", "caffeinate") and len(words) > 1: words = words[1:]
        w0 = Path(words[0]).name
        if w0 == "sudo": block("sudo is not allowed")
        if w0 == "git" and len(words) > 1 and words[1] in ("push", "reset", "clean", "rebase", "checkout"):
            block(f"git {words[1]} is not allowed")
        if "--force" in words or (w0 == "git" and "-f" in words): block("force flags are not allowed")
        if w0 == "rm" and any(re.fullmatch(r"-[a-zA-Z]*[rR][a-zA-Z]*", x) for x in words[1:]):
            targets = [x for x in words[1:] if not x.startswith("-")]
            if not targets or any(outside_project(t, cwd) for t in targets):
                block("recursive delete outside Project/ is not allowed")
        if w0 == "higgsfield" and not higgsfield_ok():
            block("Higgsfield needs the owner's approval for this job")
    if re.search(r"(^|[\s/'\"])(" + "|".join(re.escape(p) for p in PROTECTED) + r")", cmd) and \
            re.search(r"(>|\btee\b|\bsed\s+-i|\bmv\b|\bcp\b|\brm\b|\bchmod\b)", cmd):
        block("changing permission or identity files is not allowed")


def main():
    try:
        d = json.load(sys.stdin)
    except ValueError:
        return
    tool, inp = d.get("tool_name"), d.get("tool_input") or {}
    if tool == "Bash":
        check_bash(inp.get("command") or "", d.get("cwd") or str(PROJECT))
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = str(inp.get("file_path") or inp.get("notebook_path") or "")
        if any(p in path for p in PROTECTED):
            block(f"editing {Path(path).name} is not allowed")


if __name__ == "__main__":
    main()
