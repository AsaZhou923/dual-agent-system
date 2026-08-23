# 系统安全边界

## 不进入 Git

- Buzz/Nostr 私钥、OpenAI/API token、macOS Keychain、DPAPI 文件；
- 真实 `.env`、Runner/Lead config、身份、公钥映射和事件 ID；
- SQLite、WAL/SHM、Relay dump、日志、任务正文和 Codex session；
- worktree、任务产物、Ollama manifests、GGUF/model blobs；
- Buzz、Node、Codex、Ollama 和其他第三方二进制。

## 权限

- Windows Codex Lead 是唯一最终验收者。
- Mac Supervisor 不获得 Relay owner/admin 私钥。
- Ornith 不直接接触 Buzz 或云端凭据。
- write task 在系统兼容 profile 中默认禁用。
- 任意 shell、无限制路径、免密 sudo 和未声明网络访问均不属于允许能力。

## 依赖

第三方依赖只在 `dependencies.lock.json` 中记录版本、commit 或 digest，不通过总仓库重新分发。更新依赖时必须重新运行组件 CI、兼容验证和真实链路验收。
