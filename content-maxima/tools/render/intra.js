// All-keyframe copies of an editable's clips, shared by render.js and audit.js.
//   * a seek on an all-keyframe copy decodes one frame instead of everything since the
//     last keyframe (120 s -> 40 s on a 29 s video with five clips); on the original
//     talking-head clips and their cut-outs the audit's seeks ran past their timeout
//   * copies are cached in materials/<name>/deletable/intra/, keyed by the clip's path,
//     size, mtime, ctime and inode (a clip replaced by mv gets a new copy), so only the
//     first audit or render pays for them
//   * alpha is kept for VP9 cut-outs, and each copy keeps its clip's extension
//     (inspect.js knows a cut-out by its video/webm blob)
//   * a clip not at FPS (Omni 24, HeyGen 25) is motion-interpolated to FPS here: a 24 fps clip
//     seeked at 30 repeats every 4th frame, a judder on the presenter. minterpolate is
//     slow (about 3 output frames a second at 1080x1920), paid once per clip thanks to the cache
// Bump INTRA_VERSION after changing the encoder settings, so old copies are not reused.
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), crypto = require('crypto');

const INTRA_VERSION = '2';
const FPS = 30;

// The clone pad gives the last source frame something to interpolate towards; -t cuts it back.
const interp = fps => `tpad=stop_mode=clone:stop=1,minterpolate=fps=${fps}:mi_mode=mci`;
const rateOf = file => {
  const m = probe(file, 'stream=codec_type,r_frame_rate').match(/codec_type=video\s+r_frame_rate=(\d+)\/(\d+)/);
  return m && +m[2] ? +m[1] / +m[2] : NaN;
};

const run = (cmd, args) => new Promise((res, rej) => {
  const p = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] }); let err = '';
  p.stderr.on('data', d => { err += d; });
  p.on('close', c => c === 0 ? res() : rej(new Error(`${cmd} ${c}: ${err.slice(-400)}`)));
});
const probe = (file, entries) => execFileSync('ffprobe', ['-v', 'error', '-show_entries', entries, '-of', 'default=nw=1', file], { encoding: 'utf8' });

/** { src as written in the html: all-keyframe copy at `fps` } for every clip of `ed` that exists. */
async function intraCopies(dir, ed, fps) {
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
    const key = crypto.createHash('sha1').update([src, size, mtimeMs, ctimeMs, ino, fps, INTRA_VERSION].join('|')).digest('hex').slice(0, 16);
    const copy = path.join(cache, `${key}${ext}`);
    if (fs.existsSync(copy)) { swap[src] = copy; cached++; return; }
    const part = path.join(cache, `${key}.part${ext}`);
    const alpha = /alpha_mode=1/i.test(probe(file, 'stream_tags=alpha_mode'));
    const rate = rateOf(file);
    const convert = Number.isFinite(rate) && Math.abs(rate - fps) > 0.01;
    const secs = convert ? probe(file, 'format=duration').match(/duration=([\d.]+)/)?.[1] : null;
    const trim = secs ? ['-t', secs] : [];
    if (convert) console.log(`  intra: ${src} interpolated ${+rate.toFixed(2)} -> ${fps} fps`);
    const args = alpha
      ? ['-y', '-c:v', 'libvpx-vp9', '-i', file, '-an',
         ...(convert ? ['-filter_complex', `[0:v]format=yuva420p,split[c][a];[c]format=yuv420p,${interp(fps)}[ci];[a]alphaextract,format=yuv420p,${interp(fps)},format=gray[ai];[ci][ai]alphamerge[o]`, '-map', '[o]'] : []),
         ...trim, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-g', '1',
         '-deadline', 'realtime', '-cpu-used', '8', '-row-mt', '1', '-crf', '20', '-b:v', '0', part]
      : ['-y', '-i', file, '-an', ...(convert ? ['-vf', interp(fps)] : []), ...trim,
         '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '1', '-crf', '16', '-pix_fmt', 'yuv420p', part];
    await run('ffmpeg', args);
    fs.renameSync(part, copy);
    swap[src] = copy; encoded++;
  }));
  if (ed.videos.length) console.log(`  intra: ${cached} cached, ${encoded} encoded in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  return swap;
}

// A clip at another rate is interpolated in intraCopies; only an unreadable rate is left unconverted.
function clipFpsWarnings(dir, ed, fps) {
  const warnings = [];
  for (const src of ed.videos) {
    const file = path.join(dir, src);
    if (fs.existsSync(file) && !Number.isFinite(rateOf(file))) warnings.push(`${src} has no readable frame rate; it is not interpolated to ${fps} fps`);
  }
  return warnings;
}

module.exports = { FPS, intraCopies, probe, clipFpsWarnings };
