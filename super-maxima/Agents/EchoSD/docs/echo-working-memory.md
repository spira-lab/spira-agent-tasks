# Echo — Working memory

What the user asked Echo to remember, kept across sessions. Echo's tools read it; Echo writes
to it only when the user (through Nova) asks her to remember, change, or forget something.

## Product writing styles

A product listed here has its own writing styles. For that video style, its scripts cycle
**only** through the styles listed, and those styles are **never** given to any other product,
brand, or Brandless script. The cycling tool and the director tool apply this table; keep one
row per product and video style, and write the styles exactly as in `styles/echo-styles.md`,
separated by commas.

| Product | Video style | Cycle only these writing styles |
|---|---|---|
| Cookiy Earn Text Agent | talking head edited | cookiy editorial, cookiy buyer, cookiy professional |

## Angle rules

How each brand's angle (the one core subject of a script) may repeat. Echo's repeat check
(`tools/echo-similar.py`) and the writers' briefs apply this table. A brand or product with
no row follows the default: the angle is the script's core subject, and no recorded angle
of that brand is ever repeated. One row per brand and product. "Last N" counts the brand's
newest recorded scripts. "Pick only from" is a list file under `docs/angle-lists/`, or "-".

| Brand | Product | The angle is | Never repeat within the last | Pick only from |
|---|---|---|---|---|
| Cookiy Labs | Cookiy Earn Text Agent | the profession (the person speaking, or the expert a team is looking for) | 30 | docs/angle-lists/CookiyLabs-professions.md |
| IASO | - | the script's one core subject | 100 | - |

**Carousels** (every carousel style, e.g. `corporate carousel`, which was named `carousel` until the rename the same day; the owner's rule, 2026-10-27): a carousel's angle is its one core topic, and **a carousel angle never repeats within the brand's last 75 carousels** (the owner, 2026-10-27; it was never-repeat at install, changed the same day so the record doesn't bloat). They are kept in their own record, `scripts/<Brand>/carousel-angles.json`, one per brand for every carousel style, and checked only against that brand's earlier carousel angles: a video angle never blocks a carousel angle. The rows above are for video scripts and do not apply to carousels.
