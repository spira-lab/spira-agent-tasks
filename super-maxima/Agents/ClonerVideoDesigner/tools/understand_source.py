#!/usr/bin/env python3
"""Have Gemini watch and listen to a source video, through a Spira workflow made for this run only.

usage: python3 understand_source.py <video file or public URL> --task-id <Task ID> [--out <understanding.md>]

- Paths may be absolute, relative to the current folder, or relative to the Super Nova folder
  (e.g. Project/CookiyLabs/editable/materials/07-cookiylabs-10-24/source/source.mp4).
- uploads a local file to Spira first (spira assets upload)
- uses the workflow named "Clone Source Understanding <Task ID>" on the signed-in account, or creates it
  from ../references/source-understanding-workflow.json. One workflow per run, so parallel runs never
  overwrite each other's video input.
- sets ONLY the video URL on the workflow's video input and sends the full definition back
  (a partial definition would wipe the Gemini node)
- starts a run, waits for it (about 30 s, about 2 credits), prints the breakdown, and prints the run's
  credits when Spira reports them ("credits: <n>" or "credits: not reported, estimate 2")
- --out must be inside Super Nova/Project/ (or the system temp folder); only folders inside Project/
  are ever created.
Standard library only; needs the Spira CLI, signed in. Run with python3.
"""
import json, os, re, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUPER = HERE.parents[2]                      # tools -> ClonerVideoDesigner -> Agents -> Super Nova
PROJECT = SUPER / "Project"
DEF_FILE = HERE.parent / "references" / "source-understanding-workflow.json"
BASE_NAME = "Clone Source Understanding"


def resolve_in(p):
    """An input path: absolute, relative to the current folder, or relative to Super Nova."""
    q = Path(p).expanduser()
    if q.is_absolute():
        return q.resolve()
    if q.exists():
        return q.resolve()
    return (SUPER / q).resolve()


def resolve_out(p):
    """An output path inside Project/ (folders created only there) or the system temp folder."""
    q = Path(p).expanduser()
    if not q.is_absolute():
        q = (SUPER / q) if q.parts and q.parts[0] in ("Project", "Agents") else (Path.cwd() / q)
    q = q.resolve()
    temps = {Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()}
    if q.is_relative_to(PROJECT):
        q.parent.mkdir(parents=True, exist_ok=True)
        return q
    if any(q.is_relative_to(t) for t in temps):
        if not q.parent.is_dir():
            sys.exit(f"{q.parent} does not exist (only folders inside {PROJECT} are created)")
        return q
    sys.exit(f"--out must be inside {PROJECT} or the system temp folder, not {q}")


def spira(*args):
    r = subprocess.run(["spira", "--json", *args], capture_output=True, text=True)
    t = r.stdout + r.stderr
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        sys.exit(f'spira {" ".join(args[:3])}: no JSON in output:\n{t[:800]}')
    d = json.loads(m.group(0), strict=False)
    if d.get("status") == "error":
        sys.exit(f'spira {" ".join(args[:3])} failed: {(d.get("error") or {}).get("message")}')
    return d.get("data") or {}


def find_credits(obj):
    """The first numeric 'credits'-like field anywhere in a run record, or None."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("credits", "creditsused", "credits_used", "totalcredits", "cost") and isinstance(v, (int, float)):
                return v
        for v in obj.values():
            c = find_credits(v)
            if c is not None:
                return c
    elif isinstance(obj, list):
        for v in obj:
            c = find_credits(v)
            if c is not None:
                return c
    return None


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    src = args[0]
    if "--task-id" not in args:
        sys.exit("--task-id <Task ID> is required: the workflow is named with it so parallel runs never collide")
    task = args[args.index("--task-id") + 1].strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", task):
        sys.exit(f"--task-id must be letters, digits, - or _, not {task!r}")
    name = f"{BASE_NAME} {task}"
    out_file = resolve_out(args[args.index("--out") + 1]) if "--out" in args else None

    # 1. a public URL for the video
    if re.match(r"https?://", src):
        url = src
    else:
        f = resolve_in(src)
        if not f.is_file():
            sys.exit(f"no such video: {f}")
        up = spira("assets", "upload", str(f))
        url = up.get("url") or (up.get("asset") or {}).get("url")
        if not url:
            sys.exit(f"upload gave no URL: {json.dumps(up)[:400]}")
    print("video:", url, file=sys.stderr)

    # 2. this run's workflow: find it by its exact name, or create it
    lst = spira("workflows", "list")
    items = lst if isinstance(lst, list) else (lst.get("items") or lst.get("workflows") or [])
    wf = next((w for w in items if w.get("name") == name), None)
    if not wf:
        defn = json.loads(DEF_FILE.read_text(encoding="utf-8"))["workflowDefinition"]
        created = spira("workflows", "create", "--name", name, "--visibility", "private",
                        "--workflow-definition-json", json.dumps(defn))
        wf = created.get("workflow", created)
        print("workflow created:", name, wf.get("id"), file=sys.stderr)
    wid = wf["id"]

    # 3. set only the video URL, send the whole definition back
    full = spira("workflows", "get", wid)
    defn = (full.get("workflow") or full)["workflowDefinition"]
    vids = [n for n in defn["nodes"] if n["type"] == "videoInput"]
    llms = [n for n in defn["nodes"] if n["type"] == "textChatLlm"]
    if not vids or not llms:
        sys.exit(f"workflow '{name}' is missing its video input or Gemini node; rename it in Spira and run again to recreate it")
    vids[0]["data"]["videoUrl"] = url
    spira("workflows", "update", wid, "--workflow-definition-json", json.dumps(defn))

    # 4. run and wait (inside this tool, so no shell loop is needed)
    run = spira("workflows", "runs", "start", wid)
    rid = (run.get("run") or run).get("id") or run.get("runId")
    if not rid:
        sys.exit(f"no run id: {json.dumps(run)[:400]}")
    t0 = time.time()
    while time.time() - t0 < 600:
        r = spira("workflows", "runs", "get", rid)
        st = ((r.get("run") or r).get("status") or "").lower()
        if st in ("success", "completed", "succeeded"):
            text = (((r.get("nodeStates") or {}).get(llms[0]["id"]) or {}).get("outputs") or {}).get("text", {}).get("value", "")
            c = find_credits(r)
            print(f"done in {int(time.time() - t0)} s; workflow {name}; run {rid}", file=sys.stderr)
            print(f"credits: {c}" if c is not None else "credits: not reported, estimate 2", file=sys.stderr)
            print(text)
            if out_file:
                out_file.write_text(text, encoding="utf-8")
                print("wrote", out_file, file=sys.stderr)
            sys.exit(0 if text.strip() else 1)
        if st in ("failed", "error", "cancelled", "canceled"):
            sys.exit(f"run {rid} {st}")
        time.sleep(8)
    sys.exit(f"run {rid} still running after 10 min")


if __name__ == "__main__":
    main()
