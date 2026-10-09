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
//   * the music bed lands at BED_LUFS, 14 LU under the voice. A library bed reaches it
//     through the gain measured for its own track and written to the editable as
//     data-level-db: the files were documented as levelled by ear, and measured they
//     are not (they span 20.7 LU, six of them louder than the voice), so the level is
//     worked out per track rather than trusted. Generated music, which has no measured
//     level, is levelled to BED_LUFS instead.
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

// Where a music bed belongs, 14 LU under the -16 voice. fetch-resource.py targets the
// same value when it works out a track's data-level-db; the two must stay in step.
const BED_LUFS = -30;
const LIBRARY_MUSIC = (() => {
  try {
    const m = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'resources.json'), 'utf8'));
    return new Set(Object.entries(m.files || {}).filter(([k]) => k.startsWith('music/')).map(([, f]) => f.sha256));
  } catch { return new Set(); }
})();
const fromLibrary = file => LIBRARY_MUSIC.has(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'));

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
    let level = 'aformat=sample_rates=48000:channel_layouts=stereo';
    if (!fromLibrary(path.join(dir, ed.bgmSrc))) {
      // No measured level to work from, so normalise the bed itself.
      level = `loudnorm=I=${BED_LUFS}:TP=-2:LRA=9,aresample=48000`;
      console.log(`  ${ed.bgmSrc} is not a library track: levelled to ${BED_LUFS} LUFS`);
    } else if (ed.bgmLevelDb === null) {
      // A library bed with no written gain is the state this change exists to end: the
      // track would play at whatever its file carries, up to 6 LU above the voice. Say
      // so rather than render it silently.
      console.error(`warning: ${ed.bgmSrc} is a library track with no data-level-db, so it will play at its own level; re-fetch it with tools/fetch-resource.py --write-level <editable.html>`);
    } else if (ed.bgmLevelDb) {   // 0 dB is the no-op case, so a falsy check is enough
      level += `,volume=${ed.bgmLevelDb}dB`;
      console.log(`  ${ed.bgmSrc}: ${ed.bgmLevelDb} dB, to reach ${BED_LUFS} LUFS`);
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
