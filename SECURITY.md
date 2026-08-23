# Security policy

不要在 issue、pull request 或 commit 中提交真实凭据、节点身份、事件 ID、内网坐标、配置、数据库、日志、任务正文、模型文件或运行产物。

安全问题使用 GitHub Security Advisory 私下报告。如果凭据可能泄漏，应先轮换或撤销，再调查代码路径。

涉及协议、权限、subprocess、网络、凭据或写入能力的变更必须：

1. 先在所属组件仓库增加回归测试；
2. 更新本仓库兼容 profile 和 fixture；
3. 更新 submodule gitlink；
4. 运行完整系统验证；
5. 对真实链路使用新的 `(job_id, attempt)`，不得重放不确定 attempt。
