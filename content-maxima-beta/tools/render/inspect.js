// The in-browser half of audit.js: leaks, text and the sheet frames, on a page opened
// by stage.js's openStage. Runs in the render Lambda (audit.js -> lambda.js), which
// has the browser; the file checks and the sheet tiling stay with audit.js.
const path = require('path');
const { seekTo } = require('./stage');

// Safe zone on the 1080 x 1920 canvas; the icon column narrows it below y 1255.
const ZONE = { left: 70, top: 230, right: 1005, bottom: 1615, stepY: 1255, stepRight: 890 };

/** Every .scene with an id, and the moment it starts (its earliest animation). */
const sceneList = page => page.evaluate(() => [...document.querySelectorAll('#stage .scene[id]')].map(s => {
  const delays = window.__anims.filter(a => a.effect && a.effect.target && s.contains(a.effect.target))
    .map(a => a.effect.getTiming().delay || 0);
  return { id: s.id, start: delays.length ? Math.min(...delays) : 0 };
}));

/**
 * When each text block lands, so it can be measured once it is where it will
 * stay: a phrase at its last word's delay + 500 ms, every other block at its
 * entry's end + 200 ms, or 600 ms into its scene when nothing animates it.
 * Blocks are marked with data-audit-* so any later pass can find them back.
 *
 * `inspect` and `measure` share this, so the problems one reports and the sizes
 * the other reports are about the same elements, measured at the same moments.
 */
async function textTargets(page, scenes, durationMs, portrait) {
  const phrases = await page.evaluate(() => [...new Set([...document.querySelectorAll('#stage .w')].map(w => w.parentElement))]
    .map((p, i) => {
      p.dataset.auditId = i;
      const last = Math.max(...[...p.querySelectorAll('.w, :scope > .w')].map(w => {
        const a = w.getAnimations()[0];
        return a ? (a.effect.getTiming().delay || 0) : 0;
      }));
      return { id: i, t: last + 500 };
    }));
  const blocks = !portrait ? [] : await page.evaluate(() => {
    const hidden = kf => kf && (kf.opacity === '0' || /inset\(\s*100%|inset\([^)]*100%\s*\)/.test(kf.clipPath || '') || /scale\(0\)/.test(kf.transform || ''));
    const ownText = e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const all = [...document.querySelectorAll('#stage *')].filter(e => ownText(e) && !e.closest('#captions') && !e.closest('.w') && !e.querySelector('.w'));
    // the outermost element with text of its own stands for the block
    const tops = all.filter(e => { for (let p = e.parentElement; p && p.id !== 'stage'; p = p.parentElement) if (all.includes(p)) return false; return true; });
    return tops.map((e, i) => {
      e.dataset.auditText = i;
      let end = null;
      for (let p = e; p && p.id !== 'stage'; p = p.parentElement) {
        p.getAnimations().forEach(a => {
          if (!hidden(a.effect.getKeyframes()[0])) return;
          const tm = a.effect.getTiming();
          end = Math.max(end || 0, (tm.delay || 0) + (tm.duration || 0));
        });
      }
      const scene = e.closest('.scene');
      return { id: i, t: end, scene: scene ? scene.id : null };
    });
  });
  const sceneStart = Object.fromEntries(scenes.map(s => [s.id, s.start]));
  const byTime = new Map();
  for (const b of blocks) {
    const t = Math.min(b.t != null ? b.t + 200 : (sceneStart[b.scene] || 0) + 600, durationMs - 100);
    if (!byTime.has(t)) byTime.set(t, { t, scene: b.scene, ids: [] });
    byTime.get(t).ids.push(b.id);
  }
  // Left to right, top to bottom at each moment: measuring must be repeatable,
  // so nothing here may depend on the order the page happened to hand back.
  const rows = [...byTime.values()].sort((a, b) => a.t - b.t).map(r => ({ ...r, ids: r.ids.sort((a, b) => a - b) }));
  return { phrases, rows };
}

/**
 * `at`: null for the whole video, or the ms to look around (0.5 s either side).
 * Frames for the sheet are written to `shotDir` as 000.jpg, 001.jpg, ...
 */
async function inspect(page, { at, durationMs, shotDir }) {
  const inWindow = t => !at || at.some(a => Math.abs(t - a) <= 500);
  const problems = [];
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

  const scenes = await sceneList(page);

  // Leaks.
  const leakTimes = [0, ...scenes.filter(s => s.start >= 400).map(s => s.start - 400)].filter(inWindow);
  for (const t of [...new Set(leakTimes)]) {
    await seekTo(page, t, false);
    const leaks = await page.evaluate(t => {
      const stage = document.getElementById('stage').getBoundingClientRect();
      // Seen at all: opacity along the chain, and no ancestor clipped away or scaled to nothing.
      const seen1 = el => {
        let o = 1;
        for (let e = el; e && e.id !== 'stage'; e = e.parentElement) {
          const cs = getComputedStyle(e);
          o *= parseFloat(cs.opacity);
          if (/inset\(\s*100%|inset\([^)]*100%\s*\)/.test(cs.clipPath) || /^matrix\(0, 0, 0, 0,/.test(cs.transform)) return false;
        }
        return o > 0.05;
      };
      const hidden = kf => kf && (kf.opacity === '0' || /inset\(\s*100%|inset\([^)]*100%\s*\)/.test(kf.clipPath || '') || /scale\(0\)/.test(kf.transform || ''));
      const out = [];
      const seen = new Set();
      window.__anims.forEach(a => {
        const el = a.effect && a.effect.target;
        if (!el || seen.has(el)) return;
        const delay = a.effect.getTiming().delay || 0;
        if (delay <= t + 20 || !hidden(a.effect.getKeyframes()[0])) return;
        seen.add(el);
        const r = el.getBoundingClientRect();
        if (seen1(el) && r.width > 2 && r.height > 2 && r.bottom > stage.top && r.top < stage.bottom && getComputedStyle(el).visibility !== 'hidden') {
          const scene = el.closest('.scene');
          out.push(`${scene ? '#' + scene.id + ' ' : ''}${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : ''} (enters at ${(delay / 1000).toFixed(2)}s)`);
        }
      });
      return out;
    }, t);
    leaks.slice(0, 8).forEach(l => problems.push(`leak @${(t / 1000).toFixed(2)}s: ${l} is already visible (an exit's backwards fill on the same element, rule 10: move the exit to a wrapper)`));
    // A scene that has not started shows nothing, whether or not its content animates in:
    // content with no entry animation at all is visible from t = 0 unless its scene hides it.
    const early = await page.evaluate(({ t, scenes }) => {
      const stage = document.getElementById('stage').getBoundingClientRect();
      const shown = el => {
        let o = 1;
        for (let e = el; e && e.id !== 'stage'; e = e.parentElement) {
          const cs = getComputedStyle(e);
          if (cs.display === 'none' || cs.visibility === 'hidden') return false;
          o *= parseFloat(cs.opacity);
          if (/inset\(\s*100%|inset\([^)]*100%\s*\)|circle\(0/.test(cs.clipPath) || /^matrix\(0, 0, 0, 0,/.test(cs.transform)) return false;
        }
        return o > 0.05;
      };
      const out = [];
      // scenes that begin within the first second are the opening, shown from frame 0 by design
      scenes.filter(s => s.start > Math.max(t + 200, 1000)).forEach(s => {
        const el = document.getElementById(s.id);
        const hit = [...el.querySelectorAll('img, video, svg, canvas, *')].find(e => {
          if (!['IMG', 'VIDEO', 'svg', 'CANVAS'].includes(e.tagName) && ![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return false;
          const r = e.getBoundingClientRect();
          return r.width > 2 && r.height > 2 && r.bottom > stage.top && r.top < stage.bottom && r.right > stage.left && r.left < stage.right && shown(e);
        });
        if (hit) out.push(`#${s.id} (starts ${(s.start / 1000).toFixed(2)}s) already shows ${hit.tagName.toLowerCase()}${hit.className && typeof hit.className === 'string' ? '.' + hit.className.trim().split(/\s+/).join('.') : ''}`);
      });
      return out;
    }, { t, scenes });
    early.forEach(l => problems.push(`leak @${(t / 1000).toFixed(2)}s: ${l} (give the scene container an entry, e.g. opacity 0 until its start, or an entry on that element)`));
  }

  // Text. The safe zone is a 9:16 rule; other ratios get the caption and lonely-word checks only.
  const portrait = await page.evaluate(() => window.STAGE.width === 1080 && window.STAGE.height === 1920);
  const { phrases, rows } = await textTargets(page, scenes, durationMs, portrait);
  for (const ph of phrases.filter(p => inWindow(p.t))) {
    await seekTo(page, ph.t, false);
    const r = await page.evaluate(({ id, Z }) => {
      const p = document.querySelector(`[data-audit-id="${id}"]`);
      let o = 1; for (let e = p; e && e.id !== 'stage'; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity);
      if (o < 0.5) return null;
      const st = document.getElementById('stage').getBoundingClientRect();
      const b = p.getBoundingClientRect();
      const box = { left: b.left - st.left, right: b.right - st.left, top: b.top - st.top, bottom: b.bottom - st.top };
      const lines = [];
      [...new Set([...p.querySelectorAll('.w, :scope > .w')])].forEach(w => {
        const wr = w.getBoundingClientRect(); const cy = (wr.top + wr.bottom) / 2;
        let L = lines.find(l => Math.abs(l.cy - cy) < wr.height * 0.6);
        if (!L) { L = { cy, words: [] }; lines.push(L); }
        L.words.push(w);
      });
      const flags = [];
      const rLim = Z ? (box.bottom > Z.stepY ? Z.stepRight : Z.right) : 0;
      if (Z && box.left < Z.left) flags.push(`left ${Math.round(box.left)}`);
      if (Z && box.right > rLim) flags.push(`right ${Math.round(box.right)} (limit ${rLim})`);
      if (Z && box.top < Z.top) flags.push(`top ${Math.round(box.top)}`);
      if (Z && box.bottom > Z.bottom) flags.push(`bottom ${Math.round(box.bottom)}`);
      if (flags.length && /left|right|top|bottom/.test(flags.join())) flags.push('outside the safe zone: x 70-1005, y 230-1255, then x 70-890 down to y 1615');
      if (lines.length > 2 && p.closest('#captions, .cap, .caption, .captions, #caps')) flags.push(`${lines.length} lines (captions take one or two: split the phrase)`);
      const lonely = lines.filter(l => l.words.length === 1 && !l.words[0].classList.contains('k') && l.words[0].textContent.trim().length <= 9)
        .map(l => l.words[0].textContent.trim());
      if (lonely.length) flags.push(`lonely word: ${lonely.join(' | ')} (rewrap so no short word sits alone on a line; a deliberate one-word key line gets class k)`);
      const text = [...p.querySelectorAll('.w')].map(w => w.textContent.trim()).join(' ').slice(0, 48);
      return flags.length ? `"${text}": ${flags.join(', ')}` : null;
    }, { id: ph.id, Z: portrait ? ZONE : null });
    if (r) problems.push(`text @${(ph.t / 1000).toFixed(2)}s ${r}`);
  }

  // Other text: every text block that is not a .w phrase (headlines, labels, pills, card copy),
  // checked against the safe zone once its entry has finished.
  if (portrait) {
    for (const { t, ids } of rows.filter(r => inWindow(r.t))) {
      await seekTo(page, t, false);
      const out = await page.evaluate(({ ids, Z }) => ids.map(id => {
        const el = document.querySelector(`[data-audit-text="${id}"]`);
        let o = 1;
        for (let e = el; e && e.id !== 'stage'; e = e.parentElement) {
          const cs = getComputedStyle(e);
          if (cs.display === 'none' || cs.visibility === 'hidden') return null;
          o *= parseFloat(cs.opacity);
        }
        if (o < 0.5) return null;
        const st = document.getElementById('stage').getBoundingClientRect();
        const range = document.createRange(); range.selectNodeContents(el);
        const b = range.getBoundingClientRect();
        if (b.width < 2 || b.height < 2) return null;
        const box = { left: b.left - st.left, right: b.right - st.left, top: b.top - st.top, bottom: b.bottom - st.top };
        // off the canvas altogether is a deliberate exit, not a placement
        if (box.right < 0 || box.left > st.width || box.bottom < 0 || box.top > st.height) return null;
        const rLim = box.bottom > Z.stepY ? Z.stepRight : Z.right;
        const flags = [];
        if (box.left < Z.left) flags.push(`left ${Math.round(box.left)}`);
        if (box.right > rLim) flags.push(`right ${Math.round(box.right)} (limit ${rLim})`);
        if (box.top < Z.top) flags.push(`top ${Math.round(box.top)}`);
        if (box.bottom > Z.bottom) flags.push(`bottom ${Math.round(box.bottom)}`);
        return flags.length ? `"${el.textContent.trim().replace(/\s+/g, ' ').slice(0, 48)}": ${flags.join(', ')}, outside the safe zone: x 70-1005, y 230-1255, then x 70-890 down to y 1615 (shrink, rewrap or move it inside)` : null;
      }).filter(Boolean), { ids, Z: ZONE });
      out.forEach(l => problems.push(`text @${(t / 1000).toFixed(2)}s ${l}`));
    }
  }

  // Fonts: a family that failed to load falls back silently; type set only in the
  // system fonts means the video has no type design of its own.
  const fonts = await page.evaluate(() => {
    const faces = [...document.fonts];
    return {
      failed: [...new Set(faces.filter(f => f.status === 'error').map(f => f.family.replace(/"/g, '')))],
      loaded: faces.filter(f => f.status === 'loaded').length,
    };
  });
  fonts.failed.forEach(f => problems.push(`font: ${f} failed to load; copy its file from fonts/ into materials/<name>/fonts/ and point the @font-face src at it`));
  if (!fonts.loaded) problems.push('font: no text uses a font from fonts/; set the headlines, key words and captions in the fonts the style calls for (stage-canvas-html section 3)');

  // Sheet, and on each sheet frame: frame-filling layers that stop just short of the canvas edge.
  const times = at || [0, ...scenes.map(s => s.start + 600), durationMs - 100]
    .filter(t => t >= 0 && t < durationMs).sort((a, b) => a - b);
  const shots = [];
  const slivers = new Set();
  // The harness swaps each clip's src for a blob, so a cut-out is known by the blob's type.
  await page.evaluate(() => Promise.all([...document.querySelectorAll('#stage video')].map(v =>
    fetch(v.currentSrc || v.src).then(r => r.blob()).then(b => { if (b.type === 'video/webm') v.dataset.auditCutout = '1'; }).catch(() => {}))));
  for (const t of [...new Set(times)]) {
    await seekTo(page, t);
    const found = await page.evaluate(() => {
      const st = document.getElementById('stage').getBoundingClientRect();
      const W = st.width, H = st.height;
      const shown = el => {
        let o = 1;
        for (let e = el; e && e.id !== 'stage'; e = e.parentElement) {
          const cs = getComputedStyle(e);
          if (cs.display === 'none' || cs.visibility === 'hidden') return false;
          o *= parseFloat(cs.opacity);
        }
        return o > 0.5;
      };
      // What is painted: an img or video under object-fit contain paints less than its box.
      const painted = el => {
        const r = el.getBoundingClientRect();
        const box = { left: r.left - st.left, top: r.top - st.top, right: r.right - st.left, bottom: r.bottom - st.top };
        const iw = el.videoWidth || el.naturalWidth, ih = el.videoHeight || el.naturalHeight;
        const fit = getComputedStyle(el).objectFit;
        if (iw && ih && (fit === 'contain' || fit === 'scale-down')) {
          const s = Math.min(r.width / iw, r.height / ih), w = iw * s, h = ih * s;
          const cx = (box.left + box.right) / 2, cy = (box.top + box.bottom) / 2;
          return { left: cx - w / 2, right: cx + w / 2, top: cy - h / 2, bottom: cy + h / 2 };
        }
        return box;
      };
      // A cut-out's frame, under object-fit none (intrinsic size, centred) or cover
      // (clipped to its box), mapped through the element's transform.
      const frameRect = el => {
        const r = el.getBoundingClientRect(), fit = getComputedStyle(el).objectFit;
        const sx = r.width / (el.offsetWidth || 1), sy = r.height / (el.offsetHeight || 1);
        const box = { left: r.left - st.left, top: r.top - st.top, right: r.right - st.left, bottom: r.bottom - st.top };
        if (fit !== 'none') return fit === 'cover' || fit === 'fill' ? box : painted(el);
        const cx = (box.left + box.right) / 2, cy = (box.top + box.bottom) / 2;
        const w = el.videoWidth * sx, h = el.videoHeight * sy;
        return { left: Math.max(box.left, cx - w / 2), right: Math.min(box.right, cx + w / 2), top: Math.max(box.top, cy - h / 2), bottom: Math.min(box.bottom, cy + h / 2) };
      };
      // Which sides of the decoded frame the figure touches (opaque along more than 3% of that side).
      const touched = v => {
        const w = v.videoWidth, h = v.videoHeight;
        if (!w || !h) return [];
        const c = document.createElement('canvas'); c.width = w; c.height = h;
        const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(v, 0, 0);
        const share = (x, y, ww, hh) => { const d = g.getImageData(x, y, ww, hh).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 128) n++; return n / (ww * hh); };
        return [['left', share(0, 0, 2, h)], ['right', share(w - 2, 0, 2, h)], ['top', share(0, 0, w, 2)], ['bottom', share(0, h - 2, w, 2)]]
          .filter(([, s]) => s > 0.03).map(([side]) => side);
      };
      const out = [];
      document.querySelectorAll('#stage video').forEach(v => {
        if (!v.dataset.auditCutout || !shown(v)) return;
        const f = frameRect(v);
        if (f.right <= 0 || f.left >= W || f.bottom <= 0 || f.top >= H) return;
        const inside = { left: f.left > 2 && f.left, right: W - f.right > 2 && f.right, top: f.top > 2 && f.top, bottom: H - f.bottom > 2 && f.bottom };
        const cuts = touched(v).filter(side => inside[side] !== false).map(side => `${side} at ${side === 'left' || side === 'right' ? 'x' : 'y'} ${Math.round(inside[side])}`);
        if (cuts.length) {
          const scene = v.closest('.scene');
          out.push(`${scene ? '#' + scene.id + ' ' : ''}cut-out is cropped by its own frame inside the canvas (${cuts.join(', ')}): the figure ends in a straight line there; scale or move it so the cropped side runs past the canvas edge`);
        }
      });
      document.querySelectorAll('#stage img, #stage video, #stage canvas, #stage .scene, #stage .scene > *, #stage .bg').forEach(el => {
        if (!shown(el)) return;
        const cs = getComputedStyle(el);
        const media = ['IMG', 'VIDEO', 'CANVAS'].includes(el.tagName);
        if (!media && cs.backgroundImage === 'none' && (cs.backgroundColor === 'rgba(0, 0, 0, 0)' || cs.backgroundColor === 'transparent')) return;
        if (el.dataset.auditCutout) return; // a cut-out is a figure, not a layer; checked above
        const b = painted(el);
        const gaps = [];
        if (b.bottom - b.top >= 0.6 * H) {
          if (b.left > 0.5 && b.left < 70) gaps.push(`left ${Math.round(b.left)} px`);
          if (W - b.right > 0.5 && W - b.right < 75) gaps.push(`right ${Math.round(W - b.right)} px`);
        }
        if (b.right - b.left >= 0.6 * W) {
          if (b.top > 0.5 && b.top < 96) gaps.push(`top ${Math.round(b.top)} px`);
          if (H - b.bottom > 0.5 && H - b.bottom < 96) gaps.push(`bottom ${Math.round(H - b.bottom)} px`);
        }
        if (gaps.length) {
          const scene = el.closest('.scene');
          const name = `${scene && scene !== el ? '#' + scene.id + ' ' : ''}${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).join('.') : ''}`;
          out.push(`${name} stops short of the canvas edge (${gaps.join(', ')})`);
        }
      });
      return out;
    });
    found.forEach(s => {
      if (slivers.has(s)) return;
      slivers.add(s);
      problems.push(`edge @${(t / 1000).toFixed(2)}s: ${s}${s.includes('cut-out') ? '' : '; a frame-filling layer runs to all four edges (object-fit: cover), or sits clearly inside the safe zone as a card'}`);
    });
    const f = path.join(shotDir, `${String(shots.length).padStart(3, '0')}.jpg`);
    await page.screenshot({ path: f, type: 'jpeg', quality: 80 });
    shots.push({ f, t });
  }
  const stuck = await page.evaluate(() => window.__stuck);
  return { scenes, problems, errors, stuck, portrait, shots };
}

/**
 * What each piece of text measures on the stage: where it sits, how many lines
 * it wrapped to, how wide each line is, and the type size it was set in. For
 * audit.js's --measure, where the point is to see the numbers rather than to be
 * told they are wrong: this returns measurements, never a problem and never a
 * suggested size, because a size that fits one wrapping does not fit the next.
 *
 * Same elements and same moments as `inspect`, so a size here and a `text @t`
 * line there are about the same thing.
 */
async function measure(page, { at, durationMs }) {
  const inWindow = t => !at || at.some(a => Math.abs(t - a) <= 500);
  const { phrases, rows } = await textTargets(page, await sceneList(page), durationMs, true);

  const box = async (sel, attr) => page.evaluate(({ sel, attr, Z }) => {
    const p = document.querySelector(`[data-audit-${attr}="${sel}"]`);
    if (!p) return null;
    let o = 1;
    for (let e = p; e && e.id !== 'stage'; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden') return null;
      o *= parseFloat(cs.opacity);
    }
    if (o < 0.5) return null;
    const st = document.getElementById('stage').getBoundingClientRect();
    // A phrase is measured by its parent's box, any other block by the ink of
    // its text: the same two measures `inspect` judges against the zone.
    const words = [...new Set([...p.querySelectorAll('.w, :scope > .w')])];
    const r = words.length ? p.getBoundingClientRect() : (() => {
      const range = document.createRange(); range.selectNodeContents(p); return range.getBoundingClientRect();
    })();
    const b = { left: r.left - st.left, right: r.right - st.left, top: r.top - st.top, bottom: r.bottom - st.top };
    if (r.width < 2 || r.height < 2) return null;
    if (b.right < 0 || b.left > st.width || b.bottom < 0 || b.top > st.height) return null;
    const lines = [];
    if (words.length) {
      words.forEach(w => {
        const wr = w.getBoundingClientRect(); const cy = (wr.top + wr.bottom) / 2;
        let L = lines.find(l => Math.abs(l.cy - cy) < wr.height * 0.6);
        if (!L) { L = { cy, x0: Infinity, x1: -Infinity, n: 0 }; lines.push(L); }
        L.x0 = Math.min(L.x0, wr.left); L.x1 = Math.max(L.x1, wr.right); L.n++;
      });
      lines.sort((a, b) => a.cy - b.cy);
    }
    const limit = b.bottom > Z.stepY ? Z.stepRight : Z.right;
    const scene = p.closest('.scene');
    const face = words.length ? words[0] : p;
    const cs = getComputedStyle(face);
    return {
      scene: scene ? scene.id : null,
      text: p.textContent.trim().replace(/\s+/g, ' ').slice(0, 48),
      font: cs.fontFamily.split(',')[0].replace(/["']/g, ''),
      size: parseFloat(cs.fontSize),
      // Only a phrase is split into lines by its words; any other block is one
      // run of text, so its wrapping is not known here and is left out.
      lines: lines.length ? lines.map(l => ({ words: l.n, width: Math.round(l.x1 - l.x0) })) : null,
      box: { left: Math.round(b.left), right: Math.round(b.right), top: Math.round(b.top), bottom: Math.round(b.bottom) },
      over: { left: Math.round(Z.left - b.left), right: Math.round(b.right - limit), top: Math.round(Z.top - b.top), bottom: Math.round(b.bottom - Z.bottom) },
    };
  }, { sel, attr, Z: ZONE });

  const out = [];
  for (const ph of phrases.filter(p => inWindow(p.t))) {
    await seekTo(page, ph.t, false);
    const r = await box(ph.id, 'id');
    if (r) out.push({ ...r, t: ph.t, kind: 'phrase' });
  }
  for (const { t, ids } of rows.filter(r => inWindow(r.t))) {
    await seekTo(page, t, false);
    for (const id of ids) {
      const r = await box(id, 'text');
      if (r) out.push({ ...r, t, kind: 'block' });
    }
  }
  out.sort((a, b) => a.t - b.t || (a.scene || '').localeCompare(b.scene || '') || a.box.top - b.box.top || a.box.left - b.box.left);
  return { rows: out, portrait: await page.evaluate(() => window.STAGE.width === 1080 && window.STAGE.height === 1920) };
}

module.exports = { inspect, measure };
