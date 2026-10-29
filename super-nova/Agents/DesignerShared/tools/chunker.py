# SPS chunker for the talking-head clips. The script is never changed; only clip lengths adapt.
# Split at sentence ends, group sentences into chunks, and give each chunk a clip length
# so its syllables per second land in the target band.
#   Gemini Omni (default): 4 / 6 / 8 / 10 s clips
#   Seedance 1.5 Pro (--model seedance, the fallback only): 4 / 8 / 12 s clips
# SPS is counted over the clip's SPEAKING time, not its full length: Omni leaves about 1 s of
# silence in every clip (about 0.6 s before the speech and 0.4 s after; the owner's finding,
# 2026-10-22), so an Omni 6 s clip has 5 s to speak. Seedance has no such pad.
#   target   4.9-5.2 SPS  (natural pace, ends on time, smooth joins)
#   fallback 4.0-5.2 SPS  (only when no grouping lands in the target)
#   ceiling  5.2 SPS      (never exceeded; above this Omni cuts lines off)
# Chunks under 4.0 are allowed only as a last resort and are flagged (silence risk).
#
# Syllables are counted by rules built into this file: no dictionary, no installs,
# plain Python 3. Copy this one file anywhere. Numbers and % are read out as words,
# capital abbreviations are spelled (AI = 2), and compounds split (ChatGPT = chat + G P T).
#   python3 chunker.py <script.txt|script.json> [plan.json] [--model omni|seedance]
# A .json script may add {"syllables": {"word": n}} to override any count.
# Checked against the CMU dictionary: 98% of everyday words exact, scripts within 3%.
import json, re, sys
from functools import lru_cache

TARGET = (4.9, 5.2)
FALLBACK = (4.0, 5.2)
CEILING = 5.2
MODELS = {  # clip length (s) -> listed Spira credits at 1080p (checked against `spira ai models get`, 2026-10-24)
    'omni': {4: 41, 6: 54, 8: 68, 10: 81},                       # gemini-omni-flash-1.1
    'seedance': {4: 35.44, 8: 70.88, 12: 106.32},                # seedance-1.5-pro, sound on (8.86/s)
}
PADS = {'omni': 1.0, 'seedance': 0.0}   # seconds of silence the model leaves in every clip
CLIPS = MODELS['omni']
PAD = PADS['omni']
def speak(d): return d - PAD             # the seconds a clip of length d has for speech
MID = sum(TARGET) / 2

ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'twenty thirty forty fifty sixty seventy eighty ninety'.split()

def number_words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10 - 2] + ('' if n % 10 == 0 else ' ' + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' ' + number_words(n % 100))
    if n < 1000000:
        return number_words(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + number_words(n % 1000))
    return ' '.join(ONES[int(d)] for d in str(n))

def spoken(text):
    """Write numbers and symbols the way they are said."""
    text = re.sub(r'(\d+)\.(\d+)', r'\1 point \2', text)  # 2.5 -> 2 point 5
    text = re.sub(r'(\d+)%', lambda m: m.group(1) + ' percent', text)
    text = re.sub(r'\$(\d+)', lambda m: m.group(1) + ' dollars', text)
    text = text.replace('&', ' and ')
    return re.sub(r'\d+', lambda m: number_words(int(m.group())), text)

def sentences(text):
    # A sentence ends at . ! or ? (optionally followed by a closing quote or bracket) and then a space.
    # So a decimal (2.5) never splits, and a last sentence with no end mark is kept, never dropped.
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|(?<=[.!?]["”’)])\s+', text.strip()) if s.strip()]

def words(s):
    return re.findall(r"[A-Za-z0-9'’]+", spoken(s).replace('-', ' '))

# Words the rules get wrong. Add brand names and odd words here as they come up.
EXCEPTIONS = {
    'nike': 2, 'facebook': 2, 'youtube': 2, 'ok': 2, 'okay': 2, 'hours': 2, 'hour': 2,
    'our': 2, 'fire': 2, 'every': 2, 'everything': 3, 'everyone': 3, 'business': 2,
    'different': 3, 'pipeline': 2, 'files': 1, 'vs': 2, 'creators': 3, 'create': 2,
    'created': 3, 'idea': 3, 'ideas': 3, 'real': 1, 'really': 2, 'area': 3, 'video': 3,
    'videos': 3, 'people': 2, 'little': 2, 'gonna': 2, 'wanna': 2, 'gotta': 2,
    'actually': 4, 'usually': 4, 'intuitive': 4, 'spira': 2, 'maxima': 3,
}
SUB = re.compile(r'cial|tia|cius|cious|giu|ion|iou|sia$|ely$|[^aeiouytd]ed$|[^aeiouylsxzh]es$|[^aeiouy]e$|^ye|ue$')
ADD = re.compile(r'ia|riet|dien|iu|io|ii|[aeiouym]bl$|[aeiou]{3}|^mc|ism$|([^aeiouy])\1l$|[^l]lien|^coa[dglx].|[^gq]ua[^auieo]|dnt$|uity$|ie(r|st)$|[aeiouy]ing$|eo|[^aeiou]y[aeiou]|[cg]es$')

def rule_syllables(word):
    w = re.sub(r'[^a-z]', '', word.lower())
    if not w:
        return 0
    if w in EXCEPTIONS:
        return EXCEPTIONS[w]
    if len(w) <= 3:
        return 1
    n = len([g for g in re.split(r'[^aeiouy]+', w) if g])
    n -= len(SUB.findall(w))
    n += len(ADD.findall(w))
    if re.search(r'[^aeiouyl]le[sd]?$', w):
        n += 1  # bottle, single, angle, garbled: the -le is its own syllable
    return max(1, n)

def syllables(word, overrides):
    w = word.lower().replace('’', "'")
    if w in overrides:
        return overrides[w]
    if word.isupper() and len(word) > 1:  # AI, UGC: said letter by letter
        return sum(3 if c == 'W' else 1 for c in word)
    # CapCut -> Cap + Cut, ChatGPT -> Chat + G P T; capital runs are spelled out.
    # Apostrophes are dropped first so contractions (that's, you're) stay one word.
    parts = re.findall(r'[A-Z]{2,}(?![a-z])|[A-Z]?[a-z]+|[A-Z]', re.sub(r"['’]", '', word))
    if len(parts) > 1:
        return sum(sum(3 if c == 'W' else 1 for c in p) if p.isupper() else rule_syllables(p) for p in parts)
    return rule_syllables(w)

def band(sps):
    if TARGET[0] <= sps <= TARGET[1]:
        return 'target'
    if FALLBACK[0] <= sps <= FALLBACK[1]:
        return 'fallback'
    return 'slow'  # under 4.0; over the ceiling is never chosen

PENALTY = {'target': 0, 'fallback': 1, 'slow': 5}

def plan(text, overrides=None):
    """overrides: optional dict word(lowercase) -> syllables."""
    overrides = {k.lower(): v for k, v in (overrides or {}).items()}
    sents = sentences(text)
    n_syl = [sum(syllables(w, overrides) for w in words(s)) for s in sents]

    def options(total):
        # every clip that keeps the chunk at or under the ceiling
        return [d for d in sorted(CLIPS) if total / speak(d) <= CEILING]

    @lru_cache(None)
    def best(i):
        # score = (band penalties, listed cost, distance from target middle)
        if i == len(sents):
            return ((0, 0.0, 0.0), ())
        out = None
        for j in range(i + 1, len(sents) + 1):
            total = sum(n_syl[i:j])
            opts = options(total)
            if not opts:
                break  # adding more sentences only makes it denser
            rest_score, rest = best(j)
            for d in opts:
                sps = total / speak(d)
                score = (rest_score[0] + PENALTY[band(sps)],
                         rest_score[1] + CLIPS[d],
                         rest_score[2] + abs(sps - MID))
                cand = (score, ((i, j, d),) + rest)
                if out is None or cand[0] < out[0]:
                    out = cand
        if out is None:
            raise SystemExit(f'sentence {i+1} alone is over {CEILING * speak(max(CLIPS)):.0f} syllables; split it')
        return out

    (_, cost, _), chunks = best(0)
    res = []
    for i, j, d in chunks:
        t = ' '.join(sents[i:j]); s = sum(n_syl[i:j]); w = len(words(t))
        res.append({'text': t, 'duration': d, 'speak': speak(d), 'syllables': s, 'sps': round(s / speak(d), 2),
                    'band': band(s / speak(d)), 'words': w, 'wps': round(w / speak(d), 2)})
    return cost, res

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--model' in args:
        i = args.index('--model'); m = args[i + 1].lower(); del args[i:i + 2]
        if m not in MODELS: sys.exit(f'--model must be one of: {", ".join(MODELS)}')
        CLIPS = MODELS[m]; PAD = PADS[m]
    if not args: sys.exit('usage: chunker.py <script.txt|script.json> [plan.json] [--model omni|seedance]')
    sys.argv = [sys.argv[0]] + args
    src = sys.argv[1]
    if src.endswith('.json'):
        cfg = json.load(open(src))
        cost, res = plan(cfg['text'], cfg.get('syllables'))
    else:
        cost, res = plan(open(src).read())
    for k, c in enumerate(res, 1):
        flag = {'target': '', 'fallback': '  [fallback]', 'slow': '  [UNDER 4.0: silence risk]'}[c['band']]
        print(f"chunk {k}: {c['duration']} s (speaks {c['speak']:g} s) | {c['syllables']} syl ({c['sps']}/s){flag} | {c['words']} words ({c['wps']}/s) | {c['text']}")
    print(f'total {sum(c["duration"] for c in res)} s, {cost} credits (listed)')
    if len(sys.argv) > 2:
        json.dump(res, open(sys.argv[2], 'w'), indent=1)
