// Renders an SVG logo to a PNG with a transparent background (headless Chrome).
// quill-assets.py runs this for SVG logos; Quill does not run it directly.
//   node quill-svg.js <in.svg> <out.png>
const path = require('path');
const fs = require('fs');
const SUPER = path.resolve(__dirname, '..', '..', '..');
const { chromium } = require(path.join(SUPER, 'Agents', 'DesignerShared', 'tools', 'render', 'node_modules', 'playwright-core'));
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const [inp, out] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const page = await browser.newPage({ deviceScaleFactor: 4 });
  await page.setContent(`<html><body style="margin:0;background:transparent">${fs.readFileSync(inp, 'utf8')}</body></html>`);
  const svg = page.locator('svg').first();
  await svg.evaluate(el => { if (!el.getAttribute('width')) { el.setAttribute('width', el.getBBox().width || 400); el.setAttribute('height', el.getBBox().height || 200); } });
  await svg.screenshot({ path: out, omitBackground: true });
  await browser.close();
  console.log(JSON.stringify({ ok: true, out }));
})().catch(e => { console.log(JSON.stringify({ ok: false, error: String(e).slice(0, 300) })); process.exit(1); });
