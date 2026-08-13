# ACCEPTANCE-001：阶段 1A 验收矩阵

> 版本：0.1.0
>
> 状态：Proposed — Awaiting Product/QA Owner Approval
>
> 范围：[MVP-001](MVP-001%20阶段1A模拟器MVP范围.md) · [STORY-MAP-001](STORY-MAP-001%20阶段1A用户故事地图.md)
>
> 演示：[DEMO-001](DEMO-001%20阶段1A合成数据演示脚本.md)

本文细化 PRD Acceptance 的 Stage 1A 场景，但不替代或弱化 PRD。冲突时以已批准 PRD 为准，并停止受影响实现直到变更完成。

## 一、判定规则

每个 P0 Story 必须覆盖四类路径：

| Path | 含义 | 通过原则 |
|---|---|---|
| `N` Normal | 授权、合法、服务正常 | 产生唯一、可查询、可审计的预期事实 |
| `P` Permission | 跨租户、跨设备、错误角色或身份 | 服务端/Broker 拒绝，敏感事实不泄漏且无副作用 |
| `E` Exception | 非法输入、状态、顺序、重复或过期 | 稳定错误分类；不覆盖新事实、不重复执行 |
| `D` Degraded | 依赖故障、弱网、断线、超时或恢复 | 有界降级、Fail Closed、可恢复，不伪造成功 |

通用失败规则：

- 任一越权、未授权命令或未来能力成功执行，整项 W1 运行验收失败。
- UI 隐藏不算权限控制；必须直接调用 API/消息入口验证。
- HTTP 5xx、进程崩溃或日志中出现异常不等于已安全拒绝；测试必须断言状态与副作用。
- 测试框架错误、系统失败和设备拒绝不得被归类为用户成功。
- Simulator 通过只能写为 `Simulator Verified`；需要实机事实的部分继续 `HIL Missing`。

## 二、P0 Story 验收场景

### 1. ST-GOV-001：机构隔离与最小权限

| Scenario ID | Path | Given / When / Then | Trace | Planned Test / Evidence |
|---|---|---|---|---|
| S1A-AC-GOV-001-N | N | Given ORG-SIM-A 的机构管理员和设备运维；When 查询并执行各自权限矩阵内动作；Then 只返回本机构授权字段和设备，允许动作成功且留下关联 ID | GOV-001/002；AC-GOV-001/002 | TST-GOV-001/002；W6a/W6b/W7b2 |
| S1A-AC-GOV-001-P | P | Given ORG-SIM-A Actor；When 通过 REST、RLS、MQTT、SSE、对象访问或直接隐藏接口访问 ORG-SIM-B/SIM-B-*；Then 全部拒绝、无存在性/内容泄漏、无订阅或写副作用 | GOV-001/002；AC-GOV-001/002 | TST-GOV-001/002；EVD-GOV-001/002 |
| S1A-AC-GOV-001-E | E | Given 缺失、未知或冲突的组织/角色上下文；When 请求任一机构资源；Then 返回稳定认证/授权错误，不以默认租户继续，不产生业务事实 | GOV-001/002；AC-GOV-001/002 | API/RBAC 负向 Fixture |
| S1A-AC-GOV-001-D | D | Given 授权事实无法可靠读取或缓存版本不可确认；When 发起读写或设备控制；Then Fail Closed，不使用过期扩权，不把拒绝记录为业务成功 | GOV-001/002；AC-GOV-001/002 | Auth dependency fault test |

### 2. ST-GOV-002：跨机构支持审计

| Scenario ID | Path | Given / When / Then | Trace | Planned Test / Evidence |
|---|---|---|---|---|
| S1A-AC-GOV-002-N | N | Given 有授权的平台管理员和明确 Reason；When 执行范围内跨机构支持查询；Then 审计包含 Actor、机构、动作、目标、理由、前后状态、时间、request/trace ID | GOV-003；AC-GOV-003 | TST-GOV-003；W6a/W7b2/W9a |
| S1A-AC-GOV-002-P | P | Given 机构管理员或设备运维；When 尝试平台级跨机构支持入口或查询跨机构审计；Then 拒绝且目标租户信息不可见 | GOV-003；AC-GOV-003 | RBAC/API/E2E negative |
| S1A-AC-GOV-002-E | E | Given 平台管理员；When Reason 为空、目标无效、范围超出阶段 1A 或尝试修改既有审计；Then 操作拒绝，审计记录不可由普通业务路径变更 | GOV-003；AC-GOV-003 | Audit validation/tamper test |
| S1A-AC-GOV-002-D | D | Given 审计事实无法持久化；When 发起跨机构支持或命令；Then 高权限动作在产生副作用前被阻断，不排队为未审计成功 | GOV-003；AC-GOV-003 | Audit-store fault test |

### 3. ST-DEV-001：设备注册、Provision 与绑定

| Scenario ID | Path | Given / When / Then | Trace | Planned Test / Evidence |
|---|---|---|---|---|
| S1A-AC-DEV-001-N | N | Given SIM-A-001 在合法初态并有独立测试身份；When 授权运维完成注册、Provision、绑定和激活；Then 只发生合法状态转换，归属 SITE-SIM-A1，操作者与历史可查询 | DEV-001/002；AC-DEV-001/002 | TST-DEV-001/002；W5b/W6b/W8a |
| S1A-AC-DEV-001-P | P | Given 错误、共享、过期、吊销证书，伪造 Device ID 或 ORG-SIM-B Actor；When 连接/绑定 SIM-A-001；Then MQTT/HTTPS/绑定均拒绝且不得激活或改变归属 | DEV-001/002；AC-DEV-001/002 | mTLS/Binding negative Fixture |
| S1A-AC-DEV-001-E | E | Given 已使用/过期 Binding Code、重复请求或非法生命周期转换；When 提交；Then 返回稳定错误或相同幂等结果，不创建重复设备/身份/历史 | DEV-002；AC-DEV-002 | State model/API idempotency |
| S1A-AC-DEV-001-D | D | Given Registry、Provision API 或 Broker 在流程中不可用；When 重试操作；Then 不出现“已激活但无有效身份”等部分成功，恢复后按相同幂等键安全继续 | DEV-001/002；AC-DEV-001/002 | Provision fault/recovery test |

### 4. ST-DEV-002：状态、Shadow、遥测与事件

| Scenario ID | Path | Given / When / Then | Trace | Planned Test / Evidence |
|---|---|---|---|---|
| S1A-AC-DEV-002-N | N | Given SIM-A-001 合法连接；When 上报 Birth、Reported Shadow、最小遥测和结构化事件；Then 在线、Last Seen、Boot ID、版本和合法事实可在授权查询中一致呈现 | DEV-003/004/005；AC-DEV-003/004/005 | TST-DEV-003/004/005；W5a/W8a |
| S1A-AC-DEV-002-P | P | Given 证书设备、Topic Device ID、Payload Device ID 或 Registry 归属不一致；When 上报或查询；Then Broker/网关/API 拒绝或隔离，不写入目标设备事实 | DEV-001/005；AC-DEV-001/005 | Protocol identity negative |
| S1A-AC-DEV-002-E | E | Given 未知 Major、缺字段、越界单位、超大/超速 Payload 或旧 Shadow Version；When 接收；Then 稳定拒绝/隔离，旧状态不覆盖新状态且可观测 | DEV-004/005；AC-DEV-004/005 | Schema/rate/size/property tests |
| S1A-AC-DEV-002-D | D | Given Will、网络丢失、进程重启或上行事实暂时延迟；When 运维查看设备；Then 状态按规则转为 Offline/Stale 并展示数据时效，不把陈旧数据显示为健康实时事实 | DEV-003/005；AC-DEV-003/005 | Disconnect/restart/freshness test |

### 5. ST-DEV-003：弱网、重连和幂等补传

| Scenario ID | Path | Given / When / Then | Trace | Planned Test / Evidence |
|---|---|---|---|---|
| S1A-AC-DEV-003-N | N | Given SIM-A-003 有按 Sequence 缓冲的关键事件；When 网络恢复并重连；Then 事件按契约补传，每个 event/message ID 只产生一个事实，最终状态收敛 | DEV-006；AC-DEV-006 | TST-DEV-006；W8b Conformance |
| S1A-AC-DEV-003-P | P | Given 合法设备尝试借补传向其他 Device Topic/Identity 写入；When 重连发送；Then 全部拒绝，不因 Persistent Session 绕过 ACL | DEV-001/006；AC-DEV-001/006 | MQTT ACL reconnect negative |
| S1A-AC-DEV-003-E | E | Given 重复 Message ID、乱序 Sequence、旧 Shadow、无法解析或漂移时间；When 消费；Then 去重、忽略或隔离结果明确，使用 Server Receive Time 保持事实顺序 | DEV-004/006；AC-DEV-004/006 | Property/fixed-seed scenario |
| S1A-AC-DEV-003-D | D | Given 丢包、抖动、断网和重连风暴；When 固定故障场景执行；Then 使用有界退避/缓冲，优先保留关键事件/ACK，恢复后无重复事实且服务不失控 | DEV-006；AC-DEV-006 | Weak-network/reconnect load test |

### 6. ST-OPS-001：设备查询、事件与基础告警

| Scenario ID | Path | Given / When / Then | Trace | Planned Test / Evidence |
|---|---|---|---|---|
| S1A-AC-OPS-001-N | N | Given ORG-SIM-A 运维；When 按机构/场地/状态筛选并查看设备详情；Then 显示约定在线、版本、Shadow、遥测、事件；约定事件只产生一个可确认告警和上下文 | OPS-001/003；AC-OPS-001/003 | TST-OPS-001/003；W6b/W7b2 |
| S1A-AC-OPS-001-P | P | Given 未授权角色或 ORG-SIM-B Actor；When 查询 SIM-A-*、敏感字段、事件、告警或实时流；Then 列表/计数/详情/订阅全部拒绝或不包含目标数据 | OPS-001/003；AC-OPS-001/003 | API/RLS/SSE/E2E negative |
| S1A-AC-OPS-001-E | E | Given 未知设备、非法筛选/游标或重复事件；When 查询/消费；Then 返回稳定 404/校验结果，重复事件不重复产生告警 | OPS-001/003；AC-OPS-001/003 | Validation/alert dedup test |
| S1A-AC-OPS-001-D | D | Given Broker/Redis/遥测处理短时不可用；When 查看设备；Then 可用事实保持只读并标记 Stale/Partial，告警不伪造已恢复，服务恢复后状态可收敛 | OPS-001/003；AC-OPS-001/003 | Dependency fault/UI state test |

### 7. ST-OPS-002：refresh_shadow 命令闭环

| Scenario ID | Path | Given / When / Then | Trace | Planned Test / Evidence |
|---|---|---|---|---|
| S1A-AC-OPS-002-N | N | Given 授权运维和在线 SIM-A-001；When 以唯一 Idempotency Key 下发合法 `refresh_shadow`；Then 仅创建一个命令，经历 Accepted/Running/Succeeded 或明确 Failed，ACK、结果和审计可查询 | OPS-002；AC-OPS-002 | TST-OPS-002；W5c/W8a/W8b |
| S1A-AC-OPS-002-P | P | Given 错误角色、其他机构、其他设备身份或非白名单/批量/高风险命令；When 请求；Then 在 Publish 前拒绝，不产生 Command、消息或设备副作用 | OPS-002；AC-OPS-002 | Command authorization negative |
| S1A-AC-OPS-002-E | E | Given 重复 Idempotency Key、非法参数、离线/非法设备状态、过期请求或迟到 ACK；When 处理；Then 只有一个命令事实，非法/过期状态明确且不能回退已完成终态 | OPS-002；AC-OPS-002 | State machine/property test |
| S1A-AC-OPS-002-D | D | Given Broker、Worker 或事实存储故障/超时；When 发起或等待命令；Then 不显示 Succeeded；在可证明边界内保持未接受、Failed 或 Expired，恢复/重试仍受同一幂等键约束 | OPS-002；AC-OPS-002 | Publish/worker/database fault test |

## 三、覆盖摘要

| Story | N | P | E | D | 场景数 |
|---|---:|---:|---:|---:|---:|
| ST-GOV-001 | 1 | 1 | 1 | 1 | 4 |
| ST-GOV-002 | 1 | 1 | 1 | 1 | 4 |
| ST-DEV-001 | 1 | 1 | 1 | 1 | 4 |
| ST-DEV-002 | 1 | 1 | 1 | 1 | 4 |
| ST-DEV-003 | 1 | 1 | 1 | 1 | 4 |
| ST-OPS-001 | 1 | 1 | 1 | 1 | 4 |
| ST-OPS-002 | 1 | 1 | 1 | 1 | 4 |
| **合计** | **7** | **7** | **7** | **7** | **28** |

## 四、证据等级

| 等级 | 含义 | 当前状态 |
|---|---|---|
| Specified | 场景、输入、结果、Trace 和计划证据完整 | 本文候选完成，待 Owner 批准 |
| Automated | 指定测试在固定 Commit/Schema 上通过 | 待后续工作包 |
| Simulator Verified | 六台 Simulator 的适用场景通过 | 待 W8b/W9a |
| HIL Verified | 同一套件在真实设备组合通过 | `blocked_no_physical_device` |
| Production Accepted | 真实机构授权、SLO、安全与发布 Gate 通过 | 明确不在阶段 1A |

演示只能辅助审查，不替代上述证据等级。
