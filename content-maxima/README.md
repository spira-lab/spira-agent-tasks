> **This repository is for Spira.ai and its team only.** It is the intellectual property of Jeff Mouie Ramirez, strictly confidential, and is not to be shared outside the team or used for personal gain. Upon leaving the company, the copy on your local device must be removed, as it is subject to your NDA. Any misuse of this material is a breach of that NDA and will be treated as one.

# Content Maxima

![Content Maxima: video production, orchestrated](docs/cover.png)

![What it is not](docs/not.png)

## Getting started

![Step 1: Clone the package](docs/step-1.png)

![Step 2: Install what the tools need](docs/step-2.png)

![Step 3: Set your working folder](docs/step-3.png)

![Step 4: How to prompt](docs/step-4.png)

## How to use

![Providing a file](docs/guide-1.png)

![Style sheet](docs/guide-2.png)

![Talking head or voice-over video](docs/guide-3.png)

![Your own talking head](docs/guide-4.png)

![Music](docs/guide-5.png)

![Add-on skills](docs/guide-6.png)

![Working memory](docs/guide-7.png)

## What is in the package

| Folder | Holds |
|--------|-------|
| `skills/` | The procedures a session reads: creative video production, toolkit, prompting, stage canvas HTML, file management, known methods, add-ons, working memory |
| `stage/` | The 9:16 stage template every editable is copied from |
| `tools/` | The renderer and stage audit, the generation, captions and cover scripts, the Whisper timings and music bed scripts |
| `sfx/` | Sound effects and their metadata |
| `music/` | The music library, numbered tracks |
| `docs/` | These cards and the script that renders them |

The cards are generated from `docs/steps.html`. After editing it, run `node docs/render-steps.js` from the package folder to refresh the images.
