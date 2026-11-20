#!/usr/bin/env node
// Parallel frame-by-frame render of a stage editable to H.264 MP4 with VO + music.
// Usage: node tools/render/render.js <editable.html> <out.mp4> [fps] [workers]
//   * N browsers each render a slice of the timeline; segments are concatenated
//   * frames captured as JPEG (PNG encode + transfer was the per-frame cost)
//   * the animation list is queried once per worker, not once per frame
//   * stage size is read from the page (window.STAGE), so any ratio works
//   * Chrome is found through Playwright's "chrome" channel on any OS;
//     set CHROME_PATH to override
const { chromium } = require('playwright-core');
const { spawn, execFileSync } = require('child_process');
// Screenshots arrive as JPEG (full range, BT.601). Convert to limited-range BT.709 and
// tag it in the H.264 bitstream so players and platforms don't guess and wash it out.
// Only the scale filter is used: the render Lambda's ffmpeg has no format filter.
const COLOR_OUT = ['-vf', 'scale=in_range=pc:in_color_matrix=bt601:out_range=tv:out_color_matrix=bt709', '-pix_fmt', 'yuv420p',
  '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
  '-bsf:v', 'h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1'];
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os');

const args = process.argv.slice(2);
const usePng = args.includes('--png');
const [htmlArg, outArg, fpsArg, workersArg] = args.filter(a => !a.startsWith('--'));
if (!htmlArg || !outArg) { console.error('usage: render.js <editable.html> <out.mp4> [fps] [workers]'); process.exit(2); }
const htmlPath = path.resolve(htmlArg), out = path.resolve(outArg);
const dir = path.dirname(htmlPath);            // the editable's folder; everything it references is below it
const rel = path.basename(htmlPath);
const fps = parseInt(fpsArg || '30', 10);
const WORKERS = parseInt(workersArg || '4', 10);

const html = fs.readFileSync(htmlPath, 'utf8');
const durationMs = parseInt((html.match(/data-duration="(\d+)"/) || [0, 0])[1], 10);
const voSrc = (html.match(/<audio id="vo" src="([^"]+)"/) || [])[1];
const bgmSrc = (html.match(/<audio id="bgm" src="([^"]+)"/) || [])[1];
if (!durationMs) throw new Error(`${rel} has no data-duration on #stage`);
const frames = Math.round(durationMs / 1000 * fps);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'stage-render-'));
fs.mkdirSync(path.dirname(out), { recursive: true });

const mime = { html:'text/html', css:'text/css', js:'text/javascript', json:'application/json',
               png:'image/png', jpg:'image/jpeg', jpeg:'image/jpeg', webp:'image/webp', gif:'image/gif', svg:'image/svg+xml', avif:'image/avif',
               mp3:'audio/mpeg', wav:'audio/wav', m4a:'audio/mp4', ogg:'audio/ogg',
               mp4:'video/mp4', webm:'video/webm', mov:'video/quicktime',
               woff:'font/woff', woff2:'font/woff2', ttf:'font/ttf', otf:'font/otf' };
const server = http.createServer((req, res) => {
  const p = path.join(dir, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(dir) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': mime[path.extname(p).slice(1).toLowerCase()] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

// Injected once per page: pause every animation, cache the list, expose a cheap seek.
const PREP = `
  (() => {
    const stage = document.getElementById('stage');
    stage.classList.add('is-paused');
    const anims = document.getAnimations();
    anims.forEach(a => { try { a.pause(); } catch (e) {} });
    window.__anims = anims;
    window.__seek = ms => { if (window.STAGE && typeof window.STAGE.seek === 'function') { try { window.STAGE.seek(ms); } catch (e) {} } const a = window.__anims; for (let i = 0; i < a.length; i++) { try { a[i].currentTime = ms; } catch (e) {} } };
    // <video> elements inside the stage: seek each to its own time for the
    // stage time (data-start = stage ms at which the clip's time is 0) and
    // resolve once the frame is decoded.
    const vids = [...stage.querySelectorAll('video')];
    vids.forEach(v => { v.muted = true; v.pause(); });
    window.__seekVideos = ms => Promise.all(vids.map(v => new Promise(res => {
      if (!v.readyState || !v.duration) return res();
      const start = parseFloat(v.dataset.start) || 0;
      const t = Math.min(Math.max((ms - start) / 1000, 0), v.duration - 0.001);
      if (Math.abs(v.currentTime - t) < 0.0005) return res();
      const done = () => { v.removeEventListener('seeked', done); res(); };
      v.addEventListener('seeked', done);
      v.currentTime = t;
    })));
    return anims.length;
  })()`;

function launchOpts() {
  const o = { args: ['--force-device-scale-factor=1'] };
  if (process.env.CHROME_PATH) o.executablePath = process.env.CHROME_PATH; else o.channel = 'chrome';
  return o;
}

async function runWorker(id, from, to, port) {
  const seg = path.join(tmp, `seg${String(id).padStart(2, '0')}.mp4`);
  const browser = await chromium.launch(launchOpts());
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error(`w${id} page error:`, e.message));
  await page.goto(`http://127.0.0.1:${port}/${encodeURIComponent(rel)}?render`, { waitUntil: 'load' });
  const [W, H] = await page.evaluate(() => [window.STAGE.width, window.STAGE.height]);
  await page.setViewportSize({ width: W, height: H });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
    // the harness swaps each video src for a blob; wait until that blob is decodable
    await Promise.all([...document.querySelectorAll('#stage video')].map(v => new Promise(r => {
      if (!v.getAttribute('src')) return r();
      const ok = () => v.readyState >= 2 && v.currentSrc.startsWith('blob:');
      if (ok()) return r();
      const iv = setInterval(() => { if (ok()) { clearInterval(iv); r(); } }, 50);
      setTimeout(() => { clearInterval(iv); r(); }, 20000);
    })));
  });
  const nAnims = await page.evaluate(PREP);

  const ff = spawn('ffmpeg', ['-y','-v','error','-f','image2pipe','-vcodec', usePng ? 'png' : 'mjpeg', '-framerate',String(fps),'-i','-',
    '-c:v','libx264','-preset','medium','-crf','17',...COLOR_OUT, seg], { stdio: ['pipe','inherit','inherit'] });
  const write = buf => new Promise(r => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', r); else r(); });

  let tSeek = 0, tShot = 0, tPipe = 0;
  const clip = { x: 0, y: 0, width: W, height: H };
  for (let i = from; i < to; i++) {
    const ms = i * 1000 / fps;
    let t0 = Date.now();
    await page.evaluate(ms => { window.__seek(ms); return window.__seekVideos(ms).then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))); }, ms);
    let t1 = Date.now();
    const shot = await page.screenshot(usePng ? { type:'png', clip } : { type:'jpeg', quality:92, clip });
    let t2 = Date.now();
    await write(shot);
    tSeek += t1 - t0; tShot += t2 - t1; tPipe += Date.now() - t2;
    if ((i - from) % 100 === 0) process.stdout.write(`\r  w${id} ${i - from}/${to - from}   `);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error(`w${id} ffmpeg ${c}`))));
  await browser.close();
  const n = to - from;
  console.log(`\n  w${id} done ${n} frames | ${W}x${H} | anims ${nAnims} | seek ${(tSeek/n).toFixed(0)}ms shot ${(tShot/n).toFixed(0)}ms pipe ${(tPipe/n).toFixed(0)}ms`);
  return seg;
}

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  console.log(`rendering ${rel}: ${frames} frames @ ${fps} fps across ${WORKERS} workers${usePng ? ' +png' : ''}`);

  const bounds = [];
  for (let i = 0; i < WORKERS; i++) bounds.push([Math.floor(i * frames / WORKERS), Math.floor((i + 1) * frames / WORKERS)]);
  const t0 = Date.now();
  const segs = await Promise.all(bounds.map(([a, b], i) => runWorker(i, a, b, port)));
  console.log(`  capture done in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  server.closeAllConnections && server.closeAllConnections();
  server.close();
  const tTail = Date.now();

  const listFile = path.join(tmp, 'list.txt');
  fs.writeFileSync(listFile, segs.map(s => `file '${s}'`).join('\n'));
  const silent = path.join(tmp, 'joined.mp4');
  execFileSync('ffmpeg', ['-y','-v','error','-f','concat','-safe','0','-i',listFile,'-c','copy', silent]);

  const secs = (durationMs / 1000).toFixed(3);
  const inputs = ['-i', silent]; const parts = []; let idx = 1;
  if (voSrc) { inputs.push('-i', path.join(dir, voSrc)); parts.push(`[${idx}:a]loudnorm=I=-16:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,apad[vo]`); idx++; }
  if (bgmSrc) {
    const bed = path.join(tmp, 'bed.wav');
    execFileSync('python3', [path.join(__dirname, '..', 'bgm-extend.py'), path.join(dir, bgmSrc), bed, secs], { stdio: 'inherit' });
    inputs.push('-i', bed);
    parts.push(`[${idx}:a]loudnorm=I=-36:TP=-6:LRA=9,afade=t=in:d=1,afade=t=out:st=${(durationMs/1000-1.5).toFixed(2)}:d=1.5[bed]`); idx++;
  }
  const labels = (voSrc ? '[vo]' : '') + (bgmSrc ? '[bed]' : '');
  const n = (voSrc ? 1 : 0) + (bgmSrc ? 1 : 0);
  const fc = parts.join(';') + (n ? `;${labels}amix=inputs=${n}:normalize=0,atrim=0:${secs}[a]` : '');
  execFileSync('ffmpeg', ['-y','-v','error', ...inputs, ...(n ? ['-filter_complex',fc,'-map','0:v','-map','[a]','-c:a','aac','-b:a','192k'] : []),
    '-c:v','copy','-t',secs,'-movflags','+faststart', out], { stdio: 'inherit' });
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`  concat+audio in ${((Date.now()-tTail)/1000).toFixed(0)}s | total ${((Date.now()-t0)/1000).toFixed(0)}s`);
  console.log('done:', out);
  process.exit(0);   // keep-alive sockets otherwise hold the event loop open
})().catch(e => { console.error(e); process.exit(1); });
