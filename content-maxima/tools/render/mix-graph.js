// The final render and audition stems share these exact normalization, timing and fade filters.
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const OTHER_BED_LUFS = -26;
const PKG = path.join(__dirname, '..', '..');
// sha256 -> package path of every library track, and package path -> its measured gain.
const LIBRARY_MUSIC = new Map(Object.entries(JSON.parse(fs.readFileSync(path.join(PKG, 'resources.json'), 'utf8')).files || {})
  .filter(([k]) => k.startsWith('music/')).map(([k, f]) => [f.sha256, k]));
const LIBRARY_GAIN = new Map(JSON.parse(fs.readFileSync(path.join(PKG, 'music', 'Music metadata.json'), 'utf8'))
  .map(t => [t.path, t.gain_db]));
const libraryPath = file => LIBRARY_MUSIC.get(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'));


function mixGraph(ed, dir, tmp, secs) {
  // Settled before the capture, so a bed without its gain costs a message, not a render.
  // null: generated music, levelled by loudnorm in the mix.
  const bedGainDb = (() => {
    if (!ed.bgmSrc) return null;
    const track = libraryPath(path.join(dir, ed.bgmSrc));
    if (!track) {
      if (ed.bgmGainDb !== null) console.error(`warning: ${ed.bgmSrc} is not a library track; its data-gain-db is ignored`);
      return null;
    }
    const want = LIBRARY_GAIN.get(track);
    const fail = msg => { console.error(`error: ${msg}`); process.exit(1); };
    if (typeof want !== 'number') fail(`${track} has no gain_db in music/Music metadata.json`);
    if (ed.bgmGainDb === null) fail(`#bgm (${track}) has no data-gain-db: copy the gain from the music pick's reply, data-gain-db="${want.toFixed(1)}"`);
    if (!(Math.abs(ed.bgmGainDb - want) <= 0.05)) fail(`#bgm (${track}) has data-gain-db="${ed.bgmGainDb}", but the track's gain is ${want.toFixed(1)}: copy it as it is`);
    return want;
  })();

  // Optional level adjustments (stage-canvas-html section 5), checked before the capture too.
  // Absent, every one is a no-op and the mix is exactly the default one.
  const levels = (() => {
    const fail = msg => { console.error(`error: ${msg}`); process.exit(1); };
    const inRange = (v, lo, hi, what) => {
      if (v === null) return null;
      if (!Number.isFinite(v) || v < lo || v > hi) fail(`${what} must be a number of dB from ${lo} to ${hi}, got "${v}"`);
      return v;
    };
    const vo = inRange(ed.voGainDb, -12, 6, '#vo data-gain-db');
    const bed = inRange(ed.bgmOffsetDb, -20, 6, '#bgm data-gain-offset-db');
    // As low as 1%: a manual edit's sound turned down below 10% stays a cue at its own level.
    ed.sfx.forEach(s => inRange(s.gainDb, -40, 6, `sfx ${s.src} data-gain-db`));
    const duck = (ed.bgmDuck === null ? [] : ed.bgmDuck.split(',')).map(part => {
      const m = part.trim().match(/^(\d+)-(\d+):(-?\d+(?:\.\d+)?)$/);
      if (!m) fail(`#bgm data-duck entries are "startMs-endMs:dB", got "${part.trim()}"`);
      const [s, e, db] = [Number(m[1]), Number(m[2]), Number(m[3])];
      if (!(s < e) || e > ed.durationMs) fail(`#bgm data-duck range ${s}-${e} must be inside 0-${ed.durationMs} ms`);
      if (db < -30 || db > 0) fail(`#bgm data-duck ${s}-${e} must lower by 0 to -30 dB, got ${db}`);
      return { s, e, db };
    }).sort((a, b) => a.s - b.s);
    duck.forEach((d, i) => { if (i && d.s < duck[i - 1].e) fail(`#bgm data-duck ranges ${duck[i - 1].s}-${duck[i - 1].e} and ${d.s}-${d.e} overlap`); });
    if (ed.bgmDuck !== null && !ed.bgmSrc) fail('data-duck is set but there is no #bgm');
    return { vo, bed, duck };
  })();
  const DUCK_RAMP_S = 0.3;
  const dbFilter = db => (db ? `,volume=${db}dB` : '');
  // One frame-evaluated gain per range: 0 dB outside, `db` inside, ramped over DUCK_RAMP_S at both ends.
  // volume evaluates once per frame, and loudnorm flushes its 3 s lookahead as one large frame at the
  // end, so the bed is first cut into 10 ms frames; without it the duck is skipped near the end.
  const duckFilters = levels.duck.length ? ',asetnsamples=n=480:p=0' + levels.duck.map(({ s, e, db }) => {
    const [a, b] = [(s / 1000).toFixed(3), (e / 1000).toFixed(3)];
    return `,volume='pow(10,${db}*clip(min((t-${a})/${DUCK_RAMP_S},(${b}-t)/${DUCK_RAMP_S}),0,1)/20)':eval=frame`;
  }).join('') : '';
  const inputs = [], parts = [], labels = [];
  let idx = 0;
  if (ed.voSrc) {
    inputs.push('-i', path.join(dir, ed.voSrc));
    // A voice an edit levelled before cutting it is not levelled again: a shorter voice levels to another gain.
    const level = ed.voLevelled ? 'aresample=48000' : 'loudnorm=I=-16:TP=-1.5:LRA=7';
    parts.push(`[${idx}:a]${level}${dbFilter(levels.vo)},aformat=channel_layouts=stereo,apad[vo]`); labels.push('[vo]'); idx++;
  }
  ed.sfx.forEach((s, k) => {
    const file = path.join(dir, s.src);
    if (!fs.existsSync(file)) { console.error(`warning: sound effect ${s.src} not found, skipped`); return; }
    const ms = Math.max(0, Math.round(s.at));
    inputs.push('-i', file);
    parts.push(`[${idx}:a]aformat=sample_rates=48000:channel_layouts=stereo${dbFilter(s.gainDb)},adelay=${ms}|${ms}[fx${k}]`); labels.push(`[fx${k}]`); idx++;
  });
  if (ed.bgmSrc) {
    const bed = path.join(tmp, 'bed.wav');
    execFileSync('python3', [path.join(__dirname, '..', 'bgm-extend.py'), path.join(dir, ed.bgmSrc), bed, secs], { stdio: 'inherit' });
    inputs.push('-i', bed);
    const offset = levels.bed ?? 0;
    let level = `aformat=sample_rates=48000:channel_layouts=stereo,volume=${offset ? Math.round((bedGainDb + offset) * 100) / 100 : bedGainDb}dB`;
    if (bedGainDb === null) {
      level = `loudnorm=I=${OTHER_BED_LUFS}:TP=-2:LRA=9,aresample=48000${dbFilter(levels.bed)}`;
      console.log(`  ${ed.bgmSrc} is not a library track: levelled to ${OTHER_BED_LUFS} LUFS`);
    } else {
      console.log(`  ${ed.bgmSrc}: library bed at ${bedGainDb} dB`);
    }
    if (offset) console.log(`  bed offset ${offset} dB`);
    if (levels.duck.length) console.log(`  bed ducked: ${levels.duck.map(d => `${d.s}-${d.e} ms ${d.db} dB`).join(', ')}`);
    parts.push(`[${idx}:a]${level}${duckFilters},afade=t=in:d=1,afade=t=out:st=${(ed.durationMs/1000-1.5).toFixed(2)}:d=1.5[bed]`); labels.push('[bed]'); idx++;
  }

  return { inputs, parts, labels };
}
module.exports = { mixGraph };
