# SECRET-INVENTORY-001：Secret、PKI 与签名密钥清单

> 版本：1.0.0
>
> 状态：Approved — Stage 1A Engineering Boundary
>
> 日期：2026 年 8 月 13 日
>
> 安全/隐私 Owner：高端阳（2026 年 8 月 13 日批准）
>
> 批准记录：https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5#issuecomment-5278502909
>
> GitHub Work Item：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)

本文只登记 Secret 类型、Owner、信任域和生命周期，不保存任何真实值、私钥、Token、密码、恢复码或可用证书。

## 一、环境与信任域

| Domain | 用途 | 允许存储 | 禁止事项 |
|---|---|---|---|
| DEV-LOCAL | 单开发机、纯合成数据 | 未跟踪 `.env`、运行时临时目录、开发专用 CA | 真实客户/生产 Secret；提交到 Git |
| CI-EPHEMERAL | PR/主分支验证 | GitHub Encrypted Secrets/OIDC、Job 临时文件 | Fork PR 暴露、长期静态云 Key、打印值 |
| TEST-SHARED | 共享非生产验证 | 待选 Secret Manager、测试专用 CA/账号 | 与生产复用、使用个人账号 |
| PROD | 未来生产 | 经批准的 Secret Manager/KMS/HSM | 当前创建或使用；普通服务读取签名 Root Key |
| CONTENT-SIGN | 内容签名 | 独立 KMS/HSM/离线域，具体方案待 G2-Content | 与 OTA、服务或开发 CA 复用 |
| OTA-OFFLINE | OTA Root/Targets 等角色 | 离线/HSM、阈值和分角色恢复，待 G1/G2-OTA | 开发机、CI、普通服务、单人全链 |

## 二、Secret 清单

| Secret ID | 类型/用途 | Domain | 运行时消费者 | 供应方式 | 轮换/吊销触发 | 当前状态 |
|---|---|---|---|---|---|---|
| SEC-WEB-001 | Web Session 签名/加密 | DEV/TEST/PROD 分离 | FastAPI Web Boundary | Secret Manager → 环境注入 | 泄漏、人员/环境变更、策略周期 | Dev placeholder only |
| SEC-DB-001 | PostgreSQL Service Credential | 每环境独立 | API/Worker/Migration 分账号 | Secret Manager/OIDC | 泄漏、权限变化、服务分拆 | Dev-only generated |
| SEC-REDIS-001 | Redis Credential/TLS Client | 每环境独立 | API/Worker | Secret Manager | 泄漏、拓扑变化 | Dev-only generated |
| SEC-S3-001 | S3/MinIO Scoped Credential | 每环境/服务独立 | API/Worker | 短期角色/OIDC 优先 | 泄漏、Bucket/Policy 变化 | Dev-only generated |
| SEC-MQTT-001 | EMQX Service Credential | 每环境/服务独立 | Device Gateway/Dispatcher | mTLS/Secret Manager | 泄漏、ACL/服务变更 | Dev-only generated |
| SEC-CA-001 | 开发 Device Root/Intermediate CA | DEV-LOCAL | 测试签发工具 | 本地生成、加密文件、忽略 Git | 测试结束、泄漏、重置 | Allowed non-production |
| SEC-DEV-001 | 模拟设备独立私钥/证书 | 单设备、单运行 | Robot Simulator | 运行时生成、结束撤销/删除 | 每次隔离运行、泄漏、吊销 Case | Allowed ephemeral |
| SEC-CI-001 | GitHub Actions Token/OIDC | CI-EPHEMERAL | 指定 Workflow | GitHub 自动/短期联合身份 | Job 结束、权限/Workflow 变化 | Enabled minimum read |
| SEC-OBS-001 | OTel/Sentry ingestion credential | 每环境独立 | 应用/Collector | Secret Manager | 泄漏、Endpoint/项目变更 | Not provisioned |
| SEC-AI-001 | AI Provider API Credential | Provider/区域/环境独立 | 仅未来 Provider Adapter | Secret Manager，禁止浏览器/设备 | 泄漏、Provider/模型/区域变化 | Prohibited / not provisioned |
| SEC-CONTENT-001 | Content signing private key | CONTENT-SIGN | 专用签名 Job/仪式 | KMS/HSM/离线待决 | 角色轮换、泄漏、算法/策略变化 | Prohibited / G2 blocked |
| SEC-OTA-ROOT-001 | OTA Root private key shares | OTA-OFFLINE | 离线 Root 仪式 | HSM/离线阈值待实机事实 | Root 轮换/恢复仪式 | Prohibited / G1 blocked |
| SEC-OTA-TARGETS-001 | OTA online/delegated signing | OTA-OFFLINE | 专用发布系统 | HSM/KMS + 阈值待决 | 角色/目标/泄漏变化 | Prohibited / G1 blocked |
| SEC-BACKUP-001 | 备份加密与恢复凭据 | 每环境独立 | 专用 Backup/Restore | KMS/HSM + break-glass | 演练、人员变化、泄漏 | Not provisioned |

## 三、最小权限与生命周期

1. 每个服务、环境、租户边界和用途使用独立身份；禁止共享万能 Key。
2. 优先使用短期联合身份/OIDC；必须使用静态 Secret 时记录创建、Owner、用途、到期和轮换。
3. Secret 只能在进程启动或请求所需边界内解密，不能进入前端 Bundle、设备 Payload 或 AI Context。
4. 日志记录 `secret_id`、版本和操作结果，不记录值、明文、完整证书或可重放材料。
5. 轮换采用双版本窗口并验证旧版本撤销；失败时回退服务配置，不恢复已泄漏 Secret。
6. 离职、权限变更、仓库/日志暴露、安全事件和环境销毁会触发立即吊销/轮换。
7. Break-glass 凭据必须封存、短期、双人启用、全程审计并在使用后轮换。

## 四、禁止进入普通服务的材料

- OTA Root、阈值 Share、内容签名 Root/发布私钥。
- CA Root 私钥、生产证书导出包和恢复助记材料。
- 数据库超级用户、云 Root/Owner、全 Bucket 或全 Broker 凭据。
- 真实 Provider 主账号 Key、生产 DPA/合同附件中的敏感信息。

## 五、验证要求

- Pre-commit 与 CI 执行 Secret 扫描；Git 历史同样扫描。
- 启动配置缺失或使用不安全生产默认值时失败。
- 日志/Trace/Sentry/测试报告执行 Canary Secret 与字段扫描。
- Fork PR 不获得写 Token 或环境 Secret。
- 任何真实 Secret 暴露按安全事件处理：吊销优先，删除 Git 内容不能代替轮换。
