# PILOT-001：模拟器工程验证范围

> 文档类型：阶段 1 工程验证范围  
> 版本：1.0.0  
> 状态：Confirmed for Simulator Development  
> 决策日期：2026 年 8 月 13 日  
> 决策来源：项目发起人明确“没有设备，使用模拟即可”  
> 阶段 1A 临时项目责任人：高端阳  
> 对应 PRD：[PRD-001 教育机器人云平台](PRD-001%20教育机器人云平台.md)  
> 对应 RTM：[RTM-001 需求追踪矩阵](RTM-001%20教育机器人云平台需求追踪矩阵.md)  
> 责任与授权：[OWNER-001 责任人与 AI 执行授权](../governance/OWNER-001%20责任人与AI执行授权.md)  
> Gate 0：[需求与责任门禁](../gates/gate-0.yaml)（Passed 2026-08-13）
> W1 批准：[MVP-001](MVP-001%20阶段1A模拟器MVP范围.md) · [Issue #3 Approval](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3#issuecomment-5278164835)（Approved 2026-08-13）

## 一、CAPABILITY

在没有任何物理机器人的前提下，团队使用确定性 Robot Simulator 和两个纯合成机构租户，开发并验证阶段 1 设备云的云端闭环：设备身份协议、MQTT/HTTPS 接入、状态、Shadow、最小遥测/事件、单设备低风险命令、Web 查询、审计和租户隔离。

这是内部工程验证，不是真实机构试点、硬件验收、现场验收或生产准入。

## 二、确认的验证范围

### 1. 机构与场地

当前没有真实试点机构。为验证多租户和负向隔离，固定使用以下合成数据：

| 类型 | organization_code | 显示名称 | site_code | 用途 |
|---|---|---|---|---|
| 主验证租户 | `ORG-SIM-A` | 模拟试点机构 A | `SITE-SIM-A1` | 正常业务路径与故障场景 |
| 隔离对照租户 | `ORG-SIM-B` | 模拟隔离机构 B | `SITE-SIM-B1` | 跨机构/RLS/ACL/SSE/S3 负向验证 |

以上名称不得出现在客户材料、生产报表或对外演示中作为真实机构。

### 2. 虚拟设备组合

模拟器只使用一个协议组合，避免在没有硬件事实时伪造多型号兼容：

```yaml
model_code: SIM_EDU_ROBOT_V1
hardware_revision: sim-r1
bootloader_major: sim-1
firmware_major: sim-1
protocol_profile: device-v1
capability_profile: stage1-device-cloud-minimal
is_physical_hardware: false
production_supported: false
```

`hardware_revision`、`bootloader_major` 和 `firmware_major` 是模拟协议维度，不代表任何真实产品硬件或固件。

### 3. 模拟设备清单

| device_code | 机构 | 固定场景 | 主要验收 |
|---|---|---|---|
| `SIM-A-001` | ORG-SIM-A | 正常在线设备 | Provision、Birth、Shadow、Telemetry、Event、Command ACK |
| `SIM-A-002` | ORG-SIM-A | 重复与乱序 | Message ID/Sequence 幂等和旧 Shadow 拒绝 |
| `SIM-A-003` | ORG-SIM-A | 弱网与断线 | Will、Session、重连退避、本地缓冲与补传 |
| `SIM-A-004` | ORG-SIM-A | 时钟漂移 | Server Receive Time、异常时间隔离和顺序语义 |
| `SIM-B-001` | ORG-SIM-B | 对照租户正常设备 | 跨机构查询、Topic、命令和实时事件隔离 |
| `SIM-B-002` | ORG-SIM-B | 命令拒绝 | 过期、重复、非法参数和非法设备状态 |

错误 CA、过期/吊销证书、伪造 Device ID、跨 Topic 和超大 Payload 使用独立负向 Fixture，不作为可管理设备注册。

### 4. 阶段 1 Capability Profile

```yaml
enabled:
  - mqtt5_mtls_protocol
  - device_https_mtls_protocol
  - birth_and_last_seen
  - reported_shadow
  - minimal_telemetry
  - structured_device_event
  - offline_event_buffer
  - refresh_shadow_command
disabled:
  - content_package_install
  - teaching_session
  - interaction_wss
  - microphone_audio
  - ai_actions
  - diagnostic_bundle
  - bulk_command
  - ota
```

## 三、可验证与不可验证声明

### 1. 模拟器可以验证

- MQTT Topic、ACL、QoS、Session、Will 和 Envelope 契约。
- Device API mTLS 握手与证书身份映射的云端行为。
- Schema、大小、速率、重复、乱序、过期和幂等语义。
- Device Registry、Shadow、Telemetry、Event 和 Command 状态机。
- Organization/RLS、跨设备访问、Web 权限和审计。
- 固定弱网/断网/重连/时钟场景下的确定性服务行为。
- 可观测字段、错误分类和 Fail Closed 行为。

### 2. 模拟器不能证明

- 物理设备私钥是否安全存储或不可导出。
- 真实 OS/Runtime、进程守护、CPU、内存、磁盘和功耗。
- 真实 Wi-Fi/4G 驱动、NAT、睡眠唤醒和现场网络分布。
- 麦克风、扬声器、屏幕、灯光、电机和安全互锁。
- Bootloader、Updater、签名验证、可信时间、A/B、断电恢复和防回滚。
- 真实音频质量、ASR/LLM/TTS 端到端时延。
- 任何真实型号、硬件修订或固件版本的兼容性。

因此，模拟器测试通过后只允许陈述“云端实现符合模拟协议和契约”，不得陈述“已兼容真实机器人”“设备安全已验证”或“可投入现场/生产”。

## 四、门禁与允许的开发活动

### 1. Simulator Development Gate

进入阶段 1 模拟器开发前必须满足：

- Gate 0：已于 2026-08-13 通过；PRD/RTM 已批准，实名 Owner 已指定，W0 校验 28/28 通过。
- G2-Device：阶段 1 MQTT、Device API、领域、数据、命令和安全契约已冻结。
- Gate 3-Sim：仓库、环境、CI、Simulator、租户负向测试和工程骨架可执行。
- Simulator Conformance：W5a～W5c、W7a、W7b、W8a～W8b 对模拟协议通过。

G1-Device 保持 `blocked_no_physical_device`，不阻塞内部模拟器开发，但继续阻塞真实设备接入、客户现场试点和生产发布。

### 2. 允许

- 领域模型、数据库 Migration/RLS、API、Device Gateway、命令状态机和 Web 设备页面开发。
- Simulator、协议契约、故障注入、CI、可观测性和恢复演练。
- 使用纯合成数据的内部 Demo 和自动化验收。

### 3. 禁止

- 把 Simulator 证书当作生产 PKI 证明。
- 以模拟通过为依据冻结真实设备型号 Capability。
- 对外承诺现场网络、硬件、音频、OTA 或真实设备 SLO。
- 启用内容安装、教学、AI、诊断包、批量命令或 OTA。
- 将任何模拟 Tenant/Device 数据与真实用户、学生或机构数据混用。

## 五、模拟器验收场景

| Scenario ID | 场景 | 期望结果 |
|---|---|---|
| SIM-AC-001 | 每设备独立测试证书连接 | 身份映射到唯一 Device；错误/过期/吊销/伪造身份拒绝 |
| SIM-AC-002 | Birth、Reported Shadow、Telemetry、Event | 合法数据可查询；非法 Schema/身份/范围隔离 |
| SIM-AC-003 | 重复 Message ID/Command Idempotency Key | 只产生一个业务事实或命令 |
| SIM-AC-004 | 乱序 Sequence/旧 Shadow Version | 不覆盖新状态，产生明确拒绝/忽略结果 |
| SIM-AC-005 | 弱网、断网、Will、重连和补传 | 在线状态确定，缓冲事件重传且不重复计数 |
| SIM-AC-006 | `refresh_shadow` 正常/过期/非法状态 | 只允许白名单参数，ACK 状态完整可审计 |
| SIM-AC-007 | ORG-SIM-A 访问 ORG-SIM-B | REST、RLS、MQTT、SSE、对象访问全部拒绝 |
| SIM-AC-008 | PostgreSQL/Redis/EMQX 短时故障 | 按 PRD 故障矩阵降级，可恢复且不伪造成功 |

## 六、退出到真实设备验证的条件

一旦获得物理设备，必须新建或更新 Pilot Scope，并至少提供：

- 真实机构/内部硬件试验场地及授权联系人。
- `model_code × hardware_revision × bootloader_major × firmware_major`。
- 样机序列号、恢复镜像、调试方式和固件 Digest。
- 私钥存储、证书轮换/吊销、网络、进程、时钟和命令本地校验证据。
- 同一 G1/G2-Device Conformance Suite 的 HIL 报告。

只有 G1-Device 与 HIL 通过、阶段 1 P0 差异为零后，才可进入真实机构试点。OTA、内容和 AI 仍分别受自己的 G1/G2 门禁约束。

## 七、当前未决事项

| 项目 | 状态 | 说明 |
|---|---|---|
| AI 执行代理 | Confirmed | OpenAI Codex 已统一承担产品、技术、模拟设备协议、安全/隐私工程和 QA 执行；非人类批准人 |
| Product Owner | Confirmed for Stage 1A | 高端阳 |
| 技术 Owner | Confirmed for Stage 1A | 高端阳 |
| 设备 Owner | Confirmed for Stage 1A | 高端阳；只批准模拟协议，不签署实机事实 |
| 安全/隐私 Owner | Confirmed for Stage 1A | 高端阳；仅合成数据和非生产范围 |
| QA/验收 Owner | Confirmed for Stage 1A | 高端阳；已接受一人多角色独立性风险 |
| 真实试点机构 | Not selected | 当前明确不使用，不能以 ORG-SIM-A 替代 |
| 真实设备组合 | Blocked | 当前没有物理设备；G1-Device 不通过 |
| W1 Product/QA Approval | Approved | 高端阳批准本文与 MVP/Story Map/Acceptance/Demo 组成阶段 1A Simulator-only 基线 |
