# Designer lessons

Lessons that designers proposed in their metadata ("lessons"), added by Nova after the owner's OK (rule 2026-10-24). Designers read this file; only Nova writes to it.

| Date | Designer | Lesson |
|---|---|---|
| 2026-10-27 | All (from Carousel 366) | When a brand's site gives two different figures (e.g. PartGenie: 56M+ parts in the homepage headline, 35 million in the FAQ), use the current headline figure; FAQs are often out of date (the owner's word). |
| 2026-11-09 | Re-skit (Task 279) | Burned-in source captions: don't use reskit.py's removelogo mask (`cutref --mask`); it took about 8 min per 3 s reference, timed out on 12 s ones, and smeared hair into the box. Blur the caption bands once over the whole source under a feathered mask (about 1 min for 67 s) and cut every reference from that copy without `--mask`. Wan repainted the blurred bands cleanly in 7 of 7 clips. |
| 2026-11-09 | Re-skit (Task 279) | Re-voiced lines often run 0.3–0.8 s past the source slot they replace. Give every clip at least 1 s of output past the last planned word, and set segment ends from the landed clip's transcript, not the source timings. |
