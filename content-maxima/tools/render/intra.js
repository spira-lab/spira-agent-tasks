// All-keyframe copies of an editable's clips, shared by render.js and audit.js.
//   * a seek on an all-keyframe copy decodes one frame instead of everything since the
//     last keyframe (120 s -> 40 s on a 29 s video with five clips); on the original
//     Seedance and Bria clips the audit's seeks ran past their timeout
//   * copies are cached in materials/<name>/deletable/intra/, keyed by the clip's path,
//     size and modification time, so only the first audit or render pays for them
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
    const { size, mtimeMs } = fs.statSync(file);
    const ext = path.extname(src);
    const key = crypto.createHash('sha1').update([src, size, mtimeMs, INTRA_VERSION].join('|')).digest('hex').slice(0, 16);
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

module.exports = { intraCopies, probe };
