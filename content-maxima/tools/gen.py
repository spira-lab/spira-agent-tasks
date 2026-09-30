#!/usr/bin/env python3
"""One generation, end to end: submit, wait, download, check.

  python3 tools/gen.py <model-id> <payload.json> <out-file> [--timeout 20m]

<payload.json> is the job's full --inputs-json object in a file (write it
first); <out-file> is where the result lands, inside the video's materials
folder. Extra results of the same job land beside it as <name>-2.<ext>, ...

Run independent generations in parallel in one command, each in the
background, then wait. Leave the output on the terminal: each line is printed
whole, and the job ids in it are how the platform bills the run.

  python3 tools/gen.py seedance-1.5-pro th-01.json th-01.mp4 &
  python3 tools/gen.py seedance-1.5-pro th-02.json th-02.mp4 &
  wait

To keep working while a long batch runs (the talking-head clips), start the
batch with the Bash tool's background mode, work, then block on it:

  python3 tools/gen.py --await th-01.mp4 th-02.mp4 th-03.mp4

--await returns once each of those generations has finished, and prints
what each one printed. Never wait with sleep, pgrep or polling loops.

Prints the job id (the platform bills the run from it), then `url: <resultUrl>`
for chaining into the next job. On failure prints the job's status and exits 1.

The job id is recorded in jobs/<out-file>.pending the moment the job is
submitted, and removed once the result is saved or the job has failed. A
generation cut off before that (a worker restart, a timeout) is picked up
from the record rather than submitted again: running the same command, or
`--await` on its output, waits for the recorded job and downloads it, so
the platform never charges twice for one output.
Checks: a .webm must carry alpha; a transparent-background .png must have an
alpha channel. A failed check is printed as `warning:` and the file is kept.
"""
import io, json, os, pathlib, subprocess, sys, time

ALPHA_FORMATS = {"rgba", "ya8", "rgba64be", "ya16be", "rgba64le", "ya16le"}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def spira_json(cmd):
    p = run(cmd)
    for chunk in (p.stdout, p.stdout[p.stdout.find("{"):] if "{" in p.stdout else ""):
        try:
            return json.loads(chunk)
        except ValueError:
            continue
    return {"status": "error", "stdout": p.stdout.strip()[-800:], "stderr": p.stderr.strip()[-800:]}


def probe(file, entries):
    p = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entries, "-of", "default=nw=1", str(file)])
    return p.stdout


def marker(out):
    """Where a generation leaves its finished marker: jobs/<out-file>.done beside the output."""
    out = pathlib.Path(out).resolve()
    return out.parent / "jobs" / f"{out.name}.done"


def record(out):
    """Where a submitted job's id waits until its result is saved: jobs/<out-file>.pending."""
    out = pathlib.Path(out).resolve()
    return out.parent / "jobs" / f"{out.name}.pending"


def process_alive(pid):
    """True while that gen.py process still runs. A restart reuses pids, so on Linux the command line must match."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    cmdline = pathlib.Path(f"/proc/{pid}/cmdline")
    return not cmdline.exists() or b"gen.py" in cmdline.read_bytes()


def parse_timeout(value):
    return int(value[:-1]) * 60 if value.endswith("m") else int(value)


def await_outputs(args):
    timeout = 1200
    if "--timeout" in args:
        i = args.index("--timeout"); timeout = parse_timeout(args[i + 1]); del args[i:i + 2]
    pending = {pathlib.Path(a).resolve(): marker(a) for a in args}
    if not pending:
        sys.exit("usage: gen.py --await <out-file> [<out-file> ...]")
    failed, deadline = [], time.time() + timeout
    while pending and time.time() < deadline:
        for out, m in list(pending.items()):
            rec = record(out)
            if not m.exists() and rec.exists():
                job = json.loads(rec.read_text())
                if not process_alive(job.get("pid", 0)):
                    # The gen.py that submitted it is gone (a restart): wait for the recorded job here.
                    marked(m, lambda: finish(job["jobId"], job["model"], out, job.get("transparent", False), f"{max(60, int(deadline - time.time()))}s"))
            if m.exists():
                done = json.loads(m.read_text())
                print(done["log"].rstrip())
                if done["status"] != "ok":
                    failed.append(out.name)
                del pending[out]
        if pending:
            time.sleep(3)
    if pending:
        sys.exit(f"still running after {timeout // 60} min: {', '.join(o.name for o in pending)}")
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


class Tee(io.TextIOBase):
    """Print as usual and keep a copy for the finished marker."""
    def __init__(self, real):
        self.real, self.buf = real, []
    def write(self, text):
        self.buf.append(text)
        return self.real.write(text)
    def flush(self):
        self.real.flush()


def main():
    args = sys.argv[1:]
    if args[:1] == ["--await"]:
        return await_outputs(args[1:])
    pos = [a for i, a in enumerate(args) if a != "--timeout" and (i == 0 or args[i - 1] != "--timeout")]
    if len(pos) == 3:
        return marked(marker(pos[2]), lambda: generate(args), silent=False)
    generate(args)


def marked(done, work, silent=True):
    """Run one generation and leave its finished marker, for --await, whatever the outcome."""
    done.parent.mkdir(parents=True, exist_ok=True)
    done.unlink(missing_ok=True)
    tee = Tee(io.StringIO() if silent else sys.stdout)
    real, sys.stdout = sys.stdout, tee
    status = "failed"
    try:
        work()
        status = "ok"
    except SystemExit:
        if not silent:
            raise
    finally:
        sys.stdout = real
        done.write_text(json.dumps({"status": status, "log": "".join(tee.buf)}))


def generate(args):
    args = list(args)
    timeout = "20m"
    if "--timeout" in args:
        i = args.index("--timeout"); timeout = args[i + 1]; del args[i:i + 2]
    if len(args) != 3:
        sys.exit(__doc__)
    model, payload_file, out = args
    payload = pathlib.Path(payload_file).read_text()
    json.loads(payload)  # fail here, not at the provider, on a malformed payload
    out = pathlib.Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    transparent = "transparent" in payload.lower()

    rec = record(out)
    if rec.exists():
        job = json.loads(rec.read_text())["jobId"]
        print(f"resuming the {model} job already submitted for {out.name}; delete {rec.name} to submit a new one")
    else:
        created = spira_json(["spira", "--json", "ai", "jobs", "create", "--model-id", model, "--inputs-json", payload])
        job = (created.get("ids") or {}).get("jobId") or (created.get("data") or {}).get("jobId")
        if not job:
            print(f"FAILED {model} -> {out.name}: {json.dumps(created.get('error', created))[:1500]}")
            sys.exit(1)
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(json.dumps({"jobId": job, "model": model, "transparent": transparent, "pid": os.getpid()}))
    finish(job, model, out, transparent, timeout)


def finish(job, model, out, transparent, timeout):
    """Wait for a submitted job, download its results beside `out` and check them; drop its record once settled."""
    print(json.dumps({"jobId": job, "model": model, "out": out.name}))
    done = spira_json(["spira", "--json", "ai", "jobs", "wait", job, "--timeout", timeout])
    urls = done.get("resultUrls") or []
    if done.get("status") not in ("completed", "succeeded") or not urls:
        detail = spira_json(["spira", "--json", "ai", "jobs", "status", job])
        state = str((detail.get("data") or {}).get("status", "")).upper()
        if state in ("QUEUED", "PENDING", "RUNNING", "PROCESSING"):
            # Still generating: keep the record so the next run of this command waits for the same job.
            print(f"STILL RUNNING {model} -> {out.name}: job {job}; run `gen.py --await {out.name}` or this command again to collect it")
            sys.exit(1)
        record(out).unlink(missing_ok=True)
        print(f"FAILED {model} -> {out.name}: {json.dumps(detail.get('data', detail))[:1500]}")
        if model == "suno-music":
            print("suno-music's provider_error is usually a rejected style: remove artist, brand, sport and place names from `style` and resubmit once.")
        sys.exit(1)

    files = []
    for n, url in enumerate(urls):
        target = out if n == 0 else out.with_name(f"{out.stem}-{n + 1}{out.suffix}")
        # curl, not urllib: the CDN turns away urllib's default client
        if run(["curl", "-sSfL", "--retry", "3", "-o", str(target), url]).returncode != 0:
            sys.exit(f"download failed: {url}")
        files.append((target, url))

    for target, _ in files:
        if target.suffix == ".webm" and "alpha_mode=1" not in probe(target, "stream_tags=alpha_mode").lower():
            print(f"warning: {target.name} has no alpha channel")
        if target.suffix == ".png" and transparent and probe(target, "stream=pix_fmt").split("=")[-1].strip() not in ALPHA_FORMATS:
            print(f"warning: {target.name} has no alpha channel; the prompt asked for a transparent background")
    record(out).unlink(missing_ok=True)
    for target, url in files:
        print(f"saved {target.name}\nurl: {url}")


if __name__ == "__main__":
    main()
