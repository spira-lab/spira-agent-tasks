#!/usr/bin/env python3
"""A video's generation chain through the Spira CLI. Every job whose inputs exist is submitted at
once; a job that needs another job's result is submitted the moment that result lands; every
result is downloaded, and every job is recorded in the metadata (with its credits) and in the
plan's job log the moment it exists. No shell loops: the tool does the waiting, with
`spira ai jobs wait`, one waiter per job, all in parallel.

  python3 <reskit>/tools/spira_chain.py price   <materials>/chain.json
        Expected credits per job and in total, from the live price list (for the plan).
  python3 <reskit>/tools/spira_chain.py run     <materials>/chain.json [--cap 120] [--parallel 10]
        Run the chain until nothing is left in flight (or --cap minutes). Start it with the Bash
        tool's run_in_background, then do the hands-on work. Resumable: job IDs are saved the
        moment they exist, so a second run never resubmits (a duplicate costs the full price).
        Only one runner per chain at a time.
  python3 <reskit>/tools/spira_chain.py wait    <materials>/chain.json [--for 9]
        Block until the chain's state changes, everything has settled, or --for minutes (keep it
        under 10, the Bash limit). Then prints the status. Use it instead of any polling loop.
  python3 <reskit>/tools/spira_chain.py status  <materials>/chain.json
  python3 <reskit>/tools/spira_chain.py approve <materials>/chain.json <label> [...]
        A job marked "hold": true (the outfit sheet) keeps its dependents waiting until you have
        looked at its result and passed your own check. This is the designer's self-check, not a
        human approval gate: nobody else is asked. Then run the chain again (it carries on).
  python3 <reskit>/tools/spira_chain.py redo    <materials>/chain.json <label> "<why>"
        One extra generation of a job (edit its inputs in chain.json first if the prompt
        changes). Its current files move to deletable/. At most 2 extra generations per job:
        a third redo is refused. Then run the chain again.

chain.json (paths relative to the materials folder):

  {"jobs": [
    {"label": "outfit", "model": "gpt-image-2", "out": "assets/outfit_sheet.png", "hold": true,
     "inputs": {"size": "16:9", "resolution": "4K", "referenceImage": ["@/abs/.../sheet_4k.png"], "prompt": "..."}},
    {"label": "plate_a", "model": "gpt-image-2", "out": "assets/plate_a.png",
     "inputs": {"size": "9:16", "resolution": "2K", "referenceImage": ["@assets/src_a.png"], "prompt": "..."}},
    {"label": "clip_A", "model": "wan-3.0", "out": "gen/out/A.mp4", "needs": ["outfit", "plate_a"],
     "inputs": {"generationType": "reference_to_video", "duration": "4", "resolution": "720p", "size": "9:16",
                "sound": false, "referenceVideo": ["@gen/ref/A.mp4"], "referenceImage": ["{{outfit}}", "{{plate_a}}"],
                "prompt": "..."}}
  ]}

  "@<path>"     a local file: uploaded once with `spira assets upload` (hosted URLs pass as they are)
  "{{label}}"   the first result URL of that job ("{{label#2}}" its second); the job then needs it
  "out"         where the first result is saved; further results get _b, _c (Suno returns two takes)

Job status values the CLI really returns (spira 0.0.32): QUEUED, RUNNING, COMPLETED, FAILED,
CANCELED, in capitals in `jobs status` (data.status, with data.credits once charged). `spira ai
jobs wait` prints a text line, then a compact JSON ending in "status": "completed" (lower case, no
credits) or an error whose code is TIMEOUT (still running: wait again), PROVIDER_FAILED or
ASYNC_STATE (ended). Statuses are compared case-insensitively; the JSON is read from its first "{".
A Wan clip with "sound": true (new or re-voiced lines) costs the same as one without.
Credits: the job's own charge when the CLI reports one, otherwise the model's live price-list
figure for these inputs (never the account balance, which other sessions share).
"""
import fcntl, json, math, queue, re, subprocess, sys, threading, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reskit_common import UA, Video, update_meta, to_deletable, duration, now

MAX_SUBMISSIONS = 3          # the first generation + at most 2 extra (the toolkit's rule)
WAIT_SLICE = "30m"           # one `spira ai jobs wait` call; on TIMEOUT it is called again
TERMINAL = {"done", "failed", "skipped"}


def spira(*args, timeout=None):
    r = subprocess.run(["spira", "--json", *map(str, args)], capture_output=True, text=True, timeout=timeout)
    out = r.stdout
    try:
        return json.loads(out[out.index("{"):])
    except ValueError:
        return {"status": "error", "error": {"code": "CLI", "message": (r.stderr or out).strip()[-400:]}}


def data_of(d):
    return d.get("data") if isinstance(d.get("data"), dict) else {}


def result_urls(d):
    dd = data_of(d); le = dd.get("latestExecution") or {}
    return le.get("resultUrls") or dd.get("resultUrls") or d.get("resultUrls") or []


def job_id_of(d):
    dd = data_of(d)
    return (d.get("ids") or {}).get("jobId") or dd.get("jobId") or dd.get("id") or d.get("id")


def reported_credits(d):
    dd = data_of(d)
    for k in ("creditsCharged", "chargedCredits", "credits", "cost", "creditCost"):
        v = dd.get(k)
        if isinstance(v, (int, float)): return float(v)
    return None


# ---------------------------------------------------------------- prices
_models = {}

def model_detail(model):
    if model not in _models:
        _models[model] = data_of(spira("ai", "models", "get", model))
    return _models[model]


def price(model, inputs, seconds=None):
    """Credits for one job from the live price list: (credits, note)."""
    m = model_detail(model)
    opts = m.get("creditOptions") or []
    if not opts: return None, "no price list"
    filled = {f["name"]: f.get("defaultValue") for f in m.get("fields", []) if "defaultValue" in f}
    filled.update(inputs)
    norm = lambda v: str(v).strip().lower()
    match = [o for o in opts if all(norm(filled.get(k)) == norm(v) for k, v in (o.get("when") or {}).items())]
    if not match: match = opts if len(opts) == 1 else []
    if not match: return None, "no price option matches these inputs"
    o = max(match, key=lambda o: len(o.get("when") or {}))
    c = float(o["credits"])
    if o.get("unit") == "per_second":
        secs = float(filled.get("duration") or seconds or 0)
        if not secs: return None, f"{o.get('label')}: unknown seconds"
        c = c * secs
    return math.ceil(c * 100 - 1e-9) / 100, o.get("label") or o.get("key")


# ---------------------------------------------------------------- the chain's files
class Chain:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.spec = json.loads(self.path.read_text())
        self.jobs = {j["label"]: j for j in self.spec["jobs"]}
        for j in self.jobs.values():
            j["needs"] = sorted(set(j.get("needs", [])) | set(self.refs(j["inputs"])))
            for n in j["needs"]:
                if n not in self.jobs: sys.exit(f"{j['label']} needs {n}, which is not in the chain")
        self.video = Video(self.path)
        self.dir = self.video.materials
        self.state_path = self.path.with_name(self.path.stem + ".state.json")
        self.log_path = self.path.with_name(self.path.stem + ".log")
        self.approved_path = self.path.with_name(self.path.stem + ".approved.json")
        self.lock = threading.Lock()

    @staticmethod
    def refs(x):
        if isinstance(x, str):
            return re.findall(r"^\{\{([A-Za-z0-9_\-]+)(?:#\d+)?\}\}$", x)
        if isinstance(x, list): return [r for i in x for r in Chain.refs(i)]
        if isinstance(x, dict): return [r for i in x.values() for r in Chain.refs(i)]
        return []

    def load(self):
        try:
            st = json.loads(self.state_path.read_text())
        except (OSError, ValueError):
            st = {}
        st.setdefault("jobs", {}); st.setdefault("uploads", {})
        for label in self.jobs:
            st["jobs"].setdefault(label, {"status": "pending", "submissions": 0, "history": []})
        return st

    def save(self, st):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, indent=1) + "\n"); tmp.replace(self.state_path)

    def say(self, line):
        line = f"{datetime.now().strftime('%H:%M:%S')} {line}"
        print(line, flush=True)
        with open(self.log_path, "a") as f: f.write(line + "\n")

    def path_of(self, rel):
        p = Path(rel).expanduser()
        return p if p.is_absolute() else self.dir / p

    # ------------------------------------------------------------ inputs
    def upload(self, st, rel):
        p = self.path_of(rel).resolve()
        if not p.is_file(): raise RuntimeError(f"no file at {p}")
        key = f"{p}|{p.stat().st_size}|{int(p.stat().st_mtime)}"
        if key not in st["uploads"]:
            d = spira("assets", "upload", p, timeout=600)
            url = data_of(d).get("url")
            if not url: raise RuntimeError(f"upload of {p.name} failed: {(d.get('error') or {}).get('message')}")
            st["uploads"][key] = url
            self.save(st)
        return st["uploads"][key]

    def resolve(self, st, x):
        if isinstance(x, str):
            m = re.match(r"^\{\{([A-Za-z0-9_\-]+)(?:#(\d+))?\}\}$", x)
            if m:
                urls = st["jobs"][m.group(1)].get("urls") or []
                k = int(m.group(2) or 1) - 1
                if k >= len(urls): raise RuntimeError(f"{m.group(1)} has no result #{k + 1}")
                return urls[k]
            if x.startswith("@"):
                return x[1:] if x[1:].startswith("https://") else self.upload(st, x[1:])
            return x
        if isinstance(x, list): return [self.resolve(st, i) for i in x]
        if isinstance(x, dict): return {k: self.resolve(st, v) for k, v in x.items()}
        return x

    def approved(self):
        """Approvals live in their own file, so `approve` never races a running runner."""
        try:
            return set(json.loads(self.approved_path.read_text()))
        except (OSError, ValueError):
            return set()

    def ready(self, st, label):
        j = self.jobs[label]; ok = self.approved()
        for n in j["needs"]:
            s = st["jobs"][n]
            if s["status"] != "done": return False
            if self.jobs[n].get("hold") and n not in ok: return False
        return True

    def runner_active(self):
        with open(self.path.with_name(self.path.stem + ".runner.lock"), "a") as lk:
            try:
                fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(lk, fcntl.LOCK_UN); return False
            except BlockingIOError:
                return True

    # ------------------------------------------------------------ records
    def record(self, label, s, inputs):
        j = self.jobs[label]
        kind = lambda f: ("video" if f.suffix in (".mp4", ".webm", ".mov") else "audio" if f.suffix in (".mp3", ".wav", ".m4a")
                          else "image")
        files = s.get("files") or [None]
        entries = []
        for i, f in enumerate(files):
            fp = Path(f) if f else None
            entries.append({
                "file": str(fp) if fp else None, "status": "in-use" if s["status"] == "done" else s["status"],
                "kind": kind(fp) if fp else None, "tool": j["model"], "label": label, "job_id": s.get("job"),
                "submission": s["submissions"], "prompt": inputs.get("prompt") or inputs.get("style") or "",
                "inputs": inputs, "source": None, "url": (s.get("urls") or [None] * (i + 1))[i] if s.get("urls") else None,
                "credits": s.get("credits") if i == 0 else 0, "credits_source": s.get("credits_source"),
                "generated": now(), "render_secs": s.get("secs"), "error": s.get("error"), "replaced_by": None})

        def put(d):
            d.setdefault("assets", [])
            d["assets"] = [a for a in d["assets"] if not (a.get("job_id") == s.get("job") and a.get("label") == label)] + entries
            d["credits_total"] = round(sum(float(a.get("credits") or 0) for a in d["assets"]), 2)
        update_meta(self.video, put)
        plan = self.video.plan
        if plan.exists():
            settings = ", ".join(f"{k} {inputs[k]}" for k in ("size", "resolution", "duration", "generationType", "mode")
                                 if k in inputs)
            with open(plan, "a") as f:
                f.write(f"| {label} | {s.get('job')} | {j['model']} | {settings} | {s.get('credits')} | {s.get('secs')} s |\n")

    def note_submitted(self, label, s, inputs):
        """The job ID goes into the metadata the moment it exists."""
        j = self.jobs[label]

        def put(d):
            d.setdefault("assets", []).append({
                "file": None, "status": "submitted", "kind": None, "tool": j["model"], "label": label, "job_id": s["job"],
                "submission": s["submissions"], "prompt": inputs.get("prompt") or inputs.get("style") or "", "inputs": inputs,
                "source": None, "url": None, "credits": 0, "credits_source": "pending", "generated": now(), "replaced_by": None})
        update_meta(self.video, put)

    # ------------------------------------------------------------ run
    def waiter(self, label, jid, q, deadline):
        transient = 0
        while True:
            d = spira("ai", "jobs", "wait", jid, "--timeout", WAIT_SLICE, "--interval", "15s")
            err = d.get("error") or {}
            if d.get("status") == "success" or str(d.get("status") or "").lower() == "completed":
                # spira 0.0.31 ends a finished wait with a compact {"status": "completed"} and no
                # credits; read the full status so the job is recorded done with its real cost
                full = spira("ai", "jobs", "status", jid)
                q.put((label, "COMPLETED", full if data_of(full) else d)); return
            if str(data_of(d).get("status") or "").upper() in ("FAILED", "CANCELED", "CANCELLED"):
                q.put((label, "FAILED", d)); return
            code = err.get("code")
            if code == "TIMEOUT" and time.time() < deadline:
                continue
            if code in ("PROVIDER_FAILED", "ASYNC_STATE"):
                time.sleep(10)                      # a job can flip: look once more before calling it failed
                again = spira("ai", "jobs", "status", jid)
                st = (data_of(again).get("status") or "").upper()
                if st == "COMPLETED": q.put((label, "COMPLETED", again)); return
                if st in ("QUEUED", "RUNNING") and time.time() < deadline: continue
                q.put((label, st or "FAILED", again if data_of(again) else d)); return
            if code == "TIMEOUT":
                q.put((label, "CAP", d)); return
            transient += 1                          # network or CLI hiccup: try again a few times
            if transient > 5 or time.time() >= deadline:
                q.put((label, "ERROR", d)); return
            time.sleep(20)

    def submit(self, st, label):
        j = self.jobs[label]; s = st["jobs"][label]
        if s["submissions"] >= MAX_SUBMISSIONS:
            s["status"] = "failed"; s["error"] = "no generations left (2 extra already used)"; return False
        try:
            inputs = self.resolve(st, j["inputs"])
        except RuntimeError as e:
            s["status"] = "failed"; s["error"] = str(e); self.say(f"{label}: cannot build inputs: {e}"); return False
        d = spira("ai", "jobs", "create", "--model-id", j["model"], "--inputs-json", json.dumps(inputs), timeout=300)
        jid = job_id_of(d) if d.get("status") == "success" else None
        if not jid:
            s["status"] = "failed"; s["error"] = f"create refused: {(d.get('error') or {}).get('message')}"
            self.say(f"{label}: {s['error']}"); return False
        s.update({"status": "submitted", "job": jid, "submitted": now(), "t0": time.time(), "inputs": inputs, "error": None})
        s["submissions"] += 1
        self.save(st)
        self.note_submitted(label, s, inputs)
        self.say(f"{label}: submitted {jid} ({j['model']}, submission {s['submissions']} of {MAX_SUBMISSIONS})")
        return True

    def finish(self, st, label, outcome, d):
        j = self.jobs[label]; s = st["jobs"][label]
        dd = data_of(d)
        s["secs"] = round(time.time() - s.get("t0", time.time()))
        if outcome == "COMPLETED":
            urls = result_urls(d)
            s["urls"] = urls; files = []
            if j.get("out") and urls:
                dest = self.path_of(j["out"]); dest.parent.mkdir(parents=True, exist_ok=True)
                for i, u in enumerate(urls):
                    f = dest if i == 0 else dest.with_name(f"{dest.stem}_{chr(97 + i)}{dest.suffix}")
                    r = subprocess.run(["curl", "-sSfL", "-A", UA, "--retry", "3", "-o", str(f), u], capture_output=True, text=True)
                    if r.returncode != 0: self.say(f"{label}: download of result {i + 1} failed: {r.stderr.strip()[-200:]}")
                    else: files.append(str(f))
            s["files"] = files
            c = reported_credits(d)
            if c is not None:
                s["credits"], s["credits_source"] = c, "job"
            else:
                secs = duration(files[0]) if files and files[0].endswith((".mp4", ".mp3", ".wav")) else None
                c, note = price(j["model"], s.get("inputs") or {}, secs)
                s["credits"], s["credits_source"] = c, f"price list: {note}"
            s["status"] = "done" if urls else "failed"
            if not urls: s["error"] = "completed with no result"
        else:
            s["status"] = "failed" if outcome != "CAP" else "submitted"
            if outcome == "CAP":
                self.say(f"{label}: still running at the cap ({s['job']}); run the chain again later to collect it"); return
            le = dd.get("latestExecution") or {}
            s["error"] = (le.get("error") if isinstance(le.get("error"), str) else (le.get("error") or {}).get("message")) \
                or (d.get("error") or {}).get("message") or outcome
            c = reported_credits(d)
            s["credits"], s["credits_source"] = (c, "job") if c is not None else (0, "failed: no charge reported")
        self.save(st)
        self.record(label, s, s.get("inputs") or {})
        self.say(f"{label}: {s['status']} credits={s.get('credits')} {s['secs']}s"
                 + (f" error={s['error']}" if s.get("error") else "") + (f" -> {', '.join(s.get('files', []))}" if s.get("files") else ""))

    def run(self, cap_min=120, parallel=10):
        lk = open(self.path.with_name(self.path.stem + ".runner.lock"), "a")
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit("a runner for this chain is already active: use `wait` instead")
        deadline = time.time() + cap_min * 60
        st = self.load(); q = queue.Queue(); live = set()
        for label, s in st["jobs"].items():          # resume jobs submitted by an earlier run
            if s["status"] == "submitted" and s.get("job"):
                live.add(label); threading.Thread(target=self.waiter, args=(label, s["job"], q, deadline), daemon=True).start()
                self.say(f"{label}: resumed waiting on {s['job']}")
        while True:
            changed = True
            while changed:
                changed = False
                for label in self.jobs:
                    s = st["jobs"][label]
                    if s["status"] == "pending" and any(st["jobs"][n]["status"] in ("failed", "skipped") for n in self.jobs[label]["needs"]):
                        s["status"] = "skipped"; s["error"] = "a job it needs failed"; changed = True
                        self.say(f"{label}: skipped, a job it needs failed")
                for label in self.jobs:
                    if len(live) >= parallel: break
                    s = st["jobs"][label]
                    if s["status"] == "pending" and self.ready(st, label):
                        if self.submit(st, label):
                            live.add(label)
                            threading.Thread(target=self.waiter, args=(label, s["job"], q, deadline), daemon=True).start()
                        changed = True
                self.save(st)
            if not live: break
            try:
                label, outcome, d = q.get(timeout=max(1, deadline - time.time() + 60))
            except queue.Empty:
                break
            live.discard(label)
            self.finish(st, label, outcome, d)
        held = [l for l, s in st["jobs"].items() if s["status"] == "pending"]
        self.say("chain stopped: " + summary(st) + (f"; waiting on approval or inputs: {', '.join(held)}" if held else ""))


def summary(st):
    c = {}
    for s in st["jobs"].values(): c[s["status"]] = c.get(s["status"], 0) + 1
    cr = sum(float(s.get("credits") or 0) for s in st["jobs"].values())
    return ", ".join(f"{v} {k}" for k, v in sorted(c.items())) + f"; credits so far {round(cr, 2)}"


def show(ch):
    st = ch.load()
    for label, j in ch.jobs.items():
        s = st["jobs"][label]
        flag = " HOLD: look at it, then approve" if j.get("hold") and s["status"] == "done" and label not in ch.approved() else ""
        print(f"{label:14} {s['status']:9} {s.get('job') or '-':38} sub {s['submissions']}/{MAX_SUBMISSIONS} "
              f"credits {s.get('credits')}{flag}" + (f" error: {s['error']}" if s.get("error") else ""))
    print(summary(st))


def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    cmd, ch = a[0], Chain(a[1])
    opt = lambda f, d: a[a.index(f) + 1] if f in a else d
    if cmd == "price":
        tot = 0
        for label, j in ch.jobs.items():
            c, note = price(j["model"], {k: v for k, v in j["inputs"].items() if not isinstance(v, (list, dict))})
            tot += c or 0
            print(f"{label:14} {j['model']:24} {c}  ({note})")
        print(f"total expected {round(tot, 2)} credits (first generations only)")
    elif cmd == "run":
        ch.run(float(opt("--cap", 120)), int(opt("--parallel", 10)))
    elif cmd == "status":
        show(ch)
    elif cmd == "wait":
        end = time.time() + float(opt("--for", 9)) * 60
        before = ch.state_path.read_text() if ch.state_path.exists() else ""
        while time.time() < end:
            st = ch.load()
            if all(s["status"] in TERMINAL or (s["status"] == "pending" and not ch.ready(st, l)) for l, s in st["jobs"].items()):
                break
            if (ch.state_path.read_text() if ch.state_path.exists() else "") != before: break
            time.sleep(5)
        show(ch)
    elif cmd == "approve":
        st = ch.load(); ok = ch.approved()
        for label in a[2:]:
            if label not in st["jobs"]: sys.exit(f"no job {label}")
            if st["jobs"][label]["status"] != "done": sys.exit(f"{label} is not done yet")
            ok.add(label)
        ch.approved_path.write_text(json.dumps(sorted(ok)) + "\n")
        print("approved:", ", ".join(a[2:]), "- a running chain carries on by itself; otherwise run it again")
    elif cmd == "redo":
        if len(a) < 4: sys.exit("usage: redo <chain.json> <label> \"<why>\"")
        label, why = a[2], a[3]
        if ch.runner_active(): sys.exit("the chain is running: wait until it stops (`wait`), then redo")
        st = ch.load(); s = st["jobs"].get(label)
        if not s: sys.exit(f"no job {label}")
        if s["status"] == "submitted": sys.exit(f"{label} is still running")
        if s["status"] == "pending": sys.exit(f"{label} is already waiting to be submitted: run the chain")
        if s["submissions"] >= MAX_SUBMISSIONS:
            sys.exit(f"{label}: 2 extra generations already used; keep the best take and say so in your final line")
        moved = [str(to_deletable(f, ch.dir / "deletable")) for f in s.get("files", []) if Path(f).exists()]

        def put(d):
            for x in d.get("assets", []):
                if x.get("job_id") == s.get("job") and x.get("label") == label and x.get("file"):
                    i = (s.get("files") or []).index(x["file"]) if x["file"] in (s.get("files") or []) else -1
                    x["status"] = "deletable"; x["rejected"] = why
                    if 0 <= i < len(moved): x["file"] = moved[i]
        update_meta(ch.video, put)
        s["history"].append({k: s.get(k) for k in ("job", "credits", "files", "error")} | {"why": why})
        ok = ch.approved() - {label}; ch.approved_path.write_text(json.dumps(sorted(ok)) + "\n")
        s.update({"status": "pending", "files": [], "urls": [], "job": None, "error": None, "credits": None})
        for l2, s2 in st["jobs"].items():             # jobs skipped because this one failed get their chance again
            if s2["status"] == "skipped" and label in ch.jobs[l2]["needs"]:
                s2["status"] = "pending"; s2["error"] = None
        ch.save(st)
        print(f"{label}: queued for submission {s['submissions'] + 1} of {MAX_SUBMISSIONS}; moved {len(moved)} file(s) to deletable. Run the chain again.")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
