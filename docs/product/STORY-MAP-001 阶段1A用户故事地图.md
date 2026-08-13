# STORY-MAP-001：阶段 1A 用户故事地图

> 版本：1.0.0
>
> 状态：Approved — Stage 1A Simulator-only
>
> 批准记录：[Issue #3 Approval](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3#issuecomment-5278164835)
>
> 范围：[MVP-001 阶段 1A 模拟器 MVP](MVP-001%20阶段1A模拟器MVP范围.md)
>
> 上位 Story：[PRD-001 第八章](PRD-001%20教育机器人云平台.md#八用户故事目录)
>
> 验收：[ACCEPTANCE-001](ACCEPTANCE-001%20阶段1A验收矩阵.md)

本文只决定阶段 1A 的交付优先级和路径，不新增产品 Requirement，也不把 Out Story 物理删除。

## 一、优先级定义

| 分类 | 含义 | 进入条件 |
|---|---|---|
| P0 | 构成 Simulator 设备云最小闭环，缺少任一项则无法证明阶段 1A 目标 | W1 批准后进入对应准备工作包；正式实现仍需 G2-Device/Gate 3-Sim |
| P1 | Gate/恢复支撑，必须在 W9a 前完成，但不属于首个用户操作闭环 | 对应前置工作包完成后排入 |
| Out | 不属于阶段 1A；必须保持 `disabled/not_started` | 只有对应阶段和 G1/G2 通过后重新排期 |

## 二、活动骨架与 P0 路径

| 活动 | 用户结果 | P0 Story | 主要 Requirement | 验收重点 |
|---|---|---|---|---|
| 1. 进入正确租户 | 管理员/运维只能看见获授权机构资源 | `ST-GOV-001` | GOV-001/002 | RLS/API/MQTT/SSE/S3 与服务端 RBAC |
| 2. 进行跨机构支持 | 平台支持操作有理由、边界和审计 | `ST-GOV-002` | GOV-003 | 审计完整、不可篡改、审计失败时阻断 |
| 3. 纳管模拟设备 | 运维注册、Provision、绑定和停用唯一身份设备 | `ST-DEV-001` | DEV-001/002 | 独立身份、合法生命周期、幂等与回退 |
| 4. 观察设备事实 | 运维看到在线、版本、Shadow、遥测和事件 | `ST-DEV-002` | DEV-003/004/005 | 状态一致、Schema/顺序/速率校验 |
| 5. 经历弱网恢复 | 重连后事件可补传且不重复 | `ST-DEV-003` | DEV-006 | 重复、乱序、时钟漂移、重连退避 |
| 6. 定位基础异常 | 运维从列表/详情/事件/告警理解设备状态 | `ST-OPS-001` | OPS-001/003；DEV-005 | 授权查询、告警去重、陈旧/降级显示 |
| 7. 执行受控操作 | 运维向单设备下发 `refresh_shadow` 并看到结果 | `ST-OPS-002` | OPS-002 | 白名单、幂等、过期、ACK、审计 |

## 三、建议交付切片

此顺序用于拆分后续 Story PR，不允许绕过每个工作包自己的依赖。

| Slice | 可演示的端到端增量 | Story | 依赖说明 |
|---|---|---|---|
| S0 范围与合成身份 | 固定 ORG/Site/User/Device 数据且未来能力不可达 | 全部 P0 的前置 | W1、W4、W6a |
| S1 租户与设备登记 | ORG-SIM-A 管理员登记并绑定 SIM-A-001，ORG-SIM-B 不可见 | GOV-001、DEV-001 | W5b、W6a、W6b、W7a |
| S2 连接与状态 | SIM-A-001 接入，上报 Birth/Shadow/Telemetry/Event，Web 可查看 | DEV-002、OPS-001 | W5a/W5b、W6a/W6b、W8a |
| S3 单命令闭环 | 运维发出 `refresh_shadow`，设备 ACK，Web/审计显示终态 | OPS-002、GOV-002 | W5c、W8a |
| S4 一致性与恢复 | SIM-A-002/003/004 验证重复、乱序、弱网、时钟漂移 | DEV-003 | W8b |
| S5 隔离与拒绝 | ORG A/B、SIM-B-001/002 与负向身份验证所有禁止路径 | 全部 P0 | W7b2、W8b |

任何 Slice 如果不能独立展示安全失败结果，就继续拆分，不能把负向验收推迟到最后补做。

## 四、全量 Story 唯一分类

### 1. P0：阶段 1A 最小闭环

| Story ID | Actor | 用户结果 | Requirement/Acceptance | 选择理由 |
|---|---|---|---|---|
| `ST-GOV-001` | ACT-ORG/ACT-OPS | 只访问所属机构授权资源 | GOV-001/002；AC-GOV-001/002 | 多租户安全前提 |
| `ST-GOV-002` | ACT-PLT | 跨机构支持操作完整审计 | GOV-003；AC-GOV-003 | 高权限操作不可无痕 |
| `ST-DEV-001` | ACT-OPS | 独立身份注册、Provision 和绑定设备 | DEV-001/002；AC-DEV-001/002 | 设备云入口 |
| `ST-DEV-002` | ACT-OPS | 查看在线、Last Seen、版本、Shadow、遥测和事件 | DEV-003/004/005；AC-DEV-003/004/005 | 设备事实主路径 |
| `ST-DEV-003` | ACT-OPS | 重连后事实正确且无重复 | DEV-006；AC-DEV-006 | 现场网络风险的模拟协议验证 |
| `ST-OPS-001` | ACT-OPS | 查询设备并理解基础事件/告警 | OPS-001/003；AC-OPS-001/003 | 运维可观察结果 |
| `ST-OPS-002` | ACT-OPS | 安全执行单设备低风险命令 | OPS-002；AC-OPS-002 | 最小控制闭环 |

### 2. P1：阶段 1A 启动支撑

| Story ID | Actor | 用户结果 | Requirement/Acceptance | 不进入首个闭环的理由 |
|---|---|---|---|---|
| `ST-REL-002` | 运维 | 已部署事实存储和配置可按目标恢复 | REL-002；AC-REL-002 | W7c/W9a 前需要，但 RPO/RTO 仍需环境事实，不是设备用户主路径 |

### 3. Out：阶段 1A 明确排除

| Story ID | 能力 | 排除理由 | 重新进入条件 |
|---|---|---|---|
| `ST-OPS-003` | 诊断包 | 涉及敏感数据采集、保存、脱敏和下载授权 | 阶段 5 风险/契约 Gate |
| `ST-CNT-001` | 内容建模 | 阶段 2；当前没有内容事实或设备安装能力 | G1/G2-Content |
| `ST-CNT-002` | 题目导入 | 阶段 2；来源样本与映射未确认 | G2-Content |
| `ST-CNT-003` | AI 草稿/内容包 | 内容权利、审核和设备安装均未通过 | G1/G2-Content |
| `ST-TCH-001` | 教学会话 | 学生身份模式和教学契约未批准 | G2-Teaching |
| `ST-TCH-002` | 学生互动 | 需要内容、脚本、设备交互和教学状态 | G2-Teaching；适用 HIL |
| `ST-TCH-003` | 学习分析 | 缺少数据政策、教学事实和指标口径 | G2-Teaching/Privacy |
| `ST-AI-001` | AI 反馈 | Provider、Eval、音频、动作安全均未知 | G1/G2-AI |
| `ST-AI-002` | AI 运营 | 模型/Prompt/成本/安全治理未冻结 | G2-AI |
| `ST-OTA-001` | OTA | 无真实 Updater、签名、A/B 或回滚事实 | G1/G2-OTA/HIL |
| `ST-REL-001` | 离线教学 | 依赖尚未进入范围的内容、教学和 AI | 对应 Content/Teaching/AI Gate |

## 五、Story Definition of Ready

P0 Story 进入正式实现前必须同时满足：

- 本文分类已由高端阳批准。
- Requirement、PRD Acceptance、ACCEPTANCE-001 Scenario 和计划 Test/Evidence 可双向追踪。
- 所需 G2-Device 契约已冻结；依赖的准备工作包已完成。
- 正常、权限、异常、降级四类路径均可自动化，且失败行为 Fail Closed。
- Synthetic Tenant、Actor、Device 和固定随机种子已定义。
- 数据分类、审计字段、可观测字段和不得记录字段已明确。
- Out 能力没有成为隐式依赖或“先留接口”。
- PR 可以独立回滚，且不会改变 G1-Device 的阻塞状态。

## 六、反范围保护

以下请求即使实现成本很低，也不能被加入 P0/P1：

- “顺便”增加题目 CRUD、聊天窗口、AI Provider 或 OTA 上传页面。
- 为真实客户或真实设备预置未验证字段并宣称兼容。
- 将 `refresh_shadow` 扩展为批量命令、Shell、URL、文件下载或任意 MQTT Publish。
- 用诊断日志、学生身份或真实机构数据让 Demo 看起来更真实。
- 用占位 API/页面返回成功来展示 Out 能力。

范围变更必须先更新 PRD/RTM/MVP/Story Map/Acceptance，并由相应 Owner 重新批准。
