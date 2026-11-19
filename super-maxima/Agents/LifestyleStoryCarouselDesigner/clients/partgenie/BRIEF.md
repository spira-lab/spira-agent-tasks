# PartGenie: client brief

**Source:** the official "PartGenie — Social Content Brief" (4 pages), received 2026-10-29. Saved at
`brief/PartGenie-Social-Content-Brief.pdf`, with the text in `brief/brief.txt`. Brand colors and fonts come
from partgenie.ai itself, because the brief has none.

## Brand
- An AI assistant for hardware engineers: find components, understand datasheets, design circuits,
  build and source a BOM.
- Tagline: **"Build hardware with AI you can verify."**
- Social bio: "The intelligence layer for hardware design. Components. Datasheets. Better decisions."
- Owned by AuraLoom LLC, Ann Arbor, Michigan. Launched November 2025.
- Origin story: the founder's parents ran an electronics factory. This is unused so far and would make a good carousel angle.
- Channels:
  - partgenie.ai
  - Instagram @partgenieai (~470 followers, 17 posts)
  - TikTok @partgenieai (~190)
  - LinkedIn (~46)
  - X @PartGenie
  - YouTube @partgenie (~10)

## Features (only these, never invent)
- **Parts database:** 56M+ components from 12,700+ manufacturers.
- **Search** in plain English. Pin-compatible alternatives. Side-by-side comparison.
- **Chat with a datasheet** instead of reading hundreds of pages.
- **Upload and identify:** circuit diagrams, PCB photos, chip markings, datasheets or BOMs.
  - PCB Photo Identifier (site, 2026-11-09): upload a board or region photo; lists readable IC marks, printed passive ratings and candidate MPNs, then datasheet Q&A or Alternative Finder. The site says it is "not a full automated BOM extractor": no unmarked MLCC values, glare or blurry marks. Free within the monthly allowance. Never claim it reads a burned or unreadable marking.
- **AI Hardware Designer:** describe a product, and it proposes the architecture, picks parts and builds the BOM.
- **Smart BOM:**
  - flags obsolete or risky parts
  - shows pricing and stock
  - finds cheaper alternatives
  - lets you chat with your BOM
  - BOM Analyzer (site, 2026-11-05): upload CSV or XLSX with no template, free health check, 0-100 health score, nothing is written to the BOM until you confirm it. The public product image shows a demo BOM (`partgenie_ev_control_module_test_bom`, 47 lines, Health 94%).
- **Design-ready ECAD:** symbols, footprints and 3D models for Altium, KiCad, Eagle, OrCAD, Allegro and more. KiCad Generator (site, 2026-11-04): enter an MPN, get a KiCad 8 symbol, footprint and 3D model with a machine import check before download; the site says "Review before production". Part pages say login required, CAD models billed separately as an add-on.
- **Sourcing:** compares pricing, stock, MOQ and availability across distributors. Includes a tariff lookup: part number to HTS code and US duty stack by origin, across "19,000+ tariff lines" (site, 2026-11-04). The site says estimates only, not a binding ruling; never call it final.
- **Platforms:** web, iOS, Android and a Chrome extension.
  - Chrome extension (Chrome Web Store listing, checked 2026-11-06, v0.1.54): recognizes the MPN on supported distributor and manufacturer product pages and opens a Chrome side panel with alternatives, ECAD (symbols, footprints, 3D, Generate KiCad) and price and stock from multiple sources; floating shortcuts on the page. The store screenshot says "Works on 60+ distributor & manufacturer catalog pages". The listing shows a user count: never quote it (no user numbers).
- **Key promise:** answers trace back to manufacturer datasheets and trusted sources. "AI you can verify,
  unlike ChatGPT."

## Pricing (for CTA slides)
- **Free:** $0, for students and makers, 50 AI credits a month.
- **Pro:** $29/mo (20% off annually), 420 credits a month, full alternatives, BOM Health and export,
  7-day free trial.
- **Education** (site, https://www.partgenie.ai/education, checked 2026-11-18, not in the client brief): 12 months of Pro complimentary for hardware/EE students at accredited schools with a verified school email, no card. Not yet used on slides.
- **Business / Enterprise:** custom pricing, with team libraries, SSO, ERP/PLM integrations and API.
- Early-stage startup. **Don't claim user numbers or funding.** There are none public.

## Audience and their pains
| Audience | Who | Main pains |
|---|---|---|
| Hardware / electrical engineers | design PCBs, pick parts | datasheet digging, EOL parts, drop-in replacements |
| FAEs | build solutions and BOMs for customers | building BOMs by hand, fast alternatives |
| Sourcing / procurement | supply risk, alternatives, cost | out of stock, obsolete parts, pricing, MOQ, tariffs |
| Students / makers / hobbyists | Arduino, ESP32, KiCad, free tier | datasheets, footprints, finding parts |

## Competitors (don't name them in a negative way; ChatGPT is the brief's own contrast)
- AI hardware tools: Flux, SnapMagic, CELUS, CircuitMind, Zenode, Z2Data
- Part search and CAD libraries: Octopart, Findchips, Ultra Librarian, AllDatasheet
- Distributors: DigiKey, Mouser, Arrow, LCSC
- General AI: ChatGPT, Gemini

These competitors' feeds are also research sources for Step 2: check what they're posting.

## Where the audience talks (research)
- r/PrintedCircuitBoard, r/AskElectronics, r/embedded, r/ElectricalEngineering, r/arduino, r/esp32, r/KiCad
- EEVblog forum, Hacker News
- hardware LinkedIn/X

## Brand look (from partgenie.ai)
- Colors: teal `#22808D` / `#207883`, light teal `#D5F0F2`, ink `#101828`.
- Status colors: success `#067647`, warning `#B54708`, error `#B42318`.
- Font: Inter Tight.
- Tone: plain, technical, confident; "AI you can verify". Insider engineer jargon on slides.
- Where it shows on a carousel: year pills, the CTA block and any end card in teal; Ryan's 2026 pill uses the teal, so it matches.
- Numbers: the brief says 56M+ parts (used on Ryan's slides too); one site page says 35M+. The brief wins.

## Rules
- UI screens are real screenshots, never generated.
- Engineers spot fakes, so check for melted chip text, wrong pin counts and impossible traces.
- Characters are fictional. Never base one on a real person's likeness.

## Not in the brief (ask / playbook)
- Carousel cadence, CTA wording, captions and hashtags, delivery.
- Which channel each format is for: 9:16 vs 4:5.

## Angles the brief opens up (unused so far)
- The founder's factory origin story.
- AI Hardware Designer: "describe a product, get a BOM".
- Tariff lookup, a natural news hook.
- Student/maker angle: Arduino, ESP32, KiCad, free tier.
- "Unlike ChatGPT": a verified answer vs a confident wrong one (see the reels script "The Chatbot Said…").
- FAE angle: a customer BOM due tomorrow.
