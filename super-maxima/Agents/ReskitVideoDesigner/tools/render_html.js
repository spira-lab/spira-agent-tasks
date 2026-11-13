#!/usr/bin/env node
// Render HTML pages to PNG with headless Chrome through the shared playwright-core
// (Agents/DesignerShared/tools/render/node_modules). Transparent unless the page sets a background.
//
//   node <reskit>/tools/render_html.js <page.html[?query][#hash]> <out.png> [width height scale]
//       Defaults 360 640 3 -> a 1080x1920 PNG (captions, beats, simulated phone screens).
//       Pop-up stickers: 960 240 1. Character sheet: 3840 2160 1. A UI rebuild: the capture's native width at scale 1.
//   node <reskit>/tools/render_html.js --batch <jobs.json>
//       jobs.json: [{"page": "...", "out": "...", "width": 360, "height": 640, "scale": 3}, ...]
//       One browser for all of them (much faster than one call per overlay).
//
// The hash carries the text for the templates in this folder (caption.html, beat.html, popup.html):
// pass it URL-encoded. Relative paths are taken from the current folder.
// Prints one line per PNG: <out> <width>x<height>. Exits 1 if any render failed.
'use strict';
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = (() => { try { return require(path.join(__dirname, '..', '..', 'DesignerShared', 'tools', 'render', 'node_modules', 'playwright-core')); } catch { return require('playwright-core'); } })();

function pageUrl(spec) {
  const m = spec.match(/^([^?#]*)(\?[^#]*)?(#.*)?$/);
  const file = path.resolve(m[1]);
  if (!fs.existsSync(file)) throw new Error(`no page at ${file}`);
  return pathToFileURL(file).href + (m[2] || '') + (m[3] || '');
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return `${b.readUInt32BE(16)}x${b.readUInt32BE(20)}`;
}

async function main() {
  const a = process.argv.slice(2);
  let jobs;
  if (a[0] === '--batch') {
    jobs = JSON.parse(fs.readFileSync(a[1], 'utf8'));
  } else if (a.length >= 2) {
    jobs = [{ page: a[0], out: a[1], width: +(a[2] || 360), height: +(a[3] || 640), scale: +(a[4] || 3) }];
  } else {
    console.error('usage: render_html.js <page.html[#hash]> <out.png> [width height scale] | --batch <jobs.json>');
    process.exit(2);
  }
  const launch = { headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars'] };
  launch.executablePath = process.env.CHROME_PATH || '/usr/bin/chromium';
  const browser = await chromium.launch(launch);
  let failed = 0;
  try {
    for (const j of jobs) {
      const w = +(j.width || 360), h = +(j.height || 640), s = +(j.scale || 3);
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: s });
      const page = await ctx.newPage();
      try {
        await page.goto(pageUrl(j.page), { waitUntil: 'load', timeout: 30000 });
        await page.evaluate(async () => {
          if (document.fonts && document.fonts.ready) await document.fonts.ready;
          await Promise.all([...document.images].map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; })));
        });
        const out = path.resolve(j.out);
        fs.mkdirSync(path.dirname(out), { recursive: true });
        await page.screenshot({ path: out, omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } });
        console.log(`${out} ${pngSize(out)}`);
      } catch (e) {
        failed++;
        console.error(`render failed: ${j.page}: ${e.message}`);
      } finally {
        await ctx.close();
      }
    }
  } finally {
    await browser.close();
  }
  process.exit(failed ? 1 : 0);
}

main().catch(e => { console.error(e.message); process.exit(1); });
