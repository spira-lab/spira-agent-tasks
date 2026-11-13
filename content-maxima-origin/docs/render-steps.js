#!/usr/bin/env node
// Screenshot every card in docs/steps.html to docs/<card id>.png at 1920x1080.
// Usage: node docs/render-steps.js   (run from the package folder; needs tools/render's npm install)
const path = require('path');
const { chromium } = require(path.join(__dirname, '..', 'tools', 'render', 'node_modules', 'playwright-core'));
(async () => {
  const opts = { args: ['--force-device-scale-factor=1'] };
  if (process.env.CHROME_PATH) opts.executablePath = process.env.CHROME_PATH; else opts.channel = 'chrome';
  const browser = await chromium.launch(opts);
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'steps.html'), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const ids = await page.$$eval('section.step', els => els.map(e => e.id));
  for (const id of ids) {
    const el = await page.$('#' + id);
    await el.screenshot({ path: path.join(__dirname, `${id}.png`), type: 'png' });
    console.log(`${id}.png`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
