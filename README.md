# Dual Agent System

双机 AI Agent 协作系统的集成、兼容和版本锁定仓库。

```text
Windows Codex Lead
  -> Buzz
  -> Mac Codex Supervisor
  -> Mac Runner
  -> Ornith / Ollama Worker
```

## 组件

| 组件 | 仓库 | 当前固定 commit |
| --- | --- | --- |
| Windows Lead | `components/windows-lead` | `1956d5da42a0660bace0943c72bf299bc1cf690b` |
| Mac Runner | `components/mac-runner` | `a31a1701996f686cff3893ea2359f77c91ef1e2c` |

两个目录都是公开 Git submodule。组件独立版本控制，总仓库 commit 表示一组明确的系统组合。

## 当前状态

- 两个组件固定到已发布 commit；本地组件/合同验证已通过，GitHub-hosted CI 以对应 commit status 为准。
- `mac-job/v1` system profile 已升级为两端都接受的严格 policy v2 交集。
- `observe`、`standard-worktree`、`operational`、`privileged` 四档 profile、canonical `codex` route 和五个命名 operational capability 已通过组件 validator fixture 验证。Windows 组件额外支持的 network-free `prepare-registered-repo` 尚未进入当前 Mac source pin 的系统交集。
- 源码兼容、Windows sender 切换和完整跨机验收是三个独立门禁：Windows 生产运行时已读回 contract/profile `2/true`，但真实 canary 仍在 Mac 侧临时目录与配置不变性证据上失败，因此总仓 readiness 继续保持 pending。
- Buzz 固定到用户 fork 的 `6793b4ef98b11a64e4ead1e88ee5ec33ebe3f002`，包含 NIP-OA owner 保留和 observer NIP-44 明文上限修复。
- 网络范围仍是 `intranet-only`。

## Clone

完整验证使用 Python 3.11 或更新版本。

```bash
git clone --recurse-submodules https://github.com/AsaZhou923/dual-agent-system.git
cd dual-agent-system
python3 scripts/verify_system.py
```

两个组件仓库当前都是 Public，普通 clone 可以直接初始化。已有 checkout 可执行：

```bash
git submodule update --init --recursive
```

## Repository layout

- `components/` — 固定 commit 的 Windows Lead 与 Mac Runner
- `contracts/` — 当前系统协商协议
- `fixtures/` — 两个组件都接受的合成任务
- `compatibility.json` — component、protocol 和 readiness 状态
- `dependencies.lock.json` — 不 vendoring 的第三方基线
- `scripts/verify_system.py` — gitlink 与跨组件契约验证
- `scripts/update_component.py` — 拉取组件 `main` 并同步本地 gitlink/兼容 manifest，不自动 commit 或 push
- `docs/` — 架构、兼容、版本、部署和安全边界
- `deploy/buzz/` — Buzz upstream 基线与固定修复 commit 的部署引用

## Verification

完整验证要求 submodule 已初始化：

```bash
python3 scripts/verify_system.py
python3 -m unittest discover -s tests -v
PYTHONPATH=components/windows-lead python3 -m unittest discover -s components/windows-lead/tests -v
```

Mac Runner 的完整测试依赖 macOS，应在 Mac 或其 GitHub Actions 中运行。

## 日常更新工作流

Git 不会把组件仓库的新 commit 自动写进总仓库。更新分为两次明确的版本提交。

先在组件自己的 checkout 中修改、测试并 push：

```bash
cd /path/to/dual-agent-windows-lead
git status --short --branch
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
git add <明确文件>
git commit
git push
```

再让总仓库固定新的组件 commit：

```bash
cd /path/to/dual-agent-system
python3 scripts/update_component.py windows-lead
git diff --submodule=log
python3 scripts/verify_system.py
git add components/windows-lead compatibility.json
git commit
git push
```

Mac 组件使用同样流程，把参数改为 `mac-runner`。一次检查两个组件可使用：

```bash
python3 scripts/update_component.py all
```

辅助脚本只更新本地 checkout 和 `compatibility.json`，不会自动提交或推送；这样兼容 contract 变化仍需要人工 review。

## Git 与运行环境

`git push` 只更新 GitHub，不会自动替换正在运行的 MCP、launchd、配置或 skill 安装副本。生产环境应运行仓库 checkout，或使用经过验证的安装/同步步骤。当前 Windows MCP 仍使用旧运行目录时，在 GitHub 修改代码不会自动部署到该进程；切换必须单独完成握手和回滚验证。

## Source of truth

- Windows 任务发布与账本逻辑：Windows Lead 仓库
- Mac 本地执行事实：Mac Runner 仓库及其运行时 SQLite
- 系统允许的组件组合和 wire contract：本仓库
- Buzz 消息：传输与审计证据，不是任一 Runner 的唯一数据库

本仓库不保存真实部署配置、凭据、身份、网络坐标、数据库、日志、模型或任务产物。
