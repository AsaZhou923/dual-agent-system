# 协议兼容矩阵

两个组件在各自仓库中独立定义 `mac-job/v1`。当前固定 commit 的差异如下：

| 项目 | Windows Lead | Mac Runner | 系统 profile |
| --- | --- | --- | --- |
| `focus` | 可选 | 必填且至少 1 项 | 必填且至少 1 项 |
| 扩展字段 | 接受 `summary`、`instructions`、`acceptance_criteria`、`metadata` | `additionalProperties=false`，不认识这些字段 | wire payload 禁止扩展字段 |
| `execution_route` | `auto`、`ornith`、`mac-codex`、`ornith-then-codex` | `auto`、`ornith`、`codex` | 仅 `auto`、`ornith` |
| `preferred_worker` | 任意非空字符串 | `ornith`、`codex` | `ornith`、`codex` |
| Git SHA | 接受大小写并规范化为小写 | 只接受小写 | 只允许小写 |
| 写入 | 有路径时可接受 | 受配置和路径门禁控制 | `write=false`、`allowed_paths=[]` |

因此组件自己的 schema 不是当前 wire contract 的直接替代品。Windows Lead 发送跨机任务时必须遵守根目录 system profile；Mac Runner 继续使用自己的更具体校验和执行门禁。

`scripts/verify_system.py` 使用合成 fixture 调用两个组件的真实 validator，并检查 system profile 的字段和枚举是否仍是双方接受的子集。

Mac Runner 已定义结构化 result schema，但 Windows Lead 当前按 Buzz 原 thread 与本地账本记录状态，还没有消费同一个机器可读 result schema。因此 result contract 保持 `shared-result-contract-pending`，不得假定两边已经完成结构化结果互操作。
