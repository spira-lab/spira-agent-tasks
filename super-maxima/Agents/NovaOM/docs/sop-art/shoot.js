// Renders 1-4.html to sop-1..4.jpg at the page's own height (no empty space). Run with node.
const { chromium } = require('/Users/jefframirez/Super Nova/Agents/DesignerShared/tools/render/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ channel: 'chrome' });
  const p = await b.newPage({ viewport: { width: 1600, height: 200 }, deviceScaleFactor: 1 });
  for (const n of ['1', '2', '3', '4']) {
    await p.goto('file://' + __dirname + '/' + n + '.html', { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: __dirname + '/sop-' + n + '.jpg', type: 'jpeg', quality: 92, fullPage: true });
  }
  await b.close();
})();
