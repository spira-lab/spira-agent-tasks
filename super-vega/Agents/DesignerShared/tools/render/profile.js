// Platform profile shared by the render tools. Decisions come from the platform and the machine,
// never from new environment variables.
const fs = require('fs'), os = require('os'), path = require('path');

const MIN_FREE_BYTES = 4 * 2 ** 30;
const STALE_MS = 4 * 3600 * 1000;

function cpuCount() {
  return typeof os.availableParallelism === 'function' ? os.availableParallelism() : os.cpus().length;
}

function sweepStale(dir) {
  const now = Date.now();
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    try { if (now - fs.statSync(p).mtimeMs > STALE_MS) fs.rmSync(p, { recursive: true, force: true }); } catch {}
  }
}

let cachedRoot;
// /dev/shm (per user) on Linux when it is writable with room to spare, else the OS temp dir.
function scratchRoot() {
  if (cachedRoot) return cachedRoot;
  cachedRoot = os.tmpdir();
  try {
    fs.accessSync('/dev/shm', fs.constants.W_OK);
    const st = fs.statfsSync('/dev/shm');
    if (st.bavail * st.bsize >= MIN_FREE_BYTES) {
      const dir = path.join('/dev/shm', `supervega-${process.getuid()}`);
      fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
      sweepStale(dir);
      cachedRoot = dir;
    }
  } catch {}
  return cachedRoot;
}

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(scratchRoot(), prefix));
}

// kind: 'intermediate' (reference cuts, composites, share copy) or 'final' (the delivered picture).
function preset(kind) {
  return kind === 'final' ? 'faster' : 'veryfast';
}

// heavy-slot.py keeps <super>/.locks/render-slot-<n>.who while a slot is held (this render's own included).
function rendersRunning() {
  try {
    return fs.readdirSync(path.resolve(__dirname, '../../../../.locks')).filter((n) => /^render-slot-\d+\.who$/.test(n)).length;
  } catch { return 0; }
}

// Splits the cores among the renders running now: a lone render takes the whole machine
// (each Chrome also feeds an x264, so one Chrome per 2 cores), later ones take what is left.
function defaultWorkers() {
  return Math.max(2, Math.min(16, Math.floor(cpuCount() / (2 * Math.max(1, rendersRunning())))));
}

// Threads for each x264 process when several run side by side.
function x264Threads() {
  return 2;
}

function gpuArgs() {
  return ['--disable-gpu', '--use-angle=swiftshader'];
}

module.exports = { cpuCount, scratchRoot, makeTempDir, sweepStale, preset, defaultWorkers, x264Threads, gpuArgs };
