// All-keyframe copies of an editable's clips, shared by render.js and audit.js.
//   * a seek on an all-keyframe copy decodes one frame instead of everything since the
//     last keyframe (120 s -> 40 s on a 29 s video with five clips); on the original
//     Seedance and Bria clips the audit's seeks ran past their timeout
//   * copies are cached in materials/<name>/deletable/intra/, keyed by the clip's path,
//     size, mtime, ctime and inode (a clip replaced by mv gets a new copy), so only the
//     first audit or render pays for them
//   * alpha is kept for VP9 cut-outs, and each copy keeps its clip's extension
//     (inspect.js knows a cut-out by its video/webm blob)
// Bump INTRA_VERSION after changing the encoder settings, so old copies are not reused.
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), crypto = require('crypto');

const INTRA_VERSION = '1';

const run = (cmd, args) => new Promise((res, rej) => {
  const p = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] }); let err = '';
  p.stderr.on('data', d => { err += d; });
  p.on('close', c => c === 0 ? res() : rej(new Error(`${cmd} ${c}: ${err.slice(-400)}`)));
});
const probe = (file, entries) => execFileSync('ffprobe', ['-v', 'error', '-show_entries', entries, '-of', 'default=nw=1', file], { encoding: 'utf8' });

/** { src as written in the html: all-keyframe copy } for every clip of `ed` that exists. */
async function intraCopies(dir, ed) {
  const t0 = Date.now();
  const cache = path.join(dir, 'materials', ed.name, 'deletable', 'intra');
  fs.mkdirSync(cache, { recursive: true });
  const swap = {};
  let cached = 0, encoded = 0;
  await Promise.all(ed.videos.map(async src => {
    const file = path.join(dir, src);
    if (!fs.existsSync(file)) { console.error(`warning: ${src} not found`); return; }
    const { size, mtimeMs, ctimeMs, ino } = fs.statSync(file);
    const ext = path.extname(src);
    const key = crypto.createHash('sha1').update([src, size, mtimeMs, ctimeMs, ino, INTRA_VERSION].join('|')).digest('hex').slice(0, 16);
    const copy = path.join(cache, `${key}${ext}`);
    if (fs.existsSync(copy)) { swap[src] = copy; cached++; return; }
    const part = path.join(cache, `${key}.part${ext}`);
    const alpha = /alpha_mode=1/i.test(probe(file, 'stream_tags=alpha_mode'));
    const args = alpha
      ? ['-y', '-c:v', 'libvpx-vp9', '-i', file, '-an', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-g', '1',
         '-deadline', 'realtime', '-cpu-used', '8', '-row-mt', '1', '-crf', '20', '-b:v', '0', part]
      : ['-y', '-i', file, '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '1', '-crf', '16', '-pix_fmt', 'yuv420p', part];
    await run('ffmpeg', args);
    fs.renameSync(part, copy);
    swap[src] = copy; encoded++;
  }));
  if (ed.videos.length) console.log(`  intra: ${cached} cached, ${encoded} encoded in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  return swap;
}

/**
 * The render frame rate: the clips' own, so each output frame is one clip frame
 * (Seedance is 24 fps; sampling it at 30 repeats every fourth frame, a visible
 * judder). Rates above 30 are halved while even (60 -> 30), clips that disagree
 * are settled by the most stage time, and a stage with no clips renders at 30.
 */
function clipFps(dir, ed) {
  const byRate = new Map(), warnings = [];
  for (const src of ed.videos) {
    const file = path.join(dir, src);
    if (!fs.existsSync(file)) continue;
    const out = probe(file, 'stream=codec_type,r_frame_rate:format=duration');
    const m = out.match(/codec_type=video\s+r_frame_rate=(\d+)\/(\d+)/);
    const raw = m && +m[2] ? +m[1] / +m[2] : NaN;
    if (!(raw >= 10 && raw <= 120)) { warnings.push(`${src} has no usable frame rate (${m ? `${m[1]}/${m[2]}` : 'none'}), ignored`); continue; }
    let rate = Math.round(raw);
    while (rate > 30 && rate % 2 === 0) rate /= 2;
    const secs = parseFloat((out.match(/duration=([\d.]+)/) || [])[1]) || 0;
    const e = byRate.get(rate) || { secs: 0, clips: [] };
    e.secs += secs; e.clips.push(path.basename(src));
    byRate.set(rate, e);
  }
  if (!byRate.size) return { fps: 30, note: '30 fps (no clips on the stage)', warnings };
  const ranked = [...byRate].sort((a, b) => b[1].secs - a[1].secs);
  const [fps, top] = ranked[0];
  if (ranked.length > 1) warnings.push(`clips disagree on frame rate (${ranked.map(([r, e]) => `${r} fps: ${e.clips.join(', ')}`).join('; ')}); rendering at ${fps}, the rate with the most stage time`);
  return { fps, note: `${fps} fps from ${top.clips.join(', ')}`, warnings };
}

module.exports = { intraCopies, probe, clipFps };
