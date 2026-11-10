# IASO: brief

Brief status: **draft**. Written 2026-11-02 from the team's demo videos (Ken's "Spira AI - Client Demo Videos"), not from a client brief. The skill verifies every line against the client's site on its first run and marks what it can't confirm `[guessed]`.

Product: IASO, a CAR-T therapy maker. Social content is patient education on multiple myeloma and its treatment.
Product type: service / education (no app UI)
Where it shows: nowhere (education); the payoff is a practical action ("ask your doctor")
Real features: n/a for carousels. Topics: symptoms during treatment, infections, fertility, scans, when to call the care team
Audience: myeloma patients and their families
Markets: Malaysia (Malay), Singapore, Vietnam (Vietnamese), English
Pains, in their words: dizziness when standing · breathlessness · worry about flu · questions they forget to ask the doctor
Claims allowed: general patient education only
Never say: treatment advice, cure claims, drug promotion. Every carousel ends with "ask your doctor / care team". **Health content: check every line with Rey before generating.**

## Brand look
- Colors: orange gradient #F77D0C → #FFC32C (the most-used brand colours in the CSS), with nearby oranges #FF9E30 / #F08A06; navy #152E56 (footer/copyright band); ink #222; white #FFF. The navy #1B2F5B and orange #F7A12B in the demo videos were not found on the site; the site's own values are the ones above.
- Font: Poppins (English) and Tajawal (Arabic), both loaded as local fonts rather than from Google Fonts.
- Logo: header logo file https://en.iasobio.com/images/t_logo.png (light-header version t_logoa.png), footer https://en.iasobio.com/images/flogo.png. Its look and colour were not checked.
- Tone: hopeful, scientific and corporate: "Focusing on innovative biotherapies to bring hope of cure to patients". The site uses the word "cure"; carousels must still never make cure claims.
- Where it shows on a carousel: pills, CTA block and end-card in these colors; the product UI keeps its own real colors; caption text stays white-on-black (story) or white with outline (feed).
- Source: https://www.iasobio.com (same site as en.iasobio.com; HTML + style.css + site.css), checked 2026-11-02.
