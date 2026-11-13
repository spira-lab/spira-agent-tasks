---
name: explainer-practical-walkthrough-scriptwriting-style
description: Writes the narrator voice-over for a short-form explainer video (no talking head) in the Practical Walkthrough style: a calm narrator takes one real problem, shows the method that solves it with the product used inside one step, shows where the proof comes from, and ends on a short payoff line. Use when given a topic or the product's DNA (and optionally a duration) and asked for an explainer script. Outputs only the script as a single paragraph.
---

# Explainer Practical Walkthrough Scriptwriting Style

You are given the DNA of a product (or a brand), and sometimes a duration and instructions. Write one spoken explainer script: the voice-over of a 9:16 video with **no talking head and no presenter**. A narrator voice (ElevenLabs) reads your words, and the explainer designer turns each line into animated infographics, diagrams, kinetic text, product screens and b-roll. Your words are the whole spine of the video: what the viewer hears is what they are shown.

This style was drawn from 20 PartGenie explainers (an AI assistant for electronics engineers). The samples at the bottom are all PartGenie, but the style is for any brand: keep the shape and the voice, and take every fact from the DNA in your brief.

## Output rules

- Output the script only, as one continuous paragraph.
- No title, heading, labels, section names or line breaks inside a script.
- When asked for more than one option, give each script as its own paragraph, separated by a blank line, with no labels or numbering.
- No quotation marks around the script, no stage directions, no visual notes, no scene labels, no word count or timing notes. The designer decides the pictures from your words; never write them out.
- No preface, commentary or explanation before or after the script.
- Never ask the user a question. If something is unclear, make a sensible assumption and write the script.
- The request's instructions come first. When they ask for something this skill's defaults rule out (a length or word count, a call to action, a tone, not naming the product or brand, a structure of their own), follow the instructions; the defaults apply only where the instructions say nothing.
- Most row instructions are for the video designer, not for you: the logo, the voice line (`Use this voice: ...`), music, transitions, style sheets, on-screen text, translation. They never become spoken words. Only two of them change your script: the voice line can change the pace (see Length), and a translation note means you still write in English unless told otherwise.

## Length

- A narrator reads explainers at **2.6 to 2.9 words per second**. This was measured on 19 rendered PartGenie explainers voiced by Brian (ElevenLabs, `eleven_multilingual_v2`): 86 to 90 words took 29.4 to 36.6 seconds, 2.73 words per second on average.
- If no duration is given, the duration is 32 seconds (84 to 92 words; the samples are all 86 to 90).
- The word count must fall between duration × 2.6 and duration × 2.9.
- A voice on `eleven_v3` in the instructions reads slower (about 2.1 to 2.4 words per second, measured on IASO's narrator): use duration × 2.2 to duration × 2.5 for it, unless the instructions give a word count.
- Numbers, units and part codes slow the narrator down. Write a number the way it should be said when it matters ("three point three volts", "minus forty to eighty-five degrees") and count it as the words spoken. A script dense with figures (the samples with the most numbers ran at 2.4 words per second) stays near the low end of the range.
- Count the words before answering and adjust until the count is inside the range.

## Organic or ad

- **Organic** (every sample): never salesy, never like an ad. The narrator is nobody's spokesperson: no "we" or "our" for the brand, no price, no "free to start", no discount, no buy-now push, no superlatives about the product. The product earns its place by being the tool that does one step of the method.
- **Ad:** the organic rule may be relaxed this far: one plain closing line naming the product and what to do, or an offer, taken only from the instructions or the DNA. Keep the calm walkthrough voice; never turn it into hype.
- No follow, comment, like or DM call to action unless the request asks for one. End on the payoff line.

## What makes it an explainer, not a talking head

A talking head is a person reacting to the product to the camera ("you can now...", "here's the crazy part"). An explainer is a voice showing how something works so the viewer understands it. Hold to these:

- **No presenter.** No "I", "me", "my", "we", "us". No "in this video", "watch this", "as you can see", "on screen", "let me show you", "hey guys", no greeting, no sign-off. Nobody is on camera, so nothing refers to a face, a camera or a speaker.
- **Second person, mostly imperative.** The viewer is told what to do ("Type the part number", "Write that range down first", "Check stock"), or the narrator states how things are ("Capacity is printed on the cell."). "You" appears in only a third of the samples; the imperative does the work.
- **Every sentence is showable.** Each line hands the designer something concrete to animate: an object, a number, a step, a comparison, a before and after, a formula, a list, a product screen. A line with nothing to show ("it's a total game changer") has no place. Examples from the samples:
  - "Fifty boards, one tiny capacitor, and a listing that only sells it by the thousand." (a counter, a part close-up, a listing card)
  - "Battery life is one division: the battery's capacity over the board's average current." (a fraction building on screen)
  - "A car dashboard in July, a chest freezer, a sealed box on a sunny roof." (three quick scenes, a thermometer)
  - "Upload the BOM to PartGenie, and it pulls out every part number." (a file dropping into the product, rows lighting up)
  - "Then check each datasheet for resistance at that gate voltage." (a spec table with one row highlighted)
- **Show and understand, not hype.** The viewer should finish knowing a method, a rule, a check or a formula they can reuse, even without the product. The product makes one step faster or more certain; it is never the whole point.
- **Slower and tighter.** About 2.7 words per second against a talking head's 3.7 to 4.0, so there is room for the picture to land. About 88 words for half a minute: every word earns its place.

## How the samples are built

Use this as the shape, not as a fill-in template. Every script finds its own words.

1. **Hook (sentence 1, usually 9 to 21 words).** One real problem, situation, rule or question from the viewer's world, concrete enough to picture. The product is not in it, except when the topic is the product's own structure (its modes, its levels: samples 3 and 5). The kinds of hooks in the samples:
   - a "How to" promise (sample 1)
   - a situation that just went wrong (samples 2, 12, 18)
   - a framework count: "two modes", "three levels", "four details", "one of two reasons" (samples 3, 5, 7, 10)
   - the common mistake or the thing everyone gets backwards (samples 6, 9, 15, 19)
   - a question the viewer has asked themselves (samples 8, 20), or a "coming from X?" (sample 14)
   - a call to one audience: "Repair technicians, never..." (sample 17), or a role named in the second line (samples 18, 20)
   - a definition or formula stated flat (sample 16), an instruction to do something right now (sample 11), a list of vivid places (sample 13)
2. **Why it matters (0 to 2 sentences).** The cost of getting it wrong, or the reason the obvious way fails. Often a short flat line ("Nobody checked the gate.", "Average current usually gets guessed.").
3. **Turn (one short line).** The move from problem to method: "Flip it and start with the board.", "Build it instead.", "Treat it like a real decision.", "Answer it on the spot." Vary it; never default to "Here's how".
4. **Method, with the product inside it (3 to 5 beats).** Concrete actions in order. The product is named **once**, as the tool for one action (sentence 2 to 6; most often 3 or 4): type, upload, photograph, ask, compare, generate. Only describe what the DNA says the product does; never invent a feature, a button or a screen. Steps may be signposted ("Step one", "First", "One,", "Level one") in about a quarter of the scripts; the rest flow as plain sentences. Name every item; never point at a list the viewer cannot hear.
5. **Proof (1 sentence).** Where the answer comes from and how the viewer can check it, taken from the DNA's reason to believe. For PartGenie it is the manufacturer's datasheet behind every answer (17 of 20 samples). For another brand it is whatever the DNA gives as proof: a source, a test, a standard, a number on the label. Never invent one.
6. **Real-world check (optional, 1 sentence).** The constraint that decides it in practice. For PartGenie it is stock, minimum order and lifecycle (12 of 20). Use it only when the brand has one.
7. **Payoff line (last sentence, 3 to 12 words).** A short line that restates what changed, usually a balanced pair or a callback to the hook: "Same board, new part, layout untouched.", "Pick parts for the place, not the lab.", "Quote what can ship.", "The answer leaves the room with its proof." It works as the end card. Never a question, never a call to action.

## Voice and sentences

- Calm, precise, confident: an experienced colleague walking someone through it, never a salesperson and never a lecturer.
- Sentences average about 11 words (median 10, from 1 to 25). Six to ten sentences in 32 seconds. Mix one or two longer explaining sentences with short flat ones and the odd fragment ("Rule of thumb.", "Then check stock.", "Discontinued?").
- Specific over general: real units, real part types, real tool and distributor names, real numbers, all from the DNA or common knowledge of the trade. Do not invent precise statistics about real companies, people or products.
- Speak the audience's trade correctly and explain a term once in plain words when the viewer may not know it ("The headline resistance on a datasheet is measured at a set gate voltage...").
- Spoken, not written: contractions, plain verbs, no semicolons, no parentheses, no "Furthermore". Read it aloud; if a line is hard to say in one breath, split it.

## Phrasings to keep rare

The samples lean on a few lines. They are fine once in a while, but never in every script, and never twice in one batch:

- "the manufacturer's datasheet", "open the datasheet behind each one", "an answer tied to its source": the proof beat is needed, its wording is not. Say it a new way each time.
- "Then check stock" as the second-last beat, "who has it in stock", "pricing, stock and minimum order quantity across distributors like DigiKey, Mouser and LCSC".
- "pin-compatible alternatives", "compare the tradeoffs side by side", "lifecycle risk".
- "in plain language", "in plain words", "one plain sentence", and the "one sentence in / one question" motif.
- "like ..." to bring in an example (half the samples): use it at most once per script.
- "Here's the fix / Here's a shorter route / Here's what it looks like now".
- The "X, not Y" closer ("for the place, not the lab", "by boards, not by parts"): vary the close's shape.

Do not reuse lines or phrases from the samples, and never copy a sample's angle for PartGenie. Facts come from the DNA in your brief, never from the samples.

## No product, or a brand that may not be named

- No product: the brand is the subject, and the method uses what the brand offers.
- Brandless: the angle is the subject; the method is generic and no product is named.
- When the instructions say not to name the brand or product (e.g. a medical-awareness brand), the method and the proof stand on their own: teach the idea, end on the practical takeaway, and name nothing.

## Options

- When asked for several scripts, every script must be clearly different from the others, not a light rewording.
- Each one opens with a different kind of hook from the list above, with its own sentence shape and opening words. No two hooks share a structure or lead with the same idea.
- Vary the rest too: the beat order, whether steps are signposted, where the product comes in, the proof wording, and the shape of the payoff line.
- Before answering, compare the scripts side by side, starting with the hooks and the last lines. If any two feel close, rewrite one until it stands apart.

## Samples

PartGenie explainers (organic, voiced by Brian at about 2.7 words per second, 86 to 90 words, about 30 to 37 seconds each). Study how each one opens, turns, brings the product in once, shows its proof and closes. They are PartGenie-only facts: never reuse them for another brand.

### Sample 1: "How to" promise, numbered steps (Task 265, 88 words)

How to pull the one spec you need out of a datasheet that runs hundreds of pages. Step one, open PartGenie and type in the part number, or upload the datasheet itself. Step two, ask it like you would ask a coworker: what is the maximum operating temperature, or which pins handle I2C? Step three, check the source. Every answer traces back to the manufacturer's own datasheet, so you can confirm the exact line before it lands in your design. Pages of scrolling, swapped for one plain question.

---

### Sample 2: situation gone wrong, "three moves" (Task 273, 86 words)

A part goes out of stock right before your build, and the board is already laid out. Here's the fix in three moves. First, type the part number into PartGenie and ask for pin-compatible alternatives, so the footprint on your board stays the same. Second, compare the tradeoffs side by side, because a matching pinout doesn't mean matching specs. Third, open the manufacturer datasheet behind each option and confirm the numbers yourself. Then check who actually has it in stock. Same board, new part, layout untouched.

---

### Sample 3: the product's own structure: two modes (Task 274, 88 words)

PartGenie has two modes, Search and Work, and picking the right one is the whole trick. Use Search when your question fits in one line. What's the input voltage range on this regulator? You get a direct answer tied to its source. Use Work when the job has steps. Say you need parts for a new sensor board. Hand over the goal, and Work maps out an architecture, selects the parts, builds the BOM and flags lifecycle risk. Rule of thumb. One question, Search. A whole task, Work.

---

### Sample 4: the step everyone would skip (Task 275, 89 words)

Drawing schematic symbols and footprints by hand is the step every hardware project would love to skip. Here's what it looks like now. Pick your part in PartGenie, and it generates the symbol, the footprint and the 3D model from the manufacturer's own data. Each one is verified before you use it, so a pad spacing typo doesn't end up on a finished board. Then drop the files into the tool you already design in, whether that's Altium, KiCad, Eagle, OrCAD or Allegro. Less time drawing, more time designing.

---

### Sample 5: the product's own structure: three levels (Task 276, 90 words)

There are three levels to using PartGenie, and each one moves it closer to where you already work. Level one, the browser or the phone app. Ask a quick engineering question in plain language and get an answer tied to a datasheet. Level two, bring it into your daily tools, with a Chrome extension and workflows inside Altium, KiCad and PADS. Level three, connect your AI agents through MCP, so they can pull verified data on more than 56 million parts from over 12,700 manufacturers. One source, three ways in.

---

### Sample 6: the common habit, flipped (Task 310, 87 words)

Most people pick a microcontroller by reaching for the chip they used last time. Flip it and start with the board. Write down what it has to do, like run on two AA batteries, connect over Wi-Fi and drive a display. Type that into PartGenie and ask which MCUs fit. It compares the tradeoffs and ties every spec to the manufacturer's datasheet, so each number can be checked. Then look at stock before settling. The familiar chip might still win. Now it has to earn the spot.

---

### Sample 7: "one of two reasons" (Task 311, 88 words)

A sensor can look perfect on paper and still let a design down, for one of two reasons. The first is trusting the headline number on a product page, when that's rarely the spec the project depends on. Ask PartGenie the real question, like how accurate this humidity sensor stays across its temperature range, and get the answer from the manufacturer's datasheet. The second is a sensor that's hard to get. Check stock and minimum order quantity at distributors, and look for lifecycle risk. Right spec, right supply.

---

### Sample 8: a question with a number in it (Task 312, 89 words)

What does it take to find a voltage regulator for a board fed by 24 volts that needs a clean 5? Usually an afternoon of filter menus and open tabs. Here's a shorter route. Ask PartGenie in one sentence, like 24 volts down to 5 at around two amps in a small package. It comes back with candidates, specs, datasheets and what each one trades off, like efficiency against board space. Pick one, then grab its symbol, footprint and 3D model. One sentence in, a part ready to place.

---

### Sample 9: the part everyone treats as dull (Task 313, 88 words)

Connectors look like the dull part of a board, so they get picked last, in a hurry. That's backwards, because a connector touches everything: the layout, the enclosure, the cable on the other end. Treat it like a real decision. Search connectors in PartGenie by what matters, like pitch, pin count and current rating, and open the datasheet behind each result. Generate the footprint from manufacturer data, so the pads match the real part. Then check stock before locking it in. The dull part deserves five careful minutes.

---

### Sample 10: a four-item framework, counted out (Task 314, 87 words)

Every resistor or capacitor search comes down to four details, and once they're clear, finding passives gets fast. One, the value, like 10 kilohms or 4.7 microfarads. Two, the rating, voltage for a capacitor, power for a resistor. Three, the package size, like 0603. Four, the quantity needed. Put all four into one plain sentence in PartGenie. It finds matching parts with datasheets, then lines up pricing and stock across distributors like LCSC and TME. Four details, one sentence, and the smallest parts stop eating the afternoon.

---

### Sample 11: an instruction to do it now (Task 341, 89 words)

Point at any line on a bill of materials and ask one question. If this part disappeared tomorrow, what's plan B? A line with no answer is a single point of failure, and it's usually hiding somewhere boring. Find a second source now. Upload the BOM to PartGenie, and it pulls out every part number. For each critical line, ask for alternatives, then compare the tradeoffs and open the datasheet behind each one. Check that the backup is stocked across distributors. Plan B, written down while it's still optional.

---

### Sample 12: a situation in numbers, a simple formula (Task 342, 89 words)

Fifty boards, one tiny capacitor, and a listing that only sells it by the thousand. Now a one-cent part costs far more per board. The math is simple. Take what you're forced to buy, not what you need, and divide by the number of boards. In PartGenie, line up minimum order quantity, pricing and stock across distributors like DigiKey, Mouser and LCSC. If every listing wants a big order, ask for alternatives and run the same math. Divide by boards, not by parts, and the real price shows up.

---

### Sample 13: three vivid places (Task 343, 89 words)

A car dashboard in July, a chest freezer, a sealed box on a sunny roof. Three different homes for a circuit board, and each one rewrites the parts list. Every part has to survive the full temperature range of where it lives. Write that range down first and make it part of the search. Ask PartGenie for parts rated across it, like a regulator that runs from minus forty to eighty-five degrees. Confirm each rating in its datasheet. Then check stock. Pick parts for the place, not the lab.

---

### Sample 14: "Coming from X?", an analogy map (Task 344, 88 words)

Coming to hardware from software? Most of what you already know still applies, it just goes by different names. The documentation is now a datasheet. Ask PartGenie a question in plain language and get an answer tied to the manufacturer's source, like docs with search built in. A deprecated library is now an obsolete part, so upload the BOM and let it flag lifecycle risk. And the package manager is now a set of distributors, with real stock, real prices and minimum order quantities. Same instincts, new dependencies.

---

### Sample 15: the usual suspect is wrong (Task 345, 89 words)

A MOSFET running hot on a microcontroller board usually didn't have the wrong voltage rating. Nobody checked the gate. The headline resistance on a datasheet is measured at a set gate voltage, often ten volts, while a microcontroller pin might give three point three. There, the part may barely switch on. Search for a logic-level MOSFET. Tell PartGenie the drain voltage, the current, and the three point three volt gate drive. Then check each datasheet for resistance at that gate voltage. Match the part to the pin driving it.

---

### Sample 16: a formula stated flat (Task 374, 88 words)

Battery life is one division: the battery's capacity over the board's average current. Capacity is printed on the cell. Average current usually gets guessed. Build it instead. List every part that draws power, the microcontroller, the sensor, the radio. Ask PartGenie for each one's sleep current and active current, and open the datasheet line behind every number. Then weight each by time. A radio that's on one second a minute adds a sixtieth of its active draw. Add it up, divide, and the estimate has math behind it.

---

### Sample 17: a call to one audience (Task 375, 87 words)

Repair technicians, never order a replacement chip off its marking alone. Those markings are short codes, and the same few letters can sit on more than one part. Photograph the board and upload it to PartGenie. It recognizes the components and pulls out the key data. Then confirm the match against the manufacturer's datasheet. Discontinued? Ask for pin-compatible alternatives that land on the same pads, compare what each one changes, and check who has it in stock. The device comes back to life on the right part.

---

### Sample 18: a role under a deadline (Task 376, 88 words)

A customer's parts list lands at nine, and the quote is due by five. For a contract manufacturer, the real risk isn't the price. It's quoting a board that can't be built. Upload the list to PartGenie. It extracts every part number and checks each line for obsolete parts, so a dead component turns up before it's priced in. Next, line up pricing, stock and minimum order quantity across DigiKey, Arrow and TME. Any shaky line gets an alternative, datasheet attached for the customer. Quote what can ship.

---

### Sample 19: a relatable mess, a three-check list (Task 377, 88 words)

That drawer of parts from weekend projects gone wrong? Most of them failed a check nobody ran before checkout. Run those checks in PartGenie first. Voltage: ask whether the part runs on the three point three volts the project has. Package: find out if it's a tiny surface-mount version or one that can be soldered by hand. Pinout: chat with the datasheet about which pin does what before any wire goes in. Each answer points to the manufacturer's source. Ask before the cart, and the drawer stops growing.

---

### Sample 20: the question asked mid-meeting (Task 378, 88 words)

Can this part run off a single lithium cell? For a field application engineer, that question tends to land mid-meeting, with the customer waiting. Answer it on the spot. Open PartGenie on the phone and ask in plain words. The reply comes with its source, the manufacturer's datasheet, so the customer sees the number too. Then the follow-ups. Is there a pin-compatible option with better stock? Will it still be made next year? Ask those too, and check lifecycle risk. The answer leaves the room with its proof.
