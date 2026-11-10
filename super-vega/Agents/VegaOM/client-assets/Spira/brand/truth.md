# Spira brand truth

| Fact | Exact wording / number | Source | Checked |
|---|---|---|---|
| What Spira is | "The AI that runs your entire social"; "The only social media agent that creates, posts and grows your channel 24/7." | spira.ai homepage (capture brand/ui/2026-11-05) | 2026-11-05 |
| Makes the videos | "AI content creation": "Pick a template, add your product, and get contents at scale."; panel shows "Generating 12 posts" | spira.ai homepage | 2026-11-05 |
| Posts them | "Schedule and post": "Connect your accounts, schedule posts, and go live from the platform. Or get new warm accounts." | spira.ai homepage | 2026-11-05 |
| Platforms | TikTok, Instagram, YouTube, X and LinkedIn | Brand DNA (Lark) | 2026-11-05 |
| Grows / measures | "Performance loop": "Live counts on every post. See views, likes and shares as they come in. Understand what works and iterate."; panel "Last 7 days" with demo counts 453.5k Views, 438k Likes, 332k Shares (a site illustration, not a customer result) | spira.ai homepage | 2026-11-05 |
| Spira Maxima | Video model: paste one script, get a finished, ready-to-post video; up to 90 seconds in one generation | Brand DNA; homepage banner "Spira Maxima 1.0 is live." | 2026-11-05 |
| Calls to action that exist | nav "Book a call"; button "Start growing traffic for free"; "Start free, no credit card required." | spira.ai homepage | 2026-11-05 |
| Logo and colours | Spira_logo.png (client assets); #FF6F00, #17161A, #F8F8F8 | Request | 2026-11-05 |
| Spira does not come to you and film | No on-site film crew anywhere on the site; the videos are AI-made. Never say "we come to you and film" or "three months of content in one day". | site + DNA (absent) | 2026-11-05 |
| Every post is labelled AI | "Yes, always. Every post is AI-generated or AI-processed and says so." | spira.ai FAQ | 2026-11-05 |
| Spira Maxima output | "Turn scripts into viral, social-ready videos." Paste one script, get a finished video with presenter, voice, cuts, motion graphics, B-roll, captions and music | spira.ai/spira-maxima, Brand DNA | 2026-11-05 |
| Add the MCP to Claude Code | `claude mcp add -s user spira -- npx -y @spira-lab/mcp` ("Run one command") | spira.ai/mcp, @spira-lab/mcp README | 2026-11-05 |
| MCP setup steps | "Run one command", "Sign in once" (a browser window opens, approve it and come back), "Ask for a video" (paste your script and your agent does the rest) | spira.ai/mcp | 2026-11-05 |
| Ask in plain words | "Use Spira to turn this launch script into a 30-second reel." | spira.ai/mcp | 2026-11-05 |
| MCP tools | `spira_maxima_upload`, `spira_maxima_estimate`, `spira_maxima_create`, `spira_maxima_status`, `spira_maxima_wait`, `spira_maxima_download` | @spira-lab/mcp 0.0.1 README on npm | 2026-11-05 |
| MCP flow | upload, estimate, confirm the price, create, wait, download | @spira-lab/mcp README | 2026-11-05 |
| Finished video returns | MP4 plus a post caption, hashtags and a title; local MCP and CLI save the file | `spira agent types get spira-maxima`, spira.ai/mcp | 2026-11-05 |
| How long a video takes | "typically takes 15-30 minutes" | @spira-lab/mcp README, `spira agent types get spira-maxima` | 2026-11-05 |
| Install the CLI | `npm install -g @spira-lab/cli`, then `spira auth login` | spira.ai/mcp | 2026-11-05 |
| Make a video with the CLI | `spira agent jobs create --type spira-maxima --inputs-json '{"script":"..."}' --wait --output ./video.mp4` | `spira agent types get spira-maxima` | 2026-11-05 |
| Price of a script | 150 credits per 10 s, rounded up to whole 10-second blocks. The showcase script below estimates at 600 credits, 37 s, sufficient: true | `spira agent jobs estimate`, live | 2026-11-05 |
| Sample Maxima video | spira.ai's own showcase `showcase-services.mp4`, home-buying script; its transcript is in 212-spira-11-05's materials | spira.ai/spira-maxima | 2026-11-05 |
| Where the agent tools work today | "Claude Code and the CLI today. ChatGPT, Claude and Telegram are coming next." | spira.ai/mcp FAQ | 2026-11-05 |
| No API key needed | "You sign in with your Spira account and nothing else is needed." | spira.ai/mcp FAQ | 2026-11-05 |
| Does not exist through MCP | Editing an existing video: "not available through MCP yet" | @spira-lab/mcp README | 2026-11-05 |
| T1 Spira Maxima (Task 208) | "you paste one script, and it returns a finished, ready-to-post video"; "Turn scripts into viral, social-ready videos." | DNA; spira.ai/spira-maxima | 2026-11-05 |
| T2 Works in Claude Code, one command (Task 208) | "Run one command. Adds Spira to Claude Code for every project."; `claude mcp add -s user spira -- npx -y @spira-lab/mcp` | spira.ai/mcp (Spira for agents) | 2026-11-05 |
| T3 Sign in once, no API key (Task 208) | "Sign in once. A browser window opens. Approve it and come back."; "Do I need my own API key? No. You sign in with your Spira account" | spira.ai/mcp | 2026-11-05 |
| T4 Ask your agent (Task 208) | "Ask for a video. Paste your script and your agent does the rest."; "Ask for a video in plain words and get the file back."; example prompt "Use Spira to turn this launch script into a 30-second reel." | spira.ai/mcp | 2026-11-05 |
| T5 Cost first (Task 208) | "Get the credit cost and length of a video before it is created."; a script timed at 22 s estimated at 450 credits, billed 30 s, 150 credits per 10 s | spira.ai/mcp; `spira agent jobs estimate`, live | 2026-11-05 |
| T6 The file comes back (Task 208) | "Finished videos come back as a file or a link you can share."; "The local MCP and the CLI can save the file to your machine." | spira.ai/mcp | 2026-11-05 |
| T7 The CLI (Task 208) | `npm install -g @spira-lab/cli`; `spira auth login`; `spira agent jobs create --type spira-maxima --inputs-json '{"script":"..."}' --file speaker=./me.jpg --wait --output ./video.mp4` | spira.ai/mcp; `spira agent types get spira-maxima` (CLI 0.0.31) | 2026-11-05 |
| T8 A run takes time (Task 208) | "typical duration: 15-30 minutes; queue time depends on your plan"; "runs appear in its History" | `spira agent types get spira-maxima` | 2026-11-05 |
| T9 What one run returns (Task 208) | "one finished short video with a presenter, visuals, captions, music and sound effects"; "An MP4 video URL plus a post caption, hashtags and a title." | `spira agent types get spira-maxima` | 2026-11-05 |
| T10 Where it works today (Task 208) | "Claude Code and the CLI today. ChatGPT, Claude and Telegram are coming next." | spira.ai/mcp FAQ | 2026-11-05 |
| MCP tools (row seen in Task 212's version of this file, restored by Task 208) | `spira_maxima_upload`, `spira_maxima_estimate`, `spira_maxima_create`, `spira_maxima_status`, `spira_maxima_wait`, `spira_maxima_download`; flow: upload, estimate, confirm the price, create, wait, download | @spira-lab/mcp 0.0.1 README on npm, as read by Task 212 | 2026-11-05 |
| Sample Maxima video (row seen in Task 212's version, restored by Task 208) | spira.ai's own showcase `showcase-services.mp4` | spira.ai/spira-maxima | 2026-11-05 |
| Does not exist through MCP (row seen in Task 212's version, restored by Task 208) | Editing an existing video: "not available through MCP yet" | @spira-lab/mcp README, as read by Task 212 | 2026-11-05 |
| Page oddities (Task 208) | The agents page's example cards show other credit figures (120 credits, 45 sec; 420 credits, 45 s) and its copy text once says "Social Maxima": use the live estimate and the name Spira Maxima | spira.ai/mcp | 2026-11-05 |
| Posting 24/7 (Task 209) | "The only social media agent that creates, posts and grows your channel 24/7."; "The creative agent that makes, posts and grows your channels 24/7." | spira.ai homepage and footer | 2026-11-05 |
| Connected accounts screen (Task 209) | "Connected accounts": "Bind, review, and publish through the social channels Spira can operate for this workspace."; TikTok, YouTube, Instagram, Facebook, Twitter/X, LinkedIn | spira.ai/features/social-media-content-calendar (product panel) | 2026-11-05 |
| Schedule screen (Task 209) | "Schedules" month view; "Schedule post" panel with Date, Time and "Schedule Post" button; toast "Post Scheduled to your Calendar"; "Choose the date and time, then add the post to the shared multi-account publishing calendar." | spira.ai/features/social-media-content-calendar and /social-media-post-scheduler | 2026-11-05 |
| Analytics screen (Task 209) | "Followers" chart with tabs Views, Likes, Comments, Shares; "Live counts on every post." The chart's figures on the site are illustrations, so no figure is shown | spira.ai/features/social-media-analytics, homepage | 2026-11-05 |
| No timeline, no editor (Task 210) | "Edit with an agent, not a timeline"; "No editor and no extra tools."; "with captions, music, cuts, voice and motion graphics included" | Brand DNA | 2026-11-05 |
| MCP in plain words (Task 210) | "Connect Spira to the AI tool you already use. Ask for a video in plain words and get the file back."; lyric "It's all connected through MCP" and "one command" rest on this and on the `claude mcp add` row | spira.ai/mcp | 2026-11-05 |
| MCP confirm step (Task 210) | "spira_maxima_estimate ... Show the user the cost before calling spira_maxima_create"; a 30-second script bills 3 blocks x 150 = 450 credits | @spira-lab/mcp 0.0.1 tool descriptions; `spira agent types get spira-maxima` | 2026-11-05 |
| T319-1 Glowfount is a made-up brand (Task 319) | A round floating LED bath fountain; set in the water, tap its button, the spiral of water lights up blue, purple and pink; wordmark "glowfount" on its base. Hook "the bath upgrade you didn't know you needed ✨" is an opinion, not a claim | Request (Atlas batch 2026-11-10 glowfountreskit, row 319): "Spira demo for Glowfount, a made-up brand" | 2026-11-10 |
| T319-2 Spira in the Glowfount demo (Task 319) | No claims about Spira: only the real logo (Spira_logo.png) top-left for the whole video and a "made with Spira" end card; colours #FF6F00, #17161A, #F8F8F8 | Request (row 319) | 2026-11-10 |
| Posting is in the Spira platform, not the MCP (Task 209) | The MCP's tools make and return a video (no publish tool listed); scheduling and posting happen in Spira, or with `spira social` and `spira schedules` in the CLI. Show the agent making the video and Spira posting it | @spira-lab/mcp README row above; `spira --help` 0.0.31 | 2026-11-05 |
