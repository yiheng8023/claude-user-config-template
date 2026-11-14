#!/usr/bin/env python3
"""Check or restore the Claude Code plugin set declared in config/plugins.example.json.

  python3 scripts/plugins.py --check      report missing/disabled plugins (exit 1 on drift)
  python3 scripts/plugins.py --install    install missing plugins and enable disabled ones
  python3 scripts/plugins.py --install --include-optional
  python3 scripts/plugins.py --install --dry-run
                                         print the commands without running them

Plugin bodies live in ~/.claude/plugins/, not in this repository. install.py
restores settings.json (which lists enabledPlugins); this script restores the
plugin bodies themselves.

Requires the `claude` CLI on PATH. Versions are not pinned here: the active
marketplace snapshot decides. Marketplace/ref choices belong to configuration.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "config" / "plugins.example.json"
CLAUDE_HOME = Path.home() / ".claude"


def load_manifest(include_optional: bool = False) -> list[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plugins = data.get("plugins", [])
    if include_optional:
        plugins = [*plugins, *data.get("optionalPlugins", [])]
    if not isinstance(plugins, list) or not all(isinstance(p, str) for p in plugins):
        raise SystemExit("plugins.example.json: 'plugins' must be a list of strings")
    return plugins


def claude_bin() -> str:
    for name in ("claude", "claude.cmd", "claude.exe"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("claude CLI not found on PATH; install Claude Code first")


def run_claude(args: list[str], json_out: bool = True) -> subprocess.CompletedProcess:
    cmd = [claude_bin(), "plugin", *args]
    if json_out and args[0] != "list":
        cmd.append("--json")
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def installed_from_cli() -> dict[str, dict]:
    proc = run_claude(["list", "--json"], json_out=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip() or "claude plugin list failed")
    data = json.loads(proc.stdout)
    entries = data if isinstance(data, list) else data.get("installed", [])
    return {e["id"]: e for e in entries if isinstance(e, dict) and e.get("id") and e.get("scope") == "user"}


def installed_from_files() -> dict[str, dict]:
    """Fallback for a broken/old CLI: read the plugin registry and settings."""
    out: dict[str, dict] = {}
    registry = CLAUDE_HOME / "plugins" / "installed_plugins.json"
    if registry.exists():
        data = json.loads(registry.read_text(encoding="utf-8"))
        for name, records in (data.get("plugins") or {}).items():
            for rec in records:
                if rec.get("scope") != "user":
                    continue
                out[name] = {"id": name, "version": rec.get("version"), "enabled": None}
    enabled = {}
    settings = CLAUDE_HOME / "settings.json"
    if settings.exists():
        try:
            enabled = (json.loads(settings.read_text(encoding="utf-8")) or {}).get("enabledPlugins", {})
        except Exception:
            enabled = {}
    for name, rec in out.items():
        rec["enabled"] = bool(enabled.get(name, False))
    return out


def installed_plugins() -> dict[str, dict]:
    try:
        return installed_from_cli()
    except Exception as exc:
        print("(claude plugin list unavailable; falling back to user-scope files)")
        return installed_from_files()


def main() -> int:
    install = "--install" in sys.argv[1:]
    dry_run = "--dry-run" in sys.argv[1:]
    desired = load_manifest("--include-optional" in sys.argv[1:])
    if not desired:
        print("No plugins declared for this selection.")
        return 0
    installed = installed_plugins()

    missing = [p for p in desired if p not in installed]
    disabled = [p for p in desired if p in installed and installed[p].get("enabled") is False]
    extra = sorted(p for p in installed if p not in desired)

    print(f"declared={len(desired)} installed={len(installed)} missing={len(missing)} disabled={len(disabled)}")
    for p in desired:
        rec = installed.get(p)
        if rec is None:
            print(f"  MISSING  {p}")
        elif rec.get("enabled") is False:
            print(f"  DISABLED {p}  ({rec.get('version')})")
        else:
            print(f"  OK       {p}  ({rec.get('version')})")
    if extra:
        print("installed but not declared (left untouched):")
        for p in extra:
            print(f"  EXTRA    {p}  ({installed[p].get('version')})")

    if not install:
        return 1 if (missing or disabled) else 0

    if dry_run:
        for p in missing:
            print(f"[dry-run] claude plugin install {p} --scope user -y")
        for p in disabled:
            print(f"[dry-run] claude plugin enable {p} --scope user")
        return 0

    failed = False
    for p in missing:
        proc = run_claude(["install", p, "--scope", "user", "-y"])
        ok = proc.returncode == 0
        print(("installed " if ok else "FAILED install ") + p)
        if not ok:
            failed = True
            print((proc.stderr or proc.stdout or "").strip()[:500])
    for p in disabled:
        proc = run_claude(["enable", p, "--scope", "user"])
        ok = proc.returncode == 0
        print(("enabled " if ok else "FAILED enable ") + p)
        if not ok:
            failed = True
            print((proc.stderr or proc.stdout or "").strip()[:500])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
