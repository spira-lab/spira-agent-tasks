#!/usr/bin/env node
// Capture a screenshot of a brand's website with headless Chrome, through the shared playwright-core
// (global module). Used only when a clone needs UI screens and the
// request provides none; provided material always wins.
//
// Usage: node capture_site.js <url> <out.png> [--mobile] [--width 1080] [--height 1920]
//                             [--scale 1] [--full-page] [--wait 2500]
//   --mobile     a phone viewport (390 x 844 at scale 3, phone user agent, touch)
//   --width/--height/--scale   the viewport otherwise (default 1440 x 900 at scale 2)
//   --full-page  the whole scrolling page instead of the viewport
//   --wait <ms>  extra time after load for animations and lazy images (default 2500)
// <out.png> may be absolute, relative to the current folder, or relative to the Super Vega folder;
// it must be inside Super Vega/Project/ (only folders inside Project/ are created).
// Chrome: CHROME_PATH if set, else /usr/bin/chromium. Prints one JSON line.
const path = require('path'), fs = require('fs');

const SUPER = path.resolve(__dirname, '..', '..', '..');
const PROJECT = path.join(SUPER, 'Project');
const { chromium } = require('playwright-core');

const argv = process.argv.slice(2);
const flag = n => argv.includes(n);
const opt = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
const pos = argv.filter((a, i) => !a.startsWith('--') && !(i > 0 && ['--width', '--height', '--scale', '--wait'].includes(argv[i - 1])));
const [url, outArg] = pos;
if (!url || !outArg || !/^https?:\/\//.test(url)) {
  console.error('usage: node capture_site.js <https url> <out.png> [--mobile] [--width W] [--height H] [--scale S] [--full-page] [--wait ms]');
  process.exit(2);
}
let out = outArg;
if (!path.isAbsolute(out)) out = /^(Project|Agents)[\/\\]/.test(out) ? path.join(SUPER, out) : path.resolve(out);
out = path.resolve(out);
const inside = (p, root) => { const r = path.relative(root, p); return r && !r.startsWith('..') && !path.isAbsolute(r); };
if (!inside(out, PROJECT)) { console.error(`out must be inside ${PROJECT}, not ${out}`); process.exit(2); }
fs.mkdirSync(path.dirname(out), { recursive: true });

(async () => {
  const launch = { headless: true };
  if (process.env.CHROME_PATH) launch.executablePath = process.env.CHROME_PATH; else launch.executablePath = '/usr/bin/chromium';
  const browser = await chromium.launch(launch);
  try {
    const ctxOpts = flag('--mobile')
      ? { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
          userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1' }
      : { viewport: { width: parseInt(opt('--width', '1440'), 10), height: parseInt(opt('--height', '900'), 10) },
          deviceScaleFactor: parseFloat(opt('--scale', '2')) };
    const ctx = await browser.newContext(ctxOpts);
    const page = await ctx.newPage();
    const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(e => ({ error: e.message }));
    await page.waitForTimeout(parseInt(opt('--wait', '2500'), 10));
    await page.screenshot({ path: out, fullPage: flag('--full-page') });
    const status = resp && typeof resp.status === 'function' ? resp.status() : null;
    console.log(JSON.stringify({ ok: true, url, out, status, title: await page.title(), note: resp && resp.error ? resp.error : undefined }));
  } catch (e) {
    console.log(JSON.stringify({ ok: false, url, error: e.message }));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
