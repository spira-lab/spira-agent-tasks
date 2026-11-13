#!/usr/bin/env node
// Parallel frame-by-frame render of a stage editable to H.264 MP4 with VO, sound effects and music.
// Usage: node tools/render/render.js <editable.html> <out.mp4> [fps] [workers]
//   * fps defaults to 24, the rate of Omni clips: a clip at another rate judders
//   * N browsers each render a slice of the timeline; segments are concatenated
//   * frames captured as JPEG (PNG encode + transfer was the per-frame cost)
//   * the animation list is queried once per worker, not once per frame
//   * stage size is read from the page (window.STAGE), so any ratio works
//   * Chrome is found through Playwright's "chrome" channel on any OS;
//     set CHROME_PATH to override
//   * the audio is mixed as in the production package (stage.js readEditable, mix-graph.js,
//     stems.js): sound effects are the <audio class="sfx" data-at="ms"> tags, a library bed
//     needs its track's gain_db as data-gain-db (checked before the capture), generated
//     music is levelled to -26 LUFS; audition stems are written to <out.mp4>.audio/
const { chromium } = require('playwright-core');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os');
const { readEditable } = require('./stage');
const { writeStems, saveStems } = require('./stems');

const args = process.argv.slice(2);
const usePng = args.includes('--png');
const [htmlArg, outArg, fpsArg, workersArg] = args.filter(a => !a.startsWith('--'));
if (!htmlArg || !outArg) { console.error('usage: render.js <editable.html> <out.mp4> [fps] [workers]'); process.exit(2); }
const htmlPath = path.resolve(htmlArg), out = path.resolve(outArg);
const dir = path.dirname(htmlPath);            // the editable's folder; everything it references is below it
const rel = path.basename(htmlPath);
const fps = parseInt(fpsArg || '24', 10);
const WORKERS = parseInt(workersArg || '4', 10);

const ed = readEditable(htmlPath);
const durationMs = ed.durationMs;
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
    window.__seek = ms => { const a = window.__anims; for (let i = 0; i < a.length; i++) { try { a[i].currentTime = ms; } catch (e) {} } };
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
    '-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p', seg], { stdio: ['pipe','inherit','inherit'] });
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

function mixAudio(silent, secs, prepared) {
  const inputs = ['-i', silent], labels = [];
  const parts = [];
  for (const stem of ['vo', 'sfx', 'bgm']) {
    if (!prepared[stem]) continue;
    const index = labels.length + 1;
    inputs.push('-i', prepared[stem]);
    const muted = stem === 'bgm' ? ed.bgmMuted : stem === 'sfx' ? ed.sfxMuted : false;
    const offset = stem === 'bgm' ? ed.bgmOffsetDb ?? 0 : stem === 'sfx' ? ed.sfxOffsetDb ?? 0 : 0;
    parts.push(`[${index}:a]volume=${muted ? '0' : `${offset}dB`}[${stem}]`);
    labels.push(`[${stem}]`);
  }
  const fc = labels.length ? `${parts.join(';')};${labels.join('')}amix=inputs=${labels.length}:normalize=0,atrim=0:${secs}[a]` : '';
  execFileSync('ffmpeg', ['-y','-v','error', ...inputs, ...(fc ? ['-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:a', 'aac', '-b:a', '192k'] : []),
    '-c:v','copy','-t',secs,'-movflags','+faststart', out], { stdio: 'inherit' });
  saveStems(prepared, ed, htmlPath, out);
}

(async () => {
  // Validate and prepare the audio before spending on the frame capture.
  const prepared = writeStems(ed, dir, tmp, (durationMs / 1000).toFixed(3));
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

  mixAudio(silent, (durationMs / 1000).toFixed(3), prepared);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`  concat+audio in ${((Date.now()-tTail)/1000).toFixed(0)}s | total ${((Date.now()-t0)/1000).toFixed(0)}s`);
  console.log('done:', out);
  process.exit(0);   // keep-alive sockets otherwise hold the event loop open
})().catch(e => { console.error(e); process.exit(1); });
