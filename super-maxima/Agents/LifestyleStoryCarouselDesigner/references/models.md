# Spira image models: credit prices

Checked 2026-10-29 with `spira ai models get <id>`, on server staging.tryspira.ai.
Re-check before every quote. Each build's credits are the listed prices of its jobs (`lsc.py record`).

| Model ID | 1K | 2K | 4K | Refs | Sizes | Use for |
|---|---|---|---|---|---|---|
| `seedream-5.0-flash` | 2 | 2 | — | up to 10 | no 4:5 (use 3:4 + crop) | cheapest photoreal; test first if budget is tight |
| `nano-banana-2.1` | 2 | 3 | 5 | up to 10 | all incl. 4:5, 9:16 | **default** for carousel photos + character lock |
| `qwen-image-edit` | 1–2 | — | — | exactly 1 (required) | 1:1, 3:4, 9:16, 4:3, 16:9 | small edits on one image (fix a detail) |
| `flux-kontext` | pro 3 · max 5 | | | 1 | no 4:5 | edits |
| `gpt-image-2` | 4 | 5 | 8 | yes | no 4:5 | — |
| `gpt-image-2.5` | 2 | 6 | 10 | up to 16 | no 4:5 | sharpest detail, text-heavy images |
| `nano-banana-2` | 4 | 6 | 8 | yes | incl. 4:5 | superseded by 2.1 |
| `nano-banana-pro` | 8 | 8 | 15 | yes | incl. 4:5 | fallback when the face drifts |
| `ai-influencer-image` (Higgsfield Soul) | 7 flat (720p or 1080p) | | | **none** (text only) | 9:16, 3:4, 1:1, 2:3… no 4:5 (use 3:4 + crop) | **people shots: Rey's rule. Soul first, then Astra** |

Slides are 1080×1350 and 1152×2048, so **2K** is the working resolution.

Notes:
- `referenceImage` takes public URLs, not local paths. Upload the lock image first.
- `nano-banana-2.1` outputs PNG only and has no seed.
- A job: `submit_ai_job` with `modelId` and `inputs` (`{"prompt":"…","size":"4:5","resolution":"2K","referenceImage":["<url>"]}`), then `wait_ai_job` with its `jobId` and `saveTo` (skill section 4).

## Jobs (learned 2026-10-29)
- Record the `jobId` (`lsc.py submitted`) right after submitting. A lost job ID means a lost image.
- `PROVIDER_FAILED` jobs are not charged. Retry once.
- Billed price matched the listed price: nano-banana-2.1 at 2K = 3 credits.

## People pipeline: Higgsfield Soul + Astra (Rey's rule, 2026-10-29)
- **Astra = `gpt-image-2.5`** (Flare tier by default). It takes up to 16 reference images. Price: 1K 2, 2K 6, 4K 10.
- Soul = `ai-influencer-image`, 7 credits flat, text only, 3:4 max 1080p.
- Per people shot: Soul 7 + Astra 2K 6 = **13 credits**. Non-people shots stay on nano-banana-2.1 at 3 credits.
- Neither model has 4:5: generate at 3:4, then crop.

## Route test 1 (2026-11-02): which route makes carousel people photos
The same 3 shots (lock, over-the-shoulder with a green phone, close side profile), one take each, scored 1–5 on 6 checks.
| Route | Score /30 | Credits / shot | Verdict |
|---|---|---|---|
| **A · Soul → GPT 2.5** | **25** | 11 | **Default.** The only route that changes the camera angle per slide; natural look. Watch: the room drifts between shots. |
| C · Wan 3.0, frame pull (reference mode, 2 s, 1080p) | 25 | 24.7 | Most real and most consistent, but keeps the reference's front framing: no over-shoulder, no profile. Use for "same moment, small change" slides only. Slow queue (34 min on one job). |
| B · Nano Banana 2.1 | 22 | 3 | Reuses one background plate and ignores the angle; looks staged. Objects and hands only. |
| D · Seedance 2.0, frame pull (720p) | 21 | 55 | Good identity and profile, but 834 px frames; 1080p costs 132 per shot. Not worth it for stills. |
Seedance 1.5 Pro returned `provider_error` on every input on Spira that day (not charged).
Frame pull: decode the clip, keep the frame with the highest Laplacian variance (`01-carousel/scripts/route_test.py`).
Next to test: A with the lock passed as a place reference on the GPT edit, to stop the room drifting.
