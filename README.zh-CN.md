# claude-user-config-template

[English](README.md) | 简体中文

这是一个公开安全模板，用来帮助用户创建自己的私有 Claude Code 用户配置仓；
它不发布个人记忆、提示词、凭据、账号状态或本机运行时细节。

这是模板，不是真实用户配置。请把它作为安全起点，然后把真实 Claude 配置保存在自己的私有仓库里。
它是更通用模式的 Claude Code 专用实现：用公开安全模板承载可复用结构，用私有 overlay
保存真实记忆、偏好、凭据、本机路径、安装状态、备份、验证、恢复和回滚。其它 agent 也可以
采用同样思路，只是运行时文件和配置面不同，所以需要各自的模板。

## 从这里开始

| 你想做什么 | 入口 |
| --- | --- |
| 创建自己的私有 Claude Code 配置仓 | 把本仓作为公开安全起点 |
| 预览安装流程但不改本机 | `python -B scripts/install.py --dry-run` |
| 验证模板是否安全 | `python -B scripts/verify.py` |
| 理解整套系统 | [`open-resource-governance/docs/system-topology.md`](https://github.com/yiheng8023/open-resource-governance/blob/main/docs/system-topology.md) |

## 系统位置

本仓库是
[`open-resource-governance`](https://github.com/yiheng8023/open-resource-governance)
生态中的公开 Claude Code 专用配置模板链路。它展示的是更通用的 agent 环境可迁移模式，
不是说这套模式只适用于 Claude Code。

```text
open-resource-governance
  -> 负责整个仓库家族地图和公开/私有规则

claude-user-config-template
  -> 提供公开安全结构、占位符、安装预览和验证

私有 claude-user-config
  -> 负责真实 Claude Code 记忆、commands、hooks、本地安装策略和备份

codex-user-config-template
  -> 是 Codex 专用配置的兄弟公开模板
```

如果你需要 Claude Code 的安全起点，从本仓开始即可。若要理解更大的系统关系，请看总仓拓扑：
[`open-resource-governance/docs/system-topology.md`](https://github.com/yiheng8023/open-resource-governance/blob/main/docs/system-topology.md)。

## 它解决什么问题？

Claude Code 配置会逐渐变成个人工作环境：

- `CLAUDE.md` 全局指令；
- slash commands；
- hooks；
- status line 脚本；
- MCP 配置；
- Claude 桌面端配置；
- 精选记忆；
- 安装和恢复脚本。

这些东西很有价值，但也可能包含私有记忆、本机路径、账号假设、凭据或个人工作流偏好。
这个模板负责把可复用结构和私有状态分开。

## 仓库职责

```text
claude-user-config-template
  -> 公开安全结构、文档、占位示例、验证和搭建模型

private claude-user-config
  -> 真实 Claude Code 配置、记忆、hooks、commands、本地安装策略和备份
```

模板可以公开。真实配置仓除非经过逐文件脱敏和审查，否则应保持私有。

通用思路可迁移到其它 agent；本仓只实现 Claude Code 专用的文件和工作流形态。

## 本仓库提供什么

- 公开安全的 Claude Code 配置目录结构。
- 可替换的占位 `CLAUDE.md`。
- Claude Code 与 Claude 桌面端配置示例。
- 支持 `--dry-run` 的最小安装脚本。
- 会拒绝常见私有/密钥载荷的验证脚本。
- 公开/私有边界和私有仓搭建说明。

## 本仓库不负责什么

- 真实 Claude 记忆。
- 个人提示词、偏好、项目笔记、账号状态或本机路径。
- OAuth 状态、API key、密码、cookie、浏览器/session 状态、日志或缓存。
- 真实 MCP 凭据。
- 第三方 Skill 治理或资源发现。

## 快速开始

```bash
git clone https://github.com/yiheng8023/claude-user-config-template.git my-claude-user-config
cd my-claude-user-config
python -B scripts/verify.py
python -B scripts/install.py --dry-run
```

然后：

1. 替换 `CLAUDE.md` 中的占位内容。
2. 在 `commands/` 下加入自己的公开安全 slash commands。
3. 真实密钥放在本地环境变量或本地专用配置文件里。
4. 真实记忆放在你的私有仓，不要放进模板仓。
5. 提交前运行 `python -B scripts/verify.py`。

## 目录结构

```text
CLAUDE.md                         公开安全的全局指令起点
commands/README.md                slash command 放置说明
config/settings.example.json      Claude Code settings 占位示例
config/mcp-servers.example.json   MCP 环境变量引用占位示例
config/claude_desktop_config.example.json
                                  桌面端配置占位示例
docs/                             边界与搭建说明
hooks/README.md                   Hook 策略占位
memory/README.md                  记忆边界占位
scripts/install.py                支持 --dry-run 的最小安装器
scripts/verify.py                 公开安全与结构验证
statusline.js                     安全占位状态行
```

## 与整体体系的关系

本仓库是模块化配置体系中的公开模板链路：

- `claude-user-config` 是私有 Claude 配置真源。
- `codex-user-config` 是私有 Codex 配置真源。
- `codex-user-config-template` 是公开安全 Codex 模板。
- `open-resource-governance` 负责映射仓库家族和公开/私有边界。

## 安全边界

不要提交：

- 真实记忆；
- 凭据、token、OAuth 状态、cookie、密码或私钥；
- 本机路径；
- 账号专用 MCP 配置；
- 日志、缓存、session、telemetry 或历史记录；
- 私有项目笔记或个人偏好。

真实状态留在私有仓。本仓只放可复用结构。
