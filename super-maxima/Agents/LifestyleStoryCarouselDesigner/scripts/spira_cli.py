"""Find the Spira CLI. On Windows `spira` is a .cmd wrapper that subprocess can't run reliably
(it mangles JSON quotes), so call its Node entry point directly."""
import os, shutil, sys

def spira_cmd():
    p = shutil.which("spira")
    if not p:
        sys.exit("Spira CLI not found. Install it: npm install -g @spira-lab/cli, then spira auth login")
    if p.lower().endswith((".cmd", ".bat", ".ps1")):
        entry = os.path.join(os.path.dirname(p), "node_modules", "@spira-lab", "cli", "dist", "index.cjs")
        if os.path.exists(entry):
            return ["node", entry]
    return [p]
