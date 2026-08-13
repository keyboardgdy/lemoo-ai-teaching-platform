# DEMO-001：阶段 1A 合成数据演示脚本

> 版本：1.0.0
>
> 状态：Approved Script — Not Yet Executed
>
> 批准记录：[Issue #3 Approval](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3#issuecomment-5278164835)
>
> 范围：[MVP-001](MVP-001%20阶段1A模拟器MVP范围.md)
>
> 验收：[ACCEPTANCE-001](ACCEPTANCE-001%20阶段1A验收矩阵.md)

本文规定阶段 1A 的可重复验收演示。当前 W1 只批准脚本；在 W5/W6/W7/W8 和 Gate 3-Sim 完成前不得将脚本标为 `Executed` 或用人工演示替代自动化证据。

## 一、演示目标与限制

演示必须让审查者看到：

1. 设备云正常主路径能够闭环。
2. 权限、身份、租户和命令失败路径确实阻断。
3. 重复、乱序、弱网、时钟漂移和依赖故障不会伪造事实。
4. Content、Teaching、AI、Diagnostic、Bulk Command 和 OTA 不可达。
5. 所有画面和输出明确标记 Simulator-only、Synthetic-only、Non-production。

演示不得出现真实姓名、邮箱、学校、学生、设备序列号、客户数据、生产域名或真实凭据。

## 二、固定数据集

### 1. Seed 元数据

```yaml
dataset_id: stage1a-demo-v1
random_seed: 20260813
clock_epoch: 2030-01-01T00:00:00Z
synthetic_only: true
contains_personal_data: false
environment: local_or_ephemeral_ci
production_supported: false
```

除专门的时钟漂移 Case 外，事件时间从 `clock_epoch` 以确定性步长生成。密码、私钥和证书不写入本文，由测试运行时生成并在清理步骤撤销/删除。

### 2. Actor Fixture

| actor_code | 角色 | Tenant | 允许用途 |
|---|---|---|---|
| `USR-SIM-PLT-001` | ACT-PLT | Platform | 经 Reason 的跨机构支持与审计核查 |
| `USR-SIM-A-ORG-001` | ACT-ORG | ORG-SIM-A | A 机构成员/设备归属管理 |
| `USR-SIM-A-OPS-001` | ACT-OPS | ORG-SIM-A | A 设备查询、告警确认和单命令 |
| `USR-SIM-B-ORG-001` | ACT-ORG | ORG-SIM-B | B 机构对照管理 |
| `USR-SIM-B-OPS-001` | ACT-OPS | ORG-SIM-B | B 设备与负向命令对照 |

Display Name 使用“模拟平台管理员”“模拟 A 机构管理员”等显式合成名称；测试登录标识使用保留域 `.invalid`，不创建可投递邮箱。

### 3. Tenant、Site 与 Device Fixture

| Tenant | Site | Device |
|---|---|---|
| ORG-SIM-A | SITE-SIM-A1 | SIM-A-001、SIM-A-002、SIM-A-003、SIM-A-004 |
| ORG-SIM-B | SITE-SIM-B1 | SIM-B-001、SIM-B-002 |

全部设备使用：

```text
SIM_EDU_ROBOT_V1 × sim-r1 × sim-1 × sim-1
is_physical_hardware=false
production_supported=false
```

### 4. 负向 Fixture

- `CERT-WRONG-CA`、`CERT-EXPIRED`、`CERT-REVOKED`、`CERT-SHARED`。
- 证书/Client ID/Topic/Payload Device ID 不一致。
- 未知 Major、缺字段、超大 Payload、越界单位和超速消息。
- 重复 Message ID、重复 Idempotency Key、旧 Shadow Version、乱序 Sequence。
- 命令过期、非法参数、离线/非法设备状态、迟到 ACK。
- ORG A/B 双向 REST/RLS/MQTT/SSE/S3 越权请求。

## 三、演示前置检查

执行者必须先记录：

| 检查 | 预期 |
|---|---|
| Commit SHA | 非空，且与 CI/证据引用一致 |
| Schema Version/Digest | 当前 G2-Device 候选或冻结版本 |
| Artifact/Image Digest | 所有运行制品可追踪；不得只记录 tag |
| Dataset | `stage1a-demo-v1`，重置后 Hash 一致 |
| Environment | 本地或临时 CI，非生产 |
| Gate | Gate 0、W1、G2-Device、Gate 3-Sim 状态明确 |
| Device facts | G1-Device=`blocked_no_physical_device` |
| Future capability | 全部 `disabled/not_started` |

任一检查缺失时停止演示并记录 `NOT_READY`，不得临时跳过。

## 四、演示步骤

| Step | Actor/Device | 操作 | 期望可见结果 | Trace |
|---|---|---|---|---|
| DEMO-00 | 执行者 | 打开系统状态/版本信息 | 显示 Simulator-only、Synthetic-only、Non-production、Commit/Schema；未来能力 disabled | MVP 不变量；S1A-RUN-008 |
| DEMO-01 | USR-SIM-A-ORG-001 | 查看 A 机构、SITE-SIM-A1 和成员权限 | 只显示 ORG-SIM-A；角色可执行动作与矩阵一致 | ST-GOV-001 N |
| DEMO-02 | USR-SIM-A-ORG-001 / SIM-A-001 | 注册、Provision、绑定并激活正常设备 | 合法生命周期、唯一测试身份、归属和审计可查询 | ST-DEV-001 N |
| DEMO-03 | SIM-A-001 | 连接并发送 Birth/Reported Shadow | 设备 Online，Last Seen、Boot ID、版本和 Shadow 一致 | ST-DEV-002 N |
| DEMO-04 | SIM-A-001 | 发送最小遥测和约定事件 | 详情显示合法事实；约定事件产生一次基础告警 | ST-DEV-002/OPS-001 N |
| DEMO-05 | USR-SIM-A-OPS-001 | 下发合法 `refresh_shadow` | 一个 Command，展示 Accepted/Running/终态、ACK、结果和审计 | ST-OPS-002 N |
| DEMO-06 | SIM-A-002 | 发送重复 Message、乱序 Sequence 和旧 Shadow | 只产生一个业务事实；旧状态不覆盖新状态；拒绝/忽略可观测 | ST-DEV-003 E |
| DEMO-07 | SIM-A-003 | 注入弱网、断线、Will、重连和补传 | 状态确定、使用有界退避、关键事件补传且不重复 | ST-DEV-003 N/D |
| DEMO-08 | SIM-A-004 | 发送超前、落后和不可解析设备时间 | Server Receive Time 保持事实顺序，异常时间被隔离/标记 | ST-DEV-003 E |
| DEMO-09 | USR-SIM-A-OPS-001 / SIM-B-001 | 尝试读取/订阅/控制 B 设备 | REST/RLS/MQTT/SSE/S3 全部拒绝，无列表计数或存在性泄漏 | ST-GOV-001 P |
| DEMO-10 | 负向证书 Fixture | 连接 MQTT/Device HTTPS | 错误、共享、过期、吊销、伪造身份全部拒绝 | ST-DEV-001 P |
| DEMO-11 | USR-SIM-B-OPS-001 / SIM-B-002 | 发送重复、过期、非法参数、离线状态和非白名单命令 | 不产生重复执行；非法/过期/越权均在 Publish 前或设备端拒绝 | ST-OPS-002 P/E |
| DEMO-12 | USR-SIM-PLT-001 | 带 Reason 执行允许的跨机构支持查询并查看审计 | 审计字段完整；机构角色不可访问同一入口 | ST-GOV-002 N/P |
| DEMO-13 | 故障控制器 | 分别注入授权/审计、PostgreSQL、Redis、EMQX 短时故障 | 按 ACCEPTANCE-001 降级；无伪造成功；恢复后状态收敛 | 全部 P0 D |
| DEMO-14 | 任一 Actor/Device | 尝试 Content/Teaching/AI/Diagnostic/Bulk/OTA 入口 | UI 不出现，API/Job/消息入口不存在或明确拒绝，无副作用 | S1A-RUN-008 |
| DEMO-15 | 执行者 | 复核运行摘要、审计、指标和范围标记 | 28/28 场景、运行指标、失败清单和证据链接可查询；不产生实机声明 | W9a handoff |

## 五、负向验证最小集合

“100% 阻断”以有限、预先登记集合为分母，不允许只运行容易通过的样本：

| 集合 | 必须覆盖 |
|---|---|
| Tenant directions | ORG A → B、ORG B → A |
| Surfaces | REST、RLS direct query、MQTT publish/subscribe、SSE、S3/object access |
| Actor types | ORG admin、device ops、device identity、platform support without valid context |
| Device identity | Wrong CA、Expired、Revoked、Shared、Client ID mismatch、Topic mismatch、Payload mismatch |
| Command | Wrong role、cross-tenant、non-allowlisted、bulk、invalid args/state、expired、duplicate、late ACK |
| Message | Unknown major、missing field、oversize、over-rate、duplicate、out-of-order、old shadow、clock drift |

如果某 Surface 尚未部署，对应 Case 记录 `NOT_DEPLOYED` 并证明入口不可达；不得从分母中静默删除。

## 六、记录格式

每次执行输出至少包含：

```yaml
demo_id: DEMO-001
dataset_id: stage1a-demo-v1
commit_sha: <sha>
schema_versions: []
artifact_digests: []
started_at: <utc>
finished_at: <utc>
environment: <local-or-ephemeral-ci>
is_physical_hardware: false
production_supported: false
scenario_results:
  passed: 0
  failed: 0
  not_ready: 0
runtime_metrics: {}
g1_device: blocked_no_physical_device
evidence_links: []
```

原始报告写入对应后续 Evidence 目录；日志和截图必须去除 Token、Cookie、证书私钥及本机路径中的敏感信息。

## 七、清理与回退

1. 停止 Simulator 和故障注入器。
2. 吊销/删除本次运行时生成的测试身份；不得复用到共享或生产环境。
3. 清理临时容器和网络，命名数据卷按测试策略保留或由显式 Reset 删除。
4. 归档去敏结果、Commit、Schema 和 Digest；失败结果同样保留。
5. 恢复所有 Feature Gate 为默认关闭并再次运行可达性检查。
6. 若任一越权或伪造成功，标记整次 Demo `FAILED_SECURITY`，立即停止后续展示并进入缺陷流程。

## 八、明确声明

演示完成后的唯一允许表述是：

> 在指定 Commit、Schema、制品 Digest、合成数据集和确定性 Simulator 场景下，阶段 1A 云端实现通过了所列协议、权限、状态机和故障验收。

不得表述为“已兼容真实机器人”“已完成真实学校试点”“设备安全已验证”或“可生产部署”。
