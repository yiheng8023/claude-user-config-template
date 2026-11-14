#!/usr/bin/env python3
"""Validate repository structure, JSON contracts and public/private boundaries."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['CLAUDE.md', 'README.md', 'README.zh-CN.md', 'statusline.js',
            'scripts/install.py', 'scripts/plugins.py', 'scripts/verify.py',
            'config/settings.example.json', 'config/mcp-servers.example.json',
            'config/plugins.example.json', 'config/claude_desktop_config.example.json',
            'config/repository-policy.json', '.github/workflows/validate.yml']
PATTERNS = [
    (re.compile(r'sk-ant-[A-Za-z0-9_-]{16,}'), 'Anthropic key'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), 'API key'),
    (re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}'), 'GitHub token'),
    (re.compile(r'AKIA[0-9A-Z]{16}'), 'AWS key id'),
    (re.compile(r'xox[baprs]-[A-Za-z0-9-]{10,}'), 'Slack token'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'private key'),
    (re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), 'JWT'),
    (re.compile(r'"(?:password|secret|token|api[_-]?key)"\s*:\s*"(?!<SET_LOCALLY|__|\$\{|<)[^"]{6,}"',re.I), 'literal credential'),
]
MACHINE_PATH = re.compile(r'\b[A-Za-z]:[\\/](?![<_*])[^\s"\'<>]+|/(?:Users|home)/(?!(?:<|__|\*))[A-Za-z0-9_.-]+/')
FORBIDDEN = {'projects','sessions','shell-snapshots','session-env','telemetry','cache','backups'}
SUFFIXES = {'.db','.sqlite','.pem','.key','.p12','.pfx','.log'}


def files(root):
    if (root/'.git').exists():
        proc=subprocess.run(['git','-C',str(root),'ls-files','-z','--cached','--others','--exclude-standard'],capture_output=True,check=True)
        return sorted({root / p for p in proc.stdout.decode('utf-8').split('\0') if p})
    return sorted(p for p in root.rglob('*') if '.git' not in p.parts and '__pycache__' not in p.parts and p.is_file())


def validate(root: Path, public: bool) -> list[str]:
    errors=[]
    for name in REQUIRED:
        if not (root/name).is_file(): errors.append('missing: '+name)
    documents={}
    for file in files(root):
        rel=file.relative_to(root).as_posix()
        if file.is_symlink() or (hasattr(file,'is_junction') and file.is_junction()):
            errors.append('linked file: '+rel);continue
        if not file.is_file(): continue
        try: text=file.read_text(encoding='utf-8')
        except UnicodeError:
            errors.append('unexpected binary/non-UTF8 file: '+rel);continue
        for regex,label in PATTERNS:
            if regex.search(text): errors.append(label+': '+rel)
        if file.suffix=='.json':
            try: documents[rel]=json.loads(text)
            except ValueError: errors.append('invalid JSON: '+rel)
        if public:
            if rel.lower().startswith('memory/') and rel!='memory/README.md': errors.append('private memory: '+rel)
            if any(part.lower() in FORBIDDEN for part in file.relative_to(root).parts) or file.suffix.lower() in SUFFIXES: errors.append('private runtime file: '+rel)
            if MACHINE_PATH.search(text): errors.append('machine path: '+rel)
    settings=documents.get('config/settings.example.json',{})
    manifest=documents.get('config/plugins.example.json',{})
    if not isinstance(settings,dict) or not isinstance(manifest,dict):
        errors.append('settings/plugin manifest must be objects');return errors
    plugins=manifest.get('plugins',[]);enabled=settings.get('enabledPlugins',{})
    if not isinstance(plugins,list) or not all(isinstance(p,str) and re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+',p) for p in plugins):
        errors.append('invalid plugin IDs')
    elif len(plugins)!=len(set(plugins)) or not isinstance(enabled,dict) or set(plugins)!={k for k,v in enabled.items() if v is True}:
        errors.append('plugin manifest and enabledPlugins differ')
    optional=manifest.get('optionalPlugins',[])
    if not isinstance(optional,list) or not all(isinstance(p,str) and re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+',p) for p in optional):
        errors.append('invalid optional plugin IDs')
    elif len(optional)!=len(set(optional)) or (isinstance(plugins,list) and any(p in plugins for p in optional)):
        errors.append('duplicate default/optional plugin IDs')
    if public and (settings.get('env') or settings.get('model') or settings.get('enabledPlugins')):
        errors.append('public settings must be provider-neutral and have no enabled plugin set')
    for name,data in documents.items():
        if name.startswith('config/') and not isinstance(data,dict): errors.append('JSON object required: '+name)
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--public',action='store_true');mode.add_argument('--private',action='store_true')
    args=parser.parse_args()
    policy=json.loads((ROOT/'config/repository-policy.json').read_text(encoding='utf-8'))
    if policy.get('visibility') not in {'public','private'}: raise SystemExit('invalid repository visibility policy')
    public=args.public or (not args.private and policy['visibility']=='public')
    errors=validate(ROOT,public)
    for error in errors: print('FAIL '+error)
    print(f"Verification {'failed' if errors else 'passed'} ({'public' if public else 'private'} policy)")
    return 1 if errors else 0

if __name__=='__main__': raise SystemExit(main())
