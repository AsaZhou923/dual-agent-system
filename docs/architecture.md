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

两个组件各自包含 `mac-job/v1` schema，总仓库的 `contracts/mac-job-v1-system.schema.json` 定义两边都接受的严格 policy-v2 交集：

- `focus` 必填；
- 只允许小写 40 位 Git SHA；
- 权限 profile 为 `observe`、`standard-worktree`、`operational`、`privileged`；
- 普通代码任务一次授权整个 task worktree，`scope.paths` 只用于缩小范围；
- operational/privileged 每个任务只授权一个命名 capability，privileged 还必须绑定结构化 owner approval；
- `self-update-runner` 只能是 privileged 单 capability：固定注册源码仓库、远端/分支、安装目录、外部 one-shot helper 和 LaunchAgent；旧 Runner 在切换前进入 `VERIFYING`，新 Runner 从 helper outcome 恢复并结束同一 attempt；
- 当前路由只取两端交集：`auto`、`ornith` 或 `ornith-then-codex`；
- `context`/`extensions` 只承载描述信息，不参与权限判定；Mac Runner 可把其中的 summary、instructions 和 acceptance criteria 交给只读 worker，但它们不能扩大工具、路径、网络或写入权限。

Ornith 的只读工具循环达到固定轮数后，Runner 会丢弃膨胀的对话历史，只携带长度受限的工具证据发起无工具归纳，并以 findings result schema 约束输出。归纳仍不合法时任务失败关闭，不由 Runner 合成成功结果。

生产运行时从 legacy wire 切换到 policy v2 之前，仍必须完成 Mac 部署、账本迁移和真实跨机 canary；源码兼容状态不得替代生产验收。

Runner 自更新还有一次 bootstrap 边界：生产 Mac 必须先通过现有人工/安全部署通道安装 handler、外部 helper、固定配置 binding 和当前 `.source-commit`。Windows 只有在读取这些现场证据后才可把独立的 self-update verified gate 设为 true。源码 schema 支持、普通 permission-profile verified 或 Relay 健康都不能替代该证据。

## 网络边界

当前部署范围是 loopback 或受信任内网。总仓库不保存真实 IP、域名、公钥、频道 ID、事件 ID、凭据或防火墙状态。公网入口、路由器转发或 Tunnel 属于独立安全阶段。
