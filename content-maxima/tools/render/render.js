#!/usr/bin/env node
// Parallel frame-by-frame render of a stage editable to H.264 MP4 with VO, sound effects and music.
// Usage: node tools/render/render.js <editable.html> <out.mp4> [fps] [workers]
//   * N browsers each render a slice of the timeline; segments are concatenated
//   * frames captured as JPEG q92: PNG encode + transfer was two thirds of the per-frame cost
//   * every <video> is swapped for an all-keyframe copy before capture: a seek then
//     decodes one frame instead of everything since the last keyframe (120 s -> 40 s
//     on a 29 s video with five clips)
//   * sound effects are the editable's <audio class="sfx" data-at="ms"> tags, mixed
//     data-sfx-under LU (on #vo, default 8) under the voice
//   * stage size is read from the page (window.STAGE), so any ratio works
//   * a render already at <out.mp4> is moved to renders/deletable first; the new one
//     is checked (duration, frames, stereo), and a one-frame-per-second sheet for
//     choosing the cover is written to the materials deletable/
// Four workers saturate a 12-core machine; more only contend. process.exit(0) at the
// end is needed: the local server holds Chrome's keep-alive sockets open.
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const { serve, launch, openStage, seekTo, readEditable } = require('./stage');

const [htmlArg, outArg, fpsArg, workersArg] = process.argv.slice(2);
if (!htmlArg || !outArg) { console.error('usage: render.js <editable.html> <out.mp4> [fps] [workers]'); process.exit(2); }
const htmlPath = path.resolve(htmlArg), out = path.resolve(outArg);
const dir = path.dirname(htmlPath);            // the editable's folder; everything it references is below it
const rel = path.basename(htmlPath);
const fps = parseInt(fpsArg || '30', 10);
const WORKERS = parseInt(workersArg || '4', 10);
const inRoot = path.basename(path.dirname(out)) === 'renders';

const ed = readEditable(htmlPath);
if (!ed.durationMs) throw new Error(`${rel} has no data-duration on #stage`);
const frames = Math.round(ed.durationMs / 1000 * fps);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'stage-render-'));
fs.mkdirSync(path.dirname(out), { recursive: true });

const run = (cmd, args) => new Promise((res, rej) => {
  const p = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] }); let err = '';
  p.stderr.on('data', d => { err += d; });
  p.on('close', c => c === 0 ? res() : rej(new Error(`${cmd} ${c}: ${err.slice(-400)}`)));
});
const probe = (file, entries) => execFileSync('ffprobe', ['-v', 'error', '-show_entries', entries, '-of', 'default=nw=1', file], { encoding: 'utf8' });

// All-keyframe copy of each clip, alpha kept for VP9 cut-outs.
async function intraCopies() {
  const swap = {};
  await Promise.all(ed.videos.map(async (src, i) => {
    const file = path.join(dir, src);
    if (!fs.existsSync(file)) { console.error(`warning: ${src} not found`); return; }
    const alpha = /alpha_mode=1/i.test(probe(file, 'stream_tags=alpha_mode'));
    const copy = path.join(tmp, `clip${i}${path.extname(src)}`);
    const args = alpha
      ? ['-y', '-c:v', 'libvpx-vp9', '-i', file, '-an', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-g', '1',
         '-deadline', 'realtime', '-cpu-used', '8', '-row-mt', '1', '-crf', '20', '-b:v', '0', copy]
      : ['-y', '-i', file, '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '1', '-crf', '16', '-pix_fmt', 'yuv420p', copy];
    await run('ffmpeg', args);
    swap[src] = copy;
  }));
  return swap;
}

async function runWorker(id, from, to, port) {
  const seg = path.join(tmp, `seg${String(id).padStart(2, '0')}.mp4`);
  const browser = await launch();
  const { page, W, H, nAnims } = await openStage(browser, port, rel);
  const ff = spawn('ffmpeg', ['-y','-v','error','-f','image2pipe','-vcodec','mjpeg','-framerate',String(fps),'-i','-',
    '-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p', seg], { stdio: ['pipe','inherit','inherit'] });
  const write = buf => new Promise(r => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', r); else r(); });

  let tSeek = 0, tShot = 0, tPipe = 0;
  const clip = { x: 0, y: 0, width: W, height: H };
  for (let i = from; i < to; i++) {
    const t0 = Date.now();
    await seekTo(page, i * 1000 / fps);
    const t1 = Date.now();
    const shot = await page.screenshot({ type: 'jpeg', quality: 92, clip });
    const t2 = Date.now();
    await write(shot);
    tSeek += t1 - t0; tShot += t2 - t1; tPipe += Date.now() - t2;
    if ((i - from) % 100 === 0) process.stdout.write(`\r  w${id} ${i - from}/${to - from}   `);
  }
  const stuck = await page.evaluate(() => window.__stuck);
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error(`w${id} ffmpeg ${c}`))));
  await browser.close();
  const n = to - from;
  console.log(`\n  w${id} done ${n} frames | ${W}x${H} | anims ${nAnims} | seek ${(tSeek/n).toFixed(0)}ms shot ${(tShot/n).toFixed(0)}ms pipe ${(tPipe/n).toFixed(0)}ms${stuck ? ` | ${stuck} video seeks timed out` : ''}`);
  return seg;
}

function mixAudio(silent, secs) {
  const inputs = ['-i', silent], parts = [], labels = [];
  let idx = 1;
  if (ed.voSrc) {
    inputs.push('-i', path.join(dir, ed.voSrc));
    parts.push(`[${idx}:a]loudnorm=I=-16:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,apad[vo]`); labels.push('[vo]'); idx++;
  }
  ed.sfx.forEach((s, k) => {
    const file = path.join(dir, s.src);
    if (!fs.existsSync(file)) { console.error(`warning: sound effect ${s.src} not found, skipped`); return; }
    const ms = Math.max(0, Math.round(s.at));
    inputs.push('-i', file);
    parts.push(`[${idx}:a]loudnorm=I=${-16 - ed.sfxUnder}:TP=-3,aformat=channel_layouts=stereo,adelay=${ms}|${ms}[fx${k}]`); labels.push(`[fx${k}]`); idx++;
  });
  if (ed.bgmSrc) {
    const bed = path.join(tmp, 'bed.wav');
    execFileSync('python3', [path.join(__dirname, '..', 'bgm-extend.py'), path.join(dir, ed.bgmSrc), bed, secs], { stdio: 'inherit' });
    inputs.push('-i', bed);
    parts.push(`[${idx}:a]loudnorm=I=-36:TP=-6:LRA=9,afade=t=in:d=1,afade=t=out:st=${(ed.durationMs/1000-1.5).toFixed(2)}:d=1.5[bed]`); labels.push('[bed]'); idx++;
  }
  const fc = labels.length ? `${parts.join(';')};${labels.join('')}amix=inputs=${labels.length}:normalize=0,atrim=0:${secs}[a]` : '';
  execFileSync('ffmpeg', ['-y','-v','error', ...inputs, ...(fc ? ['-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:a', 'aac', '-b:a', '192k'] : []),
    '-c:v','copy','-t',secs,'-movflags','+faststart', out], { stdio: 'inherit' });
}

function checkRender() {
  const problems = [];
  const fmt = probe(out, 'format=duration');
  const dur = parseFloat((fmt.match(/duration=([\d.]+)/) || [])[1]) * 1000;
  if (Math.abs(dur - ed.durationMs) > 50) problems.push(`duration ${dur.toFixed(0)} ms, expected ${ed.durationMs}`);
  const nb = parseInt((probe(out, 'stream=nb_frames').match(/nb_frames=(\d+)/) || [])[1], 10);
  if (Math.abs(nb - frames) > 1) problems.push(`${nb} frames, expected ${frames}`);
  if ((ed.voSrc || ed.bgmSrc || ed.sfx.length) && !/channels=2/.test(probe(out, 'stream=channels'))) problems.push('audio is not stereo');
  console.log(problems.length ? `  check FAILED: ${problems.join('; ')}` : `  check ok: ${(ed.durationMs/1000).toFixed(2)} s, ${nb} frames, stereo`);
}

// renders/ holds only the current render: the previous one goes to renders/deletable,
// stamped with its own modification time.
function archivePrevious() {
  if (!fs.existsSync(out)) return;
  if (!inRoot) return fs.rmSync(out);
  const d = fs.statSync(out).mtime, p = n => String(n).padStart(2, '0');
  const stamp = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
  const folder = path.join(path.dirname(out), 'deletable');
  fs.mkdirSync(folder, { recursive: true });
  let target = path.join(folder, `${ed.name}_${stamp}.mp4`);
  for (let n = 2; fs.existsSync(target); n++) target = path.join(folder, `${ed.name}_${stamp}_${n}.mp4`);
  fs.renameSync(out, target);
  console.log(`previous render moved to ${path.relative(process.cwd(), target)}`);
}

function coverSheet() {
  const deletable = path.join(dir, 'materials', ed.name, 'deletable');
  if (!fs.existsSync(path.dirname(deletable))) return;
  fs.mkdirSync(deletable, { recursive: true });
  const sheet = path.join(deletable, 'cover-sheet.jpg');
  const rows = Math.ceil(ed.durationMs / 1000 / 6);
  execFileSync('ffmpeg', ['-y','-v','error','-i', out, '-vf', `fps=1,scale=216:-1,tile=6x${rows}`, '-frames:v', '1', sheet]);
  console.log(`  cover sheet: ${sheet} (tile n = second n-1; pick one, then tools/set-cover.sh ${path.relative(process.cwd(), out)} <second>)`);
}

(async () => {
  archivePrevious();
  const t0 = Date.now();
  const swap = await intraCopies();
  const tPrep = Date.now();
  const server = await serve(dir, swap);
  const port = server.address().port;
  console.log(`rendering ${rel}: ${frames} frames @ ${fps} fps across ${WORKERS} workers | ${ed.videos.length} clips prepared in ${((tPrep - t0) / 1000).toFixed(0)}s | ${ed.sfx.length} sound effects`);

  const bounds = [];
  for (let i = 0; i < WORKERS; i++) bounds.push([Math.floor(i * frames / WORKERS), Math.floor((i + 1) * frames / WORKERS)]);
  const segs = await Promise.all(bounds.map(([a, b], i) => runWorker(i, a, b, port)));
  console.log(`  capture done in ${((Date.now() - tPrep) / 1000).toFixed(0)}s`);
  server.closeAllConnections && server.closeAllConnections();
  server.close();
  const tTail = Date.now();

  const listFile = path.join(tmp, 'list.txt');
  fs.writeFileSync(listFile, segs.map(s => `file '${s}'`).join('\n'));
  const silent = path.join(tmp, 'joined.mp4');
  execFileSync('ffmpeg', ['-y','-v','error','-f','concat','-safe','0','-i',listFile,'-c','copy', silent]);
  mixAudio(silent, (ed.durationMs / 1000).toFixed(3));
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`  concat+audio in ${((Date.now()-tTail)/1000).toFixed(0)}s | total ${((Date.now()-t0)/1000).toFixed(0)}s`);

  checkRender();
  coverSheet();
  console.log('done:', out);
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
