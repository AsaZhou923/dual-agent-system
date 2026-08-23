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
| Windows Lead | `components/windows-lead` | `bac76e62db4652f60e48a0771015f6ab82f1280c` |
| Mac Runner | `components/mac-runner` | `6dfff35a76ded101e72455bf3690492d5baf4b2d` |

两个目录都是 Git submodule。组件独立版本控制，总仓库 commit 表示一组明确的系统组合。

## 当前状态

- 两个组件的固定 commit 和各自 CI 已通过。
- `mac-job/v1` 的完整组件 schema 存在差异；本仓库定义了两边都接受的只读协商子集。
- 当前系统 profile 强制 `write=false`。
- Mac Runner 已包含 Homebrew `rg` PATH 修正及相关依赖说明，但修正后的真实跨机器任务尚未重新验收。
- 网络范围仍是 `intranet-only`。

## Clone

完整验证使用 Python 3.11 或更新版本。

```bash
git clone --recurse-submodules https://github.com/AsaZhou923/dual-agent-system.git
cd dual-agent-system
python3 scripts/verify_system.py
```

Windows Lead 是私有仓库；clone 前需要相应 GitHub 读取权限。已有 checkout 可执行：

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
- `docs/` — 架构、兼容、版本、部署和安全边界
- `deploy/buzz/` — Buzz upstream 部署引用

## Verification

完整验证要求 submodule 已初始化：

```bash
python3 scripts/verify_system.py
PYTHONPATH=components/windows-lead python3 -m unittest discover -s components/windows-lead/tests -v
```

Mac Runner 的完整测试依赖 macOS，应在 Mac 或其 GitHub Actions 中运行。

## Source of truth

- Windows 任务发布与账本逻辑：Windows Lead 仓库
- Mac 本地执行事实：Mac Runner 仓库及其运行时 SQLite
- 系统允许的组件组合和 wire contract：本仓库
- Buzz 消息：传输与审计证据，不是任一 Runner 的唯一数据库

本仓库不保存真实部署配置、凭据、身份、网络坐标、数据库、日志、模型或任务产物。
