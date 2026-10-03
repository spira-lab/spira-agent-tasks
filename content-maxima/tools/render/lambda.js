// The browser work of render.js and audit.js, on AWS Lambda: CM_RENDER_LAMBDA names the
// function, CM_RENDER_BUCKET its bucket (both set on the worker; see
// apps/cc-engine/scripts/content-maxima-render-lambda/). The Lambda runs its own copy of
// stage.js and inspect.js: after changing either, re-run that deploy.sh as well.
//   * the editable, the files it references and its prepared all-keyframe clips make
//     up the site at s3://<bucket>/jobs/<id>/site/, audio left out (the page mutes it
//     at ?render; render.js mixes it locally). Each file is stored once by content at
//     jobs/cas/<sha256><ext> and copied into the site inside S3, so a file already
//     there from an earlier audit or render, of this video or any other, is not
//     uploaded again. The sha256 of each file is remembered in
//     materials/<name>/deletable/.cas-index.json by path, size, mtime, ctime and inode
//   * jobs/cas/ expires with the rest of jobs/, a day after an object was written; one
//     older than FRESH_MS is written again, so nothing a job copies can expire under it
//   * the timeline is cut into contiguous chunks of about CM_RENDER_FRAMES_PER_CHUNK
//     frames (default 90, at most CM_RENDER_MAX_CHUNKS = 40); every chunk is one
//     Lambda invocation that renders its range with the same stage.js code and
//     encoder settings, so the segments concat without a re-encode
//   * a chunk that fails (invocation or download) is run once more; the segments come
//     back in timeline order
//   * an audit is one invocation over the same site (inspect.js); its sheet frames
//     come back through the bucket
// The bucket's lifecycle rule expires jobs/ after a day; the job is also deleted here.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const { S3Client, PutObjectCommand, GetObjectCommand, HeadObjectCommand, CopyObjectCommand, ListObjectsV2Command, DeleteObjectsCommand } = require('@aws-sdk/client-s3');
const { LambdaClient, InvokeCommand } = require('@aws-sdk/client-lambda');

const FUNCTION = process.env.CM_RENDER_LAMBDA;
const BUCKET = process.env.CM_RENDER_BUCKET;
const REGION = process.env.CM_RENDER_REGION || process.env.AWS_REGION || 'us-west-1';
const FRAMES_PER_CHUNK = parseInt(process.env.CM_RENDER_FRAMES_PER_CHUNK || '90', 10);
const MAX_CHUNKS = parseInt(process.env.CM_RENDER_MAX_CHUNKS || '40', 10);
const AUDIO = /\.(mp3|wav|m4a|ogg|aac|flac)$/i;
const CAS = 'jobs/cas/';
const FRESH_MS = 20 * 3600 * 1000;  // jobs/ expires after 1 day; rewrite a cas object older than this

/** Contiguous, near-equal frame ranges [from, to). */
function planChunks(frames) {
  const n = Math.max(1, Math.min(MAX_CHUNKS, Math.ceil(frames / FRAMES_PER_CHUNK)));
  return Array.from({ length: n }, (_, i) => [Math.floor(i * frames / n), Math.floor((i + 1) * frames / n)]);
}

const walk = d => fs.readdirSync(d, { withFileTypes: true }).flatMap(e =>
  e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]);

/** Files the page can load, as { key relative to dir: local file }. */
function siteFiles(dir, rel, ed, swap) {
  const files = { [rel]: path.join(dir, rel) };
  const add = r => {
    const file = path.join(dir, r);
    if (file.startsWith(dir + path.sep) && fs.existsSync(file) && fs.statSync(file).isFile()) files[r] = file;
  };
  const materials = path.join(dir, 'materials', ed.name);
  if (fs.existsSync(materials)) {
    for (const f of walk(materials)) {
      const r = path.relative(dir, f);
      if (!/(^|\/)(deletable|jobs)\//.test(path.relative(materials, f))) add(r);
    }
  }
  const refs = [...ed.html.matchAll(/\b(?:src|href)="([^"]+)"|url\(\s*['"]?([^'")]+)['"]?\s*\)/g)].map(m => m[1] || m[2]);
  for (const r of refs) if (!/^(data:|blob:|#|[a-z]+:\/\/)/i.test(r)) add(decodeURIComponent(r.split(/[?#]/)[0]));
  for (const r of Object.keys(files)) if (AUDIO.test(r)) delete files[r];
  for (const [src, copy] of Object.entries(swap)) files[src] = copy;
  return files;
}

async function pool(items, n, fn) {
  const out = new Array(items.length); let next = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => {
    while (next < items.length) { const i = next++; out[i] = await fn(items[i], i); }
  }));
  return out;
}

function clients() {
  if (!FUNCTION || !BUCKET) throw new Error('CM_RENDER_LAMBDA and CM_RENDER_BUCKET must name the render Lambda and its bucket');
  return { s3: new S3Client({ region: REGION }), lambda: new LambdaClient({ region: REGION, maxAttempts: 1 }) };
}

const sha256 = file => new Promise((res, rej) => {
  const h = crypto.createHash('sha256');
  fs.createReadStream(file).on('error', rej).on('data', d => h.update(d)).on('end', () => res(h.digest('hex')));
});

/** { local file: { sha, size } }, reusing the hashes of files unchanged since the last audit or render. */
async function hashFiles(dir, ed, files) {
  const indexFile = path.join(dir, 'materials', ed.name, 'deletable', '.cas-index.json');
  let index = {};
  try { index = JSON.parse(fs.readFileSync(indexFile, 'utf8')); } catch { /* first run, or unreadable: hash everything */ }
  const next = {}, out = {};
  await pool([...new Set(files)], 8, async file => {
    const { size, mtimeMs, ctimeMs, ino } = fs.statSync(file);
    const stamp = [size, mtimeMs, ctimeMs, ino].join('|');
    const sha = index[file] && index[file].stamp === stamp ? index[file].sha : await sha256(file);
    next[file] = { stamp, sha };
    out[file] = { sha, size };
  });
  fs.mkdirSync(path.dirname(indexFile), { recursive: true });
  fs.writeFileSync(`${indexFile}.part`, JSON.stringify(next));
  fs.renameSync(`${indexFile}.part`, indexFile);
  return out;
}

/**
 * Build the page and what it loads under a new jobs/<id>/site/: each file goes to
 * jobs/cas/ unless it is already there and fresh, then is copied into the site inside S3.
 */
async function stageSite(s3, { dir, rel, ed, swap }) {
  const job = `jobs/${ed.name}-${Date.now().toString(36)}-${crypto.randomBytes(3).toString('hex')}`;
  const t0 = Date.now();
  const files = Object.entries(siteFiles(dir, rel, ed, swap));
  const hashes = await hashFiles(dir, ed, files.map(([, file]) => file));
  const casKey = file => `${CAS}${hashes[file].sha}${path.extname(file).toLowerCase()}`;
  const objects = new Map(files.map(([, file]) => [casKey(file), { file, size: hashes[file].size }]));
  let bytes = 0, upBytes = 0, uploaded = 0;
  await pool([...objects], 16, async ([cas, { file, size }]) => {
    const head = await s3.send(new HeadObjectCommand({ Bucket: BUCKET, Key: cas })).catch(e => {
      if (e.name === 'NotFound' || (e.$metadata && e.$metadata.httpStatusCode === 404)) return null;
      throw e;
    });
    if (head && Date.now() - head.LastModified.getTime() < FRESH_MS) return;
    // A stream cannot be replayed by the SDK's own retry, so a failed put is made again from a new one.
    await twice(`upload ${path.basename(file)}`, () =>
      s3.send(new PutObjectCommand({ Bucket: BUCKET, Key: cas, Body: fs.createReadStream(file), ContentLength: size })));
    uploaded++; upBytes += size;
  });
  await pool(files, 16, async ([key, file]) => {
    bytes += hashes[file].size;
    await s3.send(new CopyObjectCommand({ Bucket: BUCKET, Key: `${job}/site/${key}`, CopySource: `${BUCKET}/${casKey(file)}` }));
  });
  const note = `${files.length} files, ${(bytes / 1e6).toFixed(1)} MB (${uploaded} uploaded, ${(upBytes / 1e6).toFixed(1)} MB) in ${((Date.now() - t0) / 1000).toFixed(0)}s`;
  return { job, site: `${job}/site/`, note };
}

/** Run `fn`, once more if it throws (a chunk and its download are idempotent). */
async function twice(label, fn) {
  try { return await fn(); } catch (e) {
    console.error(`  ${label} failed, retrying: ${e.message}`);
    try { return await fn(); } catch (e2) { throw new Error(`${label} failed twice: ${e2.message}`); }
  }
}

async function invoke(lambda, payload) {
  const res = await lambda.send(new InvokeCommand({ FunctionName: FUNCTION, Payload: Buffer.from(JSON.stringify(payload)) }));
  const body = JSON.parse(Buffer.from(res.Payload || []).toString() || 'null');
  if (res.FunctionError) throw new Error(`${body && body.errorType}: ${body && body.errorMessage}`);
  return body;
}

async function download(s3, key, file) {
  const obj = await s3.send(new GetObjectCommand({ Bucket: BUCKET, Key: key }));
  fs.writeFileSync(file, Buffer.from(await obj.Body.transformToByteArray()));
}

async function removeJob(s3, job) {
  const listed = await s3.send(new ListObjectsV2Command({ Bucket: BUCKET, Prefix: `${job}/` }));
  const keys = (listed.Contents || []).map(o => ({ Key: o.Key }));
  if (keys.length) await s3.send(new DeleteObjectsCommand({ Bucket: BUCKET, Delete: { Objects: keys, Quiet: true } })).catch(() => {});
}

async function renderChunks({ dir, rel, ed, swap, fps, frames, tmp }) {
  const { s3, lambda } = clients();
  const { job, site, note } = await stageSite(s3, { dir, rel, ed, swap });
  const chunks = planChunks(frames);
  console.log(`rendering ${rel}: ${frames} frames @ ${fps} fps across ${chunks.length} Lambda chunks (${FUNCTION}) | ${note} | ${ed.sfx.length} sound effects`);

  const tCap = Date.now();
  const segs = await Promise.all(chunks.map(async ([from, to], i) => {
    const label = `c${String(i).padStart(2, '0')}`;
    const key = `${job}/chunks/${label}.mp4`;
    const seg = path.join(tmp, `${label}.mp4`);
    const r = await twice(label, async () => {
      const r = await invoke(lambda, { mode: 'render', bucket: BUCKET, site, rel, fps, from, to, key });
      await download(s3, key, seg);
      return r;
    });
    console.log(`${r.summary} | ${(r.ms / 1000).toFixed(0)}s${r.cold ? ' cold' : ''}`);
    return seg;
  }));
  console.log(`  ${chunks.length} chunks captured in ${((Date.now() - tCap) / 1000).toFixed(0)}s`);
  await removeJob(s3, job);
  return segs;
}

/** inspect.js on the Lambda; the sheet frames are written to `shotDir`. `swap` is intra.js's copies. */
async function auditOnLambda({ dir, rel, ed, at, shotDir, swap = {} }) {
  const { s3, lambda } = clients();
  const { job, site } = await stageSite(s3, { dir, rel, ed, swap });
  try {
    return await twice('audit', async () => {
      const r = await invoke(lambda, { mode: 'audit', bucket: BUCKET, site, rel, at, durationMs: ed.durationMs, key: `${job}/audit/` });
      await pool(r.shots, 16, (s, i) => download(s3, s.key, path.join(shotDir, `${String(i).padStart(3, '0')}.jpg`)));
      return r;
    });
  } finally {
    await removeJob(s3, job);
  }
}

module.exports = { renderChunks, auditOnLambda, planChunks };
