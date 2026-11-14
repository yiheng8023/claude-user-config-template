#!/usr/bin/env node
// Opt-in missing-env repair. Permission grants are never restored by a hook.
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

function safePath(file) {
  for (let p = path.resolve(file); ; p = path.dirname(p)) {
    try { if (fs.lstatSync(p).isSymbolicLink()) throw new Error('linked-path'); }
    catch (e) { if (e.code !== 'ENOENT') throw e; }
    if (path.dirname(p) === p) break;
  }
}
function atomicWrite(file, content, before) {
  safePath(file);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const current = () => fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null;
  if (current() !== before) throw new Error('concurrent-settings-writer');
  if (before !== null) {
    const backup = file + '.bak-' + Date.now() + '-' + crypto.randomBytes(4).toString('hex');
    fs.writeFileSync(backup, before, { flag: 'wx', mode: 0o600 });
  }
  const tmp = file + '.guard-' + process.pid + '-' + crypto.randomBytes(6).toString('hex');
  try {
    fs.writeFileSync(tmp, content, { flag: 'wx', mode: 0o600 });
    if (current() !== before) throw new Error('concurrent-settings-writer');
    safePath(file);
    fs.renameSync(tmp, file);
  } finally { if (fs.existsSync(tmp)) fs.unlinkSync(tmp); }
}
function mergeGuarded(settings, declaration) {
  if (declaration.permissions_allow?.length) throw new Error('permission-restore-is-not-supported');
  const result = JSON.parse(JSON.stringify(settings));
  const fixed = [];
  const env = declaration.env || {};
  if (typeof env !== 'object' || Array.isArray(env)) throw new Error('invalid-env-declaration');
  if (result.env !== undefined && (typeof result.env !== 'object' || result.env === null || Array.isArray(result.env))) throw new Error('invalid-settings-env');
  for (const [key, value] of Object.entries(env)) {
    if (typeof value !== 'string') throw new Error('invalid-env-value');
    if (!Object.hasOwn(result.env || {}, key)) {
      result.env ||= {};
      result.env[key] = value;
      fixed.push(key);
    }
  }
  return { settings: result, fixed };
}
function run(argv = process.argv.slice(2), home = path.join(os.homedir(), '.claude'), source = __dirname) {
  const file = path.join(home, 'settings.json');
  const dataFile = path.join(source, 'guarded-fields.json');
  safePath(file); safePath(dataFile);
  const before = fs.readFileSync(file, 'utf8');
  const original = JSON.parse(before);
  const declaration = fs.existsSync(dataFile) ? JSON.parse(fs.readFileSync(dataFile, 'utf8')) : {};
  const checked = mergeGuarded(original, declaration);
  if (argv.includes('--check')) {
    console.log('[settings-guard] missing env fields: ' + checked.fixed.length);
    return checked.fixed.length ? 1 : 0;
  }
  if (argv.includes('--install')) {
    // Deployment is owned by the backed-up, no-delete repository installer.
    console.error('[settings-guard] deploy with python -B scripts/install.py --overwrite-files');
    return 2;
  }
  if (checked.fixed.length) {
    atomicWrite(file, JSON.stringify(checked.settings, null, 2) + '\n', before);
    console.log('[settings-guard] restored missing env fields: ' + checked.fixed.length);
  }
  return 0;
}
module.exports = { safePath, atomicWrite, mergeGuarded, run };
if (require.main === module) {
  try { process.exitCode = run(); }
  catch (_) {
    console.error('[settings-guard] repair skipped; inspect declaration and concurrent writers');
    process.exitCode = process.argv.includes('--check') || process.argv.includes('--install') ? 2 : 0;
  }
}
