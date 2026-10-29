#!/usr/bin/env node
// Capture a brand's real look from its own website with headless Chrome, through the shared
// playwright-core (Agents/DesignerShared/tools/render/node_modules): screenshots, the logo, the
// colours and the page text, for the truth file and for rebuilding product screens.
//
//   node <reskit>/tools/capture_site.js <url> <out dir> [--pages <url2>,<url3>] [--full] [--hide "<css>"]
//
// For each page it writes, into <out dir>:
//   <slug>-mobile.png      390x844 at scale 3 (1170 px wide), the phone view to rebuild screens from
//   <slug>-desktop.png     1440x900 at scale 1
//   (--full: the whole page height as well, <slug>-mobile-full.png and <slug>-desktop-full.png)
//   <slug>-text.md         the visible text (features, names, prices: sources for truth.md)
//   logo-*.{svg,png,...}   logo candidates: images and inline SVGs whose name, alt or class says logo,
//                          the apple-touch-icon, the icons and og:image
//   colors.json            the most used text and background colours, and the buttons' colours
//   capture.json           what was captured, from which URL, and when
//
// It never clicks anything and never accepts a cookie or consent banner: banners and pop-ups are
// hidden with CSS (common cookie/consent selectors, plus --hide). Read the captures before use; a
// page that needs a sign-in shows only its public face. Prints one line per file.
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(__dirname, '..', '..', 'DesignerShared', 'tools', 'render', 'node_modules', 'playwright-core'));

const HIDE = ['[id*="cookie" i]', '[class*="cookie" i]', '[id*="consent" i]', '[class*="consent" i]', '[id*="onetrust" i]',
  '[class*="onetrust" i]', '[id*="gdpr" i]', '[class*="gdpr" i]', '#CybotCookiebotDialog', '[aria-label*="cookie" i]',
  '[class*="intercom" i]', '[id*="intercom" i]', '[class*="crisp" i]', '[id*="hubspot-messages" i]'];

function opt(a, f, d) { const i = a.indexOf(f); if (i < 0) return d; const v = a[i + 1]; a.splice(i, 2); return v; }
function flag(a, f) { const i = a.indexOf(f); if (i < 0) return false; a.splice(i, 1); return true; }
function slug(u) { const x = new URL(u); return ((x.hostname + x.pathname).replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'page').slice(0, 60).toLowerCase(); }

async function settle(page) {
  try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch (e) { /* busy pages: carry on */ }
  await page.evaluate(async () => {
    // scroll through once so lazy images load, then back to the top
    for (let y = 0; y < document.body.scrollHeight; y += 700) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
    window.scrollTo(0, 0);
    await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 4000); })));
  });
}

async function main() {
  const a = process.argv.slice(2);
  const extra = opt(a, '--pages', ''); const full = flag(a, '--full'); const hide = opt(a, '--hide', '');
  if (a.length < 2) { console.error('usage: capture_site.js <url> <out dir> [--pages u2,u3] [--full] [--hide "<css>"]'); process.exit(2); }
  const urls = [a[0], ...extra.split(',').map(s => s.trim()).filter(Boolean)];
  const out = path.resolve(a[1]); fs.mkdirSync(out, { recursive: true });
  const css = [...HIDE, ...(hide ? [hide] : [])].join(',') + '{display:none!important;visibility:hidden!important}';
  const launch = { headless: true };
  if (process.env.CHROME_PATH) launch.executablePath = process.env.CHROME_PATH; else launch.channel = 'chrome';
  const browser = await chromium.launch(launch);
  const record = { captured: new Date().toISOString(), pages: [], logos: [], colors: null };
  const ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';
  const views = [
    { name: 'mobile', viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, userAgent: ua },
    { name: 'desktop', viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
  ];
  const seenLogo = new Set(); let colorsDone = false;
  try {
    for (const u of urls) {
      const s = slug(u); const pageRec = { url: u, files: [] };
      for (const v of views) {
        const { name, ...ctxOpts } = v;
        const ctx = await browser.newContext(ctxOpts);
        const page = await ctx.newPage();
        try {
          await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
          await page.addStyleTag({ content: css });
          await settle(page);
          const f = path.join(out, `${s}-${name}.png`);
          await page.screenshot({ path: f }); pageRec.files.push(f); console.log(f);
          if (full) { const ff = path.join(out, `${s}-${name}-full.png`); await page.screenshot({ path: ff, fullPage: true }); pageRec.files.push(ff); console.log(ff); }
          if (name === 'mobile') {
            const text = await page.evaluate(() => document.body.innerText);
            const tf = path.join(out, `${s}-text.md`);
            fs.writeFileSync(tf, `# ${u}\n\nCaptured ${record.captured}\n\n${text}\n`); pageRec.files.push(tf); console.log(tf);
          }
          if (name === 'desktop' && !colorsDone) {
            record.colors = await page.evaluate(() => {
              const count = (m, k, w) => { if (!k || k === 'rgba(0, 0, 0, 0)' || k === 'transparent') return; m[k] = (m[k] || 0) + w; };
              const text = {}, bg = {}, buttons = {};
              for (const el of document.querySelectorAll('body *')) {
                const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
                const st = getComputedStyle(el); const area = Math.min(r.width * r.height, 1440 * 900);
                count(bg, st.backgroundColor, area);
                if (el.childNodes.length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) count(text, st.color, 1);
                if (el.matches('button, a[class*="btn" i], a[class*="button" i], [role="button"]')) count(buttons, st.backgroundColor, 1);
              }
              const top = m => Object.entries(m).sort((x, y) => y[1] - x[1]).slice(0, 8).map(e => e[0]);
              return { backgrounds: top(bg), text: top(text), buttons: top(buttons) };
            });
            fs.writeFileSync(path.join(out, 'colors.json'), JSON.stringify(record.colors, null, 1) + '\n');
            console.log(path.join(out, 'colors.json')); colorsDone = true;
          }
          if (name === 'desktop') {
            const cands = await page.evaluate(() => {
              const abs = x => { try { return new URL(x, location.href).href; } catch (e) { return null; } };
              const res = [];
              for (const img of document.querySelectorAll('img')) {
                const hay = `${img.src} ${img.alt} ${img.className} ${img.parentElement && img.parentElement.className}`.toLowerCase();
                if (hay.includes('logo')) res.push({ kind: 'img', url: abs(img.currentSrc || img.src) });
              }
              for (const svg of document.querySelectorAll('svg')) {
                const host = svg.closest('[class*="logo" i], [id*="logo" i], a[href="/"], header a');
                const hay = `${svg.getAttribute('class') || ''} ${svg.getAttribute('aria-label') || ''}`.toLowerCase();
                if (host || hay.includes('logo')) {
                  const c = svg.cloneNode(true); if (!c.getAttribute('xmlns')) c.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                  const r = svg.getBoundingClientRect(); if (r.width < 16) continue;
                  res.push({ kind: 'svg', svg: c.outerHTML });
                }
              }
              for (const l of document.querySelectorAll('link[rel*="icon" i]')) res.push({ kind: 'icon', url: abs(l.href) });
              const og = document.querySelector('meta[property="og:image"]'); if (og) res.push({ kind: 'og', url: abs(og.content) });
              return res.slice(0, 24);
            });
            let k = 0;
            for (const c of cands) {
              k++;
              try {
                if (c.kind === 'svg') {
                  if (seenLogo.has(c.svg)) continue; seenLogo.add(c.svg);
                  const f = path.join(out, `logo-svg-${k}.svg`); fs.writeFileSync(f, c.svg); record.logos.push({ file: f, from: u }); console.log(f);
                } else if (c.url && !seenLogo.has(c.url) && !c.url.startsWith('data:')) {
                  seenLogo.add(c.url);
                  const r = await ctx.request.get(c.url, { timeout: 20000 });
                  if (!r.ok()) continue;
                  const type = (r.headers()['content-type'] || '').split(';')[0];
                  const ext = { 'image/svg+xml': 'svg', 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'image/x-icon': 'ico', 'image/vnd.microsoft.icon': 'ico' }[type] || 'img';
                  const f = path.join(out, `logo-${c.kind}-${k}.${ext}`); fs.writeFileSync(f, await r.body());
                  record.logos.push({ file: f, url: c.url, from: u }); console.log(f);
                }
              } catch (e) { /* a candidate that will not load is skipped */ }
            }
          }
        } catch (e) {
          console.error(`capture failed: ${u} (${name}): ${e.message}`); pageRec.error = e.message;
        } finally {
          await ctx.close();
        }
      }
      record.pages.push(pageRec);
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(out, 'capture.json'), JSON.stringify(record, null, 1) + '\n');
  console.log(path.join(out, 'capture.json'));
  process.exit(record.pages.every(p => p.error) ? 1 : 0);
}

main().catch(e => { console.error(e.message); process.exit(1); });
