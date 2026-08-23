# 双机 Agent 系统架构

## 责任链

```text
Human owner
    |
    v
Windows Codex Lead
    |
    | signed mac-job/v1 over Buzz
    v
Mac Codex Supervisor
    |
    | deterministic local actions
    v
Mac Runner
    |
    v
Ornith / Ollama Worker
```

- Windows Codex Lead 是唯一总负责人、最终验收者和主分支集成者。
- Buzz 是带签名的传输和审计层，不是执行状态的唯一事实源。
- Mac Codex Supervisor 是 Mac 节点必需的决策层，负责路由和节点验收。
- Mac Runner 管理确定性的校验、SQLite、幂等、worktree、权限、超时、测试和产物。
- Ornith 是受限的低成本 Worker，不直接接触 Buzz 或云端凭据。

## 状态与证据

Windows 侧以 `(job_id, attempt)` 为幂等键。事件发布只证明 Relay 接收，必须从原 thread 取得 `ACK`，再记录：

```text
SENT -> ACKED -> RUNNING -> VERIFYING -> DONE / FAILED / CANCELLED
```

发送结果不确定时进入 `SEND_UNCERTAIN`，该 attempt 不得自动重放。Mac Runner 使用独立的本地状态机和 SQLite 账本；两个账本承担不同节点的事实记录。

## 协议边界

两个组件当前各自包含 `mac-job/v1` schema，但约束不完全相同。总仓库的 `contracts/mac-job-v1-system.schema.json` 定义两边都接受的协商子集：

- `focus` 必填；
- 只允许小写 40 位 Git SHA；
- 当前仅允许 `write=false`；
- 当前路由只允许 `auto` 或 `ornith`；
- 不在 wire payload 中发送 Mac Runner 未声明的扩展字段。

扩大写入或路由能力必须同时更新两个组件、系统 profile、兼容 fixture 和 submodule 指针。

## 网络边界

当前部署范围是 loopback 或受信任内网。总仓库不保存真实 IP、域名、公钥、频道 ID、事件 ID、凭据或防火墙状态。公网入口、路由器转发或 Tunnel 属于独立安全阶段。
