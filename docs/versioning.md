# 版本与 submodule 规则

两个组件独立开发和发布，总仓库只固定一组经过验证的组合。

## 更新顺序

1. 在组件仓库完成修改、测试、commit 和 push。
2. 在总仓库中 checkout 需要的组件 commit。
3. 更新 `compatibility.json` 中的 commit。
4. 必要时更新系统 contract、fixture 和依赖锁。
5. 运行 `python3 scripts/verify_system.py`。
6. 只提交两个 gitlink、兼容元数据和相关文档。

不要在总仓库中使用未经审查的 `git submodule update --remote`。可复现版本由 gitlink 中的精确 commit 决定，而不是 submodule 当前 branch HEAD。

## Clone

```bash
git clone --recurse-submodules https://github.com/AsaZhou923/dual-agent-system.git
```

Windows Lead 是私有 submodule，clone 用户必须已经拥有该仓库的读取权限和 GitHub HTTPS 凭据。

## CI 权限

GitHub 默认的仓库 `GITHUB_TOKEN` 不能自动读取另一个私有仓库。因此默认 CI 只验证总仓库的 gitlink 和兼容元数据，不初始化 submodule。需要完整跨组件 CI 时，应创建只读 GitHub App 或最小权限 fine-grained token，并作为独立 secret 配置；不要复用个人长期 token。
