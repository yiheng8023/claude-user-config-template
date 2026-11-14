# claude-user-config-template

English | [简体中文](README.zh-CN.md)

Public-safe template for a private Claude Code user-configuration repository.
It supplies reusable structure and validation; real memory, personal guidance,
credentials, account state and machine paths belong in a private repository.
This is an independently usable Claude-specific implementation of the broader
public-template/private-overlay pattern.

## Start here

Requires Git, Python 3.11+ and Node.js 22+.

```bash
python -B scripts/verify.py --public
python -B scripts/install.py --dry-run
python -B scripts/install.py
```

First create your private derivative and replace the placeholder `CLAUDE.md`.
The installer adds missing files/settings and retains existing local files,
provider credentials, permission lists, plugin choices and MCP entries. It skips
credential placeholders and disabled MCP examples. Missing MCP environment
variables defer that server until configured locally.

After reviewing repository file changes:

```bash
python -B scripts/install.py --overwrite-files --dry-run
python -B scripts/install.py --overwrite-files
```

Explicit replacement backs up each differing existing file beside it using a
unique `.bak-<timestamp>` name. Extra local commands/hooks are never deleted.
Settings still use a missing-only merge. Backups can contain local secrets and
remain local, excluded from Git. Restore the corresponding backup to roll back.
Use idle configuration writers during restore: compare-before-write detects
ordinary conflicts but does not lock external provider tools. Restart Claude
Code after changing hooks. Linked sources/destinations, including junctions, are
refused. `--claude-home` and `--mcp-config` select explicit destinations.

Claude Desktop is a separate surface. Only an explicit
`--desktop-config <local-json-file>` restores it, with an existing-file backup.
The example desktop file is documentation; real desktop JSON stays local.

## Layout

```text
CLAUDE.md                         Replaceable public-safe global guidance
commands/README.md                Command placement guidance
config/settings.example.json      Provider-neutral settings
config/mcp-servers.example.json   Disabled MCP placeholder
config/plugins.example.json       Empty plugin set
config/repository-policy.json     Public/private verification policy
config/claude_desktop_config.example.json
hooks/settings-guard.js           Missing-env guardian (no permission grants)
hooks/guarded-fields.example.json Empty opt-in declaration example
memory/README.md                  Memory boundary placeholder
docs/                             Private setup and public/private boundaries
scripts/install.py                Additive installer; backed-up explicit replacement
scripts/plugins.py                User-scope plugin check/restore
scripts/verify.py                 Structure, JSON, plugin and public-safety checks
tests/                            Installer, validator and hook regression tests
statusline.js                     Placeholder status line
```

## Plugins and guardian

Fill the plugin manifest and matching `enabledPlugins` only in your private
configuration. Versions follow the active marketplace snapshot. Optional plugin
IDs can be placed in `optionalPlugins` and selected with `--include-optional`.
Existing local plugins are retained; project-scope installs do not satisfy a
user-scope restore.

```bash
python -B scripts/plugins.py --check
python -B scripts/plugins.py --install --dry-run
python -B scripts/plugins.py --install
```

The guardian is inert without a `hooks/guarded-fields.json` declaration. In a
private derivative, copy the empty example and declare a short `env` map. It
fills absent keys only and preserves explicit values, including `0`. Remove a
declaration to retire it. Permissions are never restored; nonempty legacy
`permissions_allow` is rejected. Deploy through the repository installer;
`node hooks/settings-guard.js --install` makes no writes and directs you there.
`--check` is read-only and returns nonzero for missing/invalid fields.
The template wires SessionStart only; a private derivative can also choose
ConfigChange. No memory upload or automatic Git push hook ships here.

## Tuning decisions for private derivatives

Keep decisions tied to the actual provider and workload. Prefer adjustable
`effortLevel` to an env override that locks out per-session effort changes.
A forced subagent model is a budget policy and overrides agent model choices;
make any quality/cost override explicit. Higher output ceilings reduce usable
context before compaction. Session status-line effort is configuration evidence,
not proof of third-party provider behavior. Scope permission grants to the
operations intended; a shell wrapper allow rule can grant much more than a
read-only operation. Verify these tradeoffs against the
[official environment reference](https://code.claude.com/docs/en/env-vars) and
[permission reference](https://code.claude.com/docs/en/permissions).

CC Switch is optional local provider/MCP tooling. This template does not require
a switcher or store its database, credentials, provider mappings or local gateway.

## Verification and repository boundary

```bash
python -B scripts/verify.py --public
python -B -m unittest discover -s tests -p "test_*.py" -v
node --test tests/*.test.js
```

CI runs the explicit public gate and behavioral checks on Windows, Linux and
macOS with Python 3.11/3.14 and Node 22. The public gate parses JSON, validates
plugin-set consistency, rejects extra memory files and concrete machine paths,
and checks selected credential formats without printing matched payloads.
It is not a complete confidential-information classifier.

For a private derivative, intentionally change `config/repository-policy.json`
to `private` and run `python -B scripts/verify.py --private`; replace its CI flag
too. That permits private memory and local paths while retaining JSON, plugin
and credential-format checks. Keep the derivative private. Public contributions
always pass `--public`; changing a local policy file does not bypass that CI gate.

[Public/private boundary](docs/public-private-boundary.md) ·
[Private setup](docs/private-repo-setup.md) ·
[Repository relationship](docs/relationship-map.md)
