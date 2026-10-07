#!/usr/bin/env node
/*
 * Settings guardian — a Claude Code SessionStart hook. (Template copy.)
 *
 * Live ~/.claude/settings.json can be rewritten by outside tools (provider
 * switchers, installers, other agents). Fields that exist ONLY in that file
 * — owned by no tool — are silently dropped when such a rewrite happens
 * (observed 2026-10-01: a provider-switcher app update rewrite dropped an env
 * flag and one permissions entry).
 *
 * This hook re-asserts a short, explicitly declared list from
 * guarded-fields.json sitting next to this script (copy
 * guarded-fields.example.json to guarded-fields.json and declare YOUR
 * fields). Add-only: it never deletes or changes anything else, is a no-op
 * when nothing is missing, and any error exits 0 so it can never break a
 * session.
 *
 * It depends on nothing but Claude Code's own hook mechanism — it works
 * whether or not you use any provider switcher (that is the point).
 *
 * Modes:
 *   node settings-guard.js            hook mode: check + fix (prints only when it fixed something)
 *   node settings-guard.js --check    read-only report, changes nothing
 *   node settings-guard.js --install  deploy to ~/.claude/hooks, wire the SessionStart
 *                                     hook in settings.json, and run one fix pass
 *
 * Zero dependencies. Cross-platform (Windows / macOS / Linux).
 */
const fs = require("fs");
const os = require("os");
const path = require("path");

const HOMEDIR = os.homedir();
const CLAUDE_DIR = path.join(HOMEDIR, ".claude");
const SETTINGS = path.join(CLAUDE_DIR, "settings.json");
const HOOKS_DIR = path.join(CLAUDE_DIR, "hooks");
const SELF = __filename;
const DATA = path.join(__dirname, "guarded-fields.json");

const log = (m) => { try { console.log("[settings-guard] " + m); } catch (_) {} };

function loadGuarded() {
  try {
    const raw = JSON.parse(fs.readFileSync(DATA, "utf8"));
    const env = raw && typeof raw.env === "object" && raw.env ? raw.env : {};
    const perms = Array.isArray(raw && raw.permissions_allow) ? raw.permissions_allow : [];
    return { env, perms };
  } catch (_) {
    return { env: {}, perms: [] }; // no data file -> nothing declared -> no-op
  }
}

function readSettings() {
  return JSON.parse(fs.readFileSync(SETTINGS, "utf8"));
}

function atomicWrite(file, obj) {
  const tmp = file + ".guard-tmp";
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2) + "\n", "utf8");
  fs.renameSync(tmp, file);
}

function checkAndFix(apply) {
  const guarded = loadGuarded();
  let s;
  try { s = readSettings(); } catch (e) { log("settings.json unreadable: " + e.message); return 0; }
  const fixed = [];

  if (Object.keys(guarded.env).length) {
    s.env = s.env || {};
    for (const [k, v] of Object.entries(guarded.env)) {
      if (s.env[k] !== v) { fixed.push("env." + k); if (apply) s.env[k] = v; }
    }
  }
  for (const p of guarded.perms) {
    s.permissions = s.permissions || {};
    s.permissions.allow = s.permissions.allow || [];
    if (!s.permissions.allow.includes(p)) {
      fixed.push("permissions: " + p);
      if (apply) s.permissions.allow.push(p);
    }
  }

  if (!fixed.length) {
    if (!apply) log("all declared fields present (nothing to do)");
    return 0;
  }
  if (apply) {
    atomicWrite(SETTINGS, s);
    log("re-asserted " + fixed.length + " missing field(s): " + fixed.join("; "));
  } else {
    log("MISSING (dry-run, not written): " + fixed.join("; "));
  }
  return fixed.length;
}

function install() {
  // 1) deploy self + data into ~/.claude/hooks
  fs.mkdirSync(HOOKS_DIR, { recursive: true });
  const destSelf = path.join(HOOKS_DIR, "settings-guard.js");
  const destData = path.join(HOOKS_DIR, "guarded-fields.json");
  if (path.resolve(SELF) !== path.resolve(destSelf)) {
    fs.copyFileSync(SELF, destSelf);
    if (fs.existsSync(DATA)) fs.copyFileSync(DATA, destData);
    log("deployed to " + destSelf);
  } else if (fs.existsSync(DATA) && path.resolve(DATA) !== path.resolve(destData)) {
    fs.copyFileSync(DATA, destData);
    log("deployed data to " + destData);
  }

  // 2) wire the SessionStart hook (idempotent)
  const s = readSettings();
  s.hooks = s.hooks || {};
  s.hooks.SessionStart = s.hooks.SessionStart || [];
  const wired = JSON.stringify(s.hooks.SessionStart).includes("settings-guard.js");
  if (!wired) {
    s.hooks.SessionStart.push({
      hooks: [{ type: "command", command: "node " + destSelf.replace(/\\/g, "/") }],
    });
    atomicWrite(SETTINGS, s);
    log("SessionStart hook wired in settings.json");
  } else {
    log("SessionStart hook already present");
  }

  // 3) run one fix pass now
  checkAndFix(true);
}

try {
  const argv = process.argv.slice(2);
  if (argv.includes("--install")) install();
  else if (argv.includes("--check")) checkAndFix(false);
  else checkAndFix(true);
} catch (e) {
  try { console.log("[settings-guard] error (ignored): " + e.message); } catch (_) {}
}
process.exit(0);
