#!/usr/bin/env node
// Fast render of a stage editable to a finished MP4, in one command.
// Usage: node render-fast.js <editable.html> <out.mp4> --cover <seconds> [--sfx-gain <dB>] [--workers 4] [--fps 30]
//
// What it does, in order, and why it is fast:
//   1. Moves an existing <out.mp4> to renders/deletable/<name>_<YYYYMMDD-HHMM>.mp4.
//   2. Pre-decodes every <video> clip in the editable once, in order, into still
//      frames (JPEG, or PNG with alpha for transparent clips). Seeking compressed
//      video for every frame was 90% of the old renderer's CPU.
//   3. Headless Chrome draws each frame on the GPU (Metal); the clips show the
//      pre-decoded frame for that moment instead of seeking.
//   4. Frames are encoded on the Mac's media engine (h264_videotoolbox).
//   5. Audio: voice normalised to -16 LUFS, music bed 20 LU under it with fades,
//      and every <audio class="sfx" data-at="<seconds>"> mixed in at its time.
//   6. Embeds the frame at --cover seconds as the MP4's cover image.
//   7. Checks the output and prints one JSON line. Exit code 0 only if it passed.
const { chromium } = require('playwright-core');
const { spawn, execFileSync, execFile } = require('child_process');
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os');

// ---------- arguments ----------
const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : def; };
const positional = argv.filter((a, i) => !a.startsWith('--') && !(i > 0 && argv[i - 1].startsWith('--')));
const [htmlArg, outArg] = positional;
if (!htmlArg || !outArg) { console.error('usage: render-fast.js <editable.html> <out.mp4> --cover <seconds> [--sfx-gain <dB>] [--workers 4] [--fps 30]'); process.exit(2); }
const coverSec = parseFloat(opt('--cover', 'NaN'));
if (!(coverSec > 0)) { console.error('--cover <seconds> is required and must be after 0: the clearest poster frame, never the first frame'); process.exit(2); }
const sfxGain = parseFloat(opt('--sfx-gain', '0'));
const WORKERS = parseInt(opt('--workers', '4'), 10);
const fps = parseInt(opt('--fps', '30'), 10);

const htmlPath = path.resolve(htmlArg), out = path.resolve(outArg);
const dir = path.dirname(htmlPath), rel = path.basename(htmlPath);
const html = fs.readFileSync(htmlPath, 'utf8');
const durationMs = parseInt((html.match(/data-duration="(\d+)"/) || [0, 0])[1], 10);
if (!durationMs) { console.error(`${rel} has no data-duration on #stage`); process.exit(2); }
if (coverSec * 1000 >= durationMs) { console.error(`--cover ${coverSec} is past the end of the video (${durationMs / 1000} s)`); process.exit(2); }
const attr = (tag, name) => (tag.match(new RegExp(`\\s${name}="([^"]*)"`)) || [])[1];
const voSrc = attr((html.match(/<audio[^>]*id="vo"[^>]*>/) || [''])[0], 'src');
const bgmTag = (html.match(/<audio[^>]*id="bgm"[^>]*>/) || [''])[0];
const bgmSrc = attr(bgmTag, 'src');
// How far the music sits under the voice (-16 LUFS), in LU: data-under on the bgm tag, else 20.
const bgmUnder = parseFloat(attr(bgmTag, 'data-under') || '20');
const sfxTags = [...html.matchAll(/<audio[^>]*class="[^"]*\bsfx\b[^"]*"[^>]*>/g)].map(m => m[0])
  .map(t => ({ src: attr(t, 'src'), at: parseFloat(attr(t, 'data-at')), gain: parseFloat(attr(t, 'data-gain') || '0') }))
  .filter(s => s.src && s.at >= 0 && s.at * 1000 < durationMs);
const frames = Math.round(durationMs / 1000 * fps);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'render-fast-'));
const t0 = Date.now();
const run = (cmd, args) => new Promise((res, rej) => execFile(cmd, args, { maxBuffer: 1 << 26 }, (e, so, se) => e ? rej(new Error(se || e.message)) : res(so)));

// ---------- 1. previous render to deletable ----------
fs.mkdirSync(path.dirname(out), { recursive: true });
let movedPrevious = null;
if (fs.existsSync(out)) {
  const m = fs.statSync(out).mtime, p2 = n => String(n).padStart(2, '0');
  const stamp = `${m.getFullYear()}${p2(m.getMonth() + 1)}${p2(m.getDate())}-${p2(m.getHours())}${p2(m.getMinutes())}`;
  const delDir = path.join(path.dirname(out), 'deletable'); fs.mkdirSync(delDir, { recursive: true });
  movedPrevious = path.join(delDir, `${path.basename(out, '.mp4')}_${stamp}.mp4`);
  fs.renameSync(out, movedPrevious);
}

// ---------- 2. pre-decode clips ----------
async function predecode() {
  const stageHtml = html.slice(Math.max(0, html.indexOf('id="stage"')));
  const srcs = [...stageHtml.matchAll(/<video[^>]*\ssrc="([^"]+)"/g)].map(m => m[1]);
  const framesRoot = path.join(tmp, 'frames');
  return Promise.all(srcs.map(async (src, i) => {
    const file = path.join(dir, src);
    if (!fs.existsSync(file)) return { i, count: 0 };
    const probe = JSON.parse(await run('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries',
      'stream=codec_name,pix_fmt,r_frame_rate,height,color_space:stream_tags=alpha_mode', '-of', 'json', file])).streams[0] || {};
    const [a, b] = (probe.r_frame_rate || '30/1').split('/').map(Number); const clipFps = b ? a / b : a;
    // Transparency: the alpha_mode tag in any letter case (ffprobe may print ALPHA_MODE), or a pixel format with alpha.
    const fmtHasAlpha = f => /a/.test((f || '').replace('yuva', 'a').replace(/^yuv/, ''));
    let alpha = Object.entries(probe.tags || {}).some(([k, v]) => k.toLowerCase() === 'alpha_mode' && String(v).trim() === '1') || fmtHasAlpha(probe.pix_fmt);
    // Backup for VP8/VP9: the native decoder reports yuv420p even with alpha; the libvpx decoder reports yuva420p.
    if (!alpha && (probe.codec_name === 'vp9' || probe.codec_name === 'vp8')) {
      try {
        const lib = JSON.parse(await run('ffprobe', ['-v', 'error', '-c:v', probe.codec_name === 'vp9' ? 'libvpx-vp9' : 'libvpx',
          '-select_streams', 'v:0', '-show_entries', 'stream=pix_fmt', '-of', 'json', file])).streams[0] || {};
        alpha = fmtHasAlpha(lib.pix_fmt);
      } catch {}
    }
    const key = `c${i}`; const outDir = path.join(framesRoot, key); fs.mkdirSync(outDir, { recursive: true });
    if (alpha) {
      const dec = probe.codec_name === 'vp9' ? ['-c:v', 'libvpx-vp9'] : probe.codec_name === 'vp8' ? ['-c:v', 'libvpx'] : [];
      await run('ffmpeg', ['-v', 'error', ...dec, '-i', file, '-fps_mode', 'passthrough', '-pix_fmt', 'rgba', '-compression_level', '1', path.join(outDir, 'f%05d.png')]);
    } else {
      const m = /601|170m|470bg/.test(probe.color_space || '') || (probe.height || 0) < 720 ? 'bt601' : 'bt709';
      await run('ffmpeg', ['-v', 'error', '-i', file, '-fps_mode', 'passthrough', '-vf', `scale=in_color_matrix=${m}:in_range=tv:out_color_matrix=bt601:out_range=pc`, '-q:v', '2', path.join(outDir, 'f%05d.jpg')]);
    }
    return { i, key, fps: clipFps, ext: alpha ? '.png' : '.jpg', count: fs.readdirSync(outDir).length };
  }));
}

// ---------- 3. capture ----------
const mime = { html:'text/html', css:'text/css', js:'text/javascript', json:'application/json',
  png:'image/png', jpg:'image/jpeg', jpeg:'image/jpeg', webp:'image/webp', gif:'image/gif', svg:'image/svg+xml', avif:'image/avif',
  mp3:'audio/mpeg', wav:'audio/wav', m4a:'audio/mp4', ogg:'audio/ogg', mp4:'video/mp4', webm:'video/webm', mov:'video/quicktime',
  woff:'font/woff', woff2:'font/woff2', ttf:'font/ttf', otf:'font/otf' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const base = u.startsWith('/__frames/') ? path.join(tmp, 'frames') : dir;
  const p = u.startsWith('/__frames/') ? path.join(base, u.slice(10)) : path.join(dir, u);
  if (!p.startsWith(base) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': mime[path.extname(p).slice(1).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'max-age=3600' });
  fs.createReadStream(p).pipe(res);
});
const PREP = `(() => {
  const stage = document.getElementById('stage'); stage.classList.add('is-paused');
  const anims = document.getAnimations(); anims.forEach(a => { try { a.pause(); } catch (e) {} });
  window.__anims = anims;
  window.__seek = ms => { if (window.STAGE && typeof window.STAGE.seek === 'function') { try { window.STAGE.seek(ms); } catch (e) {} } const a = window.__anims; for (let i = 0; i < a.length; i++) { try { a[i].currentTime = ms; } catch (e) {} } };
  const vids = [...stage.querySelectorAll('video')]; vids.forEach(v => { v.muted = true; v.pause(); });
  // clips without pre-decoded frames fall back to seeking the video itself
  window.__seekVideo = (v, ms) => new Promise(res => {
    if (!v.readyState || !v.duration) return res();
    const t = Math.min(Math.max((ms - (parseFloat(v.dataset.start) || 0)) / 1000, 0), v.duration - 0.001);
    if (Math.abs(v.currentTime - t) < 0.0005) return res();
    const done = () => { v.removeEventListener('seeked', done); res(); }; v.addEventListener('seeked', done); v.currentTime = t;
  });
  window.__vids = vids; return anims.length; })()`;
const INSTALL = meta => {
  const vids = window.__vids;
  vids.forEach((v, i) => { const m = meta[i]; if (!m || !m.count) return; v.__m = m; v.__idx = 0; v.pause(); v.removeAttribute('src'); v.load(); v.preload = 'none'; });
  window.__seekVideos = ms => Promise.all(vids.map(async v => {
    const m = v.__m; if (!m) return window.__seekVideo(v, ms);
    const idx = Math.min(Math.max(Math.floor((ms - (parseFloat(v.dataset.start) || 0)) / 1000 * m.fps) + 1, 1), m.count);
    if (idx === v.__idx) return;
    const url = `/__frames/${m.key}/f${String(idx).padStart(5, '0')}${m.ext}`;
    const img = new Image(); img.src = url; await img.decode(); v.poster = url; v.__idx = idx;
  }));
  return vids.filter(v => v.__m).length;
};
const hwEncoder = (() => { try { return execFileSync('ffmpeg', ['-hide_banner', '-encoders']).toString().includes('h264_videotoolbox'); } catch { return false; } })();
const ENC = hwEncoder ? ['-c:v', 'h264_videotoolbox', '-b:v', '10M', '-profile:v', 'high', '-allow_sw', '0'] : ['-c:v', 'libx264', '-preset', 'medium', '-crf', '17'];

async function worker(id, from, to, port, meta) {
  const seg = path.join(tmp, `seg${String(id).padStart(2, '0')}.mp4`);
  const launch = { args: ['--force-device-scale-factor=1', '--use-angle=metal', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--enable-zero-copy'] };
  if (process.env.CHROME_PATH) launch.executablePath = process.env.CHROME_PATH; else launch.channel = 'chrome';
  const browser = await chromium.launch(launch);
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error(`w${id} page error:`, e.message));
  await page.goto(`http://127.0.0.1:${port}/${encodeURIComponent(rel)}?render`, { waitUntil: 'load' });
  const [W, H] = await page.evaluate(() => [window.STAGE.width, window.STAGE.height]);
  await page.setViewportSize({ width: W, height: H });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
    await Promise.all([...document.querySelectorAll('#stage video')].map(v => new Promise(r => {
      if (!v.getAttribute('src')) return r();
      const ok = () => v.readyState >= 2 && v.currentSrc.startsWith('blob:'); if (ok()) return r();
      const iv = setInterval(() => { if (ok()) { clearInterval(iv); r(); } }, 50); setTimeout(() => { clearInterval(iv); r(); }, 20000);
    })));
  });
  await page.evaluate(PREP);
  await page.evaluate(INSTALL, meta);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', String(fps), '-i', '-', ...ENC, '-pix_fmt', 'yuv420p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  const write = buf => new Promise(r => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', r); else r(); });
  const clip = { x: 0, y: 0, width: W, height: H };
  for (let i = from; i < to; i++) {
    await page.evaluate(ms => { window.__seek(ms); return window.__seekVideos(ms).then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))); }, i * 1000 / fps);
    await write(await page.screenshot({ type: 'jpeg', quality: 92, clip }));
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error(`w${id} ffmpeg ${c}`))));
  await browser.close();
  return seg;
}

(async () => {
  const meta = await predecode();
  const metaByIndex = []; meta.forEach(m => { metaByIndex[m.i] = m; });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const bounds = []; for (let i = 0; i < WORKERS; i++) bounds.push([Math.floor(i * frames / WORKERS), Math.floor((i + 1) * frames / WORKERS)]);
  const segs = await Promise.all(bounds.map(([a, b], i) => worker(i, a, b, port, metaByIndex)));
  server.closeAllConnections && server.closeAllConnections(); server.close();

  // ---------- 4. join, 5. audio ----------
  const listFile = path.join(tmp, 'list.txt'); fs.writeFileSync(listFile, segs.map(s => `file '${s}'`).join('\n'));
  const silent = path.join(tmp, 'joined.mp4');
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', listFile, '-c', 'copy', silent]);
  const secs = (durationMs / 1000).toFixed(3);
  const inputs = ['-i', silent]; const parts = []; const labels = []; let idx = 1;
  if (voSrc && fs.existsSync(path.join(dir, voSrc))) { inputs.push('-i', path.join(dir, voSrc)); parts.push(`[${idx}:a]loudnorm=I=-16:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,apad[vo]`); labels.push('[vo]'); idx++; }
  if (bgmSrc && fs.existsSync(path.join(dir, bgmSrc))) {
    const bed = path.join(tmp, 'bed.wav');
    execFileSync('python3', [path.join(__dirname, '..', 'bgm-extend.py'), path.join(dir, bgmSrc), bed, secs], { stdio: 'ignore' });
    inputs.push('-i', bed);
    // Music is set to -16 minus data-under LUFS (-36 by default) with one plain volume change, never a
    // loudness processor, so its dynamics are never reshaped; a track already there gets at most a small nudge.
    const bedStats = require('child_process').spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', bed, '-af', 'ebur128', '-f', 'null', '-'], { encoding: 'utf8' }).stderr || '';
    const bedI = parseFloat((bedStats.match(/I:\s+(-?[0-9.]+) LUFS/g) || ['I: -36 LUFS']).pop().match(/-?[0-9.]+/)[0]);
    const bedTarget = -16 - bgmUnder;
    const bedGain = Math.abs(bedI - bedTarget) < 0.3 ? 0 : bedTarget - bedI;
    parts.push(`[${idx}:a]volume=${bedGain.toFixed(2)}dB,afade=t=in:d=1,afade=t=out:st=${(durationMs / 1000 - 1.5).toFixed(2)}:d=1.5[bed]`); labels.push('[bed]'); idx++;
  }
  let sfxMixed = 0;
  for (const s of sfxTags) {
    const f = path.join(dir, s.src); if (!fs.existsSync(f)) continue;
    const ms = Math.round(s.at * 1000);
    inputs.push('-i', f);
    parts.push(`[${idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=${(sfxGain + (s.gain || 0)).toFixed(2)}dB,adelay=${ms}|${ms}[s${idx}]`);
    labels.push(`[s${idx}]`); idx++; sfxMixed++;
  }
  const n = labels.length;
  const fc = parts.join(';') + (n ? `;${labels.join('')}amix=inputs=${n}:normalize=0:duration=longest,atrim=0:${secs}[a]` : '');
  const mixed = path.join(tmp, 'mixed.mp4');
  execFileSync('ffmpeg', ['-y', '-v', 'error', ...inputs, ...(n ? ['-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000'] : []),
    '-c:v', 'copy', '-t', secs, '-movflags', '+faststart', mixed]);

  // ---------- 6. cover ----------
  const cover = path.join(tmp, 'cover.png');
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-ss', String(coverSec), '-i', mixed, '-frames:v', '1', cover]);
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', mixed, '-i', cover, '-map', '0', '-map', '1', '-c', 'copy', '-c:v:1', 'png', '-disposition:v:1', 'attached_pic', '-movflags', '+faststart', out]);

  // ---------- 7. check ----------
  const probe = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-count_packets', '-show_entries',
    'format=duration:stream=codec_type,channels,nb_read_packets:stream_disposition=attached_pic', '-of', 'json', out]).toString());
  const vid = probe.streams.find(s => s.codec_type === 'video' && !(s.disposition || {}).attached_pic);
  const aud = probe.streams.find(s => s.codec_type === 'audio');
  const cov = probe.streams.find(s => (s.disposition || {}).attached_pic);
  const gotFrames = vid ? parseInt(vid.nb_read_packets, 10) : 0;
  const gotSecs = parseFloat(probe.format.duration);
  const problems = [];
  if (Math.abs(gotFrames - frames) > 1) problems.push(`frames ${gotFrames}, expected ${frames}`);
  if (Math.abs(gotSecs - durationMs / 1000) > 0.1) problems.push(`duration ${gotSecs}s, expected ${durationMs / 1000}s`);
  if (voSrc && !(aud && aud.channels === 2)) problems.push('no stereo audio');
  if (!cov) problems.push('no cover');
  fs.rmSync(tmp, { recursive: true, force: true });
  const usedClips = meta.filter(m => m.count).length;
  console.log(JSON.stringify({ ok: problems.length === 0, out, seconds: gotSecs, frames: gotFrames, cover_at: coverSec,
    clips_predecoded: `${usedClips}/${meta.length}`, alpha_clips: meta.filter(m => m.count && m.ext === '.png').length, sfx_mixed: sfxMixed, encoder: hwEncoder ? 'hardware' : 'software',
    previous_moved_to: movedPrevious, render_seconds: Math.round((Date.now() - t0) / 1000), problems }));
  process.exit(problems.length ? 1 : 0);   // keep-alive sockets otherwise hold the event loop open
})().catch(e => { console.error(e); fs.rmSync(tmp, { recursive: true, force: true }); process.exit(1); });
