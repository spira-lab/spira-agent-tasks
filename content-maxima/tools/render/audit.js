#!/usr/bin/env node
// Pre-render audit of a stage editable, in the renderer's own ?render view.
// Usage: node tools/render/audit.js <editable.html> [--at ms,ms,...]
//   Without --at: the whole video is checked (run it when every scene is written,
//   and again after the fixes). With --at: a quick look at a stretch you just
//   built. Only those frames are shot, and leaks and text are checked only
//   between the first and last time given (0.5 s either side).
//   * leaks: an element whose entry animation (first keyframe opacity 0 or fully
//     clipped) has not started yet but is visible anyway. Checked on the first frame
//     and 0.4 s before each .scene starts (a scene starts at its earliest animation).
//   * text: every phrase (the parent of .w words) at the moment its last word has
//     landed: safe-zone hits and lines holding a single short non-key word.
//   * files: every materials/ file the html references exists, and none is in
//     deletable/ or jobs/.
//   * sheet: the frames at --at, or by default the first frame, each scene 0.6 s in
//     and the last frame, written to materials/<name>/deletable/audit-sheet.jpg.
// Prints "audit clean" or one line per problem. Fix every line, then run it again.
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const { serve, launch, openStage, seekTo, readEditable } = require('./stage');

const args = process.argv.slice(2);
const atIdx = args.indexOf('--at');
const at = atIdx >= 0 ? args.splice(atIdx, 2)[1].split(',').map(Number) : null;
const lo = at ? Math.min(...at) - 500 : -Infinity, hi = at ? Math.max(...at) + 500 : Infinity;
const inWindow = t => t >= lo && t <= hi;
if (!args[0]) { console.error('usage: audit.js <editable.html> [--at ms,ms,...]'); process.exit(2); }
const htmlPath = path.resolve(args[0]);
const dir = path.dirname(htmlPath), rel = path.basename(htmlPath);
const ed = readEditable(htmlPath);

// Safe zone on the 1080 x 1920 canvas; the icon column narrows it below y 1255.
const ZONE = { left: 70, top: 230, right: 1005, bottom: 1615, stepY: 1255, stepRight: 890 };

(async () => {
  const server = await serve(dir);
  const browser = await launch();
  const { page } = await openStage(browser, server.address().port, rel);
  const problems = [];
  const errors = [];

  // Files.
  for (const ref of [...new Set([...ed.html.matchAll(/(?:src|href)="(materials\/[^"]+)"/g)].map(m => m[1]))]) {
    if (/\/(deletable|jobs)\//.test(ref)) problems.push(`file: ${ref} is in ${ref.includes('/jobs/') ? 'jobs/' : 'deletable/'}; move what the video uses back out`);
    else if (!fs.existsSync(path.join(dir, ref))) problems.push(`file: ${ref} does not exist`);
  }
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
    await seekTo(page, t);
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
  }

  // Text.
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
    await seekTo(page, ph.t);
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
      const rLim = box.bottom > Z.stepY ? Z.stepRight : Z.right;
      if (box.left < Z.left) flags.push(`left ${Math.round(box.left)}`);
      if (box.right > rLim) flags.push(`right ${Math.round(box.right)} (limit ${rLim})`);
      if (box.top < Z.top) flags.push(`top ${Math.round(box.top)}`);
      if (box.bottom > Z.bottom) flags.push(`bottom ${Math.round(box.bottom)}`);
      if (flags.length && /left|right|top|bottom/.test(flags.join())) flags.push('outside the safe zone: x 70-1005, y 230-1255, then x 70-890 down to y 1615');
      if (lines.length > 2 && p.closest('#captions, .cap, .caption, .captions, #caps')) flags.push(`${lines.length} lines (captions take one or two: split the phrase)`);
      const lonely = lines.filter(l => l.words.length === 1 && !l.words[0].classList.contains('k') && l.words[0].textContent.trim().length <= 9)
        .map(l => l.words[0].textContent.trim());
      if (lonely.length) flags.push(`lonely word: ${lonely.join(' | ')} (rewrap so no short word sits alone on a line; a deliberate one-word key line gets class k)`);
      const text = [...p.querySelectorAll('.w')].map(w => w.textContent.trim()).join(' ').slice(0, 48);
      return flags.length ? `"${text}": ${flags.join(', ')}` : null;
    }, { id: ph.id, Z: ZONE });
    if (r) problems.push(`text @${(ph.t / 1000).toFixed(2)}s ${r}`);
  }

  // Sheet.
  const times = at || [0, ...scenes.map(s => s.start + 600), ed.durationMs - 100]
    .filter(t => t >= 0 && t < ed.durationMs).sort((a, b) => a - b);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'stage-audit-'));
  const shots = [];
  for (const t of [...new Set(times)]) {
    await seekTo(page, t);
    const f = path.join(tmp, `${String(shots.length).padStart(3, '0')}.jpg`);
    await page.screenshot({ path: f, type: 'jpeg', quality: 80 });
    shots.push({ f, t });
  }
  const stuck = await page.evaluate(() => window.__stuck);
  await browser.close();
  server.close();

  const deletable = path.join(dir, 'materials', ed.name, 'deletable');
  fs.mkdirSync(deletable, { recursive: true });
  const sheet = path.join(deletable, 'audit-sheet.jpg');
  const cols = Math.min(shots.length, 6), rows = Math.ceil(shots.length / cols);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '1', '-i', path.join(tmp, '%03d.jpg'),
    '-vf', `scale=270:480,tile=${cols}x${rows}`, '-frames:v', '1', sheet]);
  fs.rmSync(tmp, { recursive: true, force: true });

  errors.forEach(e => problems.push(`console: ${e}`));
  if (stuck) problems.push(`${stuck} video seeks timed out`);
  console.log(`scenes: ${scenes.map(s => `${s.id}@${(s.start / 1000).toFixed(2)}s`).join(' ') || 'none (.scene[id] marks one)'}`);
  if (at) console.log(`checked: ${(Math.max(lo, 0) / 1000).toFixed(1)}s to ${(Math.min(hi, ed.durationMs) / 1000).toFixed(1)}s only; run without --at for the whole video`);
  console.log(`sheet: ${sheet} (${shots.map(s => (s.t / 1000).toFixed(1) + 's').join(' ')})`);
  console.log(problems.length ? problems.join('\n') : 'audit clean');
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
