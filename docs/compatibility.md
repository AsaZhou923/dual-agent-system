# 协议兼容矩阵

两个组件在各自仓库中独立定义 `mac-job/v1`。当前固定 commit 的差异如下：

| 项目 | Windows Lead | Mac Runner | 系统 profile |
| --- | --- | --- | --- |
| `focus` | 可选 | 必填且至少 1 项 | 必填且至少 1 项 |
| 描述扩展 | 规范化旧描述字段到 `context`，保留 `extensions` | 接受 `context`、`extensions` | 只允许 `context`、`extensions` |
| `execution_route` | `auto`、`ornith`、`mac-codex`、`ornith-then-codex` | `auto`、`ornith`、`codex`、`ornith-then-codex` | `auto`、`ornith`、`ornith-then-codex` |
| `preferred_worker` | 任意非空字符串 | `ornith`、`codex` | `ornith`、`codex` |
| Git SHA | 接受大小写并规范化为小写 | 只接受小写 | 只允许小写 |
| 权限 profile | 四档 policy v2，legacy adapter | 四档 policy v2，legacy adapter | 四档 policy v2 |
| standard write | worktree 授权，paths 可选缩小 | worktree、敏感路径、diff/文件数门禁 | task worktree，默认无逐文件审批 |
| operational | 5 个命名 capability，可在发送前按 Mac gate 阻断 | 5 个固定 handler，配置级 allowlist | 每个任务恰好 1 个 capability |
| privileged | 结构化 owner approval 且 approver 必须匹配 | approval 新鲜度、owner 和确定性摘要复核 | 结构化 approval 必填 |

因此组件自己的 schema 仍不是 system wire contract 的直接替代品。Windows Lead 发送跨机任务时必须遵守根目录 system profile；Mac Runner 继续执行更具体的 repo、capability binding、敏感路径和 owner approval 门禁。

`scripts/verify_system.py` 使用覆盖四个 profile 的合成 fixtures 调用 Windows validator、Mac schema validator 与 Mac normalizer，并检查 system profile、manifest、fixture、组件字段/枚举和 capability 集合保持一致。

当前 readiness 为 `policy-v2-compatible-cutover-pending`：组件源码与合同兼容已验证，但生产 Windows 的 `mac_job_contract_version=2` / `mac_permission_profiles_verified=true` 切换必须等待 Mac 部署和真实跨机 policy-v2 canary。

Mac Runner 已定义结构化 result schema，但 Windows Lead 当前按 Buzz 原 thread 与本地账本记录状态，还没有消费同一个机器可读 result schema。因此 result contract 保持 `shared-result-contract-pending`，不得假定两边已经完成结构化结果互操作。
