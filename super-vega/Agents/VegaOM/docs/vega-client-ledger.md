# Vega — Client Ledger

Owned by Vega. Source of truth for client brands, products, where their DNA lives, brand colors, and where their assets are.

## How to use

- **Two kinds of row.** A **brand row** has the Product name empty: it is the brand's own record. A **product row** names one product (one row per product).
  - Product name covers DTC / e-commerce products or collections, SaaS features (one row per feature), or subsidiaries (one row per subsidiary).
- **DNA** — the **DNA reference** of that row (the path of its local DNA Markdown file; older rows may still hold a Lark URL), the source of information about the brand or the product. Written by Quill and recorded by Vega from Quill's approved brief.
  - Every DNA has the same fields: Brand name, Product name (empty when there is no product), Description, Key highlights, RTB (up to 5 each).
  - Vega passes the URL on. She does not open the DNA docs herself.
- **Brand colors / Brand logo** — brand-wide, kept on the brand row. Hex codes (e.g. `#1A2B3C`); several separated with `<br>`.
- **Website** — the brand's or product's own site (the page Quill researched). Passed only to the Cloner and Re-skit designers (the owner's rule, 2026-10-24), which read it for brand info and capture UI screenshots from it, and to every carousel designer (the Corporate Carousel Designer, 2026-10-27), which makes each carousel from it: a carousel cannot be made for a brand or product without one. A product row without one falls back to the brand row's.
- **Product images** — on the product row: hosted URL + local path. Local files live in `Agents/VegaOM/client-assets/<BrandName>/`, named `<BrandName>_logo`, `<BrandName>_<ProductName>_prdIMG<N>`. Several images: one per line, separated with `<br>`.

## Ledger

| Brand name | Product name | DNA (Lark URL) | Brand colors (hex) | Brand logo (hosted URL) | Brand logo (local path) | Product images (hosted URL) | Product images (local path) | Website |
|---|---|---|---|---|---|---|---|---|
| Cookiy Labs | Cookiy Earn Sell Session |  |  | https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791493697881-0f6408c8-9e5b-438f-a3de-5ee8004f8e1a.png | `Agents/VegaOM/client-assets/CookiyLabs/CookiyLabs_logo.png` |  |  |  |
| Cookiy Labs | Cookiy Earn Text Agent | https://ljpp9tldvzuk.jp.larksuite.com/docx/PZKFdnyhVobzGaxyXuQj1XyPpLc |  | https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791493697881-0f6408c8-9e5b-438f-a3de-5ee8004f8e1a.png | `Agents/VegaOM/client-assets/CookiyLabs/CookiyLabs_logo.png` |  |  | https://cookiylabs.com/agent/site/ |
| Emochi |  | https://ljpp9tldvzuk.jp.larksuite.com/docx/Rw6udq2AYoxFQvxo8CtjTK3Kpkb |  |  |  |  |  | https://emochi.com |
| IASO |  |  | #152E56<br>#F5A253<br>#FFA32A<br>#8598B7<br>#171717<br>#FFFFFF | https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791948664524-8c6800aa-778c-4ac3-9860-0b3949d7060d.png | `Agents/VegaOM/client-assets/IASO/IASO_logo.png` |  |  | https://www.iasobio.com/ |
| IASO | FUCASO | https://ljpp9tldvzuk.jp.larksuite.com/docx/ZUtQd4d91osKRHxrafQjudsQpwd |  |  |  | https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791948666695-bdfa39e3-16f4-4a60-9ab4-fe8a34064738.png<br>https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1791948668395-a0e38049-acd9-4a15-a35e-2a0860a45dd4.png | `Agents/VegaOM/client-assets/IASO/IASO_FUCASO_prdIMG1.png`<br>`Agents/VegaOM/client-assets/IASO/IASO_FUCASO_prdIMG2.png` | https://www.iasobio.com/ |
| PartGenie |  | https://ljpp9tldvzuk.jp.larksuite.com/docx/QWXodgvmjo1drXxocERj7PVIp8e | #227F8E<br>#222421 | https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1792724332988-1a4dfe63-cf84-418d-b6b7-c065ab9851d0.png | `Agents/VegaOM/client-assets/PartGenie/PartGenie_logo.png` |  |  | https://www.partgenie.ai/ |
| Spira |  |  | #FF6F00<br>#17161A<br>#F8F8F8 | https://static.viralwell.ai/assets/media/308864c5-67b4-47a3-9d2b-8aa8741308f1/uploads/1792529669522-237e7993-b291-458a-9d92-16d288d1e1ba.png | `Agents/VegaOM/client-assets/Spira/Spira_logo.png` |  |  | https://spira.ai/ |
| Spira | Spira Maxima | https://ljpp9tldvzuk.jp.larksuite.com/docx/T0iMdqZQPogAZvxzdmBjLf4PpUd |  |  |  |  |  | https://spira.ai/ |
