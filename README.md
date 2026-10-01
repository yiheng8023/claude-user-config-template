# claude-user-config-template

English | [简体中文](README.zh-CN.md)

Public-safe template for creating a private Claude Code user-configuration
repository without publishing personal memory, prompts, credentials, account
state, or machine-local runtime details.

This is a template, not a live user configuration. Use it as a safe starting
point, then keep your real Claude configuration in your own private repository.
It is a Claude Code-specific implementation of a more general pattern: keep an
AI/agent working environment portable through a public-safe template plus a
private overlay for real memory, preferences, credentials, local paths,
installed state, backup, verification, restore, and rollback. Other agents may
need different templates because their runtime files and setup surfaces differ.

## Start here

| If you want to... | Go here |
| --- | --- |
| Create your own private Claude Code config repo | Use this template as the public-safe starting point |
| Preview setup without changing your machine | `python -B scripts/install.py --dry-run` |
| Verify the template | `python -B scripts/verify.py` |
| Understand this template's boundary | [Repository Role](#repository-role) |

## Independent Template Context

This repository is an independently usable public Claude Code-specific
configuration template. It demonstrates the broader agent-environment
portability pattern through repository-owned structure, validation, and setup
guidance; the pattern itself is not limited to Claude Code.

```text
claude-user-config-template
  -> provides public-safe structure, placeholders, dry-run setup, and validation

private claude-user-config
  -> owns real Claude Code memory, commands, hooks, local install policy, and backups

codex-user-config-template
  -> is the sibling public template for Codex-specific configuration
```

Use this repository as a self-contained safe Claude Code starting point.

## What problem does this solve?

Claude Code configuration can grow into a real personal operating environment:

- `CLAUDE.md` global instructions;
- slash commands;
- hooks;
- status line scripts;
- MCP configuration;
- desktop-client configuration;
- curated memory;
- install and restore scripts.

That environment is valuable, but it can contain private memory, local paths,
account assumptions, credentials, or personal workflow choices. This template
separates reusable structure from private state.

## Repository Role

```text
claude-user-config-template
  -> public-safe structure, docs, placeholder examples, validation, and setup model

private claude-user-config
  -> real Claude Code configuration, memory, hooks, commands, local install policy, backups
```

The template may be public. Your real configuration repository should remain
private unless every file has been deliberately declassified.

The general idea is portable across agents; this repository only implements the
Claude Code-specific file and workflow shape.

## What This Repository Provides

- A public-safe Claude Code configuration layout.
- Placeholder `CLAUDE.md` guidance that users can replace.
- Example Claude Code and Claude desktop config files.
- A minimal installer with `--dry-run`.
- A verification script that rejects common private/secret payloads.
- Documentation for public/private boundaries and private setup.

## What This Repository Does Not Own

- Real Claude memory.
- Personal prompts, preferences, project notes, account state, or local paths.
- OAuth state, API keys, passwords, cookies, browser/session state, logs, or caches.
- Real MCP credentials.
- Third-party Skill governance or resource discovery.

## Quick Start

```bash
git clone https://github.com/yiheng8023/claude-user-config-template.git my-claude-user-config
cd my-claude-user-config
python -B scripts/verify.py
python -B scripts/install.py --dry-run
```

Then:

1. Replace placeholder text in `CLAUDE.md`.
2. Add your own public-safe slash commands under `commands/`.
3. Keep real secrets in local environment variables or local-only config files.
4. Keep real memory in your private repo, not in this template.
5. Run `python -B scripts/verify.py` before committing.

## Layout

```text
CLAUDE.md                         Public-safe starter global guidance
commands/README.md                Slash command placement guide
config/settings.example.json      Placeholder Claude Code settings
config/mcp-servers.example.json   Placeholder MCP env-var references
config/claude_desktop_config.example.json
                                  Placeholder desktop config
docs/                             Boundary and setup guidance
hooks/README.md                   Hook policy placeholder
memory/README.md                  Memory boundary placeholder
scripts/install.py                Minimal installer with --dry-run
scripts/verify.py                 Public-safety and structure validation
statusline.js                     Safe placeholder status line
```

## Optional Sibling Repositories

These optional sibling repositories illustrate the same
public-template/private-overlay pattern:

- `claude-user-config` is the private Claude configuration source.
- `codex-user-config` is the private Codex configuration source.
- `codex-user-config-template` is the public-safe Codex template.

## Optional Companion Tooling · CC Switch

If you juggle multiple providers or accounts, you might pair this template's structure with a local provider/account switcher. One widely used open-source option is **CC Switch** (<https://github.com/farion1231/cc-switch>): it keeps per-provider environment values (`ANTHROPIC_BASE_URL`, credentials, model mapping) in a local database and injects the active provider into `~/.claude/settings.json` — and, for the desktop client, serves third-party inference through a local gateway. Its local MCP table can also act as the source of truth pushed into `~/.claude.json` (Claude Code) and `~/.codex/config.toml` (Codex).

A common division of labour for multi-provider users:

```text
this template           -> public-safe structure, placeholder env files, validation
CC Switch (optional)    -> live provider env injection + MCP source of truth
your private repository -> real memory, credential references, backups
```

This template does **not** depend on CC Switch or any specific switcher — a restored configuration works standalone; treat it as an optional companion, not a requirement.

## Safety Boundary

Never commit:

- real memory;
- credentials, tokens, OAuth state, cookies, passwords, or private keys;
- local machine paths;
- account-specific MCP configuration;
- logs, caches, sessions, telemetry, or history;
- private project notes or personal preferences.

Use a private repository for real state. Use this repository for reusable structure.
