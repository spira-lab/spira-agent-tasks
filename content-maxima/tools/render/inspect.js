// The in-browser half of audit.js: leaks, text and the sheet frames, on a page opened
// by stage.js's openStage. Runs in the render Lambda (audit.js -> lambda.js), which
// has the browser; the file checks and the sheet tiling stay with audit.js.
const path = require('path');
const { seekTo } = require('./stage');

// Safe zone on the 1080 x 1920 canvas; the icon column narrows it below y 1255.
const ZONE = { left: 70, top: 230, right: 1005, bottom: 1615, stepY: 1255, stepRight: 890 };

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

  const scenes = await page.evaluate(() => [...document.querySelectorAll('#stage .scene[id]')].map(s => {
    const delays = window.__anims.filter(a => a.effect && a.effect.target && s.contains(a.effect.target))
      .map(a => a.effect.getTiming().delay || 0);
    return { id: s.id, start: delays.length ? Math.min(...delays) : 0 };
  }));

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
  const phrases = await page.evaluate(() => {
    const parents = [...new Set([...document.querySelectorAll('#stage .w')].map(w => w.parentElement))];
    return parents.map((p, i) => {
      p.dataset.auditId = i;
      const words = [...p.querySelectorAll(':scope > .w, :scope .w')];
      const last = Math.max(...words.map(w => {
        const a = w.getAnimations()[0];
        return a ? (a.effect.getTiming().delay || 0) : 0;
      }));
      return { id: i, t: last + 500 };
    });
  });
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
      p.querySelectorAll('.w').forEach(w => {
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
    const blocks = await page.evaluate(() => {
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
    blocks.forEach(b => {
      const t = Math.min(b.t != null ? b.t + 200 : (sceneStart[b.scene] || 0) + 600, durationMs - 100);
      if (inWindow(t)) byTime.set(t, [...(byTime.get(t) || []), b.id]);
    });
    for (const [t, ids] of [...byTime].sort((a, b) => a[0] - b[0])) {
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
      const out = [];
      document.querySelectorAll('#stage img, #stage video, #stage canvas, #stage .scene, #stage .scene > *, #stage .bg').forEach(el => {
        if (!shown(el)) return;
        const cs = getComputedStyle(el);
        const media = ['IMG', 'VIDEO', 'CANVAS'].includes(el.tagName);
        if (!media && cs.backgroundImage === 'none' && (cs.backgroundColor === 'rgba(0, 0, 0, 0)' || cs.backgroundColor === 'transparent')) return;
        if (el.dataset.auditCutout) return; // a cut-out is a figure, not a layer
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
    found.forEach(s => { if (!slivers.has(s)) { slivers.add(s); problems.push(`edge @${(t / 1000).toFixed(2)}s: ${s}; a frame-filling layer runs to all four edges (object-fit: cover), or sits clearly inside the safe zone as a card`); } });
    const f = path.join(shotDir, `${String(shots.length).padStart(3, '0')}.jpg`);
    await page.screenshot({ path: f, type: 'jpeg', quality: 80 });
    shots.push({ f, t });
  }
  const stuck = await page.evaluate(() => window.__stuck);
  return { scenes, problems, errors, stuck, portrait, shots };
}

module.exports = { inspect };
