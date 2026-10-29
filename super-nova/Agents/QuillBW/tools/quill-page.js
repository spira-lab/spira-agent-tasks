// Quill's page reader. Opens a web page in headless Chrome (so JavaScript carousels and
// lazy-loaded images really load), scrolls it, clicks through carousel arrows, and writes
// what it found to <out.json>: the page's visible text, structured product data (JSON-LD,
// Open Graph, Shopify product JSON when the shop has one), and every image URL with where
// it came from. quill-scrape.py runs this; Quill does not run it directly.
//
//   node quill-page.js <url> <out.json>
const path = require('path');
const fs = require('fs');
const SUPER = path.resolve(__dirname, '..', '..', '..');
const { chromium } = (() => { try { return require(path.join(SUPER, 'Agents', 'DesignerShared', 'tools', 'render', 'node_modules', 'playwright-core')); } catch { return require('playwright-core'); } })();
const CHROME = process.env.CHROME_PATH || '/usr/bin/chromium';

const [url, out] = process.argv.slice(2);
if (!url || !out) { console.error('usage: node quill-page.js <url> <out.json>'); process.exit(2); }

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1800 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36' });
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(2500);
    // close obvious cookie / newsletter popups so they do not hide the gallery
    for (const t of ['Accept', 'Accept all', 'I agree', 'Got it', 'Close', 'No thanks']) {
      const b = page.getByRole('button', { name: t, exact: false }).first();
      if (await b.isVisible().catch(() => false)) await b.click({ timeout: 1500 }).catch(() => {});
    }
    // scroll the whole page so lazy images load
    for (let y = 0; y < 12; y++) { await page.mouse.wheel(0, 1200); await page.waitForTimeout(350); }
    await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(500);
    // click through carousels: "next" arrows of galleries/sliders, a few times each
    const nexts = page.locator([
      'button[aria-label*="next" i]', 'button[class*="next" i]', '[class*="swiper-button-next"]',
      '.slick-next', '[class*="arrow--right" i]', '[class*="carousel"] [class*="next" i]',
      '[class*="gallery"] [class*="next" i]', '[class*="slider"] [class*="next" i]'].join(','));
    const n = Math.min(await nexts.count().catch(() => 0), 6);
    for (let i = 0; i < n; i++) {
      const b = nexts.nth(i);
      for (let k = 0; k < 12; k++) {
        if (!(await b.isVisible().catch(() => false))) break;
        await b.click({ timeout: 1200 }).catch(() => {}); await page.waitForTimeout(300);
      }
    }
    // thumbnails often hold the full set: hover/click each once
    const thumbs = page.locator('[class*="thumb" i] img, [class*="thumbnail" i] img');
    const tn = Math.min(await thumbs.count().catch(() => 0), 20);
    for (let i = 0; i < tn; i++) { await thumbs.nth(i).click({ timeout: 800 }).catch(() => {}); await page.waitForTimeout(150); }
    await page.waitForTimeout(800);

    const data = await page.evaluate(() => {
      const abs = u => { try { return new URL(u, location.href).href; } catch { return null; } };
      const fromSrcset = s => (s || '').split(',').map(x => x.trim().split(/\s+/)).filter(p => p[0])
        .map(p => ({ u: abs(p[0]), w: parseInt(p[1]) || 0 })).sort((a, b) => b.w - a.w).map(p => p.u);
      const imgs = [];
      const add = (u, how, el) => {
        if (!u || u.startsWith('data:')) return;
        const ctx = el ? [el.className, el.id, el.alt, el.closest('[class]') && el.closest('[class]').className,
          el.closest('[class*="gallery" i],[class*="carousel" i],[class*="slider" i],[class*="swiper" i],[class*="product" i],[class*="media" i]') ? 'in-gallery' : '']
          .filter(x => typeof x === 'string' && x).join(' ').slice(0, 200) : '';
        imgs.push({ url: u, how, ctx, alt: el && el.alt || '', w: el && el.naturalWidth || 0, h: el && el.naturalHeight || 0 });
      };
      for (const el of document.querySelectorAll('img, source')) {
        for (const a of ['src', 'data-src', 'data-zoom', 'data-zoom-image', 'data-large', 'data-large_image', 'data-original', 'data-image', 'data-full', 'data-master'])
          if (el.getAttribute(a)) add(abs(el.getAttribute(a)), a, el);
        for (const a of ['srcset', 'data-srcset']) fromSrcset(el.getAttribute(a)).slice(0, 1).forEach(u => add(u, a, el));
      }
      for (const a of document.querySelectorAll('a[href]'))
        if (/\.(jpe?g|png|webp)(\?|$)/i.test(a.href)) add(a.href, 'link', a.querySelector('img') || a);
      for (const el of document.querySelectorAll('[style*="background-image"]')) {
        const m = (el.getAttribute('style') || '').match(/url\(["']?([^"')]+)/); if (m) add(abs(m[1]), 'background', el);
      }
      const og = {}; for (const m of document.querySelectorAll('meta[property^="og:"], meta[name^="twitter:"], meta[name="description"]'))
        og[m.getAttribute('property') || m.getAttribute('name')] = m.getAttribute('content');
      if (og['og:image']) add(abs(og['og:image']), 'og:image', null);
      // Structured data, product only: FAQ and review entries (and ratings) are left out.
      const NOT_PRODUCT = /^(FAQPage|Question|Answer|Review|AggregateRating|Rating|BreadcrumbList|WebSite|SiteNavigationElement)$/i;
      const clean = v => {
        if (Array.isArray(v)) return v.map(clean).filter(x => x !== undefined);
        if (!v || typeof v !== 'object') return v;
        const types = [].concat(v['@type'] || []);
        if (types.length && types.every(t => NOT_PRODUCT.test(String(t)))) return undefined;
        const o = {};
        for (const [k, x] of Object.entries(v)) {
          if (/^(review|reviews|aggregateRating|mainEntity)$/i.test(k)) continue;
          const c = clean(x); if (c !== undefined) o[k] = c;
        }
        return o;
      };
      const ld = []; for (const s of document.querySelectorAll('script[type="application/ld+json"]')) { try { const c = clean(JSON.parse(s.textContent)); if (c !== undefined) ld.push(c); } catch {} }
      const logos = [];
      for (const el of document.querySelectorAll('img, svg, a'))
        if (/logo/i.test([el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className, el.id, el.alt, el.getAttribute && el.getAttribute('src'), el.getAttribute && el.getAttribute('aria-label')].join(' '))) {
          if (el.tagName === 'IMG') logos.push({ url: abs(el.currentSrc || el.src), kind: 'img', alt: el.alt });
          else if (el.tagName.toLowerCase() === 'svg') logos.push({ svg: el.outerHTML.slice(0, 200000), kind: 'svg' });
          else { const i = el.querySelector('img'); if (i) logos.push({ url: abs(i.currentSrc || i.src), kind: 'img', alt: i.alt }); }
        }
      // the logo is usually the header's link back to the home page (often an inline SVG)
      for (const a of document.querySelectorAll('header a[href="/"], header a[href="' + location.origin + '/"], a[aria-label*="home" i], [class*="header" i] a[href="/"]')) {
        const svg = a.querySelector('svg'), img = a.querySelector('img');
        if (svg) logos.push({ svg: svg.outerHTML.slice(0, 200000), kind: 'svg' });
        else if (img) logos.push({ url: abs(img.currentSrc || img.src), kind: 'img', alt: img.alt });
      }
      const main = document.querySelector('main, [role="main"], #MainContent, .product, [class*="product" i]') || document.body;
      // The DNA is about the product only. Hide reviews, testimonials, FAQs, the footer and the
      // navigation before reading the text, so none of it reaches page.md. Anything that holds the
      // product title (h1) or the main area itself is never hidden.
      const SKIP = /(^|[\s_-])(faqs?|reviews?|testimonials?|ratings?|footer|nav|navbar|navigation|breadcrumbs?|newsletter|yotpo|jdgm|judgeme|okendo|stamped|loox|trustpilot)([\s_-]|$)/i;
      const HEAD = /^(faqs?|frequently asked( questions)?|questions|reviews?|customer reviews|ratings? (&|and) reviews|testimonials?|what (our )?(customers|people|users|clients|members) (are )?say(ing)?|loved by)\b/i;
      const label = el => [typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '',
                           el.id || '', el.getAttribute('aria-label') || ''].join(' ');
      const keep = el => el === main || el.contains(main) || !!el.querySelector('h1');
      const drop = new Set();
      document.querySelectorAll('footer, nav, [role="contentinfo"], [role="navigation"], [itemtype*="Review" i], [itemtype*="FAQPage" i]').forEach(el => drop.add(el));
      document.querySelectorAll('body *').forEach(el => { if (SKIP.test(label(el))) drop.add(el); });
      document.querySelectorAll('h2, h3, h4').forEach(h => {
        if (!HEAD.test((h.innerText || '').trim())) return;
        const sec = h.closest('section, [class*="section" i], [id*="section" i]');
        drop.add(sec && !keep(sec) ? sec : (h.parentElement || h));
      });
      // link menus (site maps, "Explore" lists): blocks of 5+ links that are almost all link text
      const linky = el => { const as = el.querySelectorAll('a'); if (as.length < 5) return false;
        const all = (el.innerText || '').replace(/\s+/g, '').length; if (!all) return false;
        let inLinks = 0; as.forEach(a => { inLinks += (a.innerText || '').replace(/\s+/g, '').length; });
        return inLinks / all >= 0.85; };
      const menus = [...document.querySelectorAll('body *')].filter(el => !keep(el) && linky(el));
      menus.filter(el => !menus.some(o => o !== el && o.contains(el))).forEach(el => drop.add(el));
      let hidden = 0;
      for (const el of drop) if (!keep(el)) { el.style.setProperty('display', 'none', 'important'); hidden++; }
      return { url: location.href, title: document.title, og, ld, text: (main.innerText || document.body.innerText || '').slice(0, 60000), imgs, logos: logos.slice(0, 12),
               hidden_sections: hidden,
               shopify: !!(window.Shopify || document.querySelector('meta[name="shopify-digital-wallet"]')) };
    });
    if (data.shopify) {   // Shopify keeps the full product gallery in <product>.js
      const js = await page.evaluate(async () => { try { const r = await fetch(location.pathname.replace(/\/$/, '') + '.js'); return r.ok ? await r.json() : null; } catch { return null; } });
      if (js) { data.shopify_product = { title: js.title, description: js.description, vendor: js.vendor, type: js.type, tags: js.tags, variants: (js.variants || []).map(v => v.title) };
                for (const im of js.images || []) data.imgs.push({ url: im.startsWith('//') ? 'https:' + im : im, how: 'shopify-product', ctx: 'in-gallery', alt: js.title, w: 0, h: 0 }); }
    }
    fs.writeFileSync(out, JSON.stringify(data));
    console.log(JSON.stringify({ ok: true, images: data.imgs.length, logos: data.logos.length, text_chars: data.text.length }));
  } catch (e) {
    console.log(JSON.stringify({ ok: false, error: String(e).slice(0, 300) }));
    process.exitCode = 1;
  } finally { await browser.close(); }
})();
