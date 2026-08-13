# THREAT-MODEL-001：教育机器人云平台威胁模型

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
> 执行编制：OpenAI Codex（非批准人）
>
> GitHub Work Item：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)
>
> 范围：[MVP-001](../product/MVP-001%20阶段1A模拟器MVP范围.md) · [PILOT-001](../product/PILOT-001%20模拟器工程验证范围.md)

本文使用 STRIDE、隐私伤害和滥用场景识别威胁。它定义必须满足的控制与验证，不声称控制已经实现、系统已经安全认证，或真实设备/生产环境已经验证。

## 一、范围与安全结论

W4 的可批准结论只限于安全边界设计：

- 阶段 1A 只处理合成租户、合成 Actor、模拟设备和非生产凭据。
- Web、Device、AI、Content、OTA、运维和供应链均视为独立攻击面。
- 浏览器、现场机器人、导入文件、MQTT Payload、AI 输入输出和第三方 Provider 全部不可信。
- 当前没有真实硬件、真实机构、个人数据、生产环境或真实 AI Provider，因此相应残余风险不能关闭。
- 无法完成身份、授权、审计或持久化时必须 Fail Closed，不得伪造成功。

## 二、系统与信任边界

```mermaid
flowchart LR
    U[Web User] -->|TB-01 HTTPS| E[Caddy / Web Edge]
    R[Untrusted Robot / Simulator] -->|TB-02 mTLS MQTT| M[EMQX]
    R -->|TB-03 mTLS HTTPS/WSS| G[Device / Interaction Gateway]
    E -->|TB-04 Cookie + CSRF| A[Modular Monolith API]
    M -->|TB-05 Authenticated Envelope| A
    G -->|TB-06 Typed Internal Call| A
    A -->|TB-07 RLS / Service Identity| P[(PostgreSQL)]
    A -->|TB-08 Scoped Credential| S[(S3 / Redis)]
    A -. disabled .->|TB-09 Minimal Typed Request| X[AI Provider]
    O[Release Operator] -. isolated .->|TB-10 Offline Signing| K[Content / OTA Key Domains]
```

| Boundary | 不可信输入/变化 | 必须控制 |
|---|---|---|
| TB-01 | 浏览器参数、上传、Cookie、Origin | TLS、HttpOnly/Secure/SameSite、CSRF、Schema、CSP、限流 |
| TB-02 | 证书、Client ID、Topic、Payload、连接风暴 | 独立设备身份、ACL、四方 ID 一致、大小/速率限制 |
| TB-03 | 设备 API/WSS、音频、Session Token | mTLS、短期绑定 Token、背压、超时、格式白名单 |
| TB-04 | 用户会话、角色、机构上下文 | 服务端 RBAC、重新认证、租户上下文不可由客户端决定 |
| TB-05 | 重复、乱序、过期、未知版本消息 | Schema、幂等、Sequence、Expiry、隔离队列 |
| TB-06 | 跨模块调用和错误映射 | 类型化 Port、最小权限、稳定错误、无隐式默认租户 |
| TB-07 | SQL、RLS 上下文、迁移、管理员路径 | 参数化查询、RLS、事务级租户上下文、审计 |
| TB-08 | 对象 Key、缓存污染、临时 URL | 机构前缀、短期签名、内容类型/大小校验、事实不以缓存为准 |
| TB-09 | Prompt Injection、Provider 输出、数据跨境 | 默认禁用、最小数据、结构校验、无工具权限、人工/规则 Fallback |
| TB-10 | 构建制品、Metadata、私钥、发布请求 | 内容与 OTA 分域、离线/HSM、双人审批、阈值签名、不可变审计 |

## 三、关键资产与攻击者

| Asset ID | 资产 | 影响 |
|---|---|---|
| AST-001 | Organization、角色与授权事实 | 跨租户泄漏或控制 |
| AST-002 | Web Session、CSRF 与恢复凭据 | 账户接管 |
| AST-003 | Device CA、证书、私钥与绑定码 | 伪造机器人或接管设备 |
| AST-004 | Device Registry、Shadow、事件和命令 | 错误现场动作与事实污染 |
| AST-005 | 审计、Outbox、Job 与幂等记录 | 否认、重复执行、不可追责 |
| AST-006 | 学生身份、回答、转写与音频 | 未成年人隐私和人身影响 |
| AST-007 | 题目、解析、脚本、权利与发布状态 | 侵权、有害内容和教学错误 |
| AST-008 | Prompt、模型配置、AI Run 与 Eval | 不受控生成、成本和不可复现 |
| AST-009 | Content/OTA 制品与签名 Metadata | 供应链攻击和设备失效 |
| AST-010 | Content/OTA 私钥 | 大范围永久信任破坏 |
| AST-011 | Secret、备份、日志与诊断包 | 横向移动和数据泄漏 |
| AST-012 | CI、依赖、镜像与发布权限 | 源码/制品供应链污染 |

攻击者包括未授权互联网用户、越权机构用户、恶意/失陷平台管理员、被物理接触的机器人、伪造设备、恶意内容供应方、Prompt Injection 输入、失陷第三方 Provider、依赖投毒者和误操作人员。Simulator 也按失陷设备处理，不能因其为测试组件而跳过 ACL。

## 四、强制安全不变量

| Control ID | 不变量 | 失败行为 |
|---|---|---|
| SEC-001 | 每个请求、消息、对象和事实都有服务端确定的机构边界 | 拒绝且不泄漏存在性 |
| SEC-002 | 每设备独立身份；证书、Client ID、Topic、Payload、Registry 一致 | 断开/拒绝并产生安全事件 |
| SEC-003 | 只有版本化白名单命令；参数、状态、Expiry、幂等在云端和设备端校验 | Publish 前拒绝；设备端再次拒绝 |
| SEC-004 | AI 只能返回类型化教学建议或 Action ID，无任意工具、MQTT、OTA、数据库权限 | 丢弃输出并进入确定性 Fallback |
| SEC-005 | 客观题评分、正确答案和教学状态不由模型修改 | 忽略模型结果并记录策略违规 |
| SEC-006 | 原始学生音频默认不持久化，不持续采集环境音视频 | 未获批准时不采集/不上送 |
| SEC-007 | Content 与 OTA 信任域、Key、审批和审计完全分离 | 构建/签名/发布失败 |
| SEC-008 | 普通服务、开发机和 CI 不持有 OTA Root/发布私钥 | Key 不配置；发现即事件处置 |
| SEC-009 | 高风险动作需要重新认证、Reason、影响预览、双人审批和不可变审计 | 任一条件缺失即不可达 |
| SEC-010 | Secret 不进入源码、日志、Trace、截图、Fixture 或 AI Provider | 脱敏/阻断并轮换暴露 Secret |
| SEC-011 | 未批准能力默认 `disabled/not_started`，入口不存在或明确拒绝 | 启动失败或稳定拒绝 |
| SEC-012 | 安全关键依赖不可确认时不使用过期扩权或本地猜测继续 | Fail Closed、可观测告警 |

## 五、威胁登记表

状态含义：`Required` 表示后续工作包必须实现并提供证据；`Blocked` 表示缺少真实事实或批准，当前能力必须关闭。

| Threat ID | STRIDE/伤害 | 场景 | 固有风险 | 必须控制/验证 | 状态 |
|---|---|---|---|---|---|
| THR-001 | S/E/I | ORG A 枚举、读取或控制 ORG B | 极高 | SEC-001；REST/RLS/MQTT/SSE/S3 双向负向套件 | Required |
| THR-002 | S | 盗用 Session、固定会话或 CSRF 发起写操作 | 高 | HttpOnly/Secure/SameSite、轮换、CSRF、Origin、再认证 | Required |
| THR-003 | E | UI 隐藏但直接接口允许高权限动作 | 极高 | 服务端 RBAC、资源级授权、拒绝副作用断言 | Required |
| THR-004 | T/I | XSS/恶意内容读取会话或篡改管理操作 | 高 | 输出编码、严格 CSP、禁止任意 HTML、上传隔离 | Required |
| THR-005 | S/E | 共享、伪造、过期或吊销设备凭据接入 | 极高 | SEC-002；mTLS、唯一身份、轮换/吊销测试 | Simulator Required / HIL Blocked |
| THR-006 | S/T | Topic、Payload 与证书 Device ID 不一致 | 极高 | Broker ACL + Gateway 四方一致校验 | Required |
| THR-007 | T/R | 重复、乱序、旧 Shadow 或迟到 ACK 改写事实 | 高 | Message ID、Sequence、Version、幂等与终态不回退 | Required |
| THR-008 | D | 重连风暴、超速遥测或超大消息耗尽服务 | 高 | 配额、大小/速率上限、有界退避、隔离和负载测试 | Required |
| THR-009 | E/T | 非白名单、批量或危险命令借低风险入口下发 | 极高 | SEC-003；Catalog、严格参数、状态、设备互锁 | Required |
| THR-010 | R | 审计失败后仍执行跨机构或控制动作 | 极高 | 审计预写/同事务事实；存储失败即阻断 | Required |
| THR-011 | I | 日志、Trace、错误或诊断包泄漏身份/Secret | 极高 | 字段白名单、集中脱敏、下载授权、短期保留 | Required / Diagnostic Blocked |
| THR-012 | T/E | 对象 Key/预签名 URL 越租户或长期有效 | 高 | 机构前缀、短 TTL、一次用途、下载审计 | Required |
| THR-013 | I/隐私 | 持续录音或原始学生音频被保存/发送 | 极高 | SEC-006；无批准则无入口、内存有界缓冲、数据扫描 | AI/Teaching Blocked |
| THR-014 | I/隐私 | 设备/学生标识与回答、转写被关联或重识别 | 极高 | 身份模式、最小化、用途隔离、聚合阈值、访问分层 | Teaching Blocked |
| THR-015 | T/E | Prompt Injection 诱导运维命令、文件或网络访问 | 极高 | SEC-004；无工具、Schema、Action Allowlist、双重互锁 | AI Blocked |
| THR-016 | T | 模型改变答案、评分、会话状态或生成有害内容 | 极高 | SEC-005、适龄策略、Eval、人工审核、确定性 Fallback | AI Blocked |
| THR-017 | I | Provider 保留、训练、跨区域或向子处理者披露数据 | 极高 | Provider 尽调、DPA、区域、零/短保留、字段扫描 | Provider Blocked |
| THR-018 | D/成本 | Prompt/输入造成 Token、音频或并发成本失控 | 高 | 预算、长度、并发、超时、熔断、缓存与告警 | AI Blocked |
| THR-019 | T/权利 | 无来源、侵权或 AI 草稿绕过审核发布 | 高 | Rights Record、`ai_draft`、人工审核、发布 Gate | Content Blocked |
| THR-020 | T | 内容包被篡改、替换或目标能力不兼容 | 极高 | Hash/签名/Manifest/Capability、原子激活/回滚 | G1/G2-Content Blocked |
| THR-021 | T/E | OTA 元数据、制品、Release Counter 或目标被篡改 | 极高 | 角色/阈值签名、Expiry、Counter、A/B、设备端验签 | G1/G2-OTA Blocked |
| THR-022 | E | 普通服务或单人同时构建、签名、批准、发布 OTA | 极高 | SEC-007/008/009；分域账号、离线签名、双人审批 | OTA Blocked |
| THR-023 | T/E | 恶意依赖、Action、镜像或 CI Token 污染供应链 | 极高 | 固定版本/Hash、最小权限、SBOM、扫描、制品签名 | Required |
| THR-024 | I/T | 备份、开发导出或测试数据复制扩大泄漏面 | 高 | 合成 Fixture、加密、访问/恢复审计、到期删除 | Required / Real Data Blocked |
| THR-025 | S/R | Simulator 结果被宣传为真实设备/合规/生产事实 | 高 | 强制真实性标记、证据分级、G1/HIL 独立门禁 | Required |
| THR-026 | D/T | PostgreSQL/Redis/EMQX 故障时伪造成功或状态漂移 | 高 | PostgreSQL 为事实源、Outbox/Job、降级状态、故障注入 | Required |

## 六、验证与证据路由

| 范围 | 后续主要证据 | 当前 W4 结论 |
|---|---|---|
| Web Session/RBAC/RLS | W6a/W6b/W7b1/W7b2 | 控制已定义，未实现 |
| Device PKI/MQTT/Command | W5a～W5c/W8a/W8b | Simulator 规则已定义；实机仍阻塞 |
| Data/Deletion/Retention | W6a/W7c | 合成数据政策可准备；真实数据未批准 |
| AI/Provider/Prompt | W5f/G1/G2-AI | Draft 可准备；调用与生产仍禁用 |
| Content Rights/Package | W5d/G1/G2-Content | 治理可准备；发布仍禁用 |
| OTA/Signing | W3/W5g/G1/G2-OTA/HIL | 设计威胁已记录；全部实现仍禁用 |
| Supply Chain | W7b3/W7b4 | 基础扫描存在；签名与来源证明待完成 |

## 七、评审与变更触发

以下任一变化必须重做威胁评审：引入真实设备/机构/个人数据、选择法域或 Provider、新增命令/工具、启用文件上传/诊断/内容/教学/AI/OTA、改变身份或部署边界、发生安全事件、依赖出现关键漏洞。

批准本文只确认威胁和控制基线合理，不接受尚未量化的生产残余风险。
