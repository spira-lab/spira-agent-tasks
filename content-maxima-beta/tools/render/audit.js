#!/usr/bin/env node
// Pre-render audit of a stage editable, in the renderer's own ?render view.
// Usage: node tools/render/audit.js <editable.html> [--at ms,ms,...] [--measure]
//   Without --at: the whole video is checked (run it when every scene is written,
//   and again after the fixes). With --at: a quick look at what you just built.
//   Only those frames are shot, and leaks and text are checked only within 0.5 s
//   of each time given. Checks never decode video; only the frames shot do, and they
//   seek the same cached all-keyframe copies the render uses (intra.js), so the first
//   audit of a video pays for the copies and later audits and the render reuse them.
//   A "video seeks timed out" line is then a Lambda hiccup: run the audit again, never
//   change the scenes for it.
//   * leaks: an element whose entry animation (first keyframe opacity 0 or fully
//     clipped) has not started yet but is visible anyway. Checked on the first frame
//     and 0.4 s before each .scene starts (a scene starts at its earliest animation).
//   * text: every phrase (the parent of .w words) at the moment its last word has
//     landed: safe-zone hits and lines holding a single short non-key word; every
//     other text block (headlines, labels, card copy) once its entry has finished:
//     safe-zone hits.
//   * edge: on each sheet frame, a frame-filling layer (media or a painted box
//     spanning most of the canvas) that stops just short of an edge.
//   * font: a @font-face that failed to load, or no text in a font from fonts/.
//   * files: every materials/ file the html references (tags and CSS url()) exists,
//     and none is in deletable/ or jobs/.
//   * cut-out: talking-head clips (th-*.mp4) on the stage with no cut-out WebM.
//   * sheet: the frames at --at, or by default the first frame, each scene 0.6 s in
//     and the last frame, written to materials/<name>/deletable/audit-sheet.jpg.
// Prints "audit clean" or one line per problem. Fix every line, then run it again.
// --measure prints measurements instead of problems: every piece of text with its
// size, box, per-line wrap widths and distance outside the safe zone, the same
// elements at the same moments the audit judges, identical run to run.
// The browser half (leaks, text, frames; inspect.js) runs on the render Lambda
// (lambda.js); the file checks and the sheet are done here — except under
// --measure, where the browser is this machine's (stage.js's launch) and the
// Lambda and its S3 client are never loaded, so the run needs no credentials.
const fs = require('fs'), path = require('path'), os = require('os');
const { readEditable, serve, launch, openStage } = require('./stage');

const args = process.argv.slice(2);
const atIdx = args.indexOf('--at');
const at = atIdx >= 0 ? args.splice(atIdx, 2)[1].split(',').map(Number) : null;
const measureIdx = args.indexOf('--measure');
const measuring = measureIdx >= 0;
if (measuring) args.splice(measureIdx, 1);
if (!args[0]) { console.error('usage: audit.js <editable.html> [--at ms,ms,...] [--measure]'); process.exit(2); }
const htmlPath = path.resolve(args[0]);
const dir = path.dirname(htmlPath), rel = path.basename(htmlPath);
const ed = readEditable(htmlPath);

/**
 * Measure the video's text here, not on the Lambda: the browser is in this
 * image too (stage.js's launch), so nothing has to be uploaded, nothing has to
 * cold-start, and a number comes back in seconds. Prints one line per piece of
 * text: where it is, how many lines it wrapped to, how wide each is, and the
 * size it was set in. It never says a size is wrong, and never suggests one —
 * for that, run the audit proper, which judges the same elements.
 */
async function measureHere() {
  const server = await serve(dir);
  const browser = await launch();
  try {
    const { page, W, H } = await openStage(browser, server.address().port, rel);
    const { rows, portrait } = await require('./inspect').measure(page, { at, durationMs: ed.durationMs });
    if (!portrait) console.log(`stage is ${W}x${H}, not 9:16: the safe-zone columns are left out`);
    console.log('scene  at      text                                          size  x, y on the canvas        lines');
    for (const r of rows) {
      const over = Object.entries(r.over).filter(([, d]) => d > 0).map(([side, d]) => `${side} +${d}`);
      const lines = r.lines ? r.lines.map(l => `${l.words}w ${l.width}px`).join(' | ') : '';
      console.log(`${(r.scene || '--').padEnd(6)} ${(r.t / 1000).toFixed(2).padStart(5)}s  "${r.text.padEnd(44)}" ${String(r.size).padStart(3)}px  x ${r.box.left}-${r.box.right}, y ${r.box.top}-${r.box.bottom}${over.length ? `  outside ${over.join(' ')}` : ''}${lines ? `  ${lines}` : ''}`);
    }
    const out = rows.filter(r => Object.values(r.over).some(d => d > 0)).length;
    console.log(`${rows.length} text block${rows.length === 1 ? '' : 's'}${portrait ? `; ${out} outside the safe zone` : ''}. These are the page's own measurements: run the audit to be told what is wrong.`);
    return;
  } finally {
    await browser.close();
    server.closeAllConnections && server.closeAllConnections();
    server.close();
  }
}

if (measuring) measureHere().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
else auditVideo().catch(e => { console.error(e); process.exit(1); });

/** The whole-video audit: file checks here, the browser half on the Lambda. */
async function auditVideo() {
  const { execFileSync } = require('child_process');
  const { auditOnLambda } = require('./lambda');
  const { intraCopies } = require('./intra');
  const problems = [];

  // Files, from tags and from CSS url()s (fonts, background images).
  const refs = [...new Set([...ed.html.matchAll(/(?:src|href)="(materials\/[^"]+)"|url\(\s*['"]?(materials\/[^'")]+)/g)].map(m => m[1] || m[2]))];
  for (const ref of refs) {
    if (/\/(deletable|jobs)\//.test(ref)) problems.push(`file: ${ref} is in ${ref.includes('/jobs/') ? 'jobs/' : 'deletable/'}; move what the video uses back out`);
    else if (!fs.existsSync(path.join(dir, ref))) problems.push(`file: ${ref} does not exist`);
  }

  // A talking head is layered with its cut-out (toolkit 3f): clips on the stage and no WebM means it never is.
  if (refs.some(r => /\/th-[^/]*\.mp4$/.test(r)) && !refs.some(r => /\.webm$/.test(r))) {
    problems.push('cut-out: the talking-head clips are on the stage but none of their cut-outs is; cut every clip out (toolkit 3f) and layer the WebM over the scenes (creative-video-production section 5)');
  }

  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'stage-audit-'));
  const swap = await intraCopies(dir, ed);
  const { scenes, problems: seen, errors, stuck, portrait, shots } = await auditOnLambda({ dir, rel, ed, at, shotDir: tmp, swap });
  problems.push(...seen);

  const deletable = path.join(dir, 'materials', ed.name, 'deletable');
  fs.mkdirSync(deletable, { recursive: true });
  const sheet = path.join(deletable, 'audit-sheet.jpg');
  // A few frames come out large enough to read detail; more are tiled small.
  const big = shots.length <= 4;
  const cols = Math.min(shots.length, big ? 4 : 6), rows = Math.ceil(shots.length / cols);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '1', '-i', path.join(tmp, '%03d.jpg'),
    '-vf', `scale=${big ? '540:960' : '270:480'},tile=${cols}x${rows}`, '-frames:v', '1', sheet]);
  fs.rmSync(tmp, { recursive: true, force: true });

  errors.forEach(e => problems.push(`console: ${e}`));
  if (stuck) problems.push(`${stuck} video seeks timed out`);
  console.log(`scenes: ${scenes.map(s => `${s.id}@${(s.start / 1000).toFixed(2)}s`).join(' ') || 'none (.scene[id] marks one)'}`);
  if (!portrait) console.log('stage is not 9:16: safe-zone checks skipped; keep key elements clear of the edges by eye');
  if (at) console.log(`checked: within 0.5 s of ${at.map(a => (a / 1000).toFixed(1) + 's').join(', ')} only; run without --at for the whole video`);
  console.log(`sheet: ${sheet} (${shots.map(s => (s.t / 1000).toFixed(1) + 's').join(' ')})`);
  console.log(problems.length ? problems.join('\n') : 'audit clean');
  process.exit(0);
}
