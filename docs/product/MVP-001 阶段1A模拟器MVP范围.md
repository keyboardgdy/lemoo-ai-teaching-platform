# MVP-001：阶段 1A 模拟器 MVP 范围

> 文档类型：W1 已批准产品范围基线
>
> 版本：1.0.0
>
> 状态：Approved — Stage 1A Simulator-only
>
> 建立日期：2026 年 8 月 13 日
>
> Product Owner / QA Owner：高端阳（2026 年 8 月 13 日批准）
>
> 执行编制：OpenAI Codex（非批准人）
>
> GitHub Work Item：[#3](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3)
>
> 批准记录：[Issue #3 Approval](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3#issuecomment-5278164835)
>
> 上位需求：[PRD-001](PRD-001%20教育机器人云平台.md) · [RTM-001](RTM-001%20教育机器人云平台需求追踪矩阵.md) · [PILOT-001](PILOT-001%20模拟器工程验证范围.md)
>
> 配套产物：[STORY-MAP-001](STORY-MAP-001%20阶段1A用户故事地图.md) · [ACCEPTANCE-001](ACCEPTANCE-001%20阶段1A验收矩阵.md) · [DEMO-001](DEMO-001%20阶段1A合成数据演示脚本.md)

本文冻结 W1 的已批准范围与成功判据，不代表业务功能已经实现。高端阳已同时以 Product Owner 和 QA/验收 Owner 身份批准 `1.0.0`；任何实现证据仍须由后续工作包产生。

## 一、CAPABILITY

面向内部工程团队、机构管理员和设备运维角色，使用两个纯合成机构、六台确定性模拟设备和一个虚拟协议组合，证明阶段 1A 设备云能够形成以下最小闭环：

```text
授权与机构隔离
-> 设备注册、Provision、绑定和独立身份
-> MQTT/HTTPS 接入
-> 在线状态、Shadow、遥测、事件与基础告警
-> 单设备 refresh_shadow 命令
-> ACK、最终结果与审计
-> 重复/乱序/弱网/故障恢复
```

这项能力改变的是工程确定性：团队可以在没有物理设备时验证云端契约、状态机、权限和故障处理。它不证明客户确有该痛点，不证明真实硬件兼容，也不产生生产准入。

## 二、产品诊断与 Go/No-Go

| 问题 | W1 结论 | 证据状态 |
|---|---|---|
| 为谁 | 首先服务内部工程验证；未来用户为机构管理员和设备运维 | Actor 已定义；真实用户研究缺失 |
| 痛点 | 设备接入、状态和命令闭环尚无可重复工程证据 | 工程缺口明确；客户痛点频率/成本未量化 |
| 为什么现在 | 当前没有物理设备，但后续契约、领域和 Simulator 工作必须有唯一范围 | 用户明确选择 Simulator-only |
| 最小证明 | 两个合成租户、六台模拟设备、一个低风险命令、完整负向与降级路径 | 本文冻结候选范围；实现待后续工作包 |
| 反目标 | 题库、教学、AI、OTA、诊断包、真实机构、真实设备、生产 | 必须持续 Fail Closed |
| 如何知道有效 | 7 个 P0 Story 的 28 类验收场景全部可重复通过，运行指标达到第四章阈值 | 当前仅定义；尚未测量 |

W1 产品判断：

- **Go**：继续内部、合成、非生产的阶段 1A 工程准备。
- **No-Go**：真实机构试点、真实硬件兼容、产品市场价值、生产 SLO、内容、教学、AI、诊断和 OTA。
- HYP-001～005、PM-001～007 继续保持未知；不得用 Simulator Demo、测试覆盖率或接口数量代替客户证据。

## 三、固定验证资产

### 1. 合成机构与场地

| Organization | Site | 用途 | 真实性标记 |
|---|---|---|---|
| `ORG-SIM-A` | `SITE-SIM-A1` | 主正常路径、异常和弱网场景 | `synthetic=true` |
| `ORG-SIM-B` | `SITE-SIM-B1` | 对照路径及跨机构负向验证 | `synthetic=true` |

### 2. 唯一虚拟组合

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

全部版本字段只描述模拟协议维度。不得将其映射、宣传或推断为任何真实型号、硬件修订、Bootloader 或固件版本。

### 3. 固定模拟设备

| Device | Tenant | 主要职责 |
|---|---|---|
| `SIM-A-001` | ORG-SIM-A | 正常接入、状态、遥测、事件和命令 |
| `SIM-A-002` | ORG-SIM-A | 重复、乱序和旧 Shadow |
| `SIM-A-003` | ORG-SIM-A | 弱网、断线、Will、重连和补传 |
| `SIM-A-004` | ORG-SIM-A | 时钟漂移和服务端接收时间 |
| `SIM-B-001` | ORG-SIM-B | 对照租户正常设备与跨租户隔离 |
| `SIM-B-002` | ORG-SIM-B | 命令过期、重复、非法参数和非法状态 |

每台模拟设备必须使用独立测试身份。负向证书/身份只作为 Fixture，不登记为可管理设备。

## 四、范围与成功指标

### 1. P0 产品范围

W1 固定 7 个 P0 Story、12 项 P0 Requirement：

| Capability | P0 Story | Requirement |
|---|---|---|
| CAP-GOV | `ST-GOV-001`、`ST-GOV-002` | `PRD-GOV-001`～`003` |
| CAP-DEV | `ST-DEV-001`、`ST-DEV-002`、`ST-DEV-003` | `PRD-DEV-001`～`006` |
| CAP-OPS | `ST-OPS-001`、`ST-OPS-002` | `PRD-OPS-001`～`003` |

`ST-REL-002` 是 P1 工程支撑，用于 Gate 3-Sim 前的恢复准备，不属于首个用户闭环。所有 Story 的唯一分类见 STORY-MAP-001。

### 2. W1 规格完成指标

| Metric ID | 指标 | W1 通过阈值 |
|---|---|---:|
| W1-SPEC-001 | 现有 Story 分类覆盖 | 19/19，且每个 Story 只属于 P0/P1/Out 一类 |
| W1-SPEC-002 | P0 Story 追踪覆盖 | 7/7 均映射 Requirement、PRD Acceptance、计划 Test/Evidence |
| W1-SPEC-003 | P0 Requirement 覆盖 | 12/12，无新增孤立 Requirement |
| W1-SPEC-004 | P0 路径覆盖 | 28/28：每个 P0 Story 都有 Normal/Permission/Exception/Degraded |
| W1-SPEC-005 | 范围真实性 | 所有租户/设备均标记 Synthetic/Simulator；真实实体数量为 0 |
| W1-SPEC-006 | 未来能力泄漏 | P0/P1 中 Content/Teaching/AI/Diagnostic/OTA Story 数为 0 |

### 3. 后续运行验收指标

这些指标由后续契约、Simulator、业务切片和 W9a 产生证据；写入本文不等于已经达到。

| Metric ID | 运行目标 | 测量方法 |
|---|---:|---|
| S1A-RUN-001 | 六台设备独立身份接入 6/6；错误、共享、过期、吊销和伪造身份成功数 0 | 完整身份 Fixture 集合，每个负向 Case 至少运行一次 |
| S1A-RUN-002 | 跨机构关键负向阻断率 100% | ORG A/B 双向覆盖 REST、RLS、MQTT、SSE、对象访问；任一越权成功即失败 |
| S1A-RUN-003 | 在线状态传播 p95 < 5 秒 | 预热后至少 100 次状态转换，每台设备至少 10 次，记录服务端单调时钟 |
| S1A-RUN-004 | Command Publish → Accepted p95 < 3 秒 | 至少 100 个合法命令，每台设备至少 10 个；排除测试框架启动时间但不排除服务处理时间 |
| S1A-RUN-005 | 未授权、越权或非白名单命令成功数 0 | 完整 Permission/Exception 矩阵；不得只检查 UI 隐藏 |
| S1A-RUN-006 | 重复业务事实和重复命令数 0 | 固定种子重复/乱序场景运行两次；去除预声明的时间字段后规范化结果一致 |
| S1A-RUN-007 | P0 审计字段完整率 100% | 对登录、授权、绑定、命令、跨机构支持抽取全部记录并校验必填字段 |
| S1A-RUN-008 | 未来能力可达成功数 0 | Content/Teaching/AI/Diagnostic/Bulk/OTA 的 UI/API/Job/消息入口均不存在或明确拒绝，且无副作用 |

## 五、固定约束与不变量

1. 只允许合成数据、测试凭据、非生产环境和确定性 Simulator。
2. G1-Device 固定为 `blocked_no_physical_device`；Simulator Evidence 与 HIL Evidence 分开。
3. 每设备身份唯一；浏览器不持有设备凭据、不直连 Broker。
4. Topic 中的 Device ID、证书身份、Payload Device ID 和 Registry 归属必须一致。
5. 只有单设备低风险 `refresh_shadow`；批量、高风险和任意命令不进入范围。
6. 重复/乱序不得产生重复事实，旧 Shadow 不得覆盖新 Shadow。
7. 无法完成授权、审计或事实写入时 Fail Closed，不得伪造成功。
8. Content、Teaching、AI、Diagnostic Bundle、Bulk Command 和 OTA 保持 `disabled/not_started`。
9. 演示材料必须显示 `Simulator-only`、`is_physical_hardware=false`、`production_supported=false`。
10. 当前结果不能宣传为真实客户价值、真实设备兼容、现场验证或生产可用。

## 六、NON-GOALS

- 选择、联系或命名真实试点机构。
- 建立真实学生、教师、客户或机构账户和数据。
- 证明真实私钥存储、OS/Runtime、网络、传感器、执行器或安全互锁。
- 生产题库、内容发布、教学会话、学习分析、ASR/LLM/TTS 或 AI 出题。
- 诊断包、批量命令、高风险审批、固件上传、OTA、A/B 和回滚。
- Kubernetes、Kafka、微服务拆分、RAG、Agent、支付、直播或完整 LMS。
- 以 Demo 成功替代 Requirement Evidence、Gate 或 HIL。

## 七、依赖、风险和下一交付

| 项目 | 状态 | 影响 |
|---|---|---|
| W0 | Passed | 需求、责任与追踪可作为输入 |
| W2 | Complete | 受保护 Public 仓库和基础 CI 可用 |
| W1 Product/QA approval | Approved 2026-08-13 | 解除依赖 W1 的准备工作包阻塞；不解除各自 Gate |
| G1-Device | `blocked_no_physical_device` | 不阻塞阶段 1A；阻塞阶段 1B/真实试点/生产 |
| 产品价值证据 | Missing | 不阻塞内部工程；阻塞客户价值和 Go/No-Go 声明 |
| G2-Device / Gate 3-Sim | Not started | 阻塞正式业务切片启动 |

W1 已获批，但不直接开始业务 Handler。下一条可并行准备路线是 W4 风险边界、W5a/W5b 的 Device 契约、W6a 领域数据和 W7a 本地 TLS/Compose；它们仍各自受依赖和 Gate 约束。

## 八、审批记录

| 角色 | 姓名 | 当前结论 | 日期 |
|---|---|---|---|
| Product Owner | 高端阳 | Approved | 2026-08-13 |
| QA/验收 Owner | 高端阳 | Approved；阶段 1A 一人多角色风险已单独接受 | 2026-08-13 |
| 执行编制 | OpenAI Codex | Prepared；不得批准自己的产物 | 2026-08-13 |

批准记录原文：

> 高端阳批准 MVP-001、STORY-MAP-001、ACCEPTANCE-001、DEMO-001 和 PILOT-001 组成 W1 阶段 1A Simulator-only 范围与验收基线；接受 7 个 P0 Story、1 个 P1 Story、11 个 Out Story 的分类，并确认该批准不涵盖真实设备、真实机构、个人数据、生产、内容、教学、AI、诊断或 OTA。
