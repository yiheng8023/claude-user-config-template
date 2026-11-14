#!/usr/bin/env python3
"""Restore portable files additively; use --overwrite-files for backed-up replacements."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json_snapshot(path: Path) -> tuple[dict, bytes | None]:
    raw = path.read_bytes() if path.exists() else None
    data = json.loads(raw.decode("utf-8-sig")) if raw is not None else {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path.name}")
    return data, raw


def read_json(path: Path) -> dict:
    return read_json_snapshot(path)[0]


def safe_path(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError(f"Refusing linked path: {path}")


def clean_template(value):
    if isinstance(value, dict):
        return {k: clean_template(v) for k, v in value.items()
                if not k.startswith("_") and not
                (isinstance(v, str) and ("<SET_LOCALLY" in v or v == "replace-in-private-config"))}
    if isinstance(value, list):
        return [clean_template(v) for v in value]
    return value


def render_paths(value, home: Path):
    if isinstance(value, dict):
        return {k: render_paths(v, home) for k, v in value.items()}
    if isinstance(value, list):
        return [render_paths(v, home) for v in value]
    return value.replace("__CLAUDE_HOME__", home.as_posix()) if isinstance(value, str) else value


def merge_missing(existing: dict, defaults: dict) -> dict:
    result = copy.deepcopy(existing)
    for key, value in defaults.items():
        if key not in result:
            result[key] = copy.deepcopy(value)
        elif key not in {"permissions", "enabledPlugins"} and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_missing(result[key], value)
    return result


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


_UNSET = object()


def write_file(path: Path, content: bytes, *, dry_run=False, overwrite=True, expected_before=_UNSET) -> bool:
    safe_path(path)
    before = path.read_bytes() if path.exists() else None
    if expected_before is not _UNSET and before != expected_before:
        raise RuntimeError(f"Destination changed since preparation: {path.name}")
    if before == content:
        return False
    if before is not None and not overwrite:
        print(f"keep existing: {path}")
        return False
    print(f"{'would write' if dry_run else 'write'}: {path}")
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    if (path.read_bytes() if path.exists() else None) != before:
        raise RuntimeError(f"Destination changed during install: {path.name}")
    if before is not None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = path.with_name(path.name + f".bak-{stamp}")
        with backup.open("xb") as stream:
            os.chmod(backup, 0o600)
            stream.write(before)
        print(f"backup: {backup.name}")
    fd, temporary = tempfile.mkstemp(prefix=".config-install-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        # Detect ordinary concurrent rewrites before publishing; no OS-wide lock
        # with external switchers is implied. Restore while those writers are idle.
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError(f"Destination changed during install: {path.name}")
        safe_path(path)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def prepare_mcp(manifest: dict, existing: dict) -> tuple[dict, list[str]]:
    result = copy.deepcopy(existing)
    servers = result.get("mcpServers", {})
    if not isinstance(servers, dict) or not isinstance(manifest.get("mcpServers", {}), dict):
        raise ValueError("mcpServers must be an object")
    skipped = []
    for name, server in manifest.get("mcpServers", {}).items():
        if not isinstance(server, dict):
            raise ValueError("MCP entries must be objects")
        if name in servers or server.get("disabled") is True:
            continue
        clean = clean_template(server)
        refs = re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", json.dumps(clean))
        if any(not os.environ.get(key) for key in refs):
            skipped.append(name)
            continue
        servers[name] = clean
    if servers or "mcpServers" in result:
        result["mcpServers"] = servers
    return result, skipped


def desktop_config_path() -> Path:
    if sys.platform == 'win32':
        return Path(os.environ.get('APPDATA', str(Path.home()/'AppData'/'Roaming')))/'Claude'/'claude_desktop_config.json'
    if sys.platform == 'darwin':
        return Path.home()/'Library'/'Application Support'/'Claude'/'claude_desktop_config.json'
    return Path.home()/'.config'/'Claude'/'claude_desktop_config.json'


def install(root: Path, claude_home: Path, mcp_config: Path, *, dry_run=False, overwrite_files=False, desktop_source=None, desktop_target=None) -> None:
    safe_path(claude_home)
    safe_path(mcp_config)
    settings_path = claude_home / "settings.json"
    safe_path(settings_path)
    existing, settings_before = read_json_snapshot(settings_path)
    defaults = render_paths(clean_template(read_json(root / "config/settings.example.json")), claude_home)
    local_env = existing.get("env", {})
    if not isinstance(local_env, dict):
        raise ValueError("Existing settings env must be an object")
    provider_env = {**os.environ, **local_env}
    cloud_flags = ("CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY")
    if any(k.startswith("ANTHROPIC_") and v for k, v in provider_env.items()) or any(str(provider_env.get(k, "")).lower() in {"1", "true", "yes", "on"} for k in cloud_flags):
        # Provider setup is one unit: do not fill another provider's missing
        # model mappings into an already configured provider environment.
        defaults["env"] = {k: v for k, v in defaults.get("env", {}).items()
                           if not k.startswith("ANTHROPIC_") and k not in
                           {"CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE"}}
        defaults.pop("model", None)
    settings = merge_missing(existing, defaults)
    original_mcp, mcp_before = read_json_snapshot(mcp_config)
    mcp, skipped = prepare_mcp(read_json(root / "config/mcp-servers.example.json"), original_mcp)
    desktop_bytes = None
    if desktop_source is not None:
        safe_path(desktop_source)
        _, desktop_bytes = read_json_snapshot(desktop_source)
        desktop_target = desktop_target or desktop_config_path()
        safe_path(desktop_target)
        desktop_before = desktop_target.read_bytes() if desktop_target.exists() else None
    # Preflight all sources and targets before changing any live files.
    files = []
    for name in ("CLAUDE.md", "statusline.js", "commands", "hooks"):
        source = root / name
        candidates = source.rglob("*") if source.is_dir() else [source]
        for file in sorted(candidates):
            if file.name == "README.md" or file.name.startswith(".") or not file.is_file():
                continue
            safe_path(file)
            target = claude_home / file.relative_to(root)
            safe_path(target)
            files.append((file, target))
    for source, target in files:
        write_file(target, source.read_bytes(), dry_run=dry_run, overwrite=overwrite_files)
    if settings != existing or not settings_path.exists():
        write_file(settings_path, json_bytes(settings), dry_run=dry_run, expected_before=settings_before)
    if mcp != original_mcp:
        write_file(mcp_config, json_bytes(mcp), dry_run=dry_run, expected_before=mcp_before)
    if desktop_bytes is not None:
        write_file(desktop_target, desktop_bytes, dry_run=dry_run, expected_before=desktop_before)
    if skipped:
        print("MCP entries awaiting local environment variables: " + ", ".join(sorted(skipped)))
    print("Dry run complete; no writes." if dry_run else "Restore complete. Restart Claude Code to load changed hooks.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite-files", action="store_true", help="replace reviewed repo files with backups; keep unrelated files")
    parser.add_argument("--claude-home", type=Path, default=Path.home() / ".claude")
    parser.add_argument("--desktop-config", type=Path, help="explicit local desktop JSON to restore with backup")
    parser.add_argument("--mcp-config", type=Path, default=Path.home() / ".claude.json")
    args = parser.parse_args()
    install(ROOT, args.claude_home.absolute(), args.mcp_config.absolute(),
            dry_run=args.dry_run, overwrite_files=args.overwrite_files, desktop_source=args.desktop_config)


if __name__ == "__main__":
    main()
