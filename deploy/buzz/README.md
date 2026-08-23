# Buzz deployment reference

Buzz 是外部传输依赖，不作为本系统的第三个自研 submodule。当前固定版本记录在根目录 `dependencies.lock.json`。

部署时使用固定 Buzz upstream commit 中的 `deploy/compose/compose.yml`，并把真实 `.env` 保存在源码和总仓库之外。不要把运行中的 Compose `.env`、数据库卷、对象存储、Git 数据卷或 Relay dump 复制到本仓库。

初始网络范围只能是：

- 本机 loopback；或
- 受信任的 RFC1918 私有 LAN，配合最小 Windows/macOS 防火墙范围。

跨机器使用 TLS 时，两端必须信任证书。公网 DNS、端口转发和 Tunnel 需要单独的认证、访问控制和外部验证，不能由此目录自动启用。
