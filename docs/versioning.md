# 版本与 submodule 规则

两个组件独立开发和发布，总仓库只固定一组经过验证的组合。

## 更新顺序

1. 在组件仓库完成修改、测试、commit 和 push。
2. 在总仓库运行 `python3 scripts/update_component.py <component>`。
3. 审查新的 submodule gitlink 和 `compatibility.json` commit。
4. 必要时更新系统 contract、覆盖全部 permission profile 的 fixtures 和依赖锁。
5. 运行 `python3 scripts/verify_system.py`。
6. 只提交两个 gitlink、兼容元数据和相关文档。

不要在总仓库中使用未经审查的 `git submodule update --remote`。可复现版本由 gitlink 中的精确 commit 决定，而不是 submodule 当前 branch HEAD。

## Clone

```bash
git clone --recurse-submodules https://github.com/AsaZhou923/dual-agent-system.git
```

两个组件当前都是 Public submodule，普通 clone 和 GitHub-hosted CI 可以直接初始化。

## CI

Root CI 会递归 checkout 两个公开 submodule，验证 gitlink、兼容 manifest、四档 policy-v2 wire fixtures 和 Windows Lead 测试。Mac Runner 的完整执行测试仍由其 macOS workflow 负责。

如果未来任何组件改回 Private，Root CI 将不能继续匿名初始化该 submodule。此时应使用只读 GitHub App 或最小权限 fine-grained token，不要复用个人长期 token。

## 运行副本

版本提交和部署是两步。组件 push 后，总仓库必须更新 gitlink；总仓库 push 后，节点上的 MCP/launchd 也不会自动重启或切换源码路径。部署应继续遵循“测试 -> 单服务切换 -> 握手 -> 保留旧路径回滚”的顺序。
