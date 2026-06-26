#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
CLAUDE_HOME = HOME / ".claude"


COPY_PATHS = [
    ("CLAUDE.md", "CLAUDE.md"),
    ("statusline.js", "statusline.js"),
    ("commands", "commands"),
    ("hooks", "hooks"),
]


def copy_path(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"would copy {src} -> {dst}")
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("README.md"))
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def render_settings(dry_run: bool) -> None:
    src = ROOT / "config" / "settings.example.json"
    dst = CLAUDE_HOME / "settings.json"
    text = src.read_text(encoding="utf-8").replace("__CLAUDE_HOME__", str(CLAUDE_HOME).replace("\\", "/"))
    if dry_run:
        print(f"would render {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for rel_src, rel_dst in COPY_PATHS:
        src = ROOT / rel_src
        dst = CLAUDE_HOME / rel_dst
        if src.exists():
            copy_path(src, dst, args.dry_run)
    render_settings(args.dry_run)
    print("install template complete" + (" (dry-run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
