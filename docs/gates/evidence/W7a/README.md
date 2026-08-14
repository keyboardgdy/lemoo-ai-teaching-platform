# W7a 证据：本地 Compose 与开发 mTLS

日期：2026-08-14；范围：Stage 1A Simulator-only、本地开发、非生产。

## 交付

- `task bootstrap` 与独立 `task pki:generate` 创建或复用 `.data/pki/` 下的本地开发
  Root CA、EMQX ServerAuth 证书和非设备型 ClientAuth smoke 证书。
- CA、服务端和客户端使用三个不同的 3072-bit RSA 私钥；服务端 SAN 包含
  `localhost` 与 `127.0.0.1`；证书 Subject 显式标记 `LOCAL DEVELOPMENT ONLY`。
- 生成物全部受 `.data/` 忽略规则保护。EMQX 私钥通过 Compose secret 挂载，不进入
  YAML、环境变量、Git 或日志。
- EMQX MQTT TLS 映射为 loopback `localhost:58883`，配置 `verify_peer` 与
  `fail_if_no_peer_cert=true`；不向宿主机发布 1883。
- `task infra:up` 等待 PostgreSQL、Redis、MinIO、EMQX 健康后，自动执行真实 TLS
  smoke：无客户端证书必须被拒绝，开发 smoke 证书必须完成经 CA 与 hostname 验证的
  握手。
- Compose Runbook 固定首次启动、重复验证、Docker/容器恢复和凭证边界。

本证书不是 PILOT-001 的六台设备证书，不授予 Topic 权限。设备身份映射、每设备证书、
Client ID 绑定、ACL 与吊销属于 W8a/W8b。

## TDD

- RED Commit `86a55a2`：PKI 验收测试因 `cryptography` 与生成器不存在而在收集阶段
  失败。
- GREEN Commit `05dce7c`：实现 PKI、Compose secret、EMQX mTLS、正反 smoke 和本地
  Runbook；2 项 PKI 测试通过。
- Fix Commit `90a49f0`：实际 `task verify` 暴露 Orval 清空生成目录与 Vue 并行构建的
  竞态；保持检查集合不变，改由 `frontend:verify` 串行执行前端生成、检查和构建。

## 验证

- `task infra:config`：PASS。
- `task infra:up`：PASS；四个核心容器健康，EMQX mTLS 使用 TLS 1.3；无证书握手拒绝，
  smoke-client 握手通过。
- `task infra:down` 后再次 `task infra:up`：PASS；容器和网络重建、PKI 幂等复用、
  mTLS 再次通过；PostgreSQL named volume 中 6 台合成设备事实仍存在。
- `task verify`：PASS；后端 46 项、协议 27 项、前端 9 项，后端覆盖率 93.61%，
  前端 SFC 语句/行 99.24%、分支 92.30%、函数 100%；格式、Lint、类型、Build、
  Docs、Repo、Compose、Schema/OpenAPI 和 Orval 漂移检查全部通过。

本机 Windows 重建验证已完成。Linux CI 的真实 Compose 启动与 mTLS smoke 不能在 W7a
中修改既有 CI 门禁，将由紧随其后的 W7b1 Required Check 切片补齐；在该证据产生前，
W7a 不宣称跨平台退出条件完全通过。

本证据不授权生产部署、生产 CA/Secret、真实设备/机构/个人数据，也不启用 Content、
Teaching、AI、Diagnostics、Bulk Command 或 OTA。
