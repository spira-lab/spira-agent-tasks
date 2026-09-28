// Shared plumbing for render.js and audit.js: serve an editable's folder,
// open it at ?render in headless Chrome, and seek it frame by frame.
const { chromium } = require('playwright-core');
const fs = require('fs'), path = require('path'), http = require('http');

const MIME = { html:'text/html', css:'text/css', js:'text/javascript', json:'application/json',
               png:'image/png', jpg:'image/jpeg', jpeg:'image/jpeg', webp:'image/webp', gif:'image/gif', svg:'image/svg+xml', avif:'image/avif',
               mp3:'audio/mpeg', wav:'audio/wav', m4a:'audio/mp4', ogg:'audio/ogg',
               mp4:'video/mp4', webm:'video/webm', mov:'video/quicktime',
               woff:'font/woff', woff2:'font/woff2', ttf:'font/ttf', otf:'font/otf' };

/**
 * Static server rooted at `dir`; nothing outside it is served. `swap` maps a src as
 * written in the html to a local file streamed in its place.
 */
function serve(dir, swap = {}) {
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\//, '');
    const p = swap[rel] || path.join(dir, rel);
    if (!swap[rel] && (!p.startsWith(dir) || !fs.existsSync(p) || fs.statSync(p).isDirectory())) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p).slice(1).toLowerCase()] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

function launch() {
  const o = { args: ['--force-device-scale-factor=1'] };
  if (process.env.CHROME_PATH) o.executablePath = process.env.CHROME_PATH; else o.channel = 'chrome';
  return chromium.launch(o);
}

// Injected once per page: pause every animation, cache the list, expose a cheap
// seek. A <video> is seeked to its own time for the stage time (data-start = stage
// ms at which the clip's time is 0) and resolves once the frame is decoded. A seek
// that has not landed in SEEK_TIMEOUT ms is issued again once, then given up on,
// so one stuck decoder costs a warning instead of hanging the render.
const PREP = `
  (() => {
    const stage = document.getElementById('stage');
    stage.classList.add('is-paused');
    const anims = document.getAnimations();
    anims.forEach(a => { try { a.pause(); } catch (e) {} });
    window.__anims = anims;
    window.__seek = ms => { const a = window.__anims; for (let i = 0; i < a.length; i++) { try { a[i].currentTime = ms; } catch (e) {} } };
    const vids = [...stage.querySelectorAll('video')];
    vids.forEach(v => { v.muted = true; v.pause(); });
    window.__stuck = 0;
    const seekOne = (v, t, tries) => new Promise(res => {
      const done = ok => { clearTimeout(timer); v.removeEventListener('seeked', onSeeked); res(ok); };
      const onSeeked = () => done(true);
      const timer = setTimeout(() => done(false), 3000);
      v.addEventListener('seeked', onSeeked);
      v.currentTime = t;
    }).then(ok => ok || tries <= 0 ? ok : seekOne(v, t, tries - 1));
    window.__seekVideos = ms => Promise.all(vids.map(v => {
      if (!v.readyState || !v.duration) return null;
      const start = parseFloat(v.dataset.start) || 0;
      const t = Math.min(Math.max((ms - start) / 1000, 0), v.duration - 0.001);
      if (Math.abs(v.currentTime - t) < 0.0005 && !v.seeking) return null;
      return seekOne(v, t, 1).then(ok => { if (!ok) window.__stuck++; });
    }));
    return anims.length;
  })()`;

/** Open the editable at ?render, sized to the stage, with fonts, images and videos ready. */
async function openStage(browser, port, rel) {
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(`http://127.0.0.1:${port}/${encodeURIComponent(rel)}?render`, { waitUntil: 'load' });
  const [W, H] = await page.evaluate(() => [window.STAGE.width, window.STAGE.height]);
  await page.setViewportSize({ width: W, height: H });
  const slow = await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
    // the harness swaps each video src for a blob; wait until that blob is decodable
    const late = [];
    await Promise.all([...document.querySelectorAll('#stage video')].map(v => new Promise(r => {
      if (!v.getAttribute('src')) return r();
      const ok = () => v.readyState >= 2 && v.currentSrc.startsWith('blob:');
      if (ok()) return r();
      const iv = setInterval(() => { if (ok()) { clearInterval(iv); r(); } }, 50);
      setTimeout(() => { clearInterval(iv); late.push(v.getAttribute('src')); r(); }, 20000);
    })));
    return late;
  });
  slow.forEach(s => console.error(`warning: ${s} was not decodable after 20 s`));
  const nAnims = await page.evaluate(PREP);
  return { page, W, H, nAnims };
}

/** Put the page on stage time `ms` and wait for two painted frames. */
function seekTo(page, ms) {
  return page.evaluate(ms => { window.__seek(ms); return window.__seekVideos(ms).then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))); }, ms);
}

/** The stage facts a tool needs, read from the editable's html. */
function readEditable(htmlPath) {
  // Comments hold examples (the template's sample sfx tag), never cues.
  const html = fs.readFileSync(htmlPath, 'utf8').replace(/<!--[\s\S]*?-->/g, '');
  const attr = (tag, name) => (tag.match(new RegExp(`\\b${name}="([^"]*)"`)) || [])[1];
  const durationMs = parseInt((html.match(/data-duration="(\d+)"/) || [0, 0])[1], 10);
  const voTag = (html.match(/<audio\b[^>]*\bid="vo"[^>]*>/) || [])[0] || '';
  const bgmTag = (html.match(/<audio\b[^>]*\bid="bgm"[^>]*>/) || [])[0] || '';
  const sfx = [...html.matchAll(/<audio\b[^>]*\bclass="[^"]*\bsfx\b[^"]*"[^>]*>/g)].map(m => ({
    src: attr(m[0], 'src'), at: parseFloat(attr(m[0], 'data-at')) || 0,
  })).filter(s => s.src);
  const videos = [...new Set([...html.matchAll(/<video\b[^>]*\bsrc="([^"]+)"/g)].map(m => m[1]))];
  const name = path.basename(htmlPath).replace(/\.html?$/i, '');
  return {
    html, name, durationMs, videos, sfx,
    voSrc: attr(voTag, 'src'), bgmSrc: attr(bgmTag, 'src'),
    sfxUnder: parseFloat(attr(voTag, 'data-sfx-under')) || 8,
  };
}

module.exports = { serve, launch, openStage, seekTo, readEditable };
