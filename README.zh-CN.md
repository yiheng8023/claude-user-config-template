# claude-user-config-template

[English](README.md) | 简体中文

公开安全的 Claude Code 用户配置模板，可独立创建私有配置仓。模板承载可复用结构与验证；
真实记忆、个人指令、凭据、账号状态和本机路径留在私仓。这是公开模板／私有 overlay 模式的 Claude 专用实现。

## 开始使用

需要 Git、Python 3.11+、Node.js 22+。先创建自己的私有派生仓并替换 `CLAUDE.md` 占位内容。

```bash
python -B scripts/verify.py --public
python -B scripts/install.py --dry-run
python -B scripts/install.py
```

默认只补缺失文件/字段，保留本机文件、供应商凭据、权限清单、插件选择和已有 MCP。
不部署凭据占位符或禁用的 MCP 示例；缺少本机环境变量的服务暂缓配置。
审查仓库更新后，需要显式覆盖文件时：

```bash
python -B scripts/install.py --overwrite-files --dry-run
python -B scripts/install.py --overwrite-files
```

每个不同的原文件会生成唯一 `.bak-<时间戳>` 备份；不删除额外 commands/hooks。
settings 仍然只补缺失，不重设本机偏好。备份可能含本机凭据，仅留在本机并被 Git 排除；
回滚时恢复对应备份。部署时让供应商工具等其它写入者空闲：写前比较能识别普通冲突，不等于锁住外部进程。
Hook 修改后重启 Claude Code。拒绝符号链接和 Windows junction；可用 `--claude-home` / `--mcp-config` 选择目标。

## CLI 与 Desktop

CLI 和 Desktop 本地 Code 标签页读取同一套 Claude Code 用户及项目配置。指令、权限规则、
Hooks、Skills、用户级插件集中维护。共享 MCP 在 `~/.claude.json` 或 `.mcp.json` 定义一次。
Chat 需要的本机 MCP 可用 `claude_desktop_config.json`，本地 Code 也会读取其中的 MCP。
`--desktop-config <本地JSON>` 用于显式恢复该本机文件并备份原件。

供应商路由、Desktop 的模型选择和文件夹权限模式可能不同。用同一目录打开两端，
通过 `/status` 对照配置和模型，再检查插件及 MCP。Desktop 应用和其 Code 运行时有独立版本。
参见 [Claude Code 桌面配置文档](https://code.claude.com/docs/en/desktop#shared-configuration)。

## 目录结构

```text
CLAUDE.md                         可替换的公开安全指令
commands/README.md                命令放置说明
config/settings.example.json      不绑定供应商的设置
config/mcp-servers.example.json   禁用的 MCP 占位示例
config/plugins.example.json       默认空插件集合
config/repository-policy.json     公私仓验证策略
config/claude_desktop_config.example.json
hooks/settings-guard.js           仅补缺失 env 的守护器
hooks/guarded-fields.example.json 默认空的显式声明示例
memory/README.md                  记忆边界说明
docs/                             公私边界与派生仓说明
scripts/install.py                增量安装／显式备份覆盖
scripts/plugins.py                用户级插件检查与恢复
scripts/verify.py                 结构、JSON、插件与公开边界校验
tests/                            安装器、校验器与 Hook 回归测试
statusline.js                     状态行占位
```

## 插件与守护器

私有清单和 `enabledPlugins` 只记录新机默认恢复的插件，完整目录交给 Claude 查找。
有明确用途的候选可放入 `optionalPlugins`，或在具体项目用 local scope 按需安装。
`--include-optional` 会选中全部可选项。用户级恢复面向本机共享的 Code 客户端。
支持账号同步的登录下，账号插件可单向同步到 CLI。
参见 [插件作用域](https://code.claude.com/docs/en/discover-plugins#choose-an-install-scope)与
[账号插件同步](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)。

```bash
python -B scripts/plugins.py --check
python -B scripts/plugins.py --install --dry-run
python -B scripts/plugins.py --install
```

守护器没有 `hooks/guarded-fields.json` 声明时不做修改。私仓中复制空样例并声明简短 env 清单即可启用：
只补不存在的键，保留已有值（包括 `0`）；退休某项时移除其声明。
不恢复任何权限，旧的非空 `permissions_allow` 会被拒绝。统一通过仓库安装器部署；
旧的 `node hooks/settings-guard.js --install` 不写文件，只提示新入口。
`--check` 只读，对缺失/非法字段返回非零。模板只挂 SessionStart；私仓可另外选择 ConfigChange。
公仓不提供自动上传记忆或自动推送 Git 的 Hook。

## 私仓调优思路

按实际供应商和工作负载选择：使用可调的 `effortLevel`，审慎使用会覆盖临时选择的 effort env；
强制子代理模型是预算策略，会覆盖代理自身选择，质量/成本切换应明确；提高输出上限会缩小压缩前可用上下文。
状态行 effort 只能证明会话配置，不能证明第三方服务端行为。权限按具体操作限定，shell 包装器规则可能放行整段脚本。
参照[官方环境变量](https://code.claude.com/docs/en/env-vars)与[权限说明](https://code.claude.com/docs/en/permissions)核对。

CC Switch 为可选的本机供应商/MCP 工具；模板不依赖它，不存其数据库、凭据、模型映射或本机网关。

## 验证和公私边界

```bash
python -B scripts/verify.py --public
python -B -m unittest discover -s tests -p "test_*.py" -v
node --test tests/*.test.js
```

CI 显式运行公开策略及行为检查，覆盖 Windows、Linux、macOS，Python 3.11/3.14 和 Node 22。
公开策略解析 JSON、校验插件集合、拒绝额外记忆文件和具体机器路径，扫描特定凭据格式且不打印命中载荷。
它不等于完整的机密信息分类器。

私有派生仓应明确把 `config/repository-policy.json` 改为 `private`，运行 `verify.py --private`，
并修改其自己的 CI 参数；这允许私有记忆和本机路径，仍保留 JSON、插件和凭据格式校验。
派生仓必须保持私有。对本公开模板的贡献始终通过 `--public`，修改策略文件无法绕过 CI 的显式公开检查。

[公私边界](docs/public-private-boundary.md) · [私仓搭建](docs/private-repo-setup.md) · [仓库关系](docs/relationship-map.md)
