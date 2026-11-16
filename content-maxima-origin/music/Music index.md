# Music index
Grouped by what each track is not for. file | genre / style | mood | energy 1-10 | BPM | best for | gain | flags. Copy `gain` onto `<audio id="bgm">` as `data-gain-db`, as it is.
Flags: late-start (not on the first beat), silence Ns (gap over 2 s), busy (competes with speech: short high-energy stretches only), solo (busy solo style for short comedic or chaotic beats; its lower level is already in the gain), mix_note (follow it). Fetch with `python3 tools/fetch-resource.py music/<file> …`.

## Not for: Calm, serious or sensitive topics
BT01.mp3 | Chillhop / Lo-Fi Hip Hop | chill, groovy, positive | e6 | 96 | Tech product reviews; Lifestyle vlogs | -4.4 dB
BT02.mp3 | Future Bass / Pop EDM | uplifting, energetic, optimistic | e7 | 150 | Tech product reviews; Travel vlogs | -4.7 dB | late-start | busy
BT03.mp3 | Nu-Disco / Funk Pop / Modern Disco | upbeat, confident, energetic | e8 | 118 | Upbeat tech product reviews; Energetic corporate sizzle reels | -2.4 dB | busy
BT04.mp3 | Future Bass / Kawaii Bass | energetic, cheerful, bouncy | e8 | 160 | Tech and gadget reviews; Gaming vlogs and Let's Plays | -3.3 dB | busy
BT05.mp3 | Electronic Dance Music / Electro House | energetic, hyped, driving | e8 | 130 | Fitness and workout tutorial intros; Gaming channel commentary and montages | -2.4 dB | busy
BT06.mp3 | Cinematic Trap / Orchestral Hip-Hop | dramatic, tense, elegant | e7 | 142 | Luxury car commercials; High-end real estate or architecture video essays | -3.2 dB | busy
BT07.mp3 | Electronic / Synthwave | uplifting, driving, optimistic | e6 | 122 | Tech product reviews; Corporate innovation presentations | -6.3 dB | late-start
BT08.mp3 | Lo-fi House / Deep House | chill, sophisticated, reflective | e4 | 132 | Tech product reviews; Lifestyle and travel vlogs | -3.7 dB
BT09.mp3 | Electronic Pop / Tropical Pop | upbeat, playful, energetic | e7 | 140 | Tech reviews; Travel vlogs | -12.1 dB

## Not for: Hype, party or aggressive content
CD01.mp3 | Cinematic underscore / Minimalist documentary underscore with no drums | investigative, curious, thoughtful | e5 | 104 | True crime or investigative journalism documentaries; Corporate explainer videos detailing a complex process | -7.6 dB
CD02.mp3 | Cinematic underscore / Minimalist documentary underscore with no drums | focused process, focused, investigative | e4 | 96 | True crime or investigative journalism documentaries; Corporate explainer videos detailing a complex process | -3.6 dB
CD03.mp3 | Cinematic underscore / Minimalist documentary underscore with no drums | hopeful discovery, hopeful, reflective | e3 | 112 | True crime or investigative journalism documentaries; Corporate explainer videos detailing a complex process | -5.6 dB
CD04.mp3 | Cinematic underscore / Minimalist documentary underscore with no drums | wonder, reflective, introspective | e3 | 92 | True crime or investigative journalism documentaries; Corporate explainer videos detailing a complex process | -8.1 dB
CD05.mp3 | Cinematic underscore / Minimalist documentary underscore with no drums | curious, investigative, thoughtful | e5 | 108 | True crime or investigative journalism documentaries; Corporate explainer videos detailing a complex process | -8.1 dB

## Not for: Calm, emotional, wellness or family-friendly topics
DD01.mp3 | Synthwave / Dark driving synthwave (darksynth) | cold futuristic suspense, dark, driving | e5 | 114 | Tech and gadget reviews; Cybersecurity documentaries | -7.1 dB
DD02.mp3 | Synthwave / Dark driving synthwave (darksynth) | focused determination, dark, driving | e4 | 112 | Tech and gadget reviews; Cybersecurity documentaries | -2.6 dB
DD03.mp3 | Synthwave / Dark driving synthwave (darksynth) | night-city urgency, dark, driving | e7 | 120 | Tech and gadget reviews; Cybersecurity documentaries | -3.1 dB
DD04.mp3 | Synthwave / Dark driving synthwave (darksynth) | tense investigation, dark, driving | e6 | 110 | Tech and gadget reviews; Cybersecurity documentaries | -4.6 dB
DD05.mp3 | Synthwave / Dark driving synthwave (darksynth) | cyber-thriller focus, driving, dark | e6 | 122 | Tech and gadget reviews; Cybersecurity documentaries | -6.6 dB

## Not for: Upbeat, celebratory or comedic content
DM01.mp3 | Cinematic / Modern Classical | melancholic, reflective, mysterious | e3 | 117 | True crime documentaries; Scientific explanations (space, deep sea, technology) | -13.8 dB
DM02.mp3 | Lo-fi Hip Hop / Chillhop | chill, relaxing, introspective | e3 | 90 | Tech and coding tutorials; Lifestyle vlogs | -7.1 dB
DM03.mp3 | Synthwave / Retrowave | driving, optimistic, focused | e7 | 115 | Tech product reviews; Esports or gaming documentaries | -6.4 dB
DM04.mp3 | Cinematic / Modern Classical | reflective, poignant, melancholic | e3 | 117 | Documentary interviews about personal struggles or triumphs; Charity appeal videos | -6.5 dB
DM05.mp3 | Lo-Fi / Ambient / Chillhop | reflective, calm, introspective | e3 | 112 | Tech product reviews; Vlogs and lifestyle content | -5.1 dB
DM06.mp3 | Modern Classical / Cinematic | inspiring, hopeful, reflective | e6 | 152 | Corporate brand anthems; Documentary emotional turning points | -8.1 dB
DM07.mp3 | Lo-fi Hip Hop / Chillhop | relaxed, contemplative, mellow | e3 | 86 | Tech reviews; Vlogs | -16.3 dB | late-start
DM08.mp3 | Cinematic Ambient / Modern Classical | reflective, melancholic, introspective | e3 | 117 | Documentaries; Charity appeals | -8.3 dB
DM09.mp3 | Lo-fi Hip Hop / Chillhop | reflective, relaxed, introspective | e3 | 92 | Tech reviews; Vlogs | -8.8 dB

## Not for: Corporate, uplifting or family-friendly messages
DT01.mp3 | Hip-hop / Trap / Dark half-time trap instrumental | cold and calculating, dark, eerie | e5 | 130 | True crime YouTube videos; Urban documentary segments | -3.1 dB
DT02.mp3 | Hip-hop / Trap / Dark half-time trap instrumental | gritty and street-level, dark, gritty | e6 | 146 | True crime YouTube videos; Urban documentary segments | -4.1 dB
DT03.mp3 | Hip-hop / Trap / Dark half-time trap instrumental | noir tension, dark, eerie | e4 | 140 | True crime YouTube videos; Urban documentary segments | -4.6 dB
DT04.mp3 | Hip-hop / Trap / Dark half-time trap instrumental | suspenseful, dark, eerie | e7 | 142 | True crime YouTube videos; Urban documentary segments | -4.1 dB
DT05.mp3 | Hip-hop / Trap / Dark half-time trap instrumental | mysterious, eerie, suspenseful | e5 | 150 | True crime YouTube videos; Urban documentary segments | -5.1 dB

## Not for: High-energy hype, urgent news or intense drama
LJ01.mp3 | Lo-fi hip-hop / Lo-fi jazzhop / chillhop | hopeful study-session, hopeful, nostalgic | e3 | 82 | Tech reviews; Vlogs | -5.6 dB
LJ02.mp3 | Lo-fi hip-hop / Lo-fi jazzhop / chillhop | rainy-day mellow, mellow, nostalgic | e4 | 78 | Tech reviews; Vlogs | -8.1 dB
LJ03.mp3 | Lo-fi hip-hop / Lo-fi jazzhop / chillhop | bittersweet, nostalgic, reflective | e4 | 88 | Tech reviews; Vlogs | -6.6 dB
LJ04.mp3 | Lo-fi hip-hop / Lo-fi jazzhop / chillhop | nostalgic, relaxed, warm | e5 | 70 | Tech reviews; Vlogs | -7.6 dB
LJ05.mp3 | Lo-fi hip-hop / Lo-fi jazzhop / chillhop | cozy late-night, cozy, nostalgic | e3 | 72 | Tech reviews; Vlogs | -8.1 dB

## Not for: Urgent, aggressive or comedic content
ND01.mp3 | Synthwave / Nostalgic mid-tempo synthwave / chillwave | hopeful, nostalgic, driving | e5 | 90 | Tech and gadget reviews; Retro gaming documentaries | -11.1 dB
ND02.mp3 | Synthwave / Nostalgic mid-tempo synthwave / chillwave | bittersweet, nostalgic, driving | e4 | 100 | Tech and gadget reviews; Retro gaming documentaries | -9.6 dB
ND03.mp3 | Synthwave / Nostalgic mid-tempo synthwave / chillwave | sunset optimism, nostalgic, optimistic | e5 | 94 | Tech and gadget reviews; Retro gaming documentaries | -10.6 dB
ND04.mp3 | Synthwave / Nostalgic mid-tempo synthwave / chillwave | calm night-drive, nostalgic, driving | e6 | 84 | Tech and gadget reviews; Retro gaming documentaries | -9.1 dB
ND05.mp3 | Synthwave / Nostalgic mid-tempo synthwave / chillwave | nostalgic, atmospheric, reflective | e3 | 86 | Tech and gadget reviews; Retro gaming documentaries | -11.6 dB

## Not for: Serious, sad or calm topics, and long uninterrupted explanations: it is busy and sits close to the voice
WC01.mp3 | Contemporary classical / Unaccompanied solo woodwind caper (rubato, virtuosic) | racing thoughts, anxious, quirky | e5 | free rubato | Comedic panic or chaos; Mad scientist/genius explanations | -1.7 dB | solo
WC02.mp3 | Contemporary classical / Unaccompanied solo woodwind caper (rubato, virtuosic) | sneaky caper, quirky, anxious | e5 | free rubato | Comedic panic or chaos; Mad scientist/genius explanations | -4.6 dB
WC03.mp3 | Contemporary classical / Unaccompanied solo woodwind caper (rubato, virtuosic) | nervous suspense, anxious, tense | e7 | free rubato | Comedic panic or chaos; Mad scientist/genius explanations | 4.4 dB
WC04.mp3 | Contemporary classical / Unaccompanied solo woodwind caper (rubato, virtuosic) | playful mischief, quirky, anxious | e6 | free rubato | Comedic panic or chaos; Mad scientist/genius explanations | 0.0 dB | solo
WC05.mp3 | Contemporary classical / Unaccompanied solo woodwind caper (rubato, virtuosic) | mad-scientist frenzy, anxious, quirky | e4 | free rubato | Comedic panic or chaos; Mad scientist/genius explanations | -1.6 dB | solo
