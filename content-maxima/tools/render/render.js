#!/usr/bin/env node
// Frame-by-frame render of a stage editable to H.264 MP4 with VO, sound effects and music.
// Usage: node tools/render/render.js <editable.html> <out.mp4>
//   * always 24 fps, the rate of Seedance clips: a clip at any other rate judders, so a
//     new video model's output rate is checked first (toolkit 3, Frame rate); a clip not
//     at 24 is named in a warning
//   * the capture runs on AWS Lambda in chunks (lambda.js: CM_RENDER_LAMBDA names the
//     function, CM_RENDER_BUCKET the bucket); the segments are concatenated here
//   * frames captured as JPEG q92: PNG encode + transfer was two thirds of the per-frame cost
//   * every <video> is swapped for an all-keyframe copy before capture (intra.js): a
//     seek then decodes one frame instead of everything since the last keyframe. The
//     copies are cached in materials/<name>/deletable/intra/ and shared with audit.js
//   * sound effects are the editable's <audio class="sfx" data-at="ms"> tags, mixed at
//     the level stored in each file: the library is levelled against a -16 LUFS voice,
//     so no gain or loudness normalisation is applied to an effect
//   * a library music bed (its sha256 is in resources.json) gets the fixed gain on its tag,
//     data-gain-db, which places it at -26 LUFS, 10 LU under the voice. The value is the
//     track's gain_db in music/Music metadata.json (measured with ebur128); a library bed
//     without it, or with another value, stops the render before the capture. Any other
//     bed (generated music) is levelled to -26 LUFS by loudnorm.
//   * stage size is read from the page (window.STAGE), so any ratio works
//   * a render already at <out.mp4> is moved to renders/deletable first; the new one
//     is checked (duration, frames, stereo)
// process.exit(0) at the end is needed: the AWS clients keep their sockets open.
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const { readEditable } = require('./stage');
const { renderChunks } = require('./lambda');
const { intraCopies, probe, clipFpsWarnings } = require('./intra');
const crypto = require('crypto');

// Seedance's rate. Switching or adding a video model means checking its output rate against this.
const FPS = 24;

const OTHER_BED_LUFS = -26;
const PKG = path.join(__dirname, '..', '..');
// sha256 -> package path of every library track, and package path -> its measured gain.
const LIBRARY_MUSIC = new Map(Object.entries(JSON.parse(fs.readFileSync(path.join(PKG, 'resources.json'), 'utf8')).files || {})
  .filter(([k]) => k.startsWith('music/')).map(([k, f]) => [f.sha256, k]));
const LIBRARY_GAIN = new Map(JSON.parse(fs.readFileSync(path.join(PKG, 'music', 'Music metadata.json'), 'utf8'))
  .map(t => [t.path, t.gain_db]));
const libraryPath = file => LIBRARY_MUSIC.get(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'));

const [htmlArg, outArg, ...extra] = process.argv.slice(2);
if (!htmlArg || !outArg || extra.length) {
  console.error(`usage: render.js <editable.html> <out.mp4>  (no frame rate argument: the render is always ${FPS} fps)`);
  process.exit(2);
}
const htmlPath = path.resolve(htmlArg), out = path.resolve(outArg);
const dir = path.dirname(htmlPath);            // the editable's folder; everything it references is below it
const rel = path.basename(htmlPath);
const inRoot = path.basename(path.dirname(out)) === 'renders';

const ed = readEditable(htmlPath);
if (!ed.durationMs) throw new Error(`${rel} has no data-duration on #stage`);
const fps = FPS;
console.log(`  frame rate: ${fps} fps`);
clipFpsWarnings(dir, ed, fps).forEach(w => console.error(`warning: ${w}`));

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
  if (ed.bgmGainDb === null) fail(`#bgm (${track}) has no data-gain-db: copy the entry's gain_db, data-gain-db="${want.toFixed(1)}"`);
  if (!(Math.abs(ed.bgmGainDb - want) <= 0.05)) fail(`#bgm (${track}) has data-gain-db="${ed.bgmGainDb}", but the track's gain_db is ${want.toFixed(1)}: copy it as it is`);
  return want;
})();
const frames = Math.round(ed.durationMs / 1000 * fps);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'stage-render-'));
fs.mkdirSync(path.dirname(out), { recursive: true });

function mixAudio(silent, secs) {
  const inputs = ['-i', silent], parts = [], labels = [];
  let idx = 1;
  if (ed.voSrc) {
    inputs.push('-i', path.join(dir, ed.voSrc));
    parts.push(`[${idx}:a]loudnorm=I=-16:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,apad[vo]`); labels.push('[vo]'); idx++;
  }
  ed.sfx.forEach((s, k) => {
    const file = path.join(dir, s.src);
    if (!fs.existsSync(file)) { console.error(`warning: sound effect ${s.src} not found, skipped`); return; }
    const ms = Math.max(0, Math.round(s.at));
    inputs.push('-i', file);
    parts.push(`[${idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${ms}|${ms}[fx${k}]`); labels.push(`[fx${k}]`); idx++;
  });
  if (ed.bgmSrc) {
    const bed = path.join(tmp, 'bed.wav');
    execFileSync('python3', [path.join(__dirname, '..', 'bgm-extend.py'), path.join(dir, ed.bgmSrc), bed, secs], { stdio: 'inherit' });
    inputs.push('-i', bed);
    let level = `aformat=sample_rates=48000:channel_layouts=stereo,volume=${bedGainDb}dB`;
    if (bedGainDb === null) {
      level = `loudnorm=I=${OTHER_BED_LUFS}:TP=-2:LRA=9,aresample=48000`;
      console.log(`  ${ed.bgmSrc} is not a library track: levelled to ${OTHER_BED_LUFS} LUFS`);
    } else {
      console.log(`  ${ed.bgmSrc}: library bed at ${bedGainDb} dB`);
    }
    parts.push(`[${idx}:a]${level},afade=t=in:d=1,afade=t=out:st=${(ed.durationMs/1000-1.5).toFixed(2)}:d=1.5[bed]`); labels.push('[bed]'); idx++;
  }
  const fc = labels.length ? `${parts.join(';')};${labels.join('')}amix=inputs=${labels.length}:normalize=0,atrim=0:${secs}[a]` : '';
  execFileSync('ffmpeg', ['-y','-v','error', ...inputs, ...(fc ? ['-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:a', 'aac', '-b:a', '192k'] : []),
    '-c:v','copy','-t',secs,'-movflags','+faststart', out], { stdio: 'inherit' });
}

function checkRender() {
  const problems = [];
  const fmt = probe(out, 'format=duration');
  const dur = parseFloat((fmt.match(/duration=([\d.]+)/) || [])[1]) * 1000;
  if (Math.abs(dur - ed.durationMs) > 50) problems.push(`duration ${dur.toFixed(0)} ms, expected ${ed.durationMs}`);
  const nb = parseInt((probe(out, 'stream=nb_frames').match(/nb_frames=(\d+)/) || [])[1], 10);
  if (Math.abs(nb - frames) > 1) problems.push(`${nb} frames, expected ${frames}`);
  if ((ed.voSrc || ed.bgmSrc || ed.sfx.length) && !/channels=2/.test(probe(out, 'stream=channels'))) problems.push('audio is not stereo');
  console.log(problems.length ? `  check FAILED: ${problems.join('; ')}` : `  check ok: ${(ed.durationMs/1000).toFixed(2)} s, ${nb} frames, stereo`);
}

// renders/ holds only the current render: the previous one goes to renders/deletable,
// stamped with its own modification time.
function archivePrevious() {
  if (!fs.existsSync(out)) return;
  if (!inRoot) return fs.rmSync(out);
  const d = fs.statSync(out).mtime, p = n => String(n).padStart(2, '0');
  const stamp = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
  const folder = path.join(path.dirname(out), 'deletable');
  fs.mkdirSync(folder, { recursive: true });
  let target = path.join(folder, `${ed.name}_${stamp}.mp4`);
  for (let n = 2; fs.existsSync(target); n++) target = path.join(folder, `${ed.name}_${stamp}_${n}.mp4`);
  fs.renameSync(out, target);
  console.log(`previous render moved to ${path.relative(process.cwd(), target)}`);
}

(async () => {
  archivePrevious();
  const t0 = Date.now();
  const swap = await intraCopies(dir, ed);
  const tPrep = Date.now();
  const segs = await renderChunks({ dir, rel, ed, swap, fps, frames, tmp });
  console.log(`  capture done in ${((Date.now() - tPrep) / 1000).toFixed(0)}s`);
  const tTail = Date.now();

  const listFile = path.join(tmp, 'list.txt');
  fs.writeFileSync(listFile, segs.map(s => `file '${s}'`).join('\n'));
  const silent = path.join(tmp, 'joined.mp4');
  execFileSync('ffmpeg', ['-y','-v','error','-f','concat','-safe','0','-i',listFile,'-c','copy', silent]);
  mixAudio(silent, (ed.durationMs / 1000).toFixed(3));
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`  concat+audio in ${((Date.now()-tTail)/1000).toFixed(0)}s | total ${((Date.now()-t0)/1000).toFixed(0)}s`);

  checkRender();
  console.log('done:', out);
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
