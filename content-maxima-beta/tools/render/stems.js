// Level-ready stems: the MP4 is mixed from these float signals, and Web Audio auditions their 16-bit FLAC copies
// (about an eighth of the WAV's size, sample-exact, so the audition stays in step with the video).
const { execFileSync, spawnSync } = require('child_process');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const { mixGraph } = require('./mix-graph');

// Integrated loudness of a stem, as ebur128 measures it; null for silence.
function lufsOf(file) {
  const r = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', file, '-af', 'ebur128', '-f', 'null', '-'], { encoding: 'utf8' });
  const m = [...(r.stderr || '').matchAll(/^\s+I:\s+(-?[\d.]+) LUFS/gm)].pop();
  const v = m ? Number(m[1]) : NaN;
  return Number.isFinite(v) && v > -70 ? Math.round(v * 10) / 10 : null;
}

function writeStems(ed, dir, tmp, secs) {
  for (const level of [ed.bgmOffsetDb, ed.sfxOffsetDb]) {
    if (level != null && (!Number.isFinite(level) || level < -20 || level > 6)) throw new Error('Mix offset must be -20 to +6 dB');
  }
  if (ed.bgmMatchLufs != null && (!Number.isFinite(ed.bgmMatchLufs) || ed.bgmMatchLufs < -60 || ed.bgmMatchLufs > -5)) {
    throw new Error('#bgm data-match-lufs must be -60 to -5 LUFS');
  }
  // Preserve per-cue gains and bed ducking; the two group levels are applied after these stems.
  const graph = mixGraph({ ...ed, bgmOffsetDb: 0 }, dir, tmp, secs);
  const groups = { vo: [], sfx: [], bgm: [] };
  graph.labels.forEach((label, i) => {
    const group = label === '[vo]' ? 'vo' : label === '[bed]' ? 'bgm' : 'sfx';
    groups[group].push({ label, filter: graph.parts[i] });
  });
  const result = {};
  for (const [name, items] of Object.entries(groups)) {
    if (!items.length) continue;
    const file = path.join(tmp, `${name}.wav`);
    const filter = items.map(item => item.filter).join(';') + ';' + items.map(item => item.label).join('')
      + `amix=inputs=${items.length}:normalize=0,apad,atrim=0:${secs},aresample=48000,aformat=channel_layouts=stereo[a]`;
    execFileSync('ffmpeg', ['-y', '-v', 'error', ...graph.inputs, '-filter_complex', filter, '-map', '[a]', '-c:a', 'pcm_f32le', file], { stdio: 'inherit' });
    result[name] = file;
  }
  // A bed swapped for another kind sounds as loud as the one it replaced, as heard in this video (its own opening,
  // ducking and fades), before the group level; a track's catalogue gain levels its whole length, not this stretch.
  if (result.bgm && ed.bgmMatchLufs != null) {
    const heard = lufsOf(result.bgm);
    if (heard !== null && Math.abs(ed.bgmMatchLufs - heard) >= 0.1) {
      const matched = path.join(tmp, 'bgm-matched.wav');
      execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', result.bgm, '-af', `volume=${(ed.bgmMatchLufs - heard).toFixed(2)}dB`, '-c:a', 'pcm_f32le', matched], { stdio: 'inherit' });
      console.log(`  bed matched to ${ed.bgmMatchLufs} LUFS (was ${heard})`);
      result.bgm = matched;
    }
  }
  return result;
}

// What the voice says, a sentence at a time, as the captions spell it and when it is said: an edit can then name the
// line it changes. Without a voice or its timings there are none, which only means a line cannot be picked.
function spokenLines(ed, htmlPath, folder) {
  if (!ed.voSrc) return [];
  const out = path.join(folder, 'lines.json');
  try {
    execFileSync('python3', [path.join(__dirname, '..', 'captions.py'), htmlPath, '--lines', out], { stdio: ['ignore', 'ignore', 'inherit'] });
    return JSON.parse(fs.readFileSync(out, 'utf8')).filter(line => line.startMs < ed.durationMs && line.text.trim())
      .map(line => ({ ...line, endMs: Math.min(Math.max(line.endMs, line.startMs + 1), ed.durationMs) }));
  } catch (error) {
    console.error(`warning: no spoken lines for the edit panel (${error.message.split('\n')[0]})`);
    return [];
  } finally {
    fs.rmSync(out, { force: true });
  }
}

function saveStems(files, ed, htmlPath, videoPath) {
  const folder = `${videoPath}.audio`;
  fs.mkdirSync(folder, { recursive: true });
  // Remove the receipt before replacing files: an interrupted copy is never a ready preview.
  fs.rmSync(path.join(folder, 'manifest.json'), { force: true });
  for (const [name, file] of Object.entries(files)) {
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', file, '-c:a', 'flac', '-sample_fmt', 's16', path.join(folder, `${name}.flac`)], { stdio: 'inherit' });
  }
  const manifest = {
    schema: 1, durationMs: ed.durationMs,
    videoSha256: crypto.createHash('sha256').update(fs.readFileSync(videoPath)).digest('hex'),
    editableSha256: crypto.createHash('sha256').update(fs.readFileSync(htmlPath)).digest('hex'),
    // The bed's loudness as heard here at the default level: what a bed of another kind is matched to.
    bgm: { present: Boolean(files.bgm), muted: Boolean(ed.bgmMuted), offsetDb: ed.bgmOffsetDb ?? 0, ...(files.bgm ? { lufs: lufsOf(files.bgm) } : {}) },
    sfx: { present: Boolean(files.sfx), muted: Boolean(ed.sfxMuted), offsetDb: ed.sfxOffsetDb ?? 0 },
    vo: { present: Boolean(files.vo), lines: spokenLines(ed, htmlPath, folder) }
  };
  fs.writeFileSync(path.join(folder, 'manifest.json'), JSON.stringify(manifest));
}

module.exports = { writeStems, saveStems };
