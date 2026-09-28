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

Prints the job id (the platform bills the run from it), then `url: <resultUrl>`
for chaining into the next job. On failure prints the job's status and exits 1.
Checks: a .webm must carry alpha; a transparent-background .png must have an
alpha channel. A failed check is printed as `warning:` and the file is kept.
"""
import json, pathlib, subprocess, sys

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


def main():
    args = sys.argv[1:]
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

    created = spira_json(["spira", "--json", "ai", "jobs", "create", "--model-id", model,
                          "--inputs-json", payload, "--wait", "--wait-timeout", timeout])
    job = created.get("id") or (created.get("ids") or {}).get("jobId") or (created.get("data") or {}).get("jobId")
    if job:
        print(json.dumps({"jobId": job, "model": model, "out": out.name}))
    urls = created.get("resultUrls") or []
    if created.get("status") not in ("completed", "succeeded") or not urls:
        detail = spira_json(["spira", "--json", "ai", "jobs", "status", job]) if job else created
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
        if target.suffix == ".png" and "transparent" in payload.lower() and probe(target, "stream=pix_fmt").split("=")[-1].strip() not in ALPHA_FORMATS:
            print(f"warning: {target.name} has no alpha channel; the prompt asked for a transparent background")
    for target, url in files:
        print(f"saved {target.name}\nurl: {url}")


if __name__ == "__main__":
    main()
