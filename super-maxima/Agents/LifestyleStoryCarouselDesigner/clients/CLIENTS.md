# Client ledger

Every client the carousel skill can make posts for. A request like "make me 5 story carousels for PartGenie" is matched here by name or alias, then the skill reads that client's brief and used-ideas log.

**Brief status:** `confirmed` = from the client's own brief. `draft` = written by us from public info or the team's demo videos; the skill verifies it against the client's site on its first run and lists what it couldn't confirm.

| Client | Aliases | What it is | Audience | Product shows on | Brief | Brief status | Carousels made | Ideas used (round) |
|---|---|---|---|---|---|---|---|---|
| PartGenie | partgenie, part genie | AI assistant for hardware engineers: find parts, chat with datasheets, alternatives, BOM, ECAD files | hardware engineers, buyers, FAEs, students and makers | web, phone app, Chrome extension | [BRIEF](partgenie/BRIEF.md) | confirmed (client brief 2026-10-29) | 48 | 48 / 100 (round 1) |
| Cookiy Earn | cookiy, cookiy earn, cookiy.ai, cookiy earn text agent, cookiy earn sell session | AI agent you text that finds paid gigs (paid interviews, AI tasks, feedback); free, nothing to download | students, parents at home, side-hustlers, job seekers (US) | text chat, mobile web | [BRIEF](cookiy/BRIEF.md) | draft (site-checked 2026-11-03) | 0 + 1 reserved | 0 / 100 (1 reserved, round 1) |
| Emochi | emochi | AI character chat app: roleplay with thousands of characters, voice messages, memory, stories | young women who love fictional characters, book boyfriends, anime | phone app | [BRIEF](emochi/BRIEF.md) | draft | 0 | 0 / 100 |
| Pexo | pexo, pexo.ai | AI video agent: an idea or a website link becomes a finished video | small shop owners, freelancers, busy teams | web (laptop) | [BRIEF](pexo/BRIEF.md) | draft | 0 | 0 / 100 |
| IASO | iaso | Patient education on myeloma and CAR-T (a CAR-T maker) | patients and families in Malaysia, Singapore, Vietnam | none (education) | [BRIEF](iaso/BRIEF.md) | draft · health claims need care | 0 | 0 / 100 |
| Bybit mStocks | bybit, mstocks | Tokenised stocks on Bybit: 24/7 trading, tokens backed 1:1 by real shares | crypto traders in Brazil (PT-BR) | phone app | [BRIEF](bybit-mstocks/BRIEF.md) | draft · finance claims need care | 0 | 0 / 100 |

Super Nova (2026-11-03): a row's Brand and Product are matched here by `tools/lsc.py client`, the product first. Our Client Ledger's products Cookiy Earn Text Agent and Cookiy Earn Sell Session (brand Cookiy Labs) are Cookiy Earn; the brand name Cookiy Labs alone is not (its B2B product, Cookiy Insights on cookiy.ai, must never appear in an Earn post), so it gets its own client.

New client: add a row and a `<client>/BRIEF.md`. With no brief, the skill researches the company, drafts one marked `draft`, and lists its guesses.
