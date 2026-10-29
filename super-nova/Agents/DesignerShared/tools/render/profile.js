// Platform profile shared by the render tools. Decisions come from the platform and the machine,
// never from new environment variables. On macOS every value is the one the tools always used.
const fs = require('fs'), os = require('os'), path = require('path');

const isMac = process.platform === 'darwin';
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
  if (process.platform === 'linux') {
    try {
      fs.accessSync('/dev/shm', fs.constants.W_OK);
      const st = fs.statfsSync('/dev/shm');
      if (st.bavail * st.bsize >= MIN_FREE_BYTES) {
        const dir = path.join('/dev/shm', `supernova-${process.getuid ? process.getuid() : 'user'}`);
        fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
        sweepStale(dir);
        cachedRoot = dir;
      }
    } catch {}
  }
  return cachedRoot;
}

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(scratchRoot(), prefix));
}

// kind: 'intermediate' (reference cuts, composites, share copy) or 'final' (the delivered picture).
function preset(kind) {
  if (isMac) return 'medium';
  return kind === 'final' ? 'faster' : 'veryfast';
}

function defaultWorkers() {
  return isMac ? 4 : Math.max(1, Math.min(4, Math.floor((cpuCount() - 2) / 2)));
}

// Threads for each x264 process when several run side by side; null leaves ffmpeg's default.
function x264Threads() {
  return isMac ? null : 2;
}

function gpuArgs() {
  return isMac
    ? ['--use-angle=metal', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--enable-zero-copy']
    : ['--disable-gpu', '--use-angle=swiftshader'];
}

module.exports = { isMac, cpuCount, scratchRoot, makeTempDir, sweepStale, preset, defaultWorkers, x264Threads, gpuArgs };
