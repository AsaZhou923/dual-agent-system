# 部署边界

总仓库不是单机安装目录。Windows 和 Mac 分别部署自己的组件，总仓库记录经验证的组合。

## Windows 节点

- 从 `components/windows-lead` 对应仓库部署代码和 Codex skill。
- 真实配置、DPAPI、SQLite、Buzz 二进制和日志保存在仓库外。
- Windows Codex Lead 保留最终验收权。

## Mac 节点

- 从 `components/mac-runner` 对应仓库部署 Runner、launchd 模板和 Supervisor 集成。
- 真实 TOML、Keychain、SQLite、worktree、产物、日志和 Ollama 模型保存在仓库外。
- 执行任务前验证 Homebrew、Python、ripgrep、Codex、Ollama 和模型身份。

## 切换顺序

```text
固定组件 commit
-> 节点本地测试
-> 生成仓库外配置
-> 更新单个服务
-> MCP/ACP 握手
-> read-only compatibility job
-> standard-worktree policy-v2 canary
-> 每个启用的 operational capability 独立 canary
-> 原 thread ACK/状态核验
-> Windows Lead 最终接受
```

不得通过移动或删除正在运行的旧目录完成切换。保留旧源码路径和服务定义，直到新版本握手和回滚验证完成。

当前组件 source pin 和 policy-v2 合同已验证；真实跨机器闭环仍需使用新的 attempt 重新验收。完成前 Windows 必须保持旧 wire gate，不能把总仓库的源码兼容状态等同于生产切换完成。
